import flet as ft
import asyncio
from api_client import APIClient
from components.header import build_header
from views.catalog import build_catalog_view
from views.product_detail import build_product_detail_view
from views.cart import build_cart_view
from views.auth import build_login_view, build_register_view
from views.checkout import build_checkout_view
from views.orders import build_orders_list_view, build_order_detail_view
from views.admin_orders import (
    build_admin_orders_view,
    build_admin_order_detail_view,
)
api = APIClient()


async def main(page: ft.Page):

    page.title = "InCantoPipe"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    prefs = ft.SharedPreferences()

    state = {
        "category_slug": "", "material": "", "finish": "",
        "search": "", "sort": "-created",
        "user": None,
        "return_to": None,
    }

    content_area = ft.Column()
    header_area = ft.Column()

    # ============================================================
    # HEADER
    # ============================================================

    def update_header():
        if state["user"]:
            cart = api.get_cart()
            cart_count = cart["total_items"]
        else:
            cart_count = 0

        header_area.controls.clear()
        header_area.controls.append(
            build_header(
                on_home_click=lambda e: go_home(),
                on_cart_click=lambda e: go_cart(),
                on_login_click=lambda: go_login(from_view="catalog"),
                on_register_click=lambda: go_register(from_view="catalog"),
                on_logout_click=lambda: page.run_task(do_logout),
                on_orders_click=lambda: go_orders(),
                on_admin_click=lambda: go_admin_orders(),
                cart_count=cart_count,
                user=state.get("user"),
            )
        )
        page.update()

    # ============================================================
    # AUTENTICAZIONE
    # ============================================================

    def do_login_success(user_data):
        me = api.get_me()
        if me:
            state["user"] = me
        else:
            state["user"] = {
                "username": user_data.get("username"),
                "user_id": user_data.get("user_id"),
            }

        return_to = state.get("return_to")
        state["return_to"] = None
        if return_to == "cart":
            go_cart()
        elif return_to == "checkout":
            go_checkout()
        elif return_to == "orders":
            go_orders()
        else:
            go_home()

    async def do_logout():
        api.clear_auth_token()
        try:
            await prefs.remove("auth_token")
            await prefs.remove("user_id")
            await prefs.remove("username")
        except Exception as e:
            print(f"Errore rimozione token: {e}")
        state["user"] = None
        page.show_dialog(ft.SnackBar(content=ft.Text("Logout effettuato")))
        go_home()

    # ============================================================
    # NAVIGAZIONE
    # ============================================================

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

    def go_login(from_view="catalog"):
        state["return_to"] = from_view
        content_area.controls.clear()
        content_area.controls.append(
            build_login_view(
                page, api, prefs,
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
                page, api, prefs,
                on_success=do_login_success,
                on_login_click=lambda: go_login(from_view=from_view),
                on_back=lambda: go_home(),
            )
        )
        page.update()

    def go_cart():
        if not state["user"]:
            show_auth_dialog()
            return
        content_area.controls.clear()
        content_area.controls.append(
            build_cart_view(
                page, api,
                on_checkout=lambda: go_checkout(),
                on_back=go_home,
            )
        )
        update_header()
        page.update()

    def go_checkout():

        if not state["user"]:

            go_login(from_view="checkout")
            return

        content_area.controls.clear()

        content_area.controls.append(
            build_checkout_view(
                page, api,
                user=state["user"],
                on_success=do_order_success,
                on_back=go_cart,
            )
        )

        page.update()

    def go_orders():
        if not state["user"]:
            go_login(from_view="orders")
            return
        content_area.controls.clear()
        content_area.controls.append(
            build_orders_list_view(
                page, api,
                on_order_click=go_order_detail,
                on_back=go_home,
            )
        )
        page.update()

    def go_order_detail(order_id: int):
        content_area.controls.clear()
        content_area.controls.append(
            build_order_detail_view(
                page, api, order_id,
                on_back=go_orders,
                on_cancel=do_cancel_order,
            )
        )
        page.update()

    def add_to_cart(product_id: int):
        if not state["user"]:
            show_auth_dialog()
            return
        if api.add_to_cart(product_id):
            page.show_dialog(ft.SnackBar(
                content=ft.Text("Aggiunto al carrello!"),
                bgcolor=ft.Colors.GREEN_700,
            ))
            update_header()
        else:
            page.show_dialog(ft.SnackBar(
                content=ft.Text("Errore nell'aggiunta (prodotto non disponibile?)"),
                bgcolor=ft.Colors.RED_700,
            ))
        page.update()

    def do_order_success(order_data):
        order_number = order_data.get("order_number", "")
        page.show_dialog(ft.SnackBar(
            content=ft.Text(f"Ordine {order_number} creato! Pagamento in arrivo."),
            bgcolor=ft.Colors.GREEN_700,
        ))
        # Fase 7: qui andrà il flusso di pagamento
        go_home()

    def do_cancel_order(order_id: int):
        success, result = api.cancel_order(order_id)
        if success:
            page.show_dialog(ft.SnackBar(
                content=ft.Text("Ordine annullato"),
                bgcolor=ft.Colors.GREEN_700,
            ))
            update_header()
            go_orders()
        else:
            page.show_dialog(ft.SnackBar(
                content=ft.Text(f"Errore: {result}"),
                bgcolor=ft.Colors.RED_700,
            ))
            page.update()

    def show_auth_dialog():
        dialog = ft.AlertDialog(
            title=ft.Text("Accedi o registrati"),
            content=ft.Text(
                "Per procedere all'ordine è necessario accedere con il tuo "
                "utente o registrarti come nuovo utente."
            ),
            actions=[
                ft.TextButton(
                    "Annulla",
                    on_click=lambda e: page.pop_dialog(),
                ),
                ft.TextButton(
                    "Accedi",
                    on_click=lambda e: (page.pop_dialog(), go_login(from_view="catalog")),
                ),
                ft.Button(
                    content=ft.Text("Registrati"),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BROWN_700,
                        color=ft.Colors.WHITE,
                    ),
                    on_click=lambda e: (page.pop_dialog(), go_register(from_view="catalog")),
                ),
            ],
        )
        page.show_dialog(dialog)

    def go_admin_orders():
        """Vista admin: lista ordini."""
        if not state["user"] or not state["user"].get("is_staff"):
            page.show_dialog(ft.SnackBar(
                content=ft.Text("Accesso riservato agli amministratori"),
                bgcolor=ft.Colors.RED_700,
            ))
            return
        content_area.controls.clear()
        content_area.controls.append(
            build_admin_orders_view(
                page, api,
                on_order_click=go_admin_order_detail,
                on_back=go_home,
            )
        )
        page.update()

    def go_admin_order_detail(order_id: int):
        """Vista admin: dettaglio ordine."""
        content_area.controls.clear()
        content_area.controls.append(
            build_admin_order_detail_view(
                page, api, order_id,
                on_back=go_admin_orders,
                on_ship_done=lambda oid: go_admin_orders(),
                on_cancel_done=lambda oid: go_admin_orders(),
            )
        )
        page.update()
    # ============================================================
    # AVVIO
    # ============================================================

    # 1. Rendi la pagina SUBITO
    page.add(header_area, ft.Divider(), content_area)
    go_home()
    page.update()

    # 2. Poi carica il token, con protezione
    try:
        saved_token = await prefs.get("auth_token")
        if saved_token:
            api.set_auth_token(saved_token)
            me = api.get_me()
            if me:
                state["user"] = me
                update_header()
                page.update()
            else:
                api.clear_auth_token()
                await prefs.remove("auth_token")
                await prefs.remove("user_id")
                await prefs.remove("username")
    except Exception as e:
        print(f"Errore lettura token all'avvio: {e}")


if __name__ == "__main__":
    ft.run(main, port=8550)