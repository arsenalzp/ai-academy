"""Structured JSONL logging utilities."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def write_jsonl(log_file_path: Path, entry: Dict[str, Any]) -> None:
    """Append one JSON object as a single JSONL line with safe I/O handling."""
    try:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        with log_file_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as error:
        raise RuntimeError(f"Unable to write log file: {log_file_path}") from error
