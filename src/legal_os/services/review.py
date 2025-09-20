from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel

from ..schemas import ReviewTaskOut


@dataclass
class _ReviewTask:
    id: str
    status: str
    priority: str
    expert_type: str
    reasons: List[str]
    final_confidence: float
    created_at: datetime
    updated_at: datetime


class ReviewQueue(BaseModel):
    tasks: Dict[str, _ReviewTask] = {}

    def add(
        self,
        *,
        priority: str,
        expert_type: str,
        reasons: List[str],
        final_confidence: float,
    ) -> ReviewTaskOut:
        now = datetime.now(timezone.utc)
        task_id = f"rvw_{int(now.timestamp()*1000)}"
        task = _ReviewTask(
            id=task_id,
            status="queued",
            priority=priority,
            expert_type=expert_type,
            reasons=reasons,
            final_confidence=final_confidence,
            created_at=now,
            updated_at=now,
        )
        self.tasks[task_id] = task
        return self._to_out(task)

    def get(self, task_id: str) -> Optional[ReviewTaskOut]:
        task = self.tasks.get(task_id)
        return self._to_out(task) if task else None

    def list(self) -> List[ReviewTaskOut]:
        return [self._to_out(t) for t in self.tasks.values()]

    def start(self, task_id: str) -> Optional[ReviewTaskOut]:
        task = self.tasks.get(task_id)
        if not task:
            return None
        task.status = "in_review"
        task.updated_at = datetime.now(timezone.utc)
        return self._to_out(task)

    def complete(self, task_id: str, *, accepted: bool) -> Optional[ReviewTaskOut]:
        task = self.tasks.get(task_id)
        if not task:
            return None
        task.status = "completed" if accepted else "rejected"
        task.updated_at = datetime.now(timezone.utc)
        return self._to_out(task)

    @staticmethod
    def _to_out(task: _ReviewTask) -> ReviewTaskOut:
        return ReviewTaskOut(
            id=task.id,
            status=task.status,  # type: ignore[arg-type]
            priority=task.priority,  # type: ignore[arg-type]
            expert_type=task.expert_type,  # type: ignore[arg-type]
            reasons=task.reasons,
            final_confidence=task.final_confidence,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )


class CriticalReviewOrchestrator:
    """Routes low-confidence results to appropriate legal experts.

    Heuristic baseline per spec 1.3.3.
    """

    def __init__(self, queue: ReviewQueue | None = None) -> None:
        self.queue = queue or ReviewQueue()

    def assess_and_route(
        self,
        *,
        final_confidence: float,
        contains_constitutional: bool,
        contains_tax: bool,
        contains_commercial: bool,
        has_complex_refs: bool,
        involves_definitions: bool,
    ) -> Tuple[str | None, List[str]]:
        reasons: List[str] = []
        priority = "low"
        expert = "general_legal_expert"

        # Mandatory triggers
        if final_confidence < 0.95:
            reasons.append("confidence_below_95")
        if final_confidence < 0.90:
            reasons.append("confidence_below_90")
        if final_confidence < 0.85:
            reasons.append("confidence_below_85")

        # Content-based triggers
        if has_complex_refs:
            reasons.append("complex_cross_references")
            priority = "medium"
        if involves_definitions:
            reasons.append("statutory_definitions_present")
            priority = "medium"
        if contains_constitutional:
            expert = "constitutional_law_expert"
            priority = "high"
        elif contains_tax:
            expert = "tax_law_expert"
            priority = "high"
        elif contains_commercial:
            expert = "commercial_law_expert"
            priority = "medium"

        # Escalation by low confidence
        if final_confidence < 0.85:
            priority = "critical"
        elif final_confidence < 0.90 and priority != "critical":
            priority = "high"

        # Route only if needed
        if reasons:
            out = self.queue.add(
                priority=priority,
                expert_type=expert,
                reasons=reasons,
                final_confidence=final_confidence,
            )
            return out.id, reasons
        return None, []
