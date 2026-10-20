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
  
    <div class="label">Nome titolare carta</div>
    <input type="text" id="cardholder-name" class="field-container"
         style="width: 100%; box-sizing: border-box;"
         placeholder="Mario Rossi" />

  <button id="pay-button" disabled>Paga € __AMOUNT__</button>
  <div id="error"></div>
  <div class="note">Pagamento sicuro gestito da PayPal</div>
</div>

<!-- SDK v6 CORE (Live) -->
<script async src="https://www.paypal.com/web-sdk/v6/core"
        onload="onPayPalWebSdkLoaded()"></script>

<script>
  const PAYPAL_ORDER_ID = "__PAYPAL_ORDER_ID__";
  const RETURN_URL = "__RETURN_URL__";
  const AMOUNT = "__AMOUNT__";

  async function onPayPalWebSdkLoaded() {
    try {
      // 1. Ottieni client token dal backend
      const tokenRes = await fetch("/api/v1/payment/paypal/client-token");
      if (!tokenRes.ok) {
        throw new Error("Impossibile ottenere client token (HTTP " + tokenRes.status + ")");
      }
      const { client_token } = await tokenRes.json();

      // 2. Inizializza SDK v6
      const sdk = await window.paypal.createInstance({
        clientToken: client_token,
        components: ["card-fields"],
      });

      // 3. Crea sessione pagamento one-time
      const cardSession = sdk.createCardFieldsOneTimePaymentSession();

      // 4. Renderizza i campi
      const numberField = cardSession.createCardFieldsComponent({
        type: "number",
        placeholder: "4111 1111 1111 1111",
      });
      const expiryField = cardSession.createCardFieldsComponent({
        type: "expiry",
        placeholder: "MM/YY",
      });
      const cvvField = cardSession.createCardFieldsComponent({
        type: "cvv",
        placeholder: "123",
      });

      document.querySelector("#card-number").appendChild(numberField);
      document.querySelector("#card-expiry").appendChild(expiryField);
      document.querySelector("#card-cvv").appendChild(cvvField);

      // 5. Abilita pulsante quando i campi sono validi
      async function updateButtonState() {
  try {
    const state = await cardSession.getState();
    const allValid = Object.values(state.fields).every(f => f.isValid);
    document.querySelector("#pay-button").disabled = !allValid;
  } catch (err) {
    console.error("Errore getState:", err);
  }
}

// Ascolta i cambiamenti su ogni campo
      // Validazione: tutti i campi carta + nome titolare
          // Validazione: tutti i campi carta + nome titolare
      async function updateButtonState() {
        try {
          const state = await cardSession.getState();
          const allFieldsValid = Object.values(state.fields).every(f => f.isValid);
          const nameValid = document.querySelector("#cardholder-name").value.trim().length >= 3;
          document.querySelector("#pay-button").disabled = !(allFieldsValid && nameValid);
        } catch (err) {
          console.error("Errore getState:", err);
        }
      }

      cardSession.on("validitychange", updateButtonState);
      cardSession.on("onChange", updateButtonState);
      document.querySelector("#cardholder-name").addEventListener("input", updateButtonState);ml>
"""