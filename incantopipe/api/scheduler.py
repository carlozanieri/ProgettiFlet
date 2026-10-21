# api/scheduler.py
import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def cancel_expired_pending_orders():
    """Annulla gli ordini pending più vecchi di 24 ore e ripristina lo stock."""
    logger.info("Avvio controllo ordini pending scaduti...")
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Trova gli ordini pending creati da più di 24 ore
            cur.execute("""
                SELECT id, order_number 
                FROM orders_order 
                WHERE status = 'pending' 
                  AND created < NOW() - INTERVAL '24 hours'
            """)
            expired_orders = cur.fetchall()

            if not expired_orders:
                logger.info("Nessun ordine pending scaduto trovato.")
                return

            for order in expired_orders:
                order_id = order["id"]
                order_number = order["order_number"]
                
                # Trova gli articoli dell'ordine
                cur.execute("SELECT product_id, quantity FROM orders_orderitem WHERE order_id = %s", (order_id,))
                items = cur.fetchall()

                # Ripristina lo stock
                for item in items:
                    cur.execute("""
                        UPDATE store_product 
                        SET stock = stock + %s, available = TRUE 
                        WHERE id = %s
                    """, (item["quantity"], item["product_id"]))

                # Aggiorna lo stato dell'ordine
                cur.execute("""
                    UPDATE orders_order 
                    SET status = 'cancelled', payment_status = 'failed', updated = NOW()
                    WHERE id = %s
                """, (order_id,))
                
                logger.info(f"Ordine {order_number} annullato. Stock ripristinato.")

        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Errore durante l'annullamento degli ordini scaduti: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("=== Avvio Scheduler InCantoPipe ===")
    cancel_expired_pending_orders()
    logger.info("=== Scheduler terminato ===")