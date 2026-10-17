# views/catalog.py
import flet as ft
from api_client import APIClient
from components.product_card import build_product_card
from components.filters import build_filters


def build_catalog_view(
    page: ft.Page,
    api: APIClient,
    state: dict,
    on_product_click,
) -> ft.Container:
    """
    Costruisce la vista del catalogo con filtri.
    state: dict con category_slug, material, finish, sort, search
    """
    products_grid = ft.ResponsiveRow(spacing=15, run_spacing=15)

    def load_products():
        products_grid.controls.clear()
        products = api.get_products(
            category_slug=state.get("category_slug") or None,
            material=state.get("material") or None,
            finish=state.get("finish") or None,
            search=state.get("search") or None,
            sort=state.get("sort", "-created"),
        )

        if not products:
            products_grid.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Nessuna pipe trovata con questi filtri.",
                        size=16,
                        color=ft.Colors.GREY,
                    ),
                    padding=30,
                )
            )
        else:
            for p in products:
                products_grid.controls.append(
                    build_product_card(p, on_product_click)
                )

        page.update()

    def on_filter_change(field: str, value: str):
        if field == "reset":
            state.update({
                "category_slug": "",
                "material": "",
                "finish": "",
                "search": "",
                "sort": "-created",
            })
        else:
            state[field] = value
        load_products()

    def on_search_submit(value: str):
        state["search"] = value
        load_products()

    categories = api.get_categories()

    filters_bar = build_filters(
        categories=categories,
        current_category=state.get("category_slug", ""),
        current_material=state.get("material", ""),
        current_finish=state.get("finish", ""),
        current_sort=state.get("sort", "-created"),
        on_filter_change=on_filter_change,
        on_search_submit=on_search_submit,
    )

    load_products()

    return ft.Container(
        content=ft.Column([
            filters_bar,
            products_grid,
        ], spacing=10),
    )