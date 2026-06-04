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

def get_rows():
    cursor.execute("""
            SELECT listingparsedid, manufacturer, coolervariant, gpumodel
            FROM listing_parsed;
        """)
    return cursor.fetchall()


def normalize_model(model):
    if not model:
        return None

    model = model.strip()
    model = re.sub(r"\s+", " ", model)

    # Geforce -> GeForce
    model = re.sub(r"^Geforce\b", "GeForce", model, flags=re.I)

    # RX7700XT -> RX 7700 XT
    model = re.sub(
        r"RX\s*(\d{4})(XT|XTX|GRE)\b",
        r"RX \1 \2",
        model,
        flags=re.I
    )

    # RTX4070Ti -> RTX 4070 Ti
    model = re.sub(
        r"RTX\s*(\d{4})(TI|SUPER)\b",
        r"RTX \1 \2",
        model,
        flags=re.I
    )

    model = re.sub(r"\s+", " ", model)

    model_upper = model.upper()

    if model_upper.startswith("RX "):
        model = f"Radeon {model}"

    elif (
        model_upper.startswith("RTX ")
        or model_upper.startswith("GTX ")
        or model_upper.startswith("GT ")
        or model_upper.startswith("RTX PRO ")
    ):
        model = f"GeForce {model}"

    return model


