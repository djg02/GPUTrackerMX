from rich import print
from dotenv import load_dotenv
import os
import psycopg
import re
import unicodedata
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
            SELECT listingparsedid, manufacturer, coolervariant, gpumodel, color, title
            FROM listing_parsed
            WHERE product_normalized = FALSE;
        """)
    return cursor.fetchall()


def normalize_model(model):
    if not model:
        return None
    
    model = unicodedata.normalize("NFKC", model)

    # Remove soft hyphens and other invisible formatting chars
    model = model.replace("\u00AD", "")  # soft hyphen

    # Remove all Unicode format characters (Cf)
    model = "".join(
        c for c in model
        if unicodedata.category(c) != "Cf"
    )

    model = model.strip()
    model = re.sub(r"\s+", " ", model)

    # Geforce -> GeForce
    model = re.sub(r"^Geforce\b", "GeForce", model, flags=re.I)

    # RX7700XT -> RX 7700 XT
    model = re.sub(
        r"RX\s*(\d{4})(XTX|XT|GRE)\b",
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

WHITE_VARIANT_EXCEPTIONS = {
    "AORUS MASTER ICE",
    "MASTER ICE",
    "EAGLE ICE",
    "EAGLE ICE SFF",
    "GAMING ICE",
    "ICE",
    "ICE BLANCO",
    "HELLHOUND SPECTRAL WHITE",
}

def normalize_color(color, title=None):
    # explicit color field wins
    if color:
        value = color.upper().strip()

        replacements = {
            "Á": "A",
            "É": "E",
            "Í": "I",
            "Ó": "O",
            "Ú": "U",
        }

        for old, new in replacements.items():
            value = value.replace(old, new)

        WHITE_COLORS = {
            "WHITE",
            "BLANCO",
            "WHITE EDITION",
            "WHITE OC",
        }

        if value in WHITE_COLORS:
            return "White"

    # fallback to title
    if title:
        title_upper = title.upper()

        WHITE_KEYWORDS = (
            " WHITE ",
            " BLANCO ",
            " AMP WHITE ",
            " TWIN EDGE WHITE ",
            " SOLID WHITE ",
            " SOLID CORE WHITE ",
            " TRINITY WHITE ",
            " GAMING TRIO WHITE ",
            " VENTUS WHITE ",
            " DUAL WHITE ",
            " TUF WHITE ",
        )

        padded = f" {title_upper} "

        for keyword in WHITE_KEYWORDS:
            if keyword in padded:
                return "White"

    return None

def extract_variant_color(variant):
    if not variant:
        return None

    key = variant.upper().strip()

    if key in WHITE_VARIANT_EXCEPTIONS:
        return None

    if (
        "WHITE" in key
        or "BLANCO" in key
    ):
        return "White"

    return None

def strip_color_from_variant(variant):
    if not variant:
        return variant

    key = variant.upper().strip()

    if key in WHITE_VARIANT_EXCEPTIONS:
        return variant

    variant = re.sub(r"\bWHITE\b", "", variant, flags=re.I)
    variant = re.sub(r"\bBLANCO\b", "", variant, flags=re.I)

    variant = re.sub(r"\s+", " ", variant).strip()

    return variant

def normalize_variant(manufacturer, variant):
    if not variant:
        return None

    variant = variant.strip()
    variant = re.sub(r"\s+", " ", variant)
    variant = strip_color_from_variant(variant)

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
            "AORUS MASTER LHR": "Aorus Master LHR",
            "AORUS XTREME LHR": "Aorus Xtreme LHR",
            "XTREME WATERFORCE": "Xtreme Waterforce",
            "LOW PROFILE": "Low Profile",
            "AORUS ELITE": "AORUS Elite",
            "EAGLE SFF": "Eagle SFF",
            "ICE": "Ice",
            "WINDFORCE 2X V2": "Windforce 2X V2",
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
            "ROG ASTRAL HATSUNE MIKU" : "ROG Astral Hatsune Miku",
            "ROG ASTRAL": "ROG Astral",
            "90YV0LWA-MVAA00": "ROG Astral"
        },

        "MSI": {
            "VENTUS": "Ventus",
            "VENTUS 2X": "Ventus 2X",
            "VENTUS 2X PLUS": "Ventus 2X Plus",
            "VENTUS 3X": "Ventus 3X",
            "VENTUS 3X PLUS": "Ventus 3X Plus",
            "GAMING TRIO": "Gaming Trio",
            "GAMING TRIO PLUS": "Gaming Trio Plus",
            "GAMING TRIO WHITE": "Gaming Trio White",
            "GAMING X": "Gaming X",
            "SHADOW 2X": "Shadow 2X",
            "SHADOW 3X": "Shadow 3X",
            "INSPIRE 3X": "Inspire 3X",
            "INSPIRE 3X PLUS": "Inspire 3X Plus",
            "LIGHTNING Z": "Lightning Z",
            "VANGUARD SOC": "Vanguard SOC",
            "LOW PROFILE": "Low Profile",
            "TRIO": "Gaming Trio",
            "TRIO WHITE": "Gaming Trio White",
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
            "MLG EDITION": "MLG Edition",
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
            "SPEEDTESTER QICK": "Speedster QICK",
            "SPEEDTESTER SWFT": "Speedster SWFT",
            "SWFT CORE": "Speedster SWFT Core",
            "SWIFT": "Speedster SWFT",
            "SWIFT GAMING": "Speedster SWFT",
            "SWIFT WHITE GAMING": "Speedster SWFT White",
            "SWIFT PRO GAMING": "Speedster SWFT",
            "SWIFT TRIPLE FAN GAMING": "Speedster SWFT",
            "SWIFT TRIPLE FAN GAMING EDITON": "Speedster SWFT",
            "SWIFT WHITE TRIPLE FAN GAMING": "Speedster SWFT White",
            "SWIFT WHITE TRIPLE FAN GAMING EDITON": "Speedster SWFT White",
            "SPEEDSTER SWFT210": "Speedster SWFT",
            "SPEEDSTER SWFT CORE": "Speedster SWFT Core",
            "SPEEDSTER SWIFT TRIPLE FAN": "Speedster SWFT",
            "MERCURY TRIPLE FAN": "Mercury",
            "MERCURY TRIPLE FAN GAMING": "Mercury",
            "MERCURY GAMING RGB": "Mercury",
            "MERCURY MAGNETIC AIR": "Mercury",
            "WHITE GAMING EDITION": "Quicksilver White",
            "WHITE GAMING": "Quicksilver White",
            "GAMING EDITION": "Quicksilver",
            "GAMING": "Quicksilver",
            "QICKSILVER": "Quicksilver",
            "MERC": "Speedster Merc",
            "QICK": "Speedster QICK",
            "SWFT WHITE": "Speedster SWFT White",
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
            "GAMING TWIN EDGE": "Twin Edge",
            "TWIN EDGE OC": "Twin Edge",
            "TWIN EDGE WHITE": "Twin Edge White",
            "TWIN EDGE WHITE OC": "Twin Edge White",
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
            "OC EDITION": "OC Edition",
            "OVERCLOCKED": "OC Edition",
        },

        "ASROCK": {
            "CHALLENGER": "Challenger",
            "CHALLENGER D": "Challenger D",
            "PHANTOM GAMING": "Phantom Gaming",
            "STEEL LEGEND": "Steel Legend",
            "CHALLENGER ITX": "Challenger ITX",
            "PHANTOM GAMING D": "Phantom Gaming",
            "PHANTOM GAMING OC": "Phantom Gaming",

        },

        "SAPPHIRE": {
            "PULSE": "Pulse",
            "PURE": "Pure",
            "PULSE XT": "Pulse XT",
            "PULSE GAMING": "Pulse Gaming",
            "XL": "XL",
            "NITRO+ GAMING OC": "Nitro+",
            "NITRO+ OC": "Nitro+",
            "PURE OC": "Pure",
            "PULSE OC": "Pulse",
        },

        "INNO3D": {
            "TWIN X2": "Twin X2",
            "TWIN X2 WHITE": "Twin X2 White",
            "X3": "X3",
            "ICHILL X3": "Ichill X3",
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

    key = variant.upper()

    manufacturer_map = mappings.get(manufacturer)

    if manufacturer_map:
        for pattern, normalized in sorted(
            manufacturer_map.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            if pattern in key:
                return normalized

    return variant

def normalize_manufacturer(manufacturer):
    if not manufacturer:
        return None

    manufacturer = manufacturer.strip().upper()

    replacements = {
        "POWER COLOR": "POWERCOLOR",
    }

    return replacements.get(manufacturer, manufacturer)    


def update_listing(listingparsedid, manufacturer_normalized, model_normalized, variant_normalized, color_normalized):
    cursor.execute(
        """
        UPDATE listing_parsed
        SET
            manufacturer_normalized = %s,
            gpumodel_normalized = %s,
            coolervariant_normalized = %s,
            color_normalized = %s,
            product_normalized = TRUE
        WHERE listingparsedid = %s
        """,
        (   
            manufacturer_normalized,
            model_normalized,
            variant_normalized,
            color_normalized,
            listingparsedid,
        ),
    )


def normalize_listing_rows():
    rows = get_rows()

    for row in rows:
        try:
            color_normalized = normalize_color(row["color"], row["title"])
            manufacturer_normalized = normalize_manufacturer(row["manufacturer"])

            model_normalized = normalize_model(row["gpumodel"])

            variant_normalized = normalize_variant(row["manufacturer"], row["coolervariant"])

            update_listing(row["listingparsedid"], manufacturer_normalized, model_normalized, variant_normalized, color_normalized)
            print(f"[green]Updated[/green] {row['listingparsedid']}")

        except Exception as e:
            print(f"[red]Failed[/red] {row['listingparsedid']} -> {e}")

    conn.commit()

if __name__ == "__main__":
    normalize_listing_rows()

    cursor.close()
    conn.close()