# api/payment/paypal.py
import requests
from config import PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_API_URL
import logging

logger = logging.getLogger(__name__)


class PayPalService:
    """Servizio per interagire con PayPal REST API v2 (Auth & Capture)."""

    def __init__(self):
        self.client_id = PAYPAL_CLIENT_ID
        self.secret = PAYPAL_CLIENT_SECRET
        self.api_url = PAYPAL_API_URL
        self._access_token = None

    def get_access_token(self):
        """Ottiene il token OAuth di PayPal."""
        url = f"{self.api_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = {"grant_type": "client_credentials"}

        try:
            response = requests.post(
                url,
                headers=headers,
                data=data,
                auth=(self.client_id, self.secret),
            )
            if response.status_code == 200:
                self._access_token = response.json()["access_token"]
                return self._access_token
            logger.error(f"Errore token PayPal: {response.text}")
            return None
        except Exception as e:
            logger.error(f"Eccezione token PayPal: {e}")
            return None

    def create_order(self, order, return_url: str, cancel_url: str, payment_source: dict = None):
        """
        Crea un ordine PayPal con intent=AUTHORIZE.
        Gestisce separatamente il flusso standard (application_context) e quello con carta (payment_source).
        """
        token = self.get_access_token()
        if not token:
            return None, "Impossibile ottenere token PayPal"

        url = f"{self.api_url}/v2/checkout/orders"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        payload = {
            "intent": "AUTHORIZE",
            "purchase_units": [{
                "reference_id": str(order["id"]),
                "description": f"Ordine #{order['order_number']} - InCantoPipe",
                "amount": {
                    "currency_code": "EUR",
                    "value": f"{float(order['total']):.2f}",
                },
            }],
        }

        if payment_source:
            # Flusso carta: gli URL sono già dentro payment_source.card.experience_context
            # passato da main.py, quindi non aggiungiamo application_context
            payload["payment_source"] = payment_source
        else:
            # Flusso PayPal standard: usa application_context per gli URL
            payload["application_context"] = {
                "brand_name": "InCantoPipe",
                "landing_page": "NO_PREFERENCE",
                "user_action": "PAY_NOW",
                "return_url": return_url,
                "cancel_url": cancel_url,
            }

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 201:
                data = response.json()
                return data["id"], None
            logger.error(f"Errore create_order PayPal: {response.status_code} - {response.text}")
            return None, response.text
        except Exception as e:
            logger.error(f"Eccezione create_order: {e}")
            return None, str(e)

    def get_order_status(self, paypal_order_id: str):
        """
        Recupera lo stato dell'ordine PayPal.
        Ritorna (status, None) o (None, errore).
        """
        token = self.get_access_token()
        if not token:
            return None, "Impossibile ottenere token PayPal"

        url = f"{self.api_url}/v2/checkout/orders/{paypal_order_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("status"), None
            logger.error(f"Errore get_order_status: {response.status_code} - {response.text}")
            return None, response.text
        except Exception as e:
            logger.error(f"Eccezione get_order_status: {e}")
            return None, str(e)

    def get_approve_url(self, paypal_order_id: str) -> str | None:
        """
        Restituisce l'URL di approvazione PayPal per il flusso standard.
        """
        mode = "sandbox" if "sandbox" in self.api_url else "www"
        if mode == "sandbox":
            return f"https://www.sandbox.paypal.com/checkoutnow?token={paypal_order_id}"
        return f"https://www.paypal.com/checkoutnow?token={paypal_order_id}"

    def authorize_order(self, paypal_order_id: str):
        """
        Autorizza un ordine PayPal (blocca i fondi).
        Ritorna (authorization_id, None) o (None, errore).
        """
        token = self.get_access_token()
        if not token:
            return None, "Impossibile ottenere token PayPal"

        url = f"{self.api_url}/v2/checkout/orders/{paypal_order_id}/authorize"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 201:
                data = response.json()
                auth_id = data["purchase_units"][0]["payments"]["authorizations"][0]["id"]
                return auth_id, None
            logger.error(f"Errore authorize: {response.status_code} - {response.text}")
            return None, response.text
        except Exception as e:
            logger.error(f"Eccezione authorize: {e}")
            return None, str(e)

    def capture_authorization(self, authorization_id: str):
        """
        Cattura un'autorizzazione (incassa i fondi).
        Ritorna (capture_id, None) o (None, errore).
        """
        token = self.get_access_token()
        if not token:
            return None, "Impossibile ottenere token PayPal"

        url = f"{self.api_url}/v2/payments/authorizations/{authorization_id}/capture"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 201:
                data = response.json()
                return data["id"], None
            logger.error(f"Errore capture: {response.status_code} - {response.text}")
            return None, response.text
        except Exception as e:
            logger.error(f"Eccezione capture: {e}")
            return None, str(e)

    def void_authorization(self, authorization_id: str):
        """
        Annulla un'autorizzazione (sblocca i fondi).
        Ritorna (True, None) o (False, errore).
        """
        token = self.get_access_token()
        if not token:
            return False, "Impossibile ottenere token PayPal"

        url = f"{self.api_url}/v2/payments/authorizations/{authorization_id}/void"
        headers = {
            "Authorization": f"Bearer {token}",
        }

        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 204:
                return True, None
            logger.error(f"Errore void: {response.status_code} - {response.text}")
            return False, response.text
        except Exception as e:
            logger.error(f"Eccezione void: {e}")
            return False, str(e)


# Istanza globale
paypal_service = PayPalService()