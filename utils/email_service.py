import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


async def send_email(to: str, subject: str, html: str):

    message = MIMEMultipart("alternative")
    message["From"] = EMAIL_USER
    message["To"] = to
    message["Subject"] = subject

    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to, message.as_string())

    except Exception as e:
        print("Error sending email:", e)