def normalize_variant(manufacturer, variant):
    if not variant:
        return None

    variant = variant.strip()
    variant = re.sub(r"\s+", " ", variant)

    # obvious garbage
    variant = re.sub(r"^Tarjeta Video\s+", "", variant, flags=re.I)
    variant = re.sub(r"^Computer Corp\s+", "", variant, flags=re.I)

    if (
        len(variant) > 50
        or re.search(r"\d{4,}", variant)
        or "GARANTIA" in variant.upper()
    ):
        return None

    manufacturer = normalize_manufacturer(manufacturer)

    key = variant.upper()

    # XFX family collapsing
    if manufacturer == "XFX":
        if "MERC" in key:
            return "Mercury"

        if "QICK" in key or "QUICKSILVER" in key:
            return "Quicksilver"

        if "SWFT" in key or "SWIFT" in key:
            return "Speedster SWFT"

    # ASUS family collapsing
    if manufacturer == "ASUS":
        if "ROG STRIX" in key:
            return "ROG Strix"

        if "ROG ASTRAL" in key:
            return "ROG Astral"

        if "ROG MATRIX" in key:
            return "ROG Matrix"

        if "TUF" in key:
            return "TUF Gaming"

        if "DUAL" in key:
            return "Dual"

    # MSI family collapsing
    if manufacturer == "MSI":
        if "VENTUS 3X" in key:
            return "Ventus 3X"

        if "VENTUS 2X" in key:
            return "Ventus 2X"

        if "SHADOW 3X" in key:
            return "Shadow 3X"

        if "SHADOW 2X" in key:
            return "Shadow 2X"

        if "GAMING TRIO" in key or key == "TRIO":
            return "Gaming Trio"


    mappings = {
        "GIGABYTE": {
            "AERO": "Aero",
            "EAGLE": "Eagle",
            "EAGLE ICE": "Eagle Ice",
            "EAGLE ICE SFF": "Eagle Ice SFF",
            "EAGLE MAX": "Eagle Max",
            "EAGLEMAX": "Eagle Max",
            "ELITE": "Elite",
            "GAMING": "Gaming",
            "GAMING ICE": "Gaming Ice",
            "WINDFORCE": "Windforce",
            "WINDFORCE MAX": "Windforce Max",
            "WINDFORCE SFF": "Windforce SFF",
            "WINDFORCE V2": "Windforce V2",
            "AORUS MASTER": "AORUS Master",
            "AORUS MASTER ICE": "AORUS Master Ice",
            "XTREME WATERFORCE": "Xtreme Waterforce",
            "LOW PROFILE": "Low Profile",
            "AORUS ELITE": "AORUS Elite",
            "EAGLE SFF": "Eagle SFF",
            "ICE": "Ice",
            "WINDFORCE 2X V2": "Windforce 2X V2",
        },

        "ASUS": {
            "PRIME": "Prime",
            "DUAL": "Dual",
            "DUAL EVO": "Dual Evo",
            "DUAL EVO WHITE": "Dual Evo White",
            "DUAL WHITE": "Dual White",
            "TUF": "TUF",
            "TUF GAMING": "TUF Gaming",
            "TUF WHITE": "TUF White",
            "PROART": "ProArt",
            "ROG STRIX": "ROG Strix",
            "ROG STRIX GAMING": "ROG Strix",
            "ROG MATRIX": "ROG Matrix",
            "ROG MATRIX PLATINUM": "ROG Matrix Platinum",
            "ROG ASTRAL": "ROG Astral",
        },

        "MSI": {
            "VENTUS": "Ventus",
            "VENTUS 2X": "Ventus 2X",
            "VENTUS 2X PLUS": "Ventus 2X Plus",
            "VENTUS 3X": "Ventus 3X",
            "VENTUS 3X PLUS": "Ventus 3X Plus",
            "GAMING TRIO": "Gaming Trio",
            "GAMING X": "Gaming X",
            "SHADOW 2X": "Shadow 2X",
            "SHADOW 3X": "Shadow 3X",
            "INSPIRE 3X": "Inspire 3X",
            "LIGHTNING Z": "Lightning Z",
            "VANGUARD SOC": "Vanguard SOC",
            "LOW PROFILE": "Low Profile",
            "TRIO": "Gaming Trio",
            "VENTUS 2X WHITE": "Ventus 2X White",
            "VENTUS 2X WHITE PLUS": "Ventus 2X White Plus",
            "VENTUS 3X WHITE": "Ventus 3X White",
            "VENTUS 3X BLACK": "Ventus 3X Black",
            "VANGUARD SOC ED": "Vanguard SOC",
            "VANGUARD SOC LAUNCH": "Vanguard SOC",
            "VANGUARD LAUNCH": "Vanguard",
            "SUPRIM SOC": "Suprim SOC",
            "SUPRIM LIQUID SOC": "Suprim Liquid SOC",
            "LP": "Low Profile",
        },

        "POWERCOLOR": {
            "HELLHOUND": "Hellhound",
            "HELLHOUND REVA": "Hellhound",
            "HELLHOUND SPECTRAL": "Hellhound Spectral",
            "HELLHOUND SPECTRAL WHITE": "Hellhound Spectral White",
            "RED DEVIL": "Red Devil",
            "REAPER": "Reaper",
            "FIGHTER": "Fighter",
        },

        "XFX": {
            "MERCURY": "Mercury",
            "QUICKSILVER": "Quicksilver",
            "QUICK SILVER": "Quicksilver",
            "SPEEDSTER MERC": "Speedster Merc",
            "SPEEDSTER QICK": "Speedster QICK",
            "SPEEDSTER SWFT": "Speedster SWFT",
            "SWFT CORE": "Speedster SWFT Core",
            "SWIFT": "Speedster SWFT",
            "SWIFT GAMING": "Speedster SWFT",
            "SWIFT WHITE GAMING": "Speedster SWFT White",
            "SWIFT PRO GAMING": "Speedster SWFT",
            "SWIFT TRIPLE FAN GAMING": "Speedster SWFT",
            "SWIFT WHITE TRIPLE FAN GAMING": "Speedster SWFT White",
            "SPEEDSTER": "Speedster",
            "SPEEDSTER SWFT210": "Speedster SWFT",
            "SPEEDSTER SWFT CORE": "Speedster SWFT Core",
            "MERCURY TRIPLE FAN": "Mercury",
            "MERCURY TRIPLE FAN GAMING": "Mercury",
            "MERCURY GAMING RGB": "Mercury",
            "MERCURY MAGNETIC AIR": "Mercury",
            "WHITE GAMING": "White Gaming",
            "WHITE": "White",
            "QICKSILVER": "Quicksilver",
            "SPEEDTESTER QICK": "Speedster QICK",
            "SPEEDTESTER SWFT": "Speedster SWFT",
                    },

        "ZOTAC": {
            "AMP": "AMP",
            "AMP AIRO": "AMP AIRO",
            "AMP EXTREME": "AMP Extreme",
            "AMP EXTREME AIRO": "AMP Extreme AIRO",
            "AMP EXTREME INFINITY": "AMP Extreme Infinity",
            "AMP WHITE": "AMP White",
            "SOLID": "Solid",
            "SOLID CORE": "Solid Core",
            "SOLID SFF": "Solid SFF",
            "TWIN EDGE": "Twin Edge",
            "TRINITY WHITE": "Trinity White",
            "SOLID WHITE": "Solid White",
            "SOLID CORE WHITE": "Solid Core White",
            "GAMING SOLID": "Solid",
            "GAMING AMP HOLO": "AMP Holo",
            "TWIN EDGE GAMING": "Twin Edge",
        },

        "PNY": {
            "VERTO": "Verto",
            "TF VERTO": "TF Verto",
            "XLR8": "XLR8",
            "ARGB": "ARGB",
            "DUAL FAN": "Dual Fan",
            "DUAL": "Dual Fan",
            "EPIC-X RGB": "EPIC-X RGB",
            "XLR8 GAMING VERTO EPIC-X RGB": "XLR8 Verto",
            "XLR8 RGB": "XLR8",
            "TARJETA VIDEO VERTO": "Verto",
        },

        "ASROCK": {
            "CHALLENGER": "Challenger",
            "CHALLENGER D": "Challenger D",
            "PHANTOM GAMING": "Phantom Gaming",
            "STEEL LEGEND": "Steel Legend",
        },

        "SAPPHIRE": {
            "PULSE": "Pulse",
            "PURE": "Pure",
            "PULSE XT": "Pulse XT",
            "PULSE GAMING": "Pulse Gaming",
            "XL": "XL",
        },

        "INNO3D": {
            "TWIN X2": "Twin X2",
            "TWIN X2 WHITE": "Twin X2 White",
            "X3": "X3",
        }
    }

    key = variant.upper()

    if manufacturer in mappings:
        return mappings[manufacturer].get(key, variant)

    return variant

