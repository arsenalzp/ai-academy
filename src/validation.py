"""Pre-RAG validation helpers for staleness and duplicate checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import re
import json
from typing import Dict, List, Optional, Sequence, Tuple


ValidationStatus = str


@dataclass(frozen=True)
class PageValidationInput:
    """Input payload for duplicate detection."""

    page_id: str
    html_blob: str


class _TextExtractor(HTMLParser):
    """Extract visible text content from an HTML document."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: List[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self._parts.append(data)

    def text(self) -> str:
        return " ".join(self._parts)


def _base_report(page_id: str) -> Dict[str, object]:
    return {
        "page_id": page_id,
        "checks": {
            "staleness": "WARN",
            "duplicate": "WARN",
            "language": "WARN",
            "pii": "WARN",
        },
    }


def _normalize_language_code(language_value: str) -> str:
    cleaned = language_value.strip().lower().replace("_", "-")
    if not cleaned:
        return "en"
    return cleaned.split("-", 1)[0]


def _extract_declared_language(html_blob: str) -> Optional[str]:
    html_lang_match = re.search(
        r"<html[^>]+(?:lang|xml:lang)=[\"']([^\"']+)[\"']",
        html_blob,
        flags=re.IGNORECASE,
    )
    if html_lang_match:
        return _normalize_language_code(html_lang_match.group(1))

    meta_lang_match = re.search(
        r"<meta[^>]+(?:name|property)=[\"'](?:lang|language)[\"'][^>]+content=[\"']([^\"']+)[\"']",
        html_blob,
        flags=re.IGNORECASE,
    )
    if meta_lang_match:
        return _normalize_language_code(meta_lang_match.group(1))

    return None


def _count_emails(text: str) -> int:
    email_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    return len(re.findall(email_pattern, text))


def _apply_language_and_pii_checks(
    report: Dict[str, object],
    text: str,
    html_blob: str,
    expected_language: str = "en",
) -> None:
    declared_language = _extract_declared_language(html_blob)
    if declared_language is None:
        report["checks"]["language"] = "WARN"
    elif declared_language == _normalize_language_code(expected_language):
        report["checks"]["language"] = "PASS"
    else:
        report["checks"]["language"] = f"FAIL:{declared_language}"

    email_count = _count_emails(text)
    report["checks"]["pii"] = (
        "PASS" if email_count == 0 else f"WARN:{email_count} emails"
    )


def _to_utc(dt_value: datetime) -> datetime:
    if dt_value.tzinfo is None:
        return dt_value.replace(tzinfo=timezone.utc)
    return dt_value.astimezone(timezone.utc)


def _parse_datetime(value: object) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        return _to_utc(value)

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None

        normalized = text.replace("Z", "+00:00")
        try:
            return _to_utc(datetime.fromisoformat(normalized))
        except ValueError:
            pass

        known_formats = (
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
        )
        for date_format in known_formats:
            try:
                parsed = datetime.strptime(text, date_format)
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

    return None


def _extract_html_last_modified(html_blob: str) -> Tuple[Optional[datetime], Optional[str]]:
    patterns = (
        (
            r"<meta[^>]+(?:name|property)=[\"'](?:last-modified|last_modified|"
            r"article:modified_time|og:updated_time)[\"'][^>]+content=[\"']([^\"']+)"
            r"[\"'][^>]*>"
        ),
        (
            r"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]+(?:name|property)=[\"']"
            r"(?:last-modified|last_modified|article:modified_time|og:updated_time)[\"']"
            r"[^>]*>"
        ),
        r"<time[^>]+datetime=[\"']([^\"']+)[\"'][^>]*>",
    )
    for pattern in patterns:
        match = re.search(pattern, html_blob, flags=re.IGNORECASE)
        if not match:
            continue
        parsed = _parse_datetime(match.group(1))
        if parsed is not None:
            return parsed, "html"
    return None, None


def extract_text_from_html(html_blob: str) -> str:
    """Return plain text from HTML while preserving word boundaries."""
    parser = _TextExtractor()
    parser.feed(html_blob)
    parser.close()
    text = parser.text()
    return re.sub(r"\s+", " ", text).strip()


def staleness_scan(
    page_id: str,
    html_blob: str,
    threshold_days: int = 180,
    now: Optional[datetime] = None,
    confluence_last_modified: object = None,
    file_last_modified: object = None,
    expected_language: str = "en",
) -> Dict[str, object]:
    """Evaluate content age and return a validation report with age metadata."""
    report = _base_report(page_id)
    metadata: Dict[str, object] = {"age_days": None}

    html_dt, html_source = _extract_html_last_modified(html_blob)
    confluence_dt = _parse_datetime(confluence_last_modified)
    file_dt = _parse_datetime(file_last_modified)

    resolved_dt = html_dt or confluence_dt or file_dt
    resolved_source = html_source or ("confluence_api" if confluence_dt else None) or (
        "file_timestamp" if file_dt else None
    )

    reference_now = _to_utc(now) if now else datetime.now(timezone.utc)

    if resolved_dt is None:
        report["checks"]["staleness"] = "WARN"
        metadata["reason"] = "last_modified_not_found"
        text = extract_text_from_html(html_blob)
        _apply_language_and_pii_checks(
            report=report,
            text=text,
            html_blob=html_blob,
            expected_language=expected_language,
        )
        report["metadata"] = metadata
        return report

    age_days = max(0, (reference_now - resolved_dt).days)
    metadata["age_days"] = age_days
    metadata["last_modified"] = resolved_dt.isoformat()
    metadata["last_modified_source"] = resolved_source

    report["checks"]["staleness"] = "FAIL" if age_days > threshold_days else "PASS"
    text = extract_text_from_html(html_blob)
    _apply_language_and_pii_checks(
        report=report,
        text=text,
        html_blob=html_blob,
        expected_language=expected_language,
    )
    report["metadata"] = metadata

    print(json.dumps(report, ensure_ascii=False, indent=2))

    return report


def duplicate_detection(
    page: PageValidationInput,
    hashes: Sequence[str],
    expected_language: str = "en",
) -> Dict[str, object]:
    """Process one page, compare its hash with known hashes, and return one report."""
    text = extract_text_from_html(page.html_blob)
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    normalized_hashes = {
        known_hash.strip().lower()
        for known_hash in hashes
        if isinstance(known_hash, str) and known_hash.strip()
    }
    is_duplicate = content_hash.lower() in normalized_hashes

    if not is_duplicate:
        hashes.append(content_hash.lower())

    report = _base_report(str(page.page_id))
    report["checks"]["duplicate"] = "FAIL" if is_duplicate else "PASS"
    _apply_language_and_pii_checks(
        report=report,
        text=text,
        html_blob=page.html_blob,
        expected_language=expected_language,
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))

    return report
