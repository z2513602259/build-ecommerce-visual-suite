#!/usr/bin/env python3
"""Validate schema-v2 legacy and schema-v3 ecommerce visual-suite artifacts."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


TASK_PROFILES = {
    "DETAIL_PAGE",
    "MAIN_IMAGE",
    "PROMO_POSTER",
}
VISUAL_MODES = {
    "REDESIGN_MODE",
    "STYLE_FUSION_MODE",
    "STYLE_GUIDED_MODE",
    "FREE_FISSION_MODE",
}
IMAGE_ROLES = {"PRODUCT_SOURCE", "STYLE_BENCHMARK", "LAYOUT_WIREFRAME", "REDESIGN_SOURCE"}
STAGES = {
    "S1_COMPETITOR_RESEARCH_BLOCKED",
    "S2_PRODUCT_SELLING_POINT_REVIEW",
    "S3_STRATEGY_AND_FULL_DELIVERY",
    "S3_STRATEGY_REVIEW",
    "S3_SELECTED_STRATEGY_EXECUTION",
    "S4_IMAGE_PRODUCTION",
}
SKILL_VERSION = "3.0.0"
WORKFLOW_CONTRACT_VERSION = 3
FINGERPRINT_KEYS = ("product_fact", "product_image", "style_reference", "task_config", "research", "product")
SCREEN_FIELDS = ["页面职责", "主标题", "副标题", "卖点短句", "说明文案", "CTA或承接语", "对应的真实产品依据"]
CUSTOMER_VISIBLE_COPY_FIELDS = ("主标题", "副标题", "卖点短句", "说明文案", "CTA或承接语")
TITLE_VISIBLE_CHAR_LIMITS = {"主标题": 10, "副标题": 10}
GENERIC_TITLE_VALUES = {"材质", "尺寸", "细节", "设计", "工艺", "结构", "参数", "卖点", "场景", "品牌"}
GENERIC_BENEFIT_ONLY_VALUES = {"更清楚", "更明白", "更直接", "更易搭配", "方便核对", "更有质感", "更加高级", "观感更好", "层次更丰富"}
PURCHASE_NARRATIVE_FIELDS = ["核心购买主张", "首屏承诺", "主要购买顾虑", "决策递进", "文案气质"]
COPY_QUALITY_FIELDS = ["状态", "本方案核心购买理由", "泛化表达", "重复风险", "修正记录", "单元检查"]
COPY_QUALITY_UNIT_FIELDS = ["单元ID", "消费者决策问题", "事实锚点", "产品专属性", "购买理由明确", "泛化表达", "重复风险", "修正记录"]
OPTION_FIELDS = [
    "方案ID",
    "方案定位",
    "目标平台",
    "任务类型",
    "期望图片数量",
    "文案模式",
    "文案语调指引",
    "风格名称",
    "视觉世界观",
    "色彩策略",
    "光影策略",
    "核心材质库",
    "版式语言",
    "产品信息",
    "产品参数",
    "设计风格标签",
    "文案成稿",
    "图片任务",
    "纯图生成约束",
    "下游执行注意事项",
]
STRATEGY_REVIEW_OPTION_FIELDS = [
    "方案ID",
    "方案定位",
    "目标平台",
    "任务类型",
    "期望图片数量",
    "文案模式",
    "文案语调指引",
    "转化重点",
    "风格名称",
    "视觉世界观",
    "色彩策略",
    "光影策略",
    "核心材质库",
    "版式语言",
    "设计风格标签",
    "文案成稿",
    "图片简报",
    "纯图生成约束",
    "下游执行注意事项",
]
IMAGE_BRIEF_FIELDS = [
    "资产ID",
    "关联单元",
    "生成比例",
    "最终裁切比例",
    "场景模式",
    "证明目标",
    "镜头重点",
    "产品展示角度",
    "目标空间",
]
IMAGE_TASK_FIELDS = [
    "资产ID",
    "关联单元",
    "生成比例",
    "最终裁切比例",
    "平台安全区",
    "镜头重点",
    "产品展示角度",
    "所用原图参考",
    "保真执行",
    "场景设计",
    "独立生图提示",
    "禁止项",
    "对应的真实产品依据",
]
IDENTITY_LOCK_STATUSES = {"READY", "LIMITED", "BLOCKED"}
REFERENCE_ROLES = {"主参考", "辅助参考"}
FEATURE_IMPORTANCE = {"CRITICAL", "HIGH", "NORMAL"}
GENERATION_METHODS = {
    "真实产品抠图合成",
    "锁定产品区域仅重绘环境",
    "多图参考生成",
    "单图参考生成",
}
IDENTITY_LOCK_FIELDS = [
    "锁定ID",
    "锁定状态",
    "主参考图ID",
    "角度参考",
    "不可变特征",
    "允许变化",
    "条件变化",
    "禁止推断",
    "未确认项",
]
FIDELITY_EXECUTION_FIELDS = [
    "生成方式",
    "主参考图ID",
    "辅助参考图ID",
    "锁定特征ID",
    "允许变化",
    "禁止变化",
    "角度匹配说明",
    "结构推断风险",
]
FIDELITY_CHECK_ITEMS = [
    "结构一致性",
    "比例一致性",
    "部件数量",
    "拉手与五金",
    "边角与支撑结构",
    "材质与颜色",
    "纹理与图案方向",
    "品牌标识与固定图文",
    "参考角度匹配",
]
SCENE_MODES = {"真实使用场景", "产品肖像", "细节证据"}
SCENE_DESIGN_FIELDS = [
    "场景模式",
    "模式理由",
    "目标空间",
    "摆放与使用关系",
    "空间锚点",
    "尺度参照",
    "辅助元素",
    "协调逻辑",
    "场景事实边界",
]
CONTEXTUAL_SCENE_MARKERS = (
    "真实使用场景",
    "真实生活场景",
    "生活场景",
    "居住空间",
    "家居空间",
    "卧室",
    "客厅",
    "玄关",
    "餐厅",
    "厨房",
    "浴室",
    "书房",
    "办公室",
    "工作间",
    "户外场景",
)
PROHIBITION_GROUPS = {
    "added text or gibberish": ("文字", "乱码", "text", "gibberish"),
    "titles and subtitles": ("标题", "副标题", "title", "subtitle"),
    "labels prices and CTA": ("标签", "价格", "cta", "label", "price"),
    "icons and dimensions": ("图标", "尺寸线", "dimension", "icon"),
    "collage grid or cards": ("拼贴", "网格", "卡片", "分屏", "collage", "grid", "card"),
    "intentional text space": ("文字留白", "刻意留白", "预留", "blank space"),
    "invented product structure": ("虚构", "改变产品结构", "新增部件", "invented", "altered structure"),
}
ALLOWED_PRODUCT_SOURCE_TYPES = {"当前产品文件", "当前产品图片", "证书", "用户明确陈述"}
DEFAULT_SIX_POSITIONS = [
    "左侧纵向主卡",
    "右上横卡",
    "右中横卡",
    "全宽横卡",
    "左下半宽卡",
    "右下半宽卡",
]
COPY_PLACEHOLDER_VALUES = {
    "explanation",
    "placeholder",
    "todo",
    "tbd",
    "待补充",
    "待完善",
    "待定",
    "暂无",
    "未明确",
    "说明文案",
    "这里写文案",
    "文案待定",
}
INTERNAL_COPY_MARKERS = (
    "镜头重点",
    "产品展示角度",
    "后期排版",
    "此处展示",
    "用于说明",
    "页面职责",
    "设计备注",
    "生图提示",
    "数据源",
    "source_id",
    "asset_id",
    "占位",
)
EVIDENCE_PROVENANCE_PATTERNS = (
    r"(?:产品|本品|官方|现有)?资料(?:中)?(?:明确)?(?:写明|标注|显示|注明|记载|说明)",
    r"(?:产品)?参数(?:表|文件)?(?:中)?(?:明确)?(?:写明|标注|显示|注明|记载|说明)",
    r"(?:根据|依据|据)(?:产品|本品|官方|现有)?(?:资料|参数|参数表|参数文件|产品图|原图|图片)",
    r"(?:产品图|原图|参考图|图片)(?:中)?(?:清晰)?(?:可见|显示|展示|可以看到|能够看到)",
    r"(?:文件|文档)(?:中)?(?:明确)?(?:写明|标注|显示|注明|记载|说明)",
)
LITERARY_COPY_MARKERS = (
    "入境",
    "自有深度",
    "空间底色",
    "纹理节奏",
    "边缘有光",
    "克制有光",
    "诗意栖居",
    "写下叙事",
    "叙事感",
    "静物馆",
    "馆藏",
)
REPORTING_COPY_MARKERS = (
    "已确认的产品事实",
    "已确认产品事实",
    "真实信息一次看清",
    "逐项呈现",
    "逐项确认",
    "本页已整理",
    "均已整理在本页",
    "集中确认",
    "名称清楚",
    "一起呈现",
    "共同呈现",
    "清楚可见",
)
MECHANICAL_CTA_PATTERNS = (
    r"^(?:继续看|继续查看|逐项查看)",
    r"^(?:回看|回到)",
    r"^(?:放大查看|放大边缘)",
    r"^完成产品确认$",
)
CHINESE_BENEFIT_MARKERS = (
    "更",
    "方便",
    "轻松",
    "省",
    "清楚",
    "整齐",
    "稳",
    "适合",
    "减少",
    "避免",
    "不易",
    "易于",
    "便于",
    "耐看",
    "利落",
    "舒适",
    "分区",
    "收纳",
    "取放",
    "摆放",
    "贴合",
    "保护",
    "分类",
    "归类",
    "节省",
    "提升",
    "降低",
    "自然",
    "沉稳",
    "简洁",
    "明白",
    "放心",
)
ENGLISH_BENEFIT_MARKERS = (
    "more",
    "easier",
    "less",
    "better",
    "helps",
    "keeps",
    "fits",
    "reduces",
    "saves",
    "clear",
    "comfortable",
    "convenient",
    "organized",
    "natural",
    "stable",
    "simple",
    "protects",
    "supports",
)


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def required_keys(self, obj: Any, keys: list[str], path: str) -> None:
        if not isinstance(obj, dict):
            self.errors.append(f"{path} must be an object")
            return
        for key in keys:
            if key not in obj:
                self.errors.append(f"{path}.{key} is required")


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def json_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def resolve_artifact_refs(data: dict[str, Any], artifact_path: Path | None) -> tuple[dict[str, Any], list[str]]:
    """Resolve v3 sibling artifact references into a validation copy."""
    resolved = copy.deepcopy(data)
    errors: list[str] = []
    refs = data.get("artifact_refs")
    if data.get("schema_version") != 3 or not isinstance(refs, dict):
        return resolved, errors
    if artifact_path is None:
        if not resolved.get("product_identity_lock") or not resolved.get("competitor_research"):
            errors.append("schema-v3 artifact references require the artifact file path for resolution")
        return resolved, errors
    root = artifact_path.resolve().parent

    def load_ref(name: str) -> dict[str, Any] | None:
        ref = refs.get(name)
        if not isinstance(ref, dict):
            errors.append(f"$.artifact_refs.{name} must be an object")
            return None
        relative = ref.get("path")
        expected = ref.get("sha256")
        if not nonempty_string(relative) or not re.fullmatch(r"[0-9a-f]{64}", str(expected or "")):
            errors.append(f"$.artifact_refs.{name} requires sibling-relative path and lowercase SHA-256")
            return None
        candidate = (root / str(relative)).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            errors.append(f"$.artifact_refs.{name}.path escapes the artifact directory")
            return None
        if not candidate.is_file():
            errors.append(f"$.artifact_refs.{name}.path does not exist: {relative}")
            return None
        if sha256_file(candidate) != expected:
            errors.append(f"$.artifact_refs.{name}.sha256 does not match {relative}")
            return None
        try:
            value = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            errors.append(f"$.artifact_refs.{name} is invalid JSON: {exc}")
            return None
        return value if isinstance(value, dict) else None

    needs_refs = data.get("workflow_stage") in {"S3_STRATEGY_REVIEW", "S3_SELECTED_STRATEGY_EXECUTION", "S4_IMAGE_PRODUCTION"}
    if "product_identity_lock" in refs or needs_refs:
        lock_doc = load_ref("product_identity_lock")
        if lock_doc:
            resolved["product_identity_lock"] = lock_doc.get("product_identity_lock", lock_doc)
    if "research" in refs or needs_refs:
        research_doc = load_ref("research")
        if research_doc:
            resolved["competitor_research"] = research_doc.get("competitor_research", research_doc)
    return resolved, errors


def visible_char_count(value: str) -> int:
    return sum(1 for char in value if not char.isspace())


def validate_consumer_visible_text(value: Any, path: str, v: Validation, visible_limit: int | None = None) -> None:
    v.require(nonempty_string(value), f"{path} must be complete consumer-facing ecommerce copy")
    if not isinstance(value, str):
        return
    normalized = value.strip().lower()
    v.require(normalized not in COPY_PLACEHOLDER_VALUES, f"{path} cannot be a placeholder")
    for marker in INTERNAL_COPY_MARKERS:
        v.require(marker.lower() not in normalized, f"{path} contains internal production language: {marker}")
    for pattern in EVIDENCE_PROVENANCE_PATTERNS:
        v.require(
            re.search(pattern, normalized, re.IGNORECASE) is None,
            f"{path} contains evidence-provenance narration reserved for 对应的真实产品依据",
        )
    for marker in LITERARY_COPY_MARKERS:
        v.require(marker.lower() not in normalized, f"{path} contains literary or curatorial language: {marker}")
    for marker in REPORTING_COPY_MARKERS:
        v.require(marker.lower() not in normalized, f"{path} contains evidence-reporting language: {marker}")
    v.require(
        re.search(r"(?:src|csp|sp|asset)-\d+|\.(?:txt|json|xlsx|pdf)(?::\d+)?", normalized, re.IGNORECASE) is None,
        f"{path} must not contain source IDs, asset IDs, or file locators",
    )
    if visible_limit is not None:
        v.require(
            visible_char_count(value) <= visible_limit,
            f"{path} exceeds the {visible_limit}-visible-character ecommerce copy limit",
        )


def has_consumer_outcome(value: str) -> bool:
    normalized = value.strip().lower()
    if re.search(r"[\u3400-\u9fff]", normalized):
        return any(marker in normalized for marker in CHINESE_BENEFIT_MARKERS)
    return any(re.search(rf"\b{re.escape(marker)}\b", normalized) for marker in ENGLISH_BENEFIT_MARKERS)


def validate_conversion_benefit_text(value: Any, path: str, v: Validation) -> None:
    validate_consumer_visible_text(value, path, v, visible_limit=22)
    if not isinstance(value, str):
        return
    length = visible_char_count(value)
    v.require(length >= 6, f"{path} must contain at least 6 visible characters as a direct consumer outcome")
    v.require(has_consumer_outcome(value), f"{path} must state a direct consumer outcome or purchase benefit")


def validate_customer_copy(unit: Any, path: str, v: Validation, require_unit_id: bool = False) -> None:
    keys = (["单元ID"] if require_unit_id else []) + SCREEN_FIELDS
    v.required_keys(unit, keys, path)
    if not isinstance(unit, dict):
        return
    for key in SCREEN_FIELDS[:-1]:
        v.require(nonempty_string(unit.get(key)), f"{path}.{key} must be complete customer-facing copy")
    for key in CUSTOMER_VISIBLE_COPY_FIELDS:
        if key == "卖点短句":
            validate_conversion_benefit_text(unit.get(key), f"{path}.{key}", v)
        else:
            limit = TITLE_VISIBLE_CHAR_LIMITS.get(key)
            if key == "CTA或承接语":
                limit = 14
            validate_consumer_visible_text(unit.get(key), f"{path}.{key}", v, limit)
    responsibility = unit.get("页面职责")
    title = unit.get("主标题")
    if nonempty_string(responsibility) and nonempty_string(title):
        v.require(title.strip() != responsibility.strip(), f"{path}.主标题 must be a purchase conclusion, not a copy of 页面职责")
    if isinstance(title, str):
        v.require(title.strip() not in GENERIC_TITLE_VALUES, f"{path}.主标题 must be a purchase conclusion, not a generic page label")
    for field in ("卖点短句", "说明文案"):
        value = unit.get(field)
        if isinstance(value, str):
            v.require(value.strip() not in GENERIC_BENEFIT_ONLY_VALUES, f"{path}.{field} cannot use a generic benefit as the complete copy")
    explanation = unit.get("说明文案")
    if isinstance(explanation, str):
        normalized = explanation.strip().lower()
        length = visible_char_count(explanation)
        v.require(length >= 16, f"{path}.说明文案 must contain at least 16 visible characters")
        v.require(length <= 42, f"{path}.说明文案 exceeds the 42-visible-character ecommerce density limit")
        sentence_count = len(re.findall(r"[。！？!?]+", explanation))
        v.require(sentence_count <= 2, f"{path}.说明文案 must contain no more than two sentences")
        v.require(has_consumer_outcome(explanation), f"{path}.说明文案 must connect a product fact to a consumer outcome")
        for repeated_field in ("主标题", "卖点短句"):
            repeated = unit.get(repeated_field)
            if nonempty_string(repeated):
                v.require(normalized != repeated.strip().lower(), f"{path}.说明文案 must expand the selling point instead of repeating {repeated_field}")
    cta = unit.get("CTA或承接语")
    if isinstance(cta, str):
        normalized_cta = cta.strip()
        for pattern in MECHANICAL_CTA_PATTERNS:
            v.require(re.search(pattern, normalized_cta) is None, f"{path}.CTA或承接语 uses mechanical document navigation")
    validate_sources(unit.get("对应的真实产品依据"), f"{path}.对应的真实产品依据", v)


def validate_sources(value: Any, path: str, v: Validation) -> None:
    v.require(nonempty_list(value), f"{path} must be a nonempty list of current-product sources")
    if not isinstance(value, list):
        return
    for index, source in enumerate(value):
        source_path = f"{path}[{index}]"
        v.required_keys(source, ["source_id", "source_type", "location", "claim"], source_path)
        if not isinstance(source, dict):
            continue
        for key in ("source_id", "source_type", "location", "claim"):
            v.require(nonempty_string(source.get(key)), f"{source_path}.{key} must not be empty")
        v.require(
            source.get("source_type") in ALLOWED_PRODUCT_SOURCE_TYPES,
            f"{source_path}.source_type must be current-product evidence, not competitor or reference evidence",
        )


def validate_approval_snapshot(value: Any, path: str, v: Validation) -> dict[str, Any]:
    required = [
        "selling_points_approved",
        "selling_point_approval_evidence",
        "approved_selling_points",
        "strategy_approved",
        "approved_strategy_id",
        "strategy_approval_evidence",
    ]
    v.required_keys(value, required, path)
    if not isinstance(value, dict):
        return {}
    for flag in ("selling_points_approved", "strategy_approved"):
        v.require(isinstance(value.get(flag), bool), f"{path}.{flag} must be boolean")
    return value


def validate_input_classification(value: Any, v: Validation) -> None:
    v.require(isinstance(value, list), "$.input_classification must be a list")
    if not isinstance(value, list):
        return
    ids: list[str] = []
    for index, image in enumerate(value):
        path = f"$.input_classification[{index}]"
        v.required_keys(image, ["image_id", "path", "primary_role", "controls_routing", "allowed_transfer", "prohibited_transfer"], path)
        if not isinstance(image, dict):
            continue
        ids.append(str(image.get("image_id", "")))
        v.require(image.get("primary_role") in IMAGE_ROLES, f"{path}.primary_role is unsupported")
        v.require(isinstance(image.get("controls_routing"), bool), f"{path}.controls_routing must be boolean")
        v.require(isinstance(image.get("allowed_transfer"), list), f"{path}.allowed_transfer must be a list")
        v.require(isinstance(image.get("prohibited_transfer"), list), f"{path}.prohibited_transfer must be a list")
    v.require(len(ids) == len(set(ids)), "input image IDs must be unique")


def validate_task_config(data: dict[str, Any], v: Validation) -> dict[str, Any]:
    config = data.get("task_config")
    keys = [
        "target_platform",
        "image_count",
        "screen_count",
        "screen_count_override",
        "screen2_card_count",
        "screen2_card_count_override",
        "output_ratios",
        "platform_safe_area",
    ]
    v.required_keys(config, keys, "$.task_config")
    if not isinstance(config, dict):
        return {}
    for key in ("image_count", "screen_count", "screen2_card_count"):
        v.require(isinstance(config.get(key), int) and config.get(key) >= 0, f"$.task_config.{key} must be a nonnegative integer")
    for key in ("screen_count_override", "screen2_card_count_override"):
        v.require(isinstance(config.get(key), bool), f"$.task_config.{key} must be boolean")
    v.require(nonempty_string(config.get("target_platform")), "$.task_config.target_platform must not be empty")
    v.require(isinstance(config.get("output_ratios"), list), "$.task_config.output_ratios must be a list")
    v.require(nonempty_string(config.get("platform_safe_area")), "$.task_config.platform_safe_area must not be empty")

    profile = data.get("task_profile")
    if profile == "DETAIL_PAGE":
        screen_count = config.get("screen_count", 0)
        card_count = config.get("screen2_card_count", 0)
        v.require(screen_count >= 2, "detail-page screen_count must be at least 2")
        v.require(card_count >= 1, "detail-page screen2_card_count must be at least 1")
        expected_assets = screen_count - 1 + card_count
        v.require(config.get("image_count") == expected_assets, f"detail-page image_count must equal screen_count - 1 + screen2_card_count ({expected_assets})")
        layout = config.get("screen2_layout_spec")
        v.require(isinstance(layout, list) and len(layout) == card_count, "$.task_config.screen2_layout_spec must match screen2_card_count")
        if isinstance(layout, list):
            expected_ids = [f"SP-{i:02d}" for i in range(1, card_count + 1)]
            actual_ids = [item.get("卡片ID") for item in layout if isinstance(item, dict)]
            v.require(actual_ids == expected_ids, "screen2_layout_spec card IDs must be ordered SP-01 onward")
            for index, item in enumerate(layout):
                path = f"$.task_config.screen2_layout_spec[{index}]"
                v.required_keys(item, ["卡片ID", "卡位", "建议卡片比例"], path)
                if isinstance(item, dict):
                    v.require(nonempty_string(item.get("卡位")), f"{path}.卡位 must not be empty")
                    v.require(nonempty_string(item.get("建议卡片比例")), f"{path}.建议卡片比例 must not be empty")
            if card_count == 6 and not config.get("screen2_card_count_override"):
                positions = [item.get("卡位") for item in layout if isinstance(item, dict)]
                v.require(positions == DEFAULT_SIX_POSITIONS, "default six-card layout positions do not match the fixed hierarchy")
    else:
        v.require(config.get("screen_count") == 0, "non-detail task screen_count must be 0")
        v.require(config.get("screen2_card_count") == 0, "non-detail task screen2_card_count must be 0")
        v.require(config.get("image_count", 0) > 0, "non-detail task image_count must be positive")
    return config


def validate_common(data: dict[str, Any], v: Validation) -> tuple[dict[str, Any], dict[str, Any]]:
    v.required_keys(
        data,
        [
            "schema_version",
            "workflow_id",
            "product_fingerprint",
            "product_identity_lock",
            "workflow_stage",
            "task_profile",
            "visual_mode",
            "style_direction",
            "visual_mode_reason",
            "input_classification",
            "task_config",
            "approval_snapshot",
            "audit_result",
        ],
        "$",
    )
    schema_version = data.get("schema_version")
    v.require(schema_version in {2, 3}, "schema_version must be 2 or 3")
    if schema_version == 3:
        v.required_keys(data, ["skill_version", "workflow_contract_version", "fingerprints", "artifact_refs"], "$")
        v.require(data.get("skill_version") == SKILL_VERSION, f"skill_version must be {SKILL_VERSION}")
        v.require(data.get("workflow_contract_version") == WORKFLOW_CONTRACT_VERSION, "workflow_contract_version must be 3")
        fingerprints = data.get("fingerprints")
        v.require(isinstance(fingerprints, dict), "fingerprints must be an object")
        if isinstance(fingerprints, dict):
            for key in FINGERPRINT_KEYS:
                v.require(nonempty_string(fingerprints.get(key)), f"fingerprints.{key} must not be empty")
            v.require(data.get("product_fingerprint") == fingerprints.get("product"), "product_fingerprint must equal fingerprints.product")
    v.require(nonempty_string(data.get("workflow_id")), "workflow_id must not be empty")
    v.require(nonempty_string(data.get("product_fingerprint")), "product_fingerprint must not be empty")
    v.require(data.get("workflow_stage") in STAGES, "workflow_stage is unsupported")
    v.require(data.get("task_profile") in TASK_PROFILES, "task_profile is unsupported")
    v.require(data.get("visual_mode") in VISUAL_MODES, "visual_mode is unsupported")
    validate_product_identity_lock(
        data.get("product_identity_lock"),
        "$.product_identity_lock",
        v,
        require_ready=data.get("workflow_stage") in {"S3_STRATEGY_AND_FULL_DELIVERY", "S3_STRATEGY_REVIEW", "S3_SELECTED_STRATEGY_EXECUTION", "S4_IMAGE_PRODUCTION"},
    )
    v.require(isinstance(data.get("style_direction"), str), "style_direction must be a string")
    v.require(nonempty_string(data.get("visual_mode_reason")), "visual_mode_reason must not be empty")
    validate_input_classification(data.get("input_classification"), v)
    controlling_roles = [
        image.get("primary_role")
        for image in data.get("input_classification", [])
        if isinstance(image, dict) and image.get("controls_routing") is True
    ]
    if "REDESIGN_SOURCE" in controlling_roles:
        expected_mode = "REDESIGN_MODE"
    elif any(role in {"STYLE_BENCHMARK", "LAYOUT_WIREFRAME"} for role in controlling_roles):
        expected_mode = "STYLE_FUSION_MODE"
    elif nonempty_string(data.get("style_direction")):
        expected_mode = "STYLE_GUIDED_MODE"
    else:
        expected_mode = "FREE_FISSION_MODE"
    v.require(data.get("visual_mode") == expected_mode, f"visual_mode must be {expected_mode} for the controlling inputs")
    config = validate_task_config(data, v)
    approval = validate_approval_snapshot(data.get("approval_snapshot"), "$.approval_snapshot", v)
    audit = data.get("audit_result")
    v.required_keys(audit, ["status", "perspectives", "redline_checks", "correction_log"], "$.audit_result")
    return config, approval


def validate_sample(sample: Any, index: int, v: Validation, schema_version: int = 2) -> None:
    path = f"$.competitor_research.samples[{index}]"
    keys = [
        "样本ID",
        "来源平台或网站",
        "来源类型",
        "品牌或商品名",
        "链接",
        "访问日期",
        "与本品相似依据",
        "详情页板块顺序",
        "主要卖点与阐述方式",
        "证据表达方式",
        "可借鉴模式",
        "应避免模式",
        "来源可信度",
        "来源限制",
    ]
    v.required_keys(sample, keys, path)
    if not isinstance(sample, dict):
        return
    v.require(nonempty_string(sample.get("样本ID")), f"{path}.样本ID must not be empty")
    link = sample.get("链接")
    if schema_version == 3:
        v.required_keys(sample, ["访问状态", "证据采集时间"], path)
        v.require(isinstance(link, str) and re.match(r"^https?://", link, re.IGNORECASE) is not None, f"{path}.链接 must be a direct HTTP(S) URL")
        v.require(sample.get("访问状态") in {"ACCESSIBLE", "PARTIAL", "BLOCKED"}, f"{path}.访问状态 is unsupported")
        try:
            datetime.fromisoformat(str(sample.get("证据采集时间")))
        except ValueError:
            v.errors.append(f"{path}.证据采集时间 must be ISO-8601")
    v.require(isinstance(link, str) and link.startswith(("http://", "https://")), f"{path}.链接 must be an HTTP(S) URL")
    for key in ("详情页板块顺序", "主要卖点与阐述方式", "证据表达方式"):
        v.require(nonempty_list(sample.get(key)), f"{path}.{key} must be a nonempty list")


def validate_research(value: Any, v: Validation, schema_version: int = 2) -> None:
    path = "$.competitor_research"
    keys = [
        "research_status",
        "research_date",
        "platforms",
        "public_web_sources",
        "search_queries",
        "samples",
        "research_limitations",
        "高频消费者关注点",
        "共性板块",
        "同质化表达",
        "差异化机会",
        "平台差异",
    ]
    v.required_keys(value, keys, path)
    if not isinstance(value, dict):
        return
    v.require(value.get("research_status") == "COMPLETE", f"{path}.research_status must be COMPLETE")
    v.require(nonempty_list(value.get("search_queries")), f"{path}.search_queries must not be empty")
    samples = value.get("samples")
    v.require(nonempty_list(samples), f"{path}.samples must not be empty")
    if not isinstance(samples, list):
        return
    ids: list[str] = []
    sources: set[str] = set()
    for index, sample in enumerate(samples):
        validate_sample(sample, index, v, schema_version)
        if isinstance(sample, dict):
            ids.append(str(sample.get("样本ID", "")))
            source = sample.get("来源平台或网站")
            if nonempty_string(source):
                sources.add(source.strip().lower())
    v.require(len(ids) == len(set(ids)), "competitor sample IDs must be unique")
    limitations = value.get("research_limitations")
    v.required_keys(limitations, ["is_limited", "reason", "attempted_fallback_routes", "confidence"], f"{path}.research_limitations")
    limited = isinstance(limitations, dict) and limitations.get("is_limited") is True
    threshold_met = len(samples) >= 6 and len(sources) >= 2
    if not threshold_met:
        v.require(limited, "research below 6 samples or 2 sources requires an explicit limitation record")
        if isinstance(limitations, dict):
            v.require(nonempty_string(limitations.get("reason")), "research limitation reason must not be empty")
            v.require(nonempty_list(limitations.get("attempted_fallback_routes")), "limited research must record attempted fallback routes")
            v.require(limitations.get("confidence") in {"LOW", "MEDIUM"}, "limited research confidence must be LOW or MEDIUM")
    if schema_version == 3:
        policy = value.get("research_policy")
        v.required_keys(policy, ["max_age_days", "as_of_date"], f"{path}.research_policy")
        if isinstance(policy, dict):
            max_age = policy.get("max_age_days")
            v.require(isinstance(max_age, int) and 1 <= max_age <= 180, "research_policy.max_age_days must be 1-180")
            try:
                as_of = date.fromisoformat(str(policy.get("as_of_date")))
                research_day = date.fromisoformat(str(value.get("research_date")))
                if isinstance(max_age, int):
                    v.require((as_of - research_day).days <= max_age, "competitor research is older than research_policy.max_age_days")
                    v.require((as_of - research_day).days >= 0, "research_date cannot be after research_policy.as_of_date")
            except ValueError:
                v.errors.append("research_date and research_policy.as_of_date must be ISO dates")


def validate_candidates(value: Any, v: Validation, schema_version: int = 2) -> list[dict[str, Any]]:
    path = "$.selling_point_candidates"
    v.require(nonempty_list(value), f"{path} must not be empty")
    if not isinstance(value, list):
        return []
    keys = [
        "卖点ID",
        "类别",
        "具体产品事实",
        "可转化利益",
        "本品事实来源",
        "竞品调研依据",
        "证据类型",
        "证据强度",
        "市场判断",
        "推荐级别",
        "适合的视觉证明方式",
        "风险或待确认项",
    ]
    if schema_version >= 3:
        keys.extend(["消费者决策问题", "利益类型", "具体消费者结果", "表达边界"])
    ids: list[str] = []
    valid: list[dict[str, Any]] = []
    for index, candidate in enumerate(value):
        item_path = f"{path}[{index}]"
        v.required_keys(candidate, keys, item_path)
        if not isinstance(candidate, dict):
            continue
        valid.append(candidate)
        candidate_id = candidate.get("卖点ID")
        v.require(nonempty_string(candidate_id), f"{item_path}.卖点ID must not be empty")
        ids.append(str(candidate_id))
        validate_conversion_benefit_text(candidate.get("可转化利益"), f"{item_path}.可转化利益", v)
        if schema_version >= 3:
            v.require(nonempty_string(candidate.get("消费者决策问题")), f"{item_path}.消费者决策问题 must not be empty")
            v.require(nonempty_string(candidate.get("利益类型")), f"{item_path}.利益类型 must not be empty")
            validate_conversion_benefit_text(candidate.get("具体消费者结果"), f"{item_path}.具体消费者结果", v)
            boundary = candidate.get("表达边界")
            v.require(nonempty_string(boundary) or nonempty_list(boundary), f"{item_path}.表达边界 must not be empty")
        validate_sources(candidate.get("本品事实来源"), f"{item_path}.本品事实来源", v)
        v.require(isinstance(candidate.get("竞品调研依据"), list), f"{item_path}.竞品调研依据 must be a list")
    v.require(len(ids) == len(set(ids)), "selling-point candidate IDs must be unique")
    return valid


def validate_blocked(data: dict[str, Any], approval: dict[str, Any], v: Validation) -> None:
    v.require(data.get("research_status") == "INCOMPLETE", "research_status must be INCOMPLETE")
    v.required_keys(
        data,
        [
            "product_identity",
            "attempted_platforms",
            "attempted_queries",
            "public_fallback_sources_attempted",
            "accessible_evidence",
            "blocking_reasons",
            "required_user_input",
            "blocked_next_steps",
        ],
        "$",
    )
    v.require(not approval.get("selling_points_approved") and not approval.get("strategy_approved"), "blocked research cannot contain approvals")
    v.require(nonempty_list(data.get("attempted_queries")), "attempted_queries must not be empty")
    v.require(nonempty_list(data.get("public_fallback_sources_attempted")), "public fallback routes must be attempted")
    v.require(nonempty_list(data.get("blocking_reasons")), "blocking_reasons must not be empty")
    audit = data.get("audit_result", {})
    v.require(isinstance(audit, dict) and audit.get("status") == "BLOCKED", "blocked research audit status must be BLOCKED")


def validate_review(data: dict[str, Any], approval: dict[str, Any], v: Validation) -> None:
    v.required_keys(
        data,
        [
            "approval_status",
            "product_identity",
            "competitor_research",
            "selling_point_candidates",
            "recommended_core_set",
            "rejected_or_unverifiable_claims",
            "missing_information",
            "confirmation_request",
            "blocked_next_steps",
        ],
        "$",
    )
    v.require(data.get("approval_status") == "PENDING_USER_APPROVAL", "approval_status must be PENDING_USER_APPROVAL")
    v.require(not approval.get("selling_points_approved") and not approval.get("strategy_approved"), "S2 must remain pending user approval")
    validate_research(data.get("competitor_research"), v)
    candidates = validate_candidates(data.get("selling_point_candidates"), v, int(data.get("schema_version", 2)))
    candidate_ids = {item.get("卖点ID") for item in candidates}
    recommended = data.get("recommended_core_set")
    v.require(nonempty_list(recommended), "recommended_core_set must not be empty")
    if isinstance(recommended, list):
        v.require(all(item in candidate_ids for item in recommended), "recommended_core_set must contain candidate IDs only")
    v.require(nonempty_string(data.get("confirmation_request")), "confirmation_request must not be empty")


def validate_approved_points(value: Any, path: str, v: Validation) -> list[dict[str, Any]]:
    v.require(nonempty_list(value), f"{path} must not be empty")
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    ids: list[str] = []
    for index, point in enumerate(value):
        item_path = f"{path}[{index}]"
        point_keys = ["卖点ID", "类别", "具体产品事实", "可转化利益", "本品事实来源"]
        if "消费者决策问题" in point or "利益类型" in point or "具体消费者结果" in point or "表达边界" in point:
            point_keys.extend(["消费者决策问题", "利益类型", "具体消费者结果", "表达边界"])
        v.required_keys(point, point_keys, item_path)
        if not isinstance(point, dict):
            continue
        result.append(point)
        ids.append(str(point.get("卖点ID", "")))
        validate_conversion_benefit_text(point.get("可转化利益"), f"{item_path}.可转化利益", v)
        if len(point_keys) > 5:
            v.require(nonempty_string(point.get("消费者决策问题")), f"{item_path}.消费者决策问题 must not be empty")
            v.require(nonempty_string(point.get("利益类型")), f"{item_path}.利益类型 must not be empty")
            validate_conversion_benefit_text(point.get("具体消费者结果"), f"{item_path}.具体消费者结果", v)
            v.require(nonempty_string(point.get("表达边界")) or nonempty_list(point.get("表达边界")), f"{item_path}.表达边界 must not be empty")
        validate_sources(point.get("本品事实来源"), f"{item_path}.本品事实来源", v)
    v.require(len(ids) == len(set(ids)), f"{path} IDs must be unique")
    return result


def validate_prohibitions(value: Any, path: str, v: Validation) -> None:
    v.require(nonempty_list(value), f"{path} must be a nonempty list")
    if not isinstance(value, list):
        return
    normalized = " ".join(str(item).lower() for item in value)
    for label, terms in PROHIBITION_GROUPS.items():
        v.require(any(term.lower() in normalized for term in terms), f"{path} must prohibit {label}")


def validate_product_identity_lock(value: Any, path: str, v: Validation, require_ready: bool = False) -> None:
    v.required_keys(value, IDENTITY_LOCK_FIELDS, path)
    if not isinstance(value, dict):
        return
    status = value.get("锁定状态")
    v.require(nonempty_string(value.get("锁定ID")), f"{path}.锁定ID must not be empty")
    v.require(status in IDENTITY_LOCK_STATUSES, f"{path}.锁定状态 is unsupported")
    if require_ready:
        v.require(status == "READY", f"{path}.锁定状态 must be READY for S3/S4")
    for key in ("主参考图ID", "角度参考", "不可变特征", "允许变化", "条件变化", "禁止推断", "未确认项"):
        v.require(isinstance(value.get(key), list), f"{path}.{key} must be a list")

    features = value.get("不可变特征")
    feature_ids: list[str] = []
    if isinstance(features, list):
        for index, feature in enumerate(features):
            item_path = f"{path}.不可变特征[{index}]"
            v.required_keys(feature, ["特征ID", "类别", "特征描述", "重要级别", "本品事实来源"], item_path)
            if not isinstance(feature, dict):
                continue
            for key in ("特征ID", "类别", "特征描述"):
                v.require(nonempty_string(feature.get(key)), f"{item_path}.{key} must not be empty")
            v.require(feature.get("重要级别") in FEATURE_IMPORTANCE, f"{item_path}.重要级别 is unsupported")
            validate_sources(feature.get("本品事实来源"), f"{item_path}.本品事实来源", v)
            sources = feature.get("本品事实来源")
            if status == "READY" and isinstance(sources, list):
                v.require(
                    any(isinstance(source, dict) and source.get("source_type") == "当前产品图片" for source in sources),
                    f"{item_path}.本品事实来源 must include a 当前产品图片 source when READY",
                )
            feature_ids.append(str(feature.get("特征ID", "")))
        v.require(len(feature_ids) == len(set(feature_ids)), f"{path}.不可变特征 IDs must be unique")

    references = value.get("角度参考")
    reference_ids: list[str] = []
    reference_by_id: dict[str, dict[str, Any]] = {}
    if isinstance(references, list):
        for index, reference in enumerate(references):
            item_path = f"{path}.角度参考[{index}]"
            v.required_keys(reference, ["参考图ID", "文件路径", "视角", "角色", "可证明特征ID"], item_path)
            if not isinstance(reference, dict):
                continue
            for key in ("参考图ID", "文件路径", "视角"):
                v.require(nonempty_string(reference.get(key)), f"{item_path}.{key} must not be empty")
            v.require(reference.get("角色") in REFERENCE_ROLES, f"{item_path}.角色 is unsupported")
            proved_ids = reference.get("可证明特征ID")
            v.require(nonempty_list(proved_ids), f"{item_path}.可证明特征ID must not be empty")
            if isinstance(proved_ids, list):
                v.require(all(item in feature_ids for item in proved_ids), f"{item_path}.可证明特征ID must reference immutable features")
            reference_id = str(reference.get("参考图ID", ""))
            reference_ids.append(reference_id)
            reference_by_id[reference_id] = reference
        v.require(len(reference_ids) == len(set(reference_ids)), f"{path}.角度参考 IDs must be unique")

    primary_ids = value.get("主参考图ID")
    if isinstance(primary_ids, list):
        v.require(len(primary_ids) == len(set(primary_ids)), f"{path}.主参考图ID must be unique")
        for primary_id in primary_ids:
            v.require(primary_id in reference_by_id, f"{path}.主参考图ID contains an unknown reference ID")
            reference = reference_by_id.get(primary_id)
            if isinstance(reference, dict):
                v.require(reference.get("角色") == "主参考", f"{path}.主参考图ID must point to 角色=主参考")

    if status == "READY":
        v.require(nonempty_list(primary_ids), f"{path}.主参考图ID must not be empty when READY")
        v.require(nonempty_list(references), f"{path}.角度参考 must not be empty when READY")
        v.require(nonempty_list(features), f"{path}.不可变特征 must not be empty when READY")
        v.require(nonempty_list(value.get("允许变化")), f"{path}.允许变化 must not be empty when READY")
        v.require(nonempty_list(value.get("禁止推断")), f"{path}.禁止推断 must not be empty when READY")


def validate_fidelity_execution(value: Any, task: dict[str, Any], identity_lock: Any, path: str, v: Validation) -> None:
    v.required_keys(value, FIDELITY_EXECUTION_FIELDS, path)
    if not isinstance(value, dict) or not isinstance(identity_lock, dict):
        return
    method = value.get("生成方式")
    v.require(method in GENERATION_METHODS, f"{path}.生成方式 is unsupported; text-only product recreation is prohibited")
    primary_id = value.get("主参考图ID")
    v.require(nonempty_string(primary_id), f"{path}.主参考图ID must not be empty")
    for key in ("辅助参考图ID", "锁定特征ID", "允许变化", "禁止变化"):
        v.require(isinstance(value.get(key), list), f"{path}.{key} must be a list")
    for key in ("锁定特征ID", "允许变化", "禁止变化"):
        v.require(nonempty_list(value.get(key)), f"{path}.{key} must not be empty")
    v.require(nonempty_string(value.get("角度匹配说明")), f"{path}.角度匹配说明 must not be empty")
    v.require(value.get("结构推断风险") == "NONE", f"{path}.结构推断风险 must be NONE; change the view or return to S1")

    references = identity_lock.get("角度参考", [])
    reference_by_id = {
        item.get("参考图ID"): item for item in references if isinstance(item, dict) and nonempty_string(item.get("参考图ID"))
    }
    feature_ids = {
        item.get("特征ID") for item in identity_lock.get("不可变特征", []) if isinstance(item, dict) and nonempty_string(item.get("特征ID"))
    }
    primary = reference_by_id.get(primary_id)
    v.require(primary is not None, f"{path}.主参考图ID is not in product_identity_lock")
    auxiliary_ids = value.get("辅助参考图ID")
    if isinstance(auxiliary_ids, list):
        v.require(len(auxiliary_ids) == len(set(auxiliary_ids)), f"{path}.辅助参考图ID must be unique")
        v.require(primary_id not in auxiliary_ids, f"{path}.辅助参考图ID cannot repeat 主参考图ID")
        v.require(all(item in reference_by_id for item in auxiliary_ids), f"{path}.辅助参考图ID contains an unknown reference ID")
    if method == "多图参考生成":
        v.require(nonempty_list(auxiliary_ids), f"{path}.辅助参考图ID must not be empty for 多图参考生成")
    if method == "单图参考生成":
        v.require(isinstance(auxiliary_ids, list) and not auxiliary_ids, f"{path}.辅助参考图ID must be empty for 单图参考生成")

    locked_ids = value.get("锁定特征ID")
    if isinstance(locked_ids, list):
        v.require(len(locked_ids) == len(set(locked_ids)), f"{path}.锁定特征ID must be unique")
        v.require(all(item in feature_ids for item in locked_ids), f"{path}.锁定特征ID contains an unknown feature ID")
        supported_ids: set[str] = set()
        for reference_id in [primary_id] + (auxiliary_ids if isinstance(auxiliary_ids, list) else []):
            reference = reference_by_id.get(reference_id)
            if isinstance(reference, dict):
                supported_ids.update(reference.get("可证明特征ID", []))
        v.require(all(item in supported_ids for item in locked_ids), f"{path}.锁定特征ID must be visible in the selected references")

    source_paths = task.get("所用原图参考")
    if isinstance(source_paths, list):
        for reference_id in [primary_id] + (auxiliary_ids if isinstance(auxiliary_ids, list) else []):
            reference = reference_by_id.get(reference_id)
            if isinstance(reference, dict):
                v.require(reference.get("文件路径") in source_paths, f"{path} selected reference file must appear in 所用原图参考")
    if isinstance(primary, dict):
        view = str(primary.get("视角", "")).strip()
        v.require(view and view in str(task.get("产品展示角度", "")), f"{path} primary reference view must appear in 产品展示角度")


def validate_scene_design(value: Any, prompt: Any, path: str, v: Validation) -> None:
    v.required_keys(value, SCENE_DESIGN_FIELDS, path)
    if not isinstance(value, dict):
        return
    mode = value.get("场景模式")
    v.require(mode in SCENE_MODES, f"{path}.场景模式 must be one of {sorted(SCENE_MODES)}")
    for key in ("模式理由", "目标空间", "摆放与使用关系", "协调逻辑", "场景事实边界"):
        v.require(nonempty_string(value.get(key)), f"{path}.{key} must not be empty")
    for key in ("空间锚点", "尺度参照", "辅助元素"):
        v.require(isinstance(value.get(key), list), f"{path}.{key} must be a list")

    prompt_text = str(prompt or "")
    if mode == "真实使用场景":
        target = str(value.get("目标空间", "")).strip()
        v.require(target and not target.startswith("不适用"), f"{path}.目标空间 must name a concrete context for 真实使用场景")
        for key in ("空间锚点", "尺度参照", "辅助元素"):
            v.require(nonempty_list(value.get(key)), f"{path}.{key} must not be empty for 真实使用场景")
        if target:
            v.require(target in prompt_text, f"{path} target context must appear verbatim in 独立生图提示")
        anchors = value.get("空间锚点")
        if isinstance(anchors, list) and anchors:
            v.require(
                any(str(anchor).strip() and str(anchor).strip() in prompt_text for anchor in anchors),
                f"{path} at least one spatial anchor must appear verbatim in 独立生图提示",
            )
    elif mode in {"产品肖像", "细节证据"}:
        markers = [marker for marker in CONTEXTUAL_SCENE_MARKERS if marker in prompt_text]
        v.require(
            not markers,
            f"{path} prompt claims a contextual environment {markers}; use 真实使用场景 or remove the scene claim",
        )


def validate_image_task(task: Any, path: str, v: Validation, identity_lock: Any, require_selling_point: bool = False) -> None:
    v.required_keys(task, IMAGE_TASK_FIELDS, path)
    if not isinstance(task, dict):
        return
    if require_selling_point:
        v.require(nonempty_string(task.get("关联卖点ID")), f"{path}.关联卖点ID must not be empty")
    for key in ("资产ID", "关联单元", "生成比例", "最终裁切比例", "平台安全区", "镜头重点", "产品展示角度", "独立生图提示"):
        v.require(nonempty_string(task.get(key)), f"{path}.{key} must not be empty")
    v.require(nonempty_list(task.get("所用原图参考")), f"{path}.所用原图参考 must not be empty")
    validate_fidelity_execution(task.get("保真执行"), task, identity_lock, f"{path}.保真执行", v)
    validate_scene_design(task.get("场景设计"), task.get("独立生图提示"), f"{path}.场景设计", v)
    validate_prohibitions(task.get("禁止项"), f"{path}.禁止项", v)
    validate_sources(task.get("对应的真实产品依据"), f"{path}.对应的真实产品依据", v)


def validate_screen2(
    screen2: Any,
    config: dict[str, Any],
    approved_points: list[dict[str, Any]],
    image_task_by_id: dict[str, dict[str, Any]],
    identity_lock: Any,
    path: str,
    v: Validation,
) -> None:
    if not isinstance(screen2, dict):
        v.errors.append(f"{path} must be an object")
        return
    card_count = config.get("screen2_card_count", 0)
    responsibility = screen2.get("页面职责", "")
    v.require(isinstance(responsibility, str) and "卖点总览" in responsibility, f"{path}.页面职责 must identify a selling-point overview")
    if card_count == 6 and not config.get("screen2_card_count_override"):
        v.require(responsibility == "六大卖点总览", f"{path}.页面职责 must be 六大卖点总览 for the default contract")
    points = screen2.get("卖点总览")
    v.require(isinstance(points, list) and len(points) == card_count, f"{path}.卖点总览 must contain {card_count} items")
    if not isinstance(points, list):
        return
    approved_by_id = {point.get("卖点ID"): point for point in approved_points}
    expected_source_ids = [point.get("卖点ID") for point in approved_points[:card_count]]
    actual_source_ids: list[str] = []
    sequence_ids: list[str] = []
    asset_ids: list[str] = []
    layout_by_id = {
        item.get("卡片ID"): item
        for item in config.get("screen2_layout_spec", [])
        if isinstance(item, dict)
    }
    for index, point in enumerate(points, start=1):
        item_path = f"{path}.卖点总览[{index - 1}]"
        v.required_keys(point, ["卖点ID", "来源卖点ID", "卖点三行文案", "对应的真实产品依据", "对应纯图资产"], item_path)
        if not isinstance(point, dict):
            continue
        expected_sequence = f"SP-{index:02d}"
        sequence_id = point.get("卖点ID")
        source_id = point.get("来源卖点ID")
        sequence_ids.append(str(sequence_id))
        actual_source_ids.append(str(source_id))
        v.require(sequence_id == expected_sequence, f"{item_path}.卖点ID must be {expected_sequence}")
        approved = approved_by_id.get(source_id)
        v.require(approved is not None, f"{item_path}.来源卖点ID is not in the approved snapshot")
        copy = point.get("卖点三行文案")
        v.required_keys(copy, ["类别", "具体特征", "简短利益"], f"{item_path}.卖点三行文案")
        if isinstance(copy, dict):
            for copy_key in ("类别", "具体特征"):
                validate_consumer_visible_text(copy.get(copy_key), f"{item_path}.卖点三行文案.{copy_key}", v)
            validate_conversion_benefit_text(copy.get("简短利益"), f"{item_path}.卖点三行文案.简短利益", v)
        if isinstance(copy, dict) and isinstance(approved, dict):
            v.require(copy.get("类别") == approved.get("类别"), f"{item_path} category differs from the approved selling point")
            v.require(copy.get("具体特征") == approved.get("具体产品事实"), f"{item_path} fact differs from the approved selling point")
            v.require(copy.get("简短利益") == approved.get("可转化利益"), f"{item_path} benefit differs from the approved selling point")
            v.require(json_key(point.get("对应的真实产品依据")) == json_key(approved.get("本品事实来源")), f"{item_path} sources differ from the approved selling point")
        asset = point.get("对应纯图资产")
        validate_image_task(asset, f"{item_path}.对应纯图资产", v, identity_lock, require_selling_point=True)
        if isinstance(asset, dict):
            expected_asset_id = f"S2-{expected_sequence}"
            asset_id = asset.get("资产ID")
            asset_ids.append(str(asset_id))
            v.require(asset_id == expected_asset_id, f"{item_path}.对应纯图资产.资产ID must be {expected_asset_id}")
            v.require(asset.get("关联卖点ID") == source_id, f"{item_path}.对应纯图资产.关联卖点ID must match 来源卖点ID")
            layout = layout_by_id.get(sequence_id, {})
            v.require(asset.get("卡位") == layout.get("卡位"), f"{item_path}.对应纯图资产.卡位 must match screen2_layout_spec")
            v.require(asset.get("生成比例") == layout.get("建议卡片比例"), f"{item_path}.对应纯图资产.生成比例 must match screen2_layout_spec")
            matching_task = image_task_by_id.get(str(asset_id))
            v.require(matching_task is not None, f"{item_path} asset must also exist in 方案.图片任务")
            if isinstance(matching_task, dict):
                for key in IMAGE_TASK_FIELDS + ["关联卖点ID", "卡位"]:
                    v.require(json_key(matching_task.get(key)) == json_key(asset.get(key)), f"{item_path} asset field {key} differs from 方案.图片任务")
    v.require(actual_source_ids == expected_source_ids, "Screen 2 must use the first approved selling points in approved order")
    v.require(len(sequence_ids) == len(set(sequence_ids)) == card_count, "Screen 2 sequence IDs must be unique")
    v.require(len(asset_ids) == len(set(asset_ids)) == card_count, "Screen 2 asset IDs must be unique")


def validate_image_brief(brief: Any, path: str, v: Validation, require_selling_point: bool = False) -> None:
    v.required_keys(brief, IMAGE_BRIEF_FIELDS, path)
    if not isinstance(brief, dict):
        return
    for key in ("资产ID", "关联单元", "生成比例", "最终裁切比例", "证明目标", "镜头重点", "产品展示角度", "目标空间"):
        v.require(nonempty_string(brief.get(key)), f"{path}.{key} must not be empty")
    v.require(brief.get("场景模式") in SCENE_MODES, f"{path}.场景模式 is unsupported")
    if require_selling_point:
        v.require(nonempty_string(brief.get("关联卖点ID")), f"{path}.关联卖点ID must not be empty")
    if brief.get("场景模式") == "真实使用场景":
        target = str(brief.get("目标空间", ""))
        v.require(not target.startswith("不适用"), f"{path}.目标空间 must name a real context")


def validate_screen2_briefs(
    screen2: Any,
    config: dict[str, Any],
    approved_points: list[dict[str, Any]],
    briefs_by_id: dict[str, dict[str, Any]],
    path: str,
    v: Validation,
) -> None:
    if not isinstance(screen2, dict):
        v.errors.append(f"{path} must be an object")
        return
    card_count = config.get("screen2_card_count", 0)
    responsibility = screen2.get("页面职责", "")
    v.require(isinstance(responsibility, str) and "卖点总览" in responsibility, f"{path}.页面职责 must identify a selling-point overview")
    points = screen2.get("卖点总览")
    v.require(isinstance(points, list) and len(points) == card_count, f"{path}.卖点总览 must contain {card_count} items")
    if not isinstance(points, list):
        return
    approved_by_id = {point.get("卖点ID"): point for point in approved_points}
    expected_source_ids = [point.get("卖点ID") for point in approved_points[:card_count]]
    actual_source_ids = []
    asset_ids = []
    layout_by_id = {item.get("卡片ID"): item for item in config.get("screen2_layout_spec", []) if isinstance(item, dict)}
    for index, point in enumerate(points, start=1):
        item_path = f"{path}.卖点总览[{index - 1}]"
        v.required_keys(point, ["卖点ID", "来源卖点ID", "卖点三行文案", "对应的真实产品依据", "对应纯图资产"], item_path)
        if not isinstance(point, dict):
            continue
        sequence_id = f"SP-{index:02d}"
        source_id = point.get("来源卖点ID")
        actual_source_ids.append(source_id)
        v.require(point.get("卖点ID") == sequence_id, f"{item_path}.卖点ID must be {sequence_id}")
        approved = approved_by_id.get(source_id)
        v.require(approved is not None, f"{item_path}.来源卖点ID is not approved")
        copy_block = point.get("卖点三行文案")
        v.required_keys(copy_block, ["类别", "具体特征", "简短利益"], f"{item_path}.卖点三行文案")
        if isinstance(copy_block, dict) and isinstance(approved, dict):
            for key in ("类别", "具体特征"):
                validate_consumer_visible_text(copy_block.get(key), f"{item_path}.卖点三行文案.{key}", v)
            validate_conversion_benefit_text(copy_block.get("简短利益"), f"{item_path}.卖点三行文案.简短利益", v)
            v.require(copy_block.get("类别") == approved.get("类别"), f"{item_path} category differs from approval")
            v.require(copy_block.get("具体特征") == approved.get("具体产品事实"), f"{item_path} fact differs from approval")
            v.require(copy_block.get("简短利益") == approved.get("可转化利益"), f"{item_path} benefit differs from approval")
            v.require(json_key(point.get("对应的真实产品依据")) == json_key(approved.get("本品事实来源")), f"{item_path} sources differ from approval")
        asset = point.get("对应纯图资产")
        validate_image_brief(asset, f"{item_path}.对应纯图资产", v, require_selling_point=True)
        if isinstance(asset, dict):
            asset_id = f"S2-{sequence_id}"
            asset_ids.append(asset.get("资产ID"))
            v.require(asset.get("资产ID") == asset_id, f"{item_path}.对应纯图资产.资产ID must be {asset_id}")
            v.require(asset.get("关联卖点ID") == source_id, f"{item_path}.对应纯图资产.关联卖点ID must match 来源卖点ID")
            layout = layout_by_id.get(sequence_id, {})
            v.require(asset.get("卡位") == layout.get("卡位"), f"{item_path}.卡位 must match screen2_layout_spec")
            v.require(asset.get("生成比例") == layout.get("建议卡片比例"), f"{item_path}.生成比例 must match screen2_layout_spec")
            matching = briefs_by_id.get(asset_id)
            v.require(matching is not None, f"{item_path} brief must exist in 方案.图片简报")
            if isinstance(matching, dict):
                for key in IMAGE_BRIEF_FIELDS + ["关联卖点ID", "卡位"]:
                    v.require(json_key(matching.get(key)) == json_key(asset.get(key)), f"{item_path} brief field {key} differs from 方案.图片简报")
    v.require(actual_source_ids == expected_source_ids, "Screen 2 must preserve approved selling-point order")
    v.require(len(asset_ids) == len(set(asset_ids)) == card_count, "Screen 2 brief asset IDs must be unique")


def validate_copy_uniqueness(copy_data: Any, path: str, v: Validation) -> None:
    if not isinstance(copy_data, dict):
        return
    units = copy_data.get("屏幕文案")
    values = list(units.values()) if isinstance(units, dict) else copy_data.get("内容单元", [])
    if not isinstance(values, list):
        return
    for field in ("主标题", "副标题", "卖点短句", "说明文案"):
        texts = [str(unit.get(field, "")).strip().lower() for unit in values if isinstance(unit, dict) and nonempty_string(unit.get(field))]
        v.require(len(texts) == len(set(texts)), f"{path}.{field} contains duplicate copy across units")


def copy_unit_ids(copy_data: Any) -> list[str]:
    if not isinstance(copy_data, dict):
        return []
    screens = copy_data.get("屏幕文案")
    if isinstance(screens, dict):
        return list(screens.keys())
    units = copy_data.get("内容单元")
    if isinstance(units, list):
        return [str(unit.get("单元ID", "")) for unit in units if isinstance(unit, dict)]
    return []


def validate_purchase_narrative(value: Any, path: str, v: Validation) -> None:
    v.required_keys(value, PURCHASE_NARRATIVE_FIELDS, path)
    if not isinstance(value, dict):
        return
    for key in ("核心购买主张", "首屏承诺", "文案气质"):
        v.require(nonempty_string(value.get(key)), f"{path}.{key} must not be empty")
    for key in ("主要购买顾虑", "决策递进"):
        v.require(nonempty_list(value.get(key)), f"{path}.{key} must be a nonempty list")
    if isinstance(value.get("决策递进"), list):
        v.require(len(value["决策递进"]) >= 4, f"{path}.决策递进 must cover desire, proof, fit, and action")


def validate_copy_quality(value: Any, copy_data: Any, path: str, v: Validation) -> None:
    v.required_keys(value, COPY_QUALITY_FIELDS, path)
    if not isinstance(value, dict):
        return
    v.require(value.get("状态") == "PASS", f"{path}.状态 must be PASS before strategy review")
    v.require(nonempty_string(value.get("本方案核心购买理由")), f"{path}.本方案核心购买理由 must not be empty")
    for key in ("泛化表达", "重复风险", "修正记录"):
        v.require(isinstance(value.get(key), list), f"{path}.{key} must be a list")
    v.require(not value.get("泛化表达"), f"{path}.泛化表达 must be resolved before delivery")
    v.require(not value.get("重复风险"), f"{path}.重复风险 must be resolved before delivery")
    checks = value.get("单元检查")
    expected_ids = copy_unit_ids(copy_data)
    v.require(isinstance(checks, list), f"{path}.单元检查 must be a list")
    if not isinstance(checks, list):
        return
    ids: list[str] = []
    for index, check in enumerate(checks):
        item_path = f"{path}.单元检查[{index}]"
        v.required_keys(check, COPY_QUALITY_UNIT_FIELDS, item_path)
        if not isinstance(check, dict):
            continue
        unit_id = str(check.get("单元ID", ""))
        ids.append(unit_id)
        v.require(nonempty_string(check.get("消费者决策问题")), f"{item_path}.消费者决策问题 must not be empty")
        v.require(nonempty_string(check.get("事实锚点")), f"{item_path}.事实锚点 must not be empty")
        v.require(check.get("产品专属性") == "HIGH", f"{item_path}.产品专属性 must be HIGH for final consumer copy")
        v.require(check.get("购买理由明确") is True, f"{item_path}.购买理由明确 must be true")
        for key in ("泛化表达", "重复风险", "修正记录"):
            v.require(isinstance(check.get(key), list), f"{item_path}.{key} must be a list")
        v.require(not check.get("泛化表达"), f"{item_path}.泛化表达 must be resolved")
        v.require(not check.get("重复风险"), f"{item_path}.重复风险 must be resolved")
    v.require(ids == expected_ids, f"{path}.单元检查 must cover every copy unit in order")


def validate_strategy_review(data: dict[str, Any], config: dict[str, Any], approval: dict[str, Any], v: Validation) -> None:
    v.required_keys(data, ["product_identity", "shared_product_data", "competitor_research", "options"], "$")
    v.require(approval.get("selling_points_approved") is True, "S3A requires approved selling points")
    v.require(approval.get("strategy_approved") is False, "S3A strategy must remain unapproved")
    approved_points = validate_approved_points(approval.get("approved_selling_points"), "$.approval_snapshot.approved_selling_points", v)
    validate_research(data.get("competitor_research"), v, 3)
    validate_audit(data.get("audit_result"), v, require_pass=True)
    v.require(isinstance(data.get("shared_product_data"), dict) and bool(data.get("shared_product_data")), "shared_product_data must not be empty")
    options = data.get("options")
    v.require(isinstance(options, list) and len(options) == 3, "options must contain exactly A, B, C")
    if not isinstance(options, list):
        return
    v.require([option.get("方案ID") for option in options if isinstance(option, dict)] == ["A", "B", "C"], "options must be ordered A, B, C")
    dimension_vectors = []
    for index, option in enumerate(options):
        path = f"$.options[{index}]"
        review_option_fields = STRATEGY_REVIEW_OPTION_FIELDS + (["购买叙事", "文案质检"] if data.get("schema_version") == 3 else [])
        v.required_keys(option, review_option_fields, path)
        if not isinstance(option, dict):
            continue
        v.require(option.get("目标平台") == config.get("target_platform"), f"{path}.目标平台 must match task_config")
        v.require(option.get("任务类型") == data.get("task_profile"), f"{path}.任务类型 must match task_profile")
        v.require(option.get("期望图片数量") == config.get("image_count"), f"{path}.期望图片数量 must match image_count")
        v.require(option.get("文案模式") == "电商转化型", f"{path}.文案模式 must be 电商转化型")
        for key in ("方案定位", "文案语调指引", "转化重点", "风格名称", "视觉世界观", "色彩策略", "光影策略", "版式语言", "纯图生成约束", "下游执行注意事项"):
            v.require(nonempty_string(option.get(key)), f"{path}.{key} must not be empty")
        briefs = option.get("图片简报")
        v.require(isinstance(briefs, list) and len(briefs) == config.get("image_count"), f"{path}.图片简报 must match image_count")
        brief_by_id = {}
        if isinstance(briefs, list):
            for brief_index, brief in enumerate(briefs):
                brief_path = f"{path}.图片简报[{brief_index}]"
                validate_image_brief(brief, brief_path, v)
                if isinstance(brief, dict):
                    asset_id = str(brief.get("资产ID", ""))
                    v.require(asset_id not in brief_by_id, f"{brief_path}.资产ID must be unique")
                    brief_by_id[asset_id] = brief
        copy_data = option.get("文案成稿")
        if not isinstance(copy_data, dict):
            v.errors.append(f"{path}.文案成稿 must be an object")
            continue
        if data.get("schema_version") == 3:
            validate_purchase_narrative(option.get("购买叙事"), f"{path}.购买叙事", v)
            validate_copy_quality(option.get("文案质检"), copy_data, f"{path}.文案质检", v)
        if data.get("task_profile") == "DETAIL_PAGE":
            screens = copy_data.get("屏幕文案")
            expected_names = [f"第{i}屏" for i in range(1, config.get("screen_count", 0) + 1)]
            v.require(isinstance(screens, dict) and list(screens.keys()) == expected_names, f"{path}.屏幕文案 must match screen_count")
            if isinstance(screens, dict):
                for name in expected_names:
                    validate_customer_copy(screens.get(name), f"{path}.文案成稿.屏幕文案.{name}", v)
                if "第2屏" in screens:
                    validate_screen2_briefs(screens["第2屏"], config, approved_points, brief_by_id, f"{path}.文案成稿.屏幕文案.第2屏", v)
        else:
            units = copy_data.get("内容单元")
            v.require(isinstance(units, list) and len(units) == config.get("image_count"), f"{path}.内容单元 must match image_count")
            for unit_index, unit in enumerate(units if isinstance(units, list) else []):
                validate_customer_copy(unit, f"{path}.文案成稿.内容单元[{unit_index}]", v, require_unit_id=True)
        validate_copy_uniqueness(copy_data, f"{path}.文案成稿", v)
        scene_distribution = sorted(str(brief.get("场景模式")) for brief in briefs if isinstance(brief, dict)) if isinstance(briefs, list) else []
        contexts = sorted(str(brief.get("目标空间")) for brief in briefs if isinstance(brief, dict)) if isinstance(briefs, list) else []
        proof_goals = sorted(str(brief.get("证明目标")) for brief in briefs if isinstance(brief, dict)) if isinstance(briefs, list) else []
        dimension_vectors.append([
            option.get("转化重点"), option.get("视觉世界观"), option.get("色彩策略"), option.get("光影策略"),
            option.get("版式语言"), scene_distribution, contexts, proof_goals,
        ])
    for left in range(len(dimension_vectors)):
        for right in range(left + 1, len(dimension_vectors)):
            differences = sum(json_key(a) != json_key(b) for a, b in zip(dimension_vectors[left], dimension_vectors[right]))
            v.require(differences >= 3, f"options {chr(65 + left)}/{chr(65 + right)} must differ in at least three conversion/visual dimensions")


def validate_selected_execution(data: dict[str, Any], config: dict[str, Any], approval: dict[str, Any], artifact_path: Path | None, v: Validation) -> None:
    v.required_keys(data, ["selected_strategy_id", "strategy_source", "selected_strategy", "competitor_research"], "$")
    v.require(approval.get("selling_points_approved") is True and approval.get("strategy_approved") is True, "S3B requires both approvals")
    selected_id = data.get("selected_strategy_id")
    v.require(selected_id in {"A", "B", "C"}, "selected_strategy_id must be A, B, or C")
    v.require(selected_id == approval.get("approved_strategy_id"), "selected_strategy_id must match approval_snapshot")
    source = data.get("strategy_source")
    v.required_keys(source, ["path", "sha256", "brief_ids"], "$.strategy_source")
    approved_source_option = None
    if isinstance(source, dict):
        v.require(re.fullmatch(r"[0-9a-f]{64}", str(source.get("sha256", ""))) is not None, "strategy_source.sha256 must be lowercase SHA-256")
        if artifact_path is None:
            v.errors.append("S3B validation requires the selected-strategy artifact path")
        elif nonempty_string(source.get("path")):
            root = artifact_path.resolve().parent
            candidate = (root / str(source.get("path"))).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                v.errors.append("strategy_source.path escapes the artifact directory")
            else:
                if not candidate.is_file():
                    v.errors.append("strategy_source.path does not exist")
                elif sha256_file(candidate) != source.get("sha256"):
                    v.errors.append("strategy_source.sha256 does not match the source package")
                else:
                    try:
                        source_data = json.loads(candidate.read_text(encoding="utf-8-sig"))
                    except json.JSONDecodeError:
                        v.errors.append("strategy_source.path is invalid JSON")
                    else:
                        for source_option in source_data.get("options", []) if isinstance(source_data, dict) else []:
                            if isinstance(source_option, dict) and source_option.get("方案ID") == selected_id:
                                approved_source_option = source_option
                                break
                        v.require(approved_source_option is not None, "strategy_source does not contain the approved option")
    option = data.get("selected_strategy")
    v.required_keys(option, OPTION_FIELDS + ["购买叙事", "文案质检"], "$.selected_strategy")
    if not isinstance(option, dict):
        return
    v.require(option.get("方案ID") == selected_id, "selected_strategy.方案ID must match selected_strategy_id")
    tasks = option.get("图片任务")
    v.require(isinstance(tasks, list) and len(tasks) == config.get("image_count"), "selected_strategy.图片任务 must match image_count")
    task_ids = []
    for index, task in enumerate(tasks if isinstance(tasks, list) else []):
        validate_image_task(task, f"$.selected_strategy.图片任务[{index}]", v, data.get("product_identity_lock"))
        if isinstance(task, dict):
            task_ids.append(task.get("资产ID"))
    if isinstance(source, dict):
        v.require(task_ids == source.get("brief_ids"), "selected execution task IDs must exactly match approved brief IDs")
    if isinstance(approved_source_option, dict):
        source_brief_ids = [brief.get("资产ID") for brief in approved_source_option.get("图片简报", []) if isinstance(brief, dict)]
        v.require(task_ids == source_brief_ids, "selected execution task IDs differ from the source option briefs")
        for key in ("方案ID", "方案定位", "目标平台", "任务类型", "期望图片数量", "文案模式", "文案语调指引", "风格名称", "视觉世界观", "色彩策略", "光影策略", "核心材质库", "版式语言", "设计风格标签", "购买叙事", "文案质检", "文案成稿", "纯图生成约束", "下游执行注意事项"):
            v.require(json_key(option.get(key)) == json_key(approved_source_option.get(key)), f"selected_strategy.{key} differs from the approved S3A option")
    validate_copy_uniqueness(option.get("文案成稿"), "$.selected_strategy.文案成稿", v)
    validate_purchase_narrative(option.get("购买叙事"), "$.selected_strategy.购买叙事", v)
    validate_copy_quality(option.get("文案质检"), option.get("文案成稿"), "$.selected_strategy.文案质检", v)
    validate_audit(data.get("audit_result"), v, require_pass=True)


def validate_audit(value: Any, v: Validation, require_pass: bool) -> None:
    path = "$.audit_result"
    if not isinstance(value, dict):
        return
    if not require_pass:
        v.require(value.get("status") in {"PENDING", "BLOCKED"}, f"{path}.status must be PENDING or BLOCKED before S3")
        return
    v.require(value.get("status") == "PASS", f"{path}.status must be PASS")
    perspectives = value.get("perspectives")
    expected = {"商业操盘", "视觉设计", "技术执行", "转化心理"}
    v.require(isinstance(perspectives, dict) and set(perspectives) == expected, f"{path}.perspectives must contain the four review perspectives")
    if isinstance(perspectives, dict):
        for name in expected:
            item = perspectives.get(name)
            v.required_keys(item, ["结论", "风险"], f"{path}.perspectives.{name}")
            if isinstance(item, dict):
                v.require(nonempty_string(item.get("结论")), f"{path}.perspectives.{name}.结论 must not be empty")
                v.require(isinstance(item.get("风险"), list), f"{path}.perspectives.{name}.风险 must be a list")
    checks = value.get("redline_checks")
    v.require(isinstance(checks, list) and len(checks) == 12, f"{path}.redline_checks must contain R1 through R12")
    if isinstance(checks, list):
        ids = []
        for index, check in enumerate(checks):
            item_path = f"{path}.redline_checks[{index}]"
            v.required_keys(check, ["redline_id", "status", "findings", "corrections"], item_path)
            if not isinstance(check, dict):
                continue
            ids.append(check.get("redline_id"))
            v.require(check.get("status") in {"PASS", "NOT_APPLICABLE"}, f"{item_path}.status cannot remain FAIL")
            v.require(isinstance(check.get("findings"), list), f"{item_path}.findings must be a list")
            v.require(isinstance(check.get("corrections"), list), f"{item_path}.corrections must be a list")
            if check.get("status") == "NOT_APPLICABLE":
                v.require(nonempty_list(check.get("findings")), f"{item_path} must explain why it is not applicable")
        v.require(ids == [f"R{i}" for i in range(1, 13)], "redline_checks must be ordered R1 through R12")


def validate_strategy(data: dict[str, Any], config: dict[str, Any], approval: dict[str, Any], v: Validation) -> None:
    v.required_keys(data, ["product_identity", "competitor_research", "options"], "$")
    v.require(approval.get("selling_points_approved") is True, "S3 requires explicit selling-point approval")
    v.require(nonempty_string(approval.get("selling_point_approval_evidence")), "S3 selling-point approval evidence must not be empty")
    v.require(approval.get("strategy_approved") is False, "S3 strategy remains unapproved until the user selects A, B, or C")
    approved_points = validate_approved_points(approval.get("approved_selling_points"), "$.approval_snapshot.approved_selling_points", v)
    identity_lock = data.get("product_identity_lock")
    validate_research(data.get("competitor_research"), v)
    validate_audit(data.get("audit_result"), v, require_pass=True)

    options = data.get("options")
    v.require(isinstance(options, list) and len(options) == 3, "options must contain exactly three strategies")
    if not isinstance(options, list):
        return
    option_ids = [option.get("方案ID") for option in options if isinstance(option, dict)]
    v.require(option_ids == ["A", "B", "C"], "options must be ordered A, B, C")
    signatures: list[str] = []
    for option_index, option in enumerate(options):
        path = f"$.options[{option_index}]"
        v.required_keys(option, OPTION_FIELDS, path)
        if not isinstance(option, dict):
            continue
        v.require(option.get("目标平台") == config.get("target_platform"), f"{path}.目标平台 must match task_config")
        v.require(option.get("任务类型") == data.get("task_profile"), f"{path}.任务类型 must match task_profile")
        v.require(option.get("期望图片数量") == config.get("image_count"), f"{path}.期望图片数量 must match task_config.image_count")
        v.require(option.get("文案模式") == "电商转化型", f"{path}.文案模式 must be 电商转化型")
        for key in ("方案定位", "文案语调指引", "风格名称", "视觉世界观", "色彩策略", "光影策略", "版式语言", "纯图生成约束", "下游执行注意事项"):
            v.require(nonempty_string(option.get(key)), f"{path}.{key} must not be empty")
        for key in ("核心材质库", "产品信息", "产品参数"):
            v.require(isinstance(option.get(key), (dict, list)) and bool(option.get(key)), f"{path}.{key} must not be empty")
        v.require(nonempty_list(option.get("设计风格标签")), f"{path}.设计风格标签 must not be empty")
        pure_text = str(option.get("纯图生成约束", "")).lower()
        v.require("文字" in pure_text and "留白" in pure_text and "拼贴" in pure_text, f"{path}.纯图生成约束 must prohibit text, intentional blank space, and collage")
        signatures.append(json_key([option.get("风格名称"), option.get("视觉世界观"), option.get("色彩策略"), option.get("光影策略"), option.get("版式语言")]))

        tasks = option.get("图片任务")
        v.require(isinstance(tasks, list) and len(tasks) == config.get("image_count"), f"{path}.图片任务 must match image_count")
        task_by_id: dict[str, dict[str, Any]] = {}
        if isinstance(tasks, list):
            for task_index, task in enumerate(tasks):
                task_path = f"{path}.图片任务[{task_index}]"
                validate_image_task(task, task_path, v, identity_lock)
                if isinstance(task, dict):
                    task_id = str(task.get("资产ID", ""))
                    v.require(task_id not in task_by_id, f"{task_path}.资产ID must be unique within the option")
                    task_by_id[task_id] = task

        copy = option.get("文案成稿")
        if not isinstance(copy, dict):
            v.errors.append(f"{path}.文案成稿 must be an object")
            continue
        if data.get("task_profile") == "DETAIL_PAGE":
            screens = copy.get("屏幕文案")
            screen_count = config.get("screen_count", 0)
            expected_names = [f"第{i}屏" for i in range(1, screen_count + 1)]
            v.require(isinstance(screens, dict) and list(screens.keys()) == expected_names, f"{path}.文案成稿.屏幕文案 must contain exactly the configured screens in order")
            if isinstance(screens, dict):
                for screen_name in expected_names:
                    screen_path = f"{path}.文案成稿.屏幕文案.{screen_name}"
                    screen = screens.get(screen_name)
                    validate_customer_copy(screen, screen_path, v)
                if "第2屏" in screens:
                    validate_screen2(screens["第2屏"], config, approved_points, task_by_id, identity_lock, f"{path}.文案成稿.屏幕文案.第2屏", v)
        else:
            units = copy.get("内容单元")
            v.require(isinstance(units, list) and len(units) == config.get("image_count"), f"{path}.文案成稿.内容单元 must match image_count")
            if isinstance(units, list):
                ids: list[str] = []
                for unit_index, unit in enumerate(units):
                    unit_path = f"{path}.文案成稿.内容单元[{unit_index}]"
                    validate_customer_copy(unit, unit_path, v, require_unit_id=True)
                    if isinstance(unit, dict):
                        ids.append(str(unit.get("单元ID", "")))
                v.require(len(ids) == len(set(ids)) == config.get("image_count"), f"{path} content unit IDs must be unique")
    v.require(len(signatures) == len(set(signatures)) == 3, "A/B/C must differ in more than labels or background color")


def validate_check(value: Any, path: str, v: Validation) -> None:
    v.required_keys(value, ["status", "notes"], path)
    if isinstance(value, dict):
        v.require(value.get("status") in {"PASS", "FAIL", "PENDING"}, f"{path}.status is unsupported")


def validate_fidelity_check(value: Any, path: str, v: Validation, generated: bool) -> None:
    v.required_keys(value, ["status", "notes", "检查项"], path)
    if not isinstance(value, dict):
        return
    v.require(value.get("status") in {"PASS", "FAIL", "PENDING"}, f"{path}.status is unsupported")
    if generated:
        v.require(value.get("status") == "PASS", f"{path}.status must be PASS for a generated asset")
        v.require(nonempty_string(value.get("notes")), f"{path}.notes must not be empty for a generated asset")
    checks = value.get("检查项")
    v.require(isinstance(checks, dict), f"{path}.检查项 must be an object")
    if not isinstance(checks, dict):
        return
    v.require(list(checks.keys()) == FIDELITY_CHECK_ITEMS, f"{path}.检查项 must contain the ordered fidelity checklist")
    for name in FIDELITY_CHECK_ITEMS:
        item_path = f"{path}.检查项.{name}"
        check = checks.get(name)
        v.required_keys(check, ["status", "notes"], item_path)
        if not isinstance(check, dict):
            continue
        v.require(check.get("status") in {"PASS", "FAIL", "PENDING", "NOT_APPLICABLE"}, f"{item_path}.status is unsupported")
        if generated:
            v.require(check.get("status") in {"PASS", "NOT_APPLICABLE"}, f"{item_path}.status must be PASS or NOT_APPLICABLE for a generated asset")
            v.require(nonempty_string(check.get("notes")), f"{item_path}.notes must not be empty for a generated asset")


def explicit_production_request(text: Any, option: Any) -> bool:
    if not nonempty_string(text) or option not in {"A", "B", "C"}:
        return False
    compact = re.sub(r"\s+", "", str(text))
    return (
        ("开始生成" in compact or "开始制作" in compact or "开始生图" in compact)
        and (f"方案{option}" in compact or str(option) in compact)
        and ("图片" in compact or "纯图" in compact or "生图" in compact)
    )


def validate_production_authorization(
    reference: Any,
    artifact_path: Path | None,
    data: dict[str, Any],
    execution_ref: Any,
    v: Validation,
) -> None:
    v.required_keys(reference, ["path", "sha256"], "$.production_authorization_ref")
    if not isinstance(reference, dict):
        return
    v.require(re.fullmatch(r"[0-9a-f]{64}", str(reference.get("sha256", ""))) is not None, "production_authorization_ref.sha256 must be lowercase SHA-256")
    if artifact_path is None or not nonempty_string(reference.get("path")):
        return
    root = artifact_path.resolve().parent
    candidate = (root / str(reference.get("path"))).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        v.errors.append("production_authorization_ref.path escapes the artifact directory")
        return
    if not candidate.is_file():
        v.errors.append("production_authorization_ref.path does not exist")
        return
    if sha256_file(candidate) != reference.get("sha256"):
        v.errors.append("production_authorization_ref.sha256 does not match")
        return
    try:
        authorization = json.loads(candidate.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        v.errors.append("production_authorization_ref.path is not valid JSON")
        return
    required = ["schema_version", "skill_version", "workflow_id", "product_fingerprint", "selected_strategy_id", "selected_execution_path", "selected_execution_sha256", "approval_text", "requested_scope", "authorized_at"]
    v.required_keys(authorization, required, "$.production_authorization_ref.file")
    if not isinstance(authorization, dict):
        return
    v.require(authorization.get("schema_version") == 3 and authorization.get("skill_version") == SKILL_VERSION, "production authorization must use schema-v3 and current skill version")
    v.require(authorization.get("workflow_id") == data.get("workflow_id"), "production authorization workflow_id differs from S4")
    v.require(authorization.get("product_fingerprint") == data.get("product_fingerprint"), "production authorization product_fingerprint differs from S4")
    v.require(authorization.get("selected_strategy_id") == data.get("approved_strategy_id"), "production authorization strategy differs from S4")
    v.require(explicit_production_request(authorization.get("approval_text"), authorization.get("selected_strategy_id")), "production authorization must contain an explicit image-production request; '继续' and '确定' are invalid")
    v.require(isinstance(authorization.get("requested_scope"), list) and authorization.get("requested_scope") == data.get("requested_scope"), "S4 requested_scope must exactly match the production authorization")
    if isinstance(execution_ref, dict):
        v.require(authorization.get("selected_execution_path") == execution_ref.get("path"), "production authorization execution path differs from S4")
        v.require(authorization.get("selected_execution_sha256") == execution_ref.get("sha256"), "production authorization execution hash differs from S4")


def validate_selected_execution_delivery(selected_path: Path, v: Validation) -> None:
    root = selected_path.parent
    required = ("selected-strategy-review.md", "selected-strategy-handoff.md", "review-package-manifest.json")
    for name in required:
        v.require((root / name).is_file(), f"S4 requires verified S3B delivery file: {name}")
    manifest_path = root / "review-package-manifest.json"
    if not manifest_path.is_file():
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        v.errors.append("S4 requires a valid S3B review-package-manifest.json")
        return
    v.require(manifest.get("workflow_stage") == "S3_SELECTED_STRATEGY_EXECUTION", "S4 requires an S3B review-package manifest")
    listed = {entry.get("path"): entry for entry in manifest.get("files", []) if isinstance(entry, dict)}
    for name in (selected_path.name, "selected-strategy-review.md", "selected-strategy-handoff.md"):
        entry = listed.get(name)
        v.require(isinstance(entry, dict), f"S3B review-package manifest omits {name}")
        if isinstance(entry, dict) and (root / name).is_file():
            v.require(entry.get("sha256") == sha256_file(root / name), f"S3B review-package manifest hash mismatch for {name}")


def validate_image_manifest(
    data: dict[str, Any],
    config: dict[str, Any],
    approval: dict[str, Any],
    artifact_path: Path | None,
    v: Validation,
) -> None:
    v.required_keys(data, ["approved_strategy_id", "assets"], "$")
    v.require(approval.get("selling_points_approved") is True, "S4 requires approved selling points")
    v.require(approval.get("strategy_approved") is True, "S4 requires strategy approval")
    if data.get("schema_version") == 3:
        v.required_keys(data, ["execution_package_ref", "production_authorization_ref", "requested_scope"], "$")
        execution_ref = data.get("execution_package_ref")
        v.required_keys(execution_ref, ["path", "sha256"], "$.execution_package_ref")
        execution_tasks = None
        if isinstance(execution_ref, dict):
            v.require(re.fullmatch(r"[0-9a-f]{64}", str(execution_ref.get("sha256", ""))) is not None, "execution_package_ref.sha256 must be lowercase SHA-256")
            if artifact_path is not None and nonempty_string(execution_ref.get("path")):
                root = artifact_path.resolve().parent
                candidate = (root / str(execution_ref.get("path"))).resolve()
                try:
                    candidate.relative_to(root)
                except ValueError:
                    v.errors.append("execution_package_ref.path escapes the artifact directory")
                else:
                    if not candidate.is_file():
                        v.errors.append("execution_package_ref.path does not exist")
                    elif sha256_file(candidate) != execution_ref.get("sha256"):
                        v.errors.append("execution_package_ref.sha256 does not match")
                    else:
                        try:
                            execution_doc = json.loads(candidate.read_text(encoding="utf-8-sig"))
                            execution_tasks = execution_doc.get("selected_strategy", {}).get("图片任务")
                            validate_selected_execution_delivery(candidate, v)
                        except (json.JSONDecodeError, AttributeError):
                            v.errors.append("execution_package_ref.path is not a valid selected execution package")
        v.require(nonempty_list(data.get("requested_scope")), "requested_scope must list the assets explicitly requested for production")
        validate_production_authorization(data.get("production_authorization_ref"), artifact_path, data, execution_ref, v)
    v.require(nonempty_string(approval.get("selling_point_approval_evidence")), "S4 selling-point approval evidence must not be empty")
    v.require(nonempty_string(approval.get("strategy_approval_evidence")), "S4 strategy approval evidence must not be empty")
    strategy_id = data.get("approved_strategy_id")
    v.require(strategy_id in {"A", "B", "C"}, "approved_strategy_id must be A, B, or C")
    v.require(strategy_id == approval.get("approved_strategy_id"), "approved_strategy_id must match approval_snapshot")
    identity_lock = data.get("product_identity_lock")
    assets = data.get("assets")
    v.require(isinstance(assets, list) and len(assets) == config.get("image_count"), "S4 assets must match task_config.image_count")
    if not isinstance(assets, list):
        return
    ids: list[str] = []
    all_generated = True
    for index, asset in enumerate(assets):
        path = f"$.assets[{index}]"
        validate_image_task(asset, path, v, identity_lock)
        v.required_keys(asset, ["输出路径", "生成状态", "纯图检查", "产品保真检查", "场景适配检查"], path)
        if data.get("schema_version") == 3:
            v.required_keys(asset, ["attempt_count", "max_attempts", "last_error", "retry_decision"], path)
        if not isinstance(asset, dict):
            all_generated = False
            continue
        ids.append(str(asset.get("资产ID", "")))
        status = asset.get("生成状态")
        v.require(status in {"GENERATED", "FAILED", "PENDING"}, f"{path}.生成状态 is unsupported")
        if data.get("schema_version") == 3:
            attempts = asset.get("attempt_count")
            maximum = asset.get("max_attempts")
            v.require(isinstance(attempts, int) and attempts >= 0, f"{path}.attempt_count must be nonnegative")
            v.require(isinstance(maximum, int) and 1 <= maximum <= 5, f"{path}.max_attempts must be 1-5")
            v.require(asset.get("retry_decision") in {"PENDING", "RETRY", "STOP_LIMIT_REACHED", "COMPLETE"}, f"{path}.retry_decision is unsupported")
            if maximum != 3:
                v.require(nonempty_string(data.get("retry_override_evidence")), f"{path}.max_attempts differs from default 3 without retry_override_evidence")
            if isinstance(attempts, int) and isinstance(maximum, int):
                v.require(attempts <= maximum, f"{path}.attempt_count cannot exceed max_attempts")
                if attempts >= maximum and status != "GENERATED":
                    v.require(status == "FAILED" and asset.get("retry_decision") == "STOP_LIMIT_REACHED", f"{path} must stop after max_attempts")
        validate_check(asset.get("纯图检查"), f"{path}.纯图检查", v)
        validate_fidelity_check(asset.get("产品保真检查"), f"{path}.产品保真检查", v, generated=status == "GENERATED")
        validate_check(asset.get("场景适配检查"), f"{path}.场景适配检查", v)
        if status == "GENERATED":
            output = asset.get("输出路径")
            v.require(nonempty_string(output), f"{path}.输出路径 must not be empty for a generated asset")
            if nonempty_string(output) and artifact_path is not None:
                output_path = Path(output)
                if not output_path.is_absolute():
                    output_path = artifact_path.parent / output_path
                v.require(output_path.is_file(), f"{path}.输出路径 does not exist: {output_path}")
            for check_name in ("纯图检查", "场景适配检查"):
                check = asset.get(check_name)
                v.require(isinstance(check, dict) and check.get("status") == "PASS", f"{path}.{check_name}.status must be PASS for a generated asset")
        elif status == "FAILED":
            all_generated = False
            v.require(nonempty_string(asset.get("错误信息")), f"{path}.错误信息 is required for a failed asset")
            if data.get("schema_version") == 3:
                v.require(nonempty_string(asset.get("last_error")), f"{path}.last_error is required for a failed asset")
        else:
            all_generated = False
    v.require(len(ids) == len(set(ids)) == config.get("image_count"), "S4 asset IDs must be unique")
    if data.get("schema_version") == 3:
        requested = data.get("requested_scope") if isinstance(data.get("requested_scope"), list) else []
        v.require(len(requested) == len(set(requested)), "requested_scope asset IDs must be unique")
        v.require(set(requested) <= set(ids), "requested_scope contains unknown asset IDs")
        if isinstance(execution_tasks, list):
            expected_ids = [task.get("资产ID") for task in execution_tasks if isinstance(task, dict)]
            v.require(ids == expected_ids, "S4 asset IDs must exactly match selected execution tasks")
            by_id = {task.get("资产ID"): task for task in execution_tasks if isinstance(task, dict)}
            for asset in assets:
                if isinstance(asset, dict) and asset.get("资产ID") in by_id:
                    source_task = by_id[asset.get("资产ID")]
                    for key in IMAGE_TASK_FIELDS + ["关联卖点ID", "卡位"]:
                        v.require(json_key(asset.get(key)) == json_key(source_task.get(key)), f"S4 asset {asset.get('资产ID')} field {key} differs from selected execution")
    audit_status = data.get("audit_result", {}).get("status") if isinstance(data.get("audit_result"), dict) else None
    if all_generated:
        validate_audit(data.get("audit_result"), v, require_pass=True)
    else:
        v.require(audit_status in {"PENDING", "BLOCKED"}, "incomplete S4 manifest audit status must be PENDING or BLOCKED")


def validate_data(data: Any, artifact_path: Path | None = None) -> list[str]:
    v = Validation()
    if not isinstance(data, dict):
        return ["top-level JSON must be an object"]
    data, reference_errors = resolve_artifact_refs(data, artifact_path)
    v.errors.extend(reference_errors)
    if data.get("artifact_type") == "PRODUCT_IDENTITY_LOCK":
        v.required_keys(data, ["schema_version", "artifact_type", "workflow_id", "product_fingerprint", "product_identity_lock"], "$")
        v.require(data.get("schema_version") in {2, 3}, "schema_version must be 2 or 3")
        if data.get("schema_version") == 3:
            v.required_keys(data, ["skill_version", "workflow_contract_version", "fingerprints"], "$")
            v.require(data.get("skill_version") == SKILL_VERSION, f"skill_version must be {SKILL_VERSION}")
            v.require(data.get("workflow_contract_version") == 3, "workflow_contract_version must be 3")
        v.require(nonempty_string(data.get("workflow_id")), "workflow_id must not be empty")
        v.require(nonempty_string(data.get("product_fingerprint")), "product_fingerprint must not be empty")
        validate_product_identity_lock(data.get("product_identity_lock"), "$.product_identity_lock", v)
        return v.errors
    if data.get("artifact_type") == "COMPETITOR_RESEARCH":
        v.required_keys(data, ["schema_version", "skill_version", "workflow_contract_version", "workflow_id", "product_fingerprint", "fingerprints", "artifact_type", "competitor_research"], "$")
        v.require(data.get("schema_version") == 3, "competitor research schema_version must be 3")
        v.require(data.get("skill_version") == SKILL_VERSION, f"skill_version must be {SKILL_VERSION}")
        v.require(data.get("workflow_contract_version") == 3, "workflow_contract_version must be 3")
        fingerprints = data.get("fingerprints")
        v.require(isinstance(fingerprints, dict), "fingerprints must be an object")
        if isinstance(fingerprints, dict):
            for key in FINGERPRINT_KEYS:
                v.require(nonempty_string(fingerprints.get(key)), f"fingerprints.{key} must not be empty")
            v.require(data.get("product_fingerprint") == fingerprints.get("product"), "product_fingerprint must equal fingerprints.product")
        validate_research(data.get("competitor_research"), v, 3)
        return v.errors
    config, approval = validate_common(data, v)
    stage = data.get("workflow_stage")
    if stage == "S1_COMPETITOR_RESEARCH_BLOCKED":
        validate_blocked(data, approval, v)
        validate_audit(data.get("audit_result"), v, require_pass=False)
    elif stage == "S2_PRODUCT_SELLING_POINT_REVIEW":
        validate_review(data, approval, v)
        validate_audit(data.get("audit_result"), v, require_pass=False)
    elif stage == "S3_STRATEGY_AND_FULL_DELIVERY":
        validate_strategy(data, config, approval, v)
    elif stage == "S3_STRATEGY_REVIEW":
        validate_strategy_review(data, config, approval, v)
    elif stage == "S3_SELECTED_STRATEGY_EXECUTION":
        validate_selected_execution(data, config, approval, artifact_path, v)
    elif stage == "S4_IMAGE_PRODUCTION":
        validate_image_manifest(data, config, approval, artifact_path, v)
    return v.errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.json_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.json_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 2
    errors = validate_data(data, args.json_path.resolve())
    if errors:
        print(f"FAIL: {len(errors)} validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {data.get('workflow_stage')} schema-v{data.get('schema_version')} artifact is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
