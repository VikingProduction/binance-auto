import os
import smtplib
from email.mime.text import MIMEText

def send_report(journal):
    host = os.getenv('EMAIL_HOST')
    port = int(os.getenv('EMAIL_PORT'))
    user = os.getenv('EMAIL_USER')
    pwd  = os.getenv('EMAIL_PASS')
    to   = os.getenv('EMAIL_TO')
    
    body = "Rapport journalier de trading :\n\n" + "\n".join(journal)
    msg = MIMEText(body)
    msg['Subject'] = "Daily Trading Report"
    msg['From'] = user
    msg['To'] = to
    
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, pwd)
        server.send_message(msg)
