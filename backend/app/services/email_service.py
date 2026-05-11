"""
Email Service
SMTP sending, templates, tracking.
"""
from app.core.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import re

settings = get_settings()
logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_pass = settings.smtp_pass

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str = None,
        html: bool = False,
    ) -> bool:
        """
        Send an email via SMTP.
        Returns True if sent successfully.
        """
        if not self.smtp_host:
            logger.warning("SMTP not configured - email not sent")
            return False

        from_email = from_email or self.smtp_user

        msg = MIMEMultipart("alternative" if html else "plain")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        part = MIMEText(body, "html" if html else "plain")
        msg.attach(part)

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_pass,
                start_tls=True,
            )
            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def validate_email(self, email: str) -> bool:
        """Basic email validation."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def render_template(self, template: str, variables: dict) -> str:
        """Simple template rendering with {{variable}} syntax."""
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        return template


async def get_email_service() -> EmailService:
    return EmailService()