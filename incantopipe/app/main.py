# main.py
import flet as ft
from api_client import APIClient
from components.header import build_header
from views.catalog import build_catalog_view
from views.product_detail import build_product_detail_view

api = APIClient()


def main(page: ft.Page):
    page.title = "InCantoPipe"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # Stato dell'applicazione (persistente tra le viste)
    state = {
        "category_slug": "",
        "material": "",
        "finish": "",
        "search": "",
        "sort": "-created",
    }

    # Contenitore principale dove cambiano le viste
    content_area = ft.Column()

    def go_home():
        """Torna al catalogo."""
        content_area.controls.clear()
        content_area.controls.append(
            build_catalog_view(page, api, state, on_product_click=go_detail)
        )
        page.update()

    def go_detail(slug: str):
        """Vai al dettaglio di un prodotto."""
        content_area.controls.clear()
        content_area.controls.append(
            build_product_detail_view(
                page, api, slug, on_back=go_home
            )
        )
        page.update()

    # Header con click su "InCantoPipe" per tornare alla home
    header = build_header(on_home_click=lambda e: go_home())

    page.add(
        header,
        ft.Divider(),
        content_area,
    )

    # Avvia mostrando il catalogo
    go_home()


if __name__ == "__main__":
    ft.run(main)