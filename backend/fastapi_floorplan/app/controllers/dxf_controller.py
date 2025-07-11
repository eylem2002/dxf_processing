# ------------------------------------------------------------------------------
# DxfController Module
#
# Handles DXF file processing for the floorplan service:
#   • Parse and filter DXF geometry via ezdxf
#   • Render matching blocks and layers to B/W PNGs via ezplt.qsave
#   • Deduplicate images using MD5 hashing
#   • Generate keyword→image metadata JSON
#   • Persist floor plan records in the DB via DbController
#   • Provide FastAPI helper methods for preview, processing, export, and keyword/entity scans
#
# Key methods:
#   - process:        Full pipeline (DXF→PNGs→metadata→DB), raises HTTPException on errors
#   - preview:        Render PNGs for preview (no DB writes), raises HTTPException on errors
#   - process_request: Async FastAPI entrypoint for process()
#   - scan_dxf_for_preview: Async helper to save uploads and extract keywords/entity types
#   - extract_keywords: Scan a DXF for block and layer keywords
#   - extract_entity_types: List all DXF entity types
#   - get_floor_metadata, export_floor_image,
#     list_exported_images, get_image_file_by_id: API integration helpers (raise HTTPException)
# ------------------------------------------------------------------------------
import hashlib
import json
from pathlib import Path
import re
from typing import List
import uuid
import ezdxf

import hashlib
from ezdxf.addons.drawing import matplotlib as ezplt
from PIL import Image

