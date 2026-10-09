# app/components/header.py
import flet as ft


def build_header(
    on_home_click=None,
    on_cart_click=None,
    on_login_click=None,
    on_register_click=None,
    on_logout_click=None,
    on_orders_click=None,
    cart_count: int = 0,
    user: dict = None,
) -> ft.Container:
    """
    Header riutilizzabile con:
    - Logo/nome (torna alla home)
    - Badge carrello
    - Pulsanti Accedi/Registrati (anonimo) o menu utente (loggato)
    """
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

    # Blocco utente (menu o pulsanti)
    if user:
        display_name = user.get("first_name") or user.get("username", "Utente")
        user_block = ft.PopupMenuButton(
            items=[
                ft.PopupMenuItem(
                    content=ft.Text(f"Ciao, {display_name}"),
                    disabled=True,
                ),
                ft.PopupMenuItem(),  # separatore
                ft.PopupMenuItem(
                    content=ft.Text("I miei ordini"),
                    icon=ft.Icons.RECEIPT_LONG,
                    on_click=lambda e: on_orders_click() if on_orders_click else None,
                ),
                ft.PopupMenuItem(
                    content=ft.Text("Logout"),
                    icon=ft.Icons.LOGOUT,
                    on_click=lambda e: on_logout_click() if on_logout_click else None,
                ),
            ],
            icon=ft.Icons.ACCOUNT_CIRCLE,
            icon_color=ft.Colors.BROWN_700,
        )
    else:
        user_block = ft.Row([
            ft.TextButton(
                content=ft.Text("Accedi"),
                on_click=lambda e: on_login_click() if on_login_click else None,
            ),
            ft.Button(
                content=ft.Text("Registrati"),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BROWN_700,
                    color=ft.Colors.WHITE,
                ),
                on_click=lambda e: on_register_click() if on_register_click else None,
            ),
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
        padding=ft.Padding.symmetric(vertical=10, horizontal=10),
    )


def build_page_title(title: str) -> ft.Text:
    """Titolo di sezione riutilizzabile."""
    return ft.Text(
        title,
        size=28,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BROWN_700,
    )