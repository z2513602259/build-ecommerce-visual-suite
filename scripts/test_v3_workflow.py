#!/usr/bin/env python3
"""Regression and forward tests for schema-v3 workflow behavior."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


legacy = load("legacy_fixtures", "test_validate_output.py")
validator = load("validator_v3", "validate_output.py")
renderer = load("renderer_v3", "render_strategy_review.py")
delivery_validator = load("delivery_validator_v3", "validate_delivery_package.py")
stage_completer = load("stage_completer_v3", "complete_stage.py")
production_authorizer = load("production_authorizer_v3", "authorize_production.py")
state_validator = load("state_validator_v3", "validate_state.py")
fingerprint_builder = load("fingerprint_builder_v3", "build_source_fingerprints.py")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def component_fingerprints() -> dict[str, str]:
    return {
        "product_fact": "1" * 64,
        "product_image": "2" * 64,
        "style_reference": "3" * 64,
        "task_config": "4" * 64,
        "research": "5" * 64,
        "product": "6" * 64,
    }


def prepare_refs(root: Path, base: dict) -> dict[str, dict[str, str]]:
    lock_path = root / "product-identity-lock.json"
    lock_path.write_text(
        json.dumps(
            {
                "schema_version": 3,
                "skill_version": "3.0.0",
                "workflow_contract_version": 3,
                "workflow_id": base["workflow_id"],
                "product_fingerprint": "6" * 64,
                "fingerprints": component_fingerprints(),
                "artifact_type": "PRODUCT_IDENTITY_LOCK",
                "product_identity_lock": base["product_identity_lock"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    research = copy.deepcopy(base["competitor_research"])
    today = date.today().isoformat()
    research["research_date"] = today
    research["research_policy"] = {"max_age_days": 30, "as_of_date": today}
    for sample in research["samples"]:
        sample["访问状态"] = "ACCESSIBLE"
        sample["证据采集时间"] = today + "T10:00:00+08:00"
    research_path = root / "research.json"
    research_path.write_text(
        json.dumps(
            {
                "schema_version": 3,
                "skill_version": "3.0.0",
                "workflow_contract_version": 3,
                "workflow_id": base["workflow_id"],
                "product_fingerprint": "6" * 64,
                "fingerprints": component_fingerprints(),
                "artifact_type": "COMPETITOR_RESEARCH",
                "competitor_research": research,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return {
        "product_identity_lock": {"path": lock_path.name, "sha256": sha(lock_path)},
        "research": {"path": research_path.name, "sha256": sha(research_path)},
    }


def unique_copy(copy_data: dict, option_id: str) -> None:
    screens = copy_data.get("屏幕文案")
    if isinstance(screens, dict):
        for index, screen in enumerate(screens.values(), start=1):
            screen["主标题"] = f"收纳更清楚{index}"
            screen["副标题"] = f"分区看得懂{index}"
            screen["卖点短句"] = f"日常分类更清楚{index}"
            screen["说明文案"] = f"多层结构分区{index}，不同物品分类更清楚。"
            screen["CTA或承接语"] = f"先看细节{index}"
    units = copy_data.get("内容单元")
    if isinstance(units, list):
        for index, unit in enumerate(units, start=1):
            unit["主标题"] = f"选择更清楚{index}"
            unit["副标题"] = f"重点看得懂{index}"
            unit["卖点短句"] = f"购买判断更明白{index}"
            unit["说明文案"] = f"具体产品事实{index}，帮助购买判断更明白。"
            unit["CTA或承接语"] = f"先看重点{index}"


def to_brief(task: dict, option_id: str) -> dict:
    scene = task["场景设计"]
    brief = {
        "资产ID": task["资产ID"],
        "关联单元": task["关联单元"],
        "生成比例": task["生成比例"],
        "最终裁切比例": task["最终裁切比例"],
        "场景模式": scene["场景模式"],
        "证明目标": f"{option_id}方案证明{task['资产ID']}",
        "镜头重点": task["镜头重点"],
        "产品展示角度": task["产品展示角度"],
        "目标空间": scene["目标空间"],
    }
    for key in ("关联卖点ID", "卡位"):
        if key in task:
            brief[key] = task[key]
    return brief


def strategy_review_v3(root: Path, profile: str = "DETAIL_PAGE") -> tuple[dict, Path]:
    base = legacy.detail_strategy() if profile == "DETAIL_PAGE" else legacy.generic_strategy(profile, 3)
    refs = prepare_refs(root, base)
    data = copy.deepcopy(base)
    data.update(
        {
            "schema_version": 3,
            "skill_version": "3.0.0",
            "workflow_contract_version": 3,
            "product_fingerprint": "6" * 64,
            "fingerprints": component_fingerprints(),
            "workflow_stage": "S3_STRATEGY_REVIEW",
            "artifact_refs": refs,
            "shared_product_data": {
                "产品信息": base["options"][0]["产品信息"],
                "产品参数": base["options"][0]["产品参数"],
            },
        }
    )
    data.pop("product_identity_lock", None)
    data.pop("competitor_research", None)
    for index, option in enumerate(data["options"]):
        option["转化重点"] = ["快速理解", "品质信任", "使用适配"][index]
        tasks = option.pop("图片任务")
        option.pop("产品信息", None)
        option.pop("产品参数", None)
        unique_copy(option["文案成稿"], option["方案ID"])
        option["图片简报"] = [to_brief(task, option["方案ID"]) for task in tasks]
        screens = option["文案成稿"].get("屏幕文案", {})
        unit_ids = list(screens.keys()) if isinstance(screens, dict) else [item["单元ID"] for item in option["文案成稿"].get("内容单元", [])]
        option["购买叙事"] = {
            "核心购买主张": f"{option['方案ID']}方案用已确认产品事实建立明确购买理由",
            "首屏承诺": "先看产品为何值得选",
            "主要购买顾虑": ["产品是否符合当前需求", "关键事实是否足够明确"],
            "决策递进": ["先建立购买期待", "再给出产品证据", "核对使用或摆放适配", "消除下单顾虑并承接行动"],
            "文案气质": "直接、具体、面向购买决策",
        }
        option["文案质检"] = {
            "状态": "PASS",
            "本方案核心购买理由": f"以{option['方案ID']}方案的已确认事实回答购买顾虑",
            "泛化表达": [],
            "重复风险": [],
            "修正记录": ["已将泛化表达替换为当前产品事实锚点"],
            "单元检查": [
                {
                    "单元ID": unit_id,
                    "消费者决策问题": f"{unit_id}如何帮助我判断这款产品是否适合当前需求？",
                    "事实锚点": "当前产品已确认的材质、结构、尺寸或功能信息",
                    "产品专属性": "HIGH",
                    "购买理由明确": True,
                    "泛化表达": [],
                    "重复风险": [],
                    "修正记录": ["已补充事实锚点与消费者结果"],
                }
                for unit_id in unit_ids
            ],
        }
        if profile == "DETAIL_PAGE":
            screen2 = option["文案成稿"]["屏幕文案"]["第2屏"]
            brief_by_id = {item["资产ID"]: item for item in option["图片简报"]}
            for point in screen2["卖点总览"]:
                point["对应纯图资产"] = copy.deepcopy(brief_by_id[point["对应纯图资产"]["资产ID"]])
    path = root / "strategy-package.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data, path


def selected_execution_v3(root: Path, strategy_data: dict, strategy_path: Path) -> tuple[dict, Path]:
    legacy_full = legacy.detail_strategy()["options"][0]
    selected = copy.deepcopy(strategy_data["options"][0])
    selected["产品信息"] = strategy_data["shared_product_data"]["产品信息"]
    selected["产品参数"] = strategy_data["shared_product_data"]["产品参数"]
    selected["图片任务"] = copy.deepcopy(legacy_full["图片任务"])
    selected.pop("图片简报", None)
    source_option = strategy_data["options"][0]
    approval = copy.deepcopy(strategy_data["approval_snapshot"])
    approval.update({"strategy_approved": True, "approved_strategy_id": "A", "strategy_approval_evidence": "选择方案A"})
    data = {key: copy.deepcopy(value) for key, value in strategy_data.items() if key not in {"options", "shared_product_data"}}
    data.update(
        {
            "workflow_stage": "S3_SELECTED_STRATEGY_EXECUTION",
            "approval_snapshot": approval,
            "selected_strategy_id": "A",
            "strategy_source": {
                "path": strategy_path.name,
                "sha256": sha(strategy_path),
                "brief_ids": [brief["资产ID"] for brief in source_option["图片简报"]],
            },
            "selected_strategy": selected,
        }
    )
    path = root / "selected-strategy-package.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data, path


def production_authorization(root: Path, selected: dict, selected_path: Path, scope: list[str]) -> dict:
    authorization = {
        "schema_version": 3,
        "skill_version": "3.0.0",
        "workflow_id": selected["workflow_id"],
        "product_fingerprint": selected["product_fingerprint"],
        "selected_strategy_id": selected["selected_strategy_id"],
        "selected_execution_path": selected_path.name,
        "selected_execution_sha256": sha(selected_path),
        "approval_text": "开始生成方案A图片",
        "requested_scope": scope,
        "authorized_at": "2026-08-19T10:00:00+08:00",
    }
    path = root / "production-authorization.json"
    path.write_text(json.dumps(authorization, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"path": path.name, "sha256": sha(path)}


def s1_state() -> dict:
    return {
        "schema_version": 3,
        "skill_version": "3.0.0",
        "workflow_contract_version": 3,
        "workflow_id": "WF-TEST",
        "product_key": "brand/model",
        "product_fingerprint": "6" * 64,
        "fingerprints": component_fingerprints(),
        "product_identity_lock_id": "PIL",
        "product_identity_lock_status": "READY",
        "source_inventory": [],
        "current_stage": "S1_RESEARCH",
        "task_profile": "DETAIL_PAGE",
        "visual_mode": "FREE_FISSION_MODE",
        "task_config": {"target_platform": "JD", "image_count": 17, "screen_count": 12, "screen_count_override": False, "screen2_card_count": 6, "screen2_card_count_override": False, "output_ratios": [], "platform_safe_area": "待调研确认"},
        "flags": {"COMPETITOR_RESEARCH_COMPLETE": False, "SELLING_POINTS_APPROVED": False, "STRATEGY_APPROVED": False, "EXECUTION_PACKAGE_READY": False},
        "approval_snapshot": {"selling_points_approved": False, "selling_point_approval_evidence": "", "approved_selling_points": [], "strategy_approved": False, "approved_strategy_id": "", "strategy_approval_evidence": ""},
        "updated_at": "2026-08-19T10:00:00+08:00",
    }


def selling_point_review_v3(root: Path) -> tuple[dict, Path]:
    review = legacy.review_artifact()
    for candidate in review["selling_point_candidates"]:
        candidate.update(
            {
                "消费者决策问题": "这款产品的分区收纳是否匹配我的日常使用？",
                "利益类型": "功能利益",
                "具体消费者结果": "日常分类更清楚，取放更高效。",
                "表达边界": "仅陈述当前产品已确认的事实",
            }
        )
    refs = prepare_refs(root, review)
    review.update(
        {
            "schema_version": 3,
            "skill_version": "3.0.0",
            "workflow_contract_version": 3,
            "product_fingerprint": "6" * 64,
            "fingerprints": component_fingerprints(),
            "artifact_refs": refs,
        }
    )
    review.pop("product_identity_lock", None)
    path = root / "selling-point-review.json"
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    return review, path


def freeze_approval(approval: dict, review: dict) -> dict:
    """Freeze approved points as complete copies of the reviewed candidates."""
    candidates_by_id = {item["卖点ID"]: item for item in review["selling_point_candidates"]}
    frozen = copy.deepcopy(approval)
    frozen["approved_selling_points"] = [
        copy.deepcopy(candidates_by_id[point["卖点ID"]])
        if isinstance(point, dict) and point.get("卖点ID") in candidates_by_id
        else point
        for point in approval.get("approved_selling_points", [])
    ]
    return frozen


def run_completer(arguments: list[str]) -> int:
    old = sys.argv
    try:
        sys.argv = ["complete_stage.py", *arguments]
        return stage_completer.main()
    finally:
        sys.argv = old


def receipted_s2_state(root: Path, data: dict) -> dict:
    """Build a state that has passed the S1 and S2 scripts end to end."""
    base = legacy.review_artifact()
    refs = prepare_refs(root, base)
    state_path = root / "state.json"
    state_path.write_text(json.dumps(s1_state(), ensure_ascii=False), encoding="utf-8")
    assert run_completer(["s1", str(root / refs["research"]["path"]), str(state_path)]) == 0
    review, review_path = selling_point_review_v3(root)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["approval_snapshot"] = freeze_approval(data["approval_snapshot"], review)
    state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    assert run_completer(["s2", str(review_path), str(state_path)]) == 0
    return json.loads(state_path.read_text(encoding="utf-8"))


def s2_state(data: dict) -> dict:
    """Legacy pre-receipt state: S2 approved by hand, no S1/S2 receipts."""
    return {
        "schema_version": 3,
        "skill_version": "3.0.0",
        "workflow_contract_version": 3,
        "workflow_id": data["workflow_id"],
        "product_key": "brand/model",
        "product_fingerprint": data["product_fingerprint"],
        "fingerprints": component_fingerprints(),
        "product_identity_lock_id": "PIL",
        "product_identity_lock_status": "READY",
        "source_inventory": [],
        "current_stage": "S2_PRODUCT_SELLING_POINT_REVIEW",
        "task_profile": data["task_profile"],
        "visual_mode": data["visual_mode"],
        "task_config": data["task_config"],
        "flags": {"COMPETITOR_RESEARCH_COMPLETE": True, "SELLING_POINTS_APPROVED": True, "STRATEGY_APPROVED": False, "EXECUTION_PACKAGE_READY": False},
        "approval_snapshot": copy.deepcopy(data["approval_snapshot"]),
        "updated_at": "2026-08-19T10:00:00+08:00",
    }


class V3WorkflowTests(unittest.TestCase):
    def test_valid_s3a_and_layered_handoff(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data, path = strategy_review_v3(root)
            self.assertEqual(validator.validate_data(data, path), [])
            old = sys.argv
            try:
                sys.argv = ["render_strategy_review.py", str(path)]
                self.assertEqual(renderer.main(), 0)
            finally:
                sys.argv = old
            for name in ("strategy-review.md", "strategy-A.md", "strategy-B.md", "strategy-C.md", "strategy-handoff.md", "review-package-manifest.json"):
                self.assertTrue((root / name).is_file(), name)
            self.assertEqual(delivery_validator.validate_package(path), [])
            review = (root / "strategy-A.md").read_text(encoding="utf-8")
            self.assertNotIn("完整生图提示", review)
            self.assertIn("这套方案卖什么", review)
            self.assertIn("本屏解决的消费者问题", review)

    def test_s3a_delivery_package_is_required(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, path = strategy_review_v3(root)
            self.assertTrue(any("required delivery file is missing" in error for error in delivery_validator.validate_package(path)))

    def test_s3a_handoff_must_be_clickable_and_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, path = strategy_review_v3(root)
            old = sys.argv
            try:
                sys.argv = ["render_strategy_review.py", str(path)]
                self.assertEqual(renderer.main(), 0)
            finally:
                sys.argv = old
            (root / "strategy-handoff.md").write_text("# A/B/C方案交付\n", encoding="utf-8")
            self.assertTrue(any("verified clickable S3A handoff" in error for error in delivery_validator.validate_package(path)))

    def test_s3a_requires_purchase_narrative_and_copy_quality(self):
        with tempfile.TemporaryDirectory() as folder:
            data, path = strategy_review_v3(Path(folder))
            data["options"][0].pop("购买叙事")
            data["options"][1]["文案质检"]["单元检查"][0]["产品专属性"] = "MEDIUM"
            errors = validator.validate_data(data, path)
            self.assertTrue(any("购买叙事" in error for error in errors))
            self.assertTrue(any("产品专属性 must be HIGH" in error for error in errors))

    def test_customer_copy_rejects_generic_page_label(self):
        with tempfile.TemporaryDirectory() as folder:
            data, path = strategy_review_v3(Path(folder))
            data["options"][0]["文案成稿"]["屏幕文案"]["第3屏"]["主标题"] = "材质"
            errors = validator.validate_data(data, path)
            self.assertTrue(any("generic page label" in error for error in errors))

    def test_customer_copy_rejects_generic_benefit_as_complete_line(self):
        with tempfile.TemporaryDirectory() as folder:
            data, path = strategy_review_v3(Path(folder))
            data["options"][0]["文案成稿"]["屏幕文案"]["第3屏"]["卖点短句"] = "更清楚"
            errors = validator.validate_data(data, path)
            self.assertTrue(any("generic benefit as the complete copy" in error for error in errors))

    def test_stage_completion_and_explicit_production_authorization(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            strategy, strategy_path = strategy_review_v3(root)
            state = receipted_s2_state(root, strategy)
            # Bind the S3A package to the receipted frozen approval snapshot.
            strategy["approval_snapshot"] = copy.deepcopy(state["approval_snapshot"])
            strategy_path.write_text(json.dumps(strategy, ensure_ascii=False, indent=2), encoding="utf-8")
            state_path = root / "state.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s3a", str(strategy_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 0)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["current_stage"], "S3_STRATEGY_REVIEW")
            self.assertIn("S3A", state["delivery_receipts"])
            selected, selected_path = selected_execution_v3(root, strategy, strategy_path)
            # The user's A/B/C choice updates the state approval before S3B.
            state["approval_snapshot"] = copy.deepcopy(selected["approval_snapshot"])
            state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s3b", str(selected_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 0)
                sys.argv = ["authorize_production.py", str(selected_path), str(state_path), "--approval-text", "继续", "--scope", selected["selected_strategy"]["图片任务"][0]["资产ID"]]
                self.assertEqual(production_authorizer.main(), 1)
                sys.argv = ["authorize_production.py", str(selected_path), str(state_path), "--approval-text", "开始生成方案A图片", "--scope", selected["selected_strategy"]["图片任务"][0]["资产ID"]]
                self.assertEqual(production_authorizer.main(), 0)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["current_stage"], "S4_IMAGE_PRODUCTION")
            self.assertIn("production_authorization", state)

    def test_s3a_rejects_downgraded_approval_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            strategy, strategy_path = strategy_review_v3(root)
            # The S3A package still carries the legacy five-field snapshot while
            # the receipted state holds the complete frozen points.
            state = receipted_s2_state(root, strategy)
            self.assertGreater(len(state["approval_snapshot"]["approved_selling_points"][0]), 5)
            state_path = root / "state.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s3a", str(strategy_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 1)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertNotIn("S3A", state.get("delivery_receipts", {}))
            # The frozen snapshot must not have been downgraded by the rejected run.
            self.assertGreater(len(state["approval_snapshot"]["approved_selling_points"][0]), 5)

    def test_s3a_cannot_bypass_s2_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            strategy, strategy_path = strategy_review_v3(root)
            # Hand-edited legacy state: approval present but no S2 receipt.
            state_path = root / "state.json"
            state_path.write_text(json.dumps(s2_state(strategy), ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s3a", str(strategy_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 1)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertNotIn("S3A", state.get("delivery_receipts", {}))

    def test_s1_receipt_opens_s2_and_s2_requires_explicit_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            base = legacy.review_artifact()
            refs = prepare_refs(root, base)
            research_path = root / refs["research"]["path"]
            state_path = root / "state.json"
            state_path.write_text(json.dumps(s1_state(), ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s1", str(research_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 0)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["current_stage"], "S2_PRODUCT_SELLING_POINT_REVIEW")
            self.assertTrue(state["flags"]["COMPETITOR_RESEARCH_COMPLETE"])
            self.assertIn("S1", state["delivery_receipts"])
            self.assertEqual(state_validator.validate(state), [])

            review, review_path = selling_point_review_v3(root)
            old = sys.argv
            try:
                # Approval is still pending in state; S2 must refuse.
                sys.argv = ["complete_stage.py", "s2", str(review_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 1)
            finally:
                sys.argv = old
            state["approval_snapshot"] = freeze_approval(legacy.approval(6), review)
            state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s2", str(review_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 0)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["current_stage"], "S3_STRATEGY_REVIEW")
            self.assertTrue(state["flags"]["SELLING_POINTS_APPROVED"])
            self.assertIn("S2", state["delivery_receipts"])
            self.assertEqual(state_validator.validate(state), [])

    def test_s2_rejects_approval_of_unreviewed_selling_points(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            base = legacy.review_artifact()
            refs = prepare_refs(root, base)
            research_path = root / refs["research"]["path"]
            state_path = root / "state.json"
            state_path.write_text(json.dumps(s1_state(), ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s1", str(research_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 0)
            finally:
                sys.argv = old
            review, review_path = selling_point_review_v3(root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            approved = freeze_approval(legacy.approval(6), review)
            rogue = copy.deepcopy(approved["approved_selling_points"][0])
            rogue["卖点ID"] = "CSP-999"
            approved["approved_selling_points"].append(rogue)
            state["approval_snapshot"] = approved
            state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s2", str(review_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 1)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["current_stage"], "S2_PRODUCT_SELLING_POINT_REVIEW")
            self.assertNotIn("S2", state["delivery_receipts"])

    def test_s2_rejects_tampered_approved_content(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            base = legacy.review_artifact()
            refs = prepare_refs(root, base)
            research_path = root / refs["research"]["path"]
            state_path = root / "state.json"
            state_path.write_text(json.dumps(s1_state(), ensure_ascii=False), encoding="utf-8")
            assert run_completer(["s1", str(research_path), str(state_path)]) == 0
            review, review_path = selling_point_review_v3(root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            approved = freeze_approval(legacy.approval(6), review)
            # ID stays in the candidate set; the reviewed fact is silently rewritten.
            approved["approved_selling_points"][0]["具体产品事实"] = "被篡改的事实"
            state["approval_snapshot"] = approved
            state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s2", str(review_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 1)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertNotIn("S2", state.get("delivery_receipts", {}))

    def test_s2_rejects_deleted_approved_field(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            base = legacy.review_artifact()
            refs = prepare_refs(root, base)
            research_path = root / refs["research"]["path"]
            state_path = root / "state.json"
            state_path.write_text(json.dumps(s1_state(), ensure_ascii=False), encoding="utf-8")
            assert run_completer(["s1", str(research_path), str(state_path)]) == 0
            review, review_path = selling_point_review_v3(root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            approved = freeze_approval(legacy.approval(6), review)
            # Deleting a frozen field must fail the same way rewriting it does.
            del approved["approved_selling_points"][0]["具体产品事实"]
            state["approval_snapshot"] = approved
            state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s2", str(review_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 1)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertNotIn("S2", state.get("delivery_receipts", {}))

    def test_s2_rejects_deleted_extended_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            base = legacy.review_artifact()
            refs = prepare_refs(root, base)
            research_path = root / refs["research"]["path"]
            state_path = root / "state.json"
            state_path.write_text(json.dumps(s1_state(), ensure_ascii=False), encoding="utf-8")
            assert run_completer(["s1", str(research_path), str(state_path)]) == 0
            review, review_path = selling_point_review_v3(root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            approved = freeze_approval(legacy.approval(6), review)
            # Deleting all four v3 extended fields must fail the same way as a partial set.
            for key in ("消费者决策问题", "利益类型", "具体消费者结果", "表达边界"):
                del approved["approved_selling_points"][0][key]
            state["approval_snapshot"] = approved
            state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s2", str(review_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 1)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertNotIn("S2", state.get("delivery_receipts", {}))

    def test_s2_rejects_deleted_research_metadata_field(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            base = legacy.review_artifact()
            refs = prepare_refs(root, base)
            research_path = root / refs["research"]["path"]
            state_path = root / "state.json"
            state_path.write_text(json.dumps(s1_state(), ensure_ascii=False), encoding="utf-8")
            assert run_completer(["s1", str(research_path), str(state_path)]) == 0
            review, review_path = selling_point_review_v3(root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            approved = freeze_approval(legacy.approval(6), review)
            # Every candidate field is frozen; deleting research metadata is the same violation.
            del approved["approved_selling_points"][0]["风险或待确认项"]
            state["approval_snapshot"] = approved
            state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s2", str(review_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 1)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertNotIn("S2", state.get("delivery_receipts", {}))

    def test_s2_rejects_duplicate_approved_selling_point_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            base = legacy.review_artifact()
            refs = prepare_refs(root, base)
            research_path = root / refs["research"]["path"]
            state_path = root / "state.json"
            state_path.write_text(json.dumps(s1_state(), ensure_ascii=False), encoding="utf-8")
            assert run_completer(["s1", str(research_path), str(state_path)]) == 0
            review, review_path = selling_point_review_v3(root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            approved = freeze_approval(legacy.approval(6), review)
            # Duplicating a complete frozen point must be rejected at the S2 gate,
            # not deferred to a downstream duplicate check.
            approved["approved_selling_points"].append(copy.deepcopy(approved["approved_selling_points"][0]))
            state["approval_snapshot"] = approved
            state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s2", str(review_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 1)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertNotIn("S2", state.get("delivery_receipts", {}))

    def test_s2_rejects_non_object_approval_entries(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            base = legacy.review_artifact()
            refs = prepare_refs(root, base)
            research_path = root / refs["research"]["path"]
            state_path = root / "state.json"
            state_path.write_text(json.dumps(s1_state(), ensure_ascii=False), encoding="utf-8")
            assert run_completer(["s1", str(research_path), str(state_path)]) == 0
            review, review_path = selling_point_review_v3(root)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            approved = freeze_approval(legacy.approval(6), review)
            # Non-object entries must be rejected explicitly, never silently skipped.
            approved["approved_selling_points"].append("not a selling-point object")
            state["approval_snapshot"] = approved
            state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s2", str(review_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 1)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertNotIn("S2", state.get("delivery_receipts", {}))

    def test_backfill_recovers_legacy_pre_receipt_state(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            base = legacy.review_artifact()
            refs = prepare_refs(root, base)
            research_path = root / refs["research"]["path"]
            review, review_path = selling_point_review_v3(root)
            state_path = root / "state.json"
            # Legacy hand-approved state: at S2 with approval but no receipts.
            legacy_state = s2_state(review)
            legacy_state["approval_snapshot"] = freeze_approval(legacy.approval(6), review)
            state_path.write_text(json.dumps(legacy_state, ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                # s2 first: it advances the legacy S2 state into a valid stage.
                sys.argv = ["complete_stage.py", "s2", str(review_path), str(state_path), "--backfill"]
                self.assertEqual(stage_completer.main(), 0)
                sys.argv = ["complete_stage.py", "s1", str(research_path), str(state_path), "--backfill"]
                self.assertEqual(stage_completer.main(), 0)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertIn("S1", state["delivery_receipts"])
            self.assertIn("S2", state["delivery_receipts"])
            # The s2 backfill advances the legacy S2 state into a valid stage.
            self.assertEqual(state["current_stage"], "S3_STRATEGY_REVIEW")
            self.assertEqual(state_validator.validate(state), [])

    def test_s3a_requires_s1_receipt_after_backfill(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            base = legacy.review_artifact()
            refs = prepare_refs(root, base)
            review, review_path = selling_point_review_v3(root)
            strategy, strategy_path = strategy_review_v3(root)
            state_path = root / "state.json"
            legacy_state = s2_state(strategy)
            legacy_state["approval_snapshot"] = freeze_approval(legacy.approval(6), review)
            state_path.write_text(json.dumps(legacy_state, ensure_ascii=False), encoding="utf-8")
            # Only s2 --backfill runs; the documented s1 --backfill is skipped.
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s2", str(review_path), str(state_path), "--backfill"]
                self.assertEqual(stage_completer.main(), 0)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertIn("S2", state["delivery_receipts"])
            self.assertNotIn("S1", state["delivery_receipts"])
            # S3A must refuse until the S1 receipt also exists.
            strategy["approval_snapshot"] = copy.deepcopy(state["approval_snapshot"])
            strategy_path.write_text(json.dumps(strategy, ensure_ascii=False, indent=2), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s3a", str(strategy_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 1)
            finally:
                sys.argv = old
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertNotIn("S3A", state.get("delivery_receipts", {}))

    def test_s1_cannot_complete_from_later_stage(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            base = legacy.review_artifact()
            refs = prepare_refs(root, base)
            research_path = root / refs["research"]["path"]
            state_path = root / "state.json"
            later = s1_state()
            later["current_stage"] = "S3_STRATEGY_REVIEW"
            later["flags"]["COMPETITOR_RESEARCH_COMPLETE"] = True
            later["flags"]["SELLING_POINTS_APPROVED"] = True
            state_path.write_text(json.dumps(later, ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s1", str(research_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 1)
            finally:
                sys.argv = old

    def test_s3b_cannot_bypass_s3a_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            strategy, strategy_path = strategy_review_v3(root)
            selected, selected_path = selected_execution_v3(root, strategy, strategy_path)
            state = receipted_s2_state(root, strategy)
            state_path = root / "state.json"
            state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["complete_stage.py", "s3b", str(selected_path), str(state_path)]
                self.assertEqual(stage_completer.main(), 1)
            finally:
                sys.argv = old

    def test_s3a_rejects_duplicate_copy_and_weak_option_difference(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data, path = strategy_review_v3(root)
            screens = data["options"][0]["文案成稿"]["屏幕文案"]
            screens["第2屏"]["主标题"] = screens["第1屏"]["主标题"]
            for key in ("转化重点", "视觉世界观", "色彩策略", "光影策略", "版式语言"):
                data["options"][1][key] = data["options"][0][key]
            data["options"][1]["图片简报"] = copy.deepcopy(data["options"][0]["图片简报"])
            errors = validator.validate_data(data, path)
            self.assertTrue(any("duplicate copy" in error for error in errors))
            self.assertTrue(any("at least three" in error for error in errors))

    def test_valid_s3b_preserves_selected_strategy_and_renders_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            strategy, strategy_path = strategy_review_v3(root)
            selected, selected_path = selected_execution_v3(root, strategy, strategy_path)
            self.assertEqual(validator.validate_data(selected, selected_path), [])
            old = sys.argv
            try:
                sys.argv = ["render_strategy_review.py", str(selected_path)]
                self.assertEqual(renderer.main(), 0)
            finally:
                sys.argv = old
            review = (root / "selected-strategy-review.md").read_text(encoding="utf-8")
            self.assertIn("完整生图提示", review)
            self.assertTrue((root / "selected-strategy-handoff.md").is_file())
            self.assertEqual(delivery_validator.validate_package(selected_path), [])

    def test_s3b_rejects_changed_approved_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            strategy, strategy_path = strategy_review_v3(root)
            selected, selected_path = selected_execution_v3(root, strategy, strategy_path)
            selected["selected_strategy"]["文案成稿"]["屏幕文案"]["第1屏"]["主标题"] = "擅自改文案"
            errors = validator.validate_data(selected, selected_path)
            self.assertTrue(any("differs from the approved S3A option" in error for error in errors))

    def test_research_recency_is_enforced(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data, path = strategy_review_v3(root)
            research_path = root / data["artifact_refs"]["research"]["path"]
            research_doc = json.loads(research_path.read_text(encoding="utf-8"))
            research_doc["competitor_research"]["research_date"] = (date.today() - timedelta(days=40)).isoformat()
            research_path.write_text(json.dumps(research_doc, ensure_ascii=False), encoding="utf-8")
            data["artifact_refs"]["research"]["sha256"] = sha(research_path)
            errors = validator.validate_data(data, path)
            self.assertTrue(any("older than" in error for error in errors))

    def test_s4_retry_limit_and_execution_binding(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            strategy, strategy_path = strategy_review_v3(root)
            selected, selected_path = selected_execution_v3(root, strategy, strategy_path)
            tasks = selected["selected_strategy"]["图片任务"]
            assets = []
            for task in tasks:
                asset = copy.deepcopy(task)
                asset.update(
                    {
                        "输出路径": "",
                        "生成状态": "PENDING",
                        "attempt_count": 0,
                        "max_attempts": 3,
                        "last_error": "",
                        "retry_decision": "PENDING",
                        "纯图检查": {"status": "PENDING", "notes": "pending"},
                        "产品保真检查": legacy.fidelity_check("PENDING"),
                        "场景适配检查": {"status": "PENDING", "notes": "pending"},
                    }
                )
                assets.append(asset)
            manifest = {key: copy.deepcopy(value) for key, value in selected.items() if key not in {"selected_strategy", "strategy_source", "selected_strategy_id"}}
            old = sys.argv
            try:
                sys.argv = ["render_strategy_review.py", str(selected_path)]
                self.assertEqual(renderer.main(), 0)
            finally:
                sys.argv = old
            manifest.update(
                {
                    "workflow_stage": "S4_IMAGE_PRODUCTION",
                    "approved_strategy_id": "A",
                    "execution_package_ref": {"path": selected_path.name, "sha256": sha(selected_path)},
                    "requested_scope": [assets[0]["资产ID"]],
                    "production_authorization_ref": production_authorization(root, selected, selected_path, [assets[0]["资产ID"]]),
                    "assets": assets,
                    "audit_result": legacy.audit("PENDING"),
                }
            )
            manifest_path = root / "image-manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            self.assertEqual(validator.validate_data(manifest, manifest_path), [])
            manifest["assets"][0]["attempt_count"] = 3
            errors = validator.validate_data(manifest, manifest_path)
            self.assertTrue(any("must stop after max_attempts" in error for error in errors))

    def test_s4_rejects_continue_as_production_authorization(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            strategy, strategy_path = strategy_review_v3(root)
            selected, selected_path = selected_execution_v3(root, strategy, strategy_path)
            authorization_ref = production_authorization(root, selected, selected_path, [selected["selected_strategy"]["图片任务"][0]["资产ID"]])
            authorization_path = root / authorization_ref["path"]
            authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
            authorization["approval_text"] = "继续"
            authorization_path.write_text(json.dumps(authorization, ensure_ascii=False), encoding="utf-8")
            authorization_ref["sha256"] = sha(authorization_path)
            task = copy.deepcopy(selected["selected_strategy"]["图片任务"][0])
            task.update({"输出路径": "", "生成状态": "PENDING", "attempt_count": 0, "max_attempts": 3, "last_error": "", "retry_decision": "PENDING", "纯图检查": {"status": "PENDING", "notes": "pending"}, "产品保真检查": legacy.fidelity_check("PENDING"), "场景适配检查": {"status": "PENDING", "notes": "pending"}})
            manifest = {key: copy.deepcopy(value) for key, value in selected.items() if key not in {"selected_strategy", "strategy_source", "selected_strategy_id"}}
            manifest.update({"workflow_stage": "S4_IMAGE_PRODUCTION", "approved_strategy_id": "A", "execution_package_ref": {"path": selected_path.name, "sha256": sha(selected_path)}, "production_authorization_ref": authorization_ref, "requested_scope": [task["资产ID"]], "assets": [task], "audit_result": legacy.audit("PENDING")})
            # The first failure is the malformed asset count; the authorization error must still be visible.
            errors = validator.validate_data(manifest, root / "image-manifest.json")
            self.assertTrue(any("explicit image-production request" in error for error in errors))

    def test_cross_category_forward_fixtures_do_not_leak_product_identity(self):
        names = {"DETAIL_PAGE": "家具事实", "MAIN_IMAGE": "美妆事实", "PROMO_POSTER": "三C事实"}
        rendered = {}
        for profile, marker in names.items():
            with tempfile.TemporaryDirectory() as folder:
                data, _ = strategy_review_v3(Path(folder), profile)
                data["product_identity"] = {"产品": marker}
                rendered[profile] = renderer.render_review(data)
        for profile, marker in names.items():
            self.assertIn(marker, rendered[profile])
            for other in set(names.values()) - {marker}:
                self.assertNotIn(other, rendered[profile])


class StateAndFingerprintTests(unittest.TestCase):
    def test_component_fingerprints_change_only_for_changed_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            product = root / "product.txt"
            style = root / "style.txt"
            product.write_text("fact", encoding="utf-8")
            style.write_text("warm", encoding="utf-8")
            inventory_path = root / "source-inventory.json"
            inventory = {"workspace": str(root), "sources": [{"path": "product.txt", "scope": "PRODUCT_FACT"}, {"path": "style.txt", "scope": "STYLE_REFERENCE"}], "task_config": {"ratio": "9:16"}}
            first = fingerprint_builder.build(inventory, inventory_path)
            style.write_text("cool", encoding="utf-8")
            second = fingerprint_builder.build(inventory, inventory_path)
            self.assertEqual(first["fingerprints"]["product"], second["fingerprints"]["product"])
            self.assertNotEqual(first["fingerprints"]["style_reference"], second["fingerprints"]["style_reference"])

    def test_state_stage_and_flags_are_consistent(self):
        state = {
            "schema_version": 3,
            "skill_version": "3.0.0",
            "workflow_contract_version": 3,
            "workflow_id": "WF",
            "product_key": "brand/model",
            "product_fingerprint": "6" * 64,
            "fingerprints": component_fingerprints(),
            "product_identity_lock_id": "PIL",
            "product_identity_lock_status": "READY",
            "source_inventory": [],
            "current_stage": "S3_STRATEGY_REVIEW",
            "task_profile": "DETAIL_PAGE",
            "visual_mode": "FREE_FISSION_MODE",
            "task_config": {"image_count": 17, "screen_count": 12, "screen2_card_count": 6},
            "flags": {"COMPETITOR_RESEARCH_COMPLETE": True, "SELLING_POINTS_APPROVED": True, "STRATEGY_APPROVED": False, "EXECUTION_PACKAGE_READY": False},
            "approval_snapshot": {"selling_points_approved": True, "selling_point_approval_evidence": "确认", "approved_selling_points": [{"卖点ID": "CSP-001"}], "strategy_approved": False, "approved_strategy_id": "", "strategy_approval_evidence": ""},
            "updated_at": "2026-08-18T10:00:00+08:00",
            "delivery_receipts": {"S3A": {"strategy_path": "strategy-package.json", "strategy_sha256": "a", "manifest_path": "review-package-manifest.json", "manifest_sha256": "b", "completed_at": "2026-08-18T10:00:00+08:00"}},
        }
        self.assertEqual(state_validator.validate(state), [])
        state["flags"]["STRATEGY_APPROVED"] = True
        self.assertTrue(state_validator.validate(state))


if __name__ == "__main__":
    unittest.main(verbosity=2)
