"""CLI entrypoint for the EuroHealth AI helpdesk pipeline."""

from __future__ import annotations

import sys
import time
from typing import List

from config import load_settings
from models import QueryResponse
from policy_engine import evaluate_query
from retriever import answer_with_citation
from structured_logger import utc_now_iso, write_jsonl


def _build_blocked_response(message: str) -> QueryResponse:
    """Build a blocked response payload."""
    return QueryResponse(
        answer=message,
        sources=[],
        confidence=1.0,
        policy_triggered=True,
    )


def process_query(query: str, user_role: str = "employee", language: str = "en") -> QueryResponse:
    """Run policy check, retrieval, and return a response object."""
    settings = load_settings()
    started = time.perf_counter()

    decision = evaluate_query(query=query, policy_dir_path=settings.policy_dir_path)
    if decision.action == "block":
        response = _build_blocked_response(
            decision.redirect_message
            or "I cannot provide that information due to governance policy."
        )
    else:
        answer, sources, confidence = answer_with_citation(
            query=query,
            knowledge_dir_path=settings.knowledge_dir_path,
        )
        response = QueryResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            policy_triggered=False,
        )

    latency_ms = int((time.perf_counter() - started) * 1000)
    log_entry = {
        "timestamp": utc_now_iso(),
        "query": query,
        "response_length": len(response.answer),
        "sources": response.sources,
        "latency_ms": latency_ms,
        "policy_triggered": response.policy_triggered,
        "policy_rule_id": decision.rule_id,
        "policy_action": decision.action,
        "user_role": user_role,
        "language": language,
        "confidence": response.confidence,
        "steps": ["policy_check", "retrieval_or_block", "response"],
    }
    write_jsonl(settings.log_file_path, log_entry)
    return response


def _format_cli_output(response: QueryResponse) -> str:
    """Format response for CLI output."""
    lines: List[str] = [f"Answer: {response.answer}"]
    if response.sources:
        lines.append(f"Sources: {', '.join(response.sources)}")
    else:
        lines.append("Sources: none")
    lines.append(f"Policy triggered: {str(response.policy_triggered).lower()}")
    return "\n".join(lines)


def main(argv: List[str]) -> int:
    """Run pipeline CLI with one required query argument."""
    if len(argv) < 2:
        print("Usage: python src/pipeline.py \"<query>\"")
        return 1

    query = " ".join(argv[1:]).strip()
    if not query:
        print("Query must not be empty.")
        return 1

    try:
        response = process_query(query)
    except RuntimeError as error:
        print(f"Error: {error}")
        return 2

    print(_format_cli_output(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
