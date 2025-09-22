from __future__ import annotations

from typing import Any, Dict, cast
import lxml.etree as ET


AKN_NS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
NSMAP = {None: AKN_NS}


class AKNError(ValueError):
    pass


def transform_to_akn(doc: Dict[str, Any]) -> bytes:
    """Transform our JSON result into minimal Akoma Ntoso XML.

    Expected input keys:
      - metadata: dict with at least title and jurisdiction (optional)
      - content: list of blocks/sections with id, heading, text
    """
    meta = doc.get("metadata", {})
    title = meta.get("title", "Untitled Document")
    jurisdiction = meta.get("jurisdiction", "")

    root = ET.Element("akomaNtoso", nsmap=NSMAP)
    act = ET.SubElement(root, "act")

    meta_el = ET.SubElement(act, "meta")
    # identification
    identification = ET.SubElement(meta_el, "identification")
    frbr_work = ET.SubElement(identification, "FRBRWork")
    ET.SubElement(frbr_work, "FRBRthis", value=f"/akn/{jurisdiction}/act/unknown")
    ET.SubElement(frbr_work, "FRBRuri", value=f"/akn/{jurisdiction}/act")
    ET.SubElement(frbr_work, "FRBRdate", date="1900-01-01")
    ET.SubElement(frbr_work, "FRBRauthor", href=f"/{jurisdiction}")
    ET.SubElement(frbr_work, "FRBRcountry", value=jurisdiction)

    # main body
    body = ET.SubElement(act, "body")
    preface = ET.SubElement(body, "preface")
    h = ET.SubElement(preface, "heading")
    h.text = title

    content = doc.get("content", [])
    for idx, block in enumerate(content, start=1):
        # section
        sec = ET.SubElement(body, "section", eId=block.get("id", f"sec{idx}"))
        if block.get("heading"):
            sh = ET.SubElement(sec, "heading")
            sh.text = str(block["heading"])[:512]
        p = ET.SubElement(sec, "paragraph")
        p.text = str(block.get("text", ""))

    xml_bytes = ET.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
    )
    return cast(bytes, xml_bytes)


def validate_akn_xml(xml_bytes: bytes) -> None:
    try:
        ET.fromstring(xml_bytes)
    except ET.XMLSyntaxError as e:
        raise AKNError(f"Invalid Akoma Ntoso XML: {e}")
