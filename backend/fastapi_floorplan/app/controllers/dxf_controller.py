# ------------------------------------------------------------------------------
# DxfController Module
#
# Orchestrates the full DXF → PNG pipeline, then delegates persistence to DbController.
# Responsibilities:
#   1. DXF Parsing & Filtering:
#        • Load DXF via ezdxf
#        • Identify only “floorplan” geometry (lines, polylines, arcs, etc.)
#   2. Image Rendering:
#        • Render each matching BLOCK and LAYER to PNG via ezplt.qsave
#        • Force a strict black-on-white palette for clarity
#   3. Deduplication:
#        • Hash each PNG to avoid duplicates
#   4. Metadata Management:
#        • Collect relative paths by keyword into a JSON file
#   5. Database Integration:
#        • Save plan record and its metadata via DbController
#   6. Keyword Extraction Helper:
#        • Standalone scan of a DXF’s blocks & layers for available keywords
#
# Exposed static methods:
#   • process           — full-run: DXF → PNGs → JSON → DB
#   • preview           — DXF → PNGs → JSON (no DB)
#   • process_request   — FastAPI helper wrapping process()
#   • extract_keywords  — FastAPI helper to scan keywords only
#   • get_floor_metadata, export_floor_image,
#     list_exported_images, get_image_file_by_id — API integration helpers
#
# Dependencies:
#   - ezdxf, matplotlib (ezplt) for rendering
#   - PIL for enforcing B/W
#   - hashlib, uuid for file hashing & IDs
#   - DbController for persistence
#   - FastAPI types for API integration
# ------------------------------------------------------------------------------
import hashlib
import json
from pathlib import Path
import uuid
import ezdxf
from ezdxf.addons.drawing import matplotlib as ezplt
from PIL import Image

from app.config import (
    UPLOAD_DIR,
    KEYWORDS,
    BLACKLIST,
    EXCLUDED_LAYER_NAMES,
    DPI,
    cfg,
    OUTPUT_DIR,
    BASE_DIR,
)
from app.controllers.db_controller import DbController
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
import shutil
import mimetypes


