#!/usr/bin/env python3
"""Regression tests for the visual-suite validator and state migration."""

from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validator = load_module("visual_suite_validator", "validate_output.py")
migrator = load_module("visual_suite_migrator", "migrate_state.py")
renderer = load_module("visual_suite_review_renderer", "render_strategy_review.py")


def source(index: int = 1):
    return [{"source_id": f"SRC-{index}", "source_type": "当前产品文件", "location": f"params.txt:{index}", "claim": f"fact-{index}"}]


def research(sample_count: int = 6, source_count: int = 2):
    samples = []
    for index in range(sample_count):
        samples.append(
            {
                "样本ID": f"RS-{index + 1:02d}",
                "来源平台或网站": f"site-{index % source_count + 1}",
                "来源类型": "品牌官网",
                "品牌或商品名": f"product-{index + 1}",
                "链接": f"https://example.com/{index + 1}",
                "访问日期": "2026-08-13",
                "与本品相似依据": "same category",
                "详情页板块顺序": ["hook", "proof"],
                "主要卖点与阐述方式": ["fact with close-up"],
                "证据表达方式": ["parameter"],
                "可借鉴模式": "clear proof",
                "应避免模式": "unsupported promise",
                "来源可信度": "MEDIUM",
                "来源限制": "public visible content only",
            }
        )
    return {
        "research_status": "COMPLETE",
        "research_date": "2026-08-13",
        "platforms": ["site-1", "site-2"],
        "public_web_sources": ["https://example.com"],
        "search_queries": ["test product detail page"],
        "samples": samples,
        "research_limitations": {"is_limited": False, "reason": "", "attempted_fallback_routes": [], "confidence": "HIGH"},
        "高频消费者关注点": ["fact"],
        "共性板块": ["proof"],
        "同质化表达": ["generic"],
        "差异化机会": ["current fact"],
        "平台差异": ["density"],
    }


def approval(point_count: int = 6, strategy: bool = False):
    points = []
    for index in range(point_count):
        points.append(
            {
                "卖点ID": f"CSP-{index + 1:03d}",
                "类别": f"类别{index + 1}",
                "具体产品事实": f"fact-{index + 1}",
                "可转化利益": f"日常分类更清楚{index + 1}",
                "本品事实来源": source(index + 1),
            }
        )
    return {
        "selling_points_approved": True,
        "selling_point_approval_evidence": "用户明确确认这组卖点",
        "approved_selling_points": points,
        "strategy_approved": strategy,
        "approved_strategy_id": "A" if strategy else "",
        "strategy_approval_evidence": "用户明确选择A" if strategy else "",
    }


def audit(status: str = "PASS"):
    if status != "PASS":
        return {"status": status, "perspectives": {}, "redline_checks": [], "correction_log": []}
    return {
        "status": "PASS",
        "perspectives": {
            "商业操盘": {"结论": "pass", "风险": []},
            "视觉设计": {"结论": "pass", "风险": []},
            "技术执行": {"结论": "pass", "风险": []},
            "转化心理": {"结论": "pass", "风险": []},
        },
        "redline_checks": [
            {"redline_id": f"R{index}", "status": "PASS", "findings": [], "corrections": []}
            for index in range(1, 13)
        ],
        "correction_log": [],
    }


PROHIBITIONS = [
    "禁止任何文字和乱码",
    "禁止标题和副标题",
    "禁止标签、价格与CTA",
    "禁止图标和尺寸线",
    "禁止拼贴、网格和卡片框",
    "禁止为文字刻意留白或预留区域",
    "禁止虚构或改变产品结构及新增部件",
]


def product_image_source(index: int = 1):
    return [{"source_id": f"IMG-{index}", "source_type": "当前产品图片", "location": f"product-{index:02d}.jpg", "claim": f"visible-feature-{index}"}]


def identity_lock(status: str = "READY"):
    return {
        "锁定ID": "PIL-TEST",
        "锁定状态": status,
        "主参考图ID": ["VIEW-01"] if status == "READY" else [],
        "角度参考": [
            {
                "参考图ID": "VIEW-01",
                "文件路径": "product-01.jpg",
                "视角": "three-quarter view",
                "角色": "主参考",
                "可证明特征ID": ["PF-01"],
            }
        ] if status == "READY" else [],
        "不可变特征": [
            {
                "特征ID": "PF-01",
                "类别": "structure",
                "特征描述": "original silhouette and part arrangement",
                "重要级别": "CRITICAL",
                "本品事实来源": product_image_source(1),
            }
        ] if status == "READY" else [],
        "允许变化": ["background", "environment light"] if status == "READY" else [],
        "条件变化": [],
        "禁止推断": ["unseen structure"] if status == "READY" else [],
        "未确认项": [],
    }


