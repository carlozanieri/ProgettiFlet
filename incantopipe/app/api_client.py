# incantopipe_flet/app/api_client.py
import httpx
from typing import Optional
from config import API_BASE_URL


class APIClient:
    """Client per comunicare con l'API InCantoPipe."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(timeout=10.0)

    # ============================================================
    # CATALOGO
    # ============================================================

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

    # ============================================================
    # CARRELLO
    # ============================================================

    def get_cart(self) -> dict:
        """Carrello dell'utente autenticato."""
        try:
            r = self.client.get(f"{self.base_url}/cart")
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError as e:
            print(f"Errore get_cart: {e}")
            return {"cart_id": 0, "items": [], "total_items": 0, "total_price": 0}

    def add_to_cart(self, product_id: int, quantity: int = 1) -> bool:
        try:
            r = self.client.post(
                f"{self.base_url}/cart/add",
                json={"product_id": product_id, "quantity": quantity},
            )
            r.raise_for_status()
            return True
        except httpx.HTTPError as e:
            print(f"Errore add_to_cart: {e}")
            return False

    def update_cart_item(self, item_id: int, quantity: int) -> bool:
        try:
            r = self.client.post(
                f"{self.base_url}/cart/update",
                params={"item_id": item_id},
                json={"quantity": quantity},
            )
            r.raise_for_status()
            return True
        except httpx.HTTPError as e:
            print(f"Errore update_cart_item: {e}")
            return False

    def remove_from_cart(self, item_id: int) -> bool:
        try:
            r = self.client.post(
                f"{self.base_url}/cart/remove",
                params={"item_id": item_id},
            )
            r.raise_for_status()
            return True
        except httpx.HTTPError as e:
            print(f"Errore remove_from_cart: {e}")
            return False

    # ============================================================
    # AUTENTICAZIONE
    # ============================================================

    def set_auth_token(self, token: str):
        """Salva il token per le richieste future."""
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    def clear_auth_token(self):
        """Rimuove il token (logout)."""
        self.client.headers.pop("Authorization", None)

    def get_me(self) -> dict | None:
        """Restituisce i dati dell'utente autenticato, o None."""
        try:
            r = self.client.get(f"{self.base_url}/auth/me")
            if r.status_code == 200:
                return r.json()
            return None
        except httpx.HTTPError:
            return None

    def login(self, username: str, password: str) -> tuple:
        """Effettua il login. Ritorna (success, data_o_messaggio)."""
        try:
            r = self.client.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password},
            )
            if r.status_code == 200:
                data = r.json()
                self.set_auth_token(data["access_token"])
                return True, data
            else:
                try:
                    detail = r.json().get("detail", "Credenziali non valide")
                except Exception:
                    detail = r.text
                return False, detail
        except httpx.HTTPError as e:
            return False, f"Errore di rete: {e}"

    def register(self, username: str, email: str, password: str,
                 first_name: str = "", last_name: str = "") -> tuple:
        """Registra un nuovo utente. Ritorna (success, message)."""
        try:
            r = self.client.post(
                f"{self.base_url}/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            if r.status_code == 200:
                return True, r.json().get("message", "Registrazione completata")
            else:
                try:
                    detail = r.json().get("detail", "Errore sconosciuto")
                except Exception:
                    detail = r.text
                return False, detail
        except httpx.HTTPError as e:
            return False, f"Errore di rete: {e}"

    # ============================================================
    # ORDINI
    # ============================================================

    def create_order(self, order_data: dict) -> tuple:
        """Crea un ordine. Ritorna (success, data_o_messaggio)."""
        try:
            r = self.client.post(
                f"{self.base_url}/orders",
                json=order_data,
            )
            if r.status_code == 200:
                return True, r.json()
            else:
                try:
                    detail = r.json().get("detail", "Errore nella creazione dell'ordine")
                except Exception:
                    detail = r.text
                return False, detail
        except httpx.HTTPError as e:
            return False, f"Errore di rete: {e}"

    def get_orders(self) -> list:
        """Storico ordini dell'utente autenticato."""
        try:
            r = self.client.get(f"{self.base_url}/orders")
            if r.status_code == 200:
                return r.json()
            return []
        except httpx.HTTPError:
            return []

    def get_order(self, order_id: int):
        """Dettaglio di un ordine."""
        try:
            r = self.client.get(f"{self.base_url}/orders/{order_id}")
            if r.status_code == 200:
                return r.json()
            return None
        except httpx.HTTPError:
            return None

    def cancel_order(self, order_id: int) -> tuple:
        """Annulla un ordine. Ritorna (success, data_o_messaggio)."""
        try:
            r = self.client.post(f"{self.base_url}/orders/{order_id}/cancel")
            if r.status_code == 200:
                return True, r.json()
            else:
                try:
                    detail = r.json().get("detail", "Errore nell'annullamento")
                except Exception:
                    detail = r.text
                return False, detail
        except httpx.HTTPError as e:
            return False, f"Errore di rete: {e}"

    # ============================================================
    # PAGAMENTI
    # ============================================================

    def get_payment_status(self, order_id: int) -> dict:
        """Verifica lo stato del pagamento PayPal."""
        try:
            r = self.client.get(f"{self.base_url}/payment/paypal/status/{order_id}")
            if r.status_code == 200:
                return r.json()
            return {"authorized": False}
        except httpx.HTTPError:
            return {"authorized": False}

    def paypal_authorize(self, order_id: int) -> tuple:
        """Avvia l'autorizzazione PayPal. Ritorna (success, data_o_errore)."""
        try:
            r = self.client.post(
                f"{self.base_url}/payment/paypal/authorize",
                json={"order_id": order_id},
            )
            if r.status_code == 200:
                return True, r.json()
            else:
                try:
                    detail = r.json().get("detail", "Errore PayPal")
                except Exception:
                    detail = r.text
                return False, detail
        except httpx.HTTPError as e:
            return False, f"Errore di rete: {e}"

        # ============================================================
    # ADMIN
    # ============================================================

    def admin_list_orders(self, status: str = "authorized") -> list:
        """Lista ordini per stato (solo admin)."""
        try:
            r = self.client.get(
                f"{self.base_url}/admin/orders",
                params={"status": status},
            )
            if r.status_code == 200:
                return r.json()
            return []
        except httpx.HTTPError:
            return []

    def admin_ship_order(self, order_id: int, tracking_number: str = "") -> tuple:
        """Cattura il pagamento e marca l'ordine come spedito con tracking."""
        try:
            r = self.client.post(
                f"{self.base_url}/admin/orders/{order_id}/ship",
                json={"tracking_number": tracking_number}
            )
            if r.status_code == 200:
                return True, r.json()
            else:
                try:
                    detail = r.json().get("detail", "Errore nella spedizione")
                except Exception:
                    detail = r.text
                return False, detail
        except httpx.HTTPError as e:
            return False, f"Errore di rete: {e}"

    def admin_cancel_order(self, order_id: int) -> tuple:
        """Annulla l'ordine (void PayPal + ripristina stock)."""
        try:
            r = self.client.post(f"{self.base_url}/admin/orders/{order_id}/cancel")
            if r.status_code == 200:
                return True, r.json()
            else:
                try:
                    detail = r.json().get("detail", "Errore nell'annullamento")
                except Exception:
                    detail = r.text
                return False, detail
        except httpx.HTTPError as e:
            return False, f"Errore di rete: {e}"

    def paypal_config(self) -> dict:
        """Restituisce la configurazione PayPal (client_id, mode)."""
        try:
            r = self.client.get(f"{self.base_url}/payment/paypal/config")
            if r.status_code == 200:
                return r.json()
            return {}
        except httpx.HTTPError:
            return {}

    def paypal_client_token(self) -> str | None:
        """Ottiene un browser-safe client token per il SDK PayPal."""
        try:
            r = self.client.get(f"{self.base_url}/payment/paypal/client-token")
            if r.status_code == 200:
                return r.json().get("client_token")
            return None
        except httpx.HTTPError:
            return None

    def paypal_card_order(self, order_id: int) -> tuple:
        """Crea un ordine PayPal per il pagamento con carta."""
        try:
            r = self.client.post(
                f"{self.base_url}/payment/paypal/card-order",
                json={"order_id": order_id},
            )
            if r.status_code == 200:
                return True, r.json()
            else:
                try:
                    detail = r.json().get("detail", "Errore PayPal")
                except Exception:
                    detail = r.text
                return False, detail
        except httpx.HTTPError as e:
            return False, f"Errore di rete: {e}"