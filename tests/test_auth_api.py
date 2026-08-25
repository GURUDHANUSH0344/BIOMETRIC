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

    # Unauthenticated registration should fail (401)
    unauth_resp = client.post('/api/register', json={
        'user_id': 'student01',
        'full_name': 'John Student',
        'email': 'student01@college.edu',
        'phone': '+1234567890',
        'password': 'StudentPassword@123'
    })
    assert unauth_resp.status_code == 401

    # Login as Admin first
    admin_login = client.post('/api/login', json={
        'user_id': 'admin',
        'password': 'Admin@123456'
    })
    assert admin_login.status_code == 200

    # Admin registers user
    reg_resp = client.post('/api/register', json={
        'user_id': 'student01',
        'full_name': 'John Student',
        'email': 'student01@college.edu',
        'phone': '+1234567890',
        'password': 'StudentPassword@123'
    })
    assert reg_resp.status_code == 201
    assert reg_resp.json['success'] is True

    # Logout Admin
    client.post('/api/logout')

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

def test_admin_user_creation_endpoint(client):
    delete_user('student02')

    # Unauthenticated POST /api/admin/users should fail (401)
    unauth_resp = client.post('/api/admin/users', json={
        'user_id': 'student02',
        'full_name': 'Jane Student',
        'email': 'student02@college.edu',
        'phone': '+1987654321',
        'password': 'StudentPassword@456'
    })
    assert unauth_resp.status_code == 401

    # Login as Admin
    client.post('/api/login', json={'user_id': 'admin', 'password': 'Admin@123456'})

    # Authenticated Admin POST /api/admin/users should succeed (201)
    admin_resp = client.post('/api/admin/users', json={
        'user_id': 'student02',
        'full_name': 'Jane Student',
        'email': 'student02@college.edu',
        'phone': '+1987654321',
        'password': 'StudentPassword@456'
    })
    assert admin_resp.status_code == 201
    assert admin_resp.json['success'] is True
    assert admin_resp.json['user']['user_id'] == 'student02'

def test_admin_user_editing_endpoint(client):
    delete_user('student03')

    # Login as Admin
    client.post('/api/login', json={'user_id': 'admin', 'password': 'Admin@123456'})

    # Create user
    client.post('/api/admin/users', json={
        'user_id': 'student03',
        'full_name': 'Original Name',
        'email': 'original@college.edu',
        'phone': '+1111111111',
        'password': 'OriginalPassword@123'
    })

    # Logout Admin
    client.post('/api/logout')

    # Unauthenticated PUT /api/admin/users/student03 should fail (401)
    unauth_edit = client.put('/api/admin/users/student03', json={'full_name': 'Hacked Name'})
    assert unauth_edit.status_code == 401

    # Login as Admin again
    client.post('/api/login', json={'user_id': 'admin', 'password': 'Admin@123456'})

    # Admin updates user details (including User ID)
    edit_resp = client.put('/api/admin/users/student03', json={
        'new_user_id': 'student03_renamed',
        'full_name': 'Updated Name',
        'email': 'updated@college.edu',
        'phone': '+9999999999'
    })
    assert edit_resp.status_code == 200
    assert edit_resp.json['success'] is True
    assert edit_resp.json['user']['user_id'] == 'student03_renamed'
    assert edit_resp.json['user']['full_name'] == 'Updated Name'
    assert edit_resp.json['user']['email'] == 'updated@college.edu'
    
    # Cleanup
    delete_user('student03_renamed')

def test_check_public_attendance_endpoint(client):
    # Public attendance lookup for admin
    resp = client.get('/api/attendance/check/admin')
    assert resp.status_code == 200
    assert resp.json['success'] is True
    assert 'attendance_stats' in resp.json
    assert 'attendance_percentage' in resp.json['attendance_stats']

