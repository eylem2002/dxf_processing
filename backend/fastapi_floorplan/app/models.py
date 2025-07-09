"""
Models Module

Defines SQLAlchemy ORM models representing database tables for the DXF
Floor Plan service, plus accompanying Pydantic schemas for request/response validation.
"""
from sqlalchemy import Column, String, Text, JSON, TIMESTAMP, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from pydantic import BaseModel
from typing import List, Set, Optional

# ------------------------------------------------------------------------------
# Base class for all ORM models
# ------------------------------------------------------------------------------
Base = declarative_base()

class FloorPlan(Base):
    """
    FloorPlan ORM Model

    Represents a floor plan record extracted from a DXF file.
    Stores an ID, category keyword, relative image paths, JSON metadata, and timestamp.
    """
    __tablename__ = "floor_plans"

    # Unique identifier for this floor plan (PK)
    id = Column(String(64), primary_key=True)
    # Primary floor category keyword (e.g., 'GROUND')
    keyword = Column(String(64), nullable=True)
    # Comma-separated list of relative PNG paths
    relative_path = Column(Text, nullable=True)
    # JSON blob mapping keywords to lists of image paths
    metadata_json = Column("metadata", JSON, nullable=True)
    # Record creation timestamp
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Relationship to project links (many-to-many via ProjectDxfLink)
    project_links = relationship(
        "ProjectDxfLink", back_populates="floor_plan"
    )

class ProjectDxfLink(Base):
    """
    Association table linking projects to floor plans.
    Implements many-to-many via composite PK (project_id, floor_plan_id).
    """
    __tablename__ = "project_dxf_links"

    # ID of the project (PK, FK to external projects table)
    project_id = Column(String(100), primary_key=True)
    # ID of the linked floor plan (PK, FK to floor_plans.id)
    floor_plan_id = Column(
        String(100), ForeignKey("floor_plans.id"), primary_key=True
    )

    # Back-reference to its FloorPlan
    floor_plan = relationship(
        "FloorPlan", back_populates="project_links"
    )

# ------------------------------------------------------------------------------
# Pydantic schemas for request/response validation
# ------------------------------------------------------------------------------
class ProcessDxfParams(BaseModel):
    # List of layer/block keywords to include (optional)
    # keywords: Optional[List[str]] = None
    # List of substrings to blacklist (optional)
    # blacklist: Optional[List[str]] = None
    # Exact layer names to exclude (optional)
    # excluded_layer_names: Optional[Set[str]] = None
    # DPI for image rendering (optional)
    dpi: Optional[int] = None

class ExportParams(BaseModel):
    # ID of the floor plan
    floor_id: str
    # Category name (keyword) to export
    floor: str
    # Index of the view in the metadata list
    view_index: int

class LinkRequest(BaseModel):
    # Project to link against
    project_id: str
    # Floor plan to link
    floor_plan_id: str

class KeywordNode(BaseModel):
    # Unique identifier for this image node
    id: str
    # Hash of the dataset (floor_plan_id)
    dataset_hash: str
    # Category (keyword) of this entry
    category: str
    # Human-friendly display name ("CATEGORY/CORE_NAME")
    display_name: str
    # Actual filename on disk
    filename: str
    # Relative path to the image file
    path: str

class KeywordTree(BaseModel):
    # Root node name (always "root")
    name: str
    # List of all keyword image nodes
    children: List[KeywordNode]
