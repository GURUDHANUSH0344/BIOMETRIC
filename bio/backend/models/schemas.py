import sqlite3
from backend.database import get_db_connection
from backend.utils.serializers import row_to_dict, rows_to_list

# User Model Operations
def create_user(user_id: str, full_name: str, email: str, phone: str, password_hash: str, role: str = 'user', status: str = 'active') -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (user_id, full_name, email, phone, role, status, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id.strip(), full_name.strip(), email.strip().lower(), phone.strip(), role, status, password_hash))
        conn.commit()
        return get_user_by_id(user_id)
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError("User ID or Email already exists.") from e
    finally:
        conn.close()

def get_user_by_id(user_id: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id.strip(),))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)

def get_user_by_email(email: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)

def get_all_users(search_query: str = None, status_filter: str = None) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT u.id, u.user_id, u.full_name, u.email, u.phone, u.role, u.status, u.created_at, u.updated_at,
               COUNT(c.id) as credential_count,
               MAX(l.timestamp) as last_auth_time
        FROM users u
        LEFT JOIN webauthn_credentials c ON u.user_id = c.user_id
        LEFT JOIN authentication_logs l ON u.user_id = l.user_id AND l.result = 'SUCCESS'
        WHERE 1=1
    """
    params = []
    
    if search_query:
        query += " AND (u.full_name LIKE ? OR u.email LIKE ? OR u.user_id LIKE ? OR u.phone LIKE ?)"
        pattern = f"%{search_query.strip()}%"
        params.extend([pattern, pattern, pattern, pattern])
        
    if status_filter and status_filter.lower() != 'all':
        query += " AND u.status = ?"
        params.append(status_filter.lower())
        
    query += " GROUP BY u.id ORDER BY u.created_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows_to_list(rows)

def update_user_status(user_id: str, status: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (status, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def delete_user(user_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# WebAuthn Credentials Model Operations
def create_credential(user_id: str, credential_id: str, public_key: str, sign_count: int = 0, credential_name: str = "SmartDevice Passkey") -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO webauthn_credentials (user_id, credential_id, public_key, sign_count, credential_name)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, credential_id, public_key, sign_count, credential_name))
    conn.commit()
    cred_id = cursor.lastrowid
    cursor.execute("SELECT * FROM webauthn_credentials WHERE id = ?", (cred_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)

def get_credentials_by_user(user_id: str) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM webauthn_credentials WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows_to_list(rows)

def get_credential_by_id(credential_id: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM webauthn_credentials WHERE credential_id = ?", (credential_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)

def update_credential_sign_count(credential_id: str, new_sign_count: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE webauthn_credentials
        SET sign_count = ?, last_used_at = CURRENT_TIMESTAMP
        WHERE credential_id = ?
    """, (new_sign_count, credential_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# Geofence Settings Model Operations
def get_geofence_settings() -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM geofence_settings ORDER BY id ASC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)

def update_geofence_settings(location_name: str, latitude: float, longitude: float, radius_meters: float, max_gps_accuracy_meters: float = 50.0, is_demo_mode: bool = False) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM geofence_settings ORDER BY id ASC LIMIT 1")
    row = cursor.fetchone()
    
    demo_val = 1 if is_demo_mode else 0
    if row:
        cursor.execute("""
            UPDATE geofence_settings
            SET location_name = ?, latitude = ?, longitude = ?, radius_meters = ?, max_gps_accuracy_meters = ?, is_demo_mode = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (location_name.strip(), latitude, longitude, radius_meters, max_gps_accuracy_meters, demo_val, row['id']))
    else:
        cursor.execute("""
            INSERT INTO geofence_settings (location_name, latitude, longitude, radius_meters, max_gps_accuracy_meters, is_demo_mode)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (location_name.strip(), latitude, longitude, radius_meters, max_gps_accuracy_meters, demo_val))
        
    conn.commit()
    conn.close()
    return get_geofence_settings()


# Authentication Logs Model Operations
def log_authentication_event(user_id: str, latitude: float, longitude: float, gps_accuracy: float, calculated_distance: float, result: str, failure_reason: str = None, credential_id: str = None, ip_address: str = None, user_agent: str = None) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO authentication_logs (user_id, latitude, longitude, gps_accuracy, calculated_distance, result, failure_reason, credential_id, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, latitude, longitude, gps_accuracy, calculated_distance, result, failure_reason, credential_id, ip_address, user_agent))
    conn.commit()
    log_id = cursor.lastrowid
    cursor.execute("SELECT * FROM authentication_logs WHERE id = ?", (log_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)

def get_user_logs(user_id: str, limit: int = 100) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM authentication_logs
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows_to_list(rows)

def get_admin_logs(date_filter: str = None, status_filter: str = None, search: str = None, limit: int = 500) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT l.*, u.full_name, u.email
        FROM authentication_logs l
        LEFT JOIN users u ON l.user_id = u.user_id
        WHERE 1=1
    """
    params = []
    
    if date_filter == 'today':
        query += " AND DATE(l.timestamp) = DATE('now')"
    elif date_filter == 'yesterday':
        query += " AND DATE(l.timestamp) = DATE('now', '-1 day')"
    elif date_filter == 'last_7_days':
        query += " AND DATE(l.timestamp) >= DATE('now', '-7 days')"
    elif date_filter == 'last_30_days':
        query += " AND DATE(l.timestamp) >= DATE('now', '-30 days')"

    if status_filter and status_filter.lower() != 'all':
        query += " AND l.result = ?"
        params.append(status_filter.upper())

    if search:
        query += " AND (u.full_name LIKE ? OR u.email LIKE ? OR l.user_id LIKE ?)"
        pattern = f"%{search.strip()}%"
        params.extend([pattern, pattern, pattern])

    query += " ORDER BY l.timestamp DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows_to_list(rows)

def get_dashboard_stats() -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'user'")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'user' AND status = 'active'")
    active_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM authentication_logs WHERE DATE(timestamp) = DATE('now') AND result = 'SUCCESS'")
    today_success = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM authentication_logs WHERE DATE(timestamp) = DATE('now') AND result != 'SUCCESS'")
    today_failed = cursor.fetchone()[0]

    # Users whose last logged position today was inside the radius and successful
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id) FROM authentication_logs
        WHERE DATE(timestamp) = DATE('now') AND result = 'SUCCESS'
    """)
    users_inside_today = cursor.fetchone()[0]

    conn.close()
    return {
        'total_users': total_users,
        'active_users': active_users,
        'today_success': today_success,
        'today_failed': today_failed,
        'users_inside_today': users_inside_today
    }
