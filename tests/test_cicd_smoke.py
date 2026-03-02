"""CI/CD smoke tests for repository hygiene and build readiness."""

from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read_text(path: Path) -> str:
    """Read UTF-8 text from disk for smoke assertions."""
    return path.read_text(encoding="utf-8")


def test_requirements_files_exist_and_are_populated() -> None:
    """Ensure base and dev requirements files exist and contain expected entries."""
    requirements_path = PROJECT_ROOT / "requirements.txt"
    requirements_dev_path = PROJECT_ROOT / "requirements-dev.txt"

    assert requirements_path.exists()
    assert requirements_dev_path.exists()

    requirements_text = _read_text(requirements_path).strip()
    requirements_dev_text = _read_text(requirements_dev_path).strip()

    assert requirements_text
    assert requirements_dev_text
    assert "-r requirements.txt" in requirements_dev_text


def test_gitignore_excludes_env_files() -> None:
    """Ensure .env is excluded from version control."""
    gitignore_path = PROJECT_ROOT / ".gitignore"
    assert gitignore_path.exists()

    entries = {
        line.strip()
        for line in _read_text(gitignore_path).splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert ".env" in entries


def test_no_hardcoded_secrets_in_runtime_and_ci_files() -> None:
    """Scan key code and CI files for suspicious hardcoded secret assignments."""
    candidate_files = [
        *PROJECT_ROOT.joinpath("src").rglob("*.py"),
        *PROJECT_ROOT.joinpath("tests").rglob("*.py"),
        *PROJECT_ROOT.joinpath(".github", "workflows").rglob("*.yml"),
        PROJECT_ROOT / "Dockerfile",
    ]

    secret_assignment_pattern = re.compile(
        r"(?i)(api[_-]?key|secret|token|password|passwd)\s*[:=]\s*['\"][^'\"]+['\"]"
    )

    findings: list[str] = []
    for file_path in candidate_files:
        if not file_path.exists():
            continue
        for line_number, line in enumerate(_read_text(file_path).splitlines(), start=1):
            if secret_assignment_pattern.search(line):
                findings.append(f"{file_path.as_posix()}:{line_number}")

    assert not findings, f"Potential hardcoded secrets found: {findings}"


def test_dockerfile_exists_and_has_runtime_instructions() -> None:
    """Ensure Dockerfile includes baseline instructions needed for runtime execution."""
    dockerfile_path = PROJECT_ROOT / "Dockerfile"
    assert dockerfile_path.exists()

    dockerfile_text = _read_text(dockerfile_path)
    assert "FROM " in dockerfile_text
    assert "WORKDIR " in dockerfile_text
    assert "COPY requirements.txt" in dockerfile_text
    assert "RUN pip install" in dockerfile_text
    assert "ENTRYPOINT [\"python\", \"src/pipeline.py\"]" in dockerfile_text
