# app/views/cart.py
import flet as ft
from api_client import APIClient
from config import MEDIA_BASE_URL


def build_cart_view(
    page: ft.Page,
    api: APIClient,
    session_key: str,
    on_checkout,
    on_back,
) -> ft.Container:
    cart_data = {"items": [], "total_items": 0, "total_price": 0}
    items_container = ft.Column(spacing=10)
    total_text = ft.Text("€ 0.00", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BROWN_700)

    def reload_cart():
        nonlocal cart_data
        cart_data = api.get_cart(session_key)
        render_items()

    def render_items():
        items_container.controls.clear()
        if not cart_data["items"]:
            items_container.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.SHOPPING_CART_OUTLINED, size=80, color=ft.Colors.GREY_400),
                        ft.Text("Il tuo carrello è vuoto", size=20, color=ft.Colors.GREY_700),
                        ft.TextButton("← Torna al catalogo", on_click=lambda e: on_back()),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    padding=50,
                )
            )
        else:
            for item in cart_data["items"]:
                image_url = (
                    f"{MEDIA_BASE_URL}/{item['product_image']}"
                    if item.get("product_image") else None
                )
                items_container.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Image(
                                src=image_url, width=80, height=80, fit=ft.BoxFit.COVER,
                            ) if image_url else ft.Container(
                                content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, color=ft.Colors.GREY_400),
                                width=80, height=80, bgcolor=ft.Colors.GREY_200,
                                alignment=ft.alignment.center,
                            ),
                            ft.Column([
                                ft.Text(item["product_name"], size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(f"€ {item['price']:.2f}", size=14, color=ft.Colors.BROWN_700),
                            ], expand=True, spacing=2),
                            ft.Row([
                                ft.IconButton(
                                    ft.Icons.REMOVE,
                                    on_click=lambda e, i=item: update_quantity(i["id"], i["quantity"] - 1),
                                ),
                                ft.Text(str(item["quantity"]), size=16, width=30, text_align=ft.TextAlign.CENTER),
                                ft.IconButton(
                                    ft.Icons.ADD,
                                    on_click=lambda e, i=item: update_quantity(i["id"], i["quantity"] + 1),
                                ),
                                ft.IconButton(
                                    ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED,
                                    on_click=lambda e, i=item: remove_item(i["id"]),
                                ),
                            ], spacing=0),
                        ], spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=8,
                    )
                )
        total_text.value = f"€ {cart_data['total_price']:.2f}"
        page.update()

    def update_quantity(item_id: int, new_qty: int):
        if new_qty <= 0:
            remove_item(item_id)
            return
        if api.update_cart_item(session_key, item_id, new_qty):
            reload_cart()

    def remove_item(item_id: int):
        if api.remove_from_cart(session_key, item_id):
            reload_cart()

    reload_cart()

    return ft.Container(
        content=ft.Column([
            ft.TextButton("← Torna al catalogo", on_click=lambda e: on_back()),
            ft.Text("Carrello", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BROWN_700),
            items_container,
            ft.Divider(),
            ft.Row([
                ft.Text("Totale:", size=18, weight=ft.FontWeight.BOLD),
                total_text,
            ], alignment=ft.MainAxisAlignment.END),
            ft.Row([
                ft.ElevatedButton(
                    "Procedi all'ordine",
                    icon=ft.Icons.CHECK,
                    on_click=lambda e: on_checkout(),
                    disabled=not cart_data["items"],
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE),
                ),
            ], alignment=ft.MainAxisAlignment.END),
        ], spacing=15),
        padding=20,
    )