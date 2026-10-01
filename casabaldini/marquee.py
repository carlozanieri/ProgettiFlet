import asyncio
import flet as ft
from api import fetch_links, IMG_BASE


class MarqueeFooter:
    def __init__(self, page: ft.Page, durata_ciclo: float = 30.0):
        self.page = page
        self.durata_ciclo = durata_ciclo
        self.attivo = True
        self.fermo_hover = False
        self.fermo_tap = False

        self.links_row = ft.Row(controls=[], spacing=30, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Il wrapper con animazione nativa
        self.wrapper = ft.Container(
            content=self.links_row,
            offset=ft.Offset(x=0, y=0),
            animate_offset=ft.Animation(
                duration=int(self.durata_ciclo * 1000),
                curve=ft.AnimationCurve.LINEAR,
            ),
            on_animation_end=self._on_animazione_finita,
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
        )
        
        self.stack = ft.Stack(controls=[self.wrapper], expand=True)
        self.viewport = ft.Container(
            height=60,
            bgcolor="#2c0404",
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            expand=True,
            on_hover=self._on_hover,
            content=ft.GestureDetector(content=self.stack, on_tap=self._on_tap),
        )
        self.larghezza_giro = 1000

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

            self.larghezza_giro = max(200 * (len(self.links_row.controls) // 2), 1000)
            self._avvia_animazione()
        except Exception as e:
            print(f"ERRORE marquee: {e}")
        return self.viewport

    def _avvia_animazione(self):
        if not self.attivo or self.fermo_hover or self.fermo_tap:
            return
        # Sposta verso sinistra. Offset x è una frazione della larghezza del container.
        self.wrapper.offset = ft.Offset(x=-(self.larghezza_giro / (self.wrapper.width or 1)), y=0)
        self.wrapper.update()

    def _on_animazione_finita(self, e):
        if not self.attivo:
            return
        # Reset invisibile
        self.wrapper.animate_offset = None
        self.wrapper.offset = ft.Offset(x=0, y=0)
        self.wrapper.update()
        
        async def riparti():
            await asyncio.sleep(0.1)
            if self.attivo and not self.fermo_hover and not self.fermo_tap:
                self.wrapper.animate_offset = ft.Animation(
                    duration=int(self.durata_ciclo * 1000),
                    curve=ft.AnimationCurve.LINEAR,
                )
                self._avvia_animazione()
        asyncio.create_task(riparti())

    def _on_hover(self, e):
        valore = e.data
        if isinstance(valore, bool):
            self.fermo_hover = valore
        elif isinstance(valore, str):
            self.fermo_hover = valore.lower() == "true"
        else:
            self.fermo_hover = bool(valore)

    def _on_tap(self, e):
        self.fermo_tap = True
        asyncio.create_task(self._riprendi_dopo(3.0))

    async def _riprendi_dopo(self, secondi: float):
        await asyncio.sleep(secondi)
        self.fermo_tap = False

    def stop(self):
        self.attivo = False