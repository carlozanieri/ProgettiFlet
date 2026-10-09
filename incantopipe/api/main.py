# incantopipe_flet/api/main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from config import DATABASE_URL, API_HOST, API_PORT, MEDIA_ROOT
#from pydantic import BaseModel, EmailStr
#from auth import create_access_token, verify_password, get_current_user
from pydantic import EmailStr
import RegisterResponse
from fastapi import Depends
from auth import (
    verify_password,
    create_access_token,
    get_current_user,
    hash_password,
)
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
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Cerca SOLO carrelli anonimi (user_id IS NULL)
            cur.execute(
                "SELECT id FROM cart_cart WHERE session_key = %s AND user_id IS NULL",
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
@app.get("/api/v1/cart", response_model=CartResponse)
def get_cart(session_key: str = Query(...)):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Cerca SOLO carrelli anonimi
            cur.execute(
                "SELECT id FROM cart_cart WHERE session_key = %s AND user_id IS NULL",
                (session_key,)
            )
            row = cur.fetchone()
            if not row:
                return {"cart_id": 0, "items": [], "total_items": 0, "total_price": 0}
            cart_id = row["id"]
            # ... resto invariato
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
    session_key: str = Query(...),
    data: CartItemAdd = ...,
):
    """Aggiunge un prodotto al carrello e ne blocca la disponibilità."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 1. Verifica disponibilità con lock (evita race condition)
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
                raise HTTPException(status_code=400, detail="Prodotto non più disponibile")

            # 2. Ottieni o crea il carrello
            cart_id = get_or_create_cart(session_key)

            # 3. Verifica se il prodotto è già nel carrello
            cur.execute("""
                SELECT id, quantity FROM cart_cartitem
                WHERE cart_id = %s AND product_id = %s
            """, (cart_id, data.product_id))
            existing = cur.fetchone()

            if existing:
                # Già nel carrello: aggiorna quantità (solo per prodotti non unici)
                cur.execute("""
                    UPDATE cart_cartitem SET quantity = quantity + %s
                    WHERE id = %s
                """, (data.quantity, existing["id"]))
            else:
                # Nuovo item: inserisci
                cur.execute("""
                    INSERT INTO cart_cartitem (cart_id, product_id, quantity, added_at)
                    VALUES (%s, %s, %s, NOW())
                """, (cart_id, data.product_id, data.quantity))

                # 4. Blocca il prodotto (solo per pezzi unici: stock = 1)
                cur.execute("""
                    UPDATE store_product
                    SET stock = 0, available = FALSE
                    WHERE id = %s
                """, (data.product_id,))

            # 5. Reset del timer del carrello
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
    session_key: str = Query(...),
    item_id: int = Query(...),
    data: CartItemUpdate = ...,
):
    """Aggiorna la quantità di un articolo (reset del timer)."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 1. Trova l'item per ottenere il cart_id
            cur.execute("SELECT cart_id FROM cart_cartitem WHERE id = %s", (item_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Articolo non trovato")

            cart_id = row["cart_id"]

            # 2. Se la quantità è <= 0, rimuovi e libera
            if data.quantity <= 0:
                cur.execute("""
                    SELECT product_id FROM cart_cartitem WHERE id = %s
                """, (item_id,))
                item = cur.fetchone()
                if item:
                    cur.execute("""
                        UPDATE store_product
                        SET stock = 1, available = TRUE
                        WHERE id = %s
                    """, (item["product_id"],))
                cur.execute("DELETE FROM cart_cartitem WHERE id = %s", (item_id,))
            else:
                cur.execute("""
                    UPDATE cart_cartitem SET quantity = %s WHERE id = %s
                """, (data.quantity, item_id))

            # 3. Reset del timer
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
    session_key: str = Query(...),
    item_id: int = Query(...),
):
    """Rimuove un articolo dal carrello e ne libera la disponibilità."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 1. Trova l'item e il cart_id
            cur.execute("""
                SELECT product_id, cart_id FROM cart_cartitem
                WHERE id = %s
            """, (item_id,))
            row = cur.fetchone()
            if not row:
                return {"success": True}

            product_id = row["product_id"]
            cart_id = row["cart_id"]

            # 2. Ripristina la disponibilità del prodotto
            cur.execute("""
                UPDATE store_product
                SET stock = 1, available = TRUE
                WHERE id = %s
            """, (product_id,))

            # 3. Elimina l'item
            cur.execute("DELETE FROM cart_cartitem WHERE id = %s", (item_id,))

            # 4. Reset del timer del carrello
            cur.execute("""
                UPDATE cart_cart
                SET updated_at = NOW(), reminder_sent = FALSE
                WHERE id = %s
            """, (cart_id,))

        conn.commit()
        return {"success": True}
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
                "SELECT id, username, email, first_name, last_name "
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


@app.post("/api/v1/cart/associate")
def associate_cart(
    data: CartAssociateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Associa il carrello anonimo all'utente autenticato.

    Se l'utente ha già un carrello, i due vengono uniti.
    """
    user_id = current_user["user_id"]
    session_key = data.session_key

    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 1. Carrello anonimo (session_key)
            cur.execute(
                "SELECT id FROM cart_cart WHERE session_key = %s AND user_id IS NULL",
                (session_key,)
            )
            anon_row = cur.fetchone()
            anon_cart_id = anon_row["id"] if anon_row else None

            # 2. Carrello già associato all'utente
            cur.execute(
                "SELECT id FROM cart_cart WHERE user_id = %s",
                (user_id,)
            )
            user_row = cur.fetchone()
            user_cart_id = user_row["id"] if user_row else None

            # Caso A: solo carrello anonimo → associalo all'utente
            if anon_cart_id and not user_cart_id:
                cur.execute(
                    "UPDATE cart_cart SET user_id = %s, updated_at = NOW() WHERE id = %s",
                    (user_id, anon_cart_id)
                )
                conn.commit()
                return {"success": True, "cart_id": anon_cart_id, "action": "associated"}

            # Caso B: solo carrello utente → niente da fare
            if not anon_cart_id and user_cart_id:
                return {"success": True, "cart_id": user_cart_id, "action": "already_user"}

            # Caso C: nessun carrello → niente da fare
            if not anon_cart_id and not user_cart_id:
                return {"success": True, "cart_id": 0, "action": "no_cart"}

            # Caso D: entrambi esistono → unisci
            if anon_cart_id and user_cart_id and anon_cart_id != user_cart_id:
                # Sposta gli item del carrello anonimo al carrello utente
                # Se lo stesso prodotto è in entrambi, somma le quantità
                cur.execute("""
                    INSERT INTO cart_cartitem (cart_id, product_id, quantity, added_at)
                    SELECT %s, product_id, quantity, NOW()
                    FROM cart_cartitem
                    WHERE cart_id = %s
                """, (user_cart_id, anon_cart_id))

                # Elimina gli item del carrello anonimo
                cur.execute("DELETE FROM cart_cartitem WHERE cart_id = %s", (anon_cart_id,))

                # Elimina il carrello anonimo
                cur.execute("DELETE FROM cart_cart WHERE id = %s", (anon_cart_id,))

                # Aggiorna timestamp del carrello utente
                cur.execute(
                    "UPDATE cart_cart SET updated_at = NOW() WHERE id = %s",
                    (user_cart_id,)
                )

                conn.commit()
                return {"success": True, "cart_id": user_cart_id, "action": "merged"}

            # Caso E: stesso carrello (impossibile ma per sicurezza)
            conn.commit()
            return {"success": True, "cart_id": user_cart_id, "action": "same"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")
    finally:
        conn.close()

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


if __name__ == "__main__":
    import uvicorn
    print(f"🚀 InCantoPipe API su http://localhost:{API_PORT}")
    print(f"📖 Documentazione su http://localhost:{API_PORT}/docs")
    uvicorn.run(app, host=API_HOST, port=API_PORT)
