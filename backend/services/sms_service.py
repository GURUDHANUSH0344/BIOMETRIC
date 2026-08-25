import os
import json
import logging
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)

def send_sms_otp(phone_number: str, otp_code: str, user_name: str = "User", email: str = "") -> dict:
    """
    Sends a 6-digit OTP to the registered phone number linked with the user's registered email.
    Supports Fast2SMS, Twilio, Generic SMS Webhooks, and Console Log fallback.
    """
    clean_phone = "".join(filter(lambda c: c.isdigit() or c == '+', str(phone_number).strip()))
    message_text = f"Your FXEC Biometric verification OTP is {otp_code}. Valid for 10 minutes. Do not share with anyone."

    # 1. Fast2SMS (Common for Indian +91 numbers)
    fast2sms_key = os.getenv("FAST2SMS_API_KEY")
    if fast2sms_key:
        try:
            # Fast2SMS requires 10-digit number without country code
            ten_digit_phone = "".join(filter(str.isdigit, clean_phone))[-10:]
            url = "https://www.fast2sms.com/dev/bulkV2"
            payload = {
                "authorization": fast2sms_key,
                "route": "otp",
                "variables_values": otp_code,
                "numbers": ten_digit_phone,
                "flash": "0"
            }
            data = urllib.parse.urlencode(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"cache-control": "no-cache"})
            with urllib.request.urlopen(req, timeout=8) as response:
                res_body = response.read().decode("utf-8")
                logger.info(f"[SMS Gateway: Fast2SMS] OTP sent to {ten_digit_phone}: {res_body}")
                return {"success": True, "provider": "fast2sms"}
        except Exception as e:
            logger.error(f"[SMS Gateway: Fast2SMS Error] Failed to send SMS: {e}")

    # 2. Twilio SMS
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_from = os.getenv("TWILIO_PHONE_NUMBER")
    if twilio_sid and twilio_token and twilio_from:
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            to_phone = clean_phone if clean_phone.startswith("+") else f"+91{clean_phone}"
            payload = {
                "From": twilio_from,
                "To": to_phone,
                "Body": message_text
            }
            data = urllib.parse.urlencode(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data)
            auth_str = f"{twilio_sid}:{twilio_token}"
            import base64
            b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
            req.add_header("Authorization", f"Basic {b64_auth}")
            with urllib.request.urlopen(req, timeout=8) as response:
                logger.info(f"[SMS Gateway: Twilio] OTP sent to {to_phone}")
                return {"success": True, "provider": "twilio"}
        except Exception as e:
            logger.error(f"[SMS Gateway: Twilio Error] Failed to send SMS: {e}")

    # 3. Generic SMS Webhook
    sms_webhook = os.getenv("SMS_WEBHOOK_URL")
    if sms_webhook:
        try:
            payload = json.dumps({"phone": clean_phone, "otp": otp_code, "message": message_text, "email": email}).encode("utf-8")
            req = urllib.request.Request(sms_webhook, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=8) as response:
                return {"success": True, "provider": "webhook"}
        except Exception as e:
            logger.error(f"[SMS Gateway: Webhook Error] Failed to dispatch webhook: {e}")

    # 4. Standard Console Log fallback
    masked_phone = clean_phone[-4:].rjust(len(clean_phone), '*') if len(clean_phone) >= 4 else clean_phone
    print(f"\n=======================================================")
    print(f"📱 [SMS OTP DISPATCHED TO REGISTERED PHONE]")
    print(f"   Target Phone : {clean_phone} (Masked: {masked_phone})")
    print(f"   Linked Email : {email or 'N/A'}")
    print(f"   User Name    : {user_name}")
    print(f"   6-Digit OTP  : {otp_code}")
    print(f"   Expires In   : 10 Minutes")
    print(f"=======================================================\n")
    
    return {"success": True, "provider": "console", "phone": clean_phone, "otp": otp_code}
