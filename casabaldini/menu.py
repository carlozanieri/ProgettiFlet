import flet as ft
from api import fetch_menu


async def build_menu(page: ft.Page, on_navigate) -> ft.NavigationDrawer:
    """Costruisce il NavigationDrawer. on_navigate è una callback async(voce)"""

    menu_data = []
    try:
        menu_data = await fetch_menu()
        print(f"DEBUG menu_data: {len(menu_data)} voci ricevute")
    except Exception as e:
        print(f"ERRORE caricamento menu: {e}")

    voci = []
    for voce in menu_data:
        parent = voce.get("parent", {})
        children = voce.get("children", [])
        titolo_padre = parent.get("titolo", "")

        sottovoci = []
        for child in children:
            sottovoci.append(
                ft.ListTile(
                    title=ft.Text(child.get("titolo", ""), color="white"),
                    on_click=lambda e, c=child: page.run_task(_on_click, page, c, on_navigate),
                )
            )

        if sottovoci:
            voci.append(
                ft.ExpansionTile(
                    title=ft.Text(titolo_padre, weight=ft.FontWeight.BOLD, color="white"),
                    controls=sottovoci,
                    expanded=False,
                )
            )
        else:
            voci.append(
                ft.ListTile(
                    title=ft.Text(titolo_padre, weight=ft.FontWeight.BOLD, color="white"),
                    on_click=lambda e, p=parent: page.run_task(_on_click, page, p, on_navigate),
                )
            )

    drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(
                content=ft.Text("CasaBaldini", size=22, weight=ft.FontWeight.BOLD, color="white"),
                padding=20,
                bgcolor="#043a55",
            ),
            ft.Divider(height=1),
            ft.Column(controls=voci, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
        ],
    )

    return drawer


async def _on_click(page: ft.Page, voce: dict, on_navigate):
    """Chiude il drawer e delega la navigazione alla callback."""
    page.drawer.open = False
    page.update()
    await on_navigate(voce)