#!/usr/bin/env python3
"""Render, validate, receipt, and advance an S3A or S3B delivery stage."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_delivery_package import validate_package
from validate_output import validate_data
from validate_state import validate as validate_state


STAGE_BY_COMMAND = {"s3a": "S3_STRATEGY_REVIEW", "s3b": "S3_SELECTED_STRATEGY_EXECUTION"}
RECEIPT_KEY = {"s3a": "S3A", "s3b": "S3B"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: dict[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def validate_prior_gate(stage: str, strategy_path: Path, state_path: Path, state: dict[str, Any]) -> list[str]:
    """Refuse a manual jump past the verified prior delivery gate."""
    errors: list[str] = []
    if stage == "s3a":
        if state.get("current_stage") != "S2_PRODUCT_SELLING_POINT_REVIEW":
            errors.append("S3A completion requires state.current_stage to be S2_PRODUCT_SELLING_POINT_REVIEW")
        approval = state.get("approval_snapshot", {})
        if not isinstance(approval, dict) or approval.get("selling_points_approved") is not True:
            errors.append("S3A completion requires an explicit frozen selling-point approval in state")
        return errors

    if state.get("current_stage") != "S3_STRATEGY_REVIEW":
        errors.append("S3B completion requires a verified S3A state; do not jump from S2 or a chat summary")
        return errors
    receipts = state.get("delivery_receipts", {})
    receipt = receipts.get("S3A") if isinstance(receipts, dict) else None
    if not isinstance(receipt, dict):
        errors.append("S3B completion requires delivery_receipts.S3A")
        return errors
    source_name = receipt.get("strategy_path")
    manifest_name = receipt.get("manifest_path")
    if not isinstance(source_name, str) or not isinstance(manifest_name, str):
        errors.append("S3A receipt must include strategy_path and manifest_path")
        return errors
    root = state_path.parent.resolve()
    source_path = (root / source_name).resolve()
    manifest_path = (root / manifest_name).resolve()
    try:
        source_path.relative_to(root)
        manifest_path.relative_to(root)
    except ValueError:
        return ["S3A receipt path escapes the workflow directory"]
    if not source_path.is_file() or not manifest_path.is_file():
        errors.append("S3B completion requires the receipted S3A package and manifest files")
        return errors
    if receipt.get("strategy_sha256") != sha256(source_path) or receipt.get("manifest_sha256") != sha256(manifest_path):
        errors.append("S3B completion requires an unchanged receipted S3A package and manifest")
    errors.extend(validate_package(source_path))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=sorted(STAGE_BY_COMMAND))
    parser.add_argument("strategy_json", type=Path)
    parser.add_argument("state_json", type=Path)
    args = parser.parse_args()
    strategy_path = args.strategy_json.resolve()
    state_path = args.state_json.resolve()
    try:
        strategy = json.loads(strategy_path.read_text(encoding="utf-8-sig"))
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    expected_stage = STAGE_BY_COMMAND[args.stage]
    if strategy.get("workflow_stage") != expected_stage:
        print(f"ERROR: expected {expected_stage} artifact", file=sys.stderr)
        return 1
    gate_errors = validate_prior_gate(args.stage, strategy_path, state_path, state)
    if gate_errors:
        print("ERROR: prior workflow gate is not complete", file=sys.stderr)
        print("\n".join(f"- {error}" for error in gate_errors), file=sys.stderr)
        return 1
    errors = validate_data(strategy, strategy_path)
    if errors:
        print("ERROR: strategy JSON is invalid", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    render = Path(__file__).with_name("render_strategy_review.py")
    result = subprocess.run([sys.executable, str(render), str(strategy_path)], text=True, capture_output=True)
    if result.returncode:
        print(result.stdout + result.stderr, file=sys.stderr)
        return result.returncode
    errors = validate_package(strategy_path)
    if errors:
        print("ERROR: readable delivery package is incomplete", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    if state.get("workflow_id") != strategy.get("workflow_id") or state.get("product_fingerprint") != strategy.get("product_fingerprint"):
        print("ERROR: state and strategy artifact do not identify the same product workflow", file=sys.stderr)
        return 1
    approval = strategy.get("approval_snapshot", {})
    flags = state.setdefault("flags", {})
    state["current_stage"] = expected_stage
    flags["COMPETITOR_RESEARCH_COMPLETE"] = True
    flags["SELLING_POINTS_APPROVED"] = True
    flags["STRATEGY_APPROVED"] = args.stage == "s3b"
    flags["EXECUTION_PACKAGE_READY"] = args.stage == "s3b"
    state["approval_snapshot"] = approval
    receipts = state.setdefault("delivery_receipts", {})
    manifest_path = strategy_path.parent / "review-package-manifest.json"
    receipts[RECEIPT_KEY[args.stage]] = {
        "strategy_path": strategy_path.name,
        "strategy_sha256": sha256(strategy_path),
        "manifest_path": manifest_path.name,
        "manifest_sha256": sha256(manifest_path),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    if args.stage == "s3a":
        state.pop("production_authorization", None)
    state["updated_at"] = datetime.now().astimezone().isoformat()
    state_errors = validate_state(state)
    if state_errors:
        print("ERROR: state would be invalid", file=sys.stderr)
        print("\n".join(f"- {error}" for error in state_errors), file=sys.stderr)
        return 1
    write_json(state_path, state)
    print(f"PASS: {expected_stage} delivery is rendered, verified, receipted, and ready for its next gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
