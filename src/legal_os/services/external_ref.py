from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict
import re
import lxml.etree as ET

from .citation import CitationService, Citation
from .akn import AKN_NS

NSMAP = {"akn": AKN_NS}


@dataclass
class ExternalRef:
    text: str
    kind: str  # statute | article | case | other
    authority: str  # e.g., KE
    jurisdiction: str  # e.g., kenya
    canonical_uri: Optional[str]
    confidence: float


@dataclass
class ExternalRefMetrics:
    total: int
    resolved: int
    resolution_rate: float


@dataclass
class ExternalRefResult:
    refs: List[ExternalRef]
    metrics: ExternalRefMetrics
    issues: List[str]


# Simple stub registry for canonical resolution
_CANONICAL_REGISTRY: Dict[str, str] = {
    "income tax act": "akn:ke/act/income-tax-act",
    "interpretation and general provisions act": "akn:ke/act/interpretation-general-provisions-act",
}


class ExternalRefResolver:
    def __init__(self) -> None:
        # Session context for audit; kept minimal here
        self._cit = CitationService(session={"user_id": "system", "document_id": "external"})

    def _normalize(self, s: str) -> str:
        return re.sub(r"\s+", " ", s).strip().lower()

    def _resolve_canonical(self, c: Citation) -> ExternalRef:
        text_norm = self._normalize(c.text)
        # naive authority/jurisdiction inference (default KE)
        authority = "KE"
        jurisdiction = "kenya"
        canonical_uri: Optional[str] = None
        conf = c.confidence
        if c.kind == "statute" or "act" in text_norm or "code" in text_norm:
            # try to extract act name portion after 'of'
            m = re.search(r"of\s+([A-Za-z\s]+?)(?:\s+Act|\s+Code|\b)", c.text, re.IGNORECASE)
            if m:
                key = self._normalize(m.group(1)) + (" act" if "act" in text_norm else "")
                for k, v in _CANONICAL_REGISTRY.items():
                    if k in key:
                        canonical_uri = v
                        conf = max(conf, 0.98)
                        break
        elif c.kind == "case" or " v." in c.text:
            # Construct a placeholder canonical pointer (no external call)
            parties = re.sub(r"[^A-Za-z\s\.v]", "", c.text)
            slug = self._normalize(parties).replace(" ", "-")
            canonical_uri = f"akn:ke/case/{slug}"
            conf = max(conf, 0.9)
        elif c.kind == "article":
            canonical_uri = None
            conf = max(conf, 0.8)
        else:
            canonical_uri = None

        return ExternalRef(
            text=c.text,
            kind=c.kind or "other",
            authority=authority,
            jurisdiction=jurisdiction,
            canonical_uri=canonical_uri,
            confidence=round(conf, 3),
        )

    def resolve_from_text(self, text: str) -> ExternalRefResult:
        citations = self._cit.extract_citations(text)
        refs: List[ExternalRef] = []
        issues: List[str] = []
        for c in citations:
            ref = self._resolve_canonical(c)
            if not ref.canonical_uri:
                issues.append(f"Unresolved external reference: {ref.text}")
            refs.append(ref)
        total = len(refs)
        resolved = sum(1 for r in refs if r.canonical_uri)
        metrics = ExternalRefMetrics(
            total=total,
            resolved=resolved,
            resolution_rate=(resolved / total) if total else 0.0,
        )
        return ExternalRefResult(refs=refs, metrics=metrics, issues=issues)

    def resolve_from_json(self, content: List[dict]) -> ExternalRefResult:
        # Concatenate text fields for detection; keep duplicates minimal by set
        texts = []
        for b in content:
            t = str(b.get("text") or "").strip()
            if t:
                texts.append(t)
        joined = "\n".join(texts)
        return self.resolve_from_text(joined)

    def resolve_from_akn_xml(self, xml: str | bytes) -> ExternalRefResult:
        xml_bytes = xml.encode("utf-8") if isinstance(xml, str) else xml
        parser = ET.XMLParser(resolve_entities=False, no_network=True)
        root = ET.fromstring(xml_bytes, parser=parser)
        texts: List[str] = []
        for t in root.xpath('//text()[not(ancestor::akn:heading)]', namespaces=NSMAP):
            texts.append(str(t))
        return self.resolve_from_text(" ".join(texts))
