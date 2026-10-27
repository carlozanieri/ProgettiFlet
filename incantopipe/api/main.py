# incantopipe_flet/api/main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import psycopg2
from datetime import datetime
import random
import string
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from config import DATABASE_URL, API_HOST, API_PORT, MEDIA_ROOT
#from pydantic import BaseModel, EmailStr
#from auth import create_access_token, verify_password, get_current_user
from pydantic import EmailStr
from fastapi import Depends
from payment.paypal import paypal_service
from auth import (
    verify_password,
    create_access_token,
    get_current_user,
    get_optional_user,
    get_current_admin,          # ← AGGIUNGI
    hash_password,
)
from fastapi import BackgroundTasks
from email_service import send_email_smtp, send_order_confirmation_email

# ==========================
# MODELLI PYDANTIC
# ==========================


class RegisterResponse(BaseModel):
    message: str
    user_id: int
    username: str


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


class OrderCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str = ""
    address: str
    postal_code: str
    city: str
    province: str = ""
    country: str = "Italia"
    shipping_notes: str = ""
    payment_method: str = "paypal"


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    price: float
    quantity: int
    total: float


class OrderResponse(BaseModel):
    id: int
    order_number: str
    status: str
    payment_status: str
    payment_method: str
    total: float
    shipping_cost: float
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    postal_code: str
    city: str
    province: str
    country: str
    shipping_notes: str
    created: str
    paid_at: Optional[str] = None
    shipped_at: Optional[str] = None
    delivered_at: Optional[str] = None
    items: list[OrderItemResponse]


class OrderListItem(BaseModel):
    id: int
    order_number: str
    status: str
    payment_status: str
    total: float
    created: str
    item_count: int


class AdminShipRequest(BaseModel):
    tracking_number: str = ""

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


def get_or_create_cart(user_id: int) -> int:
    """Restituisce (o crea) il carrello dell'utente loggato."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM cart_cart WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            if row:
                return row["id"]
            cur.execute(
                "INSERT INTO cart_cart (user_id, created_at, updated_at) "
                "VALUES (%s, NOW(), NOW()) RETURNING id",
                (user_id,)
            )
            cart_id = cur.fetchone()["id"]
        conn.commit()
        return cart_id
    finally:
        conn.close()

@app.get("/api/v1/cart", response_model=CartResponse)
def get_cart(current_user: dict = Depends(get_current_user)):
    """Restituisce il carrello dell'utente loggato."""
    user_id = current_user["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM cart_cart WHERE user_id = %s", (user_id,))
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
# api/main.py — SOSTITUISCI add_to_cart


@app.post("/api/v1/cart/add")
def add_to_cart(
    data: CartItemAdd = ...,
    current_user: dict = Depends(get_current_user),
):
    """Aggiunge un prodotto al carrello dell'utente loggato."""
    user_id = current_user["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 1. Blocca il prodotto
            cur.execute("""
                SELECT id, name, stock, available
                FROM store_product
                WHERE id = %s
                FOR UPDATE
            """, (data.product_id,))
            product = cur.fetchone()
            if not product:
                raise HTTPException(status_code=404, detail="Prodotto non trovato")
            if not product["available"] or product["stock"] <= 0:
                raise HTTPException(status_code=400, detail="Prodotto non disponibile")
            if product["stock"] < data.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Disponibilità insufficiente. Rimaste: {product['stock']}"
                )

            # 2. Carrello dell'utente
            cart_id = get_or_create_cart(user_id)

            # 3. Verifica se già nel carrello
            cur.execute("""
                SELECT id, quantity FROM cart_cartitem
                WHERE cart_id = %s AND product_id = %s
            """, (cart_id, data.product_id))
            existing = cur.fetchone()

            if existing:
                new_quantity = existing["quantity"] + data.quantity
                cur.execute(
                    "UPDATE cart_cartitem SET quantity = %s WHERE id = %s",
                    (new_quantity, existing["id"])
                )
            else:
                cur.execute("""
                    INSERT INTO cart_cartitem (cart_id, product_id, quantity, added_at)
                    VALUES (%s, %s, %s, NOW())
                """, (cart_id, data.product_id, data.quantity))

            # 4. Decrementa lo stock (sempre, sia existing che nuovo)
            new_stock = product["stock"] - data.quantity
            cur.execute("""
                UPDATE store_product
                SET stock = %s, available = %s
                WHERE id = %s
            """, (new_stock, new_stock > 0, data.product_id))

            # 5. Reset del timer
            cur.execute("""
                UPDATE cart_cart
                SET updated_at = NOW(), reminder_sent = FALSE
                WHERE id = %s
            """, (cart_id,))

        conn.commit()
        return {"success": True, "cart_id": cart_id}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
# api/main.py — SOSTITUISCI update_cart_item


