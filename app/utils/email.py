import smtplib
from email.message import EmailMessage
from app.core.config import settings

def send_verification_email(email: str, token: str):
    try:
        verification_link = f"{settings.BACKEND_URL}/auth/verify-email/{token}"
        
        msg = EmailMessage()
        msg["Subject"] = "Verify Your Email"
        msg["From"] = settings.EMAIL_SENDER
        msg["To"] = email
        msg.set_content(f"Click the link to verify your email: {verification_link}")

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_SENDER, settings.EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"Verification email sent to {email}")

    except Exception as e:
        print(f"Error sending email: {e}")
