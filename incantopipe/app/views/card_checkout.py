# app/views/card_checkout.py
import flet as ft
from flet_webview_all import FletWebviewAll


# ============================================================
# HTML CON I CAMPI CARTA PAYPAL
# ============================================================

CARD_CHECKOUT_HTML = """
<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pagamento con carta</title>
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    margin: 0; padding: 20px; background: #fafafa;
  }
  .container { max-width: 500px; margin: 0 auto; }
  h2 { color: #5d3a1a; margin-bottom: 20px; }
  .field-container {
    height: 45px;
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 0 10px;
    margin-bottom: 12px;
    background: white;
  }
  #pay-button {
    width: 100%; height: 50px; background: #5d3a1a; color: white;
    border: none; border-radius: 8px; font-size: 16px;
    font-weight: bold; cursor: pointer; margin-top: 10px;
  }
  #pay-button:disabled { background: #999; }
  #error { color: #c00; margin-top: 10px; font-size: 14px; }
  .label { font-size: 12px; color: #666; margin-bottom: 4px; }
</style>
</head>
<body>
<div class="container">
  <h2>Pagamento con carta</h2>

  <div class="label">Numero carta</div>
  <div class="field-container" id="card-number"></div>

  <div class="label">Scadenza</div>
  <div class="field-container" id="card-expiry"></div>

  <div class="label">CVV</div>
  <div class="field-container" id="card-cvv"></div>

  <button id="pay-button" disabled>Paga € __AMOUNT__</button>
  <div id="error"></div>
</div>

<script src="https://www.sandbox.paypal.com/sdk/js?client-id=__CLIENT_ID__&components=card-fields&currency=EUR"></script>
<script>
  const PAYPAL_ORDER_ID = "__PAYPAL_ORDER_ID__";

  function sendToFlet(message) {
    if (window.FletBridge && window.FletBridge.postMessage) {
      window.FletBridge.postMessage(JSON.stringify(message));
    }
  }

  async function initCardFields() {
    try {
      // 1. Ottieni client token
      const tokenRes = await fetch("/api/v1/payment/paypal/client-token");
      const tokenData = await tokenRes.json();
      const clientToken = tokenData.client_token;

      // 2. Inizializza SDK
      const sdk = await paypal.createInstance({ clientToken, components: ["card-fields"] });

      // 3. Crea sessione pagamento
      const cardSession = sdk.createCardFieldsOneTimePaymentSession();

      // 4. Renderizza i campi
      const numberField = cardSession.createCardFieldsComponent({ type: "number", placeholder: "4111 1111 1111 1111" });
      const expiryField = cardSession.createCardFieldsComponent({ type: "expirationDate", placeholder: "MM/YY" });
      const cvvField = cardSession.createCardFieldsComponent({ type: "cvv", placeholder: "123" });

      document.querySelector("#card-number").appendChild(numberField);
      document.querySelector("#card-expiry").appendChild(expiryField);
      document.querySelector("#card-cvv").appendChild(cvvField);

      // 5. Abilita il pulsante quando i campi sono validi
      cardSession.on("validitychange", (event) => {
        document.querySelector("#pay-button").disabled = !event.isValid;
      });

      // 6. Gestisci submit
      document.querySelector("#pay-button").addEventListener("click", async () => {
        document.querySelector("#error").textContent = "";
        document.querySelector("#pay-button").disabled = true;
        try {
          const { state, data } = await cardSession.submit(PAYPAL_ORDER_ID);
          if (state === "succeeded") {
            sendToFlet({ success: true, order_id: PAYPAL_ORDER_ID });
          } else if (state === "canceled") {
            sendToFlet({ success: false, error: "Pagamento annullato" });
          } else {
            sendToFlet({ success: false, error: data?.message || "Errore" });
          }
        } catch (err) {
          sendToFlet({ success: false, error: err.message });
        }
      });
    } catch (err) {
      document.querySelector("#error").textContent = "Errore: " + err.message;
      sendToFlet({ success: false, error: err.message });
    }
  }

  initCardFields();
</script>
</body>
</html>
"""


# ============================================================
# VISTA FLET CON WEBVIEW
# ============================================================

def build_card_checkout_view(
    page: ft.Page,
    api,
    order_id: int,
    paypal_order_id: str,
    amount: float,
    client_id: str,
    on_success,
    on_cancel,
) -> ft.Container:
    """
    Mostra il WebView con i campi carta di PayPal.

    on_success: callback chiamata quando il pagamento è autorizzato
    on_cancel: callback chiamata se l'utente annulla
    """
    import asyncio

    # Sostituisci i placeholder nell'HTML
    html = CARD_CHECKOUT_HTML
    html = html.replace("__CLIENT_ID__", client_id)
    html = html.replace("__PAYPAL_ORDER_ID__", paypal_order_id)
    html = html.replace("__AMOUNT__", f"{amount:.2f}")

    # Stato locale
    state = {"done": False}

    def on_js_message(e):
        """Riceve i messaggi dal JavaScript del WebView."""
        import json
        try:
            msg = json.loads(e.message_body)
        except Exception:
            return

        if state["done"]:
            return

        if msg.get("success"):
            state["done"] = True
            page.show_dialog(ft.SnackBar(
                content=ft.Text("Pagamento autorizzato!"),
                bgcolor=ft.Colors.GREEN_700,
            ))
            on_success(order_id)
        else:
            state["done"] = True
            page.show_dialog(ft.SnackBar(
                content=ft.Text(f"Errore: {msg.get('error', 'Sconosciuto')}"),
                bgcolor=ft.Colors.RED_700,
            ))
            on_cancel()

    webview = FletWebviewAll(
        html=html,
        javascript_channels=["FletBridge"],
        on_javascript_message=on_js_message,
        expand=True,
    )

    return ft.Container(
        content=ft.Column([
            ft.TextButton("← Annulla e torna al carrello",
                          on_click=lambda e: on_cancel()),
            ft.Text("Pagamento con carta", size=24,
                    weight=ft.FontWeight.BOLD, color=ft.Colors.BROWN_700),
            ft.Container(height=10),
            ft.Container(
                content=webview,
                expand=True,
                height=600,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=10,
            ),
        ], spacing=10, expand=True),
        padding=20,
        expand=True,
    )