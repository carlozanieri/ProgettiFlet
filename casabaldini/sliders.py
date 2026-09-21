import flet as ft
import httpx
from api import API_BASE, IMG_BASE


async def build_sliders(page: ft.Page, dir: str = "index") -> ft.Column:
    """Scarica gli slider e restituisce una Column responsive con tutte le immagini."""

    status = ft.Text("Caricamento slider...", color="orange", size=14)
    colonna = ft.Column(
        controls=[status],
        spacing=15,
        expand=True,
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{API_BASE}/slider?dir={dir}")
            response.raise_for_status()
            data = response.json()

        status.value = f"Caricati {len(data)} elementi"
        status.color = "green"

        for item in data:
            img_url = f"{IMG_BASE}/{dir}/{item.get('img')}"

            # ResponsiveRow: su schermi piccoli occupa tutto,
            # su schermi grandi si adatta al contenitore
            immagine = ft.Image(
                src=img_url,
                fit=ft.BoxFit.CONTAIN,  # mostra tutta l'immagine senza tagliarla
                width=None,             # lascia che sia il contenitore a decidere
                height=None,
                expand=True,
            )

            # Contenitore con larghezza piena e altezza proporzionale
            immagine_container = ft.Container(
                content=immagine,
                width=None,
                height=None,
                expand=True,
                border_radius=8,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            )

            blocco = ft.Column(
                controls=[
                    immagine_container,
                    ft.Text(
                        item.get("titolo", ""),
                        size=16,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        item.get("caption", ""),
                        size=12,
                        color="grey",
                    ),
                    ft.Divider(),
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

            # ResponsiveRow: la colonna occupa tutta la larghezza
            # su schermi piccoli, e può adattarsi su schermi grandi
            riga = ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=blocco,
                        col={"xs": 12, "sm": 12, "md": 10, "lg": 8, "xl": 6},
                        padding=5,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
                run_spacing=10,
            )

            colonna.controls.append(riga)

    except Exception as e:
        status.value = f"ERRORE: {e}"
        status.color = "red"

    return colonna