# app/main.py
import flet as ft
import uuid
from api_client import APIClient
from components.header import build_header
from views.catalog import build_catalog_view
from views.product_detail import build_product_detail_view
from views.cart import build_cart_view

api = APIClient()


def main(page: ft.Page):
    page.title = "InCantoPipe"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # Sessione anonima univoca per questo client
    session_key = str(uuid.uuid4())[:32]

    state = {
        "category_slug": "", "material": "", "finish": "",
        "search": "", "sort": "-created",
    }

    content_area = ft.Column()
    header_area = ft.Column()

    def update_header():
        cart = api.get_cart(session_key)
        header_area.controls.clear()
        header_area.controls.append(
            build_header(
                on_home_click=lambda e: go_home(),
                on_cart_click=lambda e: go_cart(),
                cart_count=cart["total_items"],
            )
        )
        page.update()

    def go_home():
        content_area.controls.clear()
        content_area.controls.append(
            build_catalog_view(page, api, state, on_product_click=go_detail)
        )
        update_header()
        page.update()

    def go_detail(slug: str):
        content_area.controls.clear()
        content_area.controls.append(
            build_product_detail_view(
                page, api, slug,
                on_back=go_home,
                on_add_to_cart=lambda pid: add_to_cart(pid),
            )
        )
        page.update()

    def go_cart():
        content_area.controls.clear()
        content_area.controls.append(
            build_cart_view(
                page, api, session_key,
                on_checkout=lambda: go_checkout(),
                on_back=go_home,
            )
        )
        update_header()
        page.update()

    def go_checkout():
        page.open(ft.SnackBar(content=ft.Text("Checkout in arrivo (Fase 6)")))
        page.update()

    def add_to_cart(product_id: int):
        if api.add_to_cart(session_key, product_id):
            page.open(ft.SnackBar(
                content=ft.Text("Aggiunto al carrello!"),
                bgcolor=ft.Colors.GREEN_700,
            ))
            update_header()
        else:
            page.open(ft.SnackBar(content=ft.Text("Errore nell'aggiunta")))
        page.update()

    page.add(header_area, ft.Divider(), content_area)
    go_home()


if __name__ == "__main__":
    ft.run(main, port=8550)