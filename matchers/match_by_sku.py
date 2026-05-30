from rich import print
from dotenv import load_dotenv
import os
import psycopg
import re
load_dotenv()

conn = psycopg.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
)

conn.row_factory = psycopg.rows.dict_row
cursor = conn.cursor()

def normalize_sku(sku: str) -> str:
    if not sku:
        return None

    sku = sku.upper().strip()
    # remove unicode weird spaces
    sku = re.sub(r'\s+', '', sku)
    # unify separators to single dash
    sku = re.sub(r'[_/\.\s]+', '-', sku)
    # remove non alphanumeric except dash
    sku = re.sub(r'[^A-Z0-9\-]', '', sku)
    # collapse dashes
    sku = re.sub(r'-+', '-', sku)
    return sku.strip('-').lower()

def get_unmatched_listings():
    cursor.execute("""
        SELECT listingid, sku 
        FROM listing_parsed
        WHERE product_matched = FALSE
        AND sku IS NOT NULL
        AND trim(sku) <> '';
    """)
    return cursor.fetchall()

def match_by_sku(rows):
    matched = 0
    not_found = 0

    for row in rows:
        try:
            normalizedsku = normalize_sku(row["sku"])

            cursor.execute("""
                SELECT productid
                FROM product_sku
                WHERE normalizedsku = %s
            """, (normalizedsku,))

            product = cursor.fetchone()

            if not product:
                not_found += 1
                continue

            cursor.execute("""
                INSERT INTO product_listing_match (
                    productid,
                    listingid,
                    matchmethod,
                    confidence
                )
                VALUES (%s,%s,%s,%s)
                ON CONFLICT (listingid) DO NOTHING
            """, (
                product["productid"],
                row["listingid"],
                "sku",
                100.0
            ))

            cursor.execute("""
                UPDATE listing_parsed
                SET product_matched = TRUE
                WHERE listingid = %s
            """, (
                row["listingid"],
            ))

            conn.commit()
            matched += 1

            print(
                f"[green]Matched Listing {row['listingid']} "
                f"→ Product {product['productid']}[/green]"
            )

        except Exception as e:
            conn.rollback()
            print(f"[red]Failed listing {row['listingid']}[/red] {e}")

    print(f"[green]Matched:[/green] {matched}")
    print(f"[yellow]No SKU Match:[/yellow] {not_found}")

if __name__ == "__main__":
    rows = get_unmatched_listings()

    print(f"[cyan]Found {len(rows)} unmatched listings[/cyan]")

    match_by_sku(rows)

    cursor.close()
    conn.close()