import csv
import io
# pyrefly: ignore [missing-import]
from flask import Blueprint, request, jsonify, Response, session
from backend.models.schemas import (
    get_dashboard_stats, get_all_users, update_user_status, delete_user,
    get_geofence_settings, update_geofence_settings, get_admin_logs,
    get_credentials_by_user, create_user, get_user_by_id, get_user_by_email,
    update_user_details, process_daily_absentees
)
from backend.utils.security import admin_required, hash_password
from backend.services.geofence import validate_coordinates

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard():
    """Returns overview statistics and recent authentication activity for admin dashboard."""
    stats = get_dashboard_stats()
    recent_logs = get_admin_logs(limit=10)
    settings = get_geofence_settings()

    return jsonify({
        'success': True,
        'stats': stats,
        'recent_activity': recent_logs,
        'geofence': settings
    })

@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """Returns list of registered users with search and filter options."""
    search = request.args.get('search')
    status_filter = request.args.get('status')
    
    users = get_all_users(search_query=search, status_filter=status_filter)
    return jsonify({
        'success': True,
        'users': users
    })

@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_admin_user():
    """Creates a new user account (Admin only)."""
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
        return jsonify({'success': False, 'message': 'User creation failed. Server error.'}), 500

@admin_bp.route('/users/<user_id>/status', methods=['POST'])
@admin_required
def change_user_status(user_id):
    """Activates or deactivates a user account."""
    data = request.get_json() or {}
    new_status = data.get('status', '').lower()

    if new_status not in ['active', 'inactive']:
        return jsonify({'success': False, 'message': 'Invalid status. Must be "active" or "inactive".'}), 400

    success = update_user_status(user_id, new_status)
    if not success:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    return jsonify({
        'success': True,
        'message': f'User "{user_id}" status updated to {new_status}.'
    })

