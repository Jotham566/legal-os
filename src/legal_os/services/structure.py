from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import re
import lxml.etree as ET

from .akn import AKN_NS

NSMAP = {"akn": AKN_NS}


@dataclass
class StructureNode:
    eid: str
    heading: str
    kind: str  # part | chapter | division | section | article | subsection | unknown
    number: Optional[str]
    level: int
    parent_eid: Optional[str]


@dataclass
class StructureParseResult:
    nodes: List[StructureNode]
    confidence: float


# Expanded patterns to cover East African variants
_PART_RE = re.compile(r"^(?:PART|Part)\s+([IVXLCDM]+|[A-Z])\b")
_CHAPTER_RE = re.compile(r"^(?:CHAPTER|Chapter)\s+([0-9IVXLCDM]+)\b")
_DIVISION_RE = re.compile(r"^(?:DIVISION|Division)\s+([A-Z]|[IVXLCDM]+|[0-9]+)\b")
_SECTION_RE = re.compile(r"^(?:SECTION|Section|Sec\.?|S\.)\s*([0-9]+[A-Za-z]?)\b")
_ARTICLE_RE = re.compile(r"^(?:ARTICLE|Article)\s*([0-9]+[A-Za-z]?)\b")
_REGULATION_RE = re.compile(r"^(?:REGULATION|Regulation)\s*([0-9]+[A-Za-z]?)\b")
_RULE_RE = re.compile(r"^(?:RULE|Rule)\s*([0-9]+[A-Za-z]?)\b")
_SUBSECTION_INLINE_RE = re.compile(r"^\(?([0-9]+|[a-z])\)\b")


def _classify_heading(heading: str) -> Tuple[str, Optional[str], int]:
    h = heading.strip()
    if m := _PART_RE.match(h):
        return ("part", m.group(1), 1)
    if m := _CHAPTER_RE.match(h):
        return ("chapter", m.group(1), 2)
    if m := _DIVISION_RE.match(h):
        return ("division", m.group(1), 2)
    if m := _SECTION_RE.match(h):
        return ("section", m.group(1), 3)
    if m := _ARTICLE_RE.match(h):
        return ("article", m.group(1), 3)
    if m := _REGULATION_RE.match(h):
        return ("regulation", m.group(1), 3)
    if m := _RULE_RE.match(h):
        return ("rule", m.group(1), 3)
    if m := _SUBSECTION_INLINE_RE.match(h):
        return ("subsection", m.group(1), 4)
    return ("unknown", None, 5)


class StructureParser:
    def parse_from_json(self, content: List[dict]) -> StructureParseResult:
        nodes: List[StructureNode] = []
        stack: List[StructureNode] = []  # track last seen node per level
        recognized = 0
        for idx, block in enumerate(content, start=1):
            eid = block.get("id") or f"sec{idx}"
            heading = str(block.get("heading") or "").strip()
            kind, number, level = _classify_heading(heading)
            if kind != "unknown":
                recognized += 1
            # Find parent: last node with level < current
            parent_eid = None
            for prev in reversed(stack):
                if prev.level < level:
                    parent_eid = prev.eid
                    break
            node = StructureNode(
                eid=eid,
                heading=heading,
                kind=kind,
                number=number,
                level=level,
                parent_eid=parent_eid,
            )
            nodes.append(node)
            # maintain stack: pop deeper or equal levels, push current
            while stack and stack[-1].level >= level:
                stack.pop()
            stack.append(node)
        confidence = recognized / len(content) if content else 0.0
        return StructureParseResult(nodes=nodes, confidence=confidence)

    def parse_from_akn_xml(self, xml: str | bytes) -> StructureParseResult:
        xml_bytes = xml.encode("utf-8") if isinstance(xml, str) else xml
        # secure parser
        parser = ET.XMLParser(resolve_entities=False, no_network=True)
        root = ET.fromstring(xml_bytes, parser=parser)
        # Gather parts/chapters/divisions/articles/sections/subsections in document order
        xpath = (
            "//akn:part | //akn:chapter | //akn:division | "
            "//akn:article | //akn:section | //akn:subsection"
        )
        elems = root.xpath(xpath, namespaces=NSMAP)
        content: List[dict] = []
        for i, el in enumerate(elems, start=1):
            tag = ET.QName(el).localname.lower()
            eid = el.get("eId") or f"{tag}{i}"
            # prefer element's own heading child if present
            h_el = el.find("{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}heading")
            heading = h_el.text.strip() if h_el is not None and h_el.text else ""
            if not heading:
                # synthesize from num + tag
                num_el = el.find("{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}num")
                num = num_el.text.strip() if num_el is not None and num_el.text else None
                if num:
                    # avoid double prefix if heading already includes tag
                    heading = f"{tag.capitalize()} {num}"
            content.append({"id": eid, "heading": heading})
        return self.parse_from_json(content)
