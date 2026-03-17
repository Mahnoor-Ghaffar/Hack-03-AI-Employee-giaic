import smtplib
import ssl
import os
import sys

def send_email(to_email, subject, body):
    sender_email = os.environ.get("EMAIL_ADDRESS")
    sender_password = os.environ.get("EMAIL_PASSWORD")

    if not sender_email or not sender_password:
        print("Error: EMAIL_ADDRESS and EMAIL_PASSWORD environment variables must be set.")
        sys.exit(1)

    message = f"""From: {sender_email}
To: {to_email}
Subject: {subject}

{body}
"""

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message)
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python send_email.py <to_email> <subject> <body>")
        sys.exit(1)

    to_email = sys.argv[1]
    subject = sys.argv[2]
    body = sys.argv[3]

    send_email(to_email, subject, body)
