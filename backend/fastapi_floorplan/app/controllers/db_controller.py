# ------------------------------------------------------------
# db_controller.py
# ------------------------------------------------------------
# Module: DbController
# 
# Provides database persistence for DXF floor plans.
# 
# Responsibilities:
#   1. Configure SQLAlchemy engine & session factory
#   2. Ensure ORM models (tables) exist in the database
#   3. Save new floor plan records with metadata
#   4. Retrieve floor plan data by plan ID
#   5. Link floor plans to projects
#   6. List all floor plans associated with a project
#   7. Build a keyword tree of all saved floor-plan images for frontend display
# 
# Public Classes:
#   - DbController: Static methods for database operations
# 
# Dependencies:
#   - sqlalchemy: Core and ORM for database interactions
#   - uuid: To generate unique identifiers for images in keyword tree
# ------------------------------------------------------------
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import SQLALCHEMY_DATABASE_URL
from app.models import Base, FloorPlan, ProjectDxfLink
import uuid
from pathlib import Path

# Create the SQLAlchemy engine (echo=True for SQL logging)
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# Create a configured "SessionLocal" class for database sessions
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Create all tables defined by SQLAlchemy models (if they don’t exist)
Base.metadata.create_all(bind=engine)


class DbController:
    """
    Static methods to interact with the database for floor plan records.
    """

    @staticmethod
    def save_floor_plan_with_id(plan_id: str, keyword: str, relative_paths: list[str], metadata: dict) -> str:
        """
        Insert a new floor plan into the database.

        Args:
            plan_id (str): Unique identifier for the floor plan.
            keyword (str): Primary category keyword for this plan (e.g., 'GROUND').
            relative_paths (list[str]): List of relative PNG file paths.
            metadata (dict): Mapping of keywords to lists of file paths.

        Returns:
            str: The provided plan_id for reference.
        """
        session = SessionLocal()
        fp = FloorPlan(
            id=plan_id,
            keyword=keyword,
            relative_path=",".join(relative_paths),
            metadata_json=metadata
        )
        session.add(fp)
        session.commit()
        session.close()
        return plan_id

    @staticmethod
    def get_floors(plan_id: str) -> dict:
        """
        Retrieve a saved floor plan record by its ID.

        Args:
            plan_id (str): UUID of the floor plan record.

        Returns:
            dict: Floor plan data including id, keyword,
                  paths, metadata, and creation timestamp,
                  or empty dict if not found.
        """
        session = SessionLocal()
        fp = session.query(FloorPlan).filter(FloorPlan.id == plan_id).first()
        session.close()
        if not fp:
            return {}
        return {
            "id": fp.id,
            "keyword": fp.keyword,
            "paths": fp.relative_path.split(","),
            "metadata": fp.metadata_json,
            "created_at": str(fp.created_at)
        }

    @staticmethod
    def link_floor_to_project(project_id: str, plan_id: str):
        """
        Create an association between a floor plan and a project.

        Args:
            project_id (str): Identifier for the project.
            plan_id (str): Identifier for the floor plan.
        """
        session = SessionLocal()
        link = ProjectDxfLink(project_id=project_id, floor_plan_id=plan_id)
        session.add(link)
        session.commit()
        session.close()

    @staticmethod
    def get_project_floorplans(project_id: str) -> list[dict]:
        """
        List all floor plans linked to a given project.

        Args:
            project_id (str): Identifier for the project.

        Returns:
            list[dict]: List of floor plan summaries (id, keyword,
                        paths, created_at).
        """
        session = SessionLocal()
        links = session.query(ProjectDxfLink).filter_by(project_id=project_id).all()
        result = []
        for link in links:
            fp = link.floor_plan
            result.append({
                "id": fp.id,
                "keyword": fp.keyword,
                "paths": fp.relative_path.split(","),
                "created_at": str(fp.created_at),
            })
        session.close()
        return result

    @staticmethod
    def get_all_keywords_tree() -> dict:
        """
        Build a flat tree of all saved floor-plan images,
        suitable for frontend hierarchical display.

        Returns:
            dict: { name: "root", children: [ ... ] }
        """
        session = SessionLocal()
        records = session.query(FloorPlan.id, FloorPlan.metadata_json).all()
        session.close()

        tree: dict = {"name": "root", "children": []}

        for plan_id, metadata in records:
            if not metadata:
                continue
            for category, rel_paths in metadata.items():
                for rel in rel_paths:
                    p = Path(rel)
                    filename = p.name
                    # strip suffix for display
                    core = filename
                    for suf in (f".block-{plan_id}.png", f".layer-{plan_id}.png"):
                        if core.endswith(suf):
                            core = core[:-len(suf)]
                            break
                    display_name = f"{category}/{core}"
                    # generate a unique id per image for frontend use
                    image_id = uuid.uuid4().hex
                    tree["children"].append({
                        "id": image_id,
                        "dataset_hash": plan_id,
                        "category": category,
                        "display_name": display_name,
                        "filename": filename,
                        "path": rel
                    })
        return tree
