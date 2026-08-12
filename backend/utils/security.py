from functools import wraps
# pyrefly: ignore [missing-import]
from flask import session, jsonify, request
# pyrefly: ignore [missing-import]
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    """Returns pbkdf2:sha256 or scrypt password hash."""
    return generate_password_hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verifies a plain text password against a hash."""
    return check_password_hash(hashed, password)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'message': 'Access denied. Administrator privileges required.'}), 403
        return f(*args, **kwargs)
    return decorated_function
