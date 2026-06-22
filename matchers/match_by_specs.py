from rich import print
from dotenv import load_dotenv
import os
import psycopg
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


def get_unmatched_listings():
    cursor.execute("""
        SELECT *
        FROM listing_parsed
        WHERE product_matched = FALSE
        AND product_normalized = TRUE
        AND manufacturer_normalized IS NOT NULL
        AND gpumodel_normalized IS NOT NULL
    """)
    return cursor.fetchall()


def find_products(manufacturer_normalized, gpumodel_normalized, vramgb, coolervariant_normalized, oc, color_normalized ):
    params = (
        manufacturer_normalized,
        gpumodel_normalized,
        vramgb,
        coolervariant_normalized,
        oc,
    )

    if color_normalized:
        cursor.execute("""
            SELECT productid
            FROM product
            WHERE producttype = 'GPU'
            AND manufacturer_normalized = %s
            AND model_normalized = %s
            AND COALESCE(vramgb, -1) = COALESCE(%s, -1)
            AND COALESCE(coolervariant_normalized, '') = COALESCE(%s, '')
            AND COALESCE(oc, FALSE) = COALESCE(%s, FALSE)
            AND color = %s
        """, (*params, color_normalized))
    else:
        cursor.execute("""
            SELECT productid
            FROM product
            WHERE producttype = 'GPU'
            AND manufacturer_normalized = %s
            AND model_normalized = %s
            AND COALESCE(vramgb, -1) = COALESCE(%s, -1)
            AND COALESCE(coolervariant_normalized, '') = COALESCE(%s, '')
            AND COALESCE(oc, FALSE) = COALESCE(%s, FALSE)
            AND color IS NULL
        """, params)

    return cursor.fetchall()


def match_by_specs(rows):
    matched = 0
    no_match = 0
    ambiguous = 0

    for row in rows:
        try:
            products = find_products(
                row["manufacturer_normalized"],
                row["gpumodel_normalized"],
                row["vramgb"],
                row["coolervariant_normalized"],
                row["oc"],
                row["color_normalized"]
            )

            if len(products) == 1:
                product_id = products[0]["productid"]

                cursor.execute("""
                   INSERT INTO product_listing_match (
                      productid, listingid, matchmethod, confidence
                      )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (listingid) DO NOTHING
                """, (product_id, row["listingid"], "spec", 85.0))

                cursor.execute("""
                    UPDATE listing_parsed
                    SET product_matched = TRUE
                    WHERE listingid = %s
                """, (row["listingid"],))

                conn.commit()

                matched += 1
                print(f"[green]Matched listing {row['listingid']} → product {product_id}[/green]")

            elif len(products) > 1:
                ambiguous += 1
                print(f"[yellow]Ambiguous listing {row['listingid']} — {len(products)} products found[/yellow]")
                for p in products:
                    print(f"  → product {p['productid']}")

            else:
                no_match += 1
                print(f"[red]No match:[/red] {row['listingid']} {row['manufacturer_normalized']} {row['gpumodel_normalized']} {row['coolervariant_normalized']} {'OC' if row['oc'] else ''} {row['vramgb']}GB")

        except Exception as e:
            conn.rollback()
            print(f"[red]Failed listing {row['listingid']}:[/red] {e}")

    print(f"\n[green]Matched:[/green] {matched}")
    print(f"[yellow]Ambiguous:[/yellow] {ambiguous}")
    print(f"[red]No match:[/red] {no_match}")


if __name__ == "__main__":
    rows = get_unmatched_listings()
    print(f"[cyan]Found {len(rows)} unmatched listings[/cyan]")
    match_by_specs(rows)
    cursor.close()
    conn.close()