# incantopipe_flet/app/main.py
import flet as ft
from api_client import APIClient
from config import MEDIA_BASE_URL

api = APIClient()


def main(page: ft.Page):
    page.title = "InCantoPipe"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # Header
    header = ft.Container(
        content=ft.Column([
            ft.Text("InCantoPipe", size=32, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BROWN_700),
            ft.Text("Pipe artigianali realizzate a mano nel Canto alla Brina",
                    size=14, italic=True, color=ft.Colors.GREY_700),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.symmetric(vertical=20),
    )

    # Contenitore dei prodotti
    products_grid = ft.ResponsiveRow(spacing=15, run_spacing=15)

    def load_products():
        products_grid.controls.clear()
        products = api.get_products()

        if not products:
            products_grid.controls.append(
                ft.Text("Nessun prodotto disponibile al momento.",
                        size=16, color=ft.Colors.GREY)
            )
        else:
            for p in products:
                products_grid.controls.append(build_product_card(p))

        page.update()

    def build_product_card(product: dict) -> ft.Container:
        image_url = (
            f"{MEDIA_BASE_URL}/{product['image']}"
            if product.get("image")
            else None
        )

        image_control = (
            ft.Image(src=image_url, height=180, fit=ft.BoxFit.COVER)
            if image_url
            else ft.Container(
                content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED,
                                size=60, color=ft.Colors.GREY_400),
                height=180,
                bgcolor=ft.Colors.GREY_200,
                alignment=ft.alignment.center,
            )
        )

        return ft.Container(
            col={"xs": 12, "sm": 6, "md": 4, "lg": 3},
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        image_control,
                        ft.Container(
                            content=ft.Column([
                                ft.Text(product["name"], size=16,
                                        weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f"€ {product['price']}",
                                    size=18, color=ft.Colors.BROWN_700,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    f"{product.get('material', '')} - {product.get('finish', '')}",
                                    size=12, color=ft.Colors.GREY_600,
                                ),
                            ], spacing=5),
                            padding=10,
                        ),
                    ], spacing=0),
                ),
            ),
        )

    # Carica i prodotti all'avvio
    load_products()

    page.add(header, products_grid)


if __name__ == "__main__":
    ft.run(main)