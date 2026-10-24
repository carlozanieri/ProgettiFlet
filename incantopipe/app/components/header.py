# app/components/header.py
import flet as ft


def build_header(
    on_home_click=None,
    on_cart_click=None,
    on_login_click=None,
    on_register_click=None,
    on_logout_click=None,
    on_orders_click=None,
    on_admin_click=None,
    cart_count: int = 0,
    user: dict = None,
) -> ft.Container:
    """Header con catalogo, carrello, autenticazione e (se admin) area admin."""

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

    if user:
        display_name = user.get("first_name") or user.get("username", "Utente")
        is_staff = user.get("is_staff", False)

        # Usiamo un PopupMenuButton: su mobile è molto meglio perché occupa meno spazio
        menu_items = [
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
        ]

        if is_staff and on_admin_click:
            menu_items.append(
                ft.PopupMenuItem(
                    content=ft.Text("Admin"),
                    icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                    on_click=lambda e: on_admin_click(),
                )
            )

        menu_items.append(
            ft.PopupMenuItem(
                content=ft.Text("Logout"),
                icon=ft.Icons.LOGOUT,
                on_click=lambda e: on_logout_click() if on_logout_click else None,
            )
        )

        user_block = ft.PopupMenuButton(
            items=menu_items,
            icon=ft.Icons.ACCOUNT_CIRCLE,
            icon_color=ft.Colors.BROWN_700,
        )
    else:
        # Su mobile i due pulsanti affiancati potrebbero non entrare.
        # Usiamo un Row che va a capo se necessario (wrap=True) ma solo per i pulsanti
        user_block = ft.Row([
            ft.TextButton(
                "Accedi",
                on_click=lambda e: on_login_click() if on_login_click else None,
            ),
            ft.TextButton(
                "Registrati",
                on_click=lambda e: on_register_click() if on_register_click else None,
            ),
        ], spacing=5, wrap=True)

    return ft.Container(
        content=ft.ResponsiveRow([
            # Colonna sinistra: Logo
            ft.Container(
                content=ft.TextButton(
                    "InCantoPipe",
                    on_click=on_home_click,
                    style=ft.ButtonStyle(color=ft.Colors.BROWN_700),
                ),
                col={"xs": 6, "sm": 6, "md": 6}, # Prende metà schermo su mobile
            ),
            # Colonna destra: Carrello + Menu Utente
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.SHOPPING_CART,
                        icon_color=ft.Colors.BROWN_700,
                        on_click=on_cart_click,
                        tooltip="Carrello",
                    ),
                    cart_badge,
                    user_block,
                ], alignment=ft.MainAxisAlignment.END, spacing=5),
                col={"xs": 6, "sm": 6, "md": 6},
                alignment=ft.Alignment.CENTER_RIGHT,
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=0, run_spacing=0),
        padding=ft.Padding.symmetric(vertical=10, horizontal=10),
    )


def build_page_title(title: str) -> ft.Text:
    return ft.Text(
        title,
        size=28,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BROWN_700,
    )