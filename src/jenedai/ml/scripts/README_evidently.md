uv **add** aiosmtpd
uv run python -m aiosmtpd -n


```python
import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg["From"] = "test@example.com"
msg["To"] = "destinataire@example.com"
msg["Subject"] = "Test"
msg.set_content("Ceci est un test.")

with smtplib.SMTP("localhost", 8025) as smtp:
    smtp.send_message(msg)
```


```
---------- MESSAGE FOLLOWS ----------
From: test@example.com
To: destinataire@example.com
Subject: Test
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 7bit
MIME-Version: 1.0
X-Peer: ('127.0.0.1', 41348)

Ceci est un test.
------------ END MESSAGE ------------
```
