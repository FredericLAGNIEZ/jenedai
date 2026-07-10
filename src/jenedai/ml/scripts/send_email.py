import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg["From"] = "test@example.com"
msg["To"] = "destinataire@example.com"
msg["Subject"] = "Test"
msg.set_content("Ceci est un test.")

with smtplib.SMTP("localhost", 8025) as smtp:
    smtp.send_message(msg)