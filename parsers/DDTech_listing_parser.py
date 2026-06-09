from rich import print
from dotenv import load_dotenv
import json
import os
import psycopg
import re
load_dotenv()

# ── Cooler variant mappings (reused from normalizer) ──────────────────────────
COOLER_MAPPINGS = {
    "GIGABYTE": {
        "AERO": "Aero",
        "EAGLE": "Eagle",
        "EAGLE ICE": "Eagle Ice",
        "EAGLE ICE SFF": "Eagle Ice SFF",
        "EAGLE MAX": "Eagle Max",
        "EAGLEMAX": "Eagle Max",
        "ELITE": "Elite",
        "ELITE WINDFORCE": "Elite WINDFORCE",
        "GAMING": "Gaming",
        "GAMING ICE": "Gaming Ice",
        "WINDFORCE": "Windforce",
        "WINDFORCE MAX": "Windforce Max",
        "WINDFORCE SFF": "Windforce SFF",
        "WINDFORCE V2": "Windforce V2",
        "WINDFORCE 2X V2": "Windforce 2X V2",
        "AORUS MASTER": "AORUS Master",
        "AORUS MASTER ICE": "AORUS Master Ice",
        "AORUS MASTER LHR": "Aorus Master LHR",
        "AORUS XTREME LHR": "Aorus Xtreme LHR",
        "AORUS ELITE": "AORUS Elite",
        "XTREME WATERFORCE": "Xtreme Waterforce",
        "LOW PROFILE": "Low Profile",
        "EAGLE SFF": "Eagle SFF",
        "ICE": "Ice",
        "AORUS XTREME": "AORUS Xtreme",
        "AORUS WATERFORCE": "AORUS Waterforce",
        "AORUS WATERFORCE WB": "AORUS Waterforce WB",
        "AORUS XTREME WATERFORCE": "AORUS Xtreme Waterforce",
        "MASTER": "AORUS Master",
        "MASTER ICE": "AORUS Master Ice",
        "XTREME": "AORUS Xtreme",
    },
    "ASUS": {
        "PRIME": "Prime",
        "DUAL EVO WHITE": "Dual Evo White",
        "DUAL EVO": "Dual Evo",
        "DUAL WHITE": "Dual White",
        "DUAL": "Dual",
        "TUF WHITE": "TUF White",
        "TUF GAMING": "TUF Gaming",
        "TUF": "TUF Gaming",
        "PROART": "ProArt",
        "ROG MATRIX PLATINUM": "ROG Matrix Platinum",
        "ROG MATRIX": "ROG Matrix",
        "ROG ASTRAL": "ROG Astral",
        "ROG STRIX GAMING": "ROG Strix",
        "ROG STRIX LC": "ROG Strix LC",
        "ROG STRIX": "ROG Strix",
        "ROG": "ROG Strix",
        "KO": "KO",
        "PHOENIX": "Phoenix",
        "STRIX": "ROG Strix",
    },
    "MSI": {
        "VENTUS 2X WHITE PLUS": "Ventus 2X White Plus",
        "VENTUS 3X WHITE": "Ventus 3X White",
        "VENTUS 3X BLACK": "Ventus 3X Black",
        "VENTUS 3X PLUS": "Ventus 3X Plus",
        "VENTUS 2X WHITE": "Ventus 2X White",
        "VENTUS 2X PLUS": "Ventus 2X Plus",
        "VENTUS 3X": "Ventus 3X",
        "VENTUS 2X": "Ventus 2X",
        "VENTUS": "Ventus",
        "GAMING X TRIO": "Gaming X Trio",
        "GAMING TRIO": "Gaming Trio",
        "GAMING TRIO WHITE": "Gaming Trio White",
        "GAMING X SLIM": "Gaming X Slim",
        "GAMING SLIM": "Gaming Slim",
        "GAMING X": "Gaming X",
        "GAMING": "Gaming",
        "SHADOW 3X": "Shadow 3X",
        "SHADOW 2X": "Shadow 2X",
        "INSPIRE 3X": "Inspire 3X",
        "INSPIRE 2X": "Inspire 2X",
        "LIGHTNING Z": "Lightning Z",
        "VANGUARD SOC LAUNCH": "Vanguard SOC",
        "VANGUARD SOC ED": "Vanguard SOC",
        "VANGUARD SOC": "Vanguard SOC",
        "VANGUARD LAUNCH": "Vanguard",
        "VANGUARD": "Vanguard",
        "SUPRIM LIQUID SOC": "Suprim Liquid SOC",
        "SUPRIM SOC": "Suprim SOC",
        "SUPRIM X": "Suprim X",
        "SUPRIM": "Suprim",
        "LOW PROFILE": "Low Profile",
        "TRIO": "Gaming Trio",
        "TRIO WHITE": "Gaming Trio White",
        "CYCLONE": "Cyclone",
        "LP": "Low Profile",
        "MLG EDITION": "MLG Edition",
    },
    "POWERCOLOR": {
        "HELLHOUND SPECTRAL WHITE": "Hellhound Spectral White",
        "HELLHOUND SPECTRAL": "Hellhound Spectral",
        "HELLHOUND REVA": "Hellhound",
        "HELLHOUND": "Hellhound",
        "RED DEVIL": "Red Devil",
        "REAPER": "Reaper",
        "FIGHTER": "Fighter",
    },
    "XFX": {
        "MERCURY TRIPLE FAN GAMING": "Mercury",
        "MERCURY TRIPLE FAN": "Mercury",
        "MERCURY GAMING RGB": "Mercury",
        "MERCURY MAGNETIC AIR": "Mercury",
        "MERCURY": "Mercury",
        "SPEEDSTER MERC": "Speedster Merc",
        "SPEEDSTER QICK": "Speedster QICK",
        "SPEEDTESTER QICK": "Speedster QICK",
        "SPEEDTESTER SWFT": "Speedster SWFT",
        "SPEEDSTER SWFT CORE": "Speedster SWFT Core",
        "SPEEDSTER SWFT210": "Speedster SWFT",
        "SPEEDSTER SWFT": "Speedster SWFT",
        "SWFT CORE": "Speedster SWFT Core",
        "SWIFT WHITE TRIPLE FAN GAMING": "Speedster SWFT White",
        "SWIFT TRIPLE FAN GAMING": "Speedster SWFT",
        "SWIFT WHITE GAMING": "Speedster SWFT White",
        "SWIFT PRO GAMING": "Speedster SWFT",
        "SWIFT GAMING": "Speedster SWFT",
        "SWIFT": "Speedster SWFT",
        "QUICKSILVER": "Quicksilver",
        "QUICK SILVER": "Quicksilver",
        "QICKSILVER": "Quicksilver",
        "WHITE GAMING": "White Gaming",
        "WHITE": "White",
        "SPEEDSTER": "Speedster",
        "MERC": "Speedster Merc",
        "QICK": "Speedster QICK",
        "SWFT WHITE": "Speedster SWFT White",
    },
    "ZOTAC": {
        "AMP EXTREME INFINITY": "AMP Extreme Infinity",
        "AMP EXTREME AIRO": "AMP Extreme AIRO",
        "AMP EXTREME": "AMP Extreme",
        "GAMING AMP HOLO": "AMP Holo",
        "AMP HOLO": "AMP Holo",
        "AMP WHITE": "AMP White",
        "AMP AIRO": "AMP AIRO",
        "AMP": "AMP",
        "SOLID CORE WHITE": "Solid Core White",
        "SOLID CORE": "Solid Core",
        "SOLID WHITE": "Solid White",
        "GAMING SOLID": "Solid",
        "SOLID SFF": "Solid SFF",
        "SOLID": "Solid",
        "TWIN EDGE GAMING": "Twin Edge",
        "TWIN EDGE": "Twin Edge",
        "TRINITY WHITE": "Trinity White",
        "TRINITY": "Trinity",
        "GAMING TWIN EDGE": "Twin Edge",
        "TWIN EDGE OC": "Twin Edge",
        "TWIN EDGE WHITE": "Twin Edge White",
        "TWIN EDGE WHITE OC": "Twin Edge White",

    },
    "PNY": {
        "XLR8 GAMING VERTO EPIC-X RGB": "XLR8 Verto",
        "EPIC-X RGB": "EPIC-X RGB",
        "XLR8 RGB": "XLR8",
        "XLR8 VERTO": "XLR8 Verto",
        "XLR8": "XLR8",
        "TF VERTO": "TF Verto",
        "TARJETA VIDEO VERTO": "Verto",
        "VERTO DUAL FAN": "Verto",
        "VERTO": "Verto",
        "ARGB": "ARGB",
        "DUAL FAN LHR": "Dual Fan",
        "DUAL FAN": "Dual Fan",
        "DUAL": "Dual Fan",
        "OC EDITION": "OC Edition",
        "OVERCLOCKED": "OC Edition",
    },
    "ASROCK": {
        "PHANTOM GAMING": "Phantom Gaming",
        "STEEL LEGEND": "Steel Legend",
        "CHALLENGER D": "Challenger D",
        "CHALLENGER PRO": "Challenger Pro",
        "CHALLENGER": "Challenger",
        "TAICHI": "Taichi",
        "CHALLENGER ITX": "Challenger ITX",
        "PHANTOM GAMING D": "Phantom Gaming",
        "PHANTOM GAMING OC": "Phantom Gaming",
    },
    "SAPPHIRE": {
        "PULSE GAMING": "Pulse Gaming",
        "PULSE XT": "Pulse XT",
        "PULSE LITE": "Pulse Lite",
        "PULSE": "Pulse",
        "NITRO+ SPECIAL EDITION": "Nitro+ SE",
        "NITRO+": "Nitro+",
        "NITRO": "Nitro+",
        "PURE": "Pure",
        "XL": "XL",
        "NITRO+ GAMING OC": "Nitro+",
        "NITRO+ OC": "Nitro+",
        "PURE OC": "Pure",
        "PULSE OC": "Pulse",
        "NITRO+ GAMING OC": "Nitro+",
        "NITRO+ OC": "Nitro+",
        "PURE OC": "Pure",
        "PULSE OC": "Pulse",
    },
    "INNO3D": {
        "TWIN X2 WHITE": "Twin X2 White",
        "TWIN X2": "Twin X2",
        "X3": "X3",
    },
    "EVGA": {
        "FTW3 ULTRA GAMING": "FTW3 Ultra",
        "FTW3": "FTW3",
        "XC3": "XC3",
        "XC": "XC",
    },
    "PALIT": {
        "GAMING PRO": "Gaming Pro",
        "GAMEROCK": "GameRock",
        "DUAL": "Dual",
    },
}

