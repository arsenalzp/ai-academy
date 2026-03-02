"""Configuration utilities for the helpdesk pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    log_file_path: Path
    policy_dir_path: Path
    knowledge_dir_path: Path


def load_settings() -> Settings:
    """Load runtime configuration from environment variables with safe defaults."""
    return Settings(
        log_file_path=Path(os.getenv("LOG_FILE_PATH", "logs/queries.jsonl")),
        policy_dir_path=Path(os.getenv("POLICY_FILE_PATH", "governance/policies")),
        knowledge_dir_path=Path(os.getenv("KNOWLEDGE_DIR_PATH", "data/knowledge")),
    )
