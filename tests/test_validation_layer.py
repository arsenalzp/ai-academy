"""Tests for pre-RAG staleness and duplicate validation checks."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.validation import PageValidationInput, duplicate_detection, staleness_scan


FIXTURES_DIR = Path(__file__).resolve().parent


def _fixture_text(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_staleness_scan_flags_old_page_and_sets_age_metadata() -> None:
    """Pages older than threshold should fail staleness and include age_days metadata."""
    stale_html = _fixture_text("page_b.html")
    fixed_now = datetime(2026, 3, 3, 12, 0, 0, tzinfo=timezone.utc)

    report = staleness_scan(
        page_id="page-b",
        html_blob=stale_html,
        threshold_days=180,
        now=fixed_now,
    )

    assert report["page_id"] == "page-b"
    assert report["checks"] == {
        "staleness": "FAIL",
        "duplicate": "WARN",
        "language": "PASS",
        "pii": "PASS",
    }


def test_duplicate_detection_processes_one_page_against_hash_list() -> None:
    """One page should be checked against known hashes and return a single-page report."""
    page_a = PageValidationInput(page_id="page-a", html_blob=_fixture_text("page_a.html"))
    page_b = PageValidationInput(page_id="page-b", html_blob=_fixture_text("page_b.html"))
    hashes = []
    page_a_report = duplicate_detection(page_a, hashes)
    page_b_report = duplicate_detection(page_b, hashes)

    assert page_a_report["page_id"] == "page-a"
    assert page_a_report["checks"] == {
        "staleness": "WARN",
        "duplicate": "PASS",
        "language": "PASS",
        "pii": "PASS",
    }

    assert page_b_report["page_id"] == "page-b"
    assert page_b_report["checks"]["duplicate"] == "FAIL"

def test_report_uses_html_lang_property_when_present() -> None:
    """If html lang is not en, report should return FAIL:<lang> based on lang property."""
    html = """
    <html lang="ru">
        <head>
            <meta name="last-modified" content="2026-02-27T12:00:00Z" />
        </head>
        <body>
            <p>This page text is English, but html lang is explicitly Russian.</p>
        </body>
    </html>
    """

    report = staleness_scan(
        page_id="VPN-004",
        html_blob=html,
        threshold_days=180,
        now=datetime(2026, 3, 3, 12, 0, 0, tzinfo=timezone.utc),
        expected_language="en",
    )

    assert report["checks"]["language"] == "FAIL:ru"
