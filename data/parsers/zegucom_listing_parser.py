from rich import print
import re
import os
import json
import psycopg
from dotenv import load_dotenv

load_dotenv()

BRANDS = [
    "ASUS", "MSI", "GIGABYTE", "XFX", "SAPPHIRE", "ZOTAC",
    "PNY", "ASROCK", "POWERCOLOR", "EVGA", "INNO3D", "PALIT",
]

VARIANT_HINTS = {
    "ASUS": ["ROG ASTRAL HATSUNE MIKU", "ROG ASTRAL", "ROG STRIX GAMING", "ROG STRIX",
    "TUF GAMING", "PROART", "DUAL", "PRIME"],

    "MSI": ["SUPRIM", "GAMING TRIO", "VENTUS", "SHADOW", "INSPIRE", "VANGUARD", "VENTUS", "TRIO"],

    "GIGABYTE": ["AORUS", "AERO", "EAGLE", "WINDFORCE", "GAMING", "MASTER", "ICE"],

    "XFX": ["MERCURY", "SWIFT", "QUICKSILVER"],
    "POWERCOLOR": ["HELLHOUND", "RED DEVIL", "REAPER", "FIGHTER"],
    "ZOTAC": ["AMP", "TWIN EDGE", "TRINITY"],
    "PNY": ["XLR8", "VERTO"],
    "ASROCK": ["PHANTOM GAMING", "STEEL LEGEND"],
    "SAPPHIRE": ["NITRO+", "PULSE", "PURE"],
    "INNO3D": ["TWIN X2", "ICHILL"],
    "EVGA": ["FTW3", "XC3"],
    "PALIT": ["GAMING PRO", "GAMEROCK"],
}

WORKSTATION_PATTERNS = [
    r'RTX\s+PRO\s+\d{4}',
    r'QUADRO\s+RTX\s+\d{4}',
    r'RTX\s+A\d{4}',
    r'QUADRO\s+[PMK]\d{4}',
]

CONSUMER_PATTERNS = [
    r'RTX\s+\d{4}\s+TI',
    r'RTX\s+\d{4}\s+SUPER',
    r'RTX\s+\d{4}',
    r'GTX\s+\d{4}',
    r'RX\s+\d{4}\s+XT',
    r'RX\s+\d{4}',
]

def normalize_title(title: str) -> str:
    if not title:
        return ""

    title = title.upper()
    title = re.sub(r'\s+', ' ', title)

    title = re.sub(r'RX\s*(\d{4})(XTX|XT|GRE)\b', r'RX \1 \2', title)
    title = re.sub(r'RX\s*(\d{4})\b', r'RX \1', title)

    title = re.sub(r'RTX\s*(\d{4})(TI|SUPER)\b', r'RTX \1 \2', title)
    title = re.sub(r'RTX\s*(\d{4})\b', r'RTX \1', title)

    return title


def parse_brand(text):
    for b in BRANDS:
        if b in text:
            return b
    return None


def parse_gpu_vendor(text):
    if any(x in text for x in ["RTX", "GTX", "QUADRO"]):
        return "NVIDIA"
    if "RX" in text or "RADEON" in text:
        return "AMD"
    if "ARC" in text:
        return "INTEL"
    return None


def parse_gpu_model(text):
    text = normalize_title(text)

    for p in WORKSTATION_PATTERNS:
        m = re.search(p, text)
        if m:
            return m.group(0)

    for p in CONSUMER_PATTERNS:
        m = re.search(p, text)
        if m:
            return m.group(0)

    return None


def parse_variant(text, brand):
    if not brand:
        return None

    hints = VARIANT_HINTS.get(brand, [])
    for h in sorted(hints, key=len, reverse=True):
        if h in text:
            return h
    return None


def parse_vram(text):
    m = re.search(r'(\d+)\s*GB|\b(\d+)G\b', text)
    if not m:
        return None
    return int(next(x for x in m.groups() if x))


def parse_memory_type(text):
    m = re.search(r'GDDR\dX?|HBM\d?', text)
    return m.group(0) if m else None


def parse_bus_width(text):
    m = re.search(r'(\d+)\s*(BIT|BITS)', text)
    return int(m.group(1)) if m else None


def parse_oc(text):
    return bool(re.search(r'\bOC\b|OVERCLOCK', text))


def parse_title(data):
    title = data.get("title") or ""
    sku = data.get("sku")
    manufacturer_json = data.get("manufacturer")

    norm = normalize_title(title)

    brand = manufacturer_json or parse_brand(norm)

    return {
        "sku": sku,
        "manufacturer": brand,
        "chipset_brand": parse_gpu_vendor(norm),
        "gpumodel": parse_gpu_model(norm),
        "coolervariant": parse_variant(norm, brand),
        "vramgb": parse_vram(norm),
        "memorytype": parse_memory_type(norm),
        "buswidth": parse_bus_width(norm),
        "oc": parse_oc(norm),
        "title": title,
    }


# DB
conn = psycopg.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
)

cursor = conn.cursor()


def save_parsed(listingid, parsed):
    try:
        cursor.execute("""
            INSERT INTO public.listing_parsed (
                listingid,
                sku,
                manufacturer,
                chipset_brand,
                gpumodel,
                coolervariant,
                vramgb,
                memorytype,
                buswidth,
                oc,
                title,
                parsedat
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
            ON CONFLICT (listingid) DO UPDATE SET
                sku = EXCLUDED.sku,
                manufacturer = EXCLUDED.manufacturer,
                chipset_brand = EXCLUDED.chipset_brand,
                gpumodel = EXCLUDED.gpumodel,
                coolervariant = EXCLUDED.coolervariant,
                vramgb = EXCLUDED.vramgb,
                memorytype = EXCLUDED.memorytype,
                buswidth = EXCLUDED.buswidth,
                oc = EXCLUDED.oc,
                title = EXCLUDED.title,
                parsedat = NOW()
        """, (
            listingid,
            parsed["sku"],
            parsed["manufacturer"],
            parsed["chipset_brand"],
            parsed["gpumodel"],
            parsed["coolervariant"],
            parsed["vramgb"],
            parsed["memorytype"],
            parsed["buswidth"],
            parsed["oc"],
            parsed["title"],
        ))

        cursor.execute("""
            UPDATE public.listing
            SET parsed = true, parsedat = NOW()
            WHERE listingid = %s
        """, (listingid,))

        conn.commit()
        print(f"[green]OK listingid={listingid} sku={parsed['sku']} model={parsed['gpumodel']}[/green]")

    except Exception as e:
        conn.rollback()
        print(f"[red]FAIL listingid={listingid} error={e} parsed={parsed}[/red]")


# MAIN LOOP
cursor.execute("""
    SELECT listingid, rawjson
    FROM listing
    WHERE parsed IS NOT TRUE AND storeid = 6
    ORDER BY listingid
""")

rows = cursor.fetchall()

for listingid, storejson in rows:
    try:
        if isinstance(storejson, str):
            data = json.loads(storejson)
        else:
            data = storejson

        parsed = parse_title(data)
        save_parsed(listingid, parsed)

    except Exception as e:
        print(f"[red]SKIP listingid={listingid} invalid json: {e}[/red]")

conn.close()
print("Done")