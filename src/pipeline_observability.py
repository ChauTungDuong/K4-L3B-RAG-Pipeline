"""Safe, per-request progress events for the demo and its local log file."""

import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable
from uuid import uuid4


LOG_PATH = Path(__file__).parent.parent / ".cache" / "rag_demo.log"
ProgressCallback = Callable[[dict], None]
_logger = logging.getLogger("rag_demo")


def new_request_id() -> str:
    return uuid4().hex[:8]


def safe_error(error: Exception) -> str:
    """Keep useful failure information without leaking keys or request URLs."""
    status = getattr(error, "code", None)
    if status is None:
        status = getattr(getattr(error, "response", None), "status_code", None)
    return f"{type(error).__name__} (HTTP {status})" if status else type(error).__name__


def _get_logger() -> logging.Logger:
    if not _logger.handlers:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(LOG_PATH, maxBytes=2_000_000, backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        _logger.addHandler(handler)
        _logger.setLevel(logging.INFO)
        _logger.propagate = False
    return _logger


def record_event(
    events: list[dict], request_id: str, stage: str, status: str,
    message: str, on_step: ProgressCallback | None = None, **details,
) -> dict:
    event = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "request_id": request_id,
        "stage": stage,
        "status": status,
        "message": message,
        **details,
    }
    events.append(event)
    _get_logger().info(json.dumps(event, ensure_ascii=False))
    if on_step is not None:
        on_step(event)
    return event


def recent_events(limit: int = 60) -> list[dict]:
    if not LOG_PATH.exists():
        return []
    lines = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events
