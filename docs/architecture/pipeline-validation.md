# Validation Layer Spec (Pre-RAG)

**Date**: Week 5, Day 16
**Status**: FINAL - (Day 17)

## 1. Purpose

The Validation Layer ensures that Confluence page HTML content is safe, well-formed, and policy-compliant **before entering the RAG ingestion pipeline**.

It acts as a quality gate to:

- Prevent malformed or low-quality content from polluting embeddings
- Enforce accessibility and structural rules
- Apply ingestion policies (age limits, duplication)
- Provide structured validation outcomes for routing and observability

---

## 2. Input and Output Contract

### 2.1 Input

The validation module ingests:

- `html_blob: string` - Raw page HTML
- `page_id: string` - Unique page identifier
- `last_modified: string | datetime` - Last modification timestamp
- `now: datetime` (optional) - Injectable clock for deterministic testing

---

### 2.2 Output

The validation layer must return a JSON object:
```json
 {
 "page_id": string,
  "checks": { 
    "staleness": "PASS | FAIL | WARN",
    "duplicate": "PASS | FAIL | WARN",
    "language": "PASS | FAIL | WARN",
    "pii": "PASS | FAIL | WARN"
  }
 }