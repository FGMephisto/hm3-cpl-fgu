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


def build_description_paragraphs(
    item: dict,
    pack_label: str,
) -> list[str]:
    """Assemble plain-text description paragraphs for an FGU item."""
    system = item.get("system", {})
    paragraphs: list[str] = []

    desc = (system.get("description") or "").strip()
    if desc:
        for line in desc.splitlines():
            line = line.strip()
            if line:
                paragraphs.append(line)

    notes = (system.get("notes") or "").strip()
    if notes:
        paragraphs.append(f"Notes: {notes}")

    if item.get("type") == "containergear":
        cap = system.get("capacity") or {}
        if "max" in cap and cap["max"] is not None:
            paragraphs.append(f"Capacity: {format_number(cap['max'])} lbs")

    paragraphs.append(f"Vendor: {pack_label}")

    source = (system.get("source") or "").strip()
    if source:
        paragraphs.append(f"Source: {source}")

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

    cost_str = format_cost(system.get("value"))
    if cost_str:
        add_typed_elem(item_el, "cost", "string", cost_str)

    weight = system.get("weight")
    if weight is not None:
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
        add_typed_elem(item_el, "subtype", "string", pack_label)

    elif foundry_type == "miscgear":
        add_typed_elem(item_el, "type", "string", "Adventuring Gear")
        add_typed_elem(item_el, "subtype", "string", pack_label)

    else:
        raise ValueError(f"Unsupported Foundry item type {foundry_type!r} on item {name!r}")

    paragraphs = build_description_paragraphs(item, pack_label)
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

        cat_el = ET.SubElement(item_root, "category", {"name": f"CPL - {pack_label}"})

        lines = [
            line for line in pack_file.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        records = [json.loads(line) for line in lines]
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
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("definition.xml", definition_bytes)
        zf.writestr("client.xml", client_bytes)

    print(
        f"Built {args.output} from hm3-cpl v{upstream_version}: "
        f"{pack_count} categories, {total_validated} items "
        f"({dict(type_counts)})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
