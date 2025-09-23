from __future__ import annotations

from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..services import embeddings as embeddings_service

router = APIRouter(prefix="/api/v1/embeddings", tags=["embeddings"])


# Simple guard against using orchestration LLMs as embedding models
_ORCHESTRATION_MODELS = {"gpt-5", "gpt-5-mini"}


def _validate_embedding_model(model: str) -> None:
    if model.strip().lower() in _ORCHESTRATION_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Selected model is for orchestration (GPT-5 family), not embeddings. "
                "Use an embeddings model like text-embedding-3-large, an Azure deployment name, "
                "gemini-embedding-001, mistral-embed, or an Ollama embedding-capable model."
            ),
        )


class EmbedJsonIn(BaseModel):
    content: List[dict]
    model: str = "text-embedding-3-large"
    dim: int = 3072
    max_chars_per_chunk: int = 800
    overlap: int = 100
    provider: str | None = None  # optional per-request provider override


class EmbedXmlIn(BaseModel):
    xml: str
    model: str = "text-embedding-3-large"
    dim: int = 3072
    max_chars_per_chunk: int = 800
    overlap: int = 100
    provider: str | None = None  # optional per-request provider override


class ChunkOut(BaseModel):
    index: int
    text: str
    vector: List[float]


class EmbedOut(BaseModel):
    model: str
    dim: int
    chunks: List[ChunkOut]
    issues: List[str]


@router.post("/json", response_model=EmbedOut)
async def embed_json(payload: EmbedJsonIn) -> EmbedOut:
    _validate_embedding_model(payload.model)
    pipe = embeddings_service.EmbeddingPipeline(provider=payload.provider)
    texts = pipe.chunk_from_json(payload.content, payload.max_chars_per_chunk, payload.overlap)
    res = pipe.generate_embeddings(texts, payload.model, payload.dim)
    return EmbedOut(
        model=res.model,
        dim=res.dim,
        chunks=[ChunkOut(index=c.index, text=c.text, vector=c.vector) for c in res.chunks],
        issues=res.issues,
    )


@router.post("/xml", response_model=EmbedOut)
async def embed_xml(payload: EmbedXmlIn) -> EmbedOut:
    _validate_embedding_model(payload.model)
    pipe = embeddings_service.EmbeddingPipeline(provider=payload.provider)
    texts = pipe.chunk_from_akn_xml(payload.xml, payload.max_chars_per_chunk, payload.overlap)
    res = pipe.generate_embeddings(texts, payload.model, payload.dim)
    return EmbedOut(
        model=res.model,
        dim=res.dim,
        chunks=[ChunkOut(index=c.index, text=c.text, vector=c.vector) for c in res.chunks],
        issues=res.issues,
    )
