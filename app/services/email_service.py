import smtplib
from email.mime.text import MIMEText
from typing import Optional


async def send_email_smtp(to: str, subject: str, html_body: str, smtp_host: str = "localhost", smtp_port: int = 25):
    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = "no-reply@appf.local"
    msg["To"] = to

    # simple synchronous send in background tasks
    with smtplib.SMTP(smtp_host, smtp_port) as s:
        s.sendmail(msg["From"], [to], msg.as_string())
