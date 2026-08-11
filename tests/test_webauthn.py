import json
from backend.services.webauthn_service import (
    get_webauthn_registration_options,
    get_webauthn_authentication_options
)

def test_webauthn_registration_options():
    options_json, challenge_b64 = get_webauthn_registration_options(
        user_id="testuser1",
        full_name="Test User",
        existing_credentials=[]
    )
    assert len(challenge_b64) > 10
    data = json.loads(options_json)
    assert data['rp']['name'] is not None
    assert data['user']['name'] == 'testuser1'
    assert 'challenge' in data

def test_webauthn_authentication_options():
    dummy_creds = [{
        'credential_id': 'dGVzdF9jcmVkZW50aWFsX2lk', # base64url "test_credential_id"
        'public_key': 'dGVzdF9wdWJsaWNfa2V5',
        'sign_count': 0
    }]
    options_json, challenge_b64 = get_webauthn_authentication_options(dummy_creds)
    assert len(challenge_b64) > 10
    data = json.loads(options_json)
    assert 'challenge' in data
    assert len(data['allowCredentials']) == 1