def normalize_manufacturer(manufacturer):
    if not manufacturer:
        return None

    manufacturer = manufacturer.strip().upper()

    replacements = {
        "POWER COLOR": "POWERCOLOR",
    }

    return replacements.get(manufacturer, manufacturer)    


def update_listing(listingparsedid, manufacturer_normalized, model_normalized, variant_normalized):
    cursor.execute(
        """
        UPDATE listing_parsed
        SET
            manufacturer_normalized = %s,
            gpumodel_normalized = %s,
            coolervariant_normalized = %s,
            product_normalized = TRUE
        WHERE listingparsedid = %s
        """,
        (
            manufacturer_normalized,
            model_normalized,
            variant_normalized,
            listingparsedid,
        ),
    )


def normalize_listing_rows():
    rows = get_rows()

    for row in rows:
        try:
            manufacturer_normalized = normalize_manufacturer(row["manufacturer"])

            model_normalized = normalize_model(row["gpumodel"])

            variant_normalized = normalize_variant(row["manufacturer"], row["coolervariant"])

            update_listing( row["listingparsedid"], manufacturer_normalized, model_normalized, variant_normalized)
            print(f"[green]Updated[/green] {row['listingparsedid']}")

        except Exception as e:
            print(f"[red]Failed[/red] {row['listingparsedid']} -> {e}")

    conn.commit()

if __name__ == "__main__":
    normalize_listing_rows()

    cursor.close()
    conn.close()