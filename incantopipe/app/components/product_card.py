# components/product_card.py
import flet as ft
from config import MEDIA_BASE_URL


def build_product_card(product: dict, on_click) -> ft.Container:
    """Card prodotto cliccabile."""
    image_url = (
        f"{MEDIA_BASE_URL}/{product['image']}"
        if product.get("image")
        else None
    )

    image_control = (
        ft.Image(src=image_url, height=180, fit=ft.BoxFit.COVER)
        if image_url
        else ft.Container(
            content=ft.Icon(
                ft.Icons.IMAGE_NOT_SUPPORTED,
                size=60,
                color=ft.Colors.GREY_400,
            ),
            height=180,
            bgcolor=ft.Colors.GREY_200,
            alignment=ft.alignment.center,
        )
    )

    # components/product_card.py

    return ft.Container(
        col={"xs": 12, "sm": 6, "md": 4, "lg": 3},
        content=ft.Card(
        content=ft.Container(
            content=ft.Column([
                image_control,
                ft.Container(
                    content=ft.Column([
                        ft.Text(product["name"], size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(f"€ {product['price']}", size=18, color=ft.Colors.BROWN_700, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{product.get('material', '')} - {product.get('finish', '')}", size=12, color=ft.Colors.GREY_600),
                    ], spacing=5),
                    padding=10,
                ),
            ], spacing=0),
            ),
        ),
        on_click=lambda e, slug=product["slug"]: on_click(slug),  # ← spostato qui
    )  