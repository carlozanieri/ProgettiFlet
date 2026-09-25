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


# ==========================
# AVVIO
# ==========================

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 InCantoPipe API su http://localhost:{API_PORT}")
    print(f"📖 Documentazione su http://localhost:{API_PORT}/docs")
    uvicorn.run(app, host=API_HOST, port=API_PORT)