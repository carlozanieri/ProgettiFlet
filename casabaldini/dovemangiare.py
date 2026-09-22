import flet as ft
from api import fetch_foods, IMG_BASE


async def build_dovemangiare(page: ft.Page, on_home) -> ft.Column:
    """Costruisce la pagina Dove Mangiare."""
    url_launcher = ft.UrlLauncher()

    titolo = ft.Text(
        "Dove Mangiare",
        size=24,
        weight=ft.FontWeight.BOLD,
        color="white",
        text_align=ft.TextAlign.CENTER,
    )

    ristoranti_column = ft.Column(controls=[], spacing=10)

    try:
        data = await fetch_foods()

        for food in data:
            titolo_r = food.get("titolo", "")
            if not titolo_r:
                continue

            indirizzo = food.get("indirizzo", "")
            telefono = food.get("telefono", "")
            apiedi = food.get("apiedi", "")
            url = food.get("link", "")
            img_name = food.get("img", "")
            img_url = f"{IMG_BASE}/ristoranti/{img_name}"

            # Riga descrittiva
            descrizione = titolo_r
            if indirizzo:
                descrizione += f" - {indirizzo}"
            if telefono:
                descrizione += f"  {telefono}"
            if apiedi:
                descrizione += f"  ({apiedi})"

            async def apri_link(e, u=url):
                if u:
                    try:
                        await url_launcher.launch_url(u)
                    except Exception as ex:
                        print(f"Errore apertura URL: {ex}")

            riga = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Image(
                            src=img_url,
                            width=60,
                            height=60,
                            fit=ft.BoxFit.CONTAIN,
                        ),
                        ft.Text(
                            descrizione,
                            size=14,
                            color="white",
                            expand=True,
                        ),
                    ],
                    spacing=15,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=10,
                border_radius=8,
                bgcolor="#1a3a4a",
                on_click=apri_link if url else None,
                ink=bool(url),
            )
            ristoranti_column.controls.append(riga)

    except Exception as e:
        print(f"ERRORE caricamento ristoranti: {e}")
        ristoranti_column.controls.append(
            ft.Text(f"Errore: {e}", color="red", size=14)
        )

    # Nota finale
    nota = ft.Text(
        "I locali contrassegnati da (**) sono raggiungibili a piedi da Casa Baldini",
        size=12,
        color="#cccccc",
        italic=True,
        text_align=ft.TextAlign.CENTER,
    )

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
                content=ristoranti_column,
                padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            ),
            ft.Container(content=nota, padding=10),
            ft.Container(content=btn_home, alignment=ft.Alignment.CENTER, padding=20),
        ],
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
    )

    return pagina