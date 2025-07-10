# ------------------------------------------------------------------------------
# fastapi_controller.py
#
# Defines the FastAPI routes for the DXF Floor Plan Service.
# Responsible for HTTP request parsing, response formatting, and delegating
# all DXF processing, preview, export, metadata, and keyword tasks to
# DxfController or DbController.
#
# Registered Endpoints:
#
# 1. POST   /process_dxf/
#    • Accepts one or more DXF file uploads.
#    • Returns: mapping of temporary IDs to file paths,
#      detected block & layer keywords, and entity types.
#
# 2. POST   /preview_from_selection/
#    • Generates preview PNGs for a given temp DXF and selected filters
#      (keywords, entity types).
#    • Does not persist to DB.
#    • Returns: preview_id, metadata (keyword → image paths), and URLs.
#
# 3. POST   /store_from_selection/
#    • Persists user-selected preview images into the database.
#    • Links the saved floor plan to a project.
#    • Returns: new floor_plan_id.
#
# 4. GET    /floors/{plan_id}
#    • Retrieves stored floor-plan metadata by its plan_id.
#    • Returns: keyword-indexed image metadata and timestamps.
#
# 5. POST   /export/
#    • Copies a selected exported floor-plan image to a job’s
#      selected_output folder.
#    • Returns: absolute path of the copied image.
#
# 6. GET    /floor-plans/{floor_plan_id}/images
#    • Lists all exported images (IDs and filenames) for a given
#      floor_plan_id.
#
# 7. GET    /images/{image_id}
#    • Serves a previously exported image by its unique image_id.
#
# 8. POST   /link_dxf_to_project/
#    • Links an existing floor plan (by floor_plan_id) to a project.
#    • Returns: success message.
#
# 9. GET    /projects/{project_id}/dxfs
#    • Lists all floor plans linked to a given project_id.
#
# 10. GET   /api/keywords/tree
#    • Builds and returns a hierarchical keyword tree of all saved
#      floor-plan images across projects.
#
# 11. POST  /generate_from_selection/
#    • Processes a temp DXF with selected filters and persists result.
#    • Returns: new floor_plan_id.
#
# 12. GET   /extract_keywords/
#    • Scans a temp DXF to list detected block, layer, and entity-layer keywords.
#    • Returns: all_block_keywords, meaningful_block_keywords,
#      all_layer_keywords, meaningful_layer_keywords.
# ------------------------------------------------------------------------------
import re
import uuid
from pathlib import Path
from typing import List
from ezdxf import readfile

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.config import UPLOAD_DIR , DPI
from app.controllers.db_controller import DbController
from app.controllers.dxf_controller import DxfController
from app.models import ExportParams, LinkRequest, KeywordTree
from app.models import KeywordTree 

router = APIRouter()

@router.post("/process_dxf/")
async def upload_file(files: List[UploadFile] = File(...)):
    """
    Handle DXF uploads for preview.
    Delegates saving and initial keyword/entity scan to DxfController.scan_dxf_for_preview().
    """
    try:
        file_map, kw_args, entity_types = await DxfController.scan_dxf_for_preview(files)
        return {
            "temp_files": file_map,
            **kw_args,
            "entity_types": entity_types,
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))


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
        keywords = params.get("keywords", [])
        entity_types = set(params.get("entity_types", []))
        dpi = params.get("dpi", DPI)

        metadata, rel_paths = DxfController.preview(
            file_path=file_path,
            keywords=keywords, 
            entity_types=entity_types,    
            dpi=dpi,
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
        parts = rel.split("/", 2)
        category = parts[1]  
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