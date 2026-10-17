import flet as ft

def main(page: ft.Page):
    page.title = "Test"
    page.add(ft.Text("Se vedi questo, Flet funziona!", size=30))

if __name__ == "__main__":
    ft.run(main, port=8551)
