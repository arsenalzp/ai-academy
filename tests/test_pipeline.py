"""Minimal tests for CLI behavior only."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_main_requires_query_argument() -> None:
    """Ensure CLI returns usage error when no query argument is provided."""
    project_root = Path(__file__).resolve().parents[1]
    pipeline_path = project_root / "src" / "pipeline.py"

    completed = subprocess.run(
        [sys.executable, str(pipeline_path)],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "Usage: python src/pipeline.py" in completed.stdout