from app.config import (
    UPLOAD_DIR,
    DPI,
    cfg,
    OUTPUT_DIR,
    BASE_DIR,
)
from app.controllers.db_controller import DbController
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
import shutil
from wordfreq import zipf_frequency
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
        try:
            img = Image.open(png_path).convert("RGB")
            pixels = img.getdata()
            new_pixels = [
                (0, 0, 0) if pixel != (255, 255, 255) else (255, 255, 255)
                for pixel in pixels
            ]
            img.putdata(new_pixels)
            img.save(png_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    @staticmethod
    def process(
        file_path: Path,
        keywords: list[str],
        entity_types: set[str],
        dpi: int,
        plan_id: str
    ) -> str:
        """
        Full-pipeline: DXF → PNGs → metadata JSON → DB record.
        Returns the plan_id on success.
        """  
        try:
            doc = ezdxf.readfile(str(file_path))
            msp = doc.modelspace()

            exported_hashes: dict[str, str] = {}
            metadata: dict[str, list[str]] = {}
            base_folder = OUTPUT_DIR / f"floor_pngs_{plan_id}"
            base_folder.mkdir(parents=True, exist_ok=True)

            # ----------------------------- BLOCK PASS ----------------------------------- #
            for blk in doc.blocks:
                name_u = blk.name.upper()
                if re.fullmatch(r"[A-Za-z]{3,}", name_u) and name_u in keywords:      
                    kw = name_u
                    folder = base_folder / kw
                    folder.mkdir(parents=True, exist_ok=True)

                    png_path = folder / f"{blk.name}.block-{plan_id}.png"
                    ezplt.qsave(
                        blk,
                        png_path,
                        dpi=dpi,
                        config=cfg,
                        filter_func=lambda e: e.dxftype() in entity_types
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
                if re.fullmatch(r"[A-Za-z]{3,}", name_u) and name_u in keywords:
                    kw = name_u
                    folder = base_folder / kw
                    folder.mkdir(parents=True, exist_ok=True)

                    png_path = folder / f"{lay.dxf.name}.layer-{plan_id}.png"
                    ezplt.qsave(
                        msp,
                        png_path,
                        dpi=dpi,
                        config=cfg,
                        filter_func=lambda e, layer=lay.dxf.name: ( e.dxf.layer == layer
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
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    async def process_request(file: UploadFile, params: dict) -> str:
        """
        Asynchronous entry for FastAPI; saves temp file then delegates to process().
        """
        try:
            ext = Path(file.filename).suffix
            plan_id = uuid.uuid4().hex
            temp_path = UPLOAD_DIR / f"{plan_id}{ext}"
            temp_path.write_bytes(await file.read())

            dpi_value = params.get("dpi", DPI)

            return DxfController.process(
                file_path=temp_path,
                dpi=dpi_value,
                plan_id=plan_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def get_floor_metadata(plan_id: str) -> dict:
        """
        Retrieve stored floor-plan metadata from the DB.
        """
        try:
            data = DbController.get_floors(plan_id)
            if not data:
                raise HTTPException(status_code=404, detail="Plan not found")
            return data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def export_floor_image(params: dict) -> str:
        """
        Copy a selected image view to a job folder and return its absolute path.
        """
        try:
            record = DbController.get_floors(params["floor_id"])
            if not record:
                raise HTTPException(status_code=404, detail="Plan not found")

            views = record.get("metadata", {}).get(params["floor"], [])
            idx = params.get("view_index", -1)
            if idx < 0 or idx >= len(views):
                raise HTTPException(status_code=400, detail="Invalid floor or view_index")

            src = OUTPUT_DIR / views[idx]
            if not src.exists():
                raise HTTPException(status_code=404, detail="Source image not found")

            dest_dir = BASE_DIR / "data" / "jobs" / params["floor_id"] / "selected_output"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / src.name
            shutil.copy(src, dest)
            return str(dest)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def list_exported_images(floor_plan_id: str) -> list[dict]:
        """
        List all images exported for a given floor plan ID.
        """
        try:
            export_dir = BASE_DIR / "data" / "jobs" / floor_plan_id / "selected_output"
            if not export_dir.exists():
                raise HTTPException(status_code=404, detail="Export directory not found")
            return [
                {"image_id": f.stem, "image_name": f.name} for f in export_dir.iterdir()
                if f.suffix.lower() in {'.png', '.jpg', '.jpeg'}
            ]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def get_image_file_by_id(image_id: str) -> FileResponse:
        """
        Serve a previously exported image by its image_id.
        """
        try:
            jobs_dir = BASE_DIR / "data" / "jobs"
            for plan_dir in jobs_dir.iterdir():
                sel_dir = plan_dir / "selected_output"
                if sel_dir.exists():
                    for img in sel_dir.iterdir():
                        if img.stem == image_id:
                            mime, _ = mimetypes.guess_type(str(img))
                            return FileResponse(img, media_type=mime)
            raise HTTPException(status_code=404, detail="Image not found")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def preview(
        file_path: Path,
        keywords: list[str],
        entity_types: set[str],
        dpi: int,
        plan_id: str
    ) -> tuple[dict[str, list[str]], list[str]]:
        """
        Render only floorplan geometry to PNGs under OUTPUT_DIR/floor_pngs_<plan_id>
        without writing to the DB (for preview).
        """
        try:
            doc = ezdxf.readfile(str(file_path))
            msp = doc.modelspace()
            metadata: dict[str, list[str]] = {}
            base_folder = OUTPUT_DIR / f"floor_pngs_{plan_id}"
            base_folder.mkdir(parents=True, exist_ok=True)
            
            def filter_func(e, layer_name=None):
                    ok_geom = e.dxftype() in entity_types
                    if layer_name:
                        ok_geom = ok_geom and getattr(e.dxf, "layer", "") == layer_name
                    return ok_geom
            # ----------------------------- BLOCK PASS ----------------------------------- #
               
            for blk in doc.blocks:
                name_u = blk.name.upper()
                # only render blocks whose UPPER name is in the selected keywords
                if re.fullmatch(r"[A-Za-z]{3,}", name_u) and name_u in keywords:
                    if not any(filter_func(e) for e in blk):
                        continue
                    kw = name_u
                    folder = base_folder / kw
                    folder.mkdir(parents=True, exist_ok=True)

                    out = folder / f"{blk.name}.block-{plan_id}.png"
                    ezplt.qsave(
                        blk,
                        out,
                        dpi=dpi,
                        config=cfg,
                        filter_func=filter_func
                    )
                    DxfController.force_black_on_white(out)
                    metadata.setdefault(kw, []).append(str(out.relative_to(OUTPUT_DIR)))


            # ----------------------------- LAYER PASS ----------------------------------- #
            for lay in doc.layers:
                name_u = lay.dxf.name.upper()
                # only render layers whose UPPER name is in the selected keywords
                if re.fullmatch(r"[A-Za-z]{3,}", name_u) and name_u in keywords:
                    if not any(filter_func(e, lay.dxf.name) for e in msp):
                            continue
                    kw = name_u
                    folder = base_folder / kw
                    folder.mkdir(parents=True, exist_ok=True)

                    out = folder / f"{lay.dxf.name}.layer-{plan_id}.png"
                    ezplt.qsave(
                        msp,
                        out,
                        dpi=dpi,
                        config=cfg,
                        filter_func=lambda e, layer=lay.dxf.name: filter_func(e, layer)
                    )
                    DxfController.force_black_on_white(out)
                    metadata.setdefault(kw, []).append(str(out.relative_to(OUTPUT_DIR)))


            meta_file = base_folder / f"metadata-{plan_id}.json"
            meta_file.write_text(json.dumps(metadata, indent=4))

            rel_paths = [p for paths in metadata.values() for p in paths]
            return metadata, rel_paths
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def extract_keywords(file_path: Path) -> dict[str, list[str]]:
        """
         Scan a DXF for our raw keywords, then split into:
         • all_block_keywords
         • meaningful_block_keywords
         • all_layer_keywords
         • meaningful_layer_keywords
        """
        try:
            doc = ezdxf.readfile(str(file_path))
            msp = doc.modelspace()
           
            block_found: set[str] = set()
            layer_found: set[str] = set()

            # collect all block names
            for blk in doc.blocks:
                nm = blk.name.upper()
                if re.fullmatch(r"[A-Za-z]{3,}", nm):
                    block_found.add(nm) 

            # collect all layer-style names
            layer_names = {lay.dxf.name.upper() for lay in doc.layers}
            entity_layers = {
                getattr(e.dxf, "layer", "").upper()
                for e in msp
                if hasattr(e.dxf, "layer")
            }
            for nm in layer_names.union(entity_layers):
                if re.fullmatch(r"[A-Za-z]{3,}", nm):
                    layer_found.add(nm)

            # sort the raw lists
            all_blocks = sorted(block_found)
            all_layers = sorted(layer_found)

            # use an English dict to pick “real words”
            def is_english(w: str) -> bool:
                # true if word is common enough in English
               return zipf_frequency(w.lower(), 'en') > 3.0

            meaningful_blocks = [w for w in all_blocks if is_english(w)]
            meaningful_layers = [w for w in all_layers if is_english(w)]

            return {
                "all_block_keywords":    all_blocks,
                "meaningful_block_keywords": meaningful_blocks,
                "all_layer_keywords":    all_layers,
                "meaningful_layer_keywords": meaningful_layers,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def extract_entity_types(file_path: Path) -> list[str]:
        """
        Scan the DXF and return a sorted list of every entity.dxftype() it contains,
        both in modelspace and in each block definition.
        """
        try:
            doc = ezdxf.readfile(str(file_path))
            types: set[str] = {e.dxftype() for e in doc.modelspace()}
            for blk in doc.blocks:
                for e in blk:
                    types.add(e.dxftype())
            return sorted(types)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def scan_dxf_for_preview(files: List[UploadFile]):
        """
        Save the uploads to UPLOAD_DIR/temp, then return:
          • file_map: {temp_id: str(path)}
          • kw_args: output of extract_keywords()
          • entity_types: output of extract_entity_types()
        """
        try:
            temp_dir = UPLOAD_DIR / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)

            file_map: dict[str,str] = {}
            for f in files:
                ext = Path(f.filename).suffix
                tid = uuid.uuid4().hex
                p = temp_dir / f"{tid}{ext}"
                p.write_bytes(await f.read())
                file_map[tid] = str(p)

            first = Path(next(iter(file_map.values())))
            kw_args = DxfController.extract_keywords(first)
            entity_types = DxfController.extract_entity_types(first)
            return file_map, kw_args, entity_types
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