@app.post("/api/v1/cart/update")
def update_cart_item(
    item_id: int = Query(...),
    data: CartItemUpdate = ...,
    current_user: dict = Depends(get_current_user),
):
    """Aggiorna la quantità di un articolo."""
    user_id = current_user["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ci.product_id, ci.cart_id, ci.quantity
                FROM cart_cartitem ci
                JOIN cart_cart c ON ci.cart_id = c.id
                WHERE ci.id = %s AND c.user_id = %s
            """, (item_id, user_id))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Articolo non trovato")

            product_id = row["product_id"]
            cart_id = row["cart_id"]
            old_quantity = row["quantity"]

            if data.quantity <= 0:
                cur.execute("""
                    UPDATE store_product
                    SET stock = stock + %s, available = TRUE
                    WHERE id = %s
                """, (old_quantity, product_id))
                cur.execute("DELETE FROM cart_cartitem WHERE id = %s", (item_id,))
            else:
                diff = data.quantity - old_quantity
                if diff > 0:
                    cur.execute(
                        "SELECT stock FROM store_product WHERE id = %s FOR UPDATE",
                        (product_id,)
                    )
                    current = cur.fetchone()
                    if current["stock"] < diff:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Disponibilità insufficiente. Rimaste: {current['stock']}"
                        )

                cur.execute("""
                    UPDATE store_product
                    SET stock = stock - %s,
                        available = (stock - %s) > 0
                    WHERE id = %s
                """, (diff, diff, product_id))

                cur.execute(
                    "UPDATE cart_cartitem SET quantity = %s WHERE id = %s",
                    (data.quantity, item_id)
                )

            cur.execute("""
                UPDATE cart_cart
                SET updated_at = NOW(), reminder_sent = FALSE
                WHERE id = %s
            """, (cart_id,))

        conn.commit()
        return {"success": True}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# api/main.py — SOSTITUISCI remove_from_cart

@app.post("/api/v1/cart/remove")
def remove_from_cart(
    item_id: int = Query(...),
    current_user: dict = Depends(get_current_user),
):
    """Rimuove un articolo dal carrello dell'utente."""
    user_id = current_user["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Verifica che l'item appartenga a un carrello dell'utente
            cur.execute("""
                SELECT ci.product_id, ci.cart_id, ci.quantity
                FROM cart_cartitem ci
                JOIN cart_cart c ON ci.cart_id = c.id
                WHERE ci.id = %s AND c.user_id = %s
            """, (item_id, user_id))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Articolo non trovato")

            product_id = row["product_id"]
            cart_id = row["cart_id"]
            quantity = row["quantity"]

            # Ripristina lo stock
            cur.execute("""
                UPDATE store_product
                SET stock = stock + %s, available = TRUE
                WHERE id = %s
            """, (quantity, product_id))

            # Elimina l'item
            cur.execute("DELETE FROM cart_cartitem WHERE id = %s", (item_id,))

            # Reset del timer
            cur.execute("""
                UPDATE cart_cart
                SET updated_at = NOW(), reminder_sent = FALSE
                WHERE id = %s
            """, (cart_id,))

        conn.commit()
        return {"success": True}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
# ==========================
# AVVIO
# ==========================


# api/main.py (da aggiungere)


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str = ""
    last_name: str = ""


@app.post("/api/v1/auth/register", response_model=RegisterResponse)
def register(user_data: UserRegister):
    """Registra un nuovo utente."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 1. Verifica duplicati (username o email)
            cur.execute(
                "SELECT id FROM auth_user WHERE username = %s OR email = %s",
                (user_data.username, user_data.email)
            )
            if cur.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="Username o email già in uso"
                )

            # 2. Hash della password nel formato Django
            # Questa operazione è eseguita qui, prima di qualsiasi operazione DB
            hashed_pw = hash_password(user_data.password)

            # 3. Inserisci il nuovo utente
            cur.execute("""
                INSERT INTO auth_user (
                    username, email, password,
                    first_name, last_name,
                    is_active, is_staff, is_superuser,
                    date_joined
                )
                VALUES (%s, %s, %s, %s, %s, TRUE, FALSE, FALSE, NOW())
                RETURNING id
            """, (
                user_data.username,
                user_data.email,
                hashed_pw,
                user_data.first_name,
                user_data.last_name,
            ))
            new_user_id = cur.fetchone()["id"]

        # Esegue il commit solo se tutto il blocco 'with' è andato a buon fine
        conn.commit()

        return {
            "message": "Registrazione completata",
            "user_id": new_user_id,
            "username": user_data.username,
        }

    except HTTPException:
        # Se l'eccezione è già un HTTPException (es. 400), la rilanciamo
        conn.rollback()
        raise
    except Exception as e:
        # Per qualsiasi altro errore, eseguiamo il rollback e restituiamo un 500 generico
        conn.rollback()
        # Logga l'errore sul server per il debug
        print(f"ERRORE CRITICO durante la registrazione: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Errore interno del server durante la registrazione.")
    finally:
        # La connessione viene sempre chiusa, indipendentemente dall'esito
        conn.close()


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_staff: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str

# api/main.py — AGGIUNGI gli endpoint di autenticazione


@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login(credentials: UserLogin):
    """Login: restituisce un JWT se le credenziali sono valide."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, password FROM auth_user "
                "WHERE username = %s AND is_active = TRUE",
                (credentials.username,)
            )
            user = cur.fetchone()

        if not user or not verify_password(credentials.password, user["password"]):
            raise HTTPException(status_code=401, detail="Credenziali non valide")

        token = create_access_token(data={
            "sub": user["username"],
            "user_id": user["id"],
        })
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user["id"],
            "username": user["username"],
        }
    finally:
        conn.close()


@app.get("/api/v1/auth/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """Restituisce i dati dell'utente autenticato."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, email, first_name, last_name, is_staff "
                "FROM auth_user WHERE id = %s",
                (current_user["user_id"],)
            )
            user = cur.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="Utente non trovato")
            return dict(user)
    finally:
        conn.close()

# api/main.py — AGGIUNGI prima di if __name__

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str = ""
    last_name: str = ""


