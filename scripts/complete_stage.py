#!/usr/bin/env python3
"""Render, validate, receipt, and advance a workflow delivery stage.

S1 and S2 verify evidence artifacts, record receipts, and open the next
gate. S3A and S3B additionally render their readable Markdown delivery
packages.
"""

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


STAGE_BY_COMMAND = {
    "s1": "S1_RESEARCH",
    "s2": "S2_PRODUCT_SELLING_POINT_REVIEW",
    "s3a": "S3_STRATEGY_REVIEW",
    "s3b": "S3_SELECTED_STRATEGY_EXECUTION",
}
RECEIPT_KEY = {"s1": "S1", "s2": "S2", "s3a": "S3A", "s3b": "S3B"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def write_json(path: Path, data: dict[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def receipted_artifact(state: dict[str, Any], state_path: Path, key: str) -> list[str]:
    """Verify that a prior evidence receipt still matches its artifact on disk."""
    receipts = state.get("delivery_receipts", {})
    receipt = receipts.get(key) if isinstance(receipts, dict) else None
    if not isinstance(receipt, dict) or not nonempty(receipt.get("artifact_path")) or not nonempty(receipt.get("artifact_sha256")):
        return [f"{key} receipt must include artifact_path and artifact_sha256"]
    root = state_path.parent.resolve()
    artifact_path = (root / str(receipt["artifact_path"])).resolve()
    try:
        artifact_path.relative_to(root)
    except ValueError:
        return [f"{key} receipt path escapes the workflow directory"]
    if not artifact_path.is_file() or receipt.get("artifact_sha256") != sha256(artifact_path):
        return [f"{key} receipt artifact is missing or changed since it was verified"]
    return []


def validate_s2_approval(approval: dict[str, Any], artifact: dict[str, Any]) -> list[str]:
    """Verify explicit approval and that approved points match the reviewed candidates."""
    errors: list[str] = []
    if approval.get("selling_points_approved") is not True:
        errors.append("S2 completion requires explicit user approval of the frozen selling points")
    if not nonempty(approval.get("selling_point_approval_evidence")):
        errors.append("S2 completion requires selling_point_approval_evidence")
    approved = approval.get("approved_selling_points")
    if not isinstance(approved, list) or not approved:
        errors.append("S2 completion requires approved_selling_points")
    else:
        non_objects = [str(index) for index, point in enumerate(approved) if not isinstance(point, dict)]
        if non_objects:
            errors.append(f"approved_selling_points contains non-object entries at indexes: {', '.join(non_objects)}")
            return errors
        candidates_by_id = {str(item.get("卖点ID")): item for item in artifact.get("selling_point_candidates", []) if isinstance(item, dict)}
        approved_ids = [str(point.get("卖点ID", "")) for point in approved]
        duplicate_ids = sorted({item for item in approved_ids if approved_ids.count(item) > 1})
        if duplicate_ids:
            errors.append(f"approved selling points contain duplicate IDs: {', '.join(duplicate_ids)}")
        for point in approved:
            point_id = str(point.get("卖点ID", ""))
            candidate = candidates_by_id.get(point_id)
            if candidate is None:
                errors.append(f"approved selling point {point_id or '?'} is not in the reviewed candidate set")
                continue
            point_keys = set(point.keys())
            candidate_keys = set(candidate.keys())
            missing_fields = candidate_keys - point_keys
            if missing_fields:
                errors.append(f"approved selling point {point_id} is missing frozen fields: {', '.join(sorted(missing_fields))}")
            unknown_fields = point_keys - candidate_keys
            if unknown_fields:
                errors.append(f"approved selling point {point_id} adds un-reviewed fields: {', '.join(sorted(unknown_fields))}")
            changed_fields = [
                key
                for key, value in point.items()
                if key != "卖点ID" and frozen_value(candidate.get(key)) != frozen_value(value)
            ]
            if changed_fields:
                errors.append(f"approved selling point {point_id} changes reviewed content in: {', '.join(sorted(changed_fields))}")
    return errors


def validate_prior_gate(stage: str, artifact: dict[str, Any], state_path: Path, state: dict[str, Any], backfill: bool = False) -> list[str]:
    """Refuse a manual jump past the verified prior delivery gate.

    In backfill mode the stage-position checks are skipped so a legacy
    pre-receipt state can recover its missing receipts in place; approval
    content validation still runs unchanged.
    """
    errors: list[str] = []
    approval = state.get("approval_snapshot", {})
    if not isinstance(approval, dict):
        approval = {}
    if backfill:
        receipts = state.get("delivery_receipts", {})
        existing = receipts.get(RECEIPT_KEY[stage]) if isinstance(receipts, dict) else None
        if isinstance(existing, dict):
            errors.append(f"state already has a {RECEIPT_KEY[stage]} receipt; backfill is unnecessary")
            return errors
        if stage == "s2":
            errors.extend(validate_s2_approval(approval, artifact))
        return errors
    if stage == "s1":
        if state.get("current_stage") != "S1_RESEARCH":
            errors.append("S1 completion requires state.current_stage to be S1_RESEARCH")
        return errors
    if stage == "s2":
        if state.get("current_stage") != "S2_PRODUCT_SELLING_POINT_REVIEW":
            errors.append("S2 completion requires a receipted S1 state; run complete_stage.py s1 first")
            return errors
        if state.get("flags", {}).get("COMPETITOR_RESEARCH_COMPLETE") is not True:
            errors.append("S2 completion requires COMPETITOR_RESEARCH_COMPLETE")
        errors.extend(receipted_artifact(state, state_path, "S1"))
        errors.extend(validate_s2_approval(approval, artifact))
        return errors
    if stage == "s3a":
        if state.get("current_stage") != "S3_STRATEGY_REVIEW":
            errors.append("S3A completion requires a receipted S2 state; run complete_stage.py s2 first")
            return errors
        errors.extend(receipted_artifact(state, state_path, "S1"))
        errors.extend(receipted_artifact(state, state_path, "S2"))
        if approval.get("selling_points_approved") is not True:
            errors.append("S3A completion requires an explicit frozen selling-point approval in state")
        if not nonempty(approval.get("selling_point_approval_evidence")) or not isinstance(approval.get("approved_selling_points"), list) or not approval.get("approved_selling_points"):
            errors.append("S3A completion requires selling-point approval evidence and frozen points")
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


def complete_evidence_stage(stage: str, artifact: dict[str, Any], artifact_path: Path, state: dict[str, Any], state_path: Path, backfill: bool = False) -> int:
    """Receipt an S1 or S2 evidence artifact and open the next gate.

    The stage advances only from its natural predecessor, so a backfill of a
    later-stage state adds receipts without rewinding or over-advancing it.
    """
    if state.get("workflow_id") != artifact.get("workflow_id") or state.get("product_fingerprint") != artifact.get("product_fingerprint"):
        print("ERROR: state and artifact do not identify the same product workflow", file=sys.stderr)
        return 1
    flags = state.setdefault("flags", {})
    if stage == "s1":
        flags["COMPETITOR_RESEARCH_COMPLETE"] = True
        if state.get("current_stage") == "S1_RESEARCH":
            state["current_stage"] = "S2_PRODUCT_SELLING_POINT_REVIEW"
        next_gate = "S2 selling-point review"
    else:
        flags["SELLING_POINTS_APPROVED"] = True
        if state.get("current_stage") == "S2_PRODUCT_SELLING_POINT_REVIEW":
            state["current_stage"] = "S3_STRATEGY_REVIEW"
        next_gate = "S3A strategy review"
    receipts = state.setdefault("delivery_receipts", {})
    receipts[RECEIPT_KEY[stage]] = {
        "artifact_path": artifact_path.name,
        "artifact_sha256": sha256(artifact_path),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    state["updated_at"] = datetime.now().astimezone().isoformat()
    state_errors = validate_state(state)
    if state_errors:
        print("ERROR: state would be invalid", file=sys.stderr)
        print("\n".join(f"- {error}" for error in state_errors), file=sys.stderr)
        return 1
    write_json(state_path, state)
    if backfill:
        print(f"PASS: {RECEIPT_KEY[stage]} receipt backfilled into state without advancing its stage")
    else:
        print(f"PASS: {STAGE_BY_COMMAND[stage]} delivery is verified, receipted, and ready for {next_gate}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=sorted(STAGE_BY_COMMAND))
    parser.add_argument("artifact_json", type=Path)
    parser.add_argument("state_json", type=Path)
    parser.add_argument("--backfill", action="store_true", help="add a missing receipt to a legacy pre-receipt v3 state without advancing its stage")
    args = parser.parse_args()
    if args.backfill and args.stage not in {"s1", "s2"}:
        print("ERROR: --backfill is only supported for s1 and s2", file=sys.stderr)
        return 2
    artifact_path = args.artifact_json.resolve()
    state_path = args.state_json.resolve()
    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8-sig"))
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    expected_stage = STAGE_BY_COMMAND[args.stage]
    if args.stage == "s1":
        if artifact.get("artifact_type") != "COMPETITOR_RESEARCH":
            print("ERROR: expected COMPETITOR_RESEARCH artifact", file=sys.stderr)
            return 1
    elif artifact.get("workflow_stage") != expected_stage:
        print(f"ERROR: expected {expected_stage} artifact", file=sys.stderr)
        return 1
    gate_errors = validate_prior_gate(args.stage, artifact, state_path, state, backfill=args.backfill)
    if gate_errors:
        print("ERROR: prior workflow gate is not complete", file=sys.stderr)
        print("\n".join(f"- {error}" for error in gate_errors), file=sys.stderr)
        return 1
    errors = validate_data(artifact, artifact_path)
    if errors:
        print("ERROR: artifact JSON is invalid", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    if args.stage in {"s1", "s2"}:
        return complete_evidence_stage(args.stage, artifact, artifact_path, state, state_path, backfill=args.backfill)
    render = Path(__file__).with_name("render_strategy_review.py")
    result = subprocess.run([sys.executable, str(render), str(artifact_path)], text=True, capture_output=True)
    if result.returncode:
        print(result.stdout + result.stderr, file=sys.stderr)
        return result.returncode
    errors = validate_package(artifact_path)
    if errors:
        print("ERROR: readable delivery package is incomplete", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    if state.get("workflow_id") != artifact.get("workflow_id") or state.get("product_fingerprint") != artifact.get("product_fingerprint"):
        print("ERROR: state and strategy artifact do not identify the same product workflow", file=sys.stderr)
        return 1
    if frozen_value(artifact.get("approval_snapshot")) != frozen_value(state.get("approval_snapshot")):
        print("ERROR: artifact approval_snapshot differs from the receipted state approval; refresh the artifact from state", file=sys.stderr)
        return 1
    approval = artifact.get("approval_snapshot", {})
    flags = state.setdefault("flags", {})
    state["current_stage"] = expected_stage
    flags["COMPETITOR_RESEARCH_COMPLETE"] = True
    flags["SELLING_POINTS_APPROVED"] = True
    flags["STRATEGY_APPROVED"] = args.stage == "s3b"
    flags["EXECUTION_PACKAGE_READY"] = args.stage == "s3b"
    state["approval_snapshot"] = approval
    receipts = state.setdefault("delivery_receipts", {})
    manifest_path = artifact_path.parent / "review-package-manifest.json"
    receipts[RECEIPT_KEY[args.stage]] = {
        "strategy_path": artifact_path.name,
        "strategy_sha256": sha256(artifact_path),
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
