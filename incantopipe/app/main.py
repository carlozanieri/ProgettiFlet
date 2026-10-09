import flet as ft
import uuid
import asyncio
from api_client import APIClient
from components.header import build_header
from views.catalog import build_catalog_view
from views.product_detail import build_product_detail_view
from views.cart import build_cart_view
from views.auth import build_login_view, build_register_view

api = APIClient()


async def main(page: ft.Page):
    
    page.title = "InCantoPipe"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # Sessione anonima univoca per questo client
    session_key = str(uuid.uuid4())[:32]

    # Stato globale dell'app
    state = {
        # Filtri catalogo
        "category_slug": "", "material": "", "finish": "",
        "search": "", "sort": "-created",
        # Autenticazione
        "user": None,
        "return_to": None,
    }

    content_area = ft.Column()
    header_area = ft.Column()

    # ============================================================
    # HEADER
    # ============================================================

    def update_header():
        header_area.controls.clear()
        header_area.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.TextButton(
                        "InCantoPipe",
                        on_click=lambda e: go_home(),
                        style=ft.ButtonStyle(color=ft.Colors.BROWN_700),
                    ),
                ]),
                padding=10,
            )
        )
        page.update()

    # ============================================================
    # AUTENTICAZIONE
    # ============================================================

    def do_login_success(user_data):
        """Callback dopo login/registrazione riuscita."""
        # Recupera dati completi dell'utente
        me = api.get_me()
        if me:
            state["user"] = me
        else:
            state["user"] = {
                "username": user_data.get("username"),
                "user_id": user_data.get("user_id"),
            }

        # Associa il carrello anonimo all'utente
        try:
            api.client.post(
                f"{api.base_url}/cart/associate",
                json={"session_key": session_key},
            )
        except Exception as e:
            print(f"Errore associazione carrello: {e}")

        # Torna alla vista precedente
        return_to = state.get("return_to")
        state["return_to"] = None
        if return_to == "cart":
            go_cart()
        elif return_to == "checkout":
            go_checkout()
        else:
            go_home()

    def do_logout():
        api.clear_auth_token()
        ft.SharedPreferences.remove("auth_token")
        ft.SharedPreferences.remove("user_id")
        ft.SharedPreferences.remove("username")
        state["user"] = None
        page.show_dialog(ft.SnackBar(content=ft.Text("Logout effettuato")))
        go_home()

    # ============================================================
    # NAVIGAZIONE
    # ============================================================

    def go_login(from_view="catalog"):
        state["return_to"] = from_view
        content_area.controls.clear()
        content_area.controls.append(
            build_login_view(
                page, api,
                on_success=do_login_success,
                on_register_click=lambda: go_register(from_view=from_view),
                on_back=lambda: go_home(),
            )
        )
        page.update()

    def go_register(from_view="catalog"):
        state["return_to"] = from_view
        content_area.controls.clear()
        content_area.controls.append(
            build_register_view(
                page, api,
                on_success=do_login_success,
                on_login_click=lambda: go_login(from_view=from_view),
                on_back=lambda: go_home(),
            )
        )
        page.update()

    def go_home():
        content_area.controls.clear()
        content_area.controls.append(
            build_catalog_view(page, api, state, on_product_click=go_detail)
        )
        update_header()
        page.update()

    def go_detail(slug: str):
        content_area.controls.clear()
        content_area.controls.append(
            build_product_detail_view(
                page, api, slug,
                on_back=go_home,
                on_add_to_cart=lambda pid: add_to_cart(pid),
            )
        )
        page.update()

    def go_cart():
        content_area.controls.clear()
        content_area.controls.append(
            build_cart_view(
                page, api, session_key,
                on_checkout=lambda: go_checkout(),
                on_back=go_home,
            )
        )
        update_header()
        page.update()

    def go_checkout():
        """Se non loggato, vai al login; altrimenti (Fase 6) procedi."""
        if not state["user"]:
            go_login(from_view="checkout")
            return
        # Fase 6: qui costruiremo il checkout
        page.show_dialog(ft.SnackBar(
            content=ft.Text("Checkout in arrivo (Fase 6)"),
        ))
        page.update()

    def add_to_cart(product_id: int):
        if api.add_to_cart(session_key, product_id):
            page.show_dialog(ft.SnackBar(
                content=ft.Text("Aggiunto al carrello!"),
                bgcolor=ft.Colors.GREEN_700,
            ))
            update_header()
        else:
            page.show_dialog(ft.SnackBar(content=ft.Text("Errore nell'aggiunta")))
        page.update()

    # ============================================================
    # AVVIO
    # ============================================================

    # Verifica se c'è un token salvato (utente già loggato)
    prefs = ft.SharedPreferences()
    saved_token = await prefs.get("auth_token")
    if saved_token:
        api.set_auth_token(saved_token)
        me = api.get_me()
        if me:
            state["user"] = me
        else:
            # Token scaduto o non valido → pulisci
            api.clear_auth_token()
            await prefs.remove("auth_token")
            await prefs.remove("user_id")
            await prefs.remove("username")

    page.add(header_area, ft.Divider(), content_area)
    go_home()


if __name__ == "__main__":
    ft.run(main, port=8550)