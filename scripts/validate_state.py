#!/usr/bin/env python3
"""Validate ecommerce visual-suite schema-v3 workflow state."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


STAGES = {
    "S1_RESEARCH",
    "S2_PRODUCT_SELLING_POINT_REVIEW",
    "S3_STRATEGY_REVIEW",
    "S3_SELECTED_STRATEGY_EXECUTION",
    "S4_IMAGE_PRODUCTION",
}
FINGERPRINT_KEYS = {"product_fact", "product_image", "style_reference", "task_config", "research", "product"}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["state must be an object"]
    required = {
        "schema_version", "skill_version", "workflow_contract_version", "workflow_id", "product_key",
        "product_fingerprint", "fingerprints", "product_identity_lock_id", "product_identity_lock_status",
        "source_inventory", "current_stage", "task_profile", "visual_mode", "task_config", "flags",
        "approval_snapshot", "updated_at",
    }
    for key in sorted(required - set(data)):
        errors.append(f"$.{key} is required")
    if data.get("schema_version") != 3:
        errors.append("schema_version must be 3")
    if data.get("skill_version") != "3.0.0" or data.get("workflow_contract_version") != 3:
        errors.append("skill_version/workflow_contract_version must be 3.0.0/3")
    if data.get("current_stage") not in STAGES:
        errors.append("current_stage is unsupported")
    for key in ("workflow_id", "product_key", "product_fingerprint", "updated_at"):
        if not nonempty(data.get(key)):
            errors.append(f"{key} must not be empty")
    try:
        datetime.fromisoformat(str(data.get("updated_at")))
    except ValueError:
        errors.append("updated_at must be ISO-8601")

    fingerprints = data.get("fingerprints")
    if not isinstance(fingerprints, dict):
        errors.append("fingerprints must be an object")
    else:
        for key in sorted(FINGERPRINT_KEYS):
            if not nonempty(fingerprints.get(key)):
                errors.append(f"fingerprints.{key} must not be empty")
        if data.get("product_fingerprint") != fingerprints.get("product"):
            errors.append("product_fingerprint must equal fingerprints.product")

    config = data.get("task_config") if isinstance(data.get("task_config"), dict) else {}
    if data.get("task_profile") == "DETAIL_PAGE":
        expected = config.get("screen_count", 0) - 1 + config.get("screen2_card_count", 0)
        if config.get("image_count") != expected:
            errors.append("DETAIL_PAGE image_count must equal screen_count - 1 + screen2_card_count")

    flags = data.get("flags") if isinstance(data.get("flags"), dict) else {}
    approval = data.get("approval_snapshot") if isinstance(data.get("approval_snapshot"), dict) else {}
    research = flags.get("COMPETITOR_RESEARCH_COMPLETE") is True
    selling = flags.get("SELLING_POINTS_APPROVED") is True
    strategy = flags.get("STRATEGY_APPROVED") is True
    execution = flags.get("EXECUTION_PACKAGE_READY") is True
    if selling != (approval.get("selling_points_approved") is True):
        errors.append("selling-point flag and approval snapshot differ")
    if strategy != (approval.get("strategy_approved") is True):
        errors.append("strategy flag and approval snapshot differ")
    if selling and (not nonempty(approval.get("selling_point_approval_evidence")) or not approval.get("approved_selling_points")):
        errors.append("selling-point approval requires evidence and frozen points")
    if strategy and (approval.get("approved_strategy_id") not in {"A", "B", "C"} or not nonempty(approval.get("strategy_approval_evidence"))):
        errors.append("strategy approval requires A/B/C and evidence")

    receipts = data.get("delivery_receipts")
    if receipts is not None and not isinstance(receipts, dict):
        errors.append("delivery_receipts must be an object when present")
    authorization = data.get("production_authorization")
    if authorization is not None:
        if not isinstance(authorization, dict) or not nonempty(authorization.get("path")) or not nonempty(authorization.get("sha256")):
            errors.append("production_authorization must contain path and sha256 when present")

    stage = data.get("current_stage")
    requirements = {
        "S1_RESEARCH": (False, False, False, False),
        "S2_PRODUCT_SELLING_POINT_REVIEW": (True, False, False, False),
        "S3_STRATEGY_REVIEW": (True, True, False, False),
        "S3_SELECTED_STRATEGY_EXECUTION": (True, True, True, None),
        "S4_IMAGE_PRODUCTION": (True, True, True, True),
    }
    expected = requirements.get(stage)
    if expected:
        actual = (research, selling, strategy, execution)
        for index, required_value in enumerate(expected):
            if required_value is not None and actual[index] != required_value:
                errors.append(f"flags are inconsistent with {stage}")
                break
    # S3_STRATEGY_REVIEW intentionally does not require an S3A receipt: the S2
    # completion script lands here before S3A delivery. Skipping S3A entirely is
    # still blocked by complete_stage.py s3b, which demands the receipted package.
    if stage in {"S3_SELECTED_STRATEGY_EXECUTION", "S4_IMAGE_PRODUCTION"} and not isinstance(receipts, dict):
        errors.append("S3B/S4 state requires verified S3A and S3B delivery receipts")
    if stage in {"S3_SELECTED_STRATEGY_EXECUTION", "S4_IMAGE_PRODUCTION"} and isinstance(receipts, dict):
        if not isinstance(receipts.get("S3A"), dict) or not isinstance(receipts.get("S3B"), dict):
            errors.append("S3B/S4 state requires delivery_receipts.S3A and delivery_receipts.S3B")
    if stage == "S4_IMAGE_PRODUCTION" and authorization is None:
        errors.append("S4 state requires an explicit production_authorization")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.state.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate(data)
    if errors:
        print(f"ERROR: state failed validation with {len(errors)} error(s)", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("PASS: schema-v3 state is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
