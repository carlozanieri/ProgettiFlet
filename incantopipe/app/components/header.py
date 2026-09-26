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