import flet as ft
from api import IMG_BASE


async def build_prenotazioni(page: ft.Page, on_home) -> ft.Column:
    """Costruisce la pagina Prenotazioni."""
    url_launcher = ft.UrlLauncher()

    titolo = ft.Text(
        "Prenotazioni",
        size=24,
        weight=ft.FontWeight.BOLD,
        color="white",
        text_align=ft.TextAlign.CENTER,
    )

    # ==================== TELEFONO ====================
    async def chiama(e):
        try:
            await url_launcher.launch_url("tel:+393207060411")
        except Exception as ex:
            print(f"Errore apertura telefono: {ex}")

    icona_telefono = ft.Image(
        src=f"{IMG_BASE}/telefono_4.jpg",
        width=40,
        height=40,
        fit=ft.BoxFit.CONTAIN,
    )

    riga_telefono = ft.Container(
        content=ft.Row(
            controls=[
                icona_telefono,
                ft.Text("Telefonando al:", size=16, color="white"),
                ft.Text("+39 320 706 0411", size=20, color="white", weight=ft.FontWeight.BOLD),
            ],
            spacing=15,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=15,
        border_radius=8,
        bgcolor="#1a3a4a",
        on_click=chiama,
        ink=True,
    )

    # ==================== EMAIL ====================
    async def invia_email(e):
        try:
            await url_launcher.launch_url(
                "mailto:bruna.bbaldini@gmail.com?subject=Richiesta informazioni CasaBaldini"
            )
        except Exception as ex:
            print(f"Errore apertura email: {ex}")

    icona_email = ft.Image(
        src=f"{IMG_BASE}/email_3.jpg",
        width=40,
        height=40,
        fit=ft.BoxFit.CONTAIN,
    )

    riga_email = ft.Container(
        content=ft.Row(
            controls=[
                icona_email,
                ft.Text("Inviando un'E-Mail a:", size=16, color="white"),
                ft.Text("bruna.bbaldini@gmail.com", size=18, color="white", weight=ft.FontWeight.BOLD),
            ],
            spacing=15,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=15,
        border_radius=8,
        bgcolor="#1a3a4a",
        on_click=invia_email,
        ink=True,
    )

    # ==================== TORNA ALLA HOME ====================
    btn_home = ft.Button(
        "Torna alla HOME",
        on_click=lambda e: page.run_task(on_home),
        style=ft.ButtonStyle(
            bgcolor="#5ec792",
            color="white",
            padding=15,
        ),
    )

    pagina = ft.Column(
        controls=[
            ft.Container(content=titolo, padding=20, alignment=ft.Alignment.CENTER),
            ft.Divider(height=1, color="#444444"),
            ft.Container(
                content=ft.Column(
                    controls=[riga_telefono, riga_email],
                    spacing=15,
                ),
                padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            ),
            ft.Container(content=btn_home, alignment=ft.Alignment.CENTER, padding=20),
        ],
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
    )

    return pagina