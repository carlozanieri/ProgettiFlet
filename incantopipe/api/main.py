# incantopipe_flet/api/main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from config import DATABASE_URL, API_HOST, API_PORT, MEDIA_ROOT


# ==========================
# MODELLI PYDANTIC
# ==========================

class Category(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = ""
    image: Optional[str] = None


class Product(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = ""
    price: float
    available: bool
    stock: int
    category_id: int
    image: Optional[str] = None
    image_2: Optional[str] = None
    image_3: Optional[str] = None
    image_4: Optional[str] = None
    material: Optional[str] = None
    finish: Optional[str] = None
    shape: Optional[str] = None
    length_mm: Optional[int] = None
    height_mm: Optional[int] = None
    bowl_diameter_mm: Optional[int] = None
    bowl_depth_mm: Optional[int] = None
    weight_grams: Optional[int] = None
    filter: Optional[bool] = False
    filter_size: Optional[str] = None
    is_unique: Optional[bool] = True
    year_made: Optional[int] = None
    serial_number: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None


class ProductListItem(BaseModel):
    """Versione ridotta per la lista"""
    id: int
    name: str
    slug: str
    price: float
    image: Optional[str] = None
    available: bool
    stock: int
    material: Optional[str] = None
    finish: Optional[str] = None
    shape: Optional[str] = None


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_slug: str
    product_image: Optional[str] = None
    price: float
    quantity: int
    total: float


class CartResponse(BaseModel):
    cart_id: int
    items: list[CartItemResponse]
    total_items: int
    total_price: float
# ==========================
# CONNESSIONE DATABASE
# ==========================


def get_db():
    """Restituisce una connessione al database PostgreSQL."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


# ==========================
# APP FASTAPI
# ==========================

app = FastAPI(title="InCantoPipe API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Immagini dei prodotti (dalla cartella media di Django)
app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")


# ==========================
# ENDPOINTS
# ==========================

@app.get("/")
def root():
    return {"message": "InCantoPipe API", "version": "1.0.0"}


@app.get("/api/v1/categories", response_model=list[Category])
def get_categories():
    """Restituisce tutte le categorie."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, slug, description, image
                FROM store_category
                ORDER BY name
            """)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()


@app.get("/api/v1/products", response_model=list[ProductListItem])
def get_products(
    category_slug: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    material: Optional[str] = Query(default=None),
    finish: Optional[str] = Query(default=None),
    shape: Optional[str] = Query(default=None),
    sort: Optional[str] = Query(default="-created"),
):
    """Restituisce la lista dei prodotti con filtri."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            query = """
                SELECT p.id, p.name, p.slug, p.price, p.image,
                       p.available, p.stock, p.material, p.finish, p.shape
                FROM store_product p
            """
            params = []
            conditions = []

            if category_slug:
                query += " JOIN store_category c ON p.category_id = c.id "
                conditions.append("c.slug = %s")
                params.append(category_slug)

            conditions.append("p.available = TRUE")
            conditions.append("p.stock > 0")

            if search:
                conditions.append("(p.name ILIKE %s OR p.description ILIKE %s)")
                params.append(f"%{search}%")
                params.append(f"%{search}%")

            if material:
                conditions.append("p.material = %s")
                params.append(material)

            if finish:
                conditions.append("p.finish = %s")
                params.append(finish)

            if shape:
                conditions.append("p.shape = %s")
                params.append(shape)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            # Ordinamento
            sort_map = {
                "-created": "p.created DESC",
                "price_asc": "p.price ASC",
                "price_desc": "p.price DESC",
                "name": "p.name ASC",
            }
            query += " ORDER BY " + sort_map.get(sort, "p.created DESC")

            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()


@app.get("/api/v1/products/{slug}", response_model=Product)
def get_product(slug: str):
    """Restituisce il dettaglio di un prodotto."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.*
                FROM store_product p
                WHERE p.slug = %s AND p.available = TRUE
            """, (slug,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Prodotto non trovato")
            product = dict(row)
            # Converti i tipi non serializzabili
            if product.get("created"):
                product["created"] = product["created"].isoformat()
            if product.get("updated"):
                product["updated"] = product["updated"].isoformat()
            return product
    finally:
        conn.close()

# api/main.py — AGGIUNGI gli endpoint del carrello


def get_or_create_cart(session_key: str) -> int:
    """Ottiene o crea un carrello per la sessione corrente."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM cart_cart WHERE session_key = %s",
                (session_key,)
            )
            row = cur.fetchone()
            if row:
                return row["id"]
            cur.execute(
                "INSERT INTO cart_cart (session_key, created_at, updated_at) "
                "VALUES (%s, NOW(), NOW()) RETURNING id",
                (session_key,)
            )
            cart_id = cur.fetchone()["id"]
        conn.commit()
        return cart_id
    finally:
        conn.close()


@app.get("/api/v1/cart", response_model=CartResponse)
def get_cart(session_key: str = Query(...)):
    """Restituisce il carrello corrente."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM cart_cart WHERE session_key = %s", (session_key,))
            row = cur.fetchone()
            if not row:
                return {"cart_id": 0, "items": [], "total_items": 0, "total_price": 0}
            cart_id = row["id"]
            cur.execute("""
                SELECT ci.id, ci.product_id, ci.quantity,
                       p.name AS product_name, p.slug AS product_slug,
                       p.image AS product_image, p.price
                FROM cart_cartitem ci
                JOIN store_product p ON ci.product_id = p.id
                WHERE ci.cart_id = %s
                ORDER BY ci.added_at
            """, (cart_id,))
            items = []
            for r in cur.fetchall():
                item = dict(r)
                item["price"] = float(item["price"])
                item["total"] = item["price"] * item["quantity"]
                items.append(item)
            total_items = sum(i["quantity"] for i in items)
            total_price = sum(i["total"] for i in items)
            return {
                "cart_id": cart_id,
                "items": items,
                "total_items": total_items,
                "total_price": total_price,
            }
    finally:
        conn.close()


@app.post("/api/v1/cart/add")
def add_to_cart(
    session_key: str = Query(...),
    data: CartItemAdd = ...,
):
    """Aggiunge un prodotto al carrello."""
    conn = get_db()
    try:
        cart_id = get_or_create_cart(session_key)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, quantity FROM cart_cartitem "
                "WHERE cart_id = %s AND product_id = %s",
                (cart_id, data.product_id)
            )
            row = cur.fetchone()
            if row:
                cur.execute(
                    "UPDATE cart_cartitem SET quantity = quantity + %s WHERE id = %s",
                    (data.quantity, row["id"])
                )
            else:
                cur.execute(
                    "INSERT INTO cart_cartitem (cart_id, product_id, quantity, added_at) "
                    "VALUES (%s, %s, %s, NOW())",
                    (cart_id, data.product_id, data.quantity)
                )
            cur.execute("UPDATE cart_cart SET updated_at = NOW() WHERE id = %s", (cart_id,))
        conn.commit()
        return {"success": True, "cart_id": cart_id}
    finally:
        conn.close()


@app.post("/api/v1/cart/update")
def update_cart_item(
    session_key: str = Query(...),
    item_id: int = Query(...),
    data: CartItemUpdate = ...,
):
    """Aggiorna la quantità di un articolo."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if data.quantity <= 0:
                cur.execute("DELETE FROM cart_cartitem WHERE id = %s", (item_id,))
            else:
                cur.execute(
                    "UPDATE cart_cartitem SET quantity = %s WHERE id = %s",
                    (data.quantity, item_id)
                )
        conn.commit()
        return {"success": True}
    finally:
        conn.close()


@app.post("/api/v1/cart/remove")
def remove_from_cart(
    session_key: str = Query(...),
    item_id: int = Query(...),
):
    """Rimuove un articolo dal carrello."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM cart_cartitem WHERE id = %s", (item_id,))
        conn.commit()
        return {"success": True}
    finally:
        conn.close()

# ==========================
# AVVIO
# ==========================

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 InCantoPipe API su http://localhost:{API_PORT}")
    print(f"📖 Documentazione su http://localhost:{API_PORT}/docs")
    uvicorn.run(app, host=API_HOST, port=API_PORT)