"""
DxfController Module

This module handles the full pipeline of extracting and storing floor plan views from DXF files.
It performs the following responsibilities:

1. **DXF Parsing & Filtering**:
   - Loads a DXF file using `ezdxf`, and accesses both its blocks and layers.
   - Filters blocks and layers based on specified `keywords`, `blacklist`, and `excluded_layer_names`.

2. **Image Rendering**:
   - For each valid block or layer, a PNG image is generated using the `ezdxf` matplotlib addon (`ezplt.qsave`).
   - PNG filenames follow the pattern:
     - `BLOCKNAME.block-<floor_plan_id>.png`
     - `LAYERNAME.layer-<floor_plan_id>.png`
   - All images are grouped under a dedicated directory:
     - `floor_pngs_<floor_plan_id>/KEYWORD/`

3. **Deduplication**:
   - Uses MD5 hashing to avoid saving duplicate rendered images.

4. **Metadata Management**:
   - Creates a JSON metadata file named `metadata-<floor_plan_id>.json` inside the floor_pngs folder.
   - Metadata maps each keyword to a list of relative image paths.

5. **Database Integration**:
   - Persists the extracted floor plan record using `DbController.save_floor_plan_with_id(...)`
   - Records include: `plan_id`, primary `keyword`, list of PNG image paths, and full metadata.

6. **API Integration Helpers**:
   - `process_request()`: Asynchronous entry point for FastAPI file uploads.
   - `get_floor_metadata()`: Retrieves metadata by floor plan ID.
   - `export_floor_image()`: Copies a selected image to a `/jobs/.../selected_output` export folder.
   - `list_exported_images()`: Lists exported images for a given floor plan ID.
   - `get_image_file_by_id()`: Retrieves a specific exported image file by filename stem (ID).

Dependencies:
- `ezdxf`, `matplotlib` for rendering
- `hashlib`, `uuid`, `pathlib` for file handling
- `json` for metadata
- `DbController` for database persistence
- `FastAPI`, `UploadFile`, and `FileResponse` for I/O and HTTP interaction
"""

import hashlib
import json,sys
from pathlib import Path
import uuid
import ezdxf
from ezdxf.addons.drawing import matplotlib as ezplt
from app.config import UPLOAD_DIR, KEYWORDS, BLACKLIST, EXCLUDED_LAYER_NAMES, DPI, cfg,OUTPUT_DIR,BASE_DIR
from app.controllers.db_controller import DbController
from fastapi import  UploadFile
import shutil
from typing import List, Set, Optional
from fastapi.responses import FileResponse
import mimetypes