def test_admin_user_editing_validation_and_status(client):
    delete_user('student04')
    delete_user('student05')

    # Login as Admin
    client.post('/api/login', json={'user_id': 'admin', 'password': 'Admin@123456'})

    # Create two test users
    client.post('/api/admin/users', json={
        'user_id': 'student04',
        'full_name': 'Student Four',
        'email': 'student04@college.edu',
        'phone': '+1000000004'
    })
    client.post('/api/admin/users', json={
        'user_id': 'student05',
        'full_name': 'Student Five',
        'email': 'student05@college.edu',
        'phone': '+1000000005'
    })

    # Update student04 with status inactive and new role admin
    edit_resp = client.put('/api/admin/users/student04', json={
        'full_name': 'Student Four Updated',
        'status': 'inactive',
        'role': 'admin'
    })
    assert edit_resp.status_code == 200
    assert edit_resp.json['success'] is True
    assert edit_resp.json['user']['status'] == 'inactive'
    assert edit_resp.json['user']['role'] == 'admin'

    # Duplicate email attempt should fail (400)
    dup_email = client.put('/api/admin/users/student04', json={'email': 'student05@college.edu'})
    assert dup_email.status_code == 400
    assert 'already registered' in dup_email.json['message']

    # Duplicate user_id attempt should fail (400)
    dup_id = client.put('/api/admin/users/student04', json={'new_user_id': 'student05'})
    assert dup_id.status_code == 400
    assert 'already registered' in dup_id.json['message']

    # Empty full name attempt should fail (400)
    empty_name = client.put('/api/admin/users/student04', json={'full_name': '   '})
    assert empty_name.status_code == 400
    assert 'cannot be empty' in empty_name.json['message']

    # Attempting to change system admin User ID should fail (400)
    admin_id_change = client.put('/api/admin/users/admin', json={'new_user_id': 'superadmin'})
    assert admin_id_change.status_code == 400
    assert 'Default system admin User ID cannot be changed' in admin_id_change.json['message']

    # Cleanup
    delete_user('student04')
    delete_user('student05')

def test_admin_user_full_details_and_password_reset(client):
    delete_user('detail_user')

    # Admin Login & Create user
    client.post('/api/login', json={'user_id': 'admin', 'password': 'Admin@123456'})
    client.post('/api/admin/users', json={
        'user_id': 'detail_user',
        'full_name': 'Detail User Test',
        'email': 'detail_user@example.com',
        'phone': '+1999222333',
        'password': 'InitialPassword@123'
    })

    # Fetch full user details
    detail_resp = client.get('/api/admin/users/detail_user')
    assert detail_resp.status_code == 200
    assert detail_resp.json['success'] is True
    data = detail_resp.json['data']
    assert data['user']['user_id'] == 'detail_user'
    assert 'credentials' in data
    assert 'attendance_stats' in data
    assert 'today_punch' in data
    assert 'recent_logs' in data

    # Admin resets user password
    reset_resp = client.post('/api/admin/users/detail_user/reset-password', json={
        'new_password': 'AdminAssignedPassword@789'
    })
    assert reset_resp.status_code == 200
    assert reset_resp.json['success'] is True

    # User can login with newly assigned password
    client.post('/api/logout')
    login_resp = client.post('/api/login', json={
        'user_id': 'detail_user',
        'password': 'AdminAssignedPassword@789'
    })
    assert login_resp.status_code == 200

    # User changes own password
    change_resp = client.post('/api/me/change-password', json={
        'current_password': 'AdminAssignedPassword@789',
        'new_password': 'UserNewPassword@999'
    })
    assert change_resp.status_code == 200
    assert change_resp.json['success'] is True

    # Cleanup
    delete_user('detail_user')

def test_admin_user_filtering_and_sorting(client):
    delete_user('sort_user_a')
    delete_user('sort_user_b')

    # Admin Login
    client.post('/api/login', json={'user_id': 'admin', 'password': 'Admin@123456'})

    client.post('/api/admin/users', json={
        'user_id': 'sort_user_a',
        'full_name': 'Alpha User',
        'email': 'alpha@example.com',
        'phone': '+1111111111',
        'role': 'user'
    })
    client.post('/api/admin/users', json={
        'user_id': 'sort_user_b',
        'full_name': 'Beta Admin',
        'email': 'beta@example.com',
        'phone': '+2222222222',
        'role': 'admin'
    })

    # Filter by role admin
    role_resp = client.get('/api/admin/users?role=admin')
    assert role_resp.status_code == 200
    admin_ids = [u['user_id'] for u in role_resp.json['users']]
    assert 'sort_user_b' in admin_ids
    assert 'sort_user_a' not in admin_ids

    # Search by keyword
    search_resp = client.get('/api/admin/users?search=Alpha')
    assert search_resp.status_code == 200
    assert len(search_resp.json['users']) == 1
    assert search_resp.json['users'][0]['user_id'] == 'sort_user_a'

    # Cleanup
    delete_user('sort_user_a')
    delete_user('sort_user_b')

