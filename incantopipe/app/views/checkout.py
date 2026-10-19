# app/views/checkout.py
import flet as ft
import asyncio
from api_client import APIClient
from config import MEDIA_BASE_URL


def build_checkout_view(page, api, user, on_success, on_back) -> ft.Container:
    """Vista di checkout: riepilogo + indirizzo + metodo pagamento."""

    cart = api.get_cart()

    if not cart["items"]:
        return ft.Container(
            content=ft.Column([
                ft.Text("Il carrello è vuoto", size=24),
                ft.TextButton("← Torna al carrello", on_click=lambda e: on_back()),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=50,
        )

    # ---- Riepilogo articoli ----
    riepilogo_rows = []
    for item in cart["items"]:
        riepilogo_rows.append(
            ft.Row([
                ft.Text(item["product_name"], size=14, expand=True),
                ft.Text(f"x{item['quantity']}", size=14, width=40),
                ft.Text(f"€ {item['total']:.2f}", size=14, width=90,
                        text_align=ft.TextAlign.RIGHT),
            ])
        )
    riepilogo_rows.append(ft.Divider())
    riepilogo_rows.append(
        ft.Row([
            ft.Text("Totale", size=16, weight=ft.FontWeight.BOLD, expand=True),
            ft.Text(f"€ {cart['total_price']:.2f}", size=18,
                    weight=ft.FontWeight.BOLD, color=ft.Colors.BROWN_700),
        ])
    )

    card_riepilogo = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Riepilogo ordine", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                *riepilogo_rows,
            ]),
            padding=20,
        )
    )

    # ---- Form indirizzo ----
    first_name_field = ft.TextField(label="Nome *", value=user.get("first_name", ""),
                                     width=300, text_size=14)
    last_name_field = ft.TextField(label="Cognome *", value=user.get("last_name", ""),
                                    width=300, text_size=14)
    email_field = ft.TextField(label="Email *", value=user.get("email", ""),
                                width=300, text_size=14,
                                keyboard_type=ft.KeyboardType.EMAIL)
    phone_field = ft.TextField(label="Telefono", width=300, text_size=14,
                                keyboard_type=ft.KeyboardType.PHONE)
    address_field = ft.TextField(label="Indirizzo *", width=300, text_size=14)
    postal_code_field = ft.TextField(label="CAP *", width=140, text_size=14)
    city_field = ft.TextField(label="Città *", width=200, text_size=14)
    province_field = ft.TextField(label="Provincia", width=100, text_size=14,
                                   max_length=2)
    country_field = ft.TextField(label="Paese", value="Italia", width=200,
                                  text_size=14)
    notes_field = ft.TextField(label="Note per la spedizione", multiline=True,
                                min_lines=2, max_lines=4, width=300, text_size=14)

    # ---- Metodo pagamento ----
    payment_radio = ft.RadioGroup(
        value="paypal",
        content=ft.Column([
            ft.Radio(value="paypal", label="PayPal"),
            ft.Radio(value="credit_card", label="Carta di credito / debito"),
        ]),
    )

    error_text = ft.Text("", color=ft.Colors.RED_700, size=13, visible=False)
    loading = ft.ProgressRing(width=20, height=20, visible=False)

    # ============================================================
    # DEFINIZIONE do_confirm
    # ============================================================
    async def do_confirm(e):
        error_text.visible = False

        # Validazione
        required = [
            (first_name_field, "Nome"),
            (last_name_field, "Cognome"),
            (email_field, "Email"),
            (address_field, "Indirizzo"),
            (postal_code_field, "CAP"),
            (city_field, "Città"),
        ]
        for field, name in required:
            if not field.value or not field.value.strip():
                error_text.value = f"Il campo '{name}' è obbligatorio."
                error_text.visible = True
                page.update()
                return

        loading.visible = True
        page.update()

        order_data = {
            "first_name": first_name_field.value.strip(),
            "last_name": last_name_field.value.strip(),
            "email": email_field.value.strip(),
            "phone": phone_field.value.strip(),
            "address": address_field.value.strip(),
            "postal_code": postal_code_field.value.strip(),
            "city": city_field.value.strip(),
            "province": province_field.value.strip(),
            "country": country_field.value.strip() or "Italia",
            "shipping_notes": notes_field.value.strip(),
            "payment_method": payment_radio.value,
        }

        # 1. Crea l'ordine
        success, data = api.create_order(order_data)
        loading.visible = False

        if not success:
            error_text.value = data
            error_text.visible = True
            page.update()
            return

        order_id = data["id"]

        # 2. Se PayPal, avvia l'autorizzazione
        if payment_radio.value == "paypal":
            auth_success, auth_data = api.paypal_authorize(order_id)
            if not auth_success:
                error_text.value = f"Errore PayPal: {auth_data}"
                error_text.visible = True
                page.update()
                return

            approve_url = auth_data.get("approve_url")
            if approve_url:
                launcher = ft.UrlLauncher()
                page.services.append(launcher)
                await launcher.launch_url(approve_url)

            show_waiting_screen(order_id)

        elif payment_radio.value == "credit_card":
            config = api.paypal_config()
            if not config.get("client_id"):
                error_text.value = "Configurazione PayPal mancante"
                error_text.visible = True
                page.update()
                return

            card_success, card_data = api.paypal_card_order(order_id)
            if not card_success:
                error_text.value = f"Errore: {card_data}"
                error_text.visible = True
                page.update()
                return

            # Apri la pagina della carta nel BROWSER
            url = f"https://incantopipe.it/api/v1/payment/paypal/card-page?order_id={order_id}"
            launcher = ft.UrlLauncher()
            page.services.append(launcher)
            await launcher.launch_url(url)

            # Mostra la schermata di attesa con polling
            show_waiting_screen(order_id)
    # ============================================================
    # DEFINIZIONE show_waiting_screen
    # ============================================================
    def show_waiting_screen(order_id: int):
        """Sostituisce il contenuto con una schermata di attesa + polling."""

        async def poll_status():
            max_attempts = 100  # 100 * 3s = 5 min
            for attempt in range(max_attempts):
                await asyncio.sleep(3)
                status_data = api.get_payment_status(order_id)
                if status_data.get("authorized"):
                    page.show_dialog(ft.SnackBar(
                        content=ft.Text("Pagamento autorizzato!"),
                        bgcolor=ft.Colors.GREEN_700,
                    ))
                    on_success({"id": order_id, "order_number": ""})
                    return

            page.show_dialog(ft.SnackBar(
                content=ft.Text("Timeout: pagamento non confermato. Riprova."),
                bgcolor=ft.Colors.ORANGE_700,
            ))

        # Sostituisci il contenuto della pagina
        if len(page.controls) > 2:
            content_area = page.controls[2]
            content_area.controls.clear()
            content_area.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.ProgressRing(width=60, height=60),
                        ft.Container(height=20),
                        ft.Text("In attesa del pagamento...", size=20,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Completa il pagamento nella finestra di PayPal che si è aperta.",
                            size=14, color=ft.Colors.GREY_600,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=20),
                        ft.TextButton(
                            "Annulla e torna al carrello",
                            on_click=lambda e: on_back(),
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=50,
                )
            )
            page.update()

        page.run_task(poll_status)

    # ============================================================
    # LAYOUT FINALE (dopo le definizioni)
    # ============================================================

    confirm_button = ft.Button(
        content=ft.Text("Conferma ordine", size=16, weight=ft.FontWeight.BOLD),
        width=300,
        height=50,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BROWN_700,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=lambda e: page.run_task(do_confirm, e),
    )

    card_form = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Indirizzo di spedizione", size=18,
                        weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([first_name_field, last_name_field],
                       spacing=10, wrap=True),
                ft.Row([email_field, phone_field], spacing=10, wrap=True),
                address_field,
                ft.Row([postal_code_field, city_field, province_field],
                       spacing=10, wrap=True),
                country_field,
                notes_field,
                ft.Divider(),
                ft.Text("Metodo di pagamento", size=18,
                        weight=ft.FontWeight.BOLD),
                payment_radio,
                ft.Container(height=10),
                error_text,
                ft.Row([loading], alignment=ft.MainAxisAlignment.CENTER),
                confirm_button,
            ]),
            padding=20,
        )
    )

    return ft.Container(
        content=ft.Column([
            ft.TextButton("← Torna al carrello",
                          on_click=lambda e: on_back()),
            ft.Text("Checkout", size=28, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BROWN_700),
            ft.Container(height=10),
            ft.ResponsiveRow([
                ft.Container(card_riepilogo, col={"xs": 12, "md": 5}),
                ft.Container(card_form, col={"xs": 12, "md": 7}),
            ], spacing=20, run_spacing=20),
        ], spacing=10),
        padding=20,
    )