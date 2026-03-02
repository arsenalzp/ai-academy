"""Minimal tests for CLI behavior only."""

from __future__ import annotations

from src.pipeline import main


def test_main_requires_query_argument() -> None:
    """Ensure CLI returns usage error when no query argument is provided."""
    exit_code = main(["pipeline.py"])
    assert exit_code == 1
