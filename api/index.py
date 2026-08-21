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

try:
    from backend.app import app
except Exception as e:
    import traceback
    error_details = traceback.format_exc()
    print(f"[VERCEL STARTUP ERROR]\n{error_details}", file=sys.stderr)
    # pyrefly: ignore [missing-import]
    from flask import Flask, jsonify
    app = Flask(__name__)
    @app.route('/')
    @app.route('/<path:path>')
    def error_fallback(path=""):
        return jsonify({
            'success': False,
            'error': 'Serverless Initialization Exception',
            'details': str(e),
            'traceback': error_details
        }), 500

# Vercel WSGI entrypoint
app = app

