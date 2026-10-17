import flet as ft
from api import IMG_BASE, API_BASE

# Limiti massimi di decodifica per le immagini (non dimensioni di layout)
MAX_LOGO_WIDTH = 400
MAX_FRONTE_WIDTH = 1200


async def build_home(page: ft.Page) -> ft.Column:
    """Costruisce la home page: logo, immagine principale, testi."""

    # ==================== LOGO ====================
    logo = ft.Image(
        src=f"{IMG_BASE}/index/logo.jpg",
        fit=ft.BoxFit.CONTAIN,
        expand=True,
        cache_width=MAX_LOGO_WIDTH,
    )

    logo_row = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=logo,
                col={"xs": 4, "sm": 4, "md": 4, "lg": 2, "xl": 2},
                padding=2,
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # ==================== IMMAGINE PRINCIPALE ====================
    fronte = ft.Image(
        src=f"{IMG_BASE}/index/fronte.jpg",
        fit=ft.BoxFit.CONTAIN,
        expand=True,
        cache_width=MAX_FRONTE_WIDTH,
    )

    fronte_row = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=fronte,
                col={"xs": 10, "sm": 10, "md": 8, "lg": 7, "xl": 7},
                padding=2,
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # ==================== TESTI ====================
    testi = ft.Column(
        controls=[
            ft.Text("Barberino di Mugello - 2,5 Km. dall'uscita dell'Autostrada A1 - a pochi Km. da Firenze", size=16, color="white", text_align=ft.TextAlign.CENTER),
            #ft.Text("2,5 Km. dall'uscita dell'Autostrada A1", size=16, color="white", text_align=ft.TextAlign.CENTER),
            #ft.Text("a pochi Km. da Firenze", size=16, color="white", text_align=ft.TextAlign.CENTER),
            ft.Text(
                "___________________________________________________",
                size=15, color="white", text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Per informazioni e prenotazioni telefona al +39 3207060411",
                size=15, color="white", weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        spacing=8,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # ==================== COMPOSIZIONE ====================
    home_column = ft.Column(
        controls=[
            logo_row,
            fronte_row,
            ft.Container(content=testi, padding=20),
        ],
        spacing=18,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
    )

    return home_column