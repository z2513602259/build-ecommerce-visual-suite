#!/usr/bin/env python3
"""Validate the human-readable S3 delivery package beside a strategy artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from validate_output import validate_data


S3A_FILES = (
    "strategy-package.json",
    "strategy-review.md",
    "strategy-A.md",
    "strategy-B.md",
    "strategy-C.md",
    "strategy-handoff.md",
    "review-package-manifest.json",
)
S3B_FILES = (
    "selected-strategy-package.json",
    "selected-strategy-review.md",
    "selected-strategy-handoff.md",
    "review-package-manifest.json",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return ""


def expected_files(stage: str) -> tuple[str, ...]:
    if stage == "S3_STRATEGY_REVIEW":
        return S3A_FILES
    if stage == "S3_SELECTED_STRATEGY_EXECUTION":
        return S3B_FILES
    return ()


def validate_package(strategy_path: Path) -> list[str]:
    errors: list[str] = []
    strategy_path = strategy_path.resolve()
    try:
        data: dict[str, Any] = json.loads(strategy_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return [f"strategy artifact does not exist: {strategy_path}"]
    except json.JSONDecodeError as exc:
        return [f"strategy artifact is not valid JSON: {exc}"]

    errors.extend(validate_data(data, strategy_path))
    stage = str(data.get("workflow_stage", ""))
    required = expected_files(stage)
    if not required:
        return errors + ["delivery package validation only supports S3A/S3B artifacts"]

    root = strategy_path.parent
    for name in required:
        if not (root / name).is_file():
            errors.append(f"required delivery file is missing: {name}")

    manifest_path = root / "review-package-manifest.json"
    if not manifest_path.is_file():
        return errors
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return errors + [f"review-package-manifest.json is invalid: {exc}"]
    if manifest.get("workflow_stage") != stage:
        errors.append("review-package manifest stage does not match strategy stage")
    if manifest.get("workflow_id") != data.get("workflow_id"):
        errors.append("review-package manifest workflow_id does not match strategy artifact")
    listed = manifest.get("files")
    if not isinstance(listed, list):
        return errors + ["review-package manifest files must be an array"]
    by_name = {entry.get("path"): entry for entry in listed if isinstance(entry, dict)}
    for name in required:
        if name == "review-package-manifest.json":
            continue
        entry = by_name.get(name)
        if not isinstance(entry, dict):
            errors.append(f"review-package manifest omits {name}")
        elif entry.get("sha256") != sha256(root / name):
            errors.append(f"review-package manifest hash mismatch for {name}")

    if stage == "S3_STRATEGY_REVIEW":
        overview = text_file(root / "strategy-review.md")
        if not all(f"方案{option}" in overview for option in "ABC"):
            errors.append("strategy-review.md does not contain an A/B/C comparison")
        handoff = text_file(root / "strategy-handoff.md")
        handoff_requirements = ("当前门控：等待选择方案", "方案总览（推荐先看）", "方案A审核书", "方案B审核书", "方案C审核书", "机器校验源（无需阅读）")
        if not all(item in handoff for item in handoff_requirements):
            errors.append("strategy-handoff.md is not a verified clickable S3A handoff")
        for option in "ABC":
            content = text_file(root / f"strategy-{option}.md")
            if "主标题" not in content or "说明文案" not in content or "逐图画面简报" not in content or "这套方案卖什么" not in content or "本屏解决的消费者问题" not in content:
                errors.append(f"strategy-{option}.md is not a complete readable option review")
    else:
        content = text_file(root / "selected-strategy-review.md")
        if "完整生图提示" not in content or "主标题" not in content or "这套方案卖什么" not in content or "本屏解决的消费者问题" not in content:
            errors.append("selected-strategy-review.md is not a complete selected execution review")
        handoff = text_file(root / "selected-strategy-handoff.md")
        if "当前门控：等待你明确要求生成图片" not in handoff or "选定方案执行书（推荐审核）" not in handoff:
            errors.append("selected-strategy-handoff.md is not a verified clickable S3B handoff")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("strategy_json", type=Path)
    args = parser.parse_args()
    errors = validate_package(args.strategy_json)
    if errors:
        print(f"FAIL: {len(errors)} delivery-package error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: human-readable S3 delivery package is complete and current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
