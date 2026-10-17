# app/views/card_checkout.py
# app/views/card_checkout.py
import flet as ft
import flet_webview as fwv


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
  h2 { color: #5d3a1a; margin-bottom: 20px; font-size: 22px; }
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
  #pay-button:disabled { background: #999; cursor: not-allowed; }
  #error { color: #c00; margin-top: 10px; font-size: 14px; }
  .label { font-size: 12px; color: #666; margin-bottom: 4px; font-weight: 600; }
  .note { font-size: 11px; color: #888; margin-top: 15px; text-align: center; }
</style>
</head>
<body>
<div class="container">
  <h2>Pagamento con carta</h2>

  <div class="label">Numero carta</div>
  <div class="field-container" id="card-number"></div>

  <div class="label">Scadenza (MM/YY)</div>
  <div class="field-container" id="card-expiry"></div>

  <div class="label">CVV</div>
  <div class="field-container" id="card-cvv"></div>

  <button id="pay-button" disabled>Paga € __AMOUNT__</button>
  <div id="error"></div>
  <div class="note">Pagamento sicuro gestito da PayPal</div>
</div>

<script src="https://www.paypal.com/sdk/js?client-id=__CLIENT_ID__&components=card-fields&currency=EUR&intent=authorize"></script>
<script>
  const PAYPAL_ORDER_ID = "__PAYPAL_ORDER_ID__";
  const RETURN_URL = "__RETURN_URL__";

  async function initCardFields() {
    try {
      // 1. Ottieni il client token dal backend
      const tokenRes = await fetch("/api/v1/payment/paypal/client-token");
      if (!tokenRes.ok) throw new Error("Impossibile ottenere client token");
      const { client_token } = await tokenRes.json();

      // 2. Inizializza il SDK PayPal con il client token
      const sdk = await window.paypal.createInstance({
        clientToken: client_token,
        components: ["card-fields"],
      });

      // 3. Crea la sessione di pagamento
      const cardSession = sdk.createCardFieldsOneTimePaymentSession();

      // 4. Renderizza i campi
      const numberField = cardSession.createCardFieldsComponent({
        type: "number",
        placeholder: "4111 1111 1111 1111"
      });
      const expiryField = cardSession.createCardFieldsComponent({
        type: "expirationDate",
        placeholder: "MM/YY"
      });
      const cvvField = cardSession.createCardFieldsComponent({
        type: "cvv",
        placeholder: "123"
      });

      document.querySelector("#card-number").appendChild(numberField);
      document.querySelector("#card-expiry").appendChild(expiryField);
      document.querySelector("#card-cvv").appendChild(cvvField);

      // 5. Abilita il pulsante quando i campi sono validi
      cardSession.on("validitychange", (event) => {
        document.querySelector("#pay-button").disabled = !event.isValid;
      });

      // 6. Gestisci il click su "Paga"
      document.querySelector("#pay-button").addEventListener("click", async () => {
        const errorEl = document.querySelector("#error");
        errorEl.textContent = "";
        const btn = document.querySelector("#pay-button");
        btn.disabled = true;
        btn.textContent = "Elaborazione...";

        try {
          const { state, data } = await cardSession.submit(PAYPAL_ORDER_ID);

          if (state === "succeeded") {
            // Redirect al backend per completare l'autorizzazione
            window.location.href = RETURN_URL;
          } else if (state === "canceled") {
            errorEl.textContent = "Pagamento annullato.";
            btn.disabled = false;
            btn.textContent = "Paga € __AMOUNT__";
          } else {
            errorEl.textContent = "Errore: " + (data?.message || "Sconosciuto");
            btn.disabled = false;
            btn.textContent = "Paga € __AMOUNT__";
          }
        } catch (err) {
          errorEl.textContent = "Errore: " + err.message;
          btn.disabled = false;
          btn.textContent = "Paga € __AMOUNT__";
        }
      });

    } catch (err) {
      document.querySelector("#error").textContent = "Errore inizializzazione: " + err.message;
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

async def build_card_checkout_view(
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
    Mostra il WebView con i campi carta di PayPal (versione asincrona).
    """
    import asyncio

    # Prepara l'HTML
    html = CARD_CHECKOUT_HTML
    html = html.replace("__CLIENT_ID__", client_id)
    html = html.replace("__PAYPAL_ORDER_ID__", paypal_order_id)
    html = html.replace("__AMOUNT__", f"{amount:.2f}")
    html = html.replace(
        "__RETURN_URL__",
        f"https://incantopipe.it/api/v1/payment/paypal/card-success?order_id={order_id}"
    )

    # Polling: rileva quando l'ordine passa a "authorized"
    done = {"value": False}

    async def poll_status():
        for _ in range(200):  # ~6 minuti
            if done["value"]:
                return
            await asyncio.sleep(2)
            status = api.get_payment_status(order_id)
            if status.get("authorized"):
                done["value"] = True
                page.show_dialog(ft.SnackBar(
                    content=ft.Text("Pagamento autorizzato!"),
                    bgcolor=ft.Colors.GREEN_700,
                ))
                on_success(order_id)
                return
        if not done["value"]:
            page.show_dialog(ft.SnackBar(
                content=ft.Text("Timeout: pagamento non confermato."),
                bgcolor=ft.Colors.ORANGE_700,
            ))

    # Crea il WebView
    webview = fwv.WebView(
        url="about:blank",
        expand=True,
        on_console_message=lambda e: print(">>> WEBVIEW CONSOLE:", e.data),
        on_web_resource_error=lambda e: print(">>> WEBVIEW ERROR:", e.data),
    )

    # Abilita JavaScript PRIMA di caricare l'HTML
    await webview.set_javascript_mode(fwv.JavaScriptMode.UNRESTRICTED)

    # Carica l'HTML con i campi carta
    await webview.load_html(html)

    # Avvia il polling
    page.run_task(poll_status)

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
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=10,
            ),
        ], spacing=10, expand=True),
        padding=20,
        expand=True,
    )
    

    # Inietta l'HTML nel WebView usando un URL data: 
    # (alternativa: caricare una pagina HTML servita dal backend)
    import urllib.parse
    data_url = "data:text/html;charset=utf-8," + urllib.parse.quote(html)
    webview.url = data_url

    # Avvia il polling
    page.run_task(poll_status)

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
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=10,
            ),
        ], spacing=10, expand=True),
        padding=20,
        expand=True,
    )