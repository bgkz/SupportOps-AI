import secrets

from backend.config import BASE_BACKEND_URL, RESEND_API_KEY


def send_email_verification(email: str):
    token = secrets.token_urlsafe(32)
    verification_url = f"{BASE_BACKEND_URL}auth/verify-email?token={token}"

    print(verification_url)
