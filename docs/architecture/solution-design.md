# Solution Design — EuroHealth AI Helpdesk

**Date**: Week 4, Day 13 (Sprint 2)
**Status**: FINAL — Approved at Go/No-Go (Day 15)

---

## System Overview

```
User Query → [AI-FE: Chat UI] → [FDE: RAG Pipeline] → [AI-SEC: PEP] → Response
                                       ↓                      ↑
                                [Vector Store]         [Policy YAML]
                                       ↓                      ↑
                                [AI-DA: Logging] ←──── [Audit Trail]
```

---

## FDE — RAG Pipeline (Agent Core)

**Component**: Query → Retrieve → Generate → Policy Check → Respond
**Technology**:
- LLM: Llama 4 Scout (17B active params, MoE 16 experts, on-prem, INT4 quantized — fits single H100)
- Embeddings: BGE-M3 (open-source, MIT license, 100+ languages, on-prem)
- Vector Store: Supabase pgvector (self-hosted PostgreSQL)
- Framework: LangChain

**Inputs**: User query (string), conversation history
**Outputs**: Generated answer (string), sources (list), confidence score (float)
**PEP Location**: Between generation and response — policy.py checks every response before user sees it

---

## AI-SE — Deployment & CI/CD

**Component**: Containerized deployment with automated quality gates
**Technology**:
- Docker + docker-compose
- GitHub Actions (lint: flake8, test: pytest, policy: YAML validation)
- Folder structure enforced by CI

**Inputs**: Source code (all roles), test suite, policy files
**Outputs**: Validated Docker image, CI pass/fail status
**Constraint**: CI pipeline must validate policy YAML syntax on every commit

---

## AI-DS — Evaluation Framework

**Component**: Golden dataset + automated quality scoring
**Technology**:
- RAGAS metrics (faithfulness, answer_relevancy)
- pytest for test execution
- JSON output format

**Inputs**: RAG pipeline responses, expected answers
**Outputs**: Per-question scores, aggregate metrics, pass/fail verdict
**Constraint**: Must test both happy-path queries AND policy-trigger queries (e.g., salary requests)

---

## AI-DA — Monitoring & Analytics

**Component**: Structured logging schema + dashboard + alerting
**Technology**:
- JSONL log format (one JSON object per line)
- SQL queries against log data
- Dashboard mockup (Grafana-style layout)

**Inputs**: Log entries from all components
**Outputs**: KPI dashboard, anomaly alerts, compliance reports
**KPIs**: Avg response time, policy violation rate, escalation rate, user satisfaction

---

## AI-PM — Project Management

**Component**: Sprint planning, status tracking, stakeholder communication
**Technology**:
- Markdown-based sprint board
- Standup template (yesterday/today/blockers)
- Stakeholder update template (for Hans Muller, CIO)

**Inputs**: All role deliverables, risk items, timeline
**Outputs**: Sprint board, status reports, scope tracker

---

## AI-FE — Chat UI

**Component**: Browser-based chat interface with trust indicators
**Technology**:
- HTML5 + CSS3 + vanilla JavaScript
- REST API calls to backend
- Streaming response display

**Inputs**: User text input
**Outputs**: AI response display, loading state, error messages, AI disclosure label
**Constraint**: Must show "AI-generated" label on every response (EU AI Act Art. 50)

---

## AI-SEC — Security & Policy Engine

**Component**: Input validation, PII detection, policy enforcement
**Technology**:
- Python regex for PII patterns (email, phone, German ID)
- JSON policy files (machine-readable rules)
- pytest for security test suite

**Inputs**: User queries (pre-processing), AI responses (post-processing)
**Outputs**: Validated input, PII alerts, policy decisions (allow/block/redirect)
**Constraint**: Policy files in governance/policies/ are the single source of truth — code reads, never hardcodes
