from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.akn_query import AKNQueryEngine, AKNQueryError

router = APIRouter(prefix="/api/v1/akn", tags=["akn"])


class XPathIn(BaseModel):
    xml: str
    query: str


class XPathOut(BaseModel):
    results: List[str]


class SectionIn(BaseModel):
    xml: str
    eid: str


class SectionOut(BaseModel):
    eid: str
    heading: str
    xml: str


class NavIn(BaseModel):
    xml: str
    eid: str


class NavOut(BaseModel):
    current_eid: str
    prev_eid: Optional[str]
    next_eid: Optional[str]
    heading: str


@router.post("/xpath", response_model=XPathOut)
async def run_xpath(payload: XPathIn) -> XPathOut:
    try:
        eng = AKNQueryEngine(payload.xml)
        results = eng.xpath(payload.query)
        return XPathOut(results=results)
    except AKNQueryError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/section", response_model=SectionOut)
async def get_section(payload: SectionIn) -> SectionOut:
    try:
        eng = AKNQueryEngine(payload.xml)
        data = eng.section_by_eid(payload.eid)
        return SectionOut(**data)
    except AKNQueryError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/nav", response_model=NavOut)
async def navigate(payload: NavIn) -> NavOut:
    try:
        eng = AKNQueryEngine(payload.xml)
        data = eng.navigate_neighbors(payload.eid)
        return NavOut(
            current_eid=str(data.get("current_eid") or ""),
            prev_eid=data.get("prev_eid"),
            next_eid=data.get("next_eid"),
            heading=str(data.get("heading") or ""),
        )
    except AKNQueryError as e:
        raise HTTPException(status_code=404, detail=str(e))
