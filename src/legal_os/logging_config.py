from __future__ import annotations

import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Optional


request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        req_id = request_id_ctx.get()
        if req_id:
            payload["request_id"] = req_id
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"))


class _RedactFilter(logging.Filter):
    _patterns = [
        (re.compile(r"(AI_API_KEY=)([^\s]+)"), r"\1***"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - simple
        msg = str(record.getMessage())
        for pattern, repl in self._patterns:
            msg = pattern.sub(repl, msg)
        record.msg = msg
        return True


def configure_json_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    for h in root.handlers:
        h.addFilter(_RedactFilter())


def set_request_id(request_id: Optional[str]) -> None:
    request_id_ctx.set(request_id)
