import math
from typing import Any, Dict, Optional

EARTH_RADIUS_METERS = 6371000.0

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the great-circle distance between two points on the Earth
    specified in decimal degrees using the Haversine formula.
    Returns distance in meters.
    """
    # Convert decimal degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    
    # Clamp a to [0.0, 1.0] to avoid math domain errors due to floating-point imprecision
    a = min(1.0, max(0.0, a))

    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance = EARTH_RADIUS_METERS * c
    return round(distance, 2)

def validate_coordinates(lat: Any, lon: Any) -> bool:
    """Validates that latitude and longitude are within standard geographical boundaries."""
    if lat is None or lon is None:
        return False
    try:
        lat_val = float(lat)
        lon_val = float(lon)
        return -90.0 <= lat_val <= 90.0 and -180.0 <= lon_val <= 180.0
    except (ValueError, TypeError):
        return False

def verify_location(
    user_lat: Any,
    user_lon: Any,
    gps_accuracy: Any = None,
    geofence_settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Independently verifies user's physical proximity on the server.
    """
    if not geofence_settings:
        return {
            'is_inside': False,
            'status': 'SETTINGS_NOT_FOUND',
            'message': 'Geofence settings are not initialized on the server.',
            'distance_meters': None,
            'required_radius': 100.0,
            'is_demo': False
        }

    default_radius = float(geofence_settings.get('radius_meters', 100.0))

    if not validate_coordinates(user_lat, user_lon):
        return {
            'is_inside': False,
            'status': 'INVALID_COORDINATES',
            'message': 'Provided GPS coordinates are outside valid geographical bounds.',
            'distance_meters': None,
            'required_radius': default_radius,
            'is_demo': False
        }

    try:
        user_lat_val = float(user_lat)
        user_lon_val = float(user_lon)
    except (ValueError, TypeError):
        return {
            'is_inside': False,
            'status': 'INVALID_COORDINATES',
            'message': 'Provided GPS coordinates are invalid numbers.',
            'distance_meters': None,
            'required_radius': default_radius,
            'is_demo': False
        }

    accuracy_val = None
    if gps_accuracy is not None:
        try:
            accuracy_val = float(gps_accuracy)
        except (ValueError, TypeError):
            accuracy_val = None

    center_lat = float(geofence_settings['latitude'])
    center_lon = float(geofence_settings['longitude'])
    radius = float(geofence_settings['radius_meters'])
    is_demo = bool(geofence_settings.get('is_demo_mode', 0))

    distance = calculate_haversine_distance(user_lat_val, user_lon_val, center_lat, center_lon)

    # Accuracy check
    max_accuracy = float(geofence_settings.get('max_gps_accuracy_meters', 200.0))
    if accuracy_val is not None and accuracy_val > max_accuracy:
        return {
            'is_inside': False,
            'status': 'GPS_ACCURACY_TOO_LOW',
            'message': f'GPS accuracy ({accuracy_val:.1f}m) exceeds acceptable maximum threshold ({max_accuracy:.1f}m). Please move to an open area or increase accuracy limit.',
            'distance_meters': distance,
            'required_radius': radius,
            'is_demo': is_demo
        }

    if is_demo:
        return {
            'is_inside': True,
            'status': 'INSIDE_RADIUS_DEMO',
            'message': f'[DEMO MODE ACTIVE] Proximity verified (Actual distance: {distance}m, Demo Radius: {radius}m).',
            'distance_meters': distance,
            'required_radius': radius,
            'is_demo': True
        }

    is_inside = (distance <= radius)
    status = 'INSIDE_RADIUS' if is_inside else 'OUTSIDE_RADIUS'
    message = 'Location verified. Inside permitted area.' if is_inside else f'You are outside the permitted area ({distance}m from center, max allowed: {radius}m).'

    return {
        'is_inside': is_inside,
        'status': status,
        'message': message,
        'distance_meters': distance,
        'required_radius': radius,
        'is_demo': False
    }
