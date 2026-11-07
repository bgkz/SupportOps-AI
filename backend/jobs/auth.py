import smtplib
from email.message import EmailMessage

import resend

from backend.config import (
    BASE_BACKEND_URL,
    MAIL_BACKEND,
    RESEND_API_KEY,
    SMTP_HOST,
    SMTP_PORT,
)


def send_email_verification(email: str, token_hash: str):
    verification_url = (
        f"{BASE_BACKEND_URL.rstrip('/')}/auth/verify-email?token={token_hash}"
    )
    subject = "Verify your email address — link expires in 30 minutes"

    if MAIL_BACKEND == "smtp":
        message = EmailMessage()
        message["From"] = "noreply@example.com"
        message["To"] = email
        message["Subject"] = subject
        message.set_content(f"Verify your email: {verification_url}")

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
            smtp.send_message(message)
        return

    resend.api_key = RESEND_API_KEY
    resend.Emails.send(
        {
            "from": "onboarding@resend.dev",
            "to": email,
            "subject": subject,
            "html": f"<p>{verification_url}</p>",
        }
    )
