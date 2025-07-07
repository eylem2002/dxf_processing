# ------------------------------------------------------------------------------
# fastapi_controller.py
#
# Defines the FastAPI routes for the DXF Floor Plan service.
# This module is responsible solely for handling HTTP requests/responses
# and parameter extraction; it delegates all DXF parsing, rendering,
# metadata management, and keyword scanning to DxfController.
#
# Registered endpoints:
#
# 1• POST  /process_dxf/
#     - Upload one or more DXF files for temporary storage.
#     - Returns: Map of temp IDs → file paths, plus available keywords.
#
# 2• POST  /preview_from_selection/
#     - Generate previews (PNG) for a given temp DXF + selected filters.
#     - Returns: preview_id, metadata, and image URLs (no DB write).
#
# 3• POST  /store_from_selection/
#     - Persist user-selected preview images into the DB and link to a project.
#     - Returns: new floor_plan_id.
#
# 4• GET   /floors/{plan_id}
#     - Retrieve metadata for a stored floor plan (images, keyword, timestamp).
#
# 5• POST  /export/
#     - Copy one exported floor-plan image to a “selected_output” job folder.
#     - Returns: absolute path of the copied image.
#
# 6• GET   /floor-plans/{floor_plan_id}/images
#     - List all exported images for a given floor_plan_id (IDs + filenames).
#
# 7• GET   /images/{image_id}
#     - Serve a previously exported image by its unique image_id.
#
# 8• POST  /link_dxf_to_project/
#     - Link an existing floor_plan to a project.
#     - Returns: success message.
#
# 9• GET   /projects/{project_id}/dxfs
#     - List all floor plans linked to a given project_id.
#
# 10• GET   /api/keywords/tree
#     - Build and return a flat “tree” of all saved floor-plan images.
#
# 11• POST  /generate_from_selection/
#     - Process a temp DXF with given keywords/params, save result, and return new ID.
#
# 12• GET   /extract_keywords/
#     - Scan a temp DXF for which KEYWORDS appear (blocks, layers, entity layers).
# ------------------------------------------------------------------------------
import re
import uuid
from pathlib import Path
from typing import List
from ezdxf import readfile

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.config import UPLOAD_DIR, EXCLUDED_LAYER_NAMES, KEYWORDS, BLACKLIST, DPI
from app.controllers.db_controller import DbController
from app.controllers.dxf_controller import DxfController
from app.models import ExportParams, LinkRequest, KeywordTree
from app.models import KeywordTree 

router = APIRouter()

@router.post("/process_dxf/")
async def upload_file(files: List[UploadFile] = File(...)):
    """
    Upload DXF files temporarily, then scan the first file for matching KEYWORDS.
    Delegates file saving and scanning to DxfController.process_request().
    Returns temp file map and available keywords.
    """
    temp_dir = UPLOAD_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    file_map: dict[str,str] = {}
    for f in files:
        ext = Path(f.filename).suffix
        tid = uuid.uuid4().hex
        p = temp_dir / f"{tid}{ext}"
        content = await f.read()
        p.write_bytes(content)
        file_map[tid] = str(p)

    # pick the first file's path
    first_path = Path(next(iter(file_map.values())))

    # now scan that DXF for our keywords
    doc = readfile(str(first_path))
    msp = doc.modelspace()

    # found: set[str] = set()
    block_found: set[str] = set()
    layer_found: set[str] = set()
    # scan blocks
    for blk in doc.blocks:
        #add code to filter only words with reg expression
       if re.fullmatch(r"[A-Za-z]{3,}", blk.name):    # letters only, length ≥ 3
            block_found.add(blk.name)
            
        # found.add(blk)
        # name = blk.name.upper()
        # if any(b in name for b in BLACKLIST):
        #     continue
        # for k in KEYWORDS:
        #     if k in name:
        #         found.add(k)
        # if name in KEYWORDS:
        #     found.add(name)
    # scan layers + entity layers
    layer_names = {lay.dxf.name.upper() for lay in doc.layers}
    entity_layers = {
        getattr(e.dxf, "layer", "").upper()
        for e in msp if hasattr(e.dxf, "layer")
    }
    for nm in layer_names.union(entity_layers):
        if re.fullmatch(r"[A-Za-z]{3,}", nm):    # letters only, length ≥ 3
            layer_found.add(nm)
        # found.add(k)
        # if nm in EXCLUDED_LAYER_NAMES or any(b in nm for b in BLACKLIST):
        #     continue
        # for k in KEYWORDS:
        #     if k in nm:
        #         found.add(k)

    return {
      "temp_files": file_map,
       "block_keywords": sorted(block_found),
       "layer_keywords": sorted(layer_found),
    }

