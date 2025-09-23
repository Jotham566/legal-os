from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Protocol
import hashlib
import random
import math
import re
import lxml.etree as ET
import time
from typing import Any, Dict, cast
from urllib.parse import urljoin

import httpx

from .akn import AKN_NS
from ..settings import get_settings

NSMAP = {"akn": AKN_NS}


@dataclass
class EmbeddingChunk:
    index: int
    text: str
    vector: List[float]


@dataclass
class EmbeddingResult:
    model: str
    dim: int
    chunks: List[EmbeddingChunk]
    issues: List[str]


class EmbeddingClient(Protocol):
    def embed_texts(self, texts: Sequence[str], model: str, dim: int) -> List[List[float]]: ...


class StubEmbeddingClient:
    """Deterministic embedding generator for tests/dev.

    Uses a hash-derived RNG to generate a unit-norm vector per text+model.
    """

    def embed_texts(self, texts: Sequence[str], model: str, dim: int) -> List[List[float]]:
        vectors: List[List[float]] = []
        for t in texts:
            seed_src = f"{model}|{t}".encode("utf-8")
            seed = int(hashlib.sha256(seed_src).hexdigest()[:16], 16)
            rng = random.Random(seed)
            vals = [rng.gauss(0, 1) for _ in range(dim)]
            # normalize to unit length
            norm = math.sqrt(sum(v * v for v in vals)) or 1.0
            vectors.append([v / norm for v in vals])
        return vectors


class OpenAIEmbeddingClient:
    def __init__(self, api_key: str, endpoint: str | None = None):
        self.api_key = api_key
        # endpoint unused for public OpenAI; kept for compatibility
        self.endpoint = endpoint
        self.base_url = "https://api.openai.com/v1/"

    def embed_texts(self, texts: Sequence[str], model: str, dim: int) -> List[List[float]]:
        if dim <= 0:
            raise ValueError("dim must be positive")
        url = urljoin(self.base_url, "embeddings")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {"model": model, "input": list(texts)}
        # 'dimensions' is supported for text-embedding-3-* models
        if dim:
            payload["dimensions"] = dim
        attempts = 0
        while True:
            attempts += 1
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                try:
                    data = resp.json()
                except Exception:
                    resp.raise_for_status()
                    raise
                if resp.status_code == 429 and attempts < 3:
                    time.sleep(1.5 * attempts)
                    continue
                if resp.status_code >= 400:
                    raise ValueError(
                        f"OpenAI embeddings error {resp.status_code}: {data}"
                    )
                vectors = [
                    item.get("embedding", []) for item in data.get("data", [])
                ]
                break
        if not vectors or any(len(v) == 0 for v in vectors):
            raise ValueError("OpenAI embeddings returned empty vectors")
        return [list(map(float, v)) for v in vectors]


class AzureOpenAIEmbeddingClient:
    def __init__(self, api_key: str, endpoint: str, api_version: str | None = None):
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.api_version = api_version or "2024-10-21"

    def embed_texts(self, texts: Sequence[str], model: str, dim: int) -> List[List[float]]:
        if dim <= 0:
            raise ValueError("dim must be positive")
        # Here, "model" is expected to be the Azure deployment name
        deployment_name = model
        # Reference:
        # https://learn.microsoft.com/azure/ai-foundry/openai/reference#embeddings
        url = (
            f"{self.endpoint}/openai/deployments/{deployment_name}/embeddings"
            f"?api-version={self.api_version}"
        )
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {"input": list(texts)}
        # dimensions supported for text-embedding-3-* models
        if dim:
            payload["dimensions"] = dim
        attempts = 0
        while True:
            attempts += 1
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                try:
                    data = resp.json()
                except Exception:
                    resp.raise_for_status()
                    raise
                if resp.status_code in (429, 503) and attempts < 3:
                    time.sleep(1.5 * attempts)
                    continue
                if resp.status_code >= 400:
                    raise ValueError(
                        f"Azure OpenAI embeddings error {resp.status_code}: {data}"
                    )
                vectors = [
                    item.get("embedding", []) for item in data.get("data", [])
                ]
                break
        if not vectors or any(len(v) == 0 for v in vectors):
            raise ValueError("Azure OpenAI embeddings returned empty vectors")
        return [list(map(float, v)) for v in vectors]


class GoogleEmbeddingClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def embed_texts(self, texts: Sequence[str], model: str, dim: int) -> List[List[float]]:
        if dim <= 0:
            raise ValueError("dim must be positive")
        # Reference: https://ai.google.dev/gemini-api/docs/embeddings
        try:
            from google import genai  # type: ignore
            from google.genai import types as genai_types  # type: ignore
        except Exception as import_err:
            raise RuntimeError(
                "Google GenAI SDK not installed. Please install 'google-genai'"
            ) from import_err
        client = genai.Client(api_key=self.api_key)
        config = (
            genai_types.EmbedContentConfig(output_dimensionality=dim) if dim else None
        )
        result = client.models.embed_content(
            model=model, contents=list(texts), config=config
        )
        embeddings: List[List[float]] = []
        for emb in result.embeddings:
            # emb.values is list of floats
            embeddings.append(list(map(float, getattr(emb, "values", []))))
        if not embeddings or any(len(v) == 0 for v in embeddings):
            raise ValueError("Google embeddings returned empty vectors")
        return embeddings


class MistralEmbeddingClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.mistral.ai/v1/embeddings"

    def embed_texts(self, texts: Sequence[str], model: str, dim: int) -> List[List[float]]:
        if dim <= 0:
            raise ValueError("dim must be positive")
        # Reference:
        # https://docs.mistral.ai/api/#tag/embeddings/operation/embeddings_v1_embeddings_postEmbeddings
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "input": list(texts),
            "output_dimension": dim,
            "output_dtype": "float",
        }
        attempts = 0
        while True:
            attempts += 1
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(self.base_url, headers=headers, json=payload)
                try:
                    data = resp.json()
                except Exception:
                    resp.raise_for_status()
                    raise
                if resp.status_code in (429, 503) and attempts < 3:
                    time.sleep(1.5 * attempts)
                    continue
                if resp.status_code >= 400:
                    raise ValueError(
                        f"Mistral embeddings error {resp.status_code}: {data}"
                    )
                items = data.get("data", [])
                vectors = [item.get("embedding", []) for item in items]
                break
        if not vectors or any(len(v) == 0 for v in vectors):
            raise ValueError("Mistral embeddings returned empty vectors")
        return [list(map(float, v)) for v in vectors]


class OllamaEmbeddingClient:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint.rstrip("/")

    def embed_texts(self, texts: Sequence[str], model: str, dim: int) -> List[List[float]]:
        if dim <= 0:
            raise ValueError("dim must be positive")
        # Reference: https://github.com/ollama/ollama/blob/main/docs/api.md#embeddings-api
        url = f"{self.endpoint}/api/embed"
        headers = {"Content-Type": "application/json"}
        payload: Dict[str, Any] = {"model": model, "input": list(texts)}
        if dim:
            payload["dimensions"] = dim
        attempts = 0
        vectors: List[List[float]] | List[float] | None = None
        while True:
            attempts += 1
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                try:
                    data = resp.json()
                except Exception:
                    resp.raise_for_status()
                    raise
                if resp.status_code in (429, 503) and attempts < 3:
                    time.sleep(1.5 * attempts)
                    continue
                if resp.status_code >= 400:
                    raise ValueError(
                        f"Ollama embeddings error {resp.status_code}: {data}"
                    )
                vectors = data.get("embeddings") or data.get("embedding")
                break
        if vectors is None:
            raise ValueError("Ollama embeddings returned no data")
        # Legacy single vector endpoint compatibility
        if isinstance(vectors, list) and vectors and isinstance(vectors[0], (int, float)):
            if len(texts) != 1:
                raise ValueError(
                    "Ollama legacy /api/embeddings supports single input only"
                )
            vec1 = cast(List[float], vectors)
            vectors_raw: List[List[float]] = [[float(x) for x in vec1]]
        else:
            if not isinstance(vectors, list):
                raise ValueError("Unexpected Ollama embeddings response shape")
            vectors_raw = []
            for item in vectors:
                if not isinstance(item, list):
                    raise ValueError("Unexpected Ollama embeddings vector type")
                vectors_raw.append([float(x) for x in item])
        if not vectors_raw or any(len(v) == 0 for v in vectors_raw):
            raise ValueError("Ollama embeddings returned empty vectors")
        return vectors_raw


