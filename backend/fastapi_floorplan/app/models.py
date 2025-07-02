"""
Models Module

Defines SQLAlchemy ORM models representing database tables for the DXF
Floor Plan service. Includes the `FloorPlan` class mapping to the `floor_plans`
table, storing image metadata in a JSON column.
"""
from sqlalchemy import Column, String, Text, JSON, TIMESTAMP
from sqlalchemy.orm import declarative_base
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import List, Set, Optional
# Base class for all ORM models
Base = declarative_base()

class FloorPlan(Base):
    """
    FloorPlan ORM Model

    Represents a floor plan record extracted from a DXF file.
    Stores a unique ID, category keyword, relative image paths,
    JSON metadata, and creation timestamp.
    """
    __tablename__ = "floor_plans"
    id = Column(String(64), primary_key=True)
    keyword = Column(String(64), nullable=True)
    relative_path = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)  
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    project_links = relationship("ProjectDxfLink", back_populates="floor_plan")




class ProjectDxfLink(Base):
    __tablename__ = "project_dxf_links"

    project_id = Column(String(100), primary_key=True)
    floor_plan_id = Column(String(100), ForeignKey("floor_plans.id"), primary_key=True)

    floor_plan = relationship("FloorPlan", back_populates="project_links")
    
class ProcessDxfParams(BaseModel):
    keywords: Optional[List[str]] = None
    blacklist: Optional[List[str]] = None
    excluded_layer_names: Optional[Set[str]] = None
    dpi: Optional[int] = None


class ExportParams(BaseModel):
    floor_id: str
    floor: str
    view_index: int
    
    
class LinkRequest(BaseModel):
    project_id: str
    floor_plan_id: str
    
    
class KeywordNode(BaseModel):
    dataset_hash: str    # the floor_plan_id
    category: str        # "ROOF"
    display_name: str    # "ROOF/A-ROOF 04"
    filename: str        # "A-ROOF 04.layer-…png"
    path: str            # the relative path in the output dir

class KeywordTree(BaseModel):
    name: str
    children: List[KeywordNode]