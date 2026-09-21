import flet as ft
from home import build_home


async def main(page: ft.Page):
    page.title = "CasaBaldini"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = "#000000"  # sfondo nero come nel web

    home_view = await build_home(page)
    page.add(home_view)
    page.update()


ft.run(main, view=ft.AppView.WEB_BROWSER)