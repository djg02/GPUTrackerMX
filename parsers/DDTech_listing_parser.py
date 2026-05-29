from rich import print
from dotenv import load_dotenv
import json
import os
import psycopg
import re
load_dotenv()
def parse_cooler_variant(title, manufacturer, chipsetbrand, gpumodel, vramgb, buswidth, memorytype, interfaceversion):
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

    # Manufacturer
    name_part = parts[0]

    name_part = re.sub(
        r'^Taje?ta[s]?\s+(?:de\s+)?[Vv]ideo\s*',
        '',
        name_part,
        flags=re.IGNORECASE
    ).strip()

    known_manufacturers = [
        'INNO3D', 'Inno3D', 'PowerColor', 'Power Color', 'ASRock',
        'Gigabyte', 'Sapphire', 'Zotac', 'ZOTAC', 'ASUS', 'MSI',
        'XFX', 'Palit', 'EVGA', 'PNY', 'Lenovo', 'Nvidia',
        'AMD', 'Intel',
    ]

    manufacturer_aliases = {
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

    chipset_names = {'nvidia', 'amd', 'intel'}

    sub_brand_map = {
        r'\bAORUS\b': 'Gigabyte',
        r'\bROG\b': 'ASUS',
    }

    manufacturer = None

    for pattern, parent in sub_brand_map.items():
        if re.search(pattern, name_part, re.IGNORECASE):
            non_chipset_mfrs = [
                m for m in known_manufacturers
                if m.lower() not in chipset_names
            ]

            if not any(
                re.search(r'\b' + re.escape(m) + r'\b', name_part, re.IGNORECASE)
                for m in non_chipset_mfrs
            ):
                manufacturer = parent
                break

    if not manufacturer:
        for mfr in known_manufacturers:
            if re.search(r'\b' + re.escape(mfr) + r'\b', name_part, re.IGNORECASE):
                manufacturer = manufacturer_aliases.get(mfr.lower(), mfr)

                name_part = re.sub(
                    r'\b' + re.escape(mfr) + r'\b',
                    '',
                    name_part,
                    flags=re.IGNORECASE,
                    count=1
                ).strip()

                break

    # Chipset
    chipsetbrand = None

    for brand in ['NVIDIA', 'AMD', 'INTEL']:
        if re.search(r'\b' + re.escape(brand) + r'\b', name_part, re.IGNORECASE):
            chipsetbrand = brand

            name_part = re.sub(
                r'\b' + re.escape(brand) + r'\b',
                '',
                name_part,
                flags=re.IGNORECASE,
                count=1
            ).strip()

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

    if coolervariant and manufacturer:
        strip_variants = {manufacturer}

        if manufacturer == 'PowerColor':
            strip_variants.add('Power Color')

        for variant in strip_variants:
            coolervariant = re.sub(
                r'\b' + re.escape(variant) + r'\b',
                '',
                coolervariant,
                flags=re.IGNORECASE
            ).strip()

        coolervariant = re.sub(r'\s+', ' ', coolervariant).strip() or None

    if coolervariant:
        coolervariant = re.sub(
            r'^Taje?ta[s]?\s+(?:de\s+)?[Vv]ideo\s*',
            '',
            coolervariant,
            flags=re.IGNORECASE
        ).strip()

        coolervariant = coolervariant or None

    try:
        cursor.execute("""
            INSERT INTO public.listing_parsed (
                listingid,
                manufacturer,
                chipset_brand,
                gpumodel,
                vramgb,
                memorytype,
                buswidth,
                interfaceversion,
                oc,
                coolervariant,
                sku,
                title,
                parsedat
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
            listingid,
            manufacturer,
            chipsetbrand,
            gpumodel,
            vramgb,
            memorytype,
            buswidth,
            interfaceversion,
            oc,
            coolervariant,
            sku,
            title
        ))

        cursor.execute("""
            UPDATE public.listing
            SET parsed = true,
                parsedat = NOW()
            WHERE listingid = %s
        """, (listingid,))

        conn.commit()

        print(f"[green]Parsed and saved {title}[/green]")

    except Exception as e:
        conn.rollback()
        print(f"[red]Failed on listingid {id}: {e}[/red]")

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
    listingid = row[0]
    title = row[1]
    parse_title_only(listingid, title, cursor, conn)
print(f"[green] Finished parsing [/green]")