class DxfController:
    """
    Central controller for DXF processing:
      • Rendering
      • Metadata generation
      • Database persistence
      • API-facing helpers
    """

    @staticmethod
    def force_black_on_white(png_path: Path):
        """
        Re-open the PNG at `png_path`, convert to pure B/W:
        • Every pixel ≠ white becomes black.
        • Saves back to the same file.
        """
        img = Image.open(png_path).convert("RGB")
        pixels = img.getdata()
        new_pixels = [
            (0, 0, 0) if pixel != (255, 255, 255) else (255, 255, 255)
            for pixel in pixels
        ]
        img.putdata(new_pixels)
        img.save(png_path)

    @staticmethod
    def is_floorplan_geometry(entity) -> bool:
        """
        True for DXF entities that form floorplan outlines:
        LINE, LWPOLYLINE, POLYLINE, CIRCLE, ARC, ELLIPSE, SPLINE.
        """
        return entity.dxftype() in {
            'LINE',
            'LWPOLYLINE',
            'POLYLINE',
            'CIRCLE',
            'ARC',
            'ELLIPSE',
            'SPLINE',
        }

    @staticmethod
    def process(
        file_path: Path,
        keywords: list[str],
        blacklist: list[str],
        excluded_layer_names: set[str],
        dpi: int,
        plan_id: str
    ) -> str:
        """
        Full-pipeline: DXF → PNGs → metadata JSON → DB record.
        Returns the plan_id on success.
        """
        doc = ezdxf.readfile(str(file_path))
        msp = doc.modelspace()

        exported_hashes: dict[str, str] = {}
        metadata: dict[str, list[str]] = {}
        base_folder = OUTPUT_DIR / f"floor_pngs_{plan_id}"
        base_folder.mkdir(parents=True, exist_ok=True)

        # ----------------------------- BLOCK PASS ----------------------------------- #
        for blk in doc.blocks:
            name_u = blk.name.upper()
            if any(k in name_u for k in keywords) and not any(b in name_u for b in blacklist):
                kw = next(k for k in keywords if k in name_u)
                folder = base_folder / kw
                folder.mkdir(parents=True, exist_ok=True)

                png_path = folder / f"{blk.name}.block-{plan_id}.png"
                ezplt.qsave(
                    blk,
                    png_path,
                    dpi=dpi,
                    config=cfg,
                    filter_func=DxfController.is_floorplan_geometry
                )
                DxfController.force_black_on_white(png_path)

                file_hash = hashlib.md5(png_path.read_bytes()).hexdigest()
                if file_hash in exported_hashes:
                    png_path.unlink()
                else:
                    exported_hashes[file_hash] = png_path.name
                    metadata.setdefault(kw, []).append(str(png_path.relative_to(OUTPUT_DIR)))

        # ----------------------------- LAYER PASS ----------------------------------- #
        for lay in doc.layers:
            name_u = lay.dxf.name.upper()
            if (
                any(k in name_u for k in keywords)
                and not any(b in name_u for b in blacklist)
                and name_u not in excluded_layer_names
            ):
                kw = next(k for k in keywords if k in name_u)
                folder = base_folder / kw
                folder.mkdir(parents=True, exist_ok=True)

                png_path = folder / f"{lay.dxf.name}.layer-{plan_id}.png"
                ezplt.qsave(
                    msp,
                    png_path,
                    dpi=dpi,
                    config=cfg,
                    filter_func=lambda e, layer=lay.dxf.name: (
                        DxfController.is_floorplan_geometry(e) and e.dxf.layer == layer
                    )
                )
                DxfController.force_black_on_white(png_path)

                file_hash = hashlib.md5(png_path.read_bytes()).hexdigest()
                if file_hash in exported_hashes:
                    png_path.unlink()
                else:
                    exported_hashes[file_hash] = png_path.name
                    metadata.setdefault(kw, []).append(str(png_path.relative_to(OUTPUT_DIR)))

        # --------------------------- METADATA FILE --------------------------------- #
        meta_file = base_folder / f"metadata-{plan_id}.json"
        meta_file.write_text(json.dumps(metadata, indent=4))

        # --------------------------- DATABASE SAVE --------------------------------- #
        primary = next(iter(metadata))
        flat_paths = [p for paths in metadata.values() for p in paths]
        DbController.save_floor_plan_with_id(plan_id, primary, flat_paths, metadata)
        return plan_id

    @staticmethod
    async def process_request(file: UploadFile, params: dict) -> str:
        """
        Asynchronous entry for FastAPI; saves temp file then delegates to process().
        """
        ext = Path(file.filename).suffix
        plan_id = uuid.uuid4().hex
        temp_path = UPLOAD_DIR / f"{plan_id}{ext}"
        temp_path.write_bytes(await file.read())

        keywords = params.get("keywords", list(KEYWORDS))
        blacklist = params.get("blacklist", list(BLACKLIST))
        excluded = set(params.get("excluded_layer_names", EXCLUDED_LAYER_NAMES))
        dpi_value = params.get("dpi", DPI)

        return DxfController.process(
            file_path=temp_path,
            keywords=keywords,
            blacklist=blacklist,
            excluded_layer_names=excluded,
            dpi=dpi_value,
            plan_id=plan_id
        )

    @staticmethod
    def get_floor_metadata(plan_id: str) -> dict:
        """
        Retrieve stored floor-plan metadata from the DB.
        """
        data = DbController.get_floors(plan_id)
        if not data:
            raise ValueError("Plan not found")
        return data

    @staticmethod
    def export_floor_image(params: dict) -> str:
        """
        Copy a selected image view to a job folder and return its absolute path.
        """
        record = DbController.get_floors(params["floor_id"])
        if not record:
            raise ValueError("Plan not found")

        views = record.get("metadata", {}).get(params["floor"], [])
        idx = params.get("view_index", -1)
        if idx < 0 or idx >= len(views):
            raise ValueError("Invalid floor or view_index")

        src = OUTPUT_DIR / views[idx]
        if not src.exists():
            raise FileNotFoundError("Source image not found")

        dest_dir = BASE_DIR / "data" / "jobs" / params["floor_id"] / "selected_output"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        shutil.copy(src, dest)
        return str(dest)

    @staticmethod
    def list_exported_images(floor_plan_id: str) -> list[dict]:
        """
        List all images exported for a given floor plan ID.
        """
        export_dir = BASE_DIR / "data" / "jobs" / floor_plan_id / "selected_output"
        if not export_dir.exists():
            raise FileNotFoundError("Export directory not found")
        return [
            {"image_id": f.stem, "image_name": f.name}
            for f in export_dir.iterdir()
            if f.suffix.lower() in {'.png', '.jpg', '.jpeg'}
        ]

    @staticmethod
    def get_image_file_by_id(image_id: str) -> FileResponse:
        """
        Serve a previously exported image by its image_id.
        """
        jobs_dir = BASE_DIR / "data" / "jobs"
        for plan_dir in jobs_dir.iterdir():
            sel_dir = plan_dir / "selected_output"
            if sel_dir.exists():
                for img in sel_dir.iterdir():
                    if img.stem == image_id:
                        mime, _ = mimetypes.guess_type(str(img))
                        return FileResponse(img, media_type=mime)
        raise FileNotFoundError("Image not found")

    @staticmethod
    def preview(
        file_path: Path,
        keywords: list[str],
        blacklist: list[str],
        excluded_layer_names: set[str],
        dpi: int,
        plan_id: str
    ) -> tuple[dict[str, list[str]], list[str]]:
        """
        Render only floorplan geometry to PNGs under OUTPUT_DIR/floor_pngs_<plan_id>
        without writing to the DB (for preview).
        """
        doc = ezdxf.readfile(str(file_path))
        msp = doc.modelspace()
        metadata: dict[str, list[str]] = {}
        base_folder = OUTPUT_DIR / f"floor_pngs_{plan_id}"
        base_folder.mkdir(parents=True, exist_ok=True)

        # ----------------------------- BLOCK PASS ----------------------------------- #
        for blk in doc.blocks:
            name_u = blk.name.upper()
            if any(k in name_u for k in keywords) and not any(b in name_u for b in blacklist):
                kw = next(k for k in keywords if k in name_u)
                folder = base_folder / kw
                folder.mkdir(parents=True, exist_ok=True)

                out = folder / f"{blk.name}.block-{plan_id}.png"
                ezplt.qsave(
                    blk,
                    out,
                    dpi=dpi,
                    config=cfg,
                    filter_func=DxfController.is_floorplan_geometry
                )
                DxfController.force_black_on_white(out)
                metadata.setdefault(kw, []).append(str(out.relative_to(OUTPUT_DIR)))

        # ----------------------------- LAYER PASS ----------------------------------- #
        for lay in doc.layers:
            name_u = lay.dxf.name.upper()
            if (
                any(k in name_u for k in keywords)
                and not any(b in name_u for b in blacklist)
                and name_u not in excluded_layer_names
            ):
                kw = next(k for k in keywords if k in name_u)
                folder = base_folder / kw
                folder.mkdir(parents=True, exist_ok=True)

                out = folder / f"{lay.dxf.name}.layer-{plan_id}.png"
                ezplt.qsave(
                    msp,
                    out,
                    dpi=dpi,
                    config=cfg,
                    filter_func=lambda e, layer=lay.dxf.name: (
                        DxfController.is_floorplan_geometry(e) and e.dxf.layer == layer
                    )
                )
                DxfController.force_black_on_white(out)
                metadata.setdefault(kw, []).append(str(out.relative_to(OUTPUT_DIR)))

        meta_file = base_folder / f"metadata-{plan_id}.json"
        meta_file.write_text(json.dumps(metadata, indent=4))

        rel_paths = [p for paths in metadata.values() for p in paths]
        return metadata, rel_paths

    @staticmethod
    def extract_keywords(file_path: Path) -> list[str]:
        """
         Scan a DXF for our KEYWORDS. Returns two sorted lists:
         • block_keywords: from block names
         • layer_keywords: from layer names or entity layers
        """
        doc = ezdxf.readfile(str(file_path))
        msp = doc.modelspace()
       
        block_found: set[str] = set()
        layer_found: set[str] = set()

        # collect all block names
        for blk in doc.blocks:
            name = blk.name.upper()
            if any(b in name for b in BLACKLIST):
                continue
            for k in KEYWORDS:
                if k in name:
                    
                    block_found.add(k)

        # collect all layer-style names
        layer_names = {lay.dxf.name.upper() for lay in doc.layers}
        entity_layers = {
            getattr(e.dxf, "layer", "").upper()
            for e in msp
            if hasattr(e.dxf, "layer")
        }
        for nm in layer_names.union(entity_layers):
            if nm in EXCLUDED_LAYER_NAMES or any(b in nm for b in BLACKLIST):
                continue
            for k in KEYWORDS:
                if k in nm:
                    
                    layer_found.add(k)

        return {"block_keywords": sorted(block_found),"layer_keywords": sorted(layer_found),}
