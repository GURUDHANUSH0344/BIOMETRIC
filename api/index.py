import sys
import os
from pathlib import Path

# Add project root directory to python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Handle writable database in Vercel serverless environment (/tmp)
if os.getenv("VERCEL"):
    from backend.config import Config
    Config.DATABASE_PATH = "/tmp/geofence_bio.db"

from backend.app import app

# Vercel WSGI entrypoint
app = app
