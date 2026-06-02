from __future__ import annotations
"""emailsend service — SMTP send reportdownload link。

Compliance requirements:
- SMTP credentialfrom environment variableread（not hardcoded）
- do not record in logs SMTP passwordorrecipientemail
- Mock mode：SMTP_HOST to empty when only records logs
"""
import logging
from typing import List

from app.core.config import settings

log = logging.getLogger(__name__)


async def send_report_email(
    recipients: List[str],
    subject: str,
    download_url: str,
    agency_name: str,
) -> bool:
    """send reportemail。SMTP_HOST to empty when to  mock mode（only records logs）。"""
    if not settings.SMTP_HOST:
        log.info("SMTP not configured, mock email: subject=%s, recipients_count=%d", subject, len(recipients))
        return True

    try:
        import aiosmtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject

        body = f"""
        <html>
        <body>
            <h2>{agency_name} — Campaign Performance Report</h2>
            <p>Your latest campaign performance report is ready.</p>
            <p><a href="{download_url}" style="background:#2E75B6;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;">Download Report (PDF)</a></p>
            <p style="color:#999;font-size:12px;">This link expires in 24 hours. Report contains aggregated data only — no personally identifiable information.</p>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, "html"))

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME or None,
            password=settings.SMTP_PASSWORD or None,
            use_tls=settings.SMTP_USE_TLS,
        )
        log.info("Report email sent: recipients_count=%d", len(recipients))
        return True
    except Exception as e:
        # compliance：not recordcompleteexception（cancancontaining SMTP credential）
        log.error("Email send failed: %s", type(e).__name__)
        return False