def fidelity_check(status: str = "PASS"):
    item_status = "PASS" if status == "PASS" else "PENDING"
    return {
        "status": status,
        "notes": "checked" if status == "PASS" else "pending",
        "检查项": {
            name: {"status": item_status, "notes": "checked" if status == "PASS" else "pending"}
            for name in validator.FIDELITY_CHECK_ITEMS
        },
    }


def image_task(asset_id: str, unit: str, basis, ratio: str = "1:1", selling_point_id: str = "", position: str = ""):
    task = {
        "资产ID": asset_id,
        "关联单元": unit,
        "生成比例": ratio,
        "最终裁切比例": ratio,
        "平台安全区": "post-layout only",
        "镜头重点": "product detail",
        "产品展示角度": "three-quarter view",
        "所用原图参考": ["product-01.jpg"],
        "保真执行": {
            "生成方式": "单图参考生成",
            "主参考图ID": "VIEW-01",
            "辅助参考图ID": [],
            "锁定特征ID": ["PF-01"],
            "允许变化": ["background", "environment light"],
            "禁止变化": ["silhouette", "part arrangement"],
            "角度匹配说明": "three-quarter view directly matches VIEW-01",
            "结构推断风险": "NONE",
        },
        "场景设计": {
            "场景模式": "产品肖像",
            "模式理由": "完整展示产品比例与外观",
            "目标空间": "不适用（产品肖像）",
            "摆放与使用关系": "受控展示，不承担真实空间使用叙事",
            "空间锚点": [],
            "尺度参照": [],
            "辅助元素": [],
            "协调逻辑": "中性背景衬托产品，不使用与产品竞争的装饰材料",
            "场景事实边界": "只表达当前产品外观，不宣称特定空间适配",
        },
        "独立生图提示": "Generate one complete product-faithful image with no added typography.",
        "禁止项": copy.deepcopy(PROHIBITIONS),
        "对应的真实产品依据": copy.deepcopy(basis),
    }
    if selling_point_id:
        task["关联卖点ID"] = selling_point_id
    if position:
        task["卡位"] = position
    return task


def base_common(profile: str, config: dict, approved):
    return {
        "schema_version": 2,
        "workflow_id": "WF-TEST",
        "product_fingerprint": "FP-TEST",
        "product_identity_lock": identity_lock(),
        "workflow_stage": "S3_STRATEGY_AND_FULL_DELIVERY",
        "task_profile": profile,
        "visual_mode": "FREE_FISSION_MODE",
        "style_direction": "",
        "visual_mode_reason": "no controlling reference or style direction",
        "input_classification": [],
        "task_config": config,
        "approval_snapshot": approved,
        "audit_result": audit(),
    }


def detail_strategy(card_count: int = 6, override: bool = False):
    approved = approval(card_count)
    positions = validator.DEFAULT_SIX_POSITIONS if card_count == 6 and not override else [f"自定义卡位{index}" for index in range(1, card_count + 1)]
    layout = [
        {"卡片ID": f"SP-{index:02d}", "卡位": positions[index - 1], "建议卡片比例": "1:1"}
        for index in range(1, card_count + 1)
    ]
    config = {
        "target_platform": "JD",
        "image_count": 11 + card_count,
        "screen_count": 12,
        "screen_count_override": False,
        "screen2_card_count": card_count,
        "screen2_card_count_override": override,
        "output_ratios": ["1:1"],
        "platform_safe_area": "post-layout safe area",
        "screen2_layout_spec": layout,
    }
    data = base_common("DETAIL_PAGE", config, approved)
    data.update({"product_identity": {"产品": "test"}, "competitor_research": research(), "options": []})
    for option_index, option_id in enumerate(("A", "B", "C"), start=1):
        tasks = []
        cards = []
        for index, point in enumerate(approved["approved_selling_points"], start=1):
            sequence = f"SP-{index:02d}"
            task = image_task(f"S2-{sequence}", "第2屏", point["本品事实来源"], "1:1", point["卖点ID"], positions[index - 1])
            tasks.append(task)
            cards.append(
                {
                    "卖点ID": sequence,
                    "来源卖点ID": point["卖点ID"],
                    "卖点三行文案": {"类别": point["类别"], "具体特征": point["具体产品事实"], "简短利益": point["可转化利益"]},
                    "对应的真实产品依据": copy.deepcopy(point["本品事实来源"]),
                    "对应纯图资产": copy.deepcopy(task),
                }
            )
        screens = {}
        for screen_index in range(1, 13):
            screen_name = f"第{screen_index}屏"
            screen = {
                "页面职责": "hook" if screen_index != 2 else ("六大卖点总览" if card_count == 6 and not override else "卖点总览"),
                "主标题": "五抽分区",
                "副标题": "收纳更清楚",
                "卖点短句": "不同物品分层归类",
                "说明文案": "五层抽屉独立分区，不同物品更好分类，日常取放更清楚。",
                "CTA或承接语": "再看怎么收",
                "对应的真实产品依据": source(1),
            }
            if screen_index == 2:
                screen["卖点总览"] = cards
            else:
                tasks.append(image_task(f"SCREEN-{screen_index:02d}", screen_name, source(1)))
            screens[screen_name] = screen
        option = {
            "方案ID": option_id,
            "方案定位": f"position-{option_id}",
            "目标平台": "JD",
            "任务类型": "DETAIL_PAGE",
            "期望图片数量": 11 + card_count,
            "文案模式": "电商转化型",
            "文案语调指引": "restrained",
            "风格名称": f"style-{option_id}",
            "视觉世界观": f"world-{option_id}",
            "色彩策略": f"color-{option_id}",
            "光影策略": f"light-{option_id}",
            "核心材质库": ["material"],
            "版式语言": f"layout-{option_id}",
            "产品信息": {"name": "test"},
            "产品参数": {"fact": "test"},
            "设计风格标签": [f"tag-{option_id}"],
            "文案成稿": {"屏幕文案": screens},
            "图片任务": tasks,
            "纯图生成约束": "禁止文字、CTA、刻意留白、拼贴、乱码、标签、价格、尺寸线和改变产品结构",
            "下游执行注意事项": "copy and collage in post-layout only",
        }
        data["options"].append(option)
    return data


