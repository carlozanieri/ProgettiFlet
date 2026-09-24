import asyncio
import flet as ft
import httpx
from api import API_BASE, IMG_BASE

SLIDE_INTERVAL = 4

# Margini per il calcolo delle dimensioni immagine
MARGINE_ORIZZONTALE = 140   # spazio per frecce + padding
MARGINE_VERTICALE = 220     # spazio per status, frecce, indicatori, dettaglio


class SliderView:
    """Carosello personalizzato con autoplay, frecce e indicatori cliccabili."""

    def __init__(self, page: ft.Page, dir_val: str, on_image_click):
        self.page = page
        self.dir = dir_val
        self.on_image_click = on_image_click
        self.slides = []
        self.current_index = 0
        self.attivo = True
        self.autoplay_task = None

        self.status = ft.Text("...", color="orange", size=14)

        # Dimensioni immagine calcolate dalla pagina
        self.larghezza_img = max((page.width or 800) - MARGINE_ORIZZONTALE, 200)
        self.altezza_img = max((page.height or 600) - MARGINE_VERTICALE, 200)

        # Immagine corrente con transizione
        self.immagine_corrente = ft.Image(
            src="",
            width=self.larghezza_img,
            height=self.altezza_img,
            fit=ft.BoxFit.CONTAIN,
        )
        self.switcher = ft.AnimatedSwitcher(
            content=self.immagine_corrente,
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=500,
            reverse_duration=500,
            switch_in_curve=ft.AnimationCurve.EASE_IN_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN_OUT,
            expand=True,
        )

        # Frecce
        self.btn_prev = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            icon_size=40,
            icon_color="white",
            on_click=lambda e: self.page.run_task(self._vai_precedente),
        )
        self.btn_next = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            icon_size=40,
            icon_color="white",
            on_click=lambda e: self.page.run_task(self._vai_successivo),
        )

        # Indicatori
        self.indicatori_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        )

        # Pulsante dettaglio
        self.btn_dettaglio = ft.Button(
            "🔍  Dettaglio",
            on_click=lambda e: self.page.run_task(self._click_dettaglio),
            style=ft.ButtonStyle(
                bgcolor="#043a55",
                color="white",
                padding=15,
            ),
        )

    async def build(self) -> ft.Column:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{API_BASE}/slider", params={"dir": self.dir})
                response.raise_for_status()
                self.slides = response.json()

            # Mostra la prima slide
            if self.slides:
                await self._mostra_slide(0)

            # Avvia autoplay
            self.autoplay_task = asyncio.create_task(self._autoplay())

            # Layout: immagine + frecce + indicatori
            return ft.Column(
                controls=[
                    self.status,
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.btn_prev,
                                ft.Container(content=self.switcher, expand=True),
                                self.btn_next,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        expand=True,
                    ),
                    self.indicatori_row,
                    ft.Container(
                        content=self.btn_dettaglio,
                        alignment=ft.Alignment.CENTER,
                        padding=10,
                    ),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            )

        except Exception as e:
            print(f"ERRORE slider: {e}")
            import traceback
            traceback.print_exc()
            self.status.value = f"Errore: {e}"
            self.status.color = "red"
            return ft.Column([self.status])

    async def _mostra_slide(self, index: int):
        if not self.slides:
            return
        self.current_index = index % len(self.slides)
        slide = self.slides[self.current_index]
        img_url = f"{IMG_BASE}/{self.dir}/{slide.get('img', '')}"

        # Aggiorna l'immagine nel switcher con dimensioni esplicite
        self.switcher.content = ft.Image(
            src=img_url,
            width=self.larghezza_img,
            height=self.altezza_img,
            fit=ft.BoxFit.CONTAIN,
        )
        self._aggiorna_indicatori()
        self.page.update()

    async def _vai_precedente(self):
        await self._mostra_slide(self.current_index - 1)

    async def _vai_successivo(self):
        await self._mostra_slide(self.current_index + 1)

    def _aggiorna_indicatori(self):
        self.indicatori_row.controls.clear()
        for i in range(len(self.slides)):
            attivo = (i == self.current_index)
            self.indicatori_row.controls.append(
                ft.Container(
                    width=14 if attivo else 10,
                    height=14 if attivo else 10,
                    border_radius=7,
                    bgcolor="#043a55" if attivo else "#888888",
                    on_click=lambda e, idx=i: self.page.run_task(self._vai_a, idx),
                    ink=True,
                )
            )

    async def _vai_a(self, index: int):
        await self._mostra_slide(index)

    async def _autoplay(self):
        while self.attivo:
            await asyncio.sleep(SLIDE_INTERVAL)
            if self.attivo and self.slides:
                await self._vai_successivo()

    def stop(self):
        self.attivo = False
        if self.autoplay_task:
            self.autoplay_task.cancel()
            self.autoplay_task = None

    async def _click_dettaglio(self):
        """Apre il dettaglio della slide corrente."""
        if not self.attivo:
            return
        if self.on_image_click and self.slides:
            idx = self.current_index
            slide = self.slides[idx]
            img_url = f"{IMG_BASE}/{self.dir}/{slide.get('img', '')}"
            await self.on_image_click(slide, img_url)


async def build_sliders(page: ft.Page, dir: str = "index", on_image_click=None) -> ft.Column:
    slider = SliderView(page, dir, on_image_click)
    pagina = await slider.build()
    page._slider_attivo = slider
    return pagina