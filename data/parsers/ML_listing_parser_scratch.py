from rich import print
import re
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

BRANDS = [
    "ASUS", "MSI", "GIGABYTE", "XFX", "SAPPHIRE", "ZOTAC",
    "PNY", "ASROCK", "POWERCOLOR", "EVGA", "INNO3D", "PALIT",
    "NVIDIA",
]

BRAND_ALIASES = {
    "POWER COLOR": "POWERCOLOR",
    "ASTROCK": "ASROCK",
}

VARIANT_HINTS = {
    "ASUS": ["ROG ASTRAL HATSUNE MIKU", "ROG ASTRAL", "ROG STRIX GAMING", "ROG STRIX",
             "ROG MATRIX PLATINUM", "ROG MATRIX", "TUF GAMING", "TUF WHITE",
             "PROART", "DUAL EVO WHITE", "DUAL EVO", "DUAL WHITE", "PRIME", "DUAL", "TUF",
             "TURBO", "PHOENIX"],

    "MSI": ["SUPRIM LIQUID SOC", "SUPRIM LIQUID X", "SUPRIM SOC", "SUPRIM X",
            "GAMING TRIO WHITE", "GAMING TRIO PLUS", "GAMING TRIO", "GAMING X",
            "VENTUS 3X WHITE", "VENTUS 3X PLUS", "VENTUS 3X",
            "VENTUS 2X WHITE PLUS", "VENTUS 2X WHITE", "VENTUS 2X PLUS", "VENTUS 2X XS", "VENTUS 2X",
            "SHADOW 3X", "SHADOW2X", "SHADOW 2X", "INSPIRE 3X PLUS", "INSPIRE 3X", "INSPIRE 2X",
            "VANGUARD SOC", "LIGHTNING Z", "EXPERT OC", "ARMOR", "MECH 2X", "MECH",
            "LOW PROFILE", "VENTUS", "TRIO", "LP", "MLG EDITION", "GAMING"],

    "GIGABYTE": ["AORUS XTREME WATERFORCE", "AORUS WATERFORCE WB", "AORUS WATERFORCE",
                 "AORUS MASTER ICE", "AORUS MASTER", "AORUS ELITE", "EAGLE ICE SFF", "LOW PROFILE",
                 "EAGLE ICE", "EAGLE MAX", "EAGLE SFF", "GAMING ICE", "WINDFORCE", "AI BOX",
                 "AERO", "EAGLE", "GAMING", "MASTER", "ELITE", "XTREME", "ICE", "LP"],

    "XFX": ["MERCURY MAGNETIC AIR", "MERCURY TRIPLE FAN GAMING", "MERCURY GAMING RGB",
            "WHITE GAMING EDITION", "SPEEDSTER SWFT CORE", "SWIFT GAMING", "QUICKSILVER",
            "MERCURY", "SWIFT", "SWFT"],

    "POWERCOLOR": ["HELLHOUND SPECTRAL WHITE", "HELLHOUND", "RED DEVIL", "RED DRAGON",
                   "REAPER", "FIGHTER", "ITX"],
    "ZOTAC": ["AMP EXTREME INFINITY", "AMP EXTREME", "TWIN EDGE", "TRINITY WHITE", "TRINITY",
              "SOLID", "SOLO", "AMP"],
    "PNY": ["XLR8 GAMING VERTO EPIC-X RGB", "EPIC-X RGB", "VERTO", "XLR8",
            "DUAL FAN", "SINGLE FAN", "TRIPLE FAN"],
    "ASROCK": ["PHANTOM GAMING OC", "STEEL LEGEND", "CHALLENGER", "PHANTOM GAMING"],
    "SAPPHIRE": ["NITRO+ GAMING OC", "NITRO+", "PULSE", "PURE"],
    "INNO3D": ["TWIN X2 WHITE", "ICHILL X3", "TWIN X2", "X3"],
    "EVGA": ["FTW3 ULTRA GAMING", "FTW3", "XC3", "XC", "BLACK EDITION", "GAMING", "KO GAMING"],
    "PALIT": ["GAMING PRO", "GAMEROCK", "DUAL"],
    "NVIDIA": ["FOUNDERS EDITION"],
}

VARIANT_REGEX_HINTS = {
    "XFX": [r'SPEEDSTER\s+[A-Z0-9]+'],
    "ASROCK": [r'PHANTOM GAMING\s*[A-Z]?', r'\bPG\s*[A-Z]?\b'],
}

