from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..db import session_scope
from ..dependencies import require_roles
from ..services.consistency import ConsistencyChecker

router = APIRouter(prefix="/api/v1/consistency", tags=["consistency"])


class CheckRequest(BaseModel):
    document_id: str
    version_id: str


class CheckResponse(BaseModel):
    document_id: str
    version_id: str
    has_json: bool
    has_xml: bool
    consistent: bool
    xml_checksum_matches: bool | None = None
    xml_well_formed: bool | None = None


class ReconcileResponse(CheckResponse):
    pass


@router.post("/check", response_model=CheckResponse)
async def check_consistency(payload: CheckRequest) -> CheckResponse:
    with session_scope() as db:
        checker = ConsistencyChecker(db)
        report = checker.check(document_id=payload.document_id, version_id=payload.version_id)
        return CheckResponse(
            document_id=report.document_id,
            version_id=report.version_id,
            has_json=report.has_json,
            has_xml=report.has_xml,
            consistent=report.consistent,
            xml_checksum_matches=report.xml_checksum_matches,
            xml_well_formed=report.xml_well_formed,
        )


@router.post("/reconcile", response_model=ReconcileResponse)
async def reconcile(
    payload: CheckRequest,
    _user: dict = Depends(require_roles("admin")),
) -> ReconcileResponse:
    with session_scope() as db:
        checker = ConsistencyChecker(db)
        report = checker.reconcile(document_id=payload.document_id, version_id=payload.version_id)
        return ReconcileResponse(
            document_id=report.document_id,
            version_id=report.version_id,
            has_json=report.has_json,
            has_xml=report.has_xml,
            consistent=report.consistent,
            xml_checksum_matches=report.xml_checksum_matches,
            xml_well_formed=report.xml_well_formed,
        )
