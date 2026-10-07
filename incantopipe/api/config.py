# api/config.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_URL = "postgresql://postgres:treX39@incantopipe.it:5432/incanto"


API_HOST = "0.0.0.0"
API_PORT = 8889
# JWT
SECRET_KEY = "-TkN1fzzZbw7288tspLR5aL9C5wmQrDT8j6JnlBfkUB770zPqLGAzuC1-uVWjlX412IZPKbBsJOwYWfkixHuvw"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 1 settimana

PAYPAL_CLIENT_ID = "tuo-client-id-sandbox"
PAYPAL_SECRET = "tuo-secret-sandbox"
PAYPAL_MODE = "sandbox"

if PAYPAL_MODE == "sandbox":
    PAYPAL_API_URL = "https://api-m.sandbox.paypal.com"
else:
    PAYPAL_API_URL = "https://api-m.paypal.com"

# Percorso relativo: funziona ovunque tu sposti il progetto
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
