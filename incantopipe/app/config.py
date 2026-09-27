# app/config.py
import os

# Legge da variabile d'ambiente, con default per sviluppo locale
API_HOST = os.environ.get("INCANTO_API_HOST", "localhost:8889")

API_BASE_URL = f"http://{API_HOST}/api/v1"
MEDIA_BASE_URL = f"http://{API_HOST}/media"


