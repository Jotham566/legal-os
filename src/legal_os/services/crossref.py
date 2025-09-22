from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import re
import lxml.etree as ET

from .structure import StructureParser, StructureNode
from .akn import AKN_NS

NSMAP = {"akn": AKN_NS}

# Reference detection patterns (case-insensitive)
_SECTION_REF = re.compile(r"\b(?:section|sec\.|s\.)\s*(\d+[A-Za-z]?)\b", re.IGNORECASE)
_ARTICLE_REF = re.compile(r"\b(?:article|art\.)\s*(\d+[A-Za-z]?)\b", re.IGNORECASE)
_REGULATION_REF = re.compile(r"\b(?:regulation|reg\.)\s*(\d+[A-Za-z]?)\b", re.IGNORECASE)
_RULE_REF = re.compile(r"\b(?:rule|r\.)\s*(\d+[A-Za-z]?)\b", re.IGNORECASE)
_SUBSECTION_REF = re.compile(r"\b(?:subsection)\s*\((\d+|[a-z])\)", re.IGNORECASE)


@dataclass
class CrossRefEdge:
    source_eid: str
    ref_text: str
    target_kind: str
    target_number: str
    target_eid: Optional[str]
    confidence: float


@dataclass
class CrossRefMetrics:
    total_refs: int
    resolved_refs: int
    resolution_rate: float


@dataclass
class CrossRefResult:
    edges: List[CrossRefEdge]
    issues: List[str]
    metrics: CrossRefMetrics


class CrossRefResolver:
    def __init__(self) -> None:
        self.parser = StructureParser()

    def _build_index(self, nodes: List[StructureNode]) -> Dict[Tuple[str, str], str]:
        index: Dict[Tuple[str, str], str] = {}
        for n in nodes:
            if n.number and n.kind in {"section", "article", "regulation", "rule"}:
                index[(n.kind, n.number.lower())] = n.eid
        return index

    def _detect_refs_in_text(self, text: str) -> List[Tuple[str, str, str]]:
        """Return list of (ref_text, kind, number)."""
        refs: List[Tuple[str, str, str]] = []
        for pat, kind in [
            (_SECTION_REF, "section"),
            (_ARTICLE_REF, "article"),
            (_REGULATION_REF, "regulation"),
            (_RULE_REF, "rule"),
        ]:
            for m in pat.finditer(text):
                refs.append((m.group(0), kind, m.group(1)))
        # Subsection detected but we resolve to parent section/article level for now
        # Could be used to refine confidence later
        return refs

    def resolve_from_json(self, content: List[dict]) -> CrossRefResult:
        nodes = self.parser.parse_from_json(content).nodes
        index = self._build_index(nodes)
        edges: List[CrossRefEdge] = []
        issues: List[str] = []
        for block in content:
            source_eid = block.get("id") or ""
            text = str(block.get("text") or "")
            for ref_text, kind, number in self._detect_refs_in_text(text):
                key = (kind, number.lower())
                target_eid = index.get(key)
                confidence = 1.0 if target_eid else 0.6
                if not target_eid:
                    issues.append(f"Unresolved reference {ref_text} from {source_eid}")
                edges.append(
                    CrossRefEdge(
                        source_eid=source_eid,
                        ref_text=ref_text,
                        target_kind=kind,
                        target_number=number,
                        target_eid=target_eid,
                        confidence=confidence,
                    )
                )
        total = len(edges)
        resolved = sum(1 for e in edges if e.target_eid)
        metrics = CrossRefMetrics(
            total_refs=total,
            resolved_refs=resolved,
            resolution_rate=(resolved / total) if total else 0.0,
        )
        return CrossRefResult(edges=edges, issues=issues, metrics=metrics)

    def resolve_from_akn_xml(self, xml: str | bytes) -> CrossRefResult:
        xml_bytes = xml.encode("utf-8") if isinstance(xml, str) else xml
        parser = ET.XMLParser(resolve_entities=False, no_network=True)
        root = ET.fromstring(xml_bytes, parser=parser)
        # Build index from structure
        nodes = self.parser.parse_from_akn_xml(xml_bytes).nodes
        index = self._build_index(nodes)
        # Extract text per section/article/etc to detect refs with source eId
        edges: List[CrossRefEdge] = []
        issues: List[str] = []
        elems = root.xpath(
            "//akn:section | //akn:article | //akn:regulation | //akn:rule",
            namespaces=NSMAP,
        )
        for el in elems:
            eid = el.get("eId") or ""
            # collect all descendant text except heading
            texts: List[str] = []
            for t in el.xpath('.//text()[not(ancestor::akn:heading)]', namespaces=NSMAP):
                texts.append(str(t))
            joined = " ".join(texts)
            for ref_text, kind, number in self._detect_refs_in_text(joined):
                key = (kind, number.lower())
                target_eid = index.get(key)
                confidence = 1.0 if target_eid else 0.6
                if not target_eid:
                    issues.append(f"Unresolved reference {ref_text} from {eid}")
                edges.append(
                    CrossRefEdge(
                        source_eid=eid,
                        ref_text=ref_text,
                        target_kind=kind,
                        target_number=number,
                        target_eid=target_eid,
                        confidence=confidence,
                    )
                )
        total = len(edges)
        resolved = sum(1 for e in edges if e.target_eid)
        metrics = CrossRefMetrics(
            total_refs=total,
            resolved_refs=resolved,
            resolution_rate=(resolved / total) if total else 0.0,
        )
        return CrossRefResult(edges=edges, issues=issues, metrics=metrics)
