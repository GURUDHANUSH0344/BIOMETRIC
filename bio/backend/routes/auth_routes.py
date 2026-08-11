from flask import Blueprint, request, jsonify, session
from backend.models.schemas import (
    create_user, get_user_by_id, get_user_by_email, get_credentials_by_user
)
from backend.utils.security import hash_password, verify_password, login_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user account."""
    data = request.get_json() or {}
    user_id = data.get('user_id', '').strip()
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()

    if not user_id or not full_name or not email or not phone:
        return jsonify({'success': False, 'message': 'All fields (User ID, Full Name, Email, Phone) are required.'}), 400

    # Default fallback password if none provided
    if not password:
        password = "PasskeyUser@2026"

    if get_user_by_id(user_id):
        return jsonify({'success': False, 'message': f'User ID "{user_id}" is already registered.'}), 400

    if get_user_by_email(email):
        return jsonify({'success': False, 'message': f'Email "{email}" is already registered.'}), 400

    try:
        pw_hash = hash_password(password)
        user = create_user(user_id, full_name, email, phone, pw_hash, role='user', status='active')
        
        # Automatically log user in into session
        session['user_id'] = user['user_id']
        session['role'] = user['role']
        session['full_name'] = user['full_name']

        return jsonify({
            'success': True,
            'message': 'Registration successful. Please proceed to register your device biometric passkey.',
            'user': {
                'user_id': user['user_id'],
                'full_name': user['full_name'],
                'email': user['email'],
                'role': user['role']
            }
        }), 201
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': 'Registration failed. Server error.'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Password login endpoint for users and admins."""
    data = request.get_json() or {}
    user_id_or_email = data.get('user_id', '').strip()
    password = data.get('password', '').strip()

    if not user_id_or_email or not password:
        return jsonify({'success': False, 'message': 'User ID / Email and password are required.'}), 400

    user = get_user_by_id(user_id_or_email)
    if not user:
        user = get_user_by_email(user_id_or_email)

    if not user or not verify_password(password, user['password_hash']):
        return jsonify({'success': False, 'message': 'Invalid credentials.'}), 401

    if user['status'] != 'active':
        return jsonify({'success': False, 'message': 'Account is inactive. Please contact system administrator.'}), 403

    session['user_id'] = user['user_id']
    session['role'] = user['role']
    session['full_name'] = user['full_name']

    return jsonify({
        'success': True,
        'message': 'Login successful.',
        'user': {
            'user_id': user['user_id'],
            'full_name': user['full_name'],
            'email': user['email'],
            'role': user['role']
        }
    })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Clear active user session."""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Returns details of the currently authenticated user in session."""
    if 'user_id' not in session:
        return jsonify({'authenticated': False, 'user': None}), 200

    user = get_user_by_id(session['user_id'])
    if not user or user['status'] != 'active':
        session.clear()
        return jsonify({'authenticated': False, 'user': None}), 200

    creds = get_credentials_by_user(user['user_id'])
    has_passkey = len(creds) > 0

    return jsonify({
        'authenticated': True,
        'user': {
            'user_id': user['user_id'],
            'full_name': user['full_name'],
            'email': user['email'],
            'phone': user['phone'],
            'role': user['role'],
            'status': user['status'],
            'has_passkey': has_passkey,
            'passkey_count': len(creds)
        }
    })
