# app/views/admin_orders.py
import flet as ft
from api_client import APIClient


def build_admin_orders_view(
    page,
    api,
    on_order_click,
    on_back,
) -> ft.Container:
    """Lista ordini per l'admin, con filtro per stato."""

    # Stato locale della vista: stato attualmente filtrato
    current_status = {"value": "authorized"}

    orders_container = ft.Column(spacing=10)

    def stato_badge(status: str) -> ft.Container:
        color_map = {
            "pending": ft.Colors.ORANGE,
            "authorized": ft.Colors.BLUE,
            "paid": ft.Colors.GREEN,
            "shipped": ft.Colors.PURPLE,
            "delivered": ft.Colors.TEAL,
            "cancelled": ft.Colors.RED,
        }
        label_map = {
            "pending": "In attesa",
            "authorized": "Autorizzato",
            "paid": "Pagato",
            "shipped": "Spedito",
            "delivered": "Consegnato",
            "cancelled": "Annullato",
        }
        return ft.Container(
            content=ft.Text(label_map.get(status, status),
                            size=11, color=ft.Colors.WHITE),
            bgcolor=color_map.get(status, ft.Colors.GREY),
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
        )

    def render_orders():
        orders_container.controls.clear()
        orders = api.admin_list_orders(current_status["value"])

        if not orders:
            orders_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        f"Nessun ordine in stato '{current_status['value']}'",
                        size=16, color=ft.Colors.GREY_700,
                    ),
                    padding=30,
                )
            )
        else:
            for o in orders:
                orders_container.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"#{o['order_number']}",
                                        size=14, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f"{o['first_name']} {o['last_name']}",
                                    size=12, color=ft.Colors.GREY_700,
                                ),
                                ft.Text(
                                    f"{o['created'][:10]}  ·  "
                                    f"{len(o['items'])} articol"
                                    f"{'o' if len(o['items']) == 1 else 'i'}",
                                    size=11, color=ft.Colors.GREY_600,
                                ),
                            ], expand=True, spacing=2),
                            ft.Column([
                                ft.Text(f"€ {o['total']:.2f}", size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.BROWN_700),
                                stato_badge(o["status"]),
                            ], horizontal_alignment=ft.CrossAxisAlignment.END,
                                spacing=4),
                        ]),
                        padding=15,
                        border=ft.Border.all(1, ft.Colors.GREY_300),
                        border_radius=10,
                        on_click=lambda e, oid=o["id"]: on_order_click(oid),
                    )
                )

        page.update()

    def on_status_change(e):
        current_status["value"] = e.control.value
        render_orders()

    status_dropdown = ft.Dropdown(
        label="Stato",
        value="authorized",
        options=[
            ft.dropdown.Option("authorized", "Autorizzati (da spedire)"),
            ft.dropdown.Option("shipped", "Spediti"),
            ft.dropdown.Option("delivered", "Consegnati"),
            ft.dropdown.Option("pending", "In attesa"),
            ft.dropdown.Option("cancelled", "Annullati"),
        ],
        on_select=on_status_change,
        width=300,
    )

    render_orders()

    return ft.Container(
        content=ft.Column([
            ft.TextButton("← Torna alla home",
                          on_click=lambda e: on_back()),
            ft.Text("Gestione ordini", size=28,
                    weight=ft.FontWeight.BOLD, color=ft.Colors.BROWN_700),
            ft.Container(height=5),
            status_dropdown,
            ft.Container(height=10),
            orders_container,
        ], spacing=10),
        padding=20,
    )


