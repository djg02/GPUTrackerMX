from rich import print
from dotenv import load_dotenv
import json
import os
import psycopg
import re
load_dotenv()

def get_spec(spec_json, group, readable_id):
    items = spec_json.get(group, [])
    for item in items:
        if item.get("readableId") == readable_id:
            return item.get("value")
    return None


def parse (id, jsondata, spec_json):
    try:
        #data extraction and parsing
        title = re.sub(r'[®™]', '', jsondata.get("title", "")).strip()
        title = re.sub(r'\s+', ' ', title)
        chipsetbrand = get_spec(spec_json, "Procesador", "familia_de_procesadores_de_graficos")
        manufacturer = jsondata.get("brand", {}).get("title")
        gpumodel = get_spec(spec_json, "Procesador", "procesador_grafico")
        series =  get_spec(spec_json, "Diseño", "serie_de_tarjeta_de_video")
        oc = get_spec(spec_json, "Desempeño", "overclocked_(oc)_edition") == "Si" or "OC" in title
        color = get_spec(spec_json, "Diseño", "color_del_producto")
        vramgb_raw = get_spec(spec_json, "Memoria", "graficos_discretos_memoria_del_adaptador")
        vramgb = int(re.sub(r'[^\d]', '', vramgb_raw)) if vramgb_raw else None
        memorytype = get_spec(spec_json, "Memoria", "tipo_de_memoria_de_adaptador_grafico")
        buswidth_raw = get_spec(spec_json, "Memoria", "ancho_de_datos")
        buswidth = int(re.sub(r'[^\d]', '', buswidth_raw)) if buswidth_raw else None
        interfaceversion_raw = get_spec(spec_json, "Puertos e Interfaces", "tipo_de_interfaz")
        interfaceversion = re.sub(r'x\d+\s*', '', interfaceversion_raw.replace("PCI Express ", "")).strip() if interfaceversion_raw else None
        fans = get_spec(spec_json, "Diseño", "numero_de_ventiladores")
        fans = int(fans) if fans and fans.isdigit() else None
        sku = jsondata.get("sku")
        listingid = id
        boostclock_raw = (
            get_spec(spec_json, "Procesador", "processor_boost_clock_speed_(oc_mode)") or
            get_spec(spec_json, "Procesador", "aumento_de_la_velocidad_de_reloj_del_procesador"))
        baseclock_raw = get_spec(spec_json, "Procesador", "processor_frequency_(oc_mode)")
        boostclock = int(re.sub(r'[^\d]', '', boostclock_raw)) if boostclock_raw else None
        baseclock = int(re.sub(r'[^\d]', '', baseclock_raw)) if baseclock_raw else None
        coolervariant = parse_cooler_variant(title, manufacturer, chipsetbrand, gpumodel, vramgb_raw, buswidth_raw, memorytype, interfaceversion_raw)
        
        cursor.execute("""
            INSERT INTO public.listing_parsed (
                listingid, manufacturer, chipset_brand, gpumodel, series,
                oc, vramgb, memorytype, buswidth, interfaceversion,
                coolervariant, color, sku, title, fans, boostclock, baseclock, parsedat
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, NOW()
            )
            ON CONFLICT (listingid) DO UPDATE SET
                manufacturer = EXCLUDED.manufacturer,
                chipset_brand = EXCLUDED.chipset_brand,
                gpumodel = EXCLUDED.gpumodel,
                series = EXCLUDED.series,
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
            id, manufacturer, chipsetbrand, gpumodel, series,
            oc, vramgb, memorytype, buswidth, interfaceversion,
            coolervariant, color, sku, title, fans, boostclock, baseclock
        ))

        cursor.execute("""
        UPDATE public.listing
        SET parsed = true, parsedat = now()
        WHERE listingid = %s
        """, (id,))
        print(f"[green]Parsed and saved {title} [/green]")

    except Exception as e:
        conn.rollback()
        print(f"[red]Failed on listingid {id}: {e}[/red]")

def parse_cooler_variant(title, manufacturer, chipsetbrand, gpumodel, vramgb_raw, buswidth_raw, memorytype, interfaceversion_raw):
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
    s = re.sub(r'\b(?:RTX|GTX|RX|Arc)?\s*\d{3,4}(?:\s*(?:Ti|XT|XTX|SUPER))?\b', '', s, flags=re.IGNORECASE).strip()

    # 3e. Strip leading/trailing commas, dashes, punctuation
    s = re.sub(r'^[\s,\-]+|[\s,\-]+$', '', s).strip()

    # 4. Remove spec suffixes (with or without leading number, handles ", -bit GDDR6" remnants)
    s = re.sub(r',?\s*\d*\s*-?\s*bit\s+\w+.*$', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r',?\s*PCI Express[\s\w.x]*.*$', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\s*-\s*incluye.*$', '', s, flags=re.IGNORECASE).strip()

    # 4a. Clean up leading/trailing commas again after suffix removal
    s = re.sub(r'^[\s,\-]+|[\s,\-]+$', '', s).strip()

    # 4b. Remove any remaining PCI Express / GDDR spec fragments
    s = re.sub(r',?\s*PCI Express[\s\w.x]*$', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r',?\s*\d+-bit\s+\w+$', '', s, flags=re.IGNORECASE).strip()

    # 4c. Strip standalone "x" leftover from x16 stripping  
    s = re.sub(r'(?<!\w)x(?!\w)', '', s, flags=re.IGNORECASE).strip()

    # 4d. Remove long parenthetical or dash-separated spec descriptions
    s = re.sub(r'\s*-\s*incluye.*$', '', s, flags=re.IGNORECASE).strip()

    # 4e. Strip fan descriptions
    s = re.sub(r'\b(?:Triple|Doble|Single|Dual|Doble)\s+Ventilador(?:es)?\b', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\b\d+\s*Ventilador(?:es)?\b', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\bTriple\s+Fan\b|\bDual\s+Fan\b|\bSingle\s+Fan\b', '', s, flags=re.IGNORECASE).strip()

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
    WHERE storeid = 2
    AND (parsed = false OR parsed IS NULL)
    ORDER BY listingid
""")

rows = cursor.fetchall()
for row in rows:
    id = row[0]
    jsondata = row[1]
    specjson = row[2]
    coolervariant = parse(id, jsondata, specjson)

conn.commit()
conn.close()
print(f"[green] Finished parsing [/green]")
