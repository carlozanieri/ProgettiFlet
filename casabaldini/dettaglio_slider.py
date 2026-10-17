import flet as ft


async def build_dettaglio(page: ft.Page, slide: dict, img_src: str, on_back) -> ft.Column:
    """Costruisce la pagina di dettaglio di una slide."""

    titolo = slide.get("titolo", "")
    testo = slide.get("testo", slide.get("caption", ""))

    immagine = ft.Image(
        src=img_src,
        fit=ft.BoxFit.CONTAIN,
        expand=True,
    )

    immagine_container = ft.Container(
        content=immagine,
        expand=True,
        padding=10,
    )

    testo_control = ft.Text(
        testo,
        size=16,
        color="white",
        text_align=ft.TextAlign.JUSTIFY,
    )

    btn_indietro = ft.Button(
        "← Indietro",
        on_click=lambda e: page.run_task(on_back),
        style=ft.ButtonStyle(
            bgcolor="#043a55",
            color="white",
            padding=15,
        ),
    )

    pagina = ft.Column(
        controls=[
            ft.Container(content=btn_indietro, padding=10),
            ft.Container(
                content=ft.Text(
                    titolo,
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color="white",
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=20, vertical=5),
            ),
            immagine_container,
            ft.Container(
                content=testo_control,
                padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            ),
        ],
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    return pagina