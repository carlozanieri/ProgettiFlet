import flet as ft

async def main(page: ft.Page):
    page.bgcolor = "#000000"
    
    page_view = ft.PageView(
        expand=True,
        viewport_fraction=0.9,
        controls=[
            ft.Container(
                bgcolor=ft.Colors.INDIGO_400,
                alignment=ft.Alignment.CENTER,
                content=ft.Text("Pagina 1", size=30, color="white"),
            ),
            ft.Container(
                bgcolor=ft.Colors.PINK_300,
                alignment=ft.Alignment.CENTER,
                content=ft.Text("Pagina 2", size=30, color="white"),
            ),
            ft.Container(
                bgcolor=ft.Colors.TEAL_300,
                alignment=ft.Alignment.CENTER,
                content=ft.Text("Pagina 3", size=30, color="white"),
            ),
        ],
    )
    
    page.add(page_view)
    page.update()

ft.run(main, view=ft.AppView.WEB_BROWSER)