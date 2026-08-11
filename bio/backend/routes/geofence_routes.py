from flask import Blueprint, request, jsonify
from backend.models.schemas import get_geofence_settings
from backend.services.geofence import verify_location

geofence_bp = Blueprint('geofence', __name__, url_prefix='/api/location')

@geofence_bp.route('/settings', methods=['GET'])
def get_settings():
    """Returns current active geofence location configuration."""
    settings = get_geofence_settings()
    if not settings:
        return jsonify({'success': False, 'message': 'Geofence settings not initialized.'}), 404
        
    return jsonify({
        'success': True,
        'settings': {
            'location_name': settings['location_name'],
            'latitude': settings['latitude'],
            'longitude': settings['longitude'],
            'radius_meters': settings['radius_meters'],
            'max_gps_accuracy_meters': settings['max_gps_accuracy_meters'],
            'is_demo_mode': bool(settings['is_demo_mode']),
            'updated_at': settings['updated_at']
        }
    })

@geofence_bp.route('/verify', methods=['POST'])
def verify_user_location():
    """Pre-flight check to verify user location status for UI feedback."""
    data = request.get_json() or {}
    lat = data.get('latitude')
    lon = data.get('longitude')
    accuracy = data.get('accuracy')

    if lat is None or lon is None:
        return jsonify({'success': False, 'message': 'Latitude and longitude coordinates are required.'}), 400

    settings = get_geofence_settings()
    result = verify_location(lat, lon, accuracy, settings)

    return jsonify({
        'success': True,
        'result': result
    })
