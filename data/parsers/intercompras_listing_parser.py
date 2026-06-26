from rich import print
from dotenv import load_dotenv
import os
import psycopg
import re
import json
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

KNOWN_MANUFACTURERS = [
    'INNO3D', 'Inno3D', 'PowerColor', 'Power Color', 'ASRock',
    'Gigabyte', 'Sapphire', 'Zotac', 'ZOTAC', 'ASUS', 'MSI',
    'XFX', 'Palit', 'EVGA', 'PNY', 'Nvidia', 'AMD', 'Intel',
]

MANUFACTURER_ALIASES = {
    'asrock': 'ASRock',
    'gigabyte': 'Gigabyte',
    'zotac': 'Zotac',
    'sapphire': 'Sapphire',
    'powercolor': 'PowerColor',
    'power color': 'PowerColor',
    'xfx': 'XFX',
    'msi': 'MSI',
    'asus': 'ASUS',
    'pny': 'PNY',
    'evga': 'EVGA',
    'inno3d': 'Inno3D',
    'palit': 'Palit',
    'amd': 'AMD',
    'nvidia': 'Nvidia',
    'intel': 'Intel',
}

CHIPSET_NAMES = {'nvidia', 'amd', 'intel'}


def parse_manufacturer_from_title(title):
    for mfr in KNOWN_MANUFACTURERS:
        if re.search(r'\b' + re.escape(mfr) + r'\b', title, re.IGNORECASE):
            canonical = MANUFACTURER_ALIASES.get(mfr.lower(), mfr)
            if canonical.lower() not in CHIPSET_NAMES:
                return canonical
    return None


def parse_gpumodel_from_title(title):
    m = re.search(
        r'(?:GeForce\s+)?(?:RTX|GTX|GT)\s+\d{3,4}(?:\s*Ti)?(?:\s+SUPER)?'
        r'|(?:Radeon\s+)?RX\s+\d{4}(?:\s*(?:XTX|XT|GRE))?'
        r'|(?:Arc\s+)?[AB]\d{3,4}\b',
        title, re.IGNORECASE
    )
    return re.sub(r'\s+', ' ', m.group(0)).strip() if m else None


def parse_vram_from_title(title):
    m = re.search(r'(\d+)\s*GB', title, re.IGNORECASE)
    return int(m.group(1)) if m else None


def parse_memtype_from_title(title):
    m = re.search(r'(GDDR\w+|HBM\w*)', title, re.IGNORECASE)
    return m.group(1).upper() if m else None


def parse_buswidth_from_title(title):
    m = re.search(r'(\d+)\s*-?\s*bits?', title, re.IGNORECASE)
    return int(m.group(1)) if m else None


def parse_interfaceversion_from_title(title):
    m = re.search(r'PCI[\s-]?E(?:xpress)?\s*(?:x\d+\s*)?([\d.]+)', title, re.IGNORECASE)
    return m.group(1) if m else None


