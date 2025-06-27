# ------------------------------------------------------------------------------
# DXF Floor Plan API Controller
#
# This module defines the FastAPI routes for interacting with the DXF floor plan
# processing service. It acts as the interface between HTTP clients and the 
# DxfController logic.
#
# Endpoints:
#
# 1. POST /process_dxf/
#    - Description: Uploads a DXF file and optional processing parameters.
#    - Action: Passes file and params to DxfController for processing.
#    - Returns: A generated floor_plan_id.
#
# 2. GET /floors/{plan_id}
#    - Description: Retrieves metadata for a previously processed DXF floor plan.
#    - Returns: Metadata including image paths, floor keywords, and timestamps.
#
# 3. POST /export/
#    - Description: Copies a selected image view from the DXF output.
#    - Action: Exports the specified image to data/jobs/{floor_id}/selected_output.
#    - Returns: Absolute path to the exported image.
#
# 4. GET /floor-plans/{floor_plan_id}/images
#    - Description: Lists all images exported for a given floor_plan_id.
#    - Returns: A list of image metadata (image_id and filename).
#
# 5. GET /images/{image_id}
#    - Description: Serves a previously exported image by its image_id.
#    - Returns: FileResponse with image content (PNG/JPEG).
#
#
# ------------------------------------------------------------------------------


from app.controllers.db_controller import DbController
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Set, Optional
from app.controllers.dxf_controller import DxfController
from fastapi import Query
from app.config import EXCLUDED_LAYER_NAMES, KEYWORDS, BLACKLIST, DPI

router = APIRouter()


class ProcessDxfParams(BaseModel):
    keywords: Optional[List[str]] = None
    blacklist: Optional[List[str]] = None
    excluded_layer_names: Optional[Set[str]] = None
    dpi: Optional[int] = None


class ExportParams(BaseModel):
    floor_id: str
    floor: str
    view_index: int


@router.post("/process_dxf/")
async def process_dxf(
    files: List[UploadFile] = File(...),
    dpi: int = Query(300, description="DPI for rendering, default 300"),
    keywords: Optional[str] = Query(None, description="Comma-separated keywords to include"),
    blacklist: Optional[str] = Query(None, description="Comma-separated blacklist strings"),
    excluded_layer_names: Optional[str] = Query(None, description="Comma-separated layer names to exclude"),
    params: ProcessDxfParams = Depends()
):
    keyword_list = keywords.split(",") if keywords else list(KEYWORDS)
    blacklist_list = blacklist.split(",") if blacklist else list(BLACKLIST)
    excluded_set = set(excluded_layer_names.split(",")) if excluded_layer_names else set(EXCLUDED_LAYER_NAMES)
    
    params = {
        "dpi": dpi,
        "keywords": keyword_list,
        "blacklist": blacklist_list,
        "excluded_layer_names": excluded_set,
    }
    """
    Upload and process a DXF file, return a floor_plan_id.
    """
    try:
        plan_ids = []
        for file in files:
            plan_id = await DxfController.process_request(file, params)
            plan_ids.append(plan_id)  
        return {"floor_plan_ids": plan_ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/floors/{plan_id}")
def get_floors(plan_id: str):
    """
    Retrieve stored floor-plan metadata by its unique ID.
    """
    try:
        return DxfController.get_floor_metadata(plan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/export/")
def export_floor(params: ExportParams):
    """
    Copy a selected floor plan image and return its absolute path.
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
    List all exported floor plan images for a given floor_plan_id.
    """
    try:
        return DxfController.list_exported_images(floor_plan_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/images/{image_id}")
def get_image_by_id(image_id: str):
    """
    Retrieve a specific exported image file by its image_id.
    """
    try:
        return DxfController.get_image_file_by_id(image_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    


class LinkRequest(BaseModel):
    project_id: str
    floor_plan_id: str

@router.post("/link_dxf_to_project/")
def link_dxf_to_project(link: LinkRequest):
    try:
        DbController.link_floor_to_project(link.project_id, link.floor_plan_id)
        return {"message": "Linked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/dxfs")
def get_dxfs_for_project(project_id: str):
    try:
        return DbController.get_project_floorplans(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))