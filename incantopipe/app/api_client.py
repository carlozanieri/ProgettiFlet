# incantopipe_flet/app/api_client.py
import httpx
from typing import Optional
from config import API_BASE_URL


class APIClient:
    """Client per comunicare con l'API InCantoPipe."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(timeout=10.0)

    def get_categories(self) -> list:
        """Restituisce tutte le categorie."""
        try:
            r = self.client.get(f"{self.base_url}/categories")
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError as e:
            print(f"Errore get_categories: {e}")
            return []

    def get_products(
        self,
        category_slug: Optional[str] = None,
        search: Optional[str] = None,
        material: Optional[str] = None,
        finish: Optional[str] = None,
        shape: Optional[str] = None,
        sort: str = "-created",
    ) -> list:
        """Restituisce la lista dei prodotti con filtri opzionali."""
        params = {"sort": sort}
        if category_slug:
            params["category_slug"] = category_slug
        if search:
            params["search"] = search
        if material:
            params["material"] = material
        if finish:
            params["finish"] = finish
        if shape:
            params["shape"] = shape

        try:
            r = self.client.get(f"{self.base_url}/products", params=params)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError as e:
            print(f"Errore get_products: {e}")
            return []

    def get_product(self, slug: str) -> Optional[dict]:
        """Restituisce il dettaglio di un prodotto."""
        try:
            r = self.client.get(f"{self.base_url}/products/{slug}")
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError as e:
            print(f"Errore get_product: {e}")
            return None
    
    def get_cart(self, session_key: str) -> dict:
        try:
            r = self.client.get(
                f"{self.base_url}/cart",
                params={"session_key": session_key},
            )
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError as e:
            print(f"Errore get_cart: {e}")
            return {"cart_id": 0, "items": [], "total_items": 0, "total_price": 0}

    def add_to_cart(self, session_key: str, product_id: int, quantity: int = 1) -> bool:
        try:
            r = self.client.post(
                f"{self.base_url}/cart/add",
                params={"session_key": session_key},
                json={"product_id": product_id, "quantity": quantity},
            )
            r.raise_for_status()
            return True
        except httpx.HTTPError as e:
            print(f"Errore add_to_cart: {e}")
            return False

    def update_cart_item(self, session_key: str, item_id: int, quantity: int) -> bool:
        try:
            r = self.client.post(
                f"{self.base_url}/cart/update",
                params={"session_key": session_key, "item_id": item_id},
                json={"quantity": quantity},
            )
            r.raise_for_status()
            return True
        except httpx.HTTPError as e:
            print(f"Errore update_cart_item: {e}")
            return False

    def remove_from_cart(self, session_key: str, item_id: int) -> bool:
        try:
            r = self.client.post(
                f"{self.base_url}/cart/remove",
                params={"session_key": session_key, "item_id": item_id},
            )
            r.raise_for_status()
            return True
        except httpx.HTTPError as e:
            print(f"Errore remove_from_cart: {e}")
            return False

    def close(self):
        self.client.close()