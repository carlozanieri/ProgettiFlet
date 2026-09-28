# components/header.py
import flet as ft


def build_header(on_home_click=None) -> ft.Container:
    """Header riutilizzabile per tutte le pagine."""
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.TextButton(
                    "InCantoPipe",
                    on_click=on_home_click,
                    style=ft.ButtonStyle(
                        color=ft.Colors.BROWN_700,
                    ),
                ),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Row([
                ft.Text(
                    "Pipe artigianali realizzate a mano nel Canto alla Brina",
                    size=13,
                    italic=True,
                    color=ft.Colors.GREY_700,
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=0),
        padding=ft.Padding.symmetric(vertical=15, horizontal=10),
    )


def build_page_title(title: str) -> ft.Text:
    """Titolo di sezione riutilizzabile."""
    return ft.Text(
        title,
        size=28,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BROWN_700,
    )

# app/components/header.py
import flet as ft


def build_header(on_home_click=None, on_cart_click=None, cart_count: int = 0) -> ft.Container:
    cart_badge = (
        ft.Container(
            content=ft.Text(str(cart_count), size=10, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED,
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=5, vertical=2),
        )
        if cart_count > 0
        else ft.Container()
    )

    return ft.Container(
        content=ft.Row([
            ft.TextButton(
                "InCantoPipe",
                on_click=on_home_click,
                style=ft.ButtonStyle(color=ft.Colors.BROWN_700),
            ),
            ft.Row([
                ft.IconButton(
                    icon=ft.Icons.SHOPPING_CART,
                    icon_color=ft.Colors.BROWN_700,
                    on_click=on_cart_click,
                    tooltip="Carrello",
                ),
                cart_badge,
            ], spacing=0),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding.symmetric(vertical=15, horizontal=10),
    )