import flet as ft
from home import build_home
from menu import build_menu
from sliders import build_sliders


async def main(page: ft.Page):
    page.title = "CasaBaldini"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = "#000000"

    # Area contenuto che cambia in base alla voce di menu
    content_area = ft.Column(
        controls=[],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )
    page.add(content_area)

    # ==================== NAVIGATORE ====================
    async def navigate(voce: dict):
        link = voce.get("link", "")
        tipopage = voce.get("tipopage", "")

        content_area.controls.clear()
        content_area.controls.append(ft.ProgressRing())

        # Routing
        if tipopage == "esterna":
            # Apri nel browser
            content_area.controls.clear()
            await page.launch_url_async(link) if hasattr(page, 'launch_url_async') else None
            # fallback
            try:
                launcher = ft.UrlLauncher()
                await launcher.launch_url(link)
            except Exception as e:
                print(f"Errore apertura URL: {e}")

        elif tipopage == "modale":
            if "prenotazioni" in link:
                content_area.controls.clear()
                content_area.controls.append(ft.Text(f"Prenotazioni: {link}"))
            elif "dovemangiare" in link:
                content_area.controls.clear()
                content_area.controls.append(ft.Text(f"Dove Mangiare: {link}"))
            else:
                content_area.controls.clear()
                content_area.controls.append(ft.Text(f"Modale: {link}"))

        elif tipopage == "interna":
            if link == "/" or link == "":
                # Home page
                view = await build_home(page)
                content_area.controls.clear()
                content_area.controls.append(view)

            elif link == "/casabaldini/index" or link == "/casabaldini":
                # Slider immagini
                view = await build_sliders(page, dir="index")
                content_area.controls.clear()
                content_area.controls.append(view)

            elif link.startswith("/casabaldini/"):
                # Sezione con slider (camere, ilpaese, lasala)
                dir_val = link.split("/")[-1]
                view = await build_sliders(page, dir=dir_val)
                content_area.controls.clear()
                content_area.controls.append(view)

            elif link == "/linkutili":
                content_area.controls.clear()
                content_area.controls.append(ft.Text(f"Link Utili: {link}"))

            else:
                content_area.controls.clear()
                content_area.controls.append(ft.Text(f"Pagina interna: {link}"))

        page.update()

    # ==================== APP BAR + DRAWER ====================
    drawer = await build_menu(page, on_navigate=navigate)
    page.drawer = drawer

    def apri_menu(e):
        page.drawer.open = True
        page.update()

    page.appbar = ft.AppBar(
        leading=ft.IconButton(icon=ft.Icons.MENU, on_click=apri_menu),
        title=ft.Text("CasaBaldini"),
        bgcolor="#043a55",
    )

    # Vista iniziale: home page
    home_view = await build_home(page)
    content_area.controls.append(home_view)
    page.update()


ft.run(main, view=ft.AppView.WEB_BROWSER)