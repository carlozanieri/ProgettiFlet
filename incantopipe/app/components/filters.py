# components/filters.py
import flet as ft


def build_filters(
    categories: list,
    current_category: str,
    current_material: str,
    current_finish: str,
    current_sort: str,
    on_filter_change,
    on_search_submit,
) -> ft.Container:
    """Barra filtri riutilizzabile."""

    # Categorie
    category_options = [ft.dropdown.Option(key="", text="Tutte le categorie")]
    for c in categories:
        category_options.append(
            ft.dropdown.Option(key=c["slug"], text=c["name"])
        )

    category_dd = ft.Dropdown(
        label="Categoria",
        value=current_category,
        options=category_options,
        on_select=lambda e: on_filter_change("category_slug", e.control.value),
        width=200,
    )

    # Materiale
    material_options = [
        ft.dropdown.Option(key="", text="Tutti i materiali"),
        ft.dropdown.Option(key="radica", text="Radica"),
        ft.dropdown.Option(key="morta", text="Radica Morta"),
        ft.dropdown.Option(key="oliva", text="Oliva"),
        ft.dropdown.Option(key="ciliegio", text="Ciliegio"),
        ft.dropdown.Option(key="noce", text="Noce"),
        ft.dropdown.Option(key="quercia", text="Quercia"),
        ft.dropdown.Option(key="acero", text="Acero"),
        ft.dropdown.Option(key="ebano", text="Ebano"),
    ]

    material_dd = ft.Dropdown(
        label="Materiale",
        value=current_material,
        options=material_options,
        on_select=lambda e: on_filter_change("material", e.control.value),
        width=180,
    )

    # Finitura
    finish_options = [
        ft.dropdown.Option(key="", text="Tutte le finiture"),
        ft.dropdown.Option(key="liscia", text="Liscia"),
        ft.dropdown.Option(key="sabbiata", text="Sabbiata"),
        ft.dropdown.Option(key="rustica", text="Rustica"),
        ft.dropdown.Option(key="liscia_sabbiata", text="Liscia/Sabbiata"),
        ft.dropdown.Option(key="levigata", text="Levigata"),
        ft.dropdown.Option(key="naturale", text="Naturale"),
    ]

    finish_dd = ft.Dropdown(
        label="Finitura",
        value=current_finish,
        options=finish_options,
        on_select=lambda e: on_filter_change("finish", e.control.value),
        width=180,
    )

    # Ordinamento
    sort_options = [
        ft.dropdown.Option(key="-created", text="Più recenti"),
        ft.dropdown.Option(key="price_asc", text="Prezzo: crescente"),
        ft.dropdown.Option(key="price_desc", text="Prezzo: decrescente"),
        ft.dropdown.Option(key="name", text="Nome A-Z"),
    ]

    sort_dd = ft.Dropdown(
        label="Ordina per",
        value=current_sort,
        options=sort_options,
        on_select=lambda e: on_filter_change("sort", e.control.value),
        width=200,
    )

    # Ricerca
    search_field = ft.TextField(
        label="Cerca pipe...",
        on_submit=lambda e: on_search_submit(e.control.value),
        width=250,
    )

    # Reset
    reset_btn = ft.TextButton(
        "Azzera filtri",
        on_click=lambda e: on_filter_change("reset", ""),
    )

    return ft.Container(
        content=ft.Column([
            ft.Row(
                [category_dd, material_dd, finish_dd, sort_dd],
                wrap=True,
                spacing=10,
                run_spacing=10,
            ),
            ft.Row(
                [search_field, reset_btn],
                wrap=True,
                spacing=10,
                run_spacing=10,
            ),
        ], spacing=10),
        padding=ft.Padding.symmetric(vertical=15),
    )