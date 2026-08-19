#!/usr/bin/env python3
"""Build deterministic component fingerprints from a source inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SCOPES = {
    "PRODUCT_FACT",
    "PRODUCT_IMAGE",
    "STYLE_REFERENCE",
    "LAYOUT_REFERENCE",
    "REDESIGN_SOURCE",
    "TASK_CONFIG",
    "RESEARCH_EVIDENCE",
}


def stable_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_parts(parts: list[bytes]) -> str:
    hasher = hashlib.sha256()
    for part in sorted(parts):
        hasher.update(len(part).to_bytes(8, "big"))
        hasher.update(part)
    return hasher.hexdigest()


def build(inventory: dict[str, Any], inventory_path: Path) -> dict[str, Any]:
    workspace = Path(inventory.get("workspace") or inventory_path.parent).expanduser()
    if not workspace.is_absolute():
        workspace = (inventory_path.parent / workspace).resolve()
    else:
        workspace = workspace.resolve()
    sources = inventory.get("sources")
    if not isinstance(sources, list):
        raise ValueError("sources must be a list")

    grouped: dict[str, list[bytes]] = {scope: [] for scope in SCOPES}
    records = []
    for index, item in enumerate(sources):
        if not isinstance(item, dict):
            raise ValueError(f"sources[{index}] must be an object")
        scope = item.get("scope")
        if scope not in SCOPES:
            raise ValueError(f"sources[{index}].scope is unsupported: {scope}")
        raw_path = item.get("path")
        value = item.get("value")
        if raw_path:
            path = (workspace / str(raw_path)).resolve()
            try:
                relative = path.relative_to(workspace).as_posix()
            except ValueError as exc:
                raise ValueError(f"sources[{index}].path escapes workspace: {raw_path}") from exc
            if not path.is_file():
                raise ValueError(f"sources[{index}].path does not exist: {raw_path}")
            file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            payload = stable_json({"path": relative, "sha256": file_hash})
            records.append({"path": relative, "scope": scope, "sha256": file_hash})
        elif value is not None:
            payload = stable_json({"value": value})
            records.append({"path": "", "scope": scope, "sha256": hashlib.sha256(payload).hexdigest()})
        else:
            raise ValueError(f"sources[{index}] requires path or value")
        grouped[scope].append(payload)

    if inventory.get("task_config") is not None:
        grouped["TASK_CONFIG"].append(stable_json(inventory.get("task_config")))

    product_fact = digest_parts(grouped["PRODUCT_FACT"])
    product_image = digest_parts(grouped["PRODUCT_IMAGE"])
    style_reference = digest_parts(
        grouped["STYLE_REFERENCE"] + grouped["LAYOUT_REFERENCE"] + grouped["REDESIGN_SOURCE"]
    )
    task_config = digest_parts(grouped["TASK_CONFIG"])
    research = digest_parts(grouped["RESEARCH_EVIDENCE"])
    product = digest_parts([product_fact.encode(), product_image.encode()])
    return {
        "schema_version": 3,
        "skill_version": "3.0.0",
        "fingerprints": {
            "product_fact": product_fact,
            "product_image": product_image,
            "style_reference": style_reference,
            "task_config": task_config,
            "research": research,
            "product": product,
        },
        "source_records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        inventory = json.loads(args.inventory.read_text(encoding="utf-8-sig"))
        result = build(inventory, args.inventory.resolve())
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.dry_run:
        print(rendered, end="")
        return 0
    output = args.output or args.inventory.with_name("fingerprints.json")
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(output)
    print(f"PASS: fingerprints written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