def pending_approval():
    return {
        "selling_points_approved": False,
        "selling_point_approval_evidence": "",
        "approved_selling_points": [],
        "strategy_approved": False,
        "approved_strategy_id": "",
        "strategy_approval_evidence": "",
    }


def selling_point_candidate(index: int):
    return {
        "卖点ID": f"CSP-{index:03d}",
        "类别": f"类别{index}",
        "具体产品事实": f"fact-{index}",
        "可转化利益": f"日常分类更清楚{index}",
        "本品事实来源": source(index),
        "竞品调研依据": ["RS-01"],
        "证据类型": "参数文件",
        "证据强度": "HIGH",
        "市场判断": "differentiated opportunity",
        "推荐级别": "CORE",
        "适合的视觉证明方式": "close-up",
        "风险或待确认项": [],
    }


def blocked_artifact():
    data = detail_strategy()
    for key in ("options", "competitor_research", "product_identity"):
        data.pop(key)
    data.update(
        {
            "workflow_stage": "S1_COMPETITOR_RESEARCH_BLOCKED",
            "approval_snapshot": pending_approval(),
            "audit_result": audit("BLOCKED"),
            "research_status": "INCOMPLETE",
            "product_identity": {"产品": "test"},
            "attempted_platforms": ["JD"],
            "attempted_queries": ["test product"],
            "public_fallback_sources_attempted": ["brand sites"],
            "accessible_evidence": [],
            "blocking_reasons": ["no responsible evidence"],
            "required_user_input": ["catalog"],
            "blocked_next_steps": ["S2", "S3", "S4"],
        }
    )
    return data


def review_artifact():
    data = detail_strategy()
    data.pop("options")
    data.update(
        {
            "workflow_stage": "S2_PRODUCT_SELLING_POINT_REVIEW",
            "approval_snapshot": pending_approval(),
            "audit_result": audit("PENDING"),
            "approval_status": "PENDING_USER_APPROVAL",
            "selling_point_candidates": [selling_point_candidate(index) for index in range(1, 7)],
            "recommended_core_set": [f"CSP-{index:03d}" for index in range(1, 7)],
            "rejected_or_unverifiable_claims": [],
            "missing_information": [],
            "confirmation_request": "请确认保留、删除、修改和排序的卖点。",
            "blocked_next_steps": ["S3", "S4"],
        }
    )
    return data