class DxfController:
    """
    DxfController

    Provides methods to process DXF files into categorized floor-plan
    images and save corresponding metadata to the database.
    """

    @staticmethod
    def process(
        file_path: Path,
        keywords: list[str],
        blacklist: list[str],
        excluded_layer_names: set[str],
        dpi: int
    ) -> str:
        """
        Process a DXF file to extract categorized floor plan images and store related metadata.

        Workflow:
        1. Generate a unique floor_plan_id (UUID) to track this processing session.
        2. Create a base output folder named `floor_pngs_<floor_plan_id>`.
        3. Iterate over DXF blocks and layers:
           - Filter using `keywords`, `blacklist`, and `excluded_layer_names`.
           - Render each valid block or layer to a PNG file using ezdxf/ezplt.
           - Name each file with a suffix `-<floor_plan_id>.png` for uniqueness.
           - Skip duplicates using MD5 hash-based deduplication.
        4. Save a metadata JSON file named `metadata-<floor_plan_id>.json` in the same folder.
        5. Persist the floor plan record to the database via `DbController`.

        Args:
            file_path (Path): Path to the uploaded DXF file.
            keywords (list[str]): Keywords to include in filtering (e.g., ["GROUND", "ROOF"]).
            blacklist (list[str]): Names or substrings to exclude from processing.
            excluded_layer_names (set[str]): Exact layer names to skip.
            dpi (int): Image resolution in dots per inch for PNG rendering.

        Returns:
            str: The generated floor_plan_id (UUID) that identifies this floor plan.
        """

        # Load the DXF document
        doc = ezdxf.readfile(str(file_path))
        msp = doc.modelspace()

        exported_hashes: dict[str, str] = {}
        metadata: dict[str, list[str]] = {}
        
        # Save floor plan early to get ID
        plan_id = uuid.uuid4().hex
        base_folder = OUTPUT_DIR / f"floor_pngs_{plan_id}"
        base_folder.mkdir(parents=True, exist_ok=True)

        # ----------------------------- BLOCK PASS ----------------------------------- #
        for blk in doc.blocks:
            name_u = blk.name.upper()
            if any(k in name_u for k in keywords) and not any(b in name_u for b in blacklist):
                keyword = next(k for k in keywords if k in name_u)
                folder = base_folder / keyword
                folder.mkdir(parents=True, exist_ok=True)
                
                png_filename = f"{blk.name}.block-{plan_id}.png"
                png_path = folder / png_filename

                ezplt.qsave(blk, png_path, dpi=dpi, config=cfg)

                file_hash = hashlib.md5(png_path.read_bytes()).hexdigest()
                if file_hash in exported_hashes:
                    png_path.unlink()
                    continue
                exported_hashes[file_hash] = png_path.name
                metadata.setdefault(keyword, []).append(str(png_path.relative_to(OUTPUT_DIR)))

        # ----------------------------- LAYER PASS ----------------------------------- #
        for lay in doc.layers:
            name_u = lay.dxf.name.upper()
            if (
                any(k in name_u for k in keywords)
                and not any(b in name_u for b in blacklist)
                and name_u not in excluded_layer_names
            ):
                keyword = next(k for k in keywords if k in name_u)
                folder = base_folder / keyword
                folder.mkdir(parents=True, exist_ok=True)

                png_filename = f"{lay.dxf.name}.layer-{plan_id}.png"
                png_path = folder / png_filename
                
                ezplt.qsave(
                    msp,
                    png_path,
                    dpi=dpi,
                    config=cfg,
                    filter_func=lambda e, layer=lay.dxf.name: e.dxf.layer == layer
                )

                file_hash = hashlib.md5(png_path.read_bytes()).hexdigest()
                if file_hash in exported_hashes:
                    png_path.unlink()
                    continue
                exported_hashes[file_hash] = png_path.name
                metadata.setdefault(keyword, []).append(str(png_path.relative_to(OUTPUT_DIR)))

        # --------------------------- METADATA FILE --------------------------------- #
        meta_filename = f"metadata-{plan_id}.json"
        meta_file = base_folder / meta_filename
        meta_file.write_text(json.dumps(metadata, indent=4))

        # --------------------------- DATABASE SAVE --------------------------------- #
        primary_keyword = next(iter(metadata))
        relative_paths = [p for paths in metadata.values() for p in paths]
        # Pass the plan_id so DB stores it (since created it earlier)
        DbController.save_floor_plan_with_id(plan_id, primary_keyword, relative_paths, metadata)
        return plan_id
    # --------------------------- API Process ---------------------------------------------#
    @staticmethod
    async def process_request(file: UploadFile, params: dict) -> str:
        temp_path = UPLOAD_DIR / file.filename
        content = await file.read()
        temp_path.write_bytes(content)

        keywords = params.get("keywords") or list(KEYWORDS)
        blacklist = params.get("blacklist") or list(BLACKLIST)
        excluded = params.get("excluded_layer_names") or set(EXCLUDED_LAYER_NAMES)
        dpi_value = params.get("dpi") or DPI

        return DxfController.process(
            temp_path,
            keywords=keywords,
            blacklist=blacklist,
            excluded_layer_names=excluded,
            dpi=dpi_value
        )

    @staticmethod
    def get_floor_metadata(plan_id: str):
        data = DbController.get_floors(plan_id)
        if not data:
            raise ValueError("Plan not found")
        return data

    @staticmethod
    def export_floor_image(params: dict) -> str:
        record = DbController.get_floors(params["floor_id"])
        if not record:
            raise ValueError("Plan not found")

        views = record.get("metadata", {}).get(params["floor"])
        if not views or params["view_index"] < 0 or params["view_index"] >= len(views):
            raise ValueError("Invalid floor or view_index")

        src_path = OUTPUT_DIR / views[params["view_index"]]
        if not src_path.exists():
            raise FileNotFoundError("Source image not found")

        try:
            job_dir = BASE_DIR / "data" / "jobs" / params["floor_id"] / "selected_output"
            job_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Failed to create export directory: {e}")

        dest_path = job_dir / src_path.name

        try:
            shutil.copy(src_path, dest_path)
        except shutil.SameFileError:
            # File already exists and is the same can ignore or log
            pass
        except OSError as e:
            raise RuntimeError(f"Failed to copy image: {e}")

        return str(dest_path)

    @staticmethod
    def list_exported_images(floor_plan_id: str):
        export_dir = BASE_DIR / "data" / "jobs" / floor_plan_id / "selected_output"
        if not export_dir.exists():
            raise FileNotFoundError("Export directory not found")

        image_files = [f for f in export_dir.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]]
        return [
            {
                "image_id": f.stem,
                "image_name": f.name
            } for f in image_files
        ]

    @staticmethod
    def get_image_file_by_id(image_id: str):
        jobs_dir = BASE_DIR / "data" / "jobs"
        for plan_dir in jobs_dir.iterdir():
            selected_output_dir = plan_dir / "selected_output"
            if selected_output_dir.exists():
                for img_file in selected_output_dir.glob("*"):
                    if img_file.stem == image_id:
                        mime_type, _ = mimetypes.guess_type(str(img_file))
                        return FileResponse(img_file, media_type=mime_type)
        raise FileNotFoundError("Image not found")