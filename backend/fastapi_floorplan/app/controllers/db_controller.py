# ------------------------------------------------------------
# db_controller.py
# ------------------------------------------------------------
# Module: DbController
# Description:
#   - Configures SQLAlchemy engine and session factory
#   - Ensures the `floor_plans` table exists in the MySQL database
#   - Provides methods to save and retrieve floor plan data
# 
# Public Classes:
#   - DbController: Static methods for database operations
# 
# Dependencies:
#   - sqlalchemy: Core and ORM for database interactions
#   - uuid: To generate unique identifiers for floor plans
# 
# Usage:
#   from app.controllers.db_controller import DbController
#   plan_id = DbController.save_floor_plan(keyword, paths, metadata)
#   data = DbController.get_floors(plan_id)
# ------------------------------------------------------------
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import SQLALCHEMY_DATABASE_URL
from app.models import Base, FloorPlan, ProjectDxfLink
import uuid

# Create the SQLAlchemy engine (echo=True for SQL logging)
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# Create a configured "SessionLocal" class for database sessions
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Create all tables defined by SQLAlchemy models (if they don’t exist)
Base.metadata.create_all(bind=engine)


class DbController:
    @staticmethod
    def save_floor_plan_with_id(plan_id: str, keyword: str, relative_paths: list[str], metadata: dict) -> str:
        """
        Save a new floor plan record to the database.

        Args:
            keyword (str): The floor category keyword (e.g., 'GROUND').
            relative_paths (list[str]): List of relative file paths for PNGs.
            metadata (dict): JSON-serializable dict mapping categories to file lists.

        Returns:
            str: Generated UUID for the saved floor plan.
        """
        session = SessionLocal()
        # plan_id = uuid.uuid4().hex
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
        Retrieve floor plan details for a given plan ID.

        Args:
            plan_id (str): UUID of the floor plan record.

        Returns:
            dict: Floor plan data including id, keyword, paths, metadata, and timestamp,
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
        session = SessionLocal()
        link = ProjectDxfLink(project_id=project_id, floor_plan_id=plan_id)
        session.add(link)
        session.commit()
        session.close()

    @staticmethod
    def get_project_floorplans(project_id: str):
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
        session = SessionLocal()
        records = session.query(FloorPlan.metadata_json).all()
        session.close()

        keyword_tree = {}

        for record in records:
            metadata = record[0]  # since `records` is list of tuples
            if not metadata:
                continue
            for keyword, files in metadata.items():
                if keyword not in keyword_tree:
                    keyword_tree[keyword] = set()
                keyword_tree[keyword].update(files)

        # Convert to hierarchical tree format
        tree = {"name": "root", "children": []}
        for keyword, files in keyword_tree.items():
            tree["children"].append({
                "name": keyword,
                "children": list(files)
            })
        return tree
