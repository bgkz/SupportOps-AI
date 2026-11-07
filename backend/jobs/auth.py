import secrets

import resend

from backend.config import BASE_BACKEND_URL, RESEND_API_KEY


def send_email_verification(email: str, token_hash: str):
    resend.api_key = RESEND_API_KEY
    verification_url = f"{BASE_BACKEND_URL}auth/verify-email?token={token_hash}"

    resend.Emails.send(
        {
            "from": "onboarding@resend.dev",
            "to": f"{email}",
            "subject": "Verify your email address — link expires in 30 minutes",
            "html": f"<p>{verification_url}</p>",
        }
    )
