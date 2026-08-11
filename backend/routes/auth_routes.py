# pyrefly: ignore [missing-import]
from flask import Blueprint, request, jsonify, session
from backend.models.schemas import (
    create_user, get_user_by_id, get_user_by_email, get_credentials_by_user,
    calculate_user_attendance_stats, update_user_details, reset_user_password,
    verify_user_phone, update_user_password_direct
)
from backend.utils.security import hash_password, verify_password, login_required, admin_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/register', methods=['POST'])
@admin_required
def register():
    """Register a new user account (Admin only)."""
    data = request.get_json() or {}
    user_id = str(data.get('user_id', '') or '').strip()
    full_name = str(data.get('full_name', '') or '').strip()
    email = str(data.get('email', '') or '').strip()
    phone = str(data.get('phone', '') or '').strip()
    password = str(data.get('password', '') or '').strip()
    role = str(data.get('role', 'user') or 'user').strip().lower()

    if not user_id or not full_name or not email or not phone:
        return jsonify({'success': False, 'message': 'All fields (User ID, Full Name, Email, Phone) are required.'}), 400

    if role not in ['user', 'admin']:
        role = 'user'

    # Default fallback password if none provided
    if not password:
        password = "PasskeyUser@2026"

    if get_user_by_id(user_id):
        return jsonify({'success': False, 'message': f'User ID "{user_id}" is already registered.'}), 400

    if get_user_by_email(email):
        return jsonify({'success': False, 'message': f'Email "{email}" is already registered.'}), 400

    try:
        pw_hash = hash_password(password)
        user = create_user(user_id, full_name, email, phone, pw_hash, role=role, status='active')
        
        return jsonify({
            'success': True,
            'message': f'User account "{user_id}" created successfully by Administrator.',
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
    att_stats = calculate_user_attendance_stats(user['user_id'])

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
            'passkey_count': len(creds),
            'attendance_stats': att_stats
        }
    })

@auth_bp.route('/me', methods=['PUT'])
@login_required
def update_own_profile():
    """Allows the currently authenticated user to update their own profile details (Name, Email, Phone, Password)."""
    current_user_id = session['user_id']
    data = request.get_json() or {}

    full_name = data.get('full_name')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')

    try:
        updated_user = update_user_details(
            user_id=current_user_id,
            full_name=full_name,
            email=email,
            phone=phone,
            new_password=password
        )
        if not updated_user:
            return jsonify({'success': False, 'message': 'User profile not found.'}), 404

        session['full_name'] = updated_user['full_name']

        return jsonify({
            'success': True,
            'message': 'Your profile details have been updated successfully.',
            'user': {
                'user_id': updated_user['user_id'],
                'full_name': updated_user['full_name'],
                'email': updated_user['email'],
                'phone': updated_user['phone'],
                'role': updated_user['role']
            }
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to update profile: {str(e)}'}), 500

@auth_bp.route('/attendance/check/<user_id>', methods=['GET'])
def check_public_attendance(user_id):
    """Public endpoint to check user attendance percentage by User ID or Email on login screen."""
    u_id = str(user_id).strip()
    user = get_user_by_id(u_id)
    if not user:
        user = get_user_by_email(u_id)
    if not user:
        return jsonify({'success': False, 'message': f'User ID / Roll No "{u_id}" not found.'}), 404

    stats = calculate_user_attendance_stats(user['user_id'])
    return jsonify({
        'success': True,
        'user_id': user['user_id'],
        'full_name': user['full_name'],
        'attendance_stats': stats
    })

import random
import time

OTP_STORE = {}

@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    """Generates and sends a 6-digit OTP code to registered user phone number."""
    data = request.get_json() or {}
    user_id_or_email = data.get('user_id', '').strip()
    phone = data.get('phone', '').strip()

    if not user_id_or_email or not phone:
        return jsonify({'success': False, 'message': 'User ID / Email and Phone Number are required.'}), 400

    try:
        user = verify_user_phone(user_id_or_email, phone)
        u_id = user['user_id']
        
        otp_code = f"{random.randint(100000, 999999)}"
        OTP_STORE[u_id] = {
            'otp': otp_code,
            'phone': phone,
            'expires': time.time() + 600  # 10 minutes expiry
        }

        return jsonify({
            'success': True,
            'message': f"OTP sent to {phone}. (Demo 6-Digit OTP: {otp_code})",
            'user_id': u_id,
            'phone': phone,
            'demo_otp': otp_code
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to send OTP. Server error.'}), 500

@auth_bp.route('/verify-otp-reset', methods=['POST'])
def verify_otp_reset():
    """Verifies the 6-digit OTP code and resets user password."""
    data = request.get_json() or {}
    user_id_or_email = data.get('user_id', '').strip()
    otp_input = data.get('otp', '').strip()
    new_password = data.get('new_password', '').strip()

    if not user_id_or_email or not otp_input or not new_password:
        return jsonify({'success': False, 'message': 'User ID, OTP Code, and New Password are required.'}), 400

    user = get_user_by_id(user_id_or_email) or get_user_by_email(user_id_or_email)
    if not user:
        return jsonify({'success': False, 'message': 'User account not found.'}), 404

    u_id = user['user_id']
    otp_record = OTP_STORE.get(u_id)

    if not otp_record or time.time() > otp_record['expires']:
        return jsonify({'success': False, 'message': 'OTP code is invalid or has expired. Please request a new OTP.'}), 400

    if str(otp_record['otp']).strip() != str(otp_input).strip():
        return jsonify({'success': False, 'message': 'Incorrect 6-digit OTP code. Please try again.'}), 400

    try:
        updated_user = update_user_password_direct(u_id, new_password)
        OTP_STORE.pop(u_id, None)

        return jsonify({
            'success': True,
            'message': f"🎉 OTP verified successfully! Password for '{updated_user['user_id']}' has been updated. You can now log in."
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': 'Password update failed. Server error.'}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset account password by verifying User ID/Email and Phone number."""
    data = request.get_json() or {}
    user_id_or_email = data.get('user_id', '').strip()
    phone = data.get('phone', '').strip()
    new_password = data.get('new_password', '').strip()

    if not user_id_or_email or not phone or not new_password:
        return jsonify({'success': False, 'message': 'User ID/Email, Phone Number, and New Password are required.'}), 400

    try:
        updated_user = reset_user_password(user_id_or_email, phone, new_password)
        return jsonify({
            'success': True,
            'message': f"Password for '{updated_user['user_id']}' reset successfully. You can now log in with your new password."
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': 'Password reset failed. Server error.'}), 500
