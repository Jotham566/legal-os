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
    kind: str  # part | chapter | section | article | unknown
    number: Optional[str]
    level: int
    parent_eid: Optional[str]


@dataclass
class StructureParseResult:
    nodes: List[StructureNode]
    confidence: float


_PART_RE = re.compile(r"^(?:PART|Part)\s+([IVXLCDM]+)\b")
_CHAPTER_RE = re.compile(r"^(?:CHAPTER|Chapter)\s+([0-9IVXLCDM]+)\b")
_SECTION_RE = re.compile(r"^(?:SECTION|Section|Sec\.?|S\.)\s*([0-9]+[A-Za-z]?)\b")
_ARTICLE_RE = re.compile(r"^(?:ARTICLE|Article)\s*([0-9]+[A-Za-z]?)\b")


def _classify_heading(heading: str) -> Tuple[str, Optional[str], int]:
    h = heading.strip()
    if m := _PART_RE.match(h):
        return ("part", m.group(1), 1)
    if m := _CHAPTER_RE.match(h):
        return ("chapter", m.group(1), 2)
    if m := _SECTION_RE.match(h):
        return ("section", m.group(1), 3)
    if m := _ARTICLE_RE.match(h):
        return ("article", m.group(1), 3)
    return ("unknown", None, 4)


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
        root = ET.fromstring(xml_bytes)
        sections = root.xpath("//akn:section", namespaces=NSMAP)
        content: List[dict] = []
        for i, sec in enumerate(sections, start=1):
            eid = sec.get("eId") or f"sec{i}"
            h_el = sec.find(
                "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}heading"
            )
            heading = h_el.text.strip() if h_el is not None and h_el.text else ""
            content.append({"id": eid, "heading": heading})
        return self.parse_from_json(content)
