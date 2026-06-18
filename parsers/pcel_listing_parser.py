from rich import print
from dotenv import load_dotenv
import json
import os
import psycopg
import re
load_dotenv()


def parse_specs(specs):
    vramgb = None
    memorytype = None
    buswidth = None
    interfaceversion = None

    for spec in specs:
        # "16GB GDDR7", "8GB GDDR6X"
        m = re.search(r'(\d+)\s*GB\s*(GDDR\w+|HBM\w*)', spec, re.IGNORECASE)
        if m and not vramgb:
            vramgb = int(m.group(1))
            memorytype = m.group(2).upper()

        # "128-bit", "96 Bit", "256 Bit"
        m = re.search(r'(\d+)\s*-?\s*bits?', spec, re.IGNORECASE)
        if m and not buswidth:
            buswidth = int(m.group(1))

        # "PCI Express 4.0", "PCI Express x16 5.0", "PCI Express x16 4.0. BULK"
        m = re.search(r'PCI\s*Express\s*(?:x\d+\s*)?([\d.]+)', spec, re.IGNORECASE)
        if m and not interfaceversion:
            interfaceversion = m.group(1).rstrip('.')

    return vramgb, memorytype, buswidth, interfaceversion

def parse_title(title, manufacturer):
    s = re.sub(r'[®™]', '', title).strip()

    # Strip leading labels
    s = re.sub(r'^Tarjeta[s]?\s+de\s+[Vv]ideo\s*', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'^Tarjeta[s]?\s+[Gg]r[aá]fica[s]?\s*', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'^TJ\s+[Vv]ideo\s*', '', s, flags=re.IGNORECASE).strip()

    # Strip parenthesized SKU codes like "(ZT-B50620F-10M)"
    s = re.sub(r'\([^)]+\)', '', s).strip()

    # Strip chipset brand
    s = re.sub(r'\b(NVIDIA|AMD|Intel)\b', '', s, flags=re.IGNORECASE).strip()

    # Strip manufacturer
    if manufacturer:
        s = re.sub(r'\b' + re.escape(manufacturer) + r'\b', '', s, flags=re.IGNORECASE).strip()

    # Extract gpumodel
    gpumodel = None
    m = re.search(
        r'(?:GeForce\s+)?(?:RTX|GTX|GT)\s+\d{3,4}(?:\s*Ti)?(?:\s+SUPER)?'
        r'|(?:Radeon\s+)?RX\s+\d{4}(?:\s*(?:XTX|XT|GRE))?'
        r'|QUADRO\s+RTX\s+\d{4}'
        r'|(?:Arc\s+)?[AB]\d{3,4}\b',
        s, re.IGNORECASE
    )
    if m:
        gpumodel = re.sub(r'\s+', ' ', m.group(0)).strip()
        s = s[:m.start()] + s[m.end():]
    
    # Catch Low Profile shorthand
    s = re.sub(r'\bLP\b', 'Low Profile', s, flags=re.IGNORECASE)

    # Clean up what's left for coolervariant
    s = re.sub(r'\bOC\b|\bEdition\b', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\b\d+G\b', '', s).strip()  # "16G", "12G" capacity suffixes
    s = re.sub(r'^[\s,\-]+|[\s,\-]+$', '', s).strip()
    s = re.sub(r'\s+', ' ', s).strip()

    coolervariant = s if len(s) >= 2 else None

    return gpumodel, coolervariant

def parse(listingid, jsondata):
    try:
        specs = jsondata["specs"]
        title = jsondata["title"]
        manufacturer = jsondata["mfr_name"]
        sku = jsondata.get("model")

        # Parse specs array
        vramgb, memorytype, buswidth, interfaceversion = parse_specs(specs)

        # Parse title for gpumodel and coolervariant
        gpumodel, coolervariant = parse_title(title, manufacturer)

        # OC from title
        oc = bool(re.search(r'\bOC\b', title, re.IGNORECASE))

        cursor.execute("""
            INSERT INTO public.listing_parsed (
                listingid, manufacturer, gpumodel,
                oc, vramgb, memorytype, buswidth, interfaceversion,
                coolervariant, sku, title, parsedat
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, NOW()
            )
            ON CONFLICT (listingid) DO UPDATE SET
                manufacturer = EXCLUDED.manufacturer,
                gpumodel = EXCLUDED.gpumodel,
                oc = EXCLUDED.oc,
                vramgb = EXCLUDED.vramgb,
                memorytype = EXCLUDED.memorytype,
                buswidth = EXCLUDED.buswidth,
                interfaceversion = EXCLUDED.interfaceversion,
                coolervariant = EXCLUDED.coolervariant,
                sku = EXCLUDED.sku,
                title = EXCLUDED.title,
                parsedat = NOW()
        """, (
            listingid, manufacturer, gpumodel,
            oc, vramgb, memorytype, buswidth, interfaceversion,
            coolervariant, sku, title
        ))

        cursor.execute("""
            UPDATE public.listing
            SET parsed = true, parsedat = NOW()
            WHERE listingid = %s
        """, (listingid,))

        conn.commit()
        print(f"[green]Parsed:[/green] {title} → gpumodel={gpumodel} cooler={coolervariant}")

    except Exception as e:
        conn.rollback()
        print(f"[red]Failed on listingid {listingid}: {e}[/red]")


conn = psycopg.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
)
cursor = conn.cursor()

cursor.execute("""
    SELECT listingid, rawjson
    FROM listing
    WHERE storeid = 4
    AND (parsed = false OR parsed IS NULL)
    ORDER BY listingid
""")

rows = cursor.fetchall()
for row in rows:
    id = row[0]
    jsondata = row[1]
    parse(id, jsondata)

print(f"[green]Finished parsing {len(rows)} listings[/green]")
cursor.close()
conn.close()