class RegisterResponse(BaseModel):
    message: str
    user_id: int
    username: str


@app.post("/api/v1/auth/register", response_model=RegisterResponse)
def register(user_data: UserRegister):
    """Registra un nuovo utente."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Verifica duplicati (username o email)
            cur.execute(
                "SELECT id FROM auth_user WHERE username = %s OR email = %s",
                (user_data.username, user_data.email)
            )
            if cur.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="Username o email già in uso"
                )

            # Hash della password nel formato Django
            hashed_pw = hash_password(user_data.password)

            # Inserisci il nuovo utente
            cur.execute("""
                INSERT INTO auth_user (
                    username, email, password,
                    first_name, last_name,
                    is_active, is_staff, is_superuser,
                    date_joined
                )
                VALUES (%s, %s, %s, %s, %s, TRUE, FALSE, FALSE, NOW())
                RETURNING id
            """, (
                user_data.username,
                user_data.email,
                hashed_pw,
                user_data.first_name,
                user_data.last_name,
            ))
            new_user_id = cur.fetchone()["id"]
        conn.commit()
        return {
            "message": "Registrazione completata",
            "user_id": new_user_id,
            "username": user_data.username,
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")
    finally:
        conn.close()


# api/main.py — AGGIUNGI prima di if __name__

class CartAssociateRequest(BaseModel):
    session_key: str


# api/main.py — AGGIUNGI prima di if __name__

@app.get("/api/v1/cart/me", response_model=CartResponse)
def get_my_cart(current_user: dict = Depends(get_current_user)):
    """Restituisce il carrello dell'utente autenticato."""
    user_id = current_user["user_id"]

    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Cerca il carrello dell'utente
            cur.execute("SELECT id FROM cart_cart WHERE user_id = %s", (user_id,))
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


def generate_order_number() -> str:
    """Genera un numero ordine unico nel formato ICP-YYYYMMDD-XXXXXX."""
    prefix = "ICP"
    timestamp = datetime.now().strftime("%Y%m%d")
    random_part = "".join(random.choices(string.digits, k=6))
    return f"{prefix}-{timestamp}-{random_part}"


