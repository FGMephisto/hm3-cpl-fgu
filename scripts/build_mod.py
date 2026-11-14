#!/usr/bin/env python3
"""Convert toastygm/hm3-cpl Foundry VTT packs into an FGU HarnMaster3.5E .mod."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

LOCATION_MAP: dict[str, str] = {
    "Skull": "Sk",
    "Face": "Fa",
    "Neck": "Nk",
    "Shoulder": "Sh",
    "Upper Arm": "Ua",
    "Elbow": "El",
    "Forearm": "Fo",
    "Hand": "Ha",
    "Thorax": "Tx",
    "Abdomen": "Ab",
    "Hip": "Hp",
    "Groin": "Gr",
    "Thigh": "Th",
    "Knee": "Kn",
    "Calf": "Ca",
    "Foot": "Ft",
}

LOCATION_ORDER: list[str] = list(LOCATION_MAP.values())

VALID_ARMOR_MATERIALS: set[str] = {
    "Cloth",
    "Quilt",
    "Leather",
    "Kurbul",
    "Ring",
    "Mail",
    "Scale",
    "Plate",
}

WATERBORNE_VEHICLES: dict[str, str] = {
    "Canoe (1-2 crew, 500 lb. cap.)": "Canoe",
    "Kayak (1 crew, 250 lb. cap.)": "Kayak",
}

DRAWN_VEHICLES: set[str] = {
    "Dogsled, one-man",
    "Hand Cart",
    "Jig, two-man",
    "Palanquin",
    "Sled, child’s",
    "Toboggan",
    "Wheelbarrow",
}

TACK_AND_HARNESS_ITEMS: set[str] = {
    "Blanket, horse",
    "Bridle",
    "Collar, horse",
    "Harness, Horse",
    "Harness, Ox",
    "Pack Harness",
    "Saddle Bag",
    "Saddle, Riding",
    "Saddle, War",
    "Yoke, Ox",
}

MUSICAL_INSTRUMENT_PACKS: set[str] = {
    "Harper",
}

MUSICAL_INSTRUMENT_ITEMS: set[str] = {
    "Clappers, bone",
}

NAVIGATOR_TOOLS_PACKS: set[str] = {
    "Pilot",
}

THIEVES_TOOLS_ITEMS: set[str] = {
    "Hardwood Strips, pack of 12",
    "Hooked wires, pack of 12",
    "Lock craft Kit, portable",
    "Lock pick Kit, large",
    "Lock pick Kit, small",
    "Lock picks, long, pack of 12",
    "Lock picks, short, pack of 12",
    "Mirror, small",
    "Probes, long, pack of 12",
}

GAMING_SET_ITEMS: set[str] = {
    "Dice, pack of 6",
    "Gaming Pieces, 1 in., per dozen",
    "Marbles, Glass, pack of 12",
    "Marbles, Stone, pack of 12",
    "Marbles, glass, pack of 12",
}

ARTISAN_TOOLS_ITEMS: set[str] = {
    "Adze",
    "Axe, Feller’s",
    "Axe, Wood",
    "Bradawl",
    "Branding Iron",
    "Carpentry Kit, portable",
    "Chisel",
    "Coin Balance",
    "Cooking Kit, portable",
    "Crowbar",
    "File, jeweler’s",
    "File, metal",
    "First aid bag w/ instruments",
    "Fishing Kit, portable",
    "Hammer, blacksmith’s",
    "Hammer, carpenter’s",
    "Hammer, jeweler’s",
    "Hand drill",
    "Hatchet, wood",
    "Hideworking Kit, portable",
    "Hoe",
    "Jeweler's File",
    "Jeweler's Hammer",
    "Jeweler's Pliers",
    "Jeweler's Scales",
    "Jeweler's Tweezers",
    "Mortar and Pestle, unglazed stoneware",
    "Pick, miner’s",
    "Pincers, carpenter’s",
    "Pitchfork",
    "Pliers, jeweler’s",
    "Plough, metal blade",
    "Saw, 2-person",
    "Saw, keyhole",
    "Saw, metal",
    "Scales & Weights",
    "Scythe",
    "Sickle",
    "Spade/Shovel",
    "Textile craft kit",
    "Tongs, blacksmith’s",
    "Tweezers, jeweler’s",
    "Wedge, splitting",
    "Wedge, staying",
    "Whetstone",
    "Woodcarving Kit, portable",
    "Writing Kit, portable",
}

HERB_ITEMS: set[str] = {
    "Alanal (Hallucinogen)",
    "Arva (Strength)",
    "Berilik (Anesthetic)",
    "Doshenkana (Poison)",
    "Elprequir (Aphrodisiac)",
    "Fanosel (Narcotic)",
    "Fletharane (Hallucinogen)",
    "Gaethipa (Poison)",
    "Habsulara (Intelligence)",
    "Herb, Common, per oz.",
    "Herb, Rare, per oz.",
    "Herb, Uncommon, per oz.",
    "Herb, Very Rare, per oz.",
    "Hreyochor (Fertility)",
    "Joldraiven (Equine Stimulant)",
    "Kargele (Healing)",
    "Lavaryctia (Sopoforic)",
    "Leortevald (Poison)",
    "Olrui / Monogium (Stimulant)",
    "Perigwar (Aphrodisiac)",
    "Pipe weed",
    "Quessel (Antidote)",
    "Rasakile (Contraceptive)",
    "Stiltrassa (Emetic)",
    "Tasparth (Ordeal Drug)",
    "Teranya (Eye Cure)",
    "Tirgaeth (Narcotic)",
    "Wylorafina (Poison)",
    "Yulpris (Universal Antidote)",
}

MEDICAL_ITEMS: set[str] = {
    "Bandages, per injury level",
    "First aid bag w/ instruments",
    "Herbal Ointments, per injury level",
    "Sutures, per injury level",
}

VEHICLE_COMPONENT_ITEMS: set[str] = {
    "Anchor, large",
    "Anchor, small",
    "Axle",
    "Axle, wagon",
    "Mast per ft",
    "Oar, kayak",
    "Oar, normal",
    "Ski pole",
    "Skis, wooden, per pair",
    "Wheel",
    "Wheel, Ironbound",
}

LIGHTING_ITEMS: set[str] = {
    "Candle Holder",
    "Candle, Calibrated",
    "Candleholder, hand",
    "Candles, Beeswax",
    "Candles, Tallow",
    "Candlestick, iron",
    "Flask of Oil, glass",
    "Flask of Oil, metal",
    "Lamp, enclosed bowl",
    "Lamp, pedestal",
    "Lamp, simple bowl",
    "Lamp. glass",
    "Lantern, metal",
    "Oil, Lamp",
    "Tinderbox",
    "Torch",
}

SPICE_ITEMS: set[str] = {
    "Spice, Alum, per oz.",
    "Spice, Ambergris",
    "Spice, Bdellium",
    "Spice, Bdellium, per oz.",
    "Spice, Camphor",
    "Spice, Camphor, per oz.",
    "Spice, Cinnamon, per oz.",
    "Spice, Frankincense",
    "Spice, Ginger",
    "Spice, Ginseng",
    "Spice, Keddryth",
    "Spice, Lashu Powder",
    "Spice, Marthyn",
    "Spice, Myrrh",
    "Spice, Nard",
    "Spice, Nutmeg",
    "Spice, Pepper",
}

PROVISIONS_PACKS: set[str] = {
    "Innkeeper",
    "Market Butcher",
    "Market Farmer",
    "Market Fisherman",
    "Market Greengrocer",
    "Market Miller",
    "Market Salter",
}

EXCLUDED_PROVISIONS: set[str] = {
    "Fleece",
    "Wool, Raw",
    "Flax",
    "Feathers",
    "Hay",
    "Fishing Kit, portable",
}

EXTRA_PROVISIONS: set[str] = {
    "Tea",
    "Sugar",
    "Oil, Cooking",
    "Fodder",
}

GEM_KEYWORDS: list[str] = [
    "ruby", "pearl", "chrysolite", "agate", "carnelian", "jade", "topaz",
    "emerald", "moonstone", "diamond", "opal", "sapphire", "garnet",
    "bloodstone", "quartz", "onyx", "jet", "amber", "jankorez", "spinel"
]

METALS_KEYWORDS: list[str] = [
    "mithral", "copper", "bronze", "steel", "pewter", "iron", "brass",
    "lead", "gold", "silver", "tin", "zinc"
]

FURNISHING_POTTER_ITEMS: set[str] = {
    "Amphorae / Azeryani", "Amphorae / Karejian", "Amphorae / Lerenil",
    "Baking Dish w/ lid, large", "Baking Dish w/ lid, small", "Baking Dish, large", "Baking Dish, small",
    "Basin, large", "Basin, small", "Bowl, serving, large", "Bowl, serving, medium", "Bowl, serving, small",
    "Chamber Pot", "Drinking beaker", "Drinking cup", "Drinking flagon", "Drinking tankard",
    "Jar, lidded, large", "Jar, lidded, medium", "Jar, lidded, small",
    "Jug, large", "Jug, small", "Pan, chafing", "Pan, dripping", "Pitcher",
    "Pipkin (pot w/ handle), large", "Pipkin (pot w/ handle), medium", "Pipkin (pot w/ handle), small",
    "Plate, dining", "Plate, serving", "Platter", "Pot, cooking, large", "Pot, cooking, small",
    "Pot, infusing", "Skillet", "Urn, Azeryani", "Urn, Hârnic", "Vase"
}

FURNISHING_TABLEWARE_ITEMS: set[str] = {
    "Bowl, pewter", "Cup, pewter", "Goblet, pewter", "Plate, pewter", "Spoon, pewter", "Tankard, pewter",
    "Flagon, wooden", "Bowl, wooden", "Plate, wooden", "Spoon, wooden", "Cup, wooden", "Tankard, wooden"
}

FURNISHING_GENERAL_ITEMS: set[str] = {
    "Bed, bunked", "Bed, double", "Bed, four post", "Bed, short", "Bed, single",
    "Bench", "Bookshelves", "Cabinet", "Chair", "Cot, baby’s", "Couch",
    "Pallet, straw", "Pew, ornate", "Table", "Throne", "Tapestry"
}

TRADE_GOODS_RAW_ITEMS: set[str] = {
    "Bone (for carving)",
    "Fleece",
    "Wool, Raw",
    "Flax",
    "Feathers",
    "Hay",
    "Clay Body, ready to use",
    "Ivory",
    "Whalebone",
    "Horn, Narwhal",
    "Ambergris (fixative)",
}

CONTAINER_SUBTYPE_PREFIXES: tuple[tuple[str, str], ...] = (
    ("backpack", "Backpack"),
    ("back bag", "Backpack"),
    ("belt pouch", "Pouch"),
    ("purse", "Pouch"),
    ("sack", "Sack"),
    ("bag", "Sack"),
    ("lockbox", "Chest"),
)

HORSE_COMMON_NOTES = (
    "Average selling price of a trained steed; untrained yearlings cost roughly half price, "
    "superb horses up to double. Load Rating (Str × 8) is the weight in lbs the horse can carry "
    "without encumbrance penalty (approx. 50 lbs of riding tack before rider mounts)."
)

# Supplemental items not present in upstream toastygm/hm3-cpl packs, keyed by pack label.
SUPPLEMENTAL_ITEMS: dict[str, list[dict]] = {
    "Ostler": [
        {
            "name": "Donkey",
            "type": "mount",
            "system": {
                "value": 420,
                "weight": 600,
                "subtype": "Draft Animal",
                "capacity": 232,
                "speed": "40",
                "description": (
                    "Donkeys originated in the steppes of central Lythia and are sturdy, long-lived, "
                    "and disease-resistant animals capable of surviving long periods with reduced food "
                    "or water. Brave and clever, though stubborn, they are commonly used as pack animals "
                    "or to protect sheep flocks.\n"
                    "Attributes: STR 29, STA 13, AGL 12, EYE 16, HRG 20, SML 18, INT 6, AUR 8, WIL 12, INI 60, END 18, MOV 40, DGE 60\n"
                    "Skills: Trample 60/7b, Bite 48/2p, Awareness 72, Jumping 72, Stealth 60, Swimming 48 | Natural Armour: B4 E3 P1 F3 (except eyes)"
                ),
                "notes": (
                    "Load Rating (Str × 8) is the weight in lbs the donkey can carry without "
                    "encumbrance penalty. Mules (offspring of male donkey and female horse) and "
                    "hinnies (offspring of male horse and female donkey) are sterile."
                ),
            },
        },
        {
            "name": "Horse, Chelni",
            "type": "mount",
            "system": {
                "value": 420,
                "weight": 700,
                "subtype": "Mount",
                "capacity": 216,
                "speed": "40",
                "description": (
                    "A small horse, indigenous to Hârn, bred by the Chelni to carry their warriors "
                    "swiftly over rugged country. Distinguished by a running walk, called the hosk, "
                    "which can reach speeds of sixteen leagues per hour. Although strong and fast, "
                    "the Chelni is too small to be a warhorse for a mounted knight.\n"
                    "Attributes: STR 27, STA 10, AGL 13, EYE 16, HRG 18, SML 18, INT 4, AUR 8, WIL 10, INI 55, END 16, MOV 40, DGE 65\n"
                    "Skills: Trample 60/7b, Awareness 68 | Natural Armour: B4 E3 P1 F3 (except eyes)"
                ),
                "notes": HORSE_COMMON_NOTES,
            },
        },
        {
            "name": "Horse, Hacherdad",
            "type": "mount",
            "system": {
                "value": 600,
                "weight": 1500,
                "subtype": "Mount",
                "capacity": 288,
                "speed": "38",
                "description": (
                    "Originated in the evergreen hardwood forests bordering the eastern Venarian Sea. "
                    "Distinguished by a long mane and tail, Hacherdads have uncanny hearing and are "
                    "highly prized by nobles as mounts for hunting. Although more skittish than Reksyni, "
                    "they make good warhorses unless abused.\n"
                    "Attributes: STR 36, STA 11, AGL 11, EYE 15, HRG 20, SML 18, INT 4, AUR 8, WIL 10, INI 50, END 19, MOV 38, DGE 55\n"
                    "Skills: Trample 55/9b, Awareness 72 | Natural Armour: B4 E3 P1 F3 (except eyes)"
                ),
                "notes": HORSE_COMMON_NOTES,
            },
        },
        {
            "name": "Horse, Hodiri",
            "type": "mount",
            "system": {
                "value": 450,
                "weight": 800,
                "subtype": "Mount",
                "capacity": 224,
                "speed": "42",
                "description": (
                    "Related to the Chelni, the Hodiri horse is taller and faster, and does not gallop "
                    "with the unique hosk gait of the Chelni horse. Hodiri tribesmen use them as warhorses "
                    "and they are popular with ostlers seeking to add speed and endurance to their palfreys.\n"
                    "Attributes: STR 28, STA 11, AGL 12, EYE 16, HRG 18, SML 19, INT 4, AUR 7, WIL 11, INI 55, END 17, MOV 42, DGE 60\n"
                    "Skills: Trample 60/7b, Awareness 72 | Natural Armour: B4 E3 P1 F3 (except eyes)"
                ),
                "notes": HORSE_COMMON_NOTES,
            },
        },
        {
            "name": "Horse, Khanset",
            "type": "mount",
            "system": {
                "value": 360,
                "weight": 1000,
                "subtype": "Mount",
                "capacity": 240,
                "speed": "45",
                "description": (
                    "The “King of Horses” originated on the great plains of central Lythia. They are "
                    "fearless and extremely protective of their owners, a natural disposition that has been "
                    "enhanced through breeding. They are too light to easily bear the weight of a heavily "
                    "armoured warrior, but are superb mounts for light cavalry and extremely popular as palfreys.\n"
                    "Attributes: STR 30, STA 9, AGL 13, EYE 17, HRG 19, SML 19, INT 5, AUR 9, WIL 12, INI 60, END 17, MOV 45, DGE 65\n"
                    "Skills: Trample 65/8b, Awareness 72 | Natural Armour: B4 E3 P1 F3 (except eyes)"
                ),
                "notes": HORSE_COMMON_NOTES,
            },
        },
        {
            "name": "Horse, Lankum",
            "type": "mount",
            "system": {
                "value": 480,
                "weight": 1200,
                "subtype": "Mount",
                "capacity": 256,
                "speed": "40",
                "description": (
                    "Originating in the Quarphor region of Lythia, the Lankum are a light-boned, strong "
                    "steed, popular as a palfrey or light charger. Distantly related to the Reksyni, the "
                    "Lankum is lighter and faster than its cousin. Half of all Lankums are “painted horses,” "
                    "usually shades of brown and white.\n"
                    "Attributes: STR 32, STA 10, AGL 12, EYE 16, HRG 18, SML 20, INT 4, AUR 7, WIL 11, INI 55, END 18, MOV 40, DGE 60\n"
                    "Skills: Trample 60/8b, Awareness 72 | Natural Armour: B4 E3 P1 F3 (except eyes)"
                ),
                "notes": HORSE_COMMON_NOTES,
            },
        },
        {
            "name": "Horse, Reksyni",
            "type": "mount",
            "system": {
                "value": 800,
                "weight": 1800,
                "subtype": "Mount",
                "capacity": 320,
                "speed": "36",
                "description": (
                    "A large and sturdy breed, known for rugged countenance, size, and endurance. Fearless "
                    "and loyal, the Reksyni is the most popular warhorse found in feudal cultures that favor "
                    "heavy and medium cavalry. They are extremely popular in Hârn.\n"
                    "Attributes: STR 40, STA 12, AGL 11, EYE 16, HRG 17, SML 20, INT 5, AUR 8, WIL 12, INI 60, END 21, MOV 36, DGE 55\n"
                    "Skills: Trample 55/10b, Awareness 72 | Natural Armour: B4 E3 P1 F3 (except eyes)"
                ),
                "notes": HORSE_COMMON_NOTES,
            },
        },
    ],
}

ROOT_ATTRS = {
    "version": "5.1",
    "dataversion": "20260124",
    "release": "5|CoreRPG:8",
}


def format_number(value: float | int) -> str:
    """Format an int/float cleanly without trailing .0 for whole numbers."""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


def format_cost(value: float | int | None) -> str:
    """Format Foundry pence value into FGU HarnMaster cost string (e.g. '570d')."""
    if value is None:
        return ""
    return f"{format_number(value)}d"


def format_coverage(locations: list[str]) -> str:
    """Convert Foundry location names into space-separated FGU 2-letter codes."""
    codes: set[str] = set()
    for loc in locations:
        code = LOCATION_MAP.get(loc)
        if not code:
            raise ValueError(f"Unknown armor location: {loc!r}")
        codes.add(code)
    ordered = [code for code in LOCATION_ORDER if code in codes]
    return " ".join(ordered)


def add_typed_elem(parent: ET.Element, tag: str, elem_type: str, text: str) -> ET.Element:
    """Append a typed FGU XML leaf element."""
    el = ET.SubElement(parent, tag, {"type": elem_type})
    el.text = text
    return el


def resolve_container_subtype(name: str) -> str:
    """Map a container item name to a HarnMaster3.5E container subtype, or '' if none."""
    lowered = name.lower()
    for prefix, subtype in CONTAINER_SUBTYPE_PREFIXES:
        if lowered.startswith(prefix):
            return subtype
    return ""


def classify_miscgear(name: str, pack_label: str) -> tuple[str, str]:
    """Return (type, subtype) for a Foundry miscgear item."""
    nl = name.lower()

    if name in HERB_ITEMS:
        return ("Herbs", "")
    if name in MEDICAL_ITEMS:
        return ("Medical", "")
    if name in VEHICLE_COMPONENT_ITEMS:
        return ("Vehicle Component", "")
    if name in SPICE_ITEMS:
        return ("Trade Goods", "Spices")
    if name in LIGHTING_ITEMS:
        return ("Adventuring Gear", "Lighting")
    if name in EXTRA_PROVISIONS or (pack_label in PROVISIONS_PACKS and name not in EXCLUDED_PROVISIONS):
        return ("Provisions", "")
    if name in FURNISHING_GENERAL_ITEMS or name in FURNISHING_POTTER_ITEMS or name in FURNISHING_TABLEWARE_ITEMS:
        return ("Furnishings", "")
    if any(gw in nl for gw in GEM_KEYWORDS) and not any(m in nl for m in METALS_KEYWORDS) and "jeweler" not in nl:
        return ("Gems", "")
    if (
        pack_label in {"Miner", "Timerwright", "Dyer"}
        or name in TRADE_GOODS_RAW_ITEMS
        or (pack_label == "Clothier" and name.startswith("Bolt of cloth"))
        or (pack_label == "Jeweler" and any(m in nl for m in METALS_KEYWORDS + ["glass", "ivory", "bone/horn"]))
    ):
        return ("Trade Goods", "")
    if name in WATERBORNE_VEHICLES:
        return ("Waterborne Vehicles", WATERBORNE_VEHICLES[name])
    if name in DRAWN_VEHICLES:
        return ("Tack, Harness, And Drawn Vehicles", "Drawn Vehicle")
    if name in TACK_AND_HARNESS_ITEMS:
        return ("Tack, Harness, And Drawn Vehicles", "Tack & Harness")
    if pack_label in MUSICAL_INSTRUMENT_PACKS or name in MUSICAL_INSTRUMENT_ITEMS:
        return ("Musical Instrument", "")
    if pack_label in NAVIGATOR_TOOLS_PACKS:
        return ("Tools", "Navigator's Tools")
    if name in THIEVES_TOOLS_ITEMS:
        return ("Tools", "Thieves' Tools")
    if name in GAMING_SET_ITEMS:
        return ("Tools", "Gaming Set")
    if name in ARTISAN_TOOLS_ITEMS:
        return ("Tools", "Artisan's Tools")
    return ("Adventuring Gear", "")


def parse_pricing_unit(notes: str) -> tuple[str, str]:
    """Extract a pricing unit (e.g. 'per lb.', 'per oz.') from notes.

    Returns (unit_suffix, remaining_notes).
    """
    notes = notes.strip()
    if not notes.startswith("per "):
        return ("", notes)

    if notes.startswith("per ct.^"):
        return ("", notes)

    # Check for compound notes like 'per ft., 1000 lb. capacity' or 'per gal., 32 hr. duration'
    if ", " in notes:
        unit_part, rest = notes.split(", ", 1)
        # Unit part like 'per ft.' -> '/ ft.'
        suffix = " / " + unit_part[4:].strip()
        return (suffix, rest.strip())

    suffix = " / " + notes[4:].strip()
    return (suffix, "")


def build_description_paragraphs(item: dict) -> list[str]:
    """Assemble plain-text description paragraphs for an FGU item."""
    system = item.get("system", {})
    paragraphs: list[str] = []

    desc = (system.get("description") or "").strip()
    notes = (system.get("notes") or "").strip()

    # Clean up typos in notes
    notes = notes.replace("capacty", "capacity").replace("capactiy", "capacity")

    # Bedroll shorthand clarification
    if notes.lower() == "freezing":
        notes = "Protection: suitable for freezing temperatures"
    elif notes.lower() == "cool":
        notes = "Protection: suitable for cool temperatures"

    # Tent frame weight & dimensions combination
    if "frame" in desc.lower() and ("capacity" in notes.lower() or "ft." in notes.lower()):
        paragraphs.append(f"Dimensions / Specs: {notes}")
        paragraphs.append(f"Frame: {desc}")
        return paragraphs

    # Special handling for gems priced per carat
    if "typical weights range" in desc.lower():
        clean_desc = desc
        if clean_desc.lower().startswith("typical weights range"):
            clean_desc = "Typical weight range: " + clean_desc[len("typical weights range"):].strip()
        paragraphs.append(clean_desc)

        if notes:
            if notes == "per ct.":
                paragraphs.append("Pricing: per carat (total price = carats × base cost)")
            elif notes.startswith("per ct.^"):
                exp = notes.split("^")[-1]
                paragraphs.append(f"Pricing: per carat^{exp} (exponential value scaling by weight)")
            else:
                paragraphs.append(f"Notes: {notes}")
        return paragraphs

    if desc:
        for line in desc.splitlines():
            line = line.strip()
            if line:
                paragraphs.append(line)

    if notes:
        unit_suffix, remaining_notes = parse_pricing_unit(notes)
        if notes.startswith("per ct.^"):
            exp = notes.split("^")[-1]
            paragraphs.append(f"Pricing: per carat^{exp} (exponential value scaling by weight)")
        elif remaining_notes:
            paragraphs.append(f"Notes: {remaining_notes}")
        elif not unit_suffix:
            paragraphs.append(f"Notes: {notes}")

    return paragraphs


def add_formatted_description(parent: ET.Element, paragraphs: list[str]) -> None:
    """Add an FGU <description type='formattedtext'> element."""
    if not paragraphs:
        return
    desc_el = ET.SubElement(parent, "description", {"type": "formattedtext"})
    for para in paragraphs:
        p = ET.SubElement(desc_el, "p")
        p.text = para


def convert_item(
    item: dict,
    node_id: str,
    pack_label: str,
) -> ET.Element:
    """Convert one Foundry hm3-cpl JSON record into an FGU <id-XXXXX> element."""
    system = item.get("system", {})
    foundry_type = item.get("type", "")
    name = (item.get("name") or "").strip()

    item_el = ET.Element(node_id)
    add_typed_elem(item_el, "name", "string", name)
    add_typed_elem(item_el, "nonid_name", "string", name)
    add_typed_elem(item_el, "version", "string", "2024")
    add_typed_elem(item_el, "vendor", "string", pack_label)

    cost_str = format_cost(system.get("value"))
    notes = (system.get("notes") or "").strip()
    unit_suffix, _ = parse_pricing_unit(notes)
    if cost_str:
        if unit_suffix:
            cost_str += unit_suffix
        add_typed_elem(item_el, "cost", "string", cost_str)

    weight = system.get("weight")
    if weight is not None:
        notes = (system.get("notes") or "").strip()
        # Gems priced per carat have fractional carats converted to 0.0004 lbs in Foundry; set to 0 in FGU
        if "per ct" in notes or "carat" in (system.get("description") or "").lower():
            add_typed_elem(item_el, "weight", "number", "0")
        else:
            add_typed_elem(item_el, "weight", "number", format_number(weight))

    if foundry_type == "armorgear":
        material = (system.get("material") or "").strip()
        if material not in VALID_ARMOR_MATERIALS:
            raise ValueError(f"Unexpected armor material {material!r} on item {name!r}")

        prot = system.get("protection") or {}
        add_typed_elem(item_el, "type", "string", "Armor")
        add_typed_elem(item_el, "subtype", "string", material)
        add_typed_elem(item_el, "armor_blunt", "number", str(int(prot.get("blunt", 0))))
        add_typed_elem(item_el, "armor_edge", "number", str(int(prot.get("edged", 0))))
        add_typed_elem(item_el, "armor_point", "number", str(int(prot.get("piercing", 0))))
        add_typed_elem(item_el, "armor_fire", "number", str(int(prot.get("fire", 0))))

        coverage = format_coverage(system.get("locations") or [])
        if coverage:
            add_typed_elem(item_el, "armor_coverage", "string", coverage)

    elif foundry_type == "containergear":
        add_typed_elem(item_el, "type", "string", "Container")
        container_subtype = resolve_container_subtype(name)
        if container_subtype:
            add_typed_elem(item_el, "subtype", "string", container_subtype)
        cap = system.get("capacity") or {}
        if "max" in cap and cap["max"] is not None:
            add_typed_elem(item_el, "capacity", "string", f"{format_number(cap['max'])} lbs")

    elif foundry_type == "miscgear":
        item_type, item_subtype = classify_miscgear(name, pack_label)
        add_typed_elem(item_el, "type", "string", item_type)
        if item_subtype:
            add_typed_elem(item_el, "subtype", "string", item_subtype)

    elif foundry_type == "mount":
        add_typed_elem(item_el, "type", "string", "Mounts and Other Animals")
        mount_subtype = (system.get("subtype") or "Mount").strip()
        if mount_subtype:
            add_typed_elem(item_el, "subtype", "string", mount_subtype)
        load_cap = system.get("capacity")
        if load_cap is not None:
            cap_str = f"{format_number(load_cap)} lbs"
            add_typed_elem(item_el, "capacity", "string", cap_str)
            add_typed_elem(item_el, "carryingcapacity", "string", cap_str)
        speed = (system.get("speed") or "").strip()
        if speed:
            add_typed_elem(item_el, "speed", "string", speed)

    else:
        raise ValueError(f"Unsupported Foundry item type {foundry_type!r} on item {name!r}")

    paragraphs = build_description_paragraphs(item)
    add_formatted_description(item_el, paragraphs)

    return item_el


def build_definition_xml(upstream_version: str) -> bytes:
    """Generate definition.xml bytes for the FGU module."""
    root = ET.Element("root", ROOT_ATTRS)
    ET.SubElement(root, "name").text = "HarnMaster Comprehensive Pricelist"
    ET.SubElement(root, "category").text = "Equipment"
    ET.SubElement(root, "author").text = f"Toasty / Scythen (hm3-cpl v{upstream_version}, FGU conversion)"
    ET.SubElement(root, "ruleset").text = "HarnMaster3.5E"
    ET.indent(root, space="\t")
    return b'<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="utf-8") + b"\n"


def build_library_section(root: ET.Element) -> None:
    """Add <library> index entry so the module appears in FGU's Library window."""
    lib = ET.SubElement(root, "library")
    mod_node = ET.SubElement(lib, "harnmastercomprehensivepricelist", {"static": "true"})
    add_typed_elem(mod_node, "categoryname", "string", "Equipment")
    add_typed_elem(mod_node, "name", "string", "harnmastercomprehensivepricelist")

    entries = ET.SubElement(mod_node, "entries")
    item_entry = ET.SubElement(entries, "item")
    link = ET.SubElement(item_entry, "librarylink", {"type": "windowreference"})
    ET.SubElement(link, "class").text = "reference_list"
    ET.SubElement(link, "recordname").text = ".."
    add_typed_elem(item_entry, "name", "string", "Items")
    add_typed_elem(item_entry, "recordtype", "string", "item")