# Manufacturer aliases (normalized key → canonical name)
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
    'lenovo': 'Lenovo',
}

KNOWN_MANUFACTURERS = [
    'INNO3D', 'Inno3D', 'PowerColor', 'Power Color', 'ASRock',
    'Gigabyte', 'Sapphire', 'Zotac', 'ZOTAC', 'ASUS', 'MSI',
    'XFX', 'Palit', 'EVGA', 'PNY', 'Lenovo', 'Nvidia',
    'AMD', 'Intel',
]

CHIPSET_NAMES = {'nvidia', 'amd', 'intel'}

SUB_BRAND_MAP = {
    r'\bAORUS\b': 'Gigabyte',
    r'\bROG\b': 'ASUS',
}


def lookup_cooler(manufacturer, text):
   # Look up cooler variant from mappings given a manufacturer and text
    if not manufacturer:
        return None
    mfr_key = manufacturer.upper()
    mapping = COOLER_MAPPINGS.get(mfr_key)
    if not mapping:
        return None
    text_upper = text.upper()
    # Sort by length descending so longer/more specific keys match first
    for key in sorted(mapping.keys(), key=len, reverse=True):
        if key in text_upper:
            return mapping[key]
    return None


def find_manufacturer_in_part(part):
    # Try to find a board partner manufacturer in a title segment
    for mfr in KNOWN_MANUFACTURERS:
        if re.search(r'\b' + re.escape(mfr) + r'\b', part, re.IGNORECASE):
            canonical = MANUFACTURER_ALIASES.get(mfr.lower(), mfr)
            if canonical.lower() not in CHIPSET_NAMES:
                return canonical
    return None


