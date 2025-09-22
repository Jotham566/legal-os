from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .structure import StructureParser, StructureNode, StructureParseResult


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: str  # info | warning | error
    eid: Optional[str] = None


@dataclass
class ValidationMetrics:
    pattern_recognition: float  # [0,1]
    numbering_consistency: float  # [0,1]
    mandatory_sections: float  # [0,1]
    amendment_tracking: float  # [0,1]
    overall_score: float  # [0,1]


@dataclass
class ValidationResult:
    metrics: ValidationMetrics
    issues: List[ValidationIssue]


MANDATORY_HEADINGS = {
    "act": ["Short title", "Interpretation"],
}


class LegalStructureValidator:
    def __init__(self) -> None:
        self.parser = StructureParser()

    def _score_pattern_recognition(self, parsed: StructureParseResult) -> float:
        return parsed.confidence

    def _score_numbering_consistency(self, nodes: List[StructureNode]) -> float:
        # within each parent_eid and kind, ensure numbers mostly increase, detect duplicates
        groups: dict[tuple[str | None, str], List[StructureNode]] = {}
        for n in nodes:
            key = (n.parent_eid, n.kind)
            groups.setdefault(key, []).append(n)
        total = 0
        good = 0
        for (_parent, kind), arr in groups.items():
            seen: set[int] = set()
            last: Optional[int] = None
            for n in arr:
                total += 1
                if n.number is None:
                    continue
                try:
                    if kind in ("part", "chapter", "division") and not n.number.isdigit():
                        val = self._roman_to_int(n.number)
                    else:
                        val = int("".join(ch for ch in n.number if ch.isdigit()))
                except Exception:
                    continue
                if val in seen:
                    # duplicate within same scope -> do not count as good
                    continue
                seen.add(val)
                if last is None or val >= last:
                    good += 1
                    last = val
        return good / total if total else 0.0

    def _score_mandatory_sections(
        self, nodes: List[StructureNode]
    ) -> Tuple[float, List[ValidationIssue]]:
        issues: List[ValidationIssue] = []
        required = set(MANDATORY_HEADINGS["act"])  # default to act for now
        headings = [n.heading for n in nodes if n.heading]
        found_required: set[str] = set()
        for req in required:
            req_l = req.lower()
            for h in headings:
                if req_l in h.lower():  # accept phrases within longer headings
                    found_required.add(req)
                    break
        missing = [h for h in required if h not in found_required]
        for h in missing:
            issues.append(
                ValidationIssue(
                    code="missing_mandatory",
                    message=f"Missing mandatory heading: {h}",
                    severity="warning",
                )
            )
        score = 1.0 - (len(missing) / len(required) if required else 0.0)
        return max(0.0, score), issues

    def _score_amendment_tracking(self, nodes: List[StructureNode]) -> float:
        # Placeholder heuristic: detect any headings containing "Amendment" or "Amended"
        has_amend = any("amend" in (n.heading or "").lower() for n in nodes)
        return 1.0 if has_amend else 0.5  # neutral baseline when unknown

    @staticmethod
    def _roman_to_int(s: str) -> int:
        vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
        total = 0
        prev = 0
        for ch in reversed(s.upper()):
            v = vals.get(ch, 0)
            if v < prev:
                total -= v
            else:
                total += v
                prev = v
        return total

    def validate_from_json(self, content: List[dict]) -> ValidationResult:
        parsed = self.parser.parse_from_json(content)
        return self._validate_parsed(parsed)

    def validate_from_akn_xml(self, xml: str | bytes) -> ValidationResult:
        parsed = self.parser.parse_from_akn_xml(xml)
        return self._validate_parsed(parsed)

    def _hierarchy_issues(self, nodes: List[StructureNode]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        # Orphan: level > 1 but no parent_eid
        for n in nodes:
            if n.level > 1 and n.parent_eid is None:
                issues.append(
                    ValidationIssue(
                        code="STRUCTURE_ORPHAN",
                        message=f"Node {n.eid} has no parent",
                        severity="warning",
                        eid=n.eid,
                    )
                )
        return issues

    def _validate_parsed(self, parsed: StructureParseResult) -> ValidationResult:
        nodes = parsed.nodes
        pattern = self._score_pattern_recognition(parsed)
        numbering = self._score_numbering_consistency(nodes)
        mandatory_score, mand_issues = self._score_mandatory_sections(nodes)
        amendment = self._score_amendment_tracking(nodes)
        # Weighted overall score
        overall = (
            0.35 * pattern + 0.3 * numbering + 0.25 * mandatory_score + 0.1 * amendment
        )
        metrics = ValidationMetrics(
            pattern_recognition=round(pattern, 3),
            numbering_consistency=round(numbering, 3),
            mandatory_sections=round(mandatory_score, 3),
            amendment_tracking=round(amendment, 3),
            overall_score=round(overall, 3),
        )
        issues = mand_issues + self._hierarchy_issues(nodes)
        return ValidationResult(metrics=metrics, issues=issues)
