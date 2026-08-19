#!/usr/bin/env python3
"""Record an explicit user image-production authorization for a selected S3B package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_delivery_package import validate_package
from validate_state import validate as validate_state


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def explicit_production_request(text: str, option: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    has_action = "开始生成" in compact or "开始制作" in compact or "开始生图" in compact
    has_option = f"方案{option}" in compact or option in compact
    has_image = "图片" in compact or "纯图" in compact or "生图" in compact
    return has_action and has_option and has_image


def write_json(path: Path, data: dict[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selected_strategy_json", type=Path)
    parser.add_argument("state_json", type=Path)
    parser.add_argument("--approval-text", required=True)
    parser.add_argument("--scope", nargs="+", required=True)
    args = parser.parse_args()
    selected_path = args.selected_strategy_json.resolve()
    state_path = args.state_json.resolve()
    try:
        selected = json.loads(selected_path.read_text(encoding="utf-8-sig"))
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if selected.get("workflow_stage") != "S3_SELECTED_STRATEGY_EXECUTION":
        print("ERROR: selected strategy package must be S3B", file=sys.stderr)
        return 1
    if state.get("current_stage") != "S3_SELECTED_STRATEGY_EXECUTION":
        print("ERROR: image production requires a verified S3B state; a chat summary or hand-written execution file is insufficient", file=sys.stderr)
        return 1
    state_errors = validate_state(state)
    if state_errors:
        print("ERROR: current workflow state is not a verified S3B gate", file=sys.stderr)
        print("\n".join(f"- {error}" for error in state_errors), file=sys.stderr)
        return 1
    option = str(selected.get("selected_strategy_id", ""))
    if option not in {"A", "B", "C"} or not explicit_production_request(args.approval_text, option):
        print("ERROR: approval text must explicitly request image production for the selected A/B/C option; generic continue/confirm messages are invalid", file=sys.stderr)
        return 1
    errors = validate_package(selected_path)
    if errors:
        print("ERROR: selected execution delivery is not ready", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    tasks = selected.get("selected_strategy", {}).get("图片任务", [])
    task_ids = {item.get("资产ID") for item in tasks if isinstance(item, dict)}
    if not set(args.scope) <= task_ids:
        print("ERROR: --scope contains an asset that is not in the selected execution package", file=sys.stderr)
        return 1
    authorization_path = selected_path.with_name("production-authorization.json")
    authorization = {
        "schema_version": 3,
        "skill_version": "3.0.0",
        "workflow_id": selected.get("workflow_id"),
        "product_fingerprint": selected.get("product_fingerprint"),
        "selected_strategy_id": option,
        "selected_execution_path": selected_path.name,
        "selected_execution_sha256": sha256(selected_path),
        "approval_text": args.approval_text,
        "requested_scope": args.scope,
        "authorized_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(authorization_path, authorization)
    state["current_stage"] = "S4_IMAGE_PRODUCTION"
    state["production_authorization"] = {"path": authorization_path.name, "sha256": sha256(authorization_path)}
    state["updated_at"] = datetime.now().astimezone().isoformat()
    errors = validate_state(state)
    if errors:
        print("ERROR: state would be invalid", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    write_json(state_path, state)
    print("PASS: explicit production authorization recorded; S4 may now create only the requested assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
