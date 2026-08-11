import pytest
from backend.services.geofence import (
    calculate_haversine_distance, validate_coordinates, verify_location
)

def test_haversine_same_point():
    """Distance between the same coordinates should be 0 meters."""
    dist = calculate_haversine_distance(13.0827, 80.2707, 13.0827, 80.2707)
    assert dist == 0.0

def test_haversine_known_distance():
    """Distance between two known points (e.g. ~111km for 1 degree lat)."""
    dist = calculate_haversine_distance(13.0, 80.0, 14.0, 80.0)
    assert 110000 < dist < 112000

def test_validate_coordinates():
    assert validate_coordinates(13.0827, 80.2707) is True
    assert validate_coordinates(0, 0) is True
    assert validate_coordinates(-90, 180) is True
    assert validate_coordinates(91, 80) is False
    assert validate_coordinates(13, -181) is False
    assert validate_coordinates(None, 80) is False

def test_verify_location_inside_radius():
    settings = {
        'latitude': 13.0827,
        'longitude': 80.2707,
        'radius_meters': 100.0,
        'max_gps_accuracy_meters': 50.0,
        'is_demo_mode': 0
    }
    # ~20 meters away
    res = verify_location(13.0828, 80.2707, 10.0, settings)
    assert res['is_inside'] is True
    assert res['status'] == 'INSIDE_RADIUS'
    assert res['distance_meters'] <= 100.0

def test_verify_location_outside_radius():
    settings = {
        'latitude': 13.0827,
        'longitude': 80.2707,
        'radius_meters': 100.0,
        'max_gps_accuracy_meters': 50.0,
        'is_demo_mode': 0
    }
    # ~1.1 km away
    res = verify_location(13.0927, 80.2707, 10.0, settings)
    assert res['is_inside'] is False
    assert res['status'] == 'OUTSIDE_RADIUS'
    assert res['distance_meters'] > 100.0

def test_verify_location_low_gps_accuracy():
    settings = {
        'latitude': 13.0827,
        'longitude': 80.2707,
        'radius_meters': 100.0,
        'max_gps_accuracy_meters': 50.0,
        'is_demo_mode': 0
    }
    # Accuracy 120m exceeds max 50m
    res = verify_location(13.0827, 80.2707, 120.0, settings)
    assert res['is_inside'] is False
    assert res['status'] == 'GPS_ACCURACY_TOO_LOW'

def test_verify_location_demo_mode():
    settings = {
        'latitude': 13.0827,
        'longitude': 80.2707,
        'radius_meters': 100.0,
        'max_gps_accuracy_meters': 50.0,
        'is_demo_mode': 1
    }
    # Far away but demo mode is active
    res = verify_location(13.5000, 80.5000, 10.0, settings)
    assert res['is_inside'] is True
    assert res['status'] == 'INSIDE_RADIUS_DEMO'

def test_verify_location_string_inputs():
    settings = {
        'latitude': 13.0827,
        'longitude': 80.2707,
        'radius_meters': 100.0,
        'max_gps_accuracy_meters': 50.0,
        'is_demo_mode': 0
    }
    res = verify_location("13.0828", "80.2707", "10.0", settings)
    assert res['is_inside'] is True
    assert res['status'] == 'INSIDE_RADIUS'

def test_verify_location_none_settings():
    res = verify_location(13.0827, 80.2707, 10.0, None)
    assert res['is_inside'] is False
    assert res['status'] == 'SETTINGS_NOT_FOUND'

