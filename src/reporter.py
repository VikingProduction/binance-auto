import smtplib
import matplotlib.pyplot as plt
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_report(journal: list, config: dict):
    if not journal:
        return
    df = pd.DataFrame(journal)
    df['pnl'] = df.apply(lambda r: (r['price']-r.get('price',0))*r.get('qty',0), axis=1)
    df['cum_pnl'] = df['pnl'].cumsum()
    plt.figure(); df['cum_pnl'].plot(title='Equity Curve'); plt.savefig('equity.png')
    # Préparer email
    msg = MIMEMultipart()
    msg['Subject'] = "Daily Trading Report"
    msg['From'] = config['email']['user']
    msg['To']   = config['email']['to']
    text = MIMEText(df.to_string(index=False))
    msg.attach(text)
    part = MIMEBase('application', 'octet-stream')
    with open('equity.png', 'rb') as f:
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition','attachment; filename="equity.png"')
    msg.attach(part)
    # Envoi
    server = smtplib.SMTP(config['email']['host'], config['email']['port'])
    server.starttls()
    server.login(config['email']['user'], config['email']['pass'])
    server.send_message(msg)
    server.quit()