@admin_bp.route('/users/<user_id>', methods=['PUT', 'POST'])
@admin_required
def edit_user_details(user_id):
    """Updates user details such as User ID, full name, email, phone, role, status, and password (Admin only)."""
    data = request.get_json() or {}
    new_user_id = data.get('new_user_id') or data.get('user_id')
    full_name = data.get('full_name')
    email = data.get('email')
    phone = data.get('phone')
    role = data.get('role')
    status = data.get('status')
    password = data.get('password')

    try:
        updated_user = update_user_details(
            user_id=user_id,
            new_user_id=new_user_id,
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            status=status,
            new_password=password
        )
        if not updated_user:
            return jsonify({'success': False, 'message': f'User "{user_id}" not found.'}), 404

        # Synchronize session if admin is updating their own logged-in account
        if session.get('user_id') == user_id or session.get('user_id') == updated_user['user_id']:
            session['user_id'] = updated_user['user_id']
            session['role'] = updated_user['role']
            session['full_name'] = updated_user['full_name']

        return jsonify({
            'success': True,
            'message': f'User account "{updated_user["user_id"]}" updated successfully.',
            'user': {
                'user_id': updated_user['user_id'],
                'full_name': updated_user['full_name'],
                'email': updated_user['email'],
                'phone': updated_user['phone'],
                'role': updated_user['role'],
                'status': updated_user['status']
            }
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to update user: {str(e)}'}), 500

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def remove_user(user_id):
    """Deletes a user account and associated passkeys."""
    if user_id == 'admin':
        return jsonify({'success': False, 'message': 'Default system admin cannot be deleted.'}), 400

    success = delete_user(user_id)
    if not success:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    return jsonify({
        'success': True,
        'message': f'User "{user_id}" has been deleted.'
    })

@admin_bp.route('/geofence', methods=['POST'])
@admin_required
def save_geofence():
    """Updates authorized location center coordinates, radius, and demo mode."""
    data = request.get_json() or {}
    location_name = data.get('location_name', '').strip()
    lat = data.get('latitude')
    lon = data.get('longitude')
    radius = data.get('radius_meters')
    max_accuracy = data.get('max_gps_accuracy_meters', 50.0)
    is_demo = data.get('is_demo_mode', False)

    if not location_name:
        return jsonify({'success': False, 'message': 'Location name is required.'}), 400

    if not validate_coordinates(lat, lon):
        return jsonify({'success': False, 'message': 'Invalid latitude or longitude.'}), 400

    try:
        radius_val = float(radius)
        if radius_val <= 0:
            return jsonify({'success': False, 'message': 'Radius must be greater than 0.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid radius value.'}), 400

    try:
        max_accuracy_val = float(max_accuracy)
    except (ValueError, TypeError):
        max_accuracy_val = 50.0

    updated = update_geofence_settings(
        location_name=location_name,
        latitude=float(lat),
        longitude=float(lon),
        radius_meters=radius_val,
        max_gps_accuracy_meters=max_accuracy_val,
        is_demo_mode=bool(is_demo)
    )

    return jsonify({
        'success': True,
        'message': 'Geofence settings updated successfully.',
        'geofence': updated
    })

@admin_bp.route('/logs', methods=['GET'])
@admin_required
def list_logs():
    """Returns authentication logs with date range, status, and search filters."""
    date_filter = request.args.get('date_filter')
    status_filter = request.args.get('status')
    search = request.args.get('search')
    
    logs = get_admin_logs(date_filter=date_filter, status_filter=status_filter, search=search)
    return jsonify({
        'success': True,
        'logs': logs
    })

@admin_bp.route('/export', methods=['GET'])
@admin_required
def export_csv():
    """Generates and downloads attendance/authentication logs as a CSV file."""
    date_filter = request.args.get('date_filter')
    status_filter = request.args.get('status')
    search = request.args.get('search')

    logs = get_admin_logs(date_filter=date_filter, status_filter=status_filter, search=search, limit=5000)

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write CSV Header
    writer.writerow([
        'Log ID', 'User ID', 'Full Name', 'Email', 'Timestamp',
        'Result', 'Calculated Distance (m)', 'GPS Accuracy (m)',
        'Latitude', 'Longitude', 'Failure Reason', 'Credential ID', 'IP Address'
    ])

    for log in logs:
        writer.writerow([
            log.get('id'),
            log.get('user_id'),
            log.get('full_name', ''),
            log.get('email', ''),
            log.get('timestamp'),
            log.get('result'),
            log.get('calculated_distance'),
            log.get('gps_accuracy'),
            log.get('latitude'),
            log.get('longitude'),
            log.get('failure_reason', ''),
            log.get('credential_id', ''),
            log.get('ip_address', '')
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=authentication_attendance_logs.csv"}
    )

@admin_bp.route('/process-absent', methods=['POST'])
@admin_required
def trigger_process_absent():
    """Manually triggers absent marking for users who did not punch in for target date (default: today)."""
    data = request.get_json() or {}
    target_date = data.get('target_date')
    res = process_daily_absentees(target_date)
    return jsonify({
        'success': True,
        'message': f"Daily attendance processed for {res['target_date']}: {res['present_count']} present, {res['absent_count']} absent ({res['newly_marked_absent']} newly recorded as ABSENT).",
        'data': res
    })

@admin_bp.route('/users/<user_id>/unblock-late', methods=['POST'])
@admin_required
def unblock_late_user(user_id):
    """Admin endpoint to unblock a user blocked due to late punch in."""
    from backend.models.schemas import admin_unblock_late_user
    admin_id = session.get('user_id', 'admin')
    admin_unblock_late_user(user_id, admin_id)
    return jsonify({
        'success': True,
        'message': f"User '{user_id}' has been unblocked by Admin. Account status set to active."
    })

@admin_bp.route('/late-requests', methods=['GET'])
@admin_required
def get_late_requests():
    """Returns list of all late permission slips for admin review."""
    from backend.models.schemas import get_all_pending_late_slips
    slips = get_all_pending_late_slips()
    return jsonify({
        'success': True,
        'slips': slips
    })
