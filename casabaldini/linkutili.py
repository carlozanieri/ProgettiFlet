import flet as ft
from api import fetch_links, IMG_BASE


async def build_linkutili(page: ft.Page, on_home) -> ft.Column:
    """Costruisce la pagina Link Utili.
    
    on_home è una callback per tornare alla home.
    """
    url_launcher = ft.UrlLauncher()

    # Titolo
    titolo = ft.Text(
        "Links Utili",
        size=24,
        weight=ft.FontWeight.BOLD,
        color="white",
        text_align=ft.TextAlign.CENTER,
    )

    # Container dei link (riempito dopo il caricamento)
    links_column = ft.Column(controls=[], spacing=10)

    try:
        data = await fetch_links()

        for link in data:
            titolo_link = link.get("titolo", "")
            url = link.get("link", "")
            img_name = link.get("img", "")
            img_url = f"{IMG_BASE}/links/{img_name}"

            async def apri_link(e, u=url):
                try:
                    await url_launcher.launch_url(u)
                except Exception as ex:
                    print(f"Errore apertura URL: {ex}")

            riga = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Image(
                            src=img_url,
                            width=50,
                            height=50,
                            fit=ft.BoxFit.CONTAIN,
                        ),
                        ft.Text(
                            titolo_link,
                            size=16,
                            color="white",
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                    spacing=15,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=10,
                border_radius=8,
                bgcolor="#1a3a4a",
                on_click=apri_link,
                ink=True,  # effetto ripple al click
            )
            links_column.controls.append(riga)

    except Exception as e:
        print(f"ERRORE caricamento link utili: {e}")
        links_column.controls.append(
            ft.Text(f"Errore: {e}", color="red", size=14)
        )

    # Pulsante "Torna alla HOME"
    btn_home = ft.Button(
        "Torna alla HOME",
        on_click=lambda e: page.run_task(on_home),
        style=ft.ButtonStyle(
            bgcolor="#5ec792",
            color="white",
            padding=15,
        ),
    )

    # Composizione finale
    pagina = ft.Column(
        controls=[
            ft.Container(content=titolo, padding=20, alignment=ft.Alignment.CENTER),
            ft.Divider(height=1, color="#444444"),
            ft.Container(
                content=links_column,
                padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            ),
            ft.Container(
                content=btn_home,
                alignment=ft.Alignment.CENTER,
                padding=20,
            ),
        ],
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
    )

    return pagina