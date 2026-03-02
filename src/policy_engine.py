"""YAML-backed policy enforcement engine."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

import yaml

from models import PolicyDecision


def _read_policy_files(policy_dir_path: Path) -> List[Dict[str, Any]]:
    """Read and parse all policy YAML files from a directory."""
    if not policy_dir_path.exists() or not policy_dir_path.is_dir():
        raise RuntimeError(f"Policy directory not found: {policy_dir_path}")

    policy_paths = sorted(policy_dir_path.rglob("*.yml")) + sorted(
        policy_dir_path.rglob("*.yaml")
    )
    if not policy_paths:
        return []

    documents: List[Dict[str, Any]] = []
    for policy_path in policy_paths:
        try:
            with policy_path.open("r", encoding="utf-8") as policy_file:
                content = yaml.safe_load(policy_file)
                documents.append(content or {})
        except FileNotFoundError as error:
            raise RuntimeError(f"Policy file not found: {policy_path}") from error
        except OSError as error:
            raise RuntimeError(f"Unable to read policy file: {policy_path}") from error
        except yaml.YAMLError as error:
            raise RuntimeError(f"Invalid policy YAML in {policy_path}") from error

    return documents


def _collect_block_rules(policy_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract block rules from policy documents."""
    block_rules: List[Dict[str, Any]] = []
    for policy_data in policy_documents:
        rules = policy_data.get("rules", [])
        if not isinstance(rules, list):
            raise RuntimeError("Policy file has invalid 'rules' structure; expected list")
        block_rules.extend(
            [
                rule
                for rule in rules
                if isinstance(rule, dict) and rule.get("action") == "block"
            ]
        )
    return block_rules


def evaluate_query(query: str, policy_dir_path: Path) -> PolicyDecision:
    """Evaluate a query against policy rules and return a policy decision."""
    policy_documents = _read_policy_files(policy_dir_path)
    block_rules = _collect_block_rules(policy_documents)

    for rule in block_rules:
        patterns = rule.get("patterns", [])
        if not isinstance(patterns, list):
            continue

        for pattern in patterns:
            if not isinstance(pattern, str):
                continue
            if re.search(pattern, query, flags=re.IGNORECASE):
                return PolicyDecision(
                    action="block",
                    rule_id=str(rule.get("id", "unknown-rule")),
                    reason=str(rule.get("reason", "Policy rule matched")),
                    redirect_message=str(
                        rule.get(
                            "redirect_message",
                            "This request is blocked by policy.",
                        )
                    ),
                )

    return PolicyDecision(
        action="allow",
        rule_id=None,
        reason="No policy rule matched",
        redirect_message=None,
    )
