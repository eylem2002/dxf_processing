from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.controllers.fastapi_controller import router
from fastapi.staticfiles import StaticFiles  

app = FastAPI(title="DXF Floor Plan API")

app.mount("/static", StaticFiles(directory="floor_pngs"), name="static")


origins = [
    "http://localhost:3000", 
   
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          
    allow_credentials=True,
    allow_methods=["*"],              # <-- allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],              # <-- allow all headers
)
# Register the API router from fastapi_controller.py
# This encapsulates all '/process_dxf/' and '/floors/{plan_id}' endpoints
app.include_router(router, tags=["DXF Floor Plans"])

# You can mount static files if you want to serve PNGs directly:
# from fastapi.staticfiles import StaticFiles
# app.mount("/floor_images", StaticFiles(directory="floor_pngs"), name="floor_images")

# Application startup and shutdown events can be added here if needed:
# @app.on_event("startup")
# async def on_startup():
#     ...
#
# @app.on_event("shutdown")
# async def on_shutdown():
#     ...