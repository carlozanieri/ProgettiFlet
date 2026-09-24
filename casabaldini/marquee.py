import asyncio
import flet as ft
from api import fetch_links, IMG_BASE


class MarqueeFooter:
    """Footer con link che scorrono orizzontalmente in modo continuo."""

    def __init__(self, page: ft.Page, passo_px: int = 1, intervallo_ms: int = 10):
        self.page = page
        self.passo_px = passo_px
        self.intervallo_ms = intervallo_ms
        self.attivo = True
        self.posizione = 0.0
        self.task = None
        self.fermo_hover = False
        self.fermo_tap = False

        self.links_row = ft.Row(
            controls=[],
            spacing=30,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.wrapper = ft.Container(
            content=self.links_row,
            left=0,
            top=0,
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
        )

        self.stack = ft.Stack(
            controls=[self.wrapper],
            expand=True,
        )

        # GestureDetector avvolge lo Stack e cattura il tocco senza bloccare i link
        self.viewport = ft.Container(
            height=60,
            bgcolor="#2c0404",
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            expand=True,
            on_hover=self._on_hover,
            content=ft.GestureDetector(
                content=self.stack,
                on_tap=self._on_tap,
                drag_interval=0,
            ),
        )

    async def build(self) -> ft.Container:
        try:
            links_data = await fetch_links()

            for _ in range(2):
                for link in links_data:
                    titolo = link.get("titolo", "")
                    url = link.get("link", "")
                    img_name = link.get("img", "")
                    img_url = f"{IMG_BASE}/links/{img_name}"

                    item = ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Image(src=img_url, width=30, height=30, fit=ft.BoxFit.CONTAIN),
                                ft.Text(titolo, size=13, color="white", weight=ft.FontWeight.BOLD),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        action=ft.OpenUrl(url, target=ft.UrlTarget.SELF),
                        padding=5,
                    )
                    self.links_row.controls.append(item)

            self.task = asyncio.create_task(self._anima())

        except Exception as e:
            print(f"ERRORE marquee: {e}")
            self.links_row.controls.append(
                ft.Text(f"Errore: {e}", color="red", size=12)
            )

        return self.viewport

    async def _anima(self):
        await asyncio.sleep(0.5)

        larghezza_giro = max(200 * (len(self.links_row.controls) // 2), 1000)

        while self.attivo:
            await asyncio.sleep(self.intervallo_ms / 1000.0)

            if not self.attivo:
                break

            if self.fermo_hover or self.fermo_tap:
                continue

            self.posizione -= self.passo_px

            if self.posizione <= -larghezza_giro:
                self.posizione = 0

            try:
                self.wrapper.left = self.posizione
                self.wrapper.update()
            except Exception:
                break

    def _on_hover(self, e):
        valore = e.data
        if isinstance(valore, bool):
            self.fermo_hover = valore
        elif isinstance(valore, str):
            self.fermo_hover = valore.lower() == "true"
        else:
            self.fermo_hover = bool(valore)

    def _on_tap(self, e):
        """Ferma per 3 secondi, poi riprende automaticamente."""
        self.fermo_tap = True
        asyncio.create_task(self._riprendi_dopo(3.0))

    async def _riprendi_dopo(self, secondi: float):
        await asyncio.sleep(secondi)
        self.fermo_tap = False

    def stop(self):
        self.attivo = False
        if self.task:
            self.task.cancel()
            self.task = None