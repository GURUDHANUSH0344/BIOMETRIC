import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "geofence_biometric_super_secret_key_change_in_production_2026")
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "database" / "geofence_bio.db"))
    
    # WebAuthn Configuration
    WEBAUTHN_RP_ID = os.getenv("WEBAUTHN_RP_ID", "localhost")
    WEBAUTHN_RP_NAME = os.getenv("WEBAUTHN_RP_NAME", "Geo-Fenced Biometric Auth System")
    WEBAUTHN_ORIGIN = os.getenv("WEBAUTHN_ORIGIN", "http://localhost:5000")
    
    # Default Geofence Config
    DEFAULT_LOCATION_NAME = os.getenv("DEFAULT_LOCATION_NAME", "Authorized Campus Site")
    DEFAULT_LATITUDE = float(os.getenv("DEFAULT_LATITUDE", "8.732309"))
    DEFAULT_LONGITUDE = float(os.getenv("DEFAULT_LONGITUDE", "77.723764"))
    DEFAULT_RADIUS_METERS = float(os.getenv("DEFAULT_RADIUS_METERS", "500.0"))
    DEFAULT_MAX_GPS_ACCURACY = float(os.getenv("DEFAULT_MAX_GPS_ACCURACY", "200.0"))
    
    # Admin Seed Credentials
    ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "admin")
    ADMIN_FULL_NAME = os.getenv("ADMIN_FULL_NAME", "System Administrator")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@geofence.local")
    ADMIN_PHONE = os.getenv("ADMIN_PHONE", "+10000000000")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123456")
    
    # Session Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1", "t")
