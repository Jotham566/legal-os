from __future__ import annotations

from typing import Dict, List, Optional
import lxml.etree as ET

from .akn import AKN_NS

# Namespace map for XPath queries (prefix-based)
NSMAP = {"akn": AKN_NS}


class AKNQueryError(ValueError):
    pass


class AKNQueryEngine:
    """Lightweight Akoma Ntoso XML query helper.

    - Caches parsed document
    - Provides namespace-aware XPath evaluation
    - Supports section lookup by eId and simple neighbor navigation
    """

    def __init__(self, xml: str | bytes):
        try:
            xml_bytes = xml.encode("utf-8") if isinstance(xml, str) else xml
            self.doc = ET.fromstring(xml_bytes)
        except (ET.XMLSyntaxError, ValueError) as e:
            raise AKNQueryError(f"Invalid XML: {e}")
        if self.doc.tag.endswith("akomaNtoso") is False and not self.doc.tag.endswith(
            "}akomaNtoso"
        ):
            # Not strictly required, but provide a hint
            pass

    def xpath(self, query: str) -> List[str]:
        """Evaluate an XPath against the AKN doc using the 'akn' namespace prefix.

        Returns string values for text results or serialized XML for node results.
        """
        try:
            results = self.doc.xpath(query, namespaces=NSMAP)
        except ET.XPathError as e:
            raise AKNQueryError(f"XPath error: {e}")
        out: List[str] = []
        for r in results:
            if isinstance(r, (str, bytes)):
                out.append(r.decode("utf-8") if isinstance(r, bytes) else r)
            elif isinstance(r, ET._Element):  # type: ignore[attr-defined]
                out.append(ET.tostring(r, encoding="unicode"))
            else:
                out.append(str(r))
        return out

    def _section_elements(self) -> List[ET._Element]:  # type: ignore[name-defined]
        return self.doc.xpath("//akn:section", namespaces=NSMAP)  # type: ignore[no-any-return]

    def section_by_eid(self, eid: str) -> Dict[str, str]:
        el = self.doc.xpath(f"//akn:section[@eId='{eid}']", namespaces=NSMAP)
        if not el:
            raise AKNQueryError(f"Section not found: {eid}")
        sec: ET._Element = el[0]  # type: ignore[index]
        heading_el = sec.find("{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}heading")
        heading = heading_el.text if heading_el is not None else ""
        return {
            "eid": eid,
            "heading": heading or "",
            "xml": ET.tostring(sec, encoding="unicode"),
        }

    def navigate_neighbors(self, eid: str) -> Dict[str, Optional[str]]:
        sections = self._section_elements()
        order = [s.get("eId") for s in sections]
        try:
            idx = order.index(eid)
        except ValueError:
            raise AKNQueryError(f"Section not found: {eid}")
        prev_eid = order[idx - 1] if idx > 0 else None
        next_eid = order[idx + 1] if idx + 1 < len(order) else None
        # Also include heading for current for convenience
        current = sections[idx]
        heading_el = current.find("{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}heading")
        heading = heading_el.text if heading_el is not None else ""
        return {
            "current_eid": eid,
            "prev_eid": prev_eid,
            "next_eid": next_eid,
            "heading": heading or "",
        }
