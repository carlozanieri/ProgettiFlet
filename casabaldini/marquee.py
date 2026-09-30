import asyncio
import flet as ft
from api import fetch_links, IMG_BASE


class MarqueeFooter:
    """Footer con link che scorrono orizzontalmente in modo fluido usando animate_offset."""

    def __init__(self, page: ft.Page, durata_ciclo: float = 15.0):
        self.page = page
        self.durata_ciclo = durata_ciclo  # secondi per un ciclo completo
        self.attivo = True
        self.task = None
        self.fermo_hover = False
        self.fermo_tap = False

        self.links_row = ft.Row(
            controls=[],
            spacing=30,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Il wrapper ha un offset animato da Flet stesso
        self.wrapper = ft.Container(
            content=self.links_row,
            offset=ft.Offset(x=0, y=0),
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
            animate_offset=ft.Animation(
                duration=int(self.durata_ciclo * 1000),
                curve=ft.AnimationCurve.LINEAR,
            ),
        )

        self.stack = ft.Stack(
            controls=[self.wrapper],
            expand=True,
        )

        self.viewport = ft.Container(
            height=60,
            bgcolor="#2c0404",
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            expand=True,
            on_hover=self._on_hover,
            content=ft.GestureDetector(
                content=self.stack,
                on_tap=self._on_tap,
            ),
        )

    async def build(self) -> ft.Container:
        try:
            links_data = await fetch_links()

            # Duplica i link per il loop continuo
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
        """Alterna l'offset da destra a sinistra in un ciclo continuo."""
        await asyncio.sleep(1)

        # Stima della larghezza di un giro completo
        larghezza_giro = max(200 * (len(self.links_row.controls) // 2), 1000)

        while self.attivo:
            # Riprendi se in pausa
            if self.fermo_hover or self.fermo_tap:
                await asyncio.sleep(0.1)
                continue

            try:
                # Sposta da 0 a -larghezza_giro (verso sinistra)
                self.wrapper.offset = ft.Offset(x=-larghezza_giro, y=0)
                self.wrapper.update()

                # Attendi la durata dell'animazione
                await asyncio.sleep(self.durata_ciclo)

                if not self.attivo:
                    break

                # Reset invisibile: torna a 0 senza animazione
                self.wrapper.animate_offset = None
                self.wrapper.offset = ft.Offset(x=0, y=0)
                self.wrapper.update()
                await asyncio.sleep(0.1)

                # Riattiva l'animazione
                self.wrapper.animate_offset = ft.Animation(
                    duration=int(self.durata_ciclo * 1000),
                    curve=ft.AnimationCurve.LINEAR,
                )

            except Exception as e:
                print(f"Errore animazione marquee: {e}")
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