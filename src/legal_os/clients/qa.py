from __future__ import annotations

from typing import Optional, Any, Dict, cast

import httpx
from pydantic import BaseModel

from ..clients.base_http import CircuitBreaker, retry_request


class QAValidateRequest(BaseModel):
    content_type: str
    data: bytes


class QAClientHTTP:
    def __init__(self, base_url: str, api_key: Optional[str] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.cb = CircuitBreaker()

    async def validate(self, req: QAValidateRequest) -> Dict[str, Any]:
        if not self.cb.allow():
            raise RuntimeError("circuit_open")

        async def _call() -> Dict[str, Any]:
            headers = {"Content-Type": req.content_type}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self.base_url}/validate",
                    content=req.data,
                    headers=headers,
                )
                resp.raise_for_status()
                return cast(Dict[str, Any], resp.json())

        try:
            res = await retry_request(_call)
            self.cb.on_success()
            return res
        except Exception:
            self.cb.on_failure()
            raise
