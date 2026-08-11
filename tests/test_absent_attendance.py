import pytest
from backend.config import Config
from backend.app import create_app
from backend.models.schemas import (
    process_daily_absentees, get_user_daily_summary,
    calculate_user_attendance_stats, delete_user
)

@pytest.fixture
def client(tmp_path):
    db_file = tmp_path / "test_absent.db"
    Config.DATABASE_PATH = str(db_file)
    
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client

def test_daily_absent_processing(client):
    delete_user('absent_user_1')

    # Admin Login
    admin_login = client.post('/api/login', json={
        'user_id': 'admin',
        'password': 'Admin@123456'
    })
    assert admin_login.status_code == 200

    # Register user who will not punch
    reg_resp = client.post('/api/register', json={
        'user_id': 'absent_user_1',
        'full_name': 'Absent User Test',
        'email': 'absent1@example.com',
        'phone': '+1999888777',
        'password': 'Password@123'
    })
    assert reg_resp.status_code == 201

    # Trigger absent processing via API
    proc_resp = client.post('/api/admin/process-absent', json={})
    assert proc_resp.status_code == 200
    assert proc_resp.json['success'] is True
    assert proc_resp.json['data']['absent_count'] >= 1

    # Logout Admin & Login as absent_user_1
    client.post('/api/logout')
    login_user = client.post('/api/login', json={
        'user_id': 'absent_user_1',
        'password': 'Password@123'
    })
    assert login_user.status_code == 200

    # Fetch User History
    hist_resp = client.get('/api/user/history')
    assert hist_resp.status_code == 200
    data = hist_resp.json
    assert data['success'] is True
    assert len(data['daily_summary']) >= 1
    
    # Check that daily summary marks status as ABSENT
    latest_day = data['daily_summary'][0]
    assert latest_day['status'] == 'ABSENT'
    assert latest_day['punch_in'] is None
    assert latest_day['periods'][0]['status'] == 'ABSENT'
