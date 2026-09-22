import flet as ft
from menu import build_menu
from home import build_home
from linkutili import build_linkutili
from dovemangiare import build_dovemangiare
from prenotazioni import build_prenotazioni
from sliders import build_sliders
from dettaglio_slider import build_dettaglio


async def main(page: ft.Page):
    page.title = "CasaBaldini"
    page.bgcolor = "#000000"
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    content_area = ft.Column(controls=[], expand=True, scroll=ft.ScrollMode.AUTO)
    page.add(content_area)

    # Stato per fermare l'autoplay quando si cambia vista
    def ferma_slider():
        if hasattr(page, "_slider_attivo") and page._slider_attivo:
            page._slider_attivo.stop()
            page._slider_attivo = None

    # ==================== CALLBACK DETTAGLIO ====================
    async def apri_dettaglio(slide, img_url):
        ferma_slider()
        # Salva la voce corrente per poter tornare indietro
        page._voce_corrente = getattr(page, "_voce_corrente", None)

        async def torna_indietro():
            # Ricostruisce lo slider della stessa sezione
            voce = getattr(page, "_voce_corrente", None)
            if voce:
                await navigate(voce)

        vista = await build_dettaglio(page, slide, img_url, on_back=torna_indietro)
        content_area.controls.clear()
        content_area.controls.append(vista)
        page.update()

    # ==================== NAVIGATORE ====================
    async def navigate(voce: dict):
        link = voce.get("link", "")
        titolo = voce.get("titolo", "")
        tipopage = voce.get("tipopage", "")

        print(f"DEBUG navigate: titolo={titolo}, link={link}, tipo={tipopage}")
        ferma_slider()

        try:
            if tipopage == "esterna":
                return  # gestito da ft.OpenUrl nel menu

            if link == "/" or link == "":
                vista = await build_home(page)
            elif link == "/casabaldini/index" or link == "/casabaldini":
                page._voce_corrente = voce
                vista = await build_sliders(page, dir="index", on_image_click=apri_dettaglio)
            elif link.startswith("/casabaldini/"):
                page._voce_corrente = voce
                dir_val = link.split("/")[-1]
                vista = await build_sliders(page, dir=dir_val, on_image_click=apri_dettaglio)
            elif link == "/linkutili":
                vista = await build_linkutili(page, on_home=home_callback)
            elif tipopage == "modale" and "prenotazioni" in link:
                vista = await build_prenotazioni(page, on_home=home_callback)
            elif tipopage == "modale" and "dovemangiare" in link:
                vista = await build_dovemangiare(page, on_home=home_callback)
            else:
                vista = ft.Container(
                    content=ft.Text(f"Pagina: {titolo} ({link})", color="white", size=16),
                    padding=20,
                )

            content_area.controls.clear()
            content_area.controls.append(vista)
            page.update()

        except Exception as e:
            print(f"ERRORE navigazione: {e}")
            import traceback
            traceback.print_exc()
            content_area.controls.clear()
            content_area.controls.append(ft.Text(f"Errore: {e}", color="red", size=14))
            page.update()

    async def home_callback():
        await navigate({"link": "/", "tipopage": "interna", "titolo": "Home"})

    # ==================== DRAWER + APP BAR ====================
    drawer = await build_menu(page, on_navigate=navigate)
    page.drawer = drawer

    def apri_menu(e):
        page.run_task(page.show_drawer)

    page.appbar = ft.AppBar(
        leading=ft.IconButton(icon=ft.Icons.MENU, on_click=apri_menu),
        title=ft.Text("CasaBaldini"),
        bgcolor="#043a55",
    )

    # ==================== VISTA INIZIALE ====================
    home_view = await build_home(page)
    content_area.controls.append(home_view)
    page.update()


ft.run(main, view=ft.AppView.WEB_BROWSER)