def generic_strategy(profile: str = "MAIN_IMAGE", image_count: int = 5):
    approved = approval(3)
    config = {
        "target_platform": "Tmall",
        "image_count": image_count,
        "screen_count": 0,
        "screen_count_override": False,
        "screen2_card_count": 0,
        "screen2_card_count_override": False,
        "output_ratios": ["1:1"],
        "platform_safe_area": "center product safe area",
    }
    data = base_common(profile, config, approved)
    data.update({"product_identity": {"产品": "cross-category test"}, "competitor_research": research(), "options": []})
    for option_id in ("A", "B", "C"):
        tasks = [image_task(f"{option_id}-ASSET-{index:02d}", f"UNIT-{index:02d}", source(1)) for index in range(1, image_count + 1)]
        units = []
        for index in range(1, image_count + 1):
            units.append(
                {
                    "单元ID": f"UNIT-{index:02d}",
                    "页面职责": "one purchase reason",
                    "主标题": "五抽分区",
                    "副标题": "收纳更清楚",
                    "卖点短句": "不同物品分层归类",
                    "说明文案": "五层抽屉独立分区，不同物品更好分类，日常取放更清楚。",
                    "CTA或承接语": "再看怎么收",
                    "对应的真实产品依据": source(1),
                }
            )
        data["options"].append(
            {
                "方案ID": option_id,
                "方案定位": f"position-{option_id}",
                "目标平台": "Tmall",
                "任务类型": profile,
                "期望图片数量": image_count,
                "文案模式": "电商转化型",
                "文案语调指引": "restrained",
                "风格名称": f"style-{option_id}",
                "视觉世界观": f"world-{option_id}",
                "色彩策略": f"color-{option_id}",
                "光影策略": f"light-{option_id}",
                "核心材质库": ["material"],
                "版式语言": f"layout-{option_id}",
                "产品信息": {"name": "test"},
                "产品参数": {"fact": "test"},
                "设计风格标签": [f"tag-{option_id}"],
                "文案成稿": {"内容单元": units},
                "图片任务": tasks,
                "纯图生成约束": "禁止文字、CTA、刻意留白、拼贴、乱码、标签、价格、尺寸线和改变产品结构",
                "下游执行注意事项": "post-layout only",
            }
        )
    return data