def parse_coolervariant_from_title(title, manufacturer):
    s = re.sub(r'[®™]', '', title).strip()
    s = re.sub(r'^Tarjeta[s]?\s+de\s+[Vv][íi]?deo\s*', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'^Tarjeta[s]?\s+[Gg]r[áa]fica[s]?\s*', '', s, flags=re.IGNORECASE).strip()

    # Strip promo text
    s = re.sub(r'¡[^!]*!', '', s)
    s = re.sub(r'>>[^<]*<<', '', s)

    # Strip chipset brand
    s = re.sub(r'\b(NVIDIA|AMD|Intel)\b', '', s, flags=re.IGNORECASE).strip()

    # Strip manufacturer
    if manufacturer:
        s = re.sub(r'\b' + re.escape(manufacturer) + r'\b', '', s, flags=re.IGNORECASE).strip()

    # Extract and remove gpumodel
    m = re.search(
        r'(?:GeForce\s+)?(?:RTX|GTX|GT)\s+\d{3,4}(?:\s*Ti)?(?:\s+SUPER)?'
        r'|(?:Radeon\s+)?RX\s+\d{4}(?:\s*(?:XTX|XT|GRE))?'
        r'|(?:Arc\s+)?[AB]\d{3,4}\b',
        s, re.IGNORECASE
    )
    if m:
        s = s[:m.start()] + s[m.end():]

    # Strip specs
    s = re.sub(r'\b\d+\s*GB\b', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\b\d+\s*-?\s*bits?\b', '', s, flags=re.IGNORECASE)
    s = re.sub(r'PCI[\s-]?E(?:xpress)?\s*(?:x\d+\s*)?[\d.]+', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\bGDDR\w+\b|\bHBM\w*\b', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\bHDMI\b|\bDisplayPort\b|\bDisplatPort\b|\bDVI\b|\bVGA\b|\bMini\s+DisplayPort\b', '', s, flags=re.IGNORECASE)

    # Strip bullet separators and pipes
    s = re.sub(r'[·•|]', ' ', s)

    # Strip noise words
    s = re.sub(r'\b(?:Refrigeración|Activa|Ventilador(?:es)?|Rendimiento|Avanzado|Tarjeta|Video|Gama|Baja|Modelo|Interfaz|Memoria|Juegos)\b', '', s, flags=re.IGNORECASE)

    # Strip OC/Edition
    s = re.sub(r'\bOC\b|\bEdition\b|\bOC Edition\b', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\b\d+G\b', '', s)

    # Strip separators and SKU-like fragments
    s = re.sub(r'[-–—·]+', ' ', s)
    s = re.sub(r'[,\.]+', ' ', s)
    s = re.sub(r'Modelo\s+[\d\s]+', '', s, flags=re.IGNORECASE)

    # Final cleanup
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'^[\s,\-]+|[\s,\-]+$', '', s).strip()

    return s if len(s) >= 2 else None


def parse(listingid, rawjson):
    try:
        title = rawjson.get("title", "")

        # Manufacturer — not in rawjson, parse from title
        manufacturer = parse_manufacturer_from_title(title)

        # GPU model — prefer structured, fall back to title
        gpumodel = rawjson.get("gpumodel") or parse_gpumodel_from_title(title)

        # VRAM
        vramgb = rawjson.get("vramgb") or parse_vram_from_title(title)

        # Memory type
        memorytype = rawjson.get("memorytype") or parse_memtype_from_title(title)

        # Bus width
        buswidth = rawjson.get("buswidth") or parse_buswidth_from_title(title)

        # Interface version — strip x8/x16 prefix
        interfaceversion_raw = rawjson.get("interfaceversion")
        if interfaceversion_raw:
            interfaceversion = re.sub(r'^x\d+\s*', '', interfaceversion_raw).strip()
        else:
            interfaceversion = parse_interfaceversion_from_title(title)

        # OC
        oc = bool(re.search(r'\bOC\b', title, re.IGNORECASE))

        # SKU
        sku = rawjson.get("sku")

        # Cooler variant from title
        coolervariant = parse_coolervariant_from_title(title, manufacturer)

        # Chipset brand
        chipset_brand = None
        if gpumodel:
            if re.search(r'GeForce|RTX|GTX|GT\b', gpumodel, re.IGNORECASE):
                chipset_brand = 'NVIDIA'
            elif re.search(r'Radeon|RX\b', gpumodel, re.IGNORECASE):
                chipset_brand = 'AMD'
            elif re.search(r'Arc|[AB]\d{3}', gpumodel, re.IGNORECASE):
                chipset_brand = 'INTEL'

        cursor.execute("""
            INSERT INTO public.listing_parsed (
                listingid, manufacturer, chipset_brand, gpumodel,
                oc, vramgb, memorytype, buswidth, interfaceversion,
                coolervariant, sku, title, parsedat
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, NOW()
            )
            ON CONFLICT (listingid) DO UPDATE SET
                manufacturer = EXCLUDED.manufacturer,
                chipset_brand = EXCLUDED.chipset_brand,
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
            listingid, manufacturer, chipset_brand, gpumodel,
            oc, vramgb, memorytype, buswidth, interfaceversion,
            coolervariant, sku, title
        ))

        cursor.execute("""
            UPDATE public.listing
            SET parsed = true, parsedat = NOW()
            WHERE listingid = %s
        """, (listingid,))

        conn.commit()
        print(f"[green]Parsed:[/green] {title[:80]} → mfr={manufacturer} cooler={coolervariant}")

    except Exception as e:
        conn.rollback()
        print(f"[red]Failed on listingid {listingid}: {e}[/red]")


cursor.execute("""
    SELECT l.listingid, l.rawjson
    FROM listing l
    WHERE l.storeid = 7
    AND (l.parsed = false OR l.parsed IS NULL)
    ORDER BY l.listingid
""")

rows = cursor.fetchall()
print(f"[cyan]Found {len(rows)} unparsed listings[/cyan]")

for row in rows:
    parse(row["listingid"], row["rawjson"])

print(f"[green]Finished parsing {len(rows)} listings[/green]")
cursor.close()
conn.close()