# app/views/orders.py
import flet as ft
from api_client import APIClient
from config import MEDIA_BASE_URL


# ============================================================
# VISTA LISTA ORDINI
# ============================================================

def build_orders_list_view(
    page: ft.Page,
    api: APIClient,
    on_order_click,
    on_back,
) -> ft.Container:
    """Lista degli ordini dell'utente autenticato."""

    orders = api.get_orders()

    if not orders:
        return ft.Container(
            content=ft.Column([
                ft.TextButton("← Torna alla home", on_click=lambda e: on_back()),
                ft.Container(height=40),
                ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=80,
                        color=ft.Colors.GREY_400),
                ft.Text("Non hai ancora effettuato ordini", size=20,
                        color=ft.Colors.GREY_700),
                ft.Text("Scopri le nostre pipe artigianali", size=14,
                        color=ft.Colors.GREY_600),
                ft.Container(height=20),
                ft.TextButton("Vai allo shopping",
                              on_click=lambda e: on_back()),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=40,
        )

    def stato_badge(status: str) -> ft.Container:
        color_map = {
            "pending": ft.Colors.ORANGE,
            "paid": ft.Colors.GREEN,
            "shipped": ft.Colors.BLUE,
            "delivered": ft.Colors.PURPLE,
            "cancelled": ft.Colors.RED,
        }
        label_map = {
            "pending": "In attesa",
            "paid": "Pagato",
            "shipped": "Spedito",
            "delivered": "Consegnato",
            "cancelled": "Annullato",
        }
        color = color_map.get(status, ft.Colors.GREY)
        label = label_map.get(status, status)
        return ft.Container(
            content=ft.Text(label, size=11, color=ft.Colors.WHITE),
            bgcolor=color,
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
        )

    rows = []
    for o in orders:
        rows.append(
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(f"Ordine #{o['order_number']}",
                                size=15, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            f"{o['created'][:10]}  ·  {o['item_count']} articol{'o' if o['item_count'] == 1 else 'i'}",
                            size=12, color=ft.Colors.GREY_600,
                        ),
                    ], expand=True, spacing=2),
                    ft.Column([
                        ft.Text(f"€ {o['total']:.2f}", size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BROWN_700),
                        stato_badge(o["status"]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=4),
                ]),
                padding=15,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                on_click=lambda e, oid=o["id"]: on_order_click(oid),
            )
        )

    return ft.Container(
        content=ft.Column([
            ft.TextButton("← Torna alla home", on_click=lambda e: on_back()),
            ft.Text("I miei ordini", size=28, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BROWN_700),
            ft.Container(height=10),
            ft.Column(rows, spacing=10),
        ], spacing=10),
        padding=20,
    )


# ============================================================
# VISTA DETTAGLIO ORDINE
# ============================================================

