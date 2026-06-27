import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

STORE_IDS = [1, 2, 3, 4, 5, 6, 7]

conn = psycopg.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
)

with conn.cursor() as cur:
    for store_id in STORE_IDS:
        cur.execute("""
            UPDATE listing
            SET availabilitystatus = 'out_of_stock',
                updatedat = NOW()
            WHERE storeid = %s
              AND lastseenat < NOW() - INTERVAL '24 hours'
              AND availabilitystatus != 'out_of_stock'
        """, (store_id,))
        print(f"Store {store_id}: {cur.rowcount} listings marked out of stock")

conn.commit()
conn.close()