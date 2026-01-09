import smtplib
import os
import json
import logging
from email.message import EmailMessage

def notification(message):
    try:
        # RabbitMQ message comes as bytes
        if isinstance(message, bytes):
            message = message.decode("utf-8")

        message = json.loads(message)

        mp3_fid = message.get("mp3_fid")
        receiver_address = message.get("username")

        if not mp3_fid or not receiver_address:
            logging.info("invalid message payload")
            return "invalid message payload"

        sender_address = os.environ.get("GMAIL_APP_USER_NAME")
        sender_password = os.environ.get("GMAIL_APP_PASSWORD")

        if not sender_address or not sender_password:
            logging.info("email credentials not configured")
            return "email credentials not configured"

        msg = EmailMessage()
        msg.set_content(
            f"""
Hi,

Your MP3 conversion is complete 🎉

File ID: {mp3_fid}

You can now download your MP3 file.

Regards,
Video to MP3 Converter
"""
        )
        msg["Subject"] = "MP3 Conversion Complete"
        msg["From"] = sender_address
        msg["To"] = receiver_address


        # Gmail SMTP
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as session:
            session.starttls()
            session.login(sender_address, sender_password)
            session.send_message(msg)

        logging.info(f"Email sent to: {receiver_address}")
        return None  # success

    except Exception as err:
        logging.error(f"Email notification failed: {err}")
        return str(err)
