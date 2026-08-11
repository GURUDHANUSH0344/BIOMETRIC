import os
import pytest
from backend.config import Config
from backend.app import create_app
from backend.database import init_db
from backend.models.schemas import delete_user

@pytest.fixture
def client(tmp_path):
    db_file = tmp_path / "test_geofence_api.db"
    Config.DATABASE_PATH = str(db_file)
    
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client

def test_user_registration_and_login_flow(client):
    # Ensure user does not exist
    delete_user('student01')

    # Register user
    reg_resp = client.post('/api/register', json={
        'user_id': 'student01',
        'full_name': 'John Student',
        'email': 'student01@college.edu',
        'phone': '+1234567890',
        'password': 'StudentPassword@123'
    })
    assert reg_resp.status_code == 201
    assert reg_resp.json['success'] is True

    # Login user
    login_resp = client.post('/api/login', json={
        'user_id': 'student01',
        'password': 'StudentPassword@123'
    })
    assert login_resp.status_code == 200
    assert login_resp.json['success'] is True

    # Check /api/me
    me_resp = client.get('/api/me')
    assert me_resp.status_code == 200
    assert me_resp.json['authenticated'] is True
    assert me_resp.json['user']['user_id'] == 'student01'

def test_admin_protection(client):
    # Unauthenticated admin access should fail 401
    dash_resp = client.get('/api/admin/dashboard')
    assert dash_resp.status_code == 401

    # Login as Admin
    admin_login = client.post('/api/login', json={
        'user_id': 'admin',
        'password': 'Admin@123456'
    })
    assert admin_login.status_code == 200

    # Admin access should succeed 200
    dash_resp = client.get('/api/admin/dashboard')
    assert dash_resp.status_code == 200
    assert dash_resp.json['success'] is True
    assert 'stats' in dash_resp.json
