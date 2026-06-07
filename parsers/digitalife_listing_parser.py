from rich import print
from dotenv import load_dotenv
import json
import os
import psycopg
import re
load_dotenv()


def get_attr(spec_json, attribute_name):
    attribute_group_map = spec_json.get("attribute_group_map", {})
    for group in attribute_group_map.values():
        for a in group.get("attributes", []):
            if a.get("attribute_name") == attribute_name:
                return a.get("value")
    return None


def parse(id, jsondata, spec_json):
    try:
        title = re.sub(r'[®™]', '', jsondata.get("name", "")).strip()
        title = re.sub(r'\s+', ' ', title)

        manufacturer = (jsondata.get("brand_name") or (jsondata.get("brand") or {}).get("name") or "").upper() or None
        chipsetbrand = get_attr(spec_json, "Familia de procesadores de gráficos")
        gpumodel = get_attr(spec_json, "Procesador gráfico")
        oc_raw = get_attr(spec_json, "Edición Overclocked (OC)")
        oc = (oc_raw == "Si") or bool(re.search(r'\bOC\b', title, re.IGNORECASE))
        color = get_attr(spec_json, "Color del producto")

        vramgb_raw = (get_attr(spec_json, "Capacidad memoria de adaptador gráfico") or get_attr(spec_json, "Capacidad de Memoria Gráfica"))
        vramgb = int(re.sub(r'[^\d]', '', vramgb_raw)) if vramgb_raw and re.search(r'\d', vramgb_raw) else None

        memorytype = get_attr(spec_json, "Tipo de memoria de adaptador gráfico")

        buswidth_raw = get_attr(spec_json, "Bus de memoria")
        buswidth = int(re.sub(r'[^\d]', '', buswidth_raw)) if buswidth_raw and re.search(r'\d', buswidth_raw) else None

        interfaceversion_raw = get_attr(spec_json, "Tipo de interfaz")
        interfaceversion = re.sub(r'x\d+\s*', '', interfaceversion_raw.replace("PCI Express ", "")).strip() if interfaceversion_raw else None

        fans_raw = get_attr(spec_json, "Número de ventiladores")
        fans = int(re.search(r'\d+', fans_raw).group()) if fans_raw and re.search(r'\d+', fans_raw) else None

        sku = jsondata.get("part_number")

        boostclock_raw = (
            get_attr(spec_json, "Frecuencia del procesador (modo OC)") or
            get_attr(spec_json, "Aumento de la velocidad de reloj del procesador")
        )
        baseclock_raw = get_attr(spec_json, "Frecuencia base del procesador")
        boostclock = int(re.sub(r'[^\d]', '', boostclock_raw)) if boostclock_raw and re.search(r'\d', boostclock_raw) else None
        baseclock = int(re.sub(r'[^\d]', '', baseclock_raw)) if baseclock_raw and re.search(r'\d', baseclock_raw) else None

        coolervariant = parse_cooler_variant(title, manufacturer, chipsetbrand, gpumodel, vramgb_raw, buswidth_raw, memorytype, interfaceversion_raw, color)

        cursor.execute("""
            INSERT INTO public.listing_parsed (
                listingid, manufacturer, chipset_brand, gpumodel,
                oc, vramgb, memorytype, buswidth, interfaceversion,
                coolervariant, color, sku, title, fans, boostclock, baseclock, parsedat
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, NOW()
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
                color = EXCLUDED.color,
                sku = EXCLUDED.sku,
                title = EXCLUDED.title,
                fans = EXCLUDED.fans,
                boostclock = EXCLUDED.boostclock,
                baseclock = EXCLUDED.baseclock,
                parsedat = now()
        """, (
            id, manufacturer, chipsetbrand, gpumodel,
            oc, vramgb, memorytype, buswidth, interfaceversion,
            coolervariant, color, sku, title, fans, boostclock, baseclock
        ))

        cursor.execute("""
            UPDATE public.listing
            SET parsed = true, parsedat = now()
            WHERE listingid = %s
        """, (id,))

        conn.commit()
        print(f"[green]Parsed and saved {title}[/green]")

    except Exception as e:
        conn.rollback()
        print(f"[red]Failed on listingid {id}: {e}[/red]")


