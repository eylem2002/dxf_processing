"""
Configuration Module

Holds global settings for the DXF Floor Plan API, including:
- ezdxf rendering configuration
- filesystem paths for uploads and outputs
- database connection settings
- DXF processing parameters (keywords, blacklist, DPI)
"""

import os
from pathlib import Path
from ezdxf.addons.drawing.config import Configuration

# ---------------------------------------------------------------------------- #
# DXF Rendering Configuration using ezdxf's matplotlib backend
# ---------------------------------------------------------------------------- #
# Set background to white, draw lines in black, and overwrite existing pixels.
cfg = Configuration(
    background_policy="white",
    color_policy="black",
    line_policy="overwrite",
)

config = cfg


# ---------------------------------------------------------------------------- #
# Filesystem Paths
# ---------------------------------------------------------------------------- #
# Base project directory
BASE_DIR = Path(__file__).parent.parent
# Directory to store temporarily uploaded DXF files
UPLOAD_DIR = BASE_DIR / "uploads"
# Directory to save exported floor-plan PNG files
OUTPUT_DIR = BASE_DIR / "floor_pngs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------- #
# Database Configuration
# ---------------------------------------------------------------------------- #
# Read database credentials from environment or use defaults
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "12345678")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_NAME = os.getenv("DB_NAME", "potato")
# Construct SQLAlchemy engine URL for MySQL
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
)

# ---------------------------------------------------------------------------- #
# DXF Processing Parameters
# ---------------------------------------------------------------------------- #
# Keywords to identify floor-related blocks and layers
KEYWORDS = ("GROUND", "FIRST", "SECOND", "THIRD", "FOURTH", "ROOF", "TOP")
# Names to skip entirely
BLACKLIST = ("LEVEL", "TAG")
# Specific layer names to exclude
EXCLUDED_LAYER_NAMES = {"A-ROOF_01", "A-ROOF_02", "A-ROOF_03"}
# DPI resolution for PNG exports
DPI = 150

