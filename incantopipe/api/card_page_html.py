# api/card_page_html.py
"""HTML della pagina per i campi carta PayPal (Advanced Card Processing)."""

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
      const tokenRes = await fetch("/api/v1/payment/paypal/client-token");
      if (!tokenRes.ok) throw new Error("Impossibile ottenere client token (HTTP " + tokenRes.status + ")");
      const { client_token } = await tokenRes.json();

      const sdk = await window.paypal.createInstance({
        clientToken: client_token,
        components: ["card-fields"],
      });

      const cardSession = sdk.createCardFieldsOneTimePaymentSession();

      const numberField = cardSession.createCardFieldsComponent({
        type: "number", placeholder: "4111 1111 1111 1111"
      });
      const expiryField = cardSession.createCardFieldsComponent({
        type: "expirationDate", placeholder: "MM/YY"
      });
      const cvvField = cardSession.createCardFieldsComponent({
        type: "cvv", placeholder: "123"
      });

      document.querySelector("#card-number").appendChild(numberField);
      document.querySelector("#card-expiry").appendChild(expiryField);
      document.querySelector("#card-cvv").appendChild(cvvField);

      cardSession.on("validitychange", (event) => {
        document.querySelector("#pay-button").disabled = !event.isValid;
      });

      document.querySelector("#pay-button").addEventListener("click", async () => {
        const errorEl = document.querySelector("#error");
        errorEl.textContent = "";
        const btn = document.querySelector("#pay-button");
        btn.disabled = true;
        btn.textContent = "Elaborazione...";

        try {
          const { state, data } = await cardSession.submit(PAYPAL_ORDER_ID);
          if (state === "succeeded") {
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