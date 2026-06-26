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

def normalize_sku(sku: str) -> str:
    if not sku:
        return None
    sku = sku.upper().strip()
    sku = re.sub(r'\s+', '', sku)
    sku = re.sub(r'[_/\.\s]+', '-', sku)
    sku = re.sub(r'[^A-Z0-9\-]', '', sku)
    sku = re.sub(r'-+', '-', sku)
    sku = re.sub(r'-ROW$', '', sku)
    return sku.strip('-').lower()


def is_junk_sku(sku):
    if not sku:
        return True
    # spec values that leaked into SKU field
    if re.match(r'^\d+-bit$', sku, re.IGNORECASE):
        return True
    return False


def get_eligible_listings():
    cursor.execute("""
        SELECT lp.*, s.storename
        FROM listing_parsed lp
        JOIN listing l ON l.listingid = lp.listingid
        JOIN store s ON s.storeid = l.storeid
        WHERE lp.chipset_brand IS NOT NULL
        AND lp.vramgb IS NOT NULL
        AND lp.memorytype IS NOT NULL
        AND lp.buswidth IS NOT NULL
        AND lp.interfaceversion IS NOT NULL
        AND lp.sku IS NOT NULL
        AND trim(lp.sku) <> ''
        AND lp.product_matched = FALSE
        AND lp.product_normalized = TRUE
        AND lp.gpumodel_normalized IS NOT NULL
        AND lp.coolervariant_normalized IS NOT NULL
        AND lp.manufacturer_normalized IS NOT NULL
        ORDER BY lp.manufacturer_normalized, lp.gpumodel_normalized
    """)
    return cursor.fetchall()


def find_existing_product(row):
    cursor.execute("""
        SELECT productid FROM product
        WHERE producttype = 'GPU'
        AND manufacturer_normalized = %s
        AND model_normalized = %s
        AND COALESCE(vramgb, -1) = COALESCE(%s, -1)
        AND COALESCE(coolervariant_normalized, '') = COALESCE(%s, '')
        AND COALESCE(oc, FALSE) = COALESCE(%s, FALSE)
    """, (
        row["manufacturer_normalized"],
        row["gpumodel_normalized"],
        row["vramgb"],
        row["coolervariant_normalized"],
        row["oc"],
    ))
    return cursor.fetchone()


def create_product(row):
    canonicalname = build_canonical_name(
        row["manufacturer_normalized"],
        row["chipset_brand"],
        row["gpumodel_normalized"],
        row["coolervariant_normalized"],
        row["oc"],
        row["vramgb"],
        row["memorytype"],
        row["color_normalized"]
)
    cursor.execute("""
        INSERT INTO product (
            producttype, canonicalname, brand,
            manufacturer, manufacturer_normalized,
            model, model_normalized,
            coolervariant, coolervariant_normalized,
            vramgb, memorytype, buswidth, interfaceversion,
            oc, color, source, createdat
        ) VALUES (
            'GPU', %s, %s,
            %s, %s,
            %s, %s,
            %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, NOW()
        )
        RETURNING productid
    """, (
        canonicalname,
        row["chipset_brand"],
        row["manufacturer"],
        row["manufacturer_normalized"],
        row["gpumodel"],
        row["gpumodel_normalized"],
        row["coolervariant"],
        row["coolervariant_normalized"],
        row["vramgb"],
        row["memorytype"],
        row["buswidth"],
        row["interfaceversion"],
        row["oc"],
        row["color_normalized"],
        row["storename"]
    ))
    return cursor.fetchone()["productid"]


def register_sku(product_id, sku):
    if not sku:
        return
    normalized = normalize_sku(sku)
    if not normalized:
        return
    cursor.execute("""
        INSERT INTO product_sku (productid, sku, normalizedsku, createdat)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (normalizedsku) DO NOTHING
    """, (product_id, sku, normalized))


def match_listing(product_id, listingid):
    cursor.execute("""
        INSERT INTO product_listing_match (productid, listingid, matchmethod, confidence)
        VALUES (%s, %s, 'product_created', 95.0)
        ON CONFLICT (listingid) DO NOTHING
    """, (product_id, listingid))
    cursor.execute("""
        UPDATE listing_parsed SET product_matched = TRUE WHERE listingid = %s
    """, (listingid,))


def run():
    rows = get_eligible_listings()
    print(f"[cyan]Found {len(rows)} eligible listings[/cyan]")

    created = 0
    reused = 0
    skipped = 0

    for row in rows:
        try:
            if is_junk_sku(row["sku"]):
                print(f"[yellow]Skipping junk SKU:[/yellow] {row['sku']}")
                skipped += 1
                continue

            existing = find_existing_product(row)

            if existing:
                product_id = existing["productid"]
                register_sku(product_id, row["sku"])
                match_listing(product_id, row["listingid"])
                conn.commit()
                reused += 1
                print(f"[blue]Reused product {product_id}:[/blue] {row['manufacturer_normalized']} {row['gpumodel_normalized']} {row['coolervariant_normalized']}")
            else:
                product_id = create_product(row)
                register_sku(product_id, row["sku"])
                match_listing(product_id, row["listingid"])
                conn.commit()
                created += 1
                print(f"[green]Created product {product_id}:[/green] {row['manufacturer_normalized']} {row['gpumodel_normalized']} {row['coolervariant_normalized']}")

        except Exception as e:
            conn.rollback()
            print(f"[red]Failed listing {row['listingid']}:[/red] {e}")

    print(f"\n[green]Created:[/green] {created}")
    print(f"[blue]Reused:[/blue] {reused}")
    print(f"[yellow]Skipped:[/yellow] {skipped}")


if __name__ == "__main__":
    run()
    cursor.close()
    conn.close()