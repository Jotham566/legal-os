from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException

from ..schemas import ReviewTaskOut
from ..services.review import CriticalReviewOrchestrator, ReviewQueue

router = APIRouter(prefix="/review", tags=["review"])

_queue = ReviewQueue()
_orch = CriticalReviewOrchestrator(queue=_queue)


@router.post("/assess-route", response_model=dict)
async def assess_route(
    final_confidence: float = Body(embed=True),
    contains_constitutional: bool = Body(False, embed=True),
    contains_tax: bool = Body(False, embed=True),
    contains_commercial: bool = Body(False, embed=True),
    has_complex_refs: bool = Body(False, embed=True),
    involves_definitions: bool = Body(False, embed=True),
) -> dict:
    task_id, reasons = _orch.assess_and_route(
        final_confidence=final_confidence,
        contains_constitutional=contains_constitutional,
        contains_tax=contains_tax,
        contains_commercial=contains_commercial,
        has_complex_refs=has_complex_refs,
        involves_definitions=involves_definitions,
    )
    return {"task_id": task_id, "reasons": reasons}


@router.get("/tasks", response_model=list[ReviewTaskOut])
async def list_tasks() -> list[ReviewTaskOut]:
    return _queue.list()


@router.post("/tasks/{task_id}/start", response_model=ReviewTaskOut)
async def start_task(task_id: str) -> ReviewTaskOut:
    out = _queue.start(task_id)
    if not out:
        raise HTTPException(status_code=404, detail="task_not_found")
    return out


@router.post("/tasks/{task_id}/complete", response_model=ReviewTaskOut)
async def complete_task(task_id: str, accepted: bool = Body(True, embed=True)) -> ReviewTaskOut:
    out = _queue.complete(task_id, accepted=accepted)
    if not out:
        raise HTTPException(status_code=404, detail="task_not_found")
    return out
