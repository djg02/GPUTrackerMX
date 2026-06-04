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

def build_canonical_name(manufacturer, chipset_brand, gpumodel, coolervariant, oc, vramgb, memorytype, color):
    parts = [manufacturer, chipset_brand, gpumodel, coolervariant]
    if oc:
        parts.append("OC")
    if vramgb is not None:
        parts.append(f"{vramgb}GB")
    if memorytype is not None:
        parts.append(memorytype)
    if color is not None:
        parts.append(color)
    return " ".join(str(x).strip() for x in parts if x is not None)

def get_unprocessed_cyberpuerta():
    cursor.execute("""
        SELECT lp.*
        FROM listing_parsed lp
        JOIN listing l
            ON lp.listingid = l.listingid
        WHERE l.storeid = 2
        AND lp.sku IS NOT NULL
        AND trim(lp.sku) <> ''
        AND lp.product_normalized = FALSE;
    """)
    return cursor.fetchall()

def create_products(rows):
    created = 0
    skipped = 0

    for row in rows:
        try:
            sku = row["sku"]
            normalizedsku = normalize_sku(sku)

            cursor.execute("""
                SELECT productid
                FROM product_sku
                WHERE normalizedsku = %s
            """, (normalizedsku,))
            existing = cursor.fetchone()

            if existing:
                product_id = existing["productid"]

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
                    product_id,
                    row["listingid"],
                    "sku",
                    100.0
                ))

                cursor.execute("""
                    UPDATE listing_parsed
                    SET
                        product_normalized = TRUE,
                        product_matched = TRUE
                    WHERE listingid = %s
                """, (
                    row["listingid"],
                ))

                conn.commit()
                skipped += 1
                continue

            canonicalname = build_canonical_name(
                row["manufacturer_normalized"],
                row["chipset_brand"],
                row["gpumodel_normalized"],
                row["coolervariant_normalized"],
                row["oc"],
                row["vramgb"],
                row["memorytype"],
                row["color"]
            )

            cursor.execute("""
                INSERT INTO product (
                    producttype,
                    canonicalname,
                    brand,
                    model,
                    model_normalized,
                    coolervariant,
                    coolervariant_normalized,
                    manufacturer,
                    manufacturer_normalized,
                    series,
                    oc,
                    vramgb,
                    memorytype,
                    buswidth,
                    interfaceversion,
                    color,
                    fans,
                    boostclock,
                    baseclock,
                    createdat
                )
                VALUES (
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,NOW()
                )
                RETURNING productid
            """, (
                "GPU",
                canonicalname,
                row["chipset_brand"],
                row["gpumodel"],
                row["gpumodel_normalized"],
                row["coolervariant"],
                row["coolervariant_normalized"],
                row["manufacturer"],
                row["manufacturer_normalized"],
                row["series"],
                row["oc"],
                row["vramgb"],
                row["memorytype"],
                row["buswidth"],
                row["interfaceversion"],
                row["color"],
                row["fans"],
                row["boostclock"],
                row["baseclock"]
            ))

            product_id = cursor.fetchone()["productid"]

            cursor.execute("""
                INSERT INTO product_sku (
                    productid,
                    sku,
                    normalizedsku
                )
                VALUES (%s,%s,%s)
            """, (
                product_id,
                sku,
                normalizedsku
            ))

            cursor.execute("""
                INSERT INTO product_listing_match (
                    productid,
                    listingid,
                    matchmethod,
                    confidence
                )
                VALUES (%s,%s,%s,%s)
            """, (
                product_id,
                row["listingid"],
                "cyberpuerta_source",
                100.0
            ))

            cursor.execute("""
                UPDATE listing_parsed
                SET
                    product_normalized = TRUE,
                    product_matched = TRUE
                WHERE listingid = %s
            """, (
                row["listingid"],
            ))

            conn.commit()

            created += 1

            print(f"[green]Created Product {product_id}[/green]")
            print(canonicalname)

        except Exception as e:
            conn.rollback()
            print(f"[red]Failed SKU {row['sku']}[/red] {e}")

    print(f"[green]Created:[/green] {created}")
    print(f"[yellow]Matched Existing SKU:[/yellow] {skipped}")

if __name__ == "__main__":

    rows = get_unprocessed_cyberpuerta()

    print(f"[cyan]Found {len(rows)} Unprocessed Cyberpuerta listings[/cyan]")

    create_products(rows)

    cursor.close()
    conn.close()