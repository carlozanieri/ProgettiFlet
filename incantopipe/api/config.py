# api/config.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Segreti (da app_secrets.py, non committato)
# Se il file manca o è incompleto, l'app DEVE fallire subito,
# così l'errore emerge in sviluppo e non in produzione.
from app_secrets import (
    SECRET_KEY,
    DATABASE_URL,
    PAYPAL_CLIENT_ID,
    PAYPAL_CLIENT_SECRET,
    PAYPAL_MODE,
)

API_HOST = "0.0.0.0"
API_PORT = 8889

# JWT
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7

# URL PayPal (derivato da PAYPAL_MODE)
if PAYPAL_MODE == "sandbox":
    PAYPAL_API_URL = "https://api-m.sandbox.paypal.com"
else:
    PAYPAL_API_URL = "https://api-m.paypal.com"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")