WORKSTATION_PATTERNS = [
    r'RTX\s+PRO\s+\d{4}',
    r'QUADRO\s+RTX\s+\d{4}',
    r'RTX\s+\d{4}\s+ADA',
    r'RTX\s+A\d{4}',
    r'QUADRO\s+P\d{4}',
    r'QUADRO\s+M\d{4}',
    r'QUADRO\s+K\d{4}',
    r'RADEON\s+PRO\s+[A-Z]\d{3,4}',
    r'\bA\d{3,4}\b',
    r'\bT\d{3,4}\b',
]

CONSUMER_PATTERNS = [
    r'RTX\s+\d{4}\s+TI',
    r'RTX\s+\d{4}\s+SUPER',
    r'RTX\s+\d{4}',
    r'GTX\s+\d{4}',

    r'RX\s+\d{4}\s+XTX',
    r'RX\s+\d{4}\s+XT',
    r'RX\s+\d{4}\s+GRE',
    r'RX\s+\d{4}',

    r'ARC\s+[AB]\d{3,4}',
]

SKU_PATTERNS_BY_BRAND = {
    "GIGABYTE": [
        r'\b(?:GIG-)?GV[- ][NR][A-Z0-9]+(?:\s[A-Z0-9]+)*-[A-Z0-9]+\b',
    ],
    "MSI": [
        r'\b912-V\d{3}-\d{3}\b',
        r'\bG\d{4}-\d{2}S\d[A-Z]\b',
        r'\bG\d{3,4}-[A-Z0-9]{4,6}\b',
        r'\b\d{6,7}-\d{2}\b',
    ],
    "XFX": [
        r'\bRX-\d{2}[A-Z0-9]{5,9}\b',
    ],
    "ZOTAC": [
        r'\bZT-[A-Z][0-9]{5}[A-Z0-9]{0,3}-[0-9]{2}[A-Z]\b',
    ],
    "SAPPHIRE": [
        r'\b\d{5}-\d{2}-\d{2}[A-Z]\b',
    ],
    "ASUS": [
        r'\b90YV[A-Z0-9]{4}-[A-Z0-9]{4,6}\b',
        r'\b(?:PRIME|DUAL|TUF|ROG-STRIX|TURBO|GT\d{3,4})-[A-Z0-9]+(?:-[A-Z0-9]+){1,6}\b',
    ],
    "PNY": [
        r'\bVC[A-Z0-9]{6,}(?:-[A-Z0-9]+)?\b',
    ],
    "POWERCOLOR": [
        r'\bRX\s?\d{3,4}[A-Z]{0,3}\s\d{1,2}G-[A-Z](?:/OC)?\b',
        r'\bAXRX\s?[A-Z0-9]+(?:\s[A-Z0-9]+)*[- ][A-Z0-9/]+\b',
    ],
    "INNO3D": [
        r'\bN\d{3}[A-Z0-9]{1,3}-[A-Z0-9]{3,6}-[A-Z0-9]{5,7}\b',
    ],
    "EVGA": [
        r'\b\d{2}G-P\d-\d{4}-[A-Z0-9]+\b',
    ],
    "NVIDIA": [
        r'\b900-[A-Z0-9]+-[A-Z0-9]+-\d+\b',
    ],
    "ASROCK": [
        r'\bRX\d{3,4}[A-Z]*-[A-Z]{2}-[A-Z0-9]+\b',
    ],
}


def _sku_normalize(title):
    title = title.upper()
    title = title.replace("'", "")
    title = re.sub(r'\s+', ' ', title)
    return title


def normalize_title(title):
    title = title.upper()
    title = title.replace("'", "")
    title = title.replace("-", " ")

    for alias, canonical in BRAND_ALIASES.items():
        title = title.replace(alias, canonical)

    title = re.sub(r'RX\s*(\d{4})(XTX|XT|GRE)\b', r'RX \1 \2', title)
    title = re.sub(r'RX\s*(\d{4})\b', r'RX \1', title)

    title = re.sub(r'RTX\s*(\d{4})(TI|SUPER)\b', r'RTX \1 \2', title)
    title = re.sub(r'RTX\s*(\d{4})\b', r'RTX \1', title)

    title = re.sub(r'\s+', ' ', title)

    return title


def parse_brand(title):
    for b in BRANDS:
        if b in title:
            return b
    return None


def parse_gpu_vendor(title):
    if any(x in title for x in ["RTX", "GTX", "GEFORCE", "QUADRO"]):
        return "NVIDIA"
    if any(x in title for x in ["RX", "RADEON"]):
        return "AMD"
    if "ARC" in title:
        return "INTEL"
    return None


def parse_gpu_model(title):
    title = normalize_title(title)

    for pattern in WORKSTATION_PATTERNS:
        m = re.search(pattern, title)
        if m:
            return m.group(0)

    for pattern in CONSUMER_PATTERNS:
        m = re.search(pattern, title)
        if m:
            return m.group(0)

    return None