@router.post("/preview_from_selection/")
def preview_from_selection(params: dict):
    """
    Generate preview PNGs from a temp DXF without persisting to the DB.
    Delegates rendering logic to DxfController.preview().
    Returns preview_id, metadata dict, and image URLs for frontend display.
    """
    try:
        preview_id = uuid.uuid4().hex
        file_path = Path(params["temp_path"])

        metadata, rel_paths = DxfController.preview(
            file_path=file_path,
            keywords=params.get("keywords", list(KEYWORDS)),
            blacklist=params.get("blacklist", list(BLACKLIST)),
            excluded_layer_names=set(params.get("excluded_layer_names", EXCLUDED_LAYER_NAMES)),
            dpi=params.get("dpi", DPI),
            plan_id=preview_id
        )

        urls = [f"/static/{p}" for p in rel_paths]
        return {"preview_id": preview_id, "metadata": metadata, "image_urls": urls}

    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.post("/store_from_selection/")
def store_from_selection(params: dict):
    """
    Persist selected preview images into the database and link to a project.
    Calls DbController.save_floor_plan_with_id() and link_floor_to_project().
    Returns the new floor_plan_id.
    """
    pid     = params["preview_id"]
    project = params["project_id"]
    sel     = params["selected_paths"]

    # Group by category = the 2nd segment of the path
    metadata: dict[str, list[str]] = {}
    for rel in sel:
        # rel looks like "floor_pngs_<plan_id>/KEYWORD/…"
        parts = rel.split("/", 2)
        # parts == ["floor_pngs_<plan_id>", "KEYWORD", "rest/of/file.png"]
        category = parts[1]    # ← grab index 1, not 0
        metadata.setdefault(category, []).append(rel)

    primary = next(iter(metadata))
    flat = [p for paths in metadata.values() for p in paths]

    DbController.save_floor_plan_with_id(
        plan_id=pid,
        keyword=primary,
        relative_paths=flat,
        metadata=metadata
    )
    DbController.link_floor_to_project(project, pid)

    return {"floor_plan_id": pid}


@router.get("/floors/{plan_id}")
def get_floors(plan_id: str):
    """
    Retrieve stored floor-plan metadata by plan_id.
    Delegates to DxfController.get_floor_metadata().
    """
    try:
        return DxfController.get_floor_metadata(plan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/export/")
def export_floor(params: ExportParams):
    """
    Copy a selected floor-plan image to the jobs selected_output folder.
    Delegates to DxfController.export_floor_image().
    Returns the absolute exported path.
    """
    try:
        path = DxfController.export_floor_image(params.dict())
        return {"exported_path": path}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/floor-plans/{floor_plan_id}/images")
def list_exported_images(floor_plan_id: str):
    """
    List all exported images (IDs + filenames) for a given floor_plan_id.
    Delegates to DxfController.list_exported_images().
    """
    try:
        return DxfController.list_exported_images(floor_plan_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/images/{image_id}")
def get_image_by_id(image_id: str):
    """
    Serve an exported image by its unique image_id.
    Delegates to DxfController.get_image_file_by_id().
    """
    try:
        return DxfController.get_image_file_by_id(image_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/link_dxf_to_project/")
def link_dxf_to_project(link: LinkRequest):
    """
    Link an existing floor plan to a project.
    Uses DbController.link_floor_to_project().
    """
    try:
        DbController.link_floor_to_project(link.project_id, link.floor_plan_id)
        return {"message": "Linked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/dxfs")
def get_dxfs_for_project(project_id: str):
    """
    Retrieve all floor plans linked to a specific project_id.
    Uses DbController.get_project_floorplans().
    """
    try:
        return DbController.get_project_floorplans(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get(
    "/api/keywords/tree",
    response_model=KeywordTree,
    summary="Get hierarchical list of available keywords"
)
def get_keywords_tree():
    """
    Build and return a flat “tree” of all floor-plan images across saved plans.
    Delegates to DbController.get_all_keywords_tree().
    """
    try:
        return DbController.get_all_keywords_tree()
    except Exception as e:
        raise HTTPException(500, f"Failed to build keyword tree: {e}")
    
    
@router.post("/generate_from_selection/")
def generate_from_selection(params: dict):
    """
    Process a temp DXF with selected filters, persist to DB, and return new ID.
    Delegates to DxfController.process().
    """
    try:
        plan_id = uuid.uuid4().hex
        file_path = Path(params["temp_path"])
        new_plan_id = DxfController.process(
            file_path=file_path,
            keywords=params.get("keywords", list(KEYWORDS)),
            blacklist=params.get("blacklist", list(BLACKLIST)),
            excluded_layer_names=set(params.get("excluded_layer_names", EXCLUDED_LAYER_NAMES)),
            dpi=params.get("dpi", DPI),
            plan_id=plan_id
        )
        return {"floor_plan_id": new_plan_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extract_keywords/")
def extract_keywords(temp_path: str):
    """
    Scan a temp DXF for which KEYWORDS appear (blocks, layers, entity layers).
    Delegates to DxfController.extract_keywords().
    """
    try:
        # Delegate the scanning logic to DxfController.extract_keywords()
        return DxfController.extract_keywords(Path(temp_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))