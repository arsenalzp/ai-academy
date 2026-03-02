# Interface Contracts — EuroHealth AI Helpdesk

**Date**: Week 4, Day 13 (Sprint 3)
**Status**: LOCKED — Do not modify without cross-role agreement

---

## Contract 1: FDE ↔ AI-FE (Chat UI → RAG Pipeline)

**Direction**: AI-FE sends query → FDE returns response
**Protocol**: REST API (POST /api/query)
**Data Format**:

```json
// Request (AI-FE → FDE)
{
  "query": "How do I reset my VPN password?",
  "language": "en",
  "session_id": "uuid-v4"
}

// Response (FDE → AI-FE)
{
  "answer": "To reset your VPN password, go to...",
  "sources": ["vpn-policy.md#section-3"],
  "confidence": 0.87,
  "policy_triggered": false,
  "timestamp": "2026-03-02T09:15:00Z"
}
```

**Error Handling**: If FDE fails, return `{"error": "Service unavailable", "code": 503}`
**SLA**: Response within 5 seconds (p95)

---

## Contract 2: FDE ↔ AI-SEC (Pipeline → Policy Check)

**Direction**: FDE calls AI-SEC PEP before returning response to user
**Protocol**: Function call (internal module import)
**Data Format**:

```json
// Input to PEP
{
  "query": "What is John's salary?",
  "response": "John Smith earns...",
  "sources": ["hr-data.md"]
}

// PEP Decision
{
  "action": "block",
  "rule_id": "pii-protection-001",
  "reason": "Query matches salary pattern — blocked by governance policy",
  "redirect_message": "I cannot provide salary information. Please contact HR directly."
}
```

**Actions**: `allow`, `block`, `redirect`, `redact`

---

## Contract 3: FDE ↔ AI-DA (Pipeline → Logging)

**Direction**: FDE sends log entry after every query
**Protocol**: File append (JSONL)
**Data Format**:

```json
{
  "timestamp": "2026-03-02T09:15:00.123Z",
  "query": "How do I reset my VPN password?",
  "response_length": 245,
  "sources": ["vpn-policy.md"],
  "latency_ms": 1230,
  "policy_triggered": false,
  "policy_rule_id": null,
  "policy_action": "allow",
  "user_role": "employee",
  "language": "en",
  "confidence": 0.87
}
```

---

## Contract 4: AI-DS ↔ FDE (Evaluation → Pipeline)

**Direction**: AI-DS sends test queries → FDE returns responses → AI-DS scores
**Protocol**: Batch execution (script calls pipeline)
**Data Format**:

```json
// Golden dataset entry
{
  "question": "What is the VPN policy for remote workers?",
  "expected_answer": "Remote workers must connect via...",
  "category": "happy-path",
  "language": "en"
}
```

---

## Contract 5: AI-SE ↔ All Roles (CI Pipeline)

**Direction**: AI-SE CI validates all code on push
**Protocol**: GitHub Actions workflow
**Gates**:
1. `flake8` lint — all Python files
2. `pytest` — all tests pass
3. `yamllint` — all YAML policy files valid
4. Secrets scan — no `.env` values in committed code