def test_user_self_profile_editing(client):
    delete_user('student06')

    # Admin creates student06
    client.post('/api/login', json={'user_id': 'admin', 'password': 'Admin@123456'})
    client.post('/api/admin/users', json={
        'user_id': 'student06',
        'full_name': 'Student Six Original',
        'email': 'student06@college.edu',
        'phone': '+1000000006',
        'password': 'Password@123'
    })
    client.post('/api/logout')

    # Login as student06
    login_resp = client.post('/api/login', json={'user_id': 'student06', 'password': 'Password@123'})
    assert login_resp.status_code == 200

    # User attempting to update own profile details via PUT /api/me should be blocked (403)
    update_resp = client.put('/api/me', json={
        'full_name': 'Student Six Updated Self',
        'email': 'student06_self@college.edu',
        'phone': '+1999888777'
    })
    assert update_resp.status_code == 403
    assert update_resp.json['success'] is False
    assert 'Only administrators are authorized' in update_resp.json['message']

    # Admin updates student06 profile via admin endpoint
    client.post('/api/logout')
    client.post('/api/login', json={'user_id': 'admin', 'password': 'Admin@123456'})
    admin_update_resp = client.put('/api/admin/users/student06', json={
        'full_name': 'Student Six Admin Updated',
        'email': 'student06_admin@college.edu',
        'phone': '+1999888777'
    })
    assert admin_update_resp.status_code == 200
    assert admin_update_resp.json['success'] is True

    # Cleanup
    delete_user('student06')

def test_punch_in_and_punch_out_tracking(client):
    from backend.models.schemas import log_authentication_event, get_user_punch_info_today, get_user_daily_summary
    
    delete_user('student07')

    # Admin creates student07
    client.post('/api/login', json={'user_id': 'admin', 'password': 'Admin@123456'})
    client.post('/api/admin/users', json={
        'user_id': 'student07',
        'full_name': 'Student Seven',
        'email': 'student07@college.edu',
        'phone': '+1000000007',
        'password': 'Password@123'
    })

    # Before any punch
    p_info0 = get_user_punch_info_today('student07')
    assert p_info0['next_punch_type'] == 'PUNCH_IN'
    assert p_info0['punch_in'] is None
    assert p_info0['punch_out'] is None

    # First biometric punch (PUNCH_IN)
    log_authentication_event('student07', 13.0, 80.0, 10.0, 5.0, 'SUCCESS')

    p_info1 = get_user_punch_info_today('student07')
    assert p_info1['next_punch_type'] == 'PUNCH_OUT'
    assert p_info1['punch_in'] is not None
    assert p_info1['punch_out'] is None
    assert p_info1['punch_count'] == 1

    # Second biometric punch (PUNCH_OUT)
    log_authentication_event('student07', 13.0, 80.0, 10.0, 5.0, 'SUCCESS')

    p_info2 = get_user_punch_info_today('student07')
    assert p_info2['next_punch_type'] == 'PUNCH_OUT'
    assert p_info2['punch_in'] is not None
    assert p_info2['punch_out'] is not None
    assert p_info2['punch_count'] == 2

    # Check daily summary & period calculation
    summary = get_user_daily_summary('student07')
    assert len(summary) >= 1
    assert summary[0]['punch_in'] is not None
    assert summary[0]['punch_out'] is not None

    # Verify first 4 periods are PRESENT upon Punch IN
    periods = summary[0]['periods']
    assert len(periods) == 7
    assert periods[0]['status'] == 'PRESENT'  # P1
    assert periods[1]['status'] == 'PRESENT'  # P2
    assert periods[2]['status'] == 'PRESENT'  # P3
    assert periods[3]['status'] == 'PRESENT'  # P4

    # Cleanup
    delete_user('student07')