def parse_cooler_variant(title, manufacturer, chipsetbrand, gpumodel, vramgb_raw, buswidth_raw, memorytype, interfaceversion_raw, color):
    s = title

    # 1. Strip slash-delimited spec segments
    parts = re.split(r'\s*/\s*', s)
    if len(parts) > 1:
        clean_parts = []
        for part in parts:
            if re.search(r'\d+GB|\d+-bit|HDMI|DisplayPort|PCI|^\d{3}-', part, re.IGNORECASE):
                break
            clean_parts.append(part)
        s = ' '.join(clean_parts).strip()

    # 2. Strip known leading labels
    s = re.sub(r'^Tarjeta[s]? de Video,?\s*', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'^Tarjeta[s]?\s*Gr[aá]fica,?\s*', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'^Gr[aá]fica,?\s*', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\bGr[aá]fico\b', '', s, flags=re.IGNORECASE).strip()

    # 3. Remove known tokens: manufacturer, chipset brand, GPU model
    for token in [manufacturer, chipsetbrand, gpumodel]:
        if token:
            s = re.sub(r'\b' + re.escape(token) + r'\b', '', s, flags=re.IGNORECASE).strip()

    # 3a. Strip architecture words
    s = re.sub(r'\b(?:GeForce|Radeon|NAVI\s*\d*)\b', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'Radeon\s*RX\s*\d{4}\s*(?:XT|XTX|SUPER)?\b', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'GeForce\s*RTX\s*\d{4}\s*(?:Ti|SUPER)?\b', '', s, flags=re.IGNORECASE).strip()

    # 3b. Strip ASUS-style capacity codes
    s = re.sub(r'\bO\d+G\b', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\bCL\s*\d+GO\b|\b\d+GO\b', '', s, flags=re.IGNORECASE).strip()

    # 3c. Strip VRAM sizes
    s = re.sub(r'\b\d+\s*GB\b', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\b\d+G\b(?!DR)', '', s, flags=re.IGNORECASE).strip()

    # 3d. Strip GPU model fragments
    s = re.sub(r'\b(?:RTX|GTX|RX|Arc)?\s*\d{3,4}(?:\s*(?:Ti|XT|XTX|SUPER))?\b', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\bR\d{4}\b', '', s, flags=re.IGNORECASE).strip()

    # 3e. Strip PCIE and GDDR specs
    s = re.sub(r'PCIE\s*\d+x\s*\d+\.?\d*', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'PCI\s*Express\s*x?\d*\s*\d+\.?\d*', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\bx\d+\b', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'GDDR\d*', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\bDDR\d*\b', '', s, flags=re.IGNORECASE).strip()

    # 3f. Strip bit/bus width remnants
    s = re.sub(r'\b\d*\s*-?\s*Bits?\b', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r',?\s*\d*\s*-?\s*bit\s+\w+.*$', '', s, flags=re.IGNORECASE).strip()

    # 3g. Strip fan descriptions
    s = re.sub(r'\b(?:Triple|Doble|Single|Dual|Doble)\s+Ventilador(?:es)?\b', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\b\d+\s*Ventilador(?:es)?\b', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\bTriple\s+Fan\b|\bDual\s+Fan\b|\bSingle\s+Fan\b', '', s, flags=re.IGNORECASE).strip()

    # 3h. Strip standalone PCIe/PCIE remnants
    s = re.sub(r'\bPCIe\b|\bPCIE\b', '', s, flags=re.IGNORECASE).strip()

    # 3i. Strip standalone "x" leftover from x16 stripping  
    s = re.sub(r'(?<!\w)x(?!\w)', '', s, flags=re.IGNORECASE).strip()

    # 3j. Strip standalone "XT" only when isolated (not part of a word like "XTX")
    s = re.sub(r'\bXT\b(?!X)', '', s).strip()
    s = re.sub(r'\bTi\b', '', s).strip()

    # 3k. Strip "- ," and ", -" and ", , " separator remnants
    s = re.sub(r',?\s*-\s*,?', ' ', s).strip()
    s = re.sub(r'(,\s*){2,}', ' ', s).strip()

    # 3l. Strip trailing/leading "- " 
    s = re.sub(r'^[\s,\-]+|[\s,\-]+$', '', s).strip()

    # 3m. Strip color tokens
    if color:
        for c in color.split(','):
            s = re.sub(r'\b' + re.escape(c.strip()) + r'\b', '', s, flags=re.IGNORECASE).strip()

    # 3o. Strip standalone resolution/version numbers like "5.0", "4.0"
    s = re.sub(r'\b\d+\.\d+\b', '', s).strip()

    # 3p. Strip "x16", "x8" slot width remnants
    s = re.sub(r'\bx\d+\b', '', s, flags=re.IGNORECASE).strip()

    # 4. Strip trailing spec suffixes
    s = re.sub(r',?\s*PCI Express[\s\w.x]*.*$', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\s*-\s*incluye.*$', '', s, flags=re.IGNORECASE).strip()

    # 5. Remove OC / Edition
    s = re.sub(r'\bOC Edition\b|\bOC\b', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\bEdition\b', '', s, flags=re.IGNORECASE).strip()

    # 6. Strip ARGB/RGB as standalone suffix
    s = re.sub(r'\bARGB\b|\bRGB\b', '', s).strip()
    s = re.sub(r',\s*', ' ', s).strip()
    
    # 7. Deduplicate consecutive repeated words
    words = s.split()
    seen = []
    seen_lower = set()
    for w in words:
        if w.lower() not in seen_lower:
            seen.append(w)
            seen_lower.add(w.lower())
    s = ' '.join(seen)

    # 7. Clean up orphaned commas and whitespace
    s = re.sub(r'(,\s*){2,}', ', ', s)
    s = re.sub(r'^[\s,\-]+|[\s,\-]+$', '', s).strip()
    s = re.sub(r'\s+', ' ', s).strip()

    # 8. Reject if it looks like a SKU code
    if s and (
        re.match(r'^[A-Z0-9][\w]*(?:-[A-Z0-9][\w]*){2,}$', s, re.IGNORECASE) or
        re.match(r'^[A-Z]{2,}\d+[A-Z0-9\-]+$', s) or
        re.match(r'^[\w]+-[\w]+-[\w]+', s) or
        '--' in s or
        re.search(r'\s-\w+', s)
    ):
        s = None

    # 9. Reject if too short or just punctuation
    if s and len(s) < 3:
        s = None

    return s or None


conn = psycopg.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
)
cursor = conn.cursor()

cursor.execute("""
    SELECT listingid, rawjson, specjson
    FROM listing
    WHERE storeid = 3
    AND (parsed = false OR parsed IS NULL)
    ORDER BY listingid
""")

rows = cursor.fetchall()
for row in rows:
    id = row[0]
    jsondata = row[1]
    spec_json = row[2]
    parse(id, jsondata, spec_json)

conn.close()
print(f"[green]Finished parsing[/green]")