def build_admin_order_detail_view(
    page,
    api,
    order_id: int,
    on_back,
    on_ship_done,
    on_cancel_done,
) -> ft.Container:
    """Dettaglio ordine per l'admin, con pulsanti Spedisci/Annulla."""

    # Trova l'ordine tra gli "authorized" (e altri stati)
    order = None
    for status in ["authorized", "shipped", "delivered", "pending", "cancelled"]:
        orders = api.admin_list_orders(status)
        for o in orders:
            if o["id"] == order_id:
                order = o
                break
        if order:
            break

    if not order:
        return ft.Container(
            content=ft.Column([
                ft.Text("Ordine non trovato", size=20),
                ft.TextButton("← Torna agli ordini",
                              on_click=lambda e: on_back()),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40,
        )

    error_text = ft.Text("", color=ft.Colors.RED_700, size=13, visible=False)
    loading = ft.ProgressRing(width=20, height=20, visible=False)

    def stato_badge(status: str) -> ft.Container:
        color_map = {
            "pending": ft.Colors.ORANGE,
            "authorized": ft.Colors.BLUE,
            "paid": ft.Colors.GREEN,
            "shipped": ft.Colors.PURPLE,
            "delivered": ft.Colors.TEAL,
            "cancelled": ft.Colors.RED,
        }
        label_map = {
            "pending": "In attesa",
            "authorized": "Autorizzato",
            "paid": "Pagato",
            "shipped": "Spedito",
            "delivered": "Consegnato",
            "cancelled": "Annullato",
        }
        return ft.Container(
            content=ft.Text(label_map.get(status, status),
                            size=11, color=ft.Colors.WHITE),
            bgcolor=color_map.get(status, ft.Colors.GREY),
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
        )

    # ---- Articoli ----
    articoli_rows = []
    for item in order["items"]:
        articoli_rows.append(
            ft.Row([
                ft.Text(item["product_name"], size=14, expand=True),
                ft.Text(f"x{item['quantity']}", size=14, width=40),
                ft.Text(f"€ {item['total']:.2f}", size=14, width=90,
                        text_align=ft.TextAlign.RIGHT),
            ])
        )

    card_articoli = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Articoli", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                *articoli_rows,
                ft.Divider(),
                ft.Row([
                    ft.Text("Totale", size=15, weight=ft.FontWeight.BOLD,
                            expand=True),
                    ft.Text(f"€ {order['total']:.2f}", size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BROWN_700),
                ]),
            ]),
            padding=20,
        )
    )

    # ---- Cliente e spedizione ----
    card_cliente = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Cliente", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"{order['first_name']} {order['last_name']}", size=14),
                ft.Text(order["email"], size=13, color=ft.Colors.GREY_700),
                ft.Text(order["phone"] or "—", size=13, color=ft.Colors.GREY_700),
                ft.Container(height=10),
                ft.Text("Indirizzo di spedizione", size=14,
                        weight=ft.FontWeight.BOLD),
                ft.Text(order["address"], size=13),
                ft.Text(
                    f"{order['postal_code']} {order['city']} ({order['province']})",
                    size=13),
                ft.Text(order["country"], size=13),
            ], spacing=3),
            padding=20,
        )
    )

    # ---- Info ordine ----
    card_info = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Informazioni ordine", size=16,
                        weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([
                    ft.Text("Numero:", size=13, weight=ft.FontWeight.BOLD,
                            width=110),
                    ft.Text(order["order_number"], size=13),
                ]),
                ft.Row([
                    ft.Text("Data:", size=13, weight=ft.FontWeight.BOLD,
                            width=110),
                    ft.Text(order["created"][:10], size=13),
                ]),
                ft.Row([
                    ft.Text("Stato:", size=13, weight=ft.FontWeight.BOLD,
                            width=110),
                    stato_badge(order["status"]),
                ]),
                ft.Row([
                    ft.Text("Pagamento:", size=13, weight=ft.FontWeight.BOLD,
                            width=110),
                    ft.Text(order["payment_method"], size=13),
                ]),
                ft.Row([
                    ft.Text("Stato pag.:", size=13, weight=ft.FontWeight.BOLD,
                            width=110),
                    ft.Text(order["payment_status"], size=13),
                ]),
            ], spacing=5),
            padding=20,
        )
    )

    # ---- Azioni admin ----
    def do_ship(e):
        # Apriamo un dialog per chiedere il tracking number
        tracking_field = ft.TextField(
            label="Codice di Tracciamento (opzionale)",
            hint_text="es. 123456789",
            width=300,
        )
        error_dialog = ft.Text("", color=ft.Colors.RED_700, size=12, visible=False)

        def confirm_ship(ev):
            page.pop_dialog()
            error_text.visible = False
            loading.visible = True
            page.update()

            # Chiamata API con il tracking number
            success, result = api.admin_ship_order(order_id, tracking_field.value.strip())
            loading.visible = False

            if success:
                page.show_dialog(ft.SnackBar(
                    content=ft.Text("Ordine spedito e pagamento incassato"),
                    bgcolor=ft.Colors.GREEN_700,
                ))
                on_ship_done(order_id)
            else:
                error_text.value = f"Errore: {result}"
                error_text.visible = True
                page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Spedisci ordine"),
            content=ft.Column([
                ft.Text("Inserisci il codice di tracciamento per il cliente (opzionale)."),
                tracking_field,
                error_dialog,
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Annulla", on_click=lambda e: page.pop_dialog()),
                ft.Button(
                    content=ft.Text("Conferma e Incassa"),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                    on_click=confirm_ship,
                ),
            ],
        )
        page.show_dialog(dialog)

    def do_cancel(e):
        def confirm_cancel(ev):
            page.pop_dialog()
            error_text.visible = False
            loading.visible = True
            page.update()

            success, result = api.admin_cancel_order(order_id)
            loading.visible = False

            if success:
                page.show_dialog(ft.SnackBar(
                    content=ft.Text("Ordine annullato"),
                    bgcolor=ft.Colors.GREEN_700,
                ))
                on_cancel_done(order_id)
            else:
                error_text.value = f"Errore: {result}"
                error_text.visible = True
                page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Annulla ordine"),
            content=ft.Text(
                "Sei sicuro di voler annullare questo ordine?\n"
                "L'autorizzazione PayPal verrà annullata e lo stock ripristinato."
            ),
            actions=[
                ft.TextButton("No, torna indietro",
                              on_click=lambda e: page.pop_dialog()),
                ft.TextButton("Sì, annulla",
                              on_click=confirm_cancel),
            ],
        )
        page.show_dialog(dialog)

    azioni = []
    if order["status"] == "authorized":
        azioni.append(
            ft.Button(
                content=ft.Text("Spedisci e incassa"),
                icon=ft.Icons.LOCAL_SHIPPING,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.GREEN_700,
                    color=ft.Colors.WHITE,
                ),
                on_click=do_ship,
            )
        )
        azioni.append(
            ft.Button(
                content=ft.Text("Annulla ordine"),
                icon=ft.Icons.CANCEL,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.RED_700,
                    color=ft.Colors.WHITE,
                ),
                on_click=do_cancel,
            )
        )

    blocco_azioni = ft.Row(azioni, alignment=ft.MainAxisAlignment.END,
                            spacing=10)

    return ft.Container(
        content=ft.Column([
            ft.TextButton("← Torna agli ordini",
                          on_click=lambda e: on_back()),
            ft.Text(f"Ordine #{order['order_number']}", size=24,
                    weight=ft.FontWeight.BOLD, color=ft.Colors.BROWN_700),
            ft.Container(height=10),
            ft.ResponsiveRow([
                ft.Container(card_articoli, col={"xs": 12, "md": 7}),
                ft.Container(
                    ft.Column([card_info, card_cliente], spacing=15),
                    col={"xs": 12, "md": 5},
                ),
            ], spacing=20, run_spacing=20),
            ft.Container(height=10),
            error_text,
            ft.Row([loading], alignment=ft.MainAxisAlignment.CENTER),
            blocco_azioni,
        ], spacing=10),
        padding=20,
    )