def build_order_detail_view(
    page: ft.Page,
    api: APIClient,
    order_id: int,
    on_back,
    on_cancel=None,
) -> ft.Container:
    """Dettaglio di un ordine."""

    order = api.get_order(order_id)

    if not order:
        return ft.Container(
            content=ft.Column([
                ft.Text("Ordine non trovato", size=20),
                ft.TextButton("← Torna agli ordini", on_click=lambda e: on_back()),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40,
        )

    # Badge stato
    stato_map = {
        "pending": ("In attesa", ft.Colors.ORANGE),
        "paid": ("Pagato", ft.Colors.GREEN),
        "shipped": ("Spedito", ft.Colors.BLUE),
        "delivered": ("Consegnato", ft.Colors.PURPLE),
        "cancelled": ("Annullato", ft.Colors.RED),
    }
    status_label, status_color = stato_map.get(
        order["status"], (order["status"], ft.Colors.GREY)
    )

    # Articoli
    articoli_rows = []
    for item in order["items"]:
        articoli_rows.append(
            ft.Row([
                ft.Text(item["product_name"], size=14, expand=True),
                ft.Text(f"x{item['quantity']}", size=14, width=40),
                ft.Text(f"€ {item['price']:.2f}", size=14, width=80,
                        text_align=ft.TextAlign.RIGHT),
                ft.Text(f"€ {item['total']:.2f}", size=14, width=90,
                        weight=ft.FontWeight.BOLD,
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
                    ft.Text("Totale", size=16, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text(f"€ {order['total']:.2f}", size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BROWN_700),
                ]),
            ]),
            padding=20,
        )
    )

    # Indirizzo
    card_indirizzo = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Indirizzo di spedizione", size=16,
                        weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"{order['first_name']} {order['last_name']}", size=14),
                ft.Text(order["address"], size=14),
                ft.Text(f"{order['postal_code']} {order['city']} ({order['province']})",
                        size=14),
                ft.Text(order["country"], size=14),
                ft.Text(order["email"], size=13, color=ft.Colors.GREY_600),
                ft.Text(order["phone"] or "", size=13, color=ft.Colors.GREY_600),
            ], spacing=3),
            padding=20,
        )
    )

    # Metadati
    card_meta = ft.Card(
        content=ft.Container(
            content=ft.Column([
                # ... (il contenuto di card_meta che hai già)
            ], spacing=5),
            padding=20,
        )
    )

    # === BLOCCO AZIONI — INIZIO ===
    azioni = []
    if order["status"] == "pending":
        def do_cancel(e):
            confirm = ft.AlertDialog(
                title=ft.Text("Annulla ordine"),
                content=ft.Text(
                    "Sei sicuro di voler annullare questo ordine?\n"
                    "L'articolo tornerà disponibile nel catalogo."
                ),
                actions=[
                    ft.TextButton(
                        "No, torna indietro",
                        on_click=lambda e: page.pop_dialog(),
                    ),
                    ft.TextButton(
                        "Sì, annulla",
                        on_click=lambda e: (page.pop_dialog(), on_cancel(order_id)),
                    ),
                ],
            )
            page.show_dialog(confirm)

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

    blocco_azioni = ft.Row(azioni, alignment=ft.MainAxisAlignment.END)
    # === BLOCCO AZIONI — FINE ===

    return ft.Container(
        content=ft.Column([
            ft.TextButton("← Torna agli ordini", on_click=lambda e: on_back()),
            ft.Text(f"Ordine #{order['order_number']}", size=24,
                    weight=ft.FontWeight.BOLD, color=ft.Colors.BROWN_700),
            ft.Container(height=10),
            ft.ResponsiveRow([
                ft.Container(card_articoli, col={"xs": 12, "md": 7}),
                ft.Container(
                    ft.Column([card_meta, card_indirizzo], spacing=15),
                    col={"xs": 12, "md": 5},
                ),
            ], spacing=20, run_spacing=20),
            ft.Container(height=10),
            blocco_azioni,
        ], spacing=10),
        padding=20,
    )

        # Pulsante "Annulla ordine" (solo per ordini pending)
    azioni = []
    if order["status"] == "pending":
        def do_cancel(e):
            confirm = ft.AlertDialog(
                title=ft.Text("Annulla ordine"),
                content=ft.Text(
                    "Sei sicuro di voler annullare questo ordine?\n"
                    "L'articolo tornerà disponibile nel catalogo."
                ),
                actions=[
                    ft.TextButton(
                        "No, torna indietro",
                        on_click=lambda e: page.pop_dialog(),
                    ),
                    ft.TextButton(
                        "Sì, annulla",
                        on_click=lambda e: (page.pop_dialog(), on_cancel(order_id)),
                    ),
                ],
            )
            page.show_dialog(confirm)

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

    blocco_azioni = ft.Row(azioni, alignment=ft.MainAxisAlignment.END)
    
    return ft.Container(
        content=ft.Column([
            ft.TextButton("← Torna agli ordini", on_click=lambda e: on_back()),
            ft.Text(f"Ordine #{order['order_number']}", size=24,
                    weight=ft.FontWeight.BOLD, color=ft.Colors.BROWN_700),
            ft.Container(height=10),
            ft.ResponsiveRow([
                ft.Container(card_articoli, col={"xs": 12, "md": 7}),
                ft.Container(
                    ft.Column([card_meta, card_indirizzo], spacing=15),
                    col={"xs": 12, "md": 5},
                ),
            ], spacing=20, run_spacing=20),
            ft.Container(height=10),
            blocco_azioni,                                # ← QUESTA RIGA
        ], spacing=10),
        padding=20,
    )