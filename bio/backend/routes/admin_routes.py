import csv
import io
from flask import Blueprint, request, jsonify, Response
from backend.models.schemas import (
    get_dashboard_stats, get_all_users, update_user_status, delete_user,
    get_geofence_settings, update_geofence_settings, get_admin_logs,
    get_credentials_by_user
)
from backend.utils.security import admin_required
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

    updated = update_geofence_settings(
        location_name=location_name,
        latitude=float(lat),
        longitude=float(lon),
        radius_meters=radius_val,
        max_gps_accuracy_meters=float(max_accuracy),
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
