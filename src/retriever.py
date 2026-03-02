"""Simple retrieval module for policy-backed answer generation."""

from __future__ import annotations

from pathlib import Path


def _read_knowledge_file(knowledge_file_path: Path) -> str:
    """Load one knowledge file from disk with explicit I/O error handling."""
    try:
        with knowledge_file_path.open("r", encoding="utf-8") as knowledge_file:
            return knowledge_file.read()
    except FileNotFoundError as error:
        raise RuntimeError(f"Knowledge file not found: {knowledge_file_path}") from error
    except OSError as error:
        raise RuntimeError(f"Unable to read knowledge file: {knowledge_file_path}") from error


def _load_knowledge_documents(knowledge_dir_path: Path) -> list[tuple[Path, str]]:
    """Load all supported knowledge files from a directory tree."""
    if not knowledge_dir_path.exists() or not knowledge_dir_path.is_dir():
        raise RuntimeError(f"Knowledge directory not found: {knowledge_dir_path}")

    candidate_paths = sorted(knowledge_dir_path.rglob("*.md")) + sorted(
        knowledge_dir_path.rglob("*.txt")
    )
    documents: list[tuple[Path, str]] = []
    for candidate_path in candidate_paths:
        documents.append((candidate_path, _read_knowledge_file(candidate_path)))
    return documents


def _score_document(query: str, document_text: str) -> int:
    """Score a document by counting matched query terms."""
    query_terms = [term for term in query.lower().split() if term]
    lowered_document_text = document_text.lower()
    return sum(1 for term in query_terms if term in lowered_document_text)


def answer_with_citation(query: str, knowledge_dir_path: Path) -> tuple[str, list[str], float]:
    """Retrieve an answer and source citation from ingested knowledge files."""
    documents = _load_knowledge_documents(knowledge_dir_path)
    if not documents:
        return "Knowledge base is currently unavailable. Please contact support.", [], 0.2

    scored_documents = [
        (path, text, _score_document(query, text)) for path, text in documents if text.strip()
    ]
    if not scored_documents:
        return "Knowledge base is currently unavailable. Please contact support.", [], 0.2

    best_path, best_text, best_score = max(scored_documents, key=lambda item: item[2])
    if best_score <= 0:
        return (
            "I do not have enough approved context to answer that safely. "
            "Please contact the internal service desk.",
            [best_path.as_posix()],
            0.35,
        )

    first_non_empty_line = next(
        (line.strip() for line in best_text.splitlines() if line.strip()),
        "Approved internal policy guidance is available.",
    )
    answer = f"Based on approved knowledge: {first_non_empty_line}"
    return answer, [best_path.as_posix()], 0.9
