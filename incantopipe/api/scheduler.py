# api/scheduler.py
import psycopg2
from config import DATABASE_URL
from psycopg2.extras import RealDictCursor


def process_reservations():
    """Libera le riserve scadute (carrelli inattivi da più di 24 ore)."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            # Trova carrelli con item e updated_at più vecchio di 24 ore
            cur.execute("""
                SELECT DISTINCT c.id
                FROM cart_cart c
                JOIN cart_cartitem ci ON ci.cart_id = c.id
                WHERE c.updated_at < NOW() - INTERVAL '24 hours'
            """)
            expired_carts = cur.fetchall()

            for cart in expired_carts:
                cart_id = cart["id"]

                # Recupera i prodotti da liberare
                cur.execute("""
                    SELECT product_id FROM cart_cartitem WHERE cart_id = %s
                """, (cart_id,))
                products = cur.fetchall()

                # Ripristina lo stock per ogni prodotto
                for p in products:
                    cur.execute("""
                        UPDATE store_product 
                        SET stock = 1, available = TRUE 
                        WHERE id = %s
                    """, (p["product_id"],))

                # Svuota il carrello
                cur.execute("DELETE FROM cart_cartitem WHERE cart_id = %s", (cart_id,))

            conn.commit()
            print(f"[{len(expired_carts)}] carrelli scaduti processati")
    finally:
        conn.close()