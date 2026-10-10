# app/components/header.py
import flet as ft


def build_header(
    on_home_click=None,
    on_cart_click=None,
    on_login_click=None,
    on_register_click=None,
    on_logout_click=None,          # ← NUOVO
    cart_count: int = 0,
    user: dict = None,
) -> ft.Container:
    """Header con catalogo, carrello, e pulsanti di autenticazione."""

    # Badge carrello
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

    # Blocco utente
    if user:
        display_name = user.get("first_name") or user.get("username", "Utente")
        user_block = ft.Row([
            ft.Text(f"Ciao, {display_name}", size=12),
            ft.TextButton(
                "Logout",
                on_click=lambda e: on_logout_click() if on_logout_click else None,
            ),
        ], spacing=5)
    else:
        user_block = ft.Row([
            ft.TextButton("Accedi",
                on_click=lambda e: on_login_click() if on_login_click else None),
            ft.TextButton("Registrati",
                on_click=lambda e: on_register_click() if on_register_click else None),
        ], spacing=5)

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
                ft.Container(width=10),
                user_block,
            ], spacing=0),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding.symmetric(vertical=15, horizontal=10),
    )


def build_page_title(title: str) -> ft.Text:
    return ft.Text(
        title,
        size=28,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BROWN_700,
    )