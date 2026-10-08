# api/scheduler.py
"""Scheduler per gestione riserve: reminder email e cleanup."""
import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import DATABASE_URL
from psycopg2.extras import RealDictCursor


# ==========================
# CONFIGURAZIONE EMAIL
# ==========================

# Per ora, modalità console (stampa le email a video)
# In futuro, sostituisci con SMTP reale
EMAIL_MODE = "console"  # "console" o "smtp"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = ""
SMTP_PASSWORD = ""
EMAIL_FROM = "noreply@incantopipe.it"


# ==========================
# CONNESSIONE
# ==========================

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


# ==========================
# INVIO EMAIL
# ==========================

def send_email(to_email: str, subject: str, body: str):
    """Invia email (console o SMTP)."""
    if EMAIL_MODE == "console":
        print("\n" + "=" * 60)
        print(f"📧 EMAIL a: {to_email}")
        print(f"   Oggetto: {subject}")
        print("-" * 60)
        print(body)
        print("=" * 60 + "\n")
        return

    # Modalità SMTP
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"✅ Email inviata a {to_email}")
    except Exception as e:
        print(f"❌ Errore invio email a {to_email}: {e}")


# ==========================
# REMINDER (24-28 ore)
# ==========================

def send_reminder_emails():
    """Invia email di reminder ai carrelli inattivi da 24-28 ore."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    c.id AS cart_id,
                    c.updated_at,
                    u.email,
                    u.first_name,
                    u.username
                FROM cart_cart c
                JOIN auth_user u ON c.user_id = u.id
                JOIN cart_cartitem ci ON ci.cart_id = c.id
                WHERE c.user_id IS NOT NULL
                  AND c.updated_at <= NOW() - INTERVAL '24 hours'
                  AND c.updated_at > NOW() - INTERVAL '28 hours'
                  AND (c.reminder_sent IS NULL OR c.reminder_sent = FALSE)
                GROUP BY c.id, c.updated_at, u.email, u.first_name, u.username
            """)
            carts = cur.fetchall()

            for cart in carts:
                # Recupera gli articoli del carrello
                cur.execute("""
                    SELECT p.name, p.price
                    FROM cart_cartitem ci
                    JOIN store_product p ON ci.product_id = p.id
                    WHERE ci.cart_id = %s
                """, (cart["cart_id"],))
                items = cur.fetchall()

                # Costruisci il corpo dell'email
                items_list = "\n".join(
                    f"  - {i['name']} (€ {i['price']})" for i in items
                )

                body = f"""Gentile {cart['first_name'] or cart['username']},

ti ricordiamo che hai ancora nel carrello su InCantoPipe:

{items_list}

Le nostre pipe sono pezzi unici: per garantirti la disponibilità,
la tua riserva scadrà tra poche ore. Se non completerai l'acquisto
entro le prossime 4 ore, l'articolo tornerà disponibile per altri
appassionati.

Per confermare il tuo ordine, accedi a InCantoPipe:

  https://incantopipe.it

Grazie per il tuo interesse!

Il team di InCantoPipe
"""

                send_email(
                    to_email=cart["email"],
                    subject="La tua pipe è ancora in attesa - InCantoPipe",
                    body=body,
                )

                # Marca il reminder come inviato
                cur.execute("""
                    UPDATE cart_cart SET reminder_sent = TRUE WHERE id = %s
                """, (cart["cart_id"],))

            conn.commit()
            print(f"[REMINDER] {len(carts)} email inviate")
    except Exception as e:
        conn.rollback()
        print(f"[REMINDER] Errore: {e}")
    finally:
        conn.close()


# ==========================
# CLEANUP (>28 ore)
# ==========================

def process_expired_reservations():
    """Libera le riserve scadute (carrelli inattivi da più di 28 ore)."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Trova carrelli scaduti
            cur.execute("""
                SELECT DISTINCT c.id AS cart_id
                FROM cart_cart c
                JOIN cart_cartitem ci ON ci.cart_id = c.id
                WHERE c.updated_at <= NOW() - INTERVAL '28 hours'
            """)
            expired_carts = cur.fetchall()

            for cart in expired_carts:
                cart_id = cart["cart_id"]

                # Trova i prodotti da liberare
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

                # Reset del carrello (pronto per nuovo uso)
                cur.execute("""
                    UPDATE cart_cart
                    SET updated_at = NOW(), reminder_sent = FALSE
                    WHERE id = %s
                """, (cart_id,))

            conn.commit()
            print(f"[CLEANUP] {len(expired_carts)} carrelli scaduti processati")
    except Exception as e:
        conn.rollback()
        print(f"[CLEANUP] Errore: {e}")
    finally:
        conn.close()


# ==========================
# MAIN
# ==========================

if __name__ == "__main__":
    print("=== Scheduler InCantoPipe ===")
    send_reminder_emails()
    process_expired_reservations()
    print("=== Fine ===")