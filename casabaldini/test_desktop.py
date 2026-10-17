import flet as ft

async def main(page: ft.Page):
    page.title = "Test desktop"
    page.add(ft.Text("Ciao dal desktop!", size=30))

ft.run(main, view=ft.AppView.FLET_APP)