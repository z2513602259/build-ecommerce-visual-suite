#!/usr/bin/env python3
"""Migrate ecommerce visual-suite workflow state v1/v2 to v3."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from validate_state import validate as validate_state


VALID_PROFILES = {"DETAIL_PAGE", "MAIN_IMAGE", "PROMO_POSTER"}
VALID_MODES = {"REDESIGN_MODE", "STYLE_FUSION_MODE", "STYLE_GUIDED_MODE", "FREE_FISSION_MODE"}


def rich_approved_points(value: Any) -> bool:
    required = {"卖点ID", "类别", "具体产品事实", "可转化利益", "本品事实来源"}
    return isinstance(value, list) and bool(value) and all(isinstance(item, dict) and required <= set(item) for item in value)


def load_fingerprints(value: dict[str, Any]) -> dict[str, str]:
    fingerprints = value.get("fingerprints") if isinstance(value.get("fingerprints"), dict) else value
    keys = ("product_fact", "product_image", "style_reference", "task_config", "research", "product")
    if not all(isinstance(fingerprints.get(key), str) and fingerprints.get(key) for key in keys):
        raise ValueError("fingerprints file must contain all six nonempty component fingerprints")
    return {key: fingerprints[key] for key in keys}


def migrate(data: dict[str, Any], fingerprints: dict[str, str]) -> tuple[dict[str, Any], list[str]]:
    if data.get("schema_version") == 3:
        return data, ["state is already schema version 3"]
    notes: list[str] = []
    old_flags = data.get("flags") if isinstance(data.get("flags"), dict) else {}
    old_approval = data.get("approval_snapshot") if isinstance(data.get("approval_snapshot"), dict) else {}
    stored_product = str(data.get("product_fingerprint") or data.get("source_fingerprint") or "")
    product_matches = bool(stored_product) and stored_product == fingerprints["product"]
    if not product_matches:
        notes.append("product fingerprint changed or was unavailable: all approvals cleared")

    selling_evidence = str(
        old_approval.get("selling_point_approval_evidence")
        or data.get("selling_point_approval_evidence")
        or data.get("approval_evidence")
        or ""
    ).strip()
    approved_points = old_approval.get("approved_selling_points") or data.get("approved_selling_points") or []
    selling_approved = (
        product_matches
        and bool(old_flags.get("SELLING_POINTS_APPROVED") or old_approval.get("selling_points_approved"))
        and bool(selling_evidence)
        and rich_approved_points(approved_points)
    )
    strategy_id = str(old_approval.get("approved_strategy_id") or data.get("approved_strategy_id") or "").strip()
    strategy_evidence = str(old_approval.get("strategy_approval_evidence") or data.get("strategy_approval_evidence") or "").strip()
    strategy_approved = (
        selling_approved
        and bool(old_flags.get("STRATEGY_APPROVED") or old_approval.get("strategy_approved"))
        and strategy_id in {"A", "B", "C"}
        and bool(strategy_evidence)
    )
    research_complete = product_matches and bool(old_flags.get("COMPETITOR_RESEARCH_COMPLETE"))
    lock_ready = data.get("product_identity_lock_status") == "READY" and bool(data.get("product_identity_lock_id"))
    if not lock_ready:
        notes.append("a READY v3-compatible product identity lock was not proven: returned to S1")
        research_complete = selling_approved = strategy_approved = False

    profile = data.get("task_profile") if data.get("task_profile") in VALID_PROFILES else "DETAIL_PAGE"
    mode = data.get("visual_mode") if data.get("visual_mode") in VALID_MODES else "FREE_FISSION_MODE"
    old_config = data.get("task_config") if isinstance(data.get("task_config"), dict) else {}
    if profile == "DETAIL_PAGE":
        screen_count = int(old_config.get("screen_count", 12))
        card_count = int(old_config.get("screen2_card_count", 6))
        image_count = screen_count - 1 + card_count
    else:
        screen_count = card_count = 0
        image_count = int(old_config.get("image_count", 1))

    if not research_complete:
        stage = "S1_RESEARCH"
    elif not selling_approved:
        stage = "S2_PRODUCT_SELLING_POINT_REVIEW"
    elif not strategy_approved:
        stage = "S3_STRATEGY_REVIEW"
    else:
        stage = "S3_SELECTED_STRATEGY_EXECUTION"
    execution_ready = False
    product_key = str(data.get("product_key") or "unconfirmed/current-folder")
    migrated = {
        "schema_version": 3,
        "skill_version": "3.0.0",
        "workflow_contract_version": 3,
        "workflow_id": str(data.get("workflow_id") or uuid.uuid5(uuid.NAMESPACE_URL, product_key)),
        "product_key": product_key,
        "product_fingerprint": fingerprints["product"],
        "fingerprints": fingerprints,
        "product_identity_lock_id": str(data.get("product_identity_lock_id") or ""),
        "product_identity_lock_status": "READY" if lock_ready else "BLOCKED",
        "source_inventory": data.get("source_inventory", []),
        "current_stage": stage,
        "task_profile": profile,
        "visual_mode": mode,
        "task_config": {
            "target_platform": old_config.get("target_platform", "未明确"),
            "image_count": image_count,
            "screen_count": screen_count,
            "screen_count_override": bool(old_config.get("screen_count_override", False)),
            "screen2_card_count": card_count,
            "screen2_card_count_override": bool(old_config.get("screen2_card_count_override", False)),
            "output_ratios": old_config.get("output_ratios", []),
            "platform_safe_area": old_config.get("platform_safe_area", "待调研确认"),
        },
        "flags": {
            "COMPETITOR_RESEARCH_COMPLETE": research_complete,
            "SELLING_POINTS_APPROVED": selling_approved,
            "STRATEGY_APPROVED": strategy_approved,
            "EXECUTION_PACKAGE_READY": execution_ready,
        },
        "approval_snapshot": {
            "selling_points_approved": selling_approved,
            "selling_point_approval_evidence": selling_evidence if selling_approved else "",
            "approved_selling_points": approved_points if selling_approved else [],
            "strategy_approved": strategy_approved,
            "approved_strategy_id": strategy_id if strategy_approved else "",
            "strategy_approval_evidence": strategy_evidence if strategy_approved else "",
        },
        "migration_notes": notes,
        "updated_at": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
    }
    return migrated, notes


def backup_path_for(path: Path) -> Path:
    candidate = path.with_name(f"{path.stem}.pre-v3-backup{path.suffix}")
    counter = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}.pre-v3-backup-{counter}{path.suffix}")
        counter += 1
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--fingerprints", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(args.state.read_text(encoding="utf-8-sig"))
        fingerprint_data = json.loads(args.fingerprints.read_text(encoding="utf-8-sig"))
        fingerprints = load_fingerprints(fingerprint_data)
        migrated, notes = migrate(data, fingerprints)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_state(migrated)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    rendered = json.dumps(migrated, ensure_ascii=False, indent=2) + "\n"
    if args.dry_run:
        print(rendered, end="")
    else:
        backup = backup_path_for(args.state)
        backup.write_bytes(args.state.read_bytes())
        temporary = args.state.with_name(args.state.name + ".tmp")
        temporary.write_text(rendered, encoding="utf-8")
        temporary.replace(args.state)
        print(f"PASS: migrated state written to {args.state}")
        print(f"PASS: previous state backed up to {backup}")
    for note in notes:
        print(f"NOTE: {note}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