def build_client_xml(upstream_dir: Path) -> tuple[bytes, Counter[str], int]:
    """Generate client.xml bytes and return (xml_bytes, type_counts, pack_count)."""
    manifest = json.loads((upstream_dir / "module.json").read_text(encoding="utf-8"))
    packs = manifest["packs"]

    root = ET.Element("root", ROOT_ATTRS)
    item_root = ET.SubElement(root, "item")

    type_counts: Counter[str] = Counter()
    next_id = 1

    for pack in packs:
        pack_label = pack["label"].strip()
        pack_file = upstream_dir / f"{pack['path']}.db"
        if not pack_file.is_file():
            raise FileNotFoundError(f"Missing pack database file: {pack_file}")

        cat_el = ET.SubElement(item_root, "category", {"name": pack_label})

        lines = [
            line for line in pack_file.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        records = [json.loads(line) for line in lines]
        records.extend(SUPPLEMENTAL_ITEMS.get(pack_label, []))
        records.sort(key=lambda r: (r.get("name") or "").lower())

        for rec in records:
            node_id = f"id-{next_id:05d}"
            next_id += 1
            cat_el.append(convert_item(rec, node_id, pack_label))
            type_counts[rec.get("type", "unknown")] += 1

    build_library_section(root)
    ET.indent(root, space="\t")
    xml_bytes = b'<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="utf-8") + b"\n"
    return xml_bytes, type_counts, len(packs)


def validate_xml(xml_bytes: bytes) -> int:
    """Re-parse generated client.xml and ensure all <id-*> item IDs are unique."""
    root = ET.fromstring(xml_bytes)
    seen_ids: set[str] = set()
    for cat in root.findall("./item/category"):
        for child in cat:
            if child.tag in seen_ids:
                raise AssertionError(f"Duplicate item node id: {child.tag}")
            seen_ids.add(child.tag)
    return len(seen_ids)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    default_upstream = repo_root / "upstream" / "hm3-cpl"
    default_output = repo_root.parent / "HarnMaster3.5E_CPL.mod"

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--upstream",
        type=Path,
        default=default_upstream,
        help="Path to upstream hm3-cpl checkout (default: upstream/hm3-cpl)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help="Output .mod path (default: ../HarnMaster3.5E_CPL.mod)",
    )
    args = parser.parse_args()

    manifest = json.loads((args.upstream / "module.json").read_text(encoding="utf-8"))
    upstream_version = manifest.get("version", "unknown")

    definition_bytes = build_definition_xml(upstream_version)
    client_bytes, type_counts, pack_count = build_client_xml(args.upstream)
    total_validated = validate_xml(client_bytes)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    thumb_path = repo_root / "assets" / "thumbnail.png"
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("definition.xml", definition_bytes)
        zf.writestr("client.xml", client_bytes)
        if thumb_path.is_file():
            zf.write(thumb_path, "thumbnail.png")

    print(
        f"Built {args.output} from hm3-cpl v{upstream_version}: "
        f"{pack_count} categories, {total_validated} items "
        f"({dict(type_counts)})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