@app.post("/api/v1/orders", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Crea un ordine dal carrello e avvia l'autorizzazione PayPal."""
    user_id = current_user["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 1. Trova il carrello
            cur.execute("SELECT id FROM cart_cart WHERE user_id = %s", (user_id,))
            cart_row = cur.fetchone()
            if not cart_row:
                raise HTTPException(status_code=400, detail="Carrello vuoto")
            cart_id = cart_row["id"]

            # 2. Recupera gli item
            cur.execute("""
                SELECT ci.product_id, ci.quantity,
                       p.name AS product_name, p.price
                FROM cart_cartitem ci
                JOIN store_product p ON ci.product_id = p.id
                WHERE ci.cart_id = %s
            """, (cart_id,))
            items = cur.fetchall()
            if not items:
                raise HTTPException(status_code=400, detail="Carrello vuoto")

            # 3. Totale
            total = sum(float(item["price"]) * item["quantity"] for item in items)

            # 4. Crea l'ordine nel database
            order_number = generate_order_number()
            cur.execute("""
                INSERT INTO orders_order (
                    first_name, last_name, email, phone,
                    address, postal_code, city, province, country,
                    shipping_notes, payment_method, paypal_transaction_id,
                    payment_status, status, total, shipping_cost,
                    user_id, order_number, created, updated
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, '',
                    'pending', 'pending', %s, 0,
                    %s, %s, NOW(), NOW()
                )
                RETURNING id, created
            """, (
                order_data.first_name, order_data.last_name, order_data.email, order_data.phone,
                order_data.address, order_data.postal_code, order_data.city,
                order_data.province, order_data.country,
                order_data.shipping_notes, order_data.payment_method,
                total, user_id, order_number,
            ))
            row = cur.fetchone()
            order_id = row["id"]
            created = row["created"]

            # 5. Crea gli order items
            for item in items:
                cur.execute("""
                    INSERT INTO orders_orderitem (
                        order_id, product_id, product_name,
                        price, quantity, payment_method
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    order_id, item["product_id"], item["product_name"],
                    item["price"], item["quantity"], order_data.payment_method,
                ))

            # 6. Svuota il carrello
            cur.execute("DELETE FROM cart_cartitem WHERE cart_id = %s", (cart_id,))
            cur.execute("""
                UPDATE cart_cart
                SET updated_at = NOW(), reminder_sent = FALSE
                WHERE id = %s
            """, (cart_id,))

        # ---> PRIMO COMMIT: L'ordine esiste nel database in stato pending <---
        conn.commit()

        # 7. Se il metodo di pagamento richiede PayPal, avvia l'autorizzazione
        paypal_order_id = None
        if order_data.payment_method in ("paypal", "credit_card"):
            return_url = f"https://incantopipe.it/api/v1/payment/paypal/card-success?order_id={order_id}" if order_data.payment_method == "credit_card" else f"https://incantopipe.it/payment/success?order_id={order_id}"
            cancel_url = f"https://incantopipe.it/payment/cancel?order_id={order_id}"
            
            # Per il flusso carta usiamo payment_source={"card": ...}, per PayPal standard nessun payment_source
            if order_data.payment_method == "credit_card":
                payment_source = {
                    "card": {
                        "attributes": {
                            "verification": {"method": "SCA_ALWAYS"}
                        },
                        "experience_context": {
                            "return_url": return_url,
                            "cancel_url": cancel_url,
                            "shipping_preference": "NO_SHIPPING",
                        }
                    }
                }
            else:
                payment_source = None

            # Chiamata a PayPal
            order_for_paypal = {"id": order_id, "order_number": order_number, "total": total}
            paypal_id, error = paypal_service.create_order(
                order_for_paypal, return_url, cancel_url, payment_source=payment_source
            )
            
            if error:
                # Se PayPal fallisce, l'ordine resta pending nel DB (lo scheduler lo pulirà)
                raise HTTPException(status_code=500, detail=f"Errore PayPal: {error}")
            
            paypal_order_id = paypal_id

            # 8. Aggiorna l'ordine con il paypal_order_id
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE orders_order
                    SET paypal_transaction_id = %s, updated = NOW()
                    WHERE id = %s
                """, (paypal_order_id, order_id))
            
            # ---> SECONDO COMMIT: Salviamo l'ID PayPal <---
            conn.commit()

        # 9. ---> LEGGIAMO I DATI DAL DATABASE PER LA RISPOSTA <---
        # Questo garantisce che la risposta rispecchi esattamente ciò che è nel DB
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, order_number, status, payment_status, payment_method,
                       total, shipping_cost, first_name, last_name, email, phone,
                       address, postal_code, city, province, country, shipping_notes,
                       created, paid_at, shipped_at, delivered_at, paypal_transaction_id
                FROM orders_order WHERE id = %s
            """, (order_id,))
            db_order = cur.fetchone()

            cur.execute("""
                SELECT id, product_id, product_name, price, quantity
                FROM orders_orderitem WHERE order_id = %s
            """, (order_id,))
            db_items = cur.fetchall()

        # 10. Costruisci la risposta usando i dati letti dal DB
        return {
            "id": db_order["id"],
            "order_number": db_order["order_number"],
            "status": db_order["status"],
            "payment_status": db_order["payment_status"],
            "payment_method": db_order["payment_method"],
            "total": float(db_order["total"]),
            "shipping_cost": float(db_order["shipping_cost"]),
            "first_name": db_order["first_name"],
            "last_name": db_order["last_name"],
            "email": db_order["email"],
            "phone": db_order["phone"],
            "address": db_order["address"],
            "postal_code": db_order["postal_code"],
            "city": db_order["city"],
            "province": db_order["province"],
            "country": db_order["country"],
            "shipping_notes": db_order["shipping_notes"],
            "created": db_order["created"].isoformat(),
            "paid_at": db_order["paid_at"].isoformat() if db_order["paid_at"] else None,
            "shipped_at": db_order["shipped_at"].isoformat() if db_order["shipped_at"] else None,
            "delivered_at": db_order["delivered_at"].isoformat() if db_order["delivered_at"] else None,
            "paypal_order_id": db_order["paypal_transaction_id"],  # <-- Letto dal DB
            "items": [
                {
                    "id": i["id"],
                    "product_id": i["product_id"],
                    "product_name": i["product_name"],
                    "price": float(i["price"]),
                    "quantity": i["quantity"],
                    "total": float(i["price"]) * i["quantity"],
                }
                for i in db_items
            ],
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")
    finally:
        conn.close()


@app.get("/api/v1/orders", response_model=list[OrderListItem])
def get_orders(current_user: dict = Depends(get_current_user)):
    """Storico ordini dell'utente autenticato."""
    user_id = current_user["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.id, o.order_number, o.status, o.payment_status,
                       o.total, o.created,
                       (SELECT COUNT(*) FROM orders_orderitem WHERE order_id = o.id) AS item_count
                FROM orders_order o
                WHERE o.user_id = %s
                ORDER BY o.created DESC
            """, (user_id,))
            rows = cur.fetchall()
            return [
                {
                    "id": r["id"],
                    "order_number": r["order_number"],
                    "status": r["status"],
                    "payment_status": r["payment_status"],
                    "total": float(r["total"]),
                    "created": r["created"].isoformat(),
                    "item_count": r["item_count"],
                }
                for r in rows
            ]
    finally:
        conn.close()


@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, current_user: dict = Depends(get_current_user)):
    """Dettaglio di un ordine dell'utente autenticato."""
    user_id = current_user["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM orders_order
                WHERE id = %s AND user_id = %s
            """, (order_id, user_id))
            order = cur.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="Ordine non trovato")

            cur.execute("""
                SELECT id, product_id, product_name, price, quantity
                FROM orders_orderitem
                WHERE order_id = %s
            """, (order_id,))
            items = cur.fetchall()

            return {
                "id": order["id"],
                "order_number": order["order_number"],
                "status": order["status"],
                "payment_status": order["payment_status"],
                "payment_method": order["payment_method"],
                "total": float(order["total"]),
                "shipping_cost": float(order["shipping_cost"]),
                "first_name": order["first_name"],
                "last_name": order["last_name"],
                "email": order["email"],
                "phone": order["phone"],
                "address": order["address"],
                "postal_code": order["postal_code"],
                "city": order["city"],
                "province": order["province"],
                "country": order["country"],
                "shipping_notes": order["shipping_notes"],
                "created": order["created"].isoformat(),
                "paid_at": order["paid_at"].isoformat() if order["paid_at"] else None,
                "shipped_at": order["shipped_at"].isoformat() if order["shipped_at"] else None,
                "delivered_at": order["delivered_at"].isoformat() if order["delivered_at"] else None,
                "items": [
                    {
                        "id": item["id"],
                        "product_id": item["product_id"],
                        "product_name": item["product_name"],
                        "price": float(item["price"]),
                        "quantity": item["quantity"],
                        "total": float(item["price"]) * item["quantity"],
                    }
                    for item in items
                ],
            }
    finally:
        conn.close()

@app.post("/api/v1/orders/{order_id}/cancel")
def cancel_order(order_id: int, current_user: dict = Depends(get_current_user)):
    """Annulla un ordine in stato 'pending'.

    Ripristina lo stock dei prodotti e rimuove gli item corrispondenti dal carrello.
    """
    user_id = current_user["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 1. Verifica che l'ordine esista, sia dell'utente e sia "pending"
            cur.execute("""
                SELECT id, status FROM orders_order
                WHERE id = %s AND user_id = %s
                FOR UPDATE
            """, (order_id, user_id))
            order = cur.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="Ordine non trovato")
            if order["status"] != "pending":
                raise HTTPException(
                    status_code=400,
                    detail="Solo gli ordini in attesa possono essere annullati"
                )

            # 2. Recupera gli item dell'ordine
            cur.execute("""
                SELECT product_id, quantity FROM orders_orderitem
                WHERE order_id = %s
            """, (order_id,))
            items = cur.fetchall()

            # 3. Ripristina lo stock
            for item in items:
                cur.execute("""
                    UPDATE store_product
                    SET stock = stock + %s, available = TRUE
                    WHERE id = %s
                """, (item["quantity"], item["product_id"]))

            # 4. Rimuovi dal carrello gli item corrispondenti
            cur.execute("SELECT id FROM cart_cart WHERE user_id = %s", (user_id,))
            cart_row = cur.fetchone()
            if cart_row:
                cart_id = cart_row["id"]
                product_ids = [item["product_id"] for item in items]
                if product_ids:
                    cur.execute("""
                        DELETE FROM cart_cartitem
                        WHERE cart_id = %s AND product_id = ANY(%s)
                    """, (cart_id, product_ids))
                    cur.execute("""
                        UPDATE cart_cart
                        SET updated_at = NOW(), reminder_sent = FALSE
                        WHERE id = %s
                    """, (cart_id,))

            # 5. Marca l'ordine come cancellato
            cur.execute("""
                UPDATE orders_order
                SET status = 'cancelled', updated = NOW()
                WHERE id = %s
            """, (order_id,))

        conn.commit()
        return {"success": True, "order_id": order_id, "status": "cancelled"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")
    finally:
        conn.close()


class PayPalAuthorizeRequest(BaseModel):
    order_id: int


@app.post("/api/v1/payment/paypal/authorize")
def paypal_authorize(
    data: PayPalAuthorizeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Crea l'ordine PayPal e restituisce l'URL di approvazione."""
    user_id = current_user["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, order_number, total, status, payment_status, user_id
                FROM orders_order
                WHERE id = %s AND user_id = %s
            """, (data.order_id, user_id))
            order = cur.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="Ordine non trovato")
            if order["status"] != "pending":
                raise HTTPException(
                    status_code=400,
                    detail=f"Ordine in stato '{order['status']}', non 'pending'"
                )

            return_url = f"https://incantopipe.it/payment/success?order_id={order['id']}"
            cancel_url = f"https://incantopipe.it/payment/cancel?order_id={order['id']}"
            paypal_id, error = paypal_service.create_order(order, return_url, cancel_url)
            if error:
                raise HTTPException(status_code=500, detail=f"Errore PayPal: {error}")

            # Salva il paypal_order_id
            cur.execute("""
                UPDATE orders_order
                SET paypal_transaction_id = %s, updated = NOW()
                WHERE id = %s
            """, (paypal_id, order["id"]))

        conn.commit()

        approve_url = paypal_service.get_approve_url(paypal_id)
        return {
            "paypal_order_id": paypal_id,
            "order_id": order["id"],
            "approve_url": approve_url,        # ← NUOVO
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


class PayPalCaptureRequest(BaseModel):
    order_id: int


class PayPalVoidRequest(BaseModel):
    order_id: int


@app.post("/api/v1/payment/paypal/capture")
def paypal_capture(
    data: PayPalCaptureRequest,
    current_user: dict = Depends(get_current_user),
):
    """Cattura il pagamento PayPal (incassa i fondi).

    Funziona solo per ordini in stato 'authorized'.
    """
    user_id = current_user["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, paypal_authorization_id, status, payment_status
                FROM orders_order
                WHERE id = %s AND user_id = %s
            """, (data.order_id, user_id))
            order = cur.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="Ordine non trovato")
            if order["payment_status"] != "authorized":
                raise HTTPException(
                    status_code=400,
                    detail=f"Ordine con payment_status '{order['payment_status']}', non 'authorized'"
                )
            if not order["paypal_authorization_id"]:
                raise HTTPException(
                    status_code=400,
                    detail="Ordine senza paypal_authorization_id"
                )

            auth_id = order["paypal_authorization_id"]

        # Cattura l'autorizzazione
        capture_id, error = paypal_service.capture_authorization(auth_id)
        if error:
            raise HTTPException(status_code=500, detail=f"Errore capture: {error}")

        # Aggiorna l'ordine
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE orders_order
                SET status = 'paid',
                    payment_status = 'captured',
                    paypal_capture_id = %s,
                    paid_at = NOW(),
                    updated = NOW()
                WHERE id = %s
            """, (capture_id, data.order_id))
        conn.commit()

        return {
            "success": True,
            "order_id": data.order_id,
            "paypal_capture_id": capture_id,
            "status": "paid",
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")
    finally:
        conn.close()


@app.post("/api/v1/payment/paypal/void")
def paypal_void(
    data: PayPalVoidRequest,
    current_user: dict = Depends(get_current_user),
):
    """Annulla l'autorizzazione PayPal (sblocca i fondi)."""
    user_id = current_user["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, paypal_authorization_id, payment_status
                FROM orders_order
                WHERE id = %s AND user_id = %s
            """, (data.order_id, user_id))
            order = cur.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="Ordine non trovato")
            if not order["paypal_authorization_id"]:
                raise HTTPException(
                    status_code=400,
                    detail="Ordine senza paypal_authorization_id"
                )

            auth_id = order["paypal_authorization_id"]

        # Chiama PayPal per annullare l'autorizzazione
        success, error = paypal_service.void_authorization(auth_id)
        if not success:
            raise HTTPException(status_code=500, detail=f"Errore void: {error}")

        # Aggiorna l'ordine
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE orders_order
                SET status = 'cancelled',
                    payment_status = 'voided',
                    updated = NOW()
                WHERE id = %s
            """, (data.order_id,))
        conn.commit()

        return {
            "success": True,
            "order_id": data.order_id,
            "status": "cancelled",
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")
    finally:
        conn.close()


@app.get("/api/v1/payment/paypal/status/{order_id}")
def paypal_status(
    order_id: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Verifica lo stato dell'ordine PayPal e autorizza se approvato."""
    user_id = current_user["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, paypal_transaction_id, status, payment_status
                FROM orders_order
                WHERE id = %s AND user_id = %s
            """, (order_id, user_id))
            order = cur.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="Ordine non trovato")

            if order["payment_status"] == "authorized":
                return {
                    "order_id": order_id, "status": order["status"],
                    "payment_status": order["payment_status"], "authorized": True,
                }

            if not order["paypal_transaction_id"]:
                raise HTTPException(status_code=400, detail="Ordine senza paypal_order_id")

            paypal_order_id = order["paypal_transaction_id"]

        # 1. Interroga PayPal per lo stato
        pp_status, error = paypal_service.get_order_status(paypal_order_id)
        if error:
            raise HTTPException(status_code=500, detail=f"Errore PayPal: {error}")

        # 2. Se lo stato è APPROVED, autorizza
        if pp_status == "APPROVED":
            auth_id, error = paypal_service.authorize_order(paypal_order_id)
            if error:
                raise HTTPException(status_code=500, detail=f"Errore authorize: {error}")

            # 3. Aggiorna l'ordine e recupera i dati per l'email
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE orders_order
                    SET status = 'authorized', payment_status = 'authorized',
                        paypal_authorization_id = %s, updated = NOW()
                    WHERE id = %s
                """, (auth_id, order_id))
                
                cur.execute("""
                    SELECT email, first_name, last_name, order_number, total, 
                           address, postal_code, city, province 
                    FROM orders_order WHERE id = %s
                """, (order_id,))
                order_info = cur.fetchone()
                
                cur.execute("SELECT product_name, quantity, price FROM orders_orderitem WHERE order_id = %s", (order_id,))
                items = cur.fetchall()
                
            conn.commit()

            # ---> INVIO EMAIL DI CONFERMA (solo ora che è authorized) <---
            if order_info:
                subject, body = send_order_confirmation_email(order_info, items)
                background_tasks.add_task(send_email_smtp, order_info['email'], subject, body)

            return {
                "order_id": order_id, "status": "authorized",
                "payment_status": "authorized", "authorized": True,
                "paypal_authorization_id": auth_id,
            }

        return {
            "order_id": order_id, "status": order["status"],
            "payment_status": order["payment_status"],
            "paypal_status": pp_status, "authorized": False,
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")
    finally:
        conn.close()

class AdminOrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    price: float
    quantity: int
    total: float


class AdminOrderResponse(BaseModel):
    id: int
    order_number: str
    status: str
    payment_status: str
    payment_method: str
    total: float
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    postal_code: str
    city: str
    province: str
    country: str
    created: str
    paid_at: Optional[str] = None
    items: list[AdminOrderItemResponse]

@app.get("/api/v1/admin/orders", response_model=list[AdminOrderResponse])
def admin_list_orders(
    status: Optional[str] = Query(default="authorized"),
    current_user: dict = Depends(get_current_admin),
):
    """Lista ordini per l'admin, filtrati per stato (default: authorized)."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, order_number, status, payment_status, payment_method,
                       total, first_name, last_name, email, phone,
                       address, postal_code, city, province, country,
                       created, paid_at
                FROM orders_order
                WHERE status = %s
                ORDER BY created DESC
            """, (status,))
            orders = cur.fetchall()

            result = []
            for order in orders:
                cur.execute("""
                    SELECT id, product_id, product_name, price, quantity
                    FROM orders_orderitem
                    WHERE order_id = %s
                """, (order["id"],))
                items = cur.fetchall()

                result.append({
                    "id": order["id"],
                    "order_number": order["order_number"],
                    "status": order["status"],
                    "payment_status": order["payment_status"],
                    "payment_method": order["payment_method"],
                    "total": float(order["total"]),
                    "first_name": order["first_name"],
                    "last_name": order["last_name"],
                    "email": order["email"],
                    "phone": order["phone"],
                    "address": order["address"],
                    "postal_code": order["postal_code"],
                    "city": order["city"],
                    "province": order["province"],
                    "country": order["country"],
                    "created": order["created"].isoformat(),
                    "paid_at": order["paid_at"].isoformat() if order["paid_at"] else None,
                    "items": [
                        {
                            "id": i["id"],
                            "product_id": i["product_id"],
                            "product_name": i["product_name"],
                            "price": float(i["price"]),
                            "quantity": i["quantity"],
                            "total": float(i["price"]) * i["quantity"],
                        }
                        for i in items
                    ],
                })
            return result
    finally:
        conn.close()


@app.post("/api/v1/admin/orders/{order_id}/ship")
def admin_ship_order(
    order_id: int,
    data: AdminShipRequest,              # <-- NUOVO PARAMETRO
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_admin),
):
    """Cattura il pagamento PayPal e marca l'ordine come spedito con tracking."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 1. Recupera l'ordine e verifica lo stato
            cur.execute("""
                SELECT id, status, payment_status, paypal_authorization_id,
                       first_name, last_name, email, order_number
                FROM orders_order WHERE id = %s
            """, (order_id,))
            order = cur.fetchone()
            
            if not order:
                raise HTTPException(status_code=404, detail="Ordine non trovato")
            if order["status"] != "authorized":
                raise HTTPException(
                    status_code=400,
                    detail=f"Ordine in stato '{order['status']}', non 'authorized'"
                )
            if not order["paypal_authorization_id"]:
                raise HTTPException(
                    status_code=400,
                    detail="Ordine senza paypal_authorization_id"
                )
            auth_id = order["paypal_authorization_id"]

            # Dati per l'email da usare dopo
            customer_email = order["email"]
            customer_name = order["first_name"]
            order_num = order["order_number"]

        # 2. Cattura il pagamento su PayPal
        capture_id, error = paypal_service.capture_authorization(auth_id)
        if error:
            raise HTTPException(status_code=500, detail=f"Errore capture: {error}")

        # 3. Aggiorna l'ordine nel database (con il tracking number)
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE orders_order
                SET status = 'shipped',
                    payment_status = 'captured',
                    paypal_capture_id = %s,
                    tracking_number = %s,              -- <-- AGGIUNTO
                    paid_at = NOW(),
                    shipped_at = NOW(),
                    updated = NOW()
                WHERE id = %s
            """, (capture_id, data.tracking_number, order_id)) # <-- Passiamo il tracking
            
        conn.commit() # <-- Commit prima di inviare l'email

        # 4. Invia l'email di spedizione in background (con tracking se presente)
        tracking_text = f"\nCodice di tracciamento: {data.tracking_number}\n" if data.tracking_number else ""
        
        subject = f"Il tuo ordine #{order_num} è stato spedito! - InCantoPipe"
        body = f"""Gentile {customer_name},

La tua pipa è stata spedita! 
{tracking_text}
Grazie per aver scelto InCantoPipe.
"""
        background_tasks.add_task(send_email_smtp, customer_email, subject, body)

        return {
            "success": True,
            "order_id": order_id,
            "status": "shipped",
            "paypal_capture_id": capture_id,
            "tracking_number": data.tracking_number, # <-- Restituiamo il tracking
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")
    finally:
        conn.close()


@app.post("/api/v1/admin/orders/{order_id}/cancel")
def admin_cancel_order(
    order_id: int,
    current_user: dict = Depends(get_current_admin),
):
    """Annulla l'ordine: void PayPal, ripristina stock, marca cancelled."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, status, payment_status, paypal_authorization_id
                FROM orders_order WHERE id = %s
            """, (order_id,))
            order = cur.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="Ordine non trovato")
            if order["status"] not in ("authorized", "pending"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Ordine in stato '{order['status']}', non annullabile"
                )

            # 1. Se c'è un'autorizzazione PayPal, annullala
            if order["paypal_authorization_id"]:
                success, error = paypal_service.void_authorization(
                    order["paypal_authorization_id"]
                )
                if not success:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Errore void PayPal: {error}"
                    )

            # 2. Ripristina lo stock
            cur.execute("""
                SELECT product_id, quantity FROM orders_orderitem
                WHERE order_id = %s
            """, (order_id,))
            items = cur.fetchall()
            for item in items:
                cur.execute("""
                    UPDATE store_product
                    SET stock = stock + %s, available = TRUE
                    WHERE id = %s
                """, (item["quantity"], item["product_id"]))

            # 3. Aggiorna l'ordine
            cur.execute("""
                UPDATE orders_order
                SET status = 'cancelled',
                    payment_status = 'voided',
                    updated = NOW()
                WHERE id = %s
            """, (order_id,))
        conn.commit()

        return {
            "success": True,
            "order_id": order_id,
            "status": "cancelled",
            "payment_status": "voided",
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")
    finally:
        conn.close()


@app.get("/api/v1/payment/paypal/config")
def paypal_config():
    """Restituisce la configurazione PayPal per il frontend."""
    from config import PAYPAL_CLIENT_ID, PAYPAL_MODE
    return {
        "client_id": PAYPAL_CLIENT_ID,
        "mode": PAYPAL_MODE,
    }


@app.get("/api/v1/payment/paypal/client-token")
def paypal_client_token():
    """Genera un browser-safe client token per il JS SDK di PayPal."""
    import requests as req
    from config import PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_API_URL

    url = f"{PAYPAL_API_URL}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
    }
    data = {
        "grant_type": "client_credentials",
        "response_type": "client_token",
        "intent": "sdk_init",
    }

    try:
        response = req.post(
            url,
            headers=headers,
            data=data,
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Errore client token PayPal: {response.text}"
            )

        token_data = response.json()
        return {"client_token": token_data["access_token"]}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")


class PayPalCardOrderRequest(BaseModel):
    order_id: int


@app.post("/api/v1/payment/paypal/card-order")
def paypal_card_order(
    data: PayPalCardOrderRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Crea un ordine PayPal con intent=AUTHORIZE per il pagamento con carta.
    Restituisce il paypal_order_id per inizializzare i Card Fields.
    """
    user_id = current_user["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, order_number, total, status, payment_status, user_id
                FROM orders_order
                WHERE id = %s AND user_id = %s
            """, (data.order_id, user_id))
            order = cur.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="Ordine non trovato")
            if order["status"] != "pending":
                raise HTTPException(
                    status_code=400,
                    detail=f"Ordine in stato '{order['status']}', non 'pending'"
                )

            return_url = f"https://incantopipe.it/api/v1/payment/paypal/card-success?order_id={order['id']}"
            cancel_url = f"https://incantopipe.it/payment/card-cancel?order_id={order['id']}"

            # Crea ordine PayPal con intent=AUTHORIZE
            paypal_id, error = paypal_service.create_order(
                order, return_url, cancel_url,
                payment_source={
                    "card": {
                        "attributes": {
                            "verification": {
                                "method": "SCA_ALWAYS"
                            }
                        },
                        "experience_context": {
                            "return_url": return_url,
                            "cancel_url": cancel_url,
                            "shipping_preference": "NO_SHIPPING",
                        }
                    }
                }
            )
            if error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Errore PayPal: {error}"
                )

            # Salva il paypal_order_id
            cur.execute("""
                UPDATE orders_order
                SET paypal_transaction_id = %s, updated = NOW()
                WHERE id = %s
            """, (paypal_id, order["id"]))

        conn.commit()
        return {
            "paypal_order_id": paypal_id,
            "order_id": order["id"],
            "amount": float(order["total"]),
            "currency": "EUR",
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")
    finally:
        conn.close()


@app.get("/api/v1/payment/paypal/card-success")
def paypal_card_success(
    background_tasks: BackgroundTasks,
    order_id: int = Query(...),
):
    """Riceve il redirect dopo il pagamento con carta e autorizza."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, paypal_transaction_id, status, payment_status
                FROM orders_order WHERE id = %s
            """, (order_id,))
            order = cur.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="Ordine non trovato")
            
            if order["payment_status"] == "authorized":
                return {"success": True, "order_id": order_id, "status": "authorized"}
            
            if not order["paypal_transaction_id"]:
                raise HTTPException(status_code=400, detail="Ordine senza paypal_order_id")
            
            paypal_order_id = order["paypal_transaction_id"]

        # 1. Autorizza
        auth_id, error = paypal_service.authorize_order(paypal_order_id)
        if error:
            raise HTTPException(status_code=500, detail=f"Errore authorize: {error}")

        # 2. Aggiorna l'ordine e recupera i dati per l'email
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE orders_order
                SET status = 'authorized', payment_status = 'authorized',
                    paypal_authorization_id = %s, updated = NOW()
                WHERE id = %s
            """, (auth_id, order_id))
            
            cur.execute("""
                SELECT email, first_name, last_name, order_number, total, 
                       address, postal_code, city, province 
                FROM orders_order WHERE id = %s
            """, (order_id,))
            order_info = cur.fetchone()
            
            cur.execute("SELECT product_name, quantity, price FROM orders_orderitem WHERE order_id = %s", (order_id,))
            items = cur.fetchall()
            
        conn.commit()

        # ---> INVIO EMAIL DI CONFERMA (solo ora che è authorized) <---
        if order_info:
            subject, body = send_order_confirmation_email(order_info, items)
            background_tasks.add_task(send_email_smtp, order_info['email'], subject, body)

        return {
            "success": True, "order_id": order_id,
            "status": "authorized", "paypal_authorization_id": auth_id,
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")
    finally:
        conn.close()


from fastapi.responses import HTMLResponse

@app.get("/api/v1/payment/paypal/card-page", response_class=HTMLResponse)
def paypal_card_page(order_id: int = Query(...)):
    """Serve la pagina HTML con i campi carta PayPal."""
    from card_page_html import CARD_CHECKOUT_HTML
    from config import PAYPAL_CLIENT_ID

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, paypal_transaction_id, total
                FROM orders_order WHERE id = %s
            """, (order_id,))
            order = cur.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="Ordine non trovato")
            if not order["paypal_transaction_id"]:
                raise HTTPException(status_code=400, detail="Ordine senza paypal_order_id")
    finally:
        conn.close()

    html = CARD_CHECKOUT_HTML
    html = html.replace("__CLIENT_ID__", PAYPAL_CLIENT_ID)
    html = html.replace("__PAYPAL_ORDER_ID__", order["paypal_transaction_id"])
    html = html.replace("__AMOUNT__", f"{float(order['total']):.2f}")
    html = html.replace(
        "__RETURN_URL__",
        f"https://incantopipe.it/api/v1/payment/paypal/card-success?order_id={order_id}"
    )
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host=API_HOST, port=API_PORT)