def test_period_attendance_rules(client):
    from backend.models.schemas import calculate_periods_status

    # Punch IN only (No Punch OUT)
    res1 = calculate_periods_status('2026-08-10 09:05:00', None)
    assert res1[0]['status'] == 'PRESENT'  # P1
    assert res1[1]['status'] == 'PRESENT'  # P2
    assert res1[2]['status'] == 'PRESENT'  # P3
    assert res1[3]['status'] == 'PRESENT'  # P4
    assert res1[4]['status'] == 'ABSENT'   # P5 (requires Punch OUT)
    assert res1[5]['status'] == 'ABSENT'   # P6
    assert res1[6]['status'] == 'ABSENT'   # P7

    # Punch OUT at 14:15 (02:15 PM) -> P5 (13:20) & P6 (14:10) PRESENT, P7 (15:15) ABSENT
    res2 = calculate_periods_status('2026-08-10 09:05:00', '2026-08-10 14:15:00')
    assert res2[0]['status'] == 'PRESENT'  # P1
    assert res2[1]['status'] == 'PRESENT'  # P2
    assert res2[2]['status'] == 'PRESENT'  # P3
    assert res2[3]['status'] == 'PRESENT'  # P4
    assert res2[4]['status'] == 'PRESENT'  # P5
    assert res2[5]['status'] == 'PRESENT'  # P6
    assert res2[6]['status'] == 'ABSENT'   # P7 (15:15 PM)

    # Punch OUT at 16:10 (04:10 PM) -> All 7 periods PRESENT
    res3 = calculate_periods_status('2026-08-10 09:05:00', '2026-08-10 16:10:00')
    assert all(p['status'] == 'PRESENT' for p in res3)

def test_forgot_password_reset_flow(client):
    delete_user('reset_test_user')

    # Admin Login & Create user
    client.post('/api/login', json={'user_id': 'admin', 'password': 'Admin@123456'})
    client.post('/api/register', json={
        'user_id': 'reset_test_user',
        'full_name': 'Reset Test',
        'email': 'reset_test@example.com',
        'phone': '+19876543210',
        'password': 'OldPassword@123'
    })
    client.post('/api/logout')

    # Reset password with incorrect phone should fail
    fail_resp = client.post('/api/reset-password', json={
        'user_id': 'reset_test_user',
        'phone': '+10000000000',
        'new_password': 'NewPassword@456'
    })
    assert fail_resp.status_code == 400

    # Reset password with correct phone should succeed
    succ_resp = client.post('/api/reset-password', json={
        'user_id': 'reset_test_user',
        'phone': '+19876543210',
        'new_password': 'NewPassword@456'
    })
    assert succ_resp.status_code == 200
    assert succ_resp.json['success'] is True

    # Login with old password should fail
    old_login = client.post('/api/login', json={'user_id': 'reset_test_user', 'password': 'OldPassword@123'})
    assert old_login.status_code == 401

    # Login with new password should succeed
    new_login = client.post('/api/login', json={'user_id': 'reset_test_user', 'password': 'NewPassword@456'})
    assert new_login.status_code == 200
    assert new_login.json['success'] is True

def test_otp_send_and_verify_flow(client):
    delete_user('otp_test_user')

    # Admin Login & Create user
    client.post('/api/login', json={'user_id': 'admin', 'password': 'Admin@123456'})
    client.post('/api/register', json={
        'user_id': 'otp_test_user',
        'full_name': 'OTP User Test',
        'email': 'otp_user@example.com',
        'phone': '+1999111222',
        'password': 'InitialPassword@123'
    })
    client.post('/api/logout')

    # Request OTP with wrong phone should fail
    fail_otp = client.post('/api/send-otp', json={'user_id': 'otp_test_user', 'phone': '+1000000000'})
    assert fail_otp.status_code == 400

    # Request OTP with correct phone should succeed
    send_resp = client.post('/api/send-otp', json={'user_id': 'otp_test_user', 'phone': '+1999111222'})
    assert send_resp.status_code == 200
    assert send_resp.json['success'] is True
    otp_code = send_resp.json['demo_otp']
    assert len(otp_code) == 6

    # Verify with wrong OTP should fail
    fail_ver = client.post('/api/verify-otp-reset', json={
        'user_id': 'otp_test_user',
        'otp': '000000',
        'new_password': 'UpdatedPassword@999'
    })
    assert fail_ver.status_code == 400

    # Verify with correct OTP should succeed
    succ_ver = client.post('/api/verify-otp-reset', json={
        'user_id': 'otp_test_user',
        'otp': otp_code,
        'new_password': 'UpdatedPassword@999'
    })
    assert succ_ver.status_code == 200
    assert succ_ver.json['success'] is True

    # Login with updated password
    login_succ = client.post('/api/login', json={'user_id': 'otp_test_user', 'password': 'UpdatedPassword@999'})
    assert login_succ.status_code == 200







