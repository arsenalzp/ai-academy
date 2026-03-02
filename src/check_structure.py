"""Folder structure checks for CI quality gate."""

from __future__ import annotations

from pathlib import Path


REQUIRED_PATHS = [
    "data",
    "docs",
    "governance",
    "governance/compliance",
    "governance/evidence",
    "governance/operating-model",
    "governance/policies",
    "monitoring",
    "src",
    "tests",
]


def find_missing_paths(project_root: Path) -> list[str]:
    """Return all required paths missing from project root."""
    missing: list[str] = []
    for relative_path in REQUIRED_PATHS:
        candidate = project_root / relative_path
        if not candidate.exists():
            missing.append(relative_path)
    return missing


def main() -> int:
    """CLI entrypoint for folder structure gate."""
    root = Path(".")
    missing_paths = find_missing_paths(root)
    if missing_paths:
        print("Folder structure validation failed. Missing paths:")
        for missing in missing_paths:
            print(f"- {missing}")
        return 1

    print("Folder structure validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
