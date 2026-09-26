# views/product_detail.py
import flet as ft
from api_client import APIClient
from config import MEDIA_BASE_URL


def build_product_detail_view(
    page: ft.Page,
    api: APIClient,
    slug: str,
    on_back,
) -> ft.Container:
    """Costruisce la vista di dettaglio prodotto."""
    product = api.get_product(slug)

    if not product:
        return ft.Container(
            content=ft.Column([
                ft.Text("Prodotto non trovato", size=24),
                ft.TextButton("← Torna al catalogo", on_click=lambda e: on_back()),
            ]),
            padding=30,
        )

    # Immagine principale
    image_url = (
        f"{MEDIA_BASE_URL}/{product['image']}"
        if product.get("image")
        else None
    )

    main_image = (
        ft.Image(src=image_url, height=400, fit=ft.BoxFit.CONTAIN)
        if image_url
        else ft.Container(
            content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED,
                            size=100, color=ft.Colors.GREY_400),
            height=400,
            bgcolor=ft.Colors.GREY_200,
            alignment=ft.alignment.center,
        )
    )

    # Galleria miniature (se presenti immagini extra)
    thumbnails = []
    for img_field in ["image_2", "image_3", "image_4"]:
        if product.get(img_field):
            thumbnails.append(
                ft.Image(
                    src=f"{MEDIA_BASE_URL}/{product[img_field]}",
                    width=80,
                    height=80,
                    fit=ft.BoxFit.COVER,
                )
            )

    # Caratteristiche
    specs = []
    spec_map = [
        ("Materiale", product.get("material")),
        ("Finitura", product.get("finish")),
        ("Forma", product.get("shape")),
        ("Lunghezza", f"{product['length_mm']} mm" if product.get("length_mm") else None),
        ("Altezza", f"{product['height_mm']} mm" if product.get("height_mm") else None),
        ("Diametro fornello", f"{product['bowl_diameter_mm']} mm" if product.get("bowl_diameter_mm") else None),
        ("Profondità fornello", f"{product['bowl_depth_mm']} mm" if product.get("bowl_depth_mm") else None),
        ("Peso", f"{product['weight_grams']} g" if product.get("weight_grams") else None),
        ("Filtro", "Sì" if product.get("filter") else "No"),
        ("Misura filtro", product.get("filter_size")),
        ("Anno", str(product["year_made"]) if product.get("year_made") else None),
        ("N. serie", product.get("serial_number")),
    ]

    for label, value in spec_map:
        if value:
            specs.append(
                ft.Row([
                    ft.Text(f"{label}:", weight=ft.FontWeight.BOLD, width=180),
                    ft.Text(str(value)),
                ])
            )

    # Badge pezzo unico
    unique_badge = (
        ft.Container(
            content=ft.Text("Pezzo Unico", color=ft.Colors.WHITE,
                            weight=ft.FontWeight.BOLD),
            bgcolor=ft.Colors.ORANGE_700,
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
            border_radius=5,
        )
        if product.get("is_unique")
        else ft.Container()
    )

    return ft.Container(
        content=ft.Column([
            ft.TextButton(
                "← Torna al catalogo",
                on_click=lambda e: on_back(),
            ),
            ft.Row([
                ft.Column([
                    main_image,
                    ft.Row(thumbnails, spacing=5) if thumbnails else ft.Container(),
                ], expand=True),
                ft.Column([
                    unique_badge,
                    ft.Text(product["name"], size=28,
                            weight=ft.FontWeight.BOLD),
                    ft.Text(
                        f"€ {product['price']}",
                        size=24,
                        color=ft.Colors.BROWN_700,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Divider(),
                    ft.Text(product.get("description", ""), size=14),
                    ft.Divider(),
                    ft.Text("Caratteristiche", size=18,
                            weight=ft.FontWeight.BOLD),
                    ft.Column(specs, spacing=5),
                ], expand=True, spacing=15),
            ], spacing=30, vertical_alignment=ft.CrossAxisAlignment.START),
        ], spacing=15),
        padding=20,
    )