from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DocumentIn(BaseModel):
    title: Optional[str] = Field(default=None, max_length=512)


class DocumentOut(BaseModel):
    id: str
    created_at: datetime
    title: Optional[str] = None


class DocumentVersionIn(BaseModel):
    content: Dict[str, Any] = Field(default_factory=dict)


class DocumentVersionOut(BaseModel):
    id: str
    document_id: str
    version_number: int
    content: Dict[str, Any]
    created_at: datetime


class Grounding(BaseModel):
    page: Optional[int] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None


class Citation(BaseModel):
    text: str
    source_id: Optional[str] = None
    grounding: Optional[Grounding] = None


class ProcessingSessionCreate(BaseModel):
    source_key: Optional[str] = None
    total_steps: int = Field(ge=1, default=10)


class ProcessingSessionOut(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    status: str
    progress: int
    eta_seconds: Optional[int] = None
    checkpoints: Dict[str, Any]
    last_error: Optional[str] = None
    source_key: Optional[str] = None


class ProcessingSessionUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    eta_seconds: Optional[int] = Field(default=None, ge=0)
    checkpoint: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
