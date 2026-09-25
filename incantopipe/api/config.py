# /home/carlo/AreaComune/ProgettiFlet/incantopipe/api/config.py

DATABASE_URL = "postgresql://postgres:treX39@incantopipe.it:5432/incanto"

API_HOST = "0.0.0.0"
API_PORT = 8889

PAYPAL_CLIENT_ID = "tuo-client-id-sandbox"
PAYPAL_SECRET = "tuo-secret-sandbox"
PAYPAL_MODE = "sandbox"

if PAYPAL_MODE == "sandbox":
    PAYPAL_API_URL = "https://api-m.sandbox.paypal.com"
else:
    PAYPAL_API_URL = "https://api-m.paypal.com"

# Percorso immagini del progetto Django esistente
MEDIA_ROOT = "/home/carlo/AreaComune/progetti_py/incantopipe/media"