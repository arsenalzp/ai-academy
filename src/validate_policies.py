"""Validate syntax of all policy YAML files."""

from __future__ import annotations

from pathlib import Path

import yaml


def validate_policy_yaml(policy_root: Path) -> list[str]:
    """Validate all YAML files under policy root and return error messages."""
    errors: list[str] = []
    for path in sorted(policy_root.rglob("*.yml")) + sorted(policy_root.rglob("*.yaml")):
        try:
            with path.open("r", encoding="utf-8") as policy_file:
                yaml.safe_load(policy_file)
        except FileNotFoundError:
            errors.append(f"File not found during scan: {path.as_posix()}")
        except OSError as error:
            errors.append(f"I/O error for {path.as_posix()}: {error}")
        except yaml.YAMLError as error:
            errors.append(f"YAML parse error in {path.as_posix()}: {error}")
    return errors


def main() -> int:
    """CLI entrypoint for policy YAML validation."""
    policy_root = Path("governance/policies")
    if not policy_root.exists():
        print("Missing policy directory: governance/policies")
        return 1

    errors = validate_policy_yaml(policy_root)
    if errors:
        print("Policy YAML validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Policy YAML validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