def parse_variant(title, brand):
    if not brand:
        return None

    hints = VARIANT_HINTS.get(brand)
    if hints:
        for h in sorted(hints, key=len, reverse=True):
            if h in title:
                return h

    regex_hints = VARIANT_REGEX_HINTS.get(brand)
    if regex_hints:
        for pattern in regex_hints:
            m = re.search(pattern, title)
            if m:
                return m.group(0).strip()

    return None


def parse_vram(title):
    gb_matches = list(re.finditer(r'(\d+)\s*GB\b', title, re.I))
    if not gb_matches:
        gb_matches = list(re.finditer(r'\b(\d+)G\b', title, re.I))
    if not gb_matches:
        # ASUS/etc SKU convention: "O12G", "O16G" = OC + capacity,
        # no word boundary before the digit since it follows a letter
        o_match = re.search(r'\bO(\d{1,2})G\b', title, re.I)
        if o_match:
            return int(o_match.group(1))
        return None

    mem_matches = list(re.finditer(r'GDDR\d*X?|HBM\d?', title, re.I))

    if mem_matches:
        best = min(
            gb_matches,
            key=lambda gb: min(abs(gb.start() - mem.start()) for mem in mem_matches)
        )
        return int(best.group(1))

    for gb in gb_matches:
        tail = title[gb.end():gb.end() + 15].upper()
        if "RAM" in tail:
            continue
        return int(gb.group(1))

    return None


def parse_memory_type(title):
    m = re.search(r'GDDR\dX?|HBM\d?', title, re.I)
    return m.group(0).upper() if m else None


def parse_bus_width(title):
    m = re.search(r'(\d+)\s*(?:BIT|BITS)\b', title, re.I)
    return int(m.group(1)) if m else None


def parse_oc(title):
    return bool(re.search(r'\bOC\b|OVERCLOCK', title, re.I))


def parse_sku(raw_title, brand):
    title = _sku_normalize(raw_title)
    if brand and brand in SKU_PATTERNS_BY_BRAND:
        for pattern in SKU_PATTERNS_BY_BRAND[brand]:
            m = re.search(pattern, title)
            if m:
                return m.group(0)
    return None


def parse_title(title):
    n = normalize_title(title)
    brand = parse_brand(n)

    return {
        "manufacturer": brand,
        "gpu_vendor": parse_gpu_vendor(n),
        "gpumodel": parse_gpu_model(n),
        "coolervariant": parse_variant(n, brand),
        "vram_gb": parse_vram(n),
        "memory_type": parse_memory_type(n),
        "bus_width": parse_bus_width(n),
        "is_oc": parse_oc(n),
        "sku": parse_sku(title, brand),
        "title": title,
    }

# db insertion

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
                listingid, manufacturer, chipset_brand, gpumodel,
                coolervariant, vramgb, memorytype, buswidth,
                oc, sku, title, parsedat
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, NOW()
            )
            ON CONFLICT (listingid) DO UPDATE SET
                manufacturer = EXCLUDED.manufacturer,
                chipset_brand = EXCLUDED.chipset_brand,
                gpumodel = EXCLUDED.gpumodel,
                coolervariant = EXCLUDED.coolervariant,
                vramgb = EXCLUDED.vramgb,
                memorytype = EXCLUDED.memorytype,
                buswidth = EXCLUDED.buswidth,
                oc = EXCLUDED.oc,
                sku = EXCLUDED.sku,
                title = EXCLUDED.title,
                parsedat = NOW()
        """, (
            listingid,
            parsed["manufacturer"],
            parsed["gpu_vendor"],
            parsed["gpumodel"],
            parsed["coolervariant"],
            parsed["vram_gb"],
            parsed["memory_type"],
            parsed["bus_width"],
            parsed["is_oc"],
            parsed["sku"],
            parsed["title"],
        ))

        cursor.execute("""
            UPDATE public.listing
            SET parsed = true, parsedat = NOW()
            WHERE listingid = %s
        """, (listingid,))

        conn.commit()
        print(f"[green]Parsed and saved on listingid {listingid}: {parsed}[/green]")

    except Exception as e:
        conn.rollback()
        print(f"[red]Failed on listingid {listingid}: {parsed}: {e}[/red]")


cursor.execute("""
    SELECT listingid, storetitle
    FROM listing
    WHERE parsed IS NOT TRUE AND storeid = 5
    ORDER BY listingid
""")

rows = cursor.fetchall()

for listingid, storetitle in rows:
    title = storetitle
    parsed = parse_title(title)
    save_parsed(listingid, parsed)

conn.close()

print("Done")