# api/card_page_html.py
"""HTML della pagina per i campi carta PayPal (Advanced Card Processing, SDK v6)."""

CARD_CHECKOUT_HTML = """
<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pagamento con carta</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         margin: 0; padding: 20px; background: #fafafa; }
  .container { max-width: 500px; margin: 0 auto; }
  h2 { color: #5d3a1a; margin-bottom: 20px; font-size: 22px; }
  .field-container { height: 45px; border: 1px solid #ccc; border-radius: 6px;
                     padding: 0 10px; margin-bottom: 12px; background: white; }
  #pay-button { width: 100%; height: 50px; background: #5d3a1a; color: white;
                border: none; border-radius: 8px; font-size: 16px;
                font-weight: bold; cursor: pointer; margin-top: 10px; }
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

  <div class="label">Nome titolare carta</div>
  <div class="field-container" id="card-name"></div>

  <button id="pay-button" disabled>Paga € __AMOUNT__</button>
  <div id="error"></div>
  <div class="note">Pagamento sicuro gestito da PayPal</div>
</div>

<script async src="https://www.paypal.com/web-sdk/v6/core"
        onload="onPayPalWebSdkLoaded()"></script>

<script>
  const PAYPAL_ORDER_ID = "__PAYPAL_ORDER_ID__";
  const RETURN_URL = "__RETURN_URL__";
  const AMOUNT = "__AMOUNT__";

  async function onPayPalWebSdkLoaded() {
    const errorEl = document.querySelector("#error");
    try {
      const tokenRes = await fetch("/api/v1/payment/paypal/client-token");
      if (!tokenRes.ok) {
        throw new Error("Impossibile ottenere client token (HTTP " + tokenRes.status + ")");
      }
      const { client_token } = await tokenRes.json();

      const sdk = await window.paypal.createInstance({
        clientToken: client_token,
        components: ["card-fields"],
      });

      const cardSession = sdk.createCardFieldsOneTimePaymentSession();
      window.cardSession = cardSession;   // per debug

      const numberField = cardSession.createCardFieldsComponent({
        type: "number", placeholder: "4111 1111 1111 1111",
      });
      const expiryField = cardSession.createCardFieldsComponent({
        type: "expiry", placeholder: "MM/YY",
      });
      const cvvField = cardSession.createCardFieldsComponent({
        type: "cvv", placeholder: "123",
      });
      const nameField = cardSession.createCardFieldsComponent({
        type: "name", placeholder: "Mario Rossi",
      });

      document.querySelector("#card-number").appendChild(numberField);
      document.querySelector("#card-expiry").appendChild(expiryField);
      document.querySelector("#card-cvv").appendChild(cvvField);
      document.querySelector("#card-name").appendChild(nameField);

      const payButton = document.querySelector("#pay-button");
      payButton.disabled = false;
      payButton.textContent = "Paga € " + AMOUNT;

      payButton.addEventListener("click", async () => {
        errorEl.textContent = "";
        payButton.disabled = true;
        payButton.textContent = "Elaborazione...";

        try {
          const { state, data } = await cardSession.submit(PAYPAL_ORDER_ID, {
            contingencies: ["SCA_ALWAYS"]
          });

          if (state === "succeeded") {
            if (data.liabilityShift === "POSSIBLE" || data.liabilityShift === "YES") {
              window.location.href = RETURN_URL;
            } else {
              errorEl.textContent = "Autenticazione 3D Secure non completata. Usa un'altra carta o PayPal.";
              payButton.disabled = false;
              payButton.textContent = "Paga € " + AMOUNT;
            }
          } else if (state === "canceled") {
            errorEl.textContent = "Pagamento annullato.";
            payButton.disabled = false;
            payButton.textContent = "Paga € " + AMOUNT;
          } else {
            errorEl.textContent = "Errore: " + JSON.stringify(data, null, 2);
            console.error("STATO SUBMIT:", state, "DATI:", data);
            payButton.disabled = false;
            payButton.textContent = "Paga € " + AMOUNT;
          }
        } catch (err) {
          errorEl.textContent = "Errore: " + err.message;
          payButton.disabled = false;
          payButton.textContent = "Paga € " + AMOUNT;
        }
      });

    } catch (err) {
      errorEl.textContent = "Errore inizializzazione: " + err.message;
    }
  }
</script>
</body>
</html>
"""