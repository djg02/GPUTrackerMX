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
    # strip regional suffix
    sku = re.sub(r'-ROW$', '', sku)
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

def find_duplicate_product(row):
    cursor.execute("""
        SELECT productid
        FROM product
        WHERE producttype = 'GPU'
        AND manufacturer_normalized = %s
        AND model_normalized = %s
        AND COALESCE(vramgb, -1) = COALESCE(%s, -1)
        AND COALESCE(memorytype, '') = COALESCE(%s, '')
        AND COALESCE(coolervariant_normalized, '') = COALESCE(%s, '')
        AND COALESCE(oc, FALSE) = COALESCE(%s, FALSE)
        AND COALESCE(color, '') = COALESCE(%s, '')
    """, (
        row["manufacturer_normalized"],
        row["gpumodel_normalized"],
        row["vramgb"],
        row["memorytype"],
        row["coolervariant_normalized"],
        row["oc"],
        row["color"]
    ))
    return cursor.fetchall()

def get_unprocessed_digitalife():
    cursor.execute("""
        SELECT lp.*
        FROM listing_parsed lp
        JOIN listing l
            ON lp.listingid = l.listingid
        WHERE l.storeid = 3
        AND lp.sku IS NOT NULL
        AND trim(lp.sku) <> ''
        AND lp.product_normalized = TRUE
        AND lp.product_matched = FALSE
        AND lp.manufacturer_normalized IS NOT NULL
        AND lp.gpumodel_normalized IS NOT NULL
        AND lp.coolervariant_normalized IS NOT NULL
        AND lp.vramgb IS NOT NULL;
    """)
    return cursor.fetchall()

def create_products(rows):
    created = 0
    sku_matched = 0
    spec_matched = 0
    ambiguous = 0

    for row in rows:
        try:
            sku = row["sku"]
            normalizedsku = normalize_sku(sku)

            # 1. SKU check
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
                        productid, listingid, matchmethod, confidence
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (listingid) DO NOTHING
                """, (product_id, row["listingid"], "sku", 100.0))

                cursor.execute("""
                    UPDATE listing_parsed
                    SET product_normalized = TRUE, product_matched = TRUE
                    WHERE listingid = %s
                """, (row["listingid"],))

                conn.commit()
                sku_matched += 1
                print(f"[yellow]SKU matched listing {row['listingid']} → product {product_id}[/yellow]")
                continue

            # 2. Spec+color duplicate check
            duplicates = find_duplicate_product(row)

            if len(duplicates) == 1:
                product_id = duplicates[0]["productid"]

                cursor.execute("""
                    INSERT INTO product_sku (productid, sku, normalizedsku)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (product_id, sku, normalizedsku))

                cursor.execute("""
                    INSERT INTO product_listing_match (
                        productid, listingid, matchmethod, confidence
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (listingid) DO NOTHING
                """, (product_id, row["listingid"], "sku", 100.0))

                cursor.execute("""
                    UPDATE listing_parsed
                    SET product_normalized = TRUE, product_matched = TRUE
                    WHERE listingid = %s
                """, (row["listingid"],))

                conn.commit()
                spec_matched += 1
                print(f"[cyan]Spec+color dedup listing {row['listingid']} → existing product {product_id}[/cyan]")
                continue

            if len(duplicates) > 1:
                ambiguous += 1
                print(f"[yellow]Ambiguous dedup listing {row['listingid']} — {len(duplicates)} products found, skipping[/yellow]")
                for p in duplicates:
                    print(f"  → product {p['productid']}")
                continue

            # 3. No duplicate found — create new product
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
                    producttype, canonicalname, brand, model, model_normalized,
                    coolervariant, coolervariant_normalized, manufacturer, manufacturer_normalized,
                    series, oc, vramgb, memorytype, buswidth, interfaceversion,
                    color, fans, boostclock, baseclock, source, createdat
                )
                VALUES (
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,NOW()
                )
                RETURNING productid
            """, (
                "GPU", canonicalname,
                row["chipset_brand"], row["gpumodel"], row["gpumodel_normalized"],
                row["coolervariant"], row["coolervariant_normalized"],
                row["manufacturer"], row["manufacturer_normalized"],
                None,  # series not available from Digitalife
                row["oc"], row["vramgb"], row["memorytype"],
                row["buswidth"], row["interfaceversion"], row["color"],
                row["fans"], row["boostclock"], row["baseclock"],
                "digitalife"
            ))

            product_id = cursor.fetchone()["productid"]

            cursor.execute("""
                INSERT INTO product_sku (productid, sku, normalizedsku)
                VALUES (%s, %s, %s)
            """, (product_id, sku, normalizedsku))

            cursor.execute("""
                INSERT INTO product_listing_match (
                    productid, listingid, matchmethod, confidence
                )
                VALUES (%s, %s, %s, %s)
            """, (product_id, row["listingid"], "digitalife_source", 100.0))

            cursor.execute("""
                UPDATE listing_parsed
                SET product_normalized = TRUE, product_matched = TRUE
                WHERE listingid = %s
            """, (row["listingid"],))

            conn.commit()
            created += 1
            print(f"[green]Created product {product_id}[/green] {canonicalname}")

        except Exception as e:
            conn.rollback()
            print(f"[red]Failed SKU {row['sku']}[/red] {e}")

    print(f"\n[green]Created:[/green] {created}")
    print(f"[yellow]SKU matched:[/yellow] {sku_matched}")
    print(f"[cyan]Spec+color dedup:[/cyan] {spec_matched}")
    print(f"[yellow]Ambiguous dedup:[/yellow] {ambiguous}")

if __name__ == "__main__":
    rows = get_unprocessed_digitalife()
    print(f"[cyan]Found {len(rows)} unprocessed Digitalife listings[/cyan]")
    create_products(rows)
    cursor.close()
    conn.close()