class EmbeddingPipeline:
    def __init__(
        self, client: Optional[EmbeddingClient] = None, provider: Optional[str] = None
    ) -> None:
        settings = get_settings()
        use_external = settings.flags.enable_external_ai and (
            provider or settings.ai_provider
        )
        if client is not None:
            self.client: EmbeddingClient = client
        elif use_external:
            prov = (provider or settings.ai_provider or "").lower()
            if prov == "openai" and settings.ai_api_key:
                self.client = OpenAIEmbeddingClient(
                    api_key=settings.ai_api_key, endpoint=settings.ai_endpoint
                )
            elif prov == "azure-openai" and settings.ai_api_key and settings.ai_endpoint:
                self.client = AzureOpenAIEmbeddingClient(
                    api_key=settings.ai_api_key,
                    endpoint=settings.ai_endpoint,
                    api_version=settings.ai_azure_api_version,
                )
            elif prov == "google" and settings.google_api_key:
                self.client = GoogleEmbeddingClient(api_key=settings.google_api_key)
            elif prov == "mistral" and settings.mistral_api_key:
                self.client = MistralEmbeddingClient(api_key=settings.mistral_api_key)
            elif prov == "ollama" and settings.ai_endpoint:
                self.client = OllamaEmbeddingClient(endpoint=settings.ai_endpoint)
            else:
                # Fallback to stub if config incomplete
                self.client = StubEmbeddingClient()
        else:
            # default to deterministic stub
            self.client = StubEmbeddingClient()

    # -------- Chunking ---------
    def chunk_from_json(
        self,
        content: List[dict],
        max_chars_per_chunk: int = 800,
        overlap: int = 100,
    ) -> List[str]:
        texts: List[str] = []
        for b in content:
            t = str(b.get("text") or "").strip()
            if t:
                texts.append(t)
        full = "\n".join(texts)
        return self._chunk_text(full, max_chars_per_chunk, overlap)

    def chunk_from_akn_xml(
        self,
        xml: str | bytes,
        max_chars_per_chunk: int = 800,
        overlap: int = 100,
    ) -> List[str]:
        xml_bytes = xml.encode("utf-8") if isinstance(xml, str) else xml
        parser = ET.XMLParser(resolve_entities=False, no_network=True)
        root = ET.fromstring(xml_bytes, parser=parser)
        # Extract text nodes, excluding headings/nums
        parts: List[str] = []
        for t in root.xpath(
            '//text()[not(ancestor::akn:heading or ancestor::akn:num)]',
            namespaces=NSMAP,
        ):
            s = re.sub(r"\s+", " ", str(t)).strip()
            if s:
                parts.append(s)
        full = " ".join(parts)
        return self._chunk_text(full, max_chars_per_chunk, overlap)

    def _chunk_text(self, text: str, max_chars: int, overlap: int) -> List[str]:
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return []
        chunks: List[str] = []
        start = 0
        n = len(text)
        step = max(1, max_chars - overlap)
        while start < n:
            end = min(n, start + max_chars)
            chunk = text[start:end]
            chunks.append(chunk)
            if end == n:
                break
            start += step
        return chunks

    # ---- Helpers ----
    def _normalize_vectors(self, vectors: List[List[float]]) -> List[List[float]]:
        normed: List[List[float]] = []
        for v in vectors:
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            normed.append([x / norm for x in v])
        return normed

    # -------- Generate ---------
    def generate_embeddings(self, texts: List[str], model: str, dim: int) -> EmbeddingResult:
        issues: List[str] = []
        if dim <= 0:
            raise ValueError("dim must be positive")
        if not texts:
            return EmbeddingResult(model=model, dim=dim, chunks=[], issues=["no_text"])
        vectors = self.client.embed_texts(texts, model, dim)
        # Normalize to unit norm for cosine similarity consistency across providers
        vectors = self._normalize_vectors(vectors)
        chunks = [
            EmbeddingChunk(index=i, text=t, vector=v)
            for i, (t, v) in enumerate(zip(texts, vectors))
        ]
        return EmbeddingResult(model=model, dim=dim, chunks=chunks, issues=issues)
