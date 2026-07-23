import os
import smtplib, ssl
from email.message import EmailMessage


def send_verification_email(email, code, name):
    return False

    # Disable for now
    msg = EmailMessage()
    msg['Subject'] = "Welcome to Crazy Penguin Wars!"
    msg['From'] = "noreply@crazypenguinwars.me"
    msg['To'] = email

    text = f"Your verification code is {code}"
    html = f"<h2>Dear {name}</h2><h1>Welcome to Crazy Penguin Wars!</h1><br>Your activation code is: <h3>{code}</h3><br>Enjoy playing the game!<br><br><img src=https://crazypenguinwars.me/assets/logo.png width=150><br><a href=https://discord.gg/PxxhzcbemQ target=_blank><img src=https://i.imgur.com/7S5ZLPZ.png width=40 height=40 title='Join our Discord!' /> </a>"

    msg.set_content(text)
    msg.add_alternative(html, subtype='html')

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.zeptomail.eu", 465, context=context) as server:
            server.login(os.environ['MAIL_USERNAME'], os.environ['MAIL_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(e)
        return False
