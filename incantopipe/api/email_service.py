# api/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app_secrets import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM

logger = logging.getLogger(__name__)


def send_email_smtp(to_email: str, subject: str, body: str):
    """Invia un'email tramite SMTP."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email inviata a {to_email}")
    except Exception as e:
        logger.error(f"Errore invio email a {to_email}: {e}")

def send_order_confirmation_email(order, items):
    """Prepara l'email di conferma per il cliente."""
    subject = f"Conferma Ordine #{order['order_number']} - InCantoPipe"
    body = f"""Gentile {order['first_name']} {order['last_name']},

Grazie per il tuo ordine su InCantoPipe!

Riepilogo:
"""
    for item in items:
        body += f"- {item['product_name']} x {item['quantity']} - € {item['price']:.2f}\n"
    
    body += f"""
Totale: € {order['total']:.2f}

Indirizzo di spedizione:
{order['address']}, {order['postal_code']} {order['city']} ({order['province']})

Ti avviseremo non appena la tua pipa sarà spedita.

Il team di InCantoPipe
"""
    return subject, body