class ValidatorTests(unittest.TestCase):
    def test_valid_standalone_product_identity_lock(self):
        data = {
            "schema_version": 2,
            "artifact_type": "PRODUCT_IDENTITY_LOCK",
            "workflow_id": "WF-TEST",
            "product_fingerprint": "FP-TEST",
            "product_identity_lock": identity_lock(),
        }
        self.assertEqual(validator.validate_data(data), [])

    def test_valid_s1_blocked(self):
        self.assertEqual(validator.validate_data(blocked_artifact()), [])

    def test_valid_s2_review(self):
        self.assertEqual(validator.validate_data(review_artifact()), [])

    def test_valid_default_detail_page(self):
        self.assertEqual(validator.validate_data(detail_strategy()), [])

    def test_s3_requires_ready_product_identity_lock(self):
        data = detail_strategy()
        data["product_identity_lock"]["锁定状态"] = "LIMITED"
        errors = validator.validate_data(data)
        self.assertTrue(any("锁定状态 must be READY for S3/S4" in error for error in errors))

    def test_text_only_product_recreation_is_rejected(self):
        data = detail_strategy()
        task = next(item for item in data["options"][0]["图片任务"] if item["资产ID"] == "SCREEN-01")
        task["保真执行"]["生成方式"] = "纯文字生成"
        errors = validator.validate_data(data)
        self.assertTrue(any("text-only product recreation is prohibited" in error for error in errors))

    def test_task_reference_must_exist_in_identity_lock(self):
        data = detail_strategy()
        task = next(item for item in data["options"][0]["图片任务"] if item["资产ID"] == "SCREEN-01")
        task["保真执行"]["主参考图ID"] = "VIEW-404"
        errors = validator.validate_data(data)
        self.assertTrue(any("主参考图ID is not in product_identity_lock" in error for error in errors))

    def test_valid_five_card_override(self):
        self.assertEqual(validator.validate_data(detail_strategy(card_count=5, override=True)), [])

    def test_all_non_detail_profiles(self):
        profiles = {
            "MAIN_IMAGE": 5,
            "PROMO_POSTER": 3,
        }
        for profile, count in profiles.items():
            with self.subTest(profile=profile):
                self.assertEqual(validator.validate_data(generic_strategy(profile, count)), [])

    def test_removed_task_profiles_are_rejected(self):
        for profile in ("PRODUCT_CARD", "SOCIAL_SEEDING", "SELLING_POINT_IMAGE", "LIVESTREAM_BACKGROUND"):
            with self.subTest(profile=profile):
                errors = validator.validate_data(generic_strategy(profile, 2))
                self.assertIn("task_profile is unsupported", errors)

    def test_four_visual_modes(self):
        cases = [
            ("FREE_FISSION_MODE", "", []),
            ("STYLE_GUIDED_MODE", "quiet luxury", []),
            (
                "STYLE_FUSION_MODE",
                "",
                [{"image_id": "REF-1", "path": "ref.jpg", "primary_role": "STYLE_BENCHMARK", "controls_routing": True, "allowed_transfer": ["light"], "prohibited_transfer": ["product facts"]}],
            ),
            (
                "REDESIGN_MODE",
                "",
                [{"image_id": "RED-1", "path": "old.jpg", "primary_role": "REDESIGN_SOURCE", "controls_routing": True, "allowed_transfer": ["intent"], "prohibited_transfer": ["defects"]}],
            ),
        ]
        for mode, style_direction, images in cases:
            with self.subTest(mode=mode):
                data = generic_strategy()
                data["visual_mode"] = mode
                data["style_direction"] = style_direction
                data["input_classification"] = images
                self.assertEqual(validator.validate_data(data), [])

    def test_sparse_research_requires_limitation(self):
        data = detail_strategy()
        data["competitor_research"] = research(sample_count=1, source_count=1)
        errors = validator.validate_data(data)
        self.assertTrue(any("limitation" in error for error in errors))

    def test_competitor_source_rejected(self):
        data = detail_strategy()
        data["approval_snapshot"]["approved_selling_points"][0]["本品事实来源"][0]["source_type"] = "竞品页面"
        errors = validator.validate_data(data)
        self.assertTrue(any("current-product evidence" in error for error in errors))

    def test_incomplete_strategy_fields_rejected(self):
        data = detail_strategy()
        del data["options"][0]["色彩策略"]
        errors = validator.validate_data(data)
        self.assertTrue(any("色彩策略 is required" in error for error in errors))

    def test_all_options_require_ecommerce_conversion_copy_mode(self):
        data = detail_strategy()
        data["options"][0]["文案模式"] = "品牌散文型"
        errors = validator.validate_data(data)
        self.assertTrue(any("文案模式 must be 电商转化型" in error for error in errors))

    def test_literary_or_curatorial_copy_is_rejected(self):
        data = detail_strategy()
        data["options"][0]["文案成稿"]["屏幕文案"]["第1屏"]["主标题"] = "深木入境"
        errors = validator.validate_data(data)
        self.assertTrue(any("literary or curatorial language" in error for error in errors))

    def test_evidence_reporting_copy_is_rejected(self):
        data = detail_strategy()
        data["options"][0]["文案成稿"]["屏幕文案"]["第2屏"]["说明文案"] = "六张卡片依次呈现已确认的产品事实，让购买判断更清楚。"
        errors = validator.validate_data(data)
        self.assertTrue(any("evidence-reporting language" in error for error in errors))

    def test_mechanical_document_navigation_cta_is_rejected(self):
        data = detail_strategy()
        data["options"][0]["文案成稿"]["屏幕文案"]["第3屏"]["CTA或承接语"] = "继续看材质与细节"
        errors = validator.validate_data(data)
        self.assertTrue(any("uses mechanical document navigation" in error for error in errors))

    def test_selling_point_line_requires_direct_consumer_outcome(self):
        data = detail_strategy()
        data["options"][0]["文案成稿"]["屏幕文案"]["第3屏"]["卖点短句"] = "乌金原木材质说明"
        errors = validator.validate_data(data)
        self.assertTrue(any("must state a direct consumer outcome" in error for error in errors))

    def test_explanation_copy_density_is_limited(self):
        data = detail_strategy()
        data["options"][0]["文案成稿"]["屏幕文案"]["第3屏"]["说明文案"] = "五层抽屉独立分区，不同物品可以按照类别分别收纳，让日常整理取放和购买判断都变得更加清楚明白。"
        errors = validator.validate_data(data)
        self.assertTrue(any("exceeds the 42-visible-character" in error for error in errors))

    def test_internal_or_placeholder_explanation_copy_is_rejected(self):
        data = detail_strategy()
        data["options"][0]["文案成稿"]["屏幕文案"]["第3屏"]["说明文案"] = "后期排版时此处展示材质镜头"
        errors = validator.validate_data(data)
        self.assertTrue(any("说明文案 contains internal production language" in error for error in errors))
        data["options"][0]["文案成稿"]["屏幕文案"]["第3屏"]["说明文案"] = "待补充"
        errors = validator.validate_data(data)
        self.assertTrue(any("说明文案 cannot be a placeholder" in error for error in errors))

    def test_title_and_subtitle_must_not_exceed_ten_visible_characters(self):
        data = detail_strategy()
        data["options"][0]["文案成稿"]["屏幕文案"]["第3屏"]["主标题"] = "一二三四五六七八九十甲"
        errors = validator.validate_data(data)
        self.assertTrue(any("主标题 exceeds the 10-visible-character" in error for error in errors))

        data = generic_strategy()
        data["options"][0]["文案成稿"]["内容单元"][0]["副标题"] = "一 二 三 四 五 六 七 八 九 十 甲"
        errors = validator.validate_data(data)
        self.assertTrue(any("副标题 exceeds the 10-visible-character" in error for error in errors))

    def test_all_consumer_visible_copy_rejects_internal_language_and_placeholders(self):
        data = detail_strategy()
        screen = data["options"][0]["文案成稿"]["屏幕文案"]["第3屏"]
        screen["卖点短句"] = "后期排版展示材质"
        screen["CTA或承接语"] = "待完善"
        errors = validator.validate_data(data)
        self.assertTrue(any("卖点短句 contains internal production language" in error for error in errors))
        self.assertTrue(any("CTA或承接语 cannot be a placeholder" in error for error in errors))

    def test_consumer_copy_rejects_evidence_provenance_narration(self):
        bad_copy = (
            "产品资料明确写明采用乌金原木。",
            "产品资料标注柜体宽度为1600毫米。",
            "资料显示表面采用水性漆涂装。",
            "参数文件注明柜体拥有九个抽屉。",
            "根据产品图可见柜体采用内嵌拉手。",
            "原图中可以看到圆润包边设计。",
        )
        for copy_text in bad_copy:
            with self.subTest(copy_text=copy_text):
                data = detail_strategy()
                data["options"][0]["文案成稿"]["屏幕文案"]["第3屏"]["说明文案"] = copy_text
                errors = validator.validate_data(data)
                self.assertTrue(any("evidence-provenance narration" in error for error in errors))

    def test_direct_consumer_product_statement_is_allowed(self):
        data = detail_strategy()
        data["options"][0]["文案成稿"]["屏幕文案"]["第3屏"]["说明文案"] = "精选乌金原木，木纹自然舒展，为空间增添沉稳质感。"
        self.assertEqual(validator.validate_data(data), [])

    def test_screen2_card_copy_is_consumer_visible_ecommerce_copy(self):
        data = detail_strategy()
        point = data["options"][0]["文案成稿"]["屏幕文案"]["第2屏"]["卖点总览"][0]
        point["卖点三行文案"]["简短利益"] = "后期排版展示利益"
        data["approval_snapshot"]["approved_selling_points"][0]["可转化利益"] = "后期排版展示利益"
        errors = validator.validate_data(data)
        self.assertTrue(any("卖点三行文案.简短利益 contains internal production language" in error for error in errors))

    def test_explanation_copy_must_expand_instead_of_repeat(self):
        data = detail_strategy()
        screen = data["options"][0]["文案成稿"]["屏幕文案"]["第3屏"]
        screen["说明文案"] = screen["卖点短句"]
        errors = validator.validate_data(data)
        self.assertTrue(any("must expand the selling point" in error for error in errors))

    def test_contextual_prompt_requires_real_usage_scene_mode(self):
        data = detail_strategy()
        task = next(item for item in data["options"][0]["图片任务"] if item["资产ID"] == "SCREEN-01")
        task["独立生图提示"] = "将产品放入现代居住空间，保持完整比例。"
        errors = validator.validate_data(data)
        self.assertTrue(any("use 真实使用场景 or remove the scene claim" in error for error in errors))

    def test_real_usage_scene_requires_anchors_scale_and_supporting_elements(self):
        data = detail_strategy()
        task = next(item for item in data["options"][0]["图片任务"] if item["资产ID"] == "SCREEN-01")
        task["场景设计"] = {
            "场景模式": "真实使用场景",
            "模式理由": "展示产品参与日常使用",
            "目标空间": "卧室靠墙收纳区",
            "摆放与使用关系": "产品靠墙落地并保留使用距离",
            "空间锚点": [],
            "尺度参照": [],
            "辅助元素": [],
            "协调逻辑": "低饱和环境衬托产品",
            "场景事实边界": "只作场景探索，不扩展为本品功能承诺",
        }
        task["独立生图提示"] = "卧室靠墙收纳区中的完整产品。"
        errors = validator.validate_data(data)
        self.assertTrue(any("空间锚点 must not be empty for 真实使用场景" in error for error in errors))
        self.assertTrue(any("尺度参照 must not be empty for 真实使用场景" in error for error in errors))
        self.assertTrue(any("辅助元素 must not be empty for 真实使用场景" in error for error in errors))

    def test_complete_real_usage_scene_is_valid(self):
        data = detail_strategy()
        task = next(item for item in data["options"][0]["图片任务"] if item["资产ID"] == "SCREEN-01")
        task["场景设计"] = {
            "场景模式": "真实使用场景",
            "模式理由": "展示产品参与日常使用",
            "目标空间": "卧室靠墙收纳区",
            "摆放与使用关系": "产品靠墙落地，与衣柜形成连续收纳关系，并保留开启距离",
            "空间锚点": ["清晰墙地交界", "相邻衣柜边缘"],
            "尺度参照": ["衣柜门板"],
            "辅助元素": ["少量折叠织物"],
            "协调逻辑": "低饱和墙面和柔和织物衬托产品，不使用竞争性木饰面",
            "场景事实边界": "同类场景只用于视觉探索，不扩展为本品功能承诺",
        }
        task["独立生图提示"] = "卧室靠墙收纳区，清晰墙地交界，产品靠墙落地并与相邻衣柜形成连续收纳关系。"
        self.assertEqual(validator.validate_data(data), [])

    def test_empty_s4_asset_rejected(self):
        data = detail_strategy()
        data["workflow_stage"] = "S4_IMAGE_PRODUCTION"
        data["approval_snapshot"] = approval(6, strategy=True)
        data["approved_strategy_id"] = "A"
        data["assets"] = [{}]
        del data["options"]
        del data["competitor_research"]
        errors = validator.validate_data(data)
        self.assertTrue(any("S4 assets must match" in error for error in errors))
        self.assertTrue(any("资产ID is required" in error for error in errors))

    def test_s4_rejects_generic_non_itemized_fidelity_check(self):
        strategy = detail_strategy()
        assets = []
        for task in strategy["options"][0]["图片任务"]:
            asset = copy.deepcopy(task)
            asset.update(
                {
                    "输出路径": "",
                    "生成状态": "PENDING",
                    "纯图检查": {"status": "PENDING", "notes": "pending"},
                    "产品保真检查": {"status": "PENDING", "notes": "pending"},
                    "场景适配检查": {"status": "PENDING", "notes": "pending"},
                }
            )
            assets.append(asset)
        data = {key: value for key, value in strategy.items() if key not in {"options", "competitor_research", "product_identity"}}
        data["workflow_stage"] = "S4_IMAGE_PRODUCTION"
        data["approval_snapshot"] = approval(6, strategy=True)
        data["approved_strategy_id"] = "A"
        data["assets"] = assets
        data["audit_result"] = audit("PENDING")
        errors = validator.validate_data(data)
        self.assertTrue(any("产品保真检查.检查项 is required" in error for error in errors))

    def test_generated_s4_requires_existing_files(self):
        strategy = detail_strategy()
        with tempfile.TemporaryDirectory() as folder:
            manifest_path = Path(folder) / "image-manifest.json"
            assets = []
            for task in strategy["options"][0]["图片任务"]:
                asset = copy.deepcopy(task)
                asset.update(
                    {
                        "输出路径": f"assets/{asset['资产ID']}.png",
                        "生成状态": "GENERATED",
                        "纯图检查": {"status": "PASS", "notes": "checked"},
                        "产品保真检查": fidelity_check(),
                        "场景适配检查": {"status": "PASS", "notes": "checked"},
                    }
                )
                assets.append(asset)
            data = {key: value for key, value in strategy.items() if key not in {"options", "competitor_research", "product_identity"}}
            data["workflow_stage"] = "S4_IMAGE_PRODUCTION"
            data["approval_snapshot"] = approval(6, strategy=True)
            data["approved_strategy_id"] = "A"
            data["assets"] = assets
            errors = validator.validate_data(data, manifest_path)
            self.assertTrue(any("does not exist" in error for error in errors))

    def test_valid_completed_s4(self):
        strategy = detail_strategy()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            manifest_path = root / "image-manifest.json"
            assets = []
            for task in strategy["options"][0]["图片任务"]:
                output = asset_dir / f"{task['资产ID']}.png"
                output.write_bytes(b"test-image-placeholder")
                asset = copy.deepcopy(task)
                asset.update(
                    {
                        "输出路径": str(output.relative_to(root)),
                        "生成状态": "GENERATED",
                        "纯图检查": {"status": "PASS", "notes": "checked"},
                        "产品保真检查": fidelity_check(),
                        "场景适配检查": {"status": "PASS", "notes": "checked"},
                    }
                )
                assets.append(asset)
            data = {key: value for key, value in strategy.items() if key not in {"options", "competitor_research", "product_identity"}}
            data["workflow_stage"] = "S4_IMAGE_PRODUCTION"
            data["approval_snapshot"] = approval(6, strategy=True)
            data["approved_strategy_id"] = "A"
            data["assets"] = assets
            self.assertEqual(validator.validate_data(data, manifest_path), [])

    def test_generated_s4_requires_scene_fit_pass(self):
        strategy = detail_strategy()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            manifest_path = root / "image-manifest.json"
            assets = []
            for task in strategy["options"][0]["图片任务"]:
                output = asset_dir / f"{task['资产ID']}.png"
                output.write_bytes(b"test-image-placeholder")
                asset = copy.deepcopy(task)
                asset.update(
                    {
                        "输出路径": str(output.relative_to(root)),
                        "生成状态": "GENERATED",
                        "纯图检查": {"status": "PASS", "notes": "checked"},
                        "产品保真检查": fidelity_check(),
                        "场景适配检查": {"status": "FAIL", "notes": "product appears pasted into an unrelated set"},
                    }
                )
                assets.append(asset)
            data = {key: value for key, value in strategy.items() if key not in {"options", "competitor_research", "product_identity"}}
            data["workflow_stage"] = "S4_IMAGE_PRODUCTION"
            data["approval_snapshot"] = approval(6, strategy=True)
            data["approved_strategy_id"] = "A"
            data["assets"] = assets
            errors = validator.validate_data(data, manifest_path)
            self.assertTrue(any("场景适配检查.status must be PASS" in error for error in errors))


