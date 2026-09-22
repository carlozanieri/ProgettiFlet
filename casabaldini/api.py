import httpx

API_BASE = "https://json.casabaldini.eu/api/v1"
IMG_BASE = "https://json.casabaldini.eu/static/img"


async def fetch_menu():
    """Recupera la struttura del menu"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(f"{API_BASE}/menu")
        response.raise_for_status()
        return response.json()