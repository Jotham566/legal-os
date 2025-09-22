from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel
import re
from difflib import SequenceMatcher
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class Citation(BaseModel):
    text: str
    section: str
    page: int
    char_offset: int
    coordinates: Tuple[float, float, float, float]
    confidence: float
    # New: light-weight classification to guide formatting
    kind: Optional[str] = None  # 'statute', 'article', 'case', 'other'


class AuditTrail(BaseModel):
    citation_id: str
    operation: str
    timestamp: str
    user_id: str
    document_id: str
    details: Dict[str, Any]


class CitationService:

    def __init__(self, session: Dict[str, str]):
        self.session = session
        self.accuracy_threshold = 0.995

    def _normalize(self, s: str) -> str:
        return re.sub(r"\s+", " ", s).strip().lower()

    def extract_citations(self, text: str, pdf_path: Optional[str] = None
                          ) -> List[Citation]:
        if pdf_path:
            # TODO: extracted_text = DoclingExtractor.extract_text(pdf_path)
            extracted_text = text
        else:
            extracted_text = text

        # Expanded patterns with simple kind tagging
        pattern_specs = [
            (r"\bSection\s+(\d+(?:\.\d+)*)\s+of\s+([A-Z\s]+(?:Act|Code)?)", "statute"),
            (
                r"\b[sS]s?\.?\s*(\d+[A-Za-z]?(?:\([\da-zA-Z]+\))*)\b"
                r"(?:\s+of\s+([A-Z][A-Za-z\s]+?)(?:\s+Act)?)?",
                "statute",
            ),
            (r"\bArticle\s+(\d+(?:\.\d+)*)\s+(?:of\s+)?([A-Z\s]+)", "article"),
            (r"\((\d{4})\)\s+([A-Z\s]+)\s+No\.?\s+(\d+)", "statute"),
            # New: bracketed year case citations like "Smith v. Republic [2020] eKLR"
            (
                r"\b([A-Z][A-Za-z\s]+ v\.? [A-Z][A-ZaZ\s]+)\s*\[\s*\d{4}\s*\]"
                r"\s*(?:eKLR|EA|KLR)?",
                "case",
            ),
            (
                r"\b([A-Z][A-Za-z\s]+ v\.? [A-Z][A-Za-z\s]+)\b,?\s*(\d{4})\s*"
                r"(?:eKLR|EA|KLR)?",
                "case",
            ),
        ]
        citations: List[Citation] = []
        for pattern, kind in pattern_specs:
            for match in re.finditer(pattern, extracted_text, re.IGNORECASE):
                citation_text = match.group(0)
                section = match.group(1) if len(match.groups()) > 0 else 'Unknown'
                # Heuristic page calc from position
                page = 1 + len(extracted_text[:match.start()].split('\n\n')) // 50
                char_offset = match.start()
                # Start with conservative baseline; will be updated in validate
                conf = 0.95
                citation = Citation(
                    text=citation_text,
                    section=section,
                    page=page,
                    char_offset=char_offset,
                    coordinates=(0, 0, 0, 0),
                    confidence=conf,
                    kind=kind,
                )
                if pdf_path:
                    citation = self.ground_coordinates(citation, pdf_path, extracted_text)
                if self.validate_accuracy(citation, extracted_text):
                    citations.append(citation)

        for citation in citations:
            self.log_audit_trail(citation, "extract")

        return citations

    def validate_accuracy(self, extracted: Citation, source_text: str) -> bool:
        # Compare against actual source slice at the detected position
        start = max(0, extracted.char_offset)
        end = min(len(source_text), start + len(extracted.text))
        source_slice = source_text[start:end]
        similarity = SequenceMatcher(
            None, self._normalize(extracted.text), self._normalize(source_slice)
        ).ratio()
        # Tie confidence to similarity (cap just below 1.0 to reflect uncertainty)
        extracted.confidence = max(extracted.confidence, min(0.999, 0.7 + 0.3 * similarity))
        if similarity < self.accuracy_threshold:
            logger.warning(
                f"Low accuracy citation: {extracted.text}, similarity: {similarity}"
            )
            self.log_audit_trail(extracted, "validate_fail")
        else:
            self.log_audit_trail(extracted, "validate_success")
        return similarity >= self.accuracy_threshold

    def ground_coordinates(
        self, citation: Citation, pdf_path: str, text: str
    ) -> Citation:
        line_height = 20.0
        char_width = 6.0
        lines_before = text[:citation.char_offset].count('\n')
        last_nl = text.rfind('\n', 0, citation.char_offset)
        chars_in_line = last_nl + 1 if last_nl != -1 else 0
        offset_in_line = citation.char_offset - chars_in_line

        margin = 50.0
        page_height = 800.0
        start_y = margin + lines_before * line_height
        start_x = margin + offset_in_line * char_width
        end_x = start_x + len(citation.text) * char_width
        end_y = start_y + line_height

        page_adjust = (citation.page - 1) * page_height
        start_y += page_adjust
        end_y += page_adjust

        citation.coordinates = (start_x, start_y, end_x, end_y)
        logger.debug(
            f"Grounded {citation.text} at {citation.coordinates} "
            f"on page {citation.page}"
        )
        self.log_audit_trail(citation, "ground")
        return citation

    def build_pdf_link(self, pdf_path: str, citation: Citation) -> str:
        # Simple fragment; some viewers support char ranges via named params
        start = citation.char_offset
        end = start + len(citation.text)
        return f"{pdf_path}#page={citation.page}&char={start}-{end}"

    def format_citation(self, citation: Citation) -> str:
        formatted = ""
        citation_lower = citation.text.lower()

        if citation.kind == 'statute' or 'act' in citation_lower or 'income tax' in citation_lower:
            formatted = (
                f"{citation.text} \u00a7 {citation.section} "
                f"({citation.page}:{citation.char_offset}-"
                f"{citation.char_offset + len(citation.text)})"
            )
        elif citation.kind == 'case' or 'v.' in citation.text or 'case' in citation_lower:
            # Avoid misusing section for cases; keep a minimal, jurisdiction-tagged form
            formatted = (
                f"{citation.text} (Kenya, p. {citation.page})"
            )
        elif citation.kind == 'article' or 'article' in citation_lower:
            formatted = f"Art. {citation.section}, {citation.text} (Kenya)"
        elif 'section' in citation_lower:
            formatted = f"s. {citation.section}, {citation.text} (Kenya)"
        else:
            formatted = f"{citation.section}, {citation.text} (p. {citation.page})"

        if not re.match(r'^[A-Z]', formatted):
            formatted = formatted.capitalize()
        formatted += "."

        self.log_audit_trail(citation, "format")
        return formatted

    def log_audit_trail(self, citation: Citation, operation: str) -> None:
        details = {
            "confidence": citation.confidence,
            "coordinates": citation.coordinates,
            "char_offset": citation.char_offset
        }
        if 'v.' in citation.text:
            details["redacted"] = True

        trail = AuditTrail(
            citation_id=citation.text[:10],
            operation=operation,
            timestamp=datetime.now().isoformat(),
            user_id=self.session.get('user_id', 'anonymous'),
            document_id=self.session.get('document_id', 'unknown'),
            details=details
        )

        redacted_details = {
            k: v if k != 'coordinates' else '[REDACTED]' for k, v in details.items()
        }
        log_entry = {
            **trail.model_dump(exclude={'details'}),
            'details': redacted_details
        }
        logger.info(f"Audit trail ({operation}): {json.dumps(log_entry)}")