class HumanReviewTests(unittest.TestCase):
    def test_detail_overview_is_complete_for_choice_without_execution_noise(self):
        rendered = renderer.render_review(detail_strategy())
        for required in (
            "# 电商视觉方案总览",
            "## A/B/C方案快速对比",
            "## 方案 A",
            "## 方案 B",
            "## 方案 C",
            "#### 第12屏",
            "#### 第2屏卖点卡片",
            "S2-SP-01",
            "[方案A审核书](strategy-A.md)",
            "[方案B审核书](strategy-B.md)",
            "[方案C审核书](strategy-C.md)",
            "画面类型",
            "画面方向",
            "对应资产",
            "说明文案（",
            "## 审核状态",
            "等待你选择 A / B / C",
        ):
            self.assertIn(required, rendered)
        self.assertIn("主标题（4/10）", rendered)
        self.assertIn("副标题（5/10）", rendered)
        self.assertIn("卖点短句（8/22）", rendered)
        self.assertIn("CTA或承接语（5/14）", rendered)
        self.assertNotIn("## 产品视觉身份锁", rendered)
        self.assertNotIn("完整生图提示", rendered)
        self.assertNotIn("### R1–R12", rendered)

    def test_option_book_contains_full_execution_and_audit_detail(self):
        data = detail_strategy()
        rendered = renderer.render_option_book(data, data["options"][0])
        for required in (
            "# 方案A选定执行书",
            "## 产品视觉身份锁",
            "不可变特征",
            "生成方式",
            "锁定特征ID",
            "场景模式",
            "目标空间",
            "摆放与使用关系",
            "完整生图提示",
            "## 审核与红线检查",
            "### R1–R12",
        ):
            self.assertIn(required, rendered)

    def test_non_detail_review_contains_every_content_unit(self):
        rendered = renderer.render_review(generic_strategy("MAIN_IMAGE", 5))
        self.assertIn("#### UNIT-05", rendered)
        self.assertIn("A-ASSET-05", rendered)
        self.assertNotIn("#### 第12屏", rendered)

    def test_cli_writes_overview_and_three_option_books_beside_valid_json(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            strategy_path = root / "strategy-package.json"
            strategy_path.write_text(__import__("json").dumps(detail_strategy(), ensure_ascii=False), encoding="utf-8")
            original_argv = __import__("sys").argv
            try:
                __import__("sys").argv = ["render_strategy_review.py", str(strategy_path)]
                self.assertEqual(renderer.main(), 0)
            finally:
                __import__("sys").argv = original_argv
            review_path = root / "strategy-review.md"
            self.assertTrue(review_path.is_file())
            self.assertIn("机器源文件：`strategy-package.json`", review_path.read_text(encoding="utf-8"))
            self.assertIn("# 电商视觉方案总览", review_path.read_text(encoding="utf-8"))
            for option_id in ("A", "B", "C"):
                detail_path = root / f"strategy-{option_id}.md"
                self.assertTrue(detail_path.is_file())
                self.assertIn(f"# 方案{option_id}选定执行书", detail_path.read_text(encoding="utf-8"))
            self.assertTrue((root / "strategy-handoff.md").is_file())
            self.assertTrue((root / "review-package-manifest.json").is_file())


class MigrationTests(unittest.TestCase):
    @staticmethod
    def fingerprints(product="FP"):
        return {
            "product_fact": "a" * 64,
            "product_image": "b" * 64,
            "style_reference": "c" * 64,
            "task_config": "d" * 64,
            "research": "e" * 64,
            "product": product,
        }

    def test_v1_approval_without_full_snapshot_is_cleared(self):
        old = {
            "product_key": "brand/model",
            "source_fingerprint": "FP",
            "flags": {"COMPETITOR_RESEARCH_COMPLETE": True, "SELLING_POINTS_APPROVED": True, "STRATEGY_APPROVED": True},
            "approved_selling_point_ids": ["CSP-001"],
            "approval_evidence": "confirmed",
            "approved_strategy_id": "A",
        }
        migrated, _ = migrator.migrate(old, self.fingerprints())
        self.assertEqual(migrated["schema_version"], 3)
        self.assertFalse(migrated["flags"]["SELLING_POINTS_APPROVED"])
        self.assertEqual(migrated["current_stage"], "S1_RESEARCH")
        self.assertEqual(migrated["product_identity_lock_status"], "BLOCKED")

    def test_removed_v1_profile_falls_back_to_detail_page(self):
        old = {
            "product_key": "brand/model",
            "source_fingerprint": "FP",
            "task_profile": "SOCIAL_SEEDING",
            "flags": {},
            "task_config": {},
        }
        migrated, _ = migrator.migrate(old, self.fingerprints())
        self.assertEqual(migrated["task_profile"], "DETAIL_PAGE")
        self.assertEqual(migrated["task_config"]["screen_count"], 12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
