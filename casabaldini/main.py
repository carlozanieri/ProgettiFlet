import flet as ft
from menu import build_menu
from home import build_home
from sliders import build_sliders
from linkutili import build_linkutili
from dovemangiare import build_dovemangiare
from prenotazioni import build_prenotazioni

async def main(page: ft.Page):
    page.title = "CasaBaldini"
    page.bgcolor = "#000000"
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    # Istanza per aprire link esterni
    url_launcher = ft.UrlLauncher()

    # Area contenuto
    content_area = ft.Column(controls=[], expand=True, scroll=ft.ScrollMode.AUTO)
    page.add(content_area)

    async def home_callback():
        """Naviga verso la home"""
        await navigate({"link": "/", "tipopage": "interna", "titolo": "Home"})

    # ==================== NAVIGATORE ====================
    async def navigate(voce: dict):
        link = voce.get("link", "")
        titolo = voce.get("titolo", "")
        tipopage = voce.get("tipopage", "")
        print(f"DEBUG navigate: titolo={titolo}, link={link}, tipo={tipopage}")

        try:
            if tipopage == "esterna":
                try:
                    await url_launcher.launch_url(link)
                except Exception as e:
                    print(f"Errore apertura URL: {e}")
                return

            if link == "/" or link == "":
                view = await build_home(page)
            elif link == "/casabaldini/index" or link == "/casabaldini":
                view = await build_sliders(page, dir="index")
            elif link.startswith("/casabaldini/"):
                dir_val = link.split("/")[-1]
                view = await build_sliders(page, dir=dir_val)
            elif link == "/linkutili":
                view = await build_linkutili(page, on_home=home_callback)
                content_area.controls.clear()
                content_area.controls.append(view)
            elif tipopage == "modale":
                if "prenotazioni" in link:
                    view = await build_prenotazioni(page, on_home=home_callback)
                elif "dovemangiare" in link:
                    view = await build_dovemangiare(page, on_home=home_callback)
                else:
                    view = ft.Container(
                        content=ft.Text(f"Modale: {titolo} ({link})", color="white", size=16),
                        padding=20,
                    )
                content_area.controls.clear()
                content_area.controls.append(view)
            else:
                view = ft.Container(
                    content=ft.Text(f"Pagina: {titolo} ({link})", color="white", size=16),
                    padding=20,
                )
            
            content_area.controls.clear()
            content_area.controls.append(view)
            page.update()

        except Exception as e:
            print(f"ERRORE navigazione: {e}")
            import traceback
            traceback.print_exc()
            content_area.controls.clear()
            content_area.controls.append(
                ft.Text(f"Errore: {e}", color="red", size=14)
            )
            page.update()

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