import math

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
    
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance = EARTH_RADIUS_METERS * c
    return round(distance, 2)

def validate_coordinates(lat: float, lon: float) -> bool:
    """Validates that latitude and longitude are within standard geographical boundaries."""
    if lat is None or lon is None:
        return False
    try:
        lat_val = float(lat)
        lon_val = float(lon)
        return -90.0 <= lat_val <= 90.0 and -180.0 <= lon_val <= 180.0
    except (ValueError, TypeError):
        return False

def verify_location(user_lat: float, user_lon: float, gps_accuracy: float, geofence_settings: dict) -> dict:
    """
    Independently verifies user's physical proximity on the server.
    """
    if not validate_coordinates(user_lat, user_lon):
        return {
            'is_inside': False,
            'status': 'INVALID_COORDINATES',
            'message': 'Provided GPS coordinates are outside valid geographical bounds.',
            'distance_meters': None,
            'required_radius': geofence_settings.get('radius_meters', 100.0)
        }

    center_lat = geofence_settings['latitude']
    center_lon = geofence_settings['longitude']
    radius = geofence_settings['radius_meters']
    is_demo = bool(geofence_settings.get('is_demo_mode', 0))

    distance = calculate_haversine_distance(user_lat, user_lon, center_lat, center_lon)

    # Accuracy check
    max_accuracy = geofence_settings.get('max_gps_accuracy_meters', 200.0)
    if gps_accuracy is not None and gps_accuracy > max_accuracy:
        return {
            'is_inside': False,
            'status': 'GPS_ACCURACY_TOO_LOW',
            'message': f'GPS accuracy ({gps_accuracy:.1f}m) exceeds acceptable maximum threshold ({max_accuracy:.1f}m). Please move to an open area or increase accuracy limit.',
            'distance_meters': distance,
            'required_radius': radius
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
