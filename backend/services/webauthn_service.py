import json
import webauthn
from webauthn.helpers import structs
from backend.config import Config
from backend.utils.serializers import bytes_to_base64url, base64url_to_bytes

def get_webauthn_registration_options(user_id: str, full_name: str, existing_credentials=None):
    """
    Generates WebAuthn registration options for a user.
    Returns (options_json_str, challenge_base64url_str)
    """
    user_id_bytes = user_id.encode('utf-8')
    
    exclude_credentials = []
    if existing_credentials:
        for cred in existing_credentials:
            cred_id_bytes = base64url_to_bytes(cred['credential_id'])
            exclude_credentials.append(
                structs.PublicKeyCredentialDescriptor(id=cred_id_bytes)
            )

    options = webauthn.generate_registration_options(
        rp_id=Config.WEBAUTHN_RP_ID,
        rp_name=Config.WEBAUTHN_RP_NAME,
        user_id=user_id_bytes,
        user_name=user_id,
        user_display_name=full_name,
        exclude_credentials=exclude_credentials,
        authenticator_selection=structs.AuthenticatorSelectionCriteria(
            user_verification=structs.UserVerificationRequirement.PREFERRED,
            resident_key=structs.ResidentKeyRequirement.PREFERRED
        )
    )

    challenge_b64 = bytes_to_base64url(options.challenge)
    options_json = webauthn.options_to_json(options)
    
    return options_json, challenge_b64

def verify_webauthn_registration(credential_payload, expected_challenge_b64: str):
    """
    Verifies the WebAuthn registration response sent by the client.
    Returns (verified_credential_id_b64, verified_public_key_b64, initial_sign_count)
    """
    expected_challenge_bytes = base64url_to_bytes(expected_challenge_b64)
    
    # Accept JSON string or dict
    if isinstance(credential_payload, dict):
        credential_str = json.dumps(credential_payload)
    else:
        credential_str = credential_payload

    verification = webauthn.verify_registration_response(
        credential=credential_str,
        expected_challenge=expected_challenge_bytes,
        expected_rp_id=Config.WEBAUTHN_RP_ID,
        expected_origin=Config.WEBAUTHN_ORIGIN,
        require_user_verification=False
    )

    cred_id_b64 = bytes_to_base64url(verification.credential_id)
    public_key_b64 = bytes_to_base64url(verification.credential_public_key)
    sign_count = verification.sign_count

    return cred_id_b64, public_key_b64, sign_count

def get_webauthn_authentication_options(user_credentials):
    """
    Generates WebAuthn authentication assertion options.
    Returns (options_json_str, challenge_base64url_str)
    """
    allow_credentials = []
    if user_credentials:
        for cred in user_credentials:
            cred_id_bytes = base64url_to_bytes(cred['credential_id'])
            allow_credentials.append(
                structs.PublicKeyCredentialDescriptor(id=cred_id_bytes)
            )

    options = webauthn.generate_authentication_options(
        rp_id=Config.WEBAUTHN_RP_ID,
        allow_credentials=allow_credentials,
        user_verification=structs.UserVerificationRequirement.PREFERRED
    )

    challenge_b64 = bytes_to_base64url(options.challenge)
    options_json = webauthn.options_to_json(options)

    return options_json, challenge_b64

def verify_webauthn_authentication(credential_payload, expected_challenge_b64: str, public_key_b64: str, current_sign_count: int):
    """
    Verifies the WebAuthn authentication assertion response.
    Returns new_sign_count.
    """
    expected_challenge_bytes = base64url_to_bytes(expected_challenge_b64)
    public_key_bytes = base64url_to_bytes(public_key_b64)

    if isinstance(credential_payload, dict):
        credential_str = json.dumps(credential_payload)
    else:
        credential_str = credential_payload

    verification = webauthn.verify_authentication_response(
        credential=credential_str,
        expected_challenge=expected_challenge_bytes,
        expected_rp_id=Config.WEBAUTHN_RP_ID,
        expected_origin=Config.WEBAUTHN_ORIGIN,
        credential_public_key=public_key_bytes,
        credential_current_sign_count=current_sign_count,
        require_user_verification=False
    )

    return verification.new_sign_count
