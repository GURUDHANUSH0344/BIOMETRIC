import sqlite3
import os
from pathlib import Path
from backend.config import Config

def get_db_connection(db_path=None):
    """Establishes and returns a connection to SQLite database."""
    if db_path is None:
        db_path = Config.DATABASE_PATH
        
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_file), timeout=10.0)
    conn.row_factory = sqlite3.Row
    # Enable foreign key support in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path=None):
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Table: users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        status TEXT NOT NULL DEFAULT 'active',
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table: webauthn_credentials
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS webauthn_credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        credential_id TEXT UNIQUE NOT NULL,
        public_key TEXT NOT NULL,
        sign_count INTEGER NOT NULL DEFAULT 0,
        transports TEXT,
        credential_name TEXT DEFAULT 'SmartDevice Passkey',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Table: geofence_settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS geofence_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        radius_meters REAL NOT NULL,
        max_gps_accuracy_meters REAL NOT NULL DEFAULT 50.0,
        is_demo_mode INTEGER NOT NULL DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table: authentication_logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS authentication_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        latitude REAL,
        longitude REAL,
        gps_accuracy REAL,
        calculated_distance REAL,
        result TEXT NOT NULL,
        failure_reason TEXT,
        credential_id TEXT,
        ip_address TEXT,
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table: late_permission_slips
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS late_permission_slips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        date TEXT NOT NULL,
        in_time TEXT NOT NULL,
        reason TEXT NOT NULL DEFAULT 'Awaiting reason input',
        status TEXT NOT NULL DEFAULT 'PENDING_APPROVAL',
        approved_by TEXT,
        approved_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    # Seed Default Geofence Settings if empty
    cursor.execute("SELECT COUNT(*) FROM geofence_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO geofence_settings (location_name, latitude, longitude, radius_meters, max_gps_accuracy_meters, is_demo_mode)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (
            Config.DEFAULT_LOCATION_NAME,
            Config.DEFAULT_LATITUDE,
            Config.DEFAULT_LONGITUDE,
            Config.DEFAULT_RADIUS_METERS,
            Config.DEFAULT_MAX_GPS_ACCURACY
        ))
        conn.commit()

    conn.close()