def parse_cooler_variant(title, manufacturer, chipsetbrand, gpumodel, vramgb, buswidth, memorytype, interfaceversion):
    parts = re.split(r'\s*/\s*', title)

    # ── Strategy 1: mapping-based lookup on the full title ────────────────────
    if manufacturer:
        cooler = lookup_cooler(manufacturer, title)
        if cooler:
            return cooler

    # ── Strategy 2: scan later slash segments for cooler keywords ─────────────
    # Useful for old DDTech titles like "... / Asus DUAL / ..." where the
    # cooler comes after the GPU model segment
    if manufacturer:
        for part in parts[1:]:
            # Skip pure spec segments
            if re.search(
                r'\d+GB|\d+-bit|HDMI|DisplayPort|PCI|^\d{3}-|RDNA|'
                r'ventiladores|Ventiladores|bits\s+GDDR|DirectX|Boost Clock',
                part, re.IGNORECASE
            ):
                continue
            cooler = lookup_cooler(manufacturer, part)
            if cooler:
                return cooler

    # ── Strategy 3: regex-based fallback (original logic) ────────────────────
    s = title

    # 1. Strip slash-delimited spec segments
    parts = re.split(r'\s*/\s*', s)
    if len(parts) > 1:
        clean_parts = []
        for part in parts:
            if re.search(r'\d+GB|\d+-bit|HDMI|DisplayPort|PCI|^\d{3}-|Tarjeta Gr|RDNA|AMD RDNA|ventiladores|Ventiladores|bits\s+GDDR', part, re.IGNORECASE):
                break
            clean_parts.append(part)
        s = ' '.join(clean_parts).strip()

    # 2. Strip known leading label
    s = re.sub(r'^Tarjeta[s]? de Video\s*', '', s, flags=re.IGNORECASE).strip()

    # 3. Remove known tokens: manufacturer, chipset brand, GPU model
    for token in [manufacturer, chipsetbrand, gpumodel]:
        if token:
            s = re.sub(r'\b' + re.escape(token) + r'\b', '', s, flags=re.IGNORECASE).strip()
    # 3a. Strip "GeForce" / "Radeon" architecture words that survive token removal
    s = re.sub(r'\b(?:GeForce|Radeon|NAVI\s*\d*)\b', '', s, flags=re.IGNORECASE).strip()

    # 3b. Strip ASUS-style VRAM/OC capacity codes: O12G, O16G, O8G and AMD capacity codes like "CL 8GO", "8GO"
    s = re.sub(r'\bO\d+G\b', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\bCL\s*\d+GO\b|\b\d+GO\b', '', s, flags=re.IGNORECASE).strip()

    # 3c. Strip standalone VRAM sizes only (must be followed by word boundary, not DDR)
    s = re.sub(r'\b\d+\s*GB\b', '', s, flags=re.IGNORECASE).strip()  # "8GB", "16 GB"
    s = re.sub(r'\b\d+G\b(?!DR)', '', s, flags=re.IGNORECASE).strip()  # "8G" but not "GDDR"

    # 3d. Strip surviving GPU model fragments: "5060 Ti", "RX 9060 XT", "GTX 1060", "RX9060XT"
    s = re.sub(r'\b(?:RTX|GTX|RX|Arc)?\s*\d{3,4}(?:\s*(?:Ti|XT|XTX|SUPER|GRE))?\b', '', s, flags=re.IGNORECASE).strip()
    
    # 3e. Strip leading/trailing commas, dashes, punctuation
    s = re.sub(r'^[\s,\-]+|[\s,\-]+$', '', s).strip()

    # 4. Remove spec suffixes (with or without leading number, handles ", -bit GDDR6" remnants)
    s = re.sub(r',?\s*\d*\s*-?\s*bit\s+\w+.*$', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r',?\s*PCI Express[\s\w.x]*.*$', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\s*-\s*incluye.*$', '', s, flags=re.IGNORECASE).strip()

    # 4b. Clean up leading/trailing commas again after suffix removal
    s = re.sub(r'^[\s,\-]+|[\s,\-]+$', '', s).strip()

    # 4b. Remove any remaining PCI Express / GDDR spec fragments
    s = re.sub(r',?\s*PCI Express[\s\w.x]*$', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r',?\s*\d+-bit\s+\w+$', '', s, flags=re.IGNORECASE).strip()

    # 4c. Remove long parenthetical or dash-separated spec descriptions
    s = re.sub(r'\s*-\s*incluye.*$', '', s, flags=re.IGNORECASE).strip()

    # 5. Remove "OC Edition" / "OC" anywhere
    s = re.sub(r'\bOC Edition\b|\bOC\b', '', s, flags=re.IGNORECASE).strip()

    # 6. Remove standalone "Edition"
    s = re.sub(r'\bEdition\b', '', s, flags=re.IGNORECASE).strip()

    # 7. Collapse whitespace
    s = re.sub(r'\s+', ' ', s).strip()

    # 8. Reject if it looks like a SKU code
    if s and (
         re.match(r'^[A-Z0-9][\w]*(?:-[A-Z0-9][\w]*){2,}$', s, re.IGNORECASE) or
    re.match(r'^[A-Z]{2,}\d+[A-Z0-9\-]+$', s) or
    re.match(r'^[\w]+-[\w]+-[\w]+', s) or
    '--' in s or# DUAL--BLANCO
    re.search(r'\s-\w+', s)# GV-N506TGAMING -8GD
    ):
        s = None

    return s or None

def parse_title_only(listingid, title, cursor, conn):
    s = title

    # Clean title
    s = re.sub(r'[®™]', '', s).strip()
    s = re.sub(r'\s+', ' ', s)

    # Split on slashes
    parts = re.split(r'\s*/\s*', s)

    # Extract specs from slash segments
    vramgb = None
    memorytype = None
    buswidth = None
    interfaceversion = None
    sku = None

    for i, part in enumerate(parts[1:], 1):
        m = re.search(r'(\d+)\s*GB\s+(?:\d+-bit\s+)?(GDDR\w+|HBM\w*)', part, re.IGNORECASE)
        if m and not vramgb:
            vramgb = int(m.group(1))
            memorytype = m.group(2).upper()

        if not vramgb:
            m = re.search(r'^(\d+)\s*GB$', part.strip(), re.IGNORECASE)
            if m:
                vramgb = int(m.group(1))
                if i < len(parts) - 1:
                    mem_m = re.search(r'(GDDR\w+|HBM\w*)', parts[i + 1], re.IGNORECASE)
                    if mem_m:
                        memorytype = mem_m.group(1).upper()

        m = re.search(r'(\d+)-bit', part, re.IGNORECASE)
        if m and not buswidth:
            buswidth = int(m.group(1))

        m = re.search(r'PCI[- ]Express(?:\s+x\d+)?\s+([\d.]+)', part, re.IGNORECASE)
        if m and not interfaceversion:
            interfaceversion = m.group(1)

    if not vramgb:
        m = re.search(r'(\d+)\s*GB\s*(GDDR\w+|HBM\w*)', parts[0], re.IGNORECASE)
        if m:
            vramgb = int(m.group(1))
            memorytype = m.group(2).upper()

    if not memorytype:
        m = re.search(r'(GDDR\w+|HBM\w*)', parts[0], re.IGNORECASE)
        if m:
            memorytype = m.group(1).upper()

    # Manufacturer detection
    name_part = parts[0]
    name_part = re.sub(r'^Taje?ta[s]?\s+(?:de\s+)?[Vv]ideo\s*', '', name_part, flags=re.IGNORECASE).strip()

    manufacturer = None

    # Sub-brand check (AORUS → Gigabyte, ROG → ASUS)
    for pattern, parent in SUB_BRAND_MAP.items():
        if re.search(pattern, name_part, re.IGNORECASE):
            non_chipset_mfrs = [m for m in KNOWN_MANUFACTURERS if m.lower() not in CHIPSET_NAMES]
            if not any(re.search(r'\b' + re.escape(m) + r'\b', name_part, re.IGNORECASE) for m in non_chipset_mfrs):
                manufacturer = parent
                break

    if not manufacturer:
        for mfr in KNOWN_MANUFACTURERS:
            if re.search(r'\b' + re.escape(mfr) + r'\b', name_part, re.IGNORECASE):
                manufacturer = MANUFACTURER_ALIASES.get(mfr.lower(), mfr)
                name_part = re.sub(r'\b' + re.escape(mfr) + r'\b', '', name_part, flags=re.IGNORECASE, count=1).strip()
                break

    # Fix: old DDTech titles start with "Nvidia GeForce ... / ASUS DUAL / ..."
    # If manufacturer resolved to a chipset brand, look in later slash segments
    if not manufacturer or manufacturer.lower() in CHIPSET_NAMES:
        for part in parts[1:]:
            # Skip pure spec segments
            if re.search(r'\d+GB|\d+-bit|PCI|DirectX|Boost Clock|HDMI|DisplayPort', part, re.IGNORECASE):
                continue
            real_mfr = find_manufacturer_in_part(part)
            if real_mfr:
                manufacturer = real_mfr
                break

    # Chipset brand
    chipsetbrand = None
    for brand in ['NVIDIA', 'AMD', 'INTEL']:
        if re.search(r'\b' + re.escape(brand) + r'\b', name_part, re.IGNORECASE):
            chipsetbrand = brand
            name_part = re.sub(r'\b' + re.escape(brand) + r'\b', '', name_part, flags=re.IGNORECASE, count=1).strip()
            break

    if not chipsetbrand:
        if re.search(r'\bGeForce\b|\bGTX\b|\bRTX\b|\bQuadro\b', name_part, re.IGNORECASE):
            chipsetbrand = 'NVIDIA'
        elif re.search(r'\bRadeon\b|\bRX\s*\d{4}\b', name_part, re.IGNORECASE):
            chipsetbrand = 'AMD'
        elif re.search(r'\bARC\b', name_part, re.IGNORECASE):
            chipsetbrand = 'INTEL'

    # GPU model
    gpumodel = None

    m = re.search(
        r'(?:GeForce\s+)?(?:RTX|GTX|GT)\s+\d{3,4}(?:\s*Ti)?(?:\s+SUPER)?'
        r'|(?:Radeon\s+)?RX\s+\d{4}(?:\s*(?:XT|XTX|GRE))?'
        r'|(?:Arc\s+)?[AB]\d{3,4}\b',
        name_part,
        re.IGNORECASE
    )

    if m:
        gpumodel = re.sub(r'\s+', ' ', m.group(0)).strip()

    # OC
    oc = bool(re.search(r'\bOC\b', title, re.IGNORECASE))

    # SKU
    for part in reversed(parts[1:]):
        part = part.strip()
        if re.match(r'^[A-Z0-9][\w]*(?:-[A-Z0-9][\w]*){1,}$', part, re.IGNORECASE):
            sku = part
            break

    # Cooler variant
    coolervariant = parse_cooler_variant(
        title,
        manufacturer,
        chipsetbrand,
        gpumodel,
        f"{vramgb}GB" if vramgb else None,
        f"{buswidth}-bit" if buswidth else None,
        memorytype,
        f"PCI Express {interfaceversion}" if interfaceversion else None
    )

    # Strip manufacturer name from coolervariant if it leaked in
    if coolervariant and manufacturer:
        strip_variants = {manufacturer}
        if manufacturer == 'PowerColor':
            strip_variants.add('Power Color')
        for variant in strip_variants:
            coolervariant = re.sub(r'\b' + re.escape(variant) + r'\b', '', coolervariant, flags=re.IGNORECASE).strip()
        coolervariant = re.sub(r'\s+', ' ', coolervariant).strip() or None

    if coolervariant:
        coolervariant = re.sub(r'^Taje?ta[s]?\s+(?:de\s+)?[Vv]ideo\s*', '', coolervariant, flags=re.IGNORECASE).strip()
        coolervariant = coolervariant or None

    try:
        cursor.execute("""
            INSERT INTO public.listing_parsed (
                listingid, manufacturer, chipset_brand, gpumodel,
                vramgb, memorytype, buswidth, interfaceversion,
                oc, coolervariant, sku, title, parsedat
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, NOW()
            )
            ON CONFLICT (listingid) DO UPDATE SET
                manufacturer = EXCLUDED.manufacturer,
                chipset_brand = EXCLUDED.chipset_brand,
                gpumodel = EXCLUDED.gpumodel,
                vramgb = EXCLUDED.vramgb,
                memorytype = EXCLUDED.memorytype,
                buswidth = EXCLUDED.buswidth,
                interfaceversion = EXCLUDED.interfaceversion,
                oc = EXCLUDED.oc,
                coolervariant = EXCLUDED.coolervariant,
                sku = EXCLUDED.sku,
                title = EXCLUDED.title,
                parsedat = NOW()
        """, (
            listingid, manufacturer, chipsetbrand, gpumodel,
            vramgb, memorytype, buswidth, interfaceversion,
            oc, coolervariant, sku, title
        ))

        cursor.execute("""
            UPDATE public.listing
            SET parsed = true, parsedat = NOW()
            WHERE listingid = %s
        """, (listingid,))

        conn.commit()
        print(f"[green]Parsed:[/green] {title[:80]}  →  mfr={manufacturer}  cooler={coolervariant}")

    except Exception as e:
        conn.rollback()
        print(f"[red]Failed on listingid {listingid}: {e}[/red]")

# Main
conn = psycopg.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
)
cursor = conn.cursor()

cursor.execute("""
    SELECT listingid, storetitle
    FROM listing
    WHERE storeid = 1
    ORDER BY listingid
""")

rows = cursor.fetchall()
for row in rows:
    parse_title_only(row[0], row[1], cursor, conn)

print(f"[green]Finished parsing {len(rows)} listings[/green]")
cursor.close()
conn.close()