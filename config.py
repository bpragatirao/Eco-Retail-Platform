"""
Centralized configuration for the Eco-Retail Platform.
All paths, database URLs, and constants are managed here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODEL_DIR = BASE_DIR / "ml"
DASHBOARD_DIR = BASE_DIR / "dashboard" / "static"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# ── Database ─────────────────────────────────────────────────────────────────
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "retail")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
SQLITE_PATH = os.getenv("SQLITE_PATH", "data/eco_retail.db")


def get_database_url() -> str:
    """Build the database URL based on DB_TYPE."""
    if DB_TYPE == "sqlite":
        return f"sqlite:///{BASE_DIR / SQLITE_PATH}"
    return (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )


DATABASE_URL = get_database_url()

# ── Application ──────────────────────────────────────────────────────────────
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── API ──────────────────────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# ── ML Constants ─────────────────────────────────────────────────────────────
MODEL_FILENAME = "demand_model.pkl"
MODEL_PATH = MODEL_DIR / MODEL_FILENAME

# ── Pricing Constants ────────────────────────────────────────────────────────
MAX_DISCOUNT = 0.50          # 50% max discount cap
CRITICAL_EXPIRY_DAYS = 3     # Days threshold for urgent pricing
WARNING_EXPIRY_DAYS = 7      # Days threshold for warning-level pricing
MIN_MARGIN = 0.10            # Minimum margin to maintain (10%)
