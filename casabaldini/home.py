import flet as ft
from api import IMG_BASE, API_BASE
import httpx


async def build_home(page: ft.Page) -> ft.Column:
    """Costruisce la home page: logo, immagine principale, testi e footer link."""

    # ==================== LOGO ====================
    logo = ft.Image(
        src=f"{IMG_BASE}/index/logo.jpg",
        fit=ft.BoxFit.CONTAIN,
        expand=True,
    )

    logo_container = ft.Container(
        content=logo,
        expand=True,
    )

    logo_row = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=logo_container,
                col={"xs": 8, "sm": 8, "md": 6, "lg": 4, "xl": 4},
                padding=5,
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # ==================== IMMAGINE PRINCIPALE ====================
    fronte = ft.Image(
        src=f"{IMG_BASE}/index/fronte.jpg",
        fit=ft.BoxFit.CONTAIN,
        expand=True, 
    )

    fronte_container = ft.Container(
        content=fronte,
        expand=True,
    )

    fronte_row = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=fronte_container,
                col={"xs": 11, "sm": 11, "md": 10, "lg": 8, "xl": 8},
                padding=5,
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # ==================== TESTI ====================
    testi = ft.Column(
        controls=[
            ft.Text("Barberino di Mugello", size=16, color="white", text_align=ft.TextAlign.CENTER),
            ft.Text("2,5 Km. dall'uscita dell'Autostrada A1", size=16, color="white", text_align=ft.TextAlign.CENTER),
            ft.Text("a pochi Km. da Firenze", size=16, color="white", text_align=ft.TextAlign.CENTER),
            ft.Text(
                "______________________________________________________",
                size=16, color="white", text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Per informazioni e prenotazioni telefona al +39 3207060411",
                size=16, color="white", weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        spacing=8,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # ==================== FOOTER LINK ====================
    ##footer = await build_footer_links(page)

    # ==================== COMPOSIZIONE ====================
    home_column = ft.Column(
        controls=[
            logo_row,
            fronte_row,
            ft.Container(content=testi, padding=20),
            ##ft.Container(content=footer, padding=ft.Padding.only(top=10, bottom=10)),
        ],
        spacing=20,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
    )

    return home_column


async def build_footer_links(page: ft.Page) -> ft.Row:
    """Costruisce la barra dei link in fondo alla home."""

    links_row = ft.Row(
        controls=[],
        spacing=30,
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{API_BASE}/links")
            response.raise_for_status()
            data = response.json()

        for link in data:
            titolo = link.get("titolo", "")
            url = link.get("link", "")
            img_name = link.get("img", "")
            img_url = f"{IMG_BASE}/links/{img_name}"

            link_control = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Image(src=img_url, width=30, height=30, fit=ft.BoxFit.CONTAIN),
                        ft.Text(titolo, size=14, color="white", weight=ft.FontWeight.BOLD),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                action=ft.OpenUrl(url, target=ft.UrlTarget.BLANK),  # <-- sostituisce on_click
                padding=5,
                border_radius=5,
            )

            links_row.controls.append(link_control)

    except Exception as e:
        print(f"Errore caricamento link: {e}")

    # Duplica i link per l'effetto continuo (quando faremo il marquee animato)
    # Per ora lasciamo lo scroll manuale

    return links_row