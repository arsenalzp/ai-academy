# EuroHealth AI Helpdesk

AI helpdesk seed implementation for an EU-regulated healthcare insurer (GDPR scope), based on the architecture in `docs/architecture/solution-design.md`.

## Architecture Mapping (from Solution Design)

High-level flow:

User Query → Query Pipeline → Policy Engine (PEP) → Response  
                                          ↘ Structured JSONL Logging

Implemented modules:

- `src/pipeline.py`: query processing, policy gate, output formatting, logging
- `src/policy_engine.py`: reads **all** policy YAML files from `governance/policies`
- `src/retriever.py`: ingests **multiple** knowledge files from `data/knowledge`
- `src/structured_logger.py`: JSONL append logger
- `src/config.py`: environment-based runtime settings

## Project Structure

```text
data/
docs/
governance/
  compliance/
  evidence/
  operating-model/
  policies/
monitoring/
src/
tests/
```

## Prerequisites

- Python 3.12+
- Docker (optional, for container run)

## Configuration

Copy `.env.example` to `.env` and adjust paths if needed:

```dotenv
LOG_FILE_PATH=logs/queries.jsonl
POLICY_FILE_PATH=governance/policies
KNOWLEDGE_DIR_PATH=data/knowledge
```

No secrets are hardcoded in source files.

## Add Runtime Inputs

This seed expects policy and knowledge artifacts to be provided at runtime.

### 1) Add policy files (`governance/policies/*.yaml`)

Example policy file:

```yaml
rules:
  - id: salary-confidentiality-001
    action: block
    reason: Salary disclosure is restricted
    redirect_message: I can’t provide salary information. Please contact HR.
    patterns:
      - "\\bsalary\\b"
      - "\\bcompensation\\b"
```

### 2) Add knowledge files (`data/knowledge/*.md` or `*.txt`)

Example knowledge file:

```md
VPN access requires MFA before entering internal systems.
```

## Local Run

Install dependencies:

```bash
pip install -r requirements-dev.txt
```

Run pipeline:

```bash
python src/pipeline.py "What is the VPN policy?"
```

Output includes:

- `Answer: ...`
- `Sources: ...`
- `Policy triggered: true|false`

Each query appends a structured log line to `logs/queries.jsonl`.

## Docker Run

Build image:

```bash
docker build -t eurohealth-helpdesk .
```

Run a query:

```bash
docker run --rm --env-file .env -v ${PWD}/logs:/app/logs eurohealth-helpdesk "What is the VPN policy?"
```

Or use Compose:

```bash
docker compose run --rm helpdesk "What is the VPN policy?"
```

## CI/CD

GitHub Actions workflow: `.github/workflows/ci.yml`

On each push and pull request, CI executes:

1. `flake8 src tests`
2. `pytest -q`
3. `python src/validate_policies.py`
4. `python src/check_structure.py`

## Test Scope (current stage)

Current tests focus on CI/CD smoke checks in `tests/test_cicd_smoke.py`:

- requirements files exist
- `.gitignore` excludes `.env`
- no obvious hardcoded secrets patterns
- `Dockerfile` exists and contains required runtime instructions

## Governance Alignment

- Policy files are external artifacts in `governance/policies` (single source of truth)
- Policy and knowledge inputs are loaded by directory, not hardcoded filenames
- Structured logging supports audit and compliance evidence collection

## Notes

- If no policy files are present, policy evaluation defaults to `allow`.
- If no knowledge files are present, the pipeline returns a safe fallback response.
