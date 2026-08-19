#!/usr/bin/env python3
"""Render validated S3A/S3B strategy artifacts as layered Markdown handoffs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from validate_output import resolve_artifact_refs, validate_data


def text(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, list):
        return "、".join(text(item) for item in value) if value else "—"
    if isinstance(value, dict):
        return "；".join(f"{key}：{text(item)}" for key, item in value.items()) if value else "—"
    return str(value).strip() or "—"


def cell(value: Any) -> str:
    return text(value).replace("|", "\\|").replace("\r", " ").replace("\n", "<br>")


def visible_char_count(value: Any) -> int:
    return sum(1 for char in text(value) if not char.isspace())


def sources(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "—"
    rendered = []
    for source in value:
        if isinstance(source, dict):
            source_id = text(source.get("source_id"))
            location = text(source.get("location"))
            claim = text(source.get("claim"))
            rendered.append(f"{source_id}（{location}）：{claim}")
        else:
            rendered.append(text(source))
    return "；".join(rendered)


def markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    result = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    result.extend("| " + " | ".join(cell(item) for item in row) + " |" for row in rows)
    return result


def render_project_summary(data: dict[str, Any], lines: list[str]) -> None:
    config = data.get("task_config", {})
    approval = data.get("approval_snapshot", {})
    lines.extend(
        markdown_table(
            ["项目项", "当前内容"],
            [
                ["任务类型", data.get("task_profile")],
                ["目标平台", config.get("target_platform")],
                ["视觉模式", data.get("visual_mode")],
                ["风格方向", data.get("style_direction")],
                ["最终屏数", config.get("screen_count")],
                ["独立纯图任务数", config.get("image_count")],
                ["第2屏卖点卡数", config.get("screen2_card_count")],
                ["输出比例", config.get("output_ratios")],
                ["卖点审核", "已通过" if approval.get("selling_points_approved") else "未通过"],
                ["方案审核", "等待选择A/B/C" if not approval.get("strategy_approved") else f"已选择{approval.get('approved_strategy_id')}"],
            ],
        )
    )
    lines.extend(["", "### 产品信息", ""])
    product = data.get("product_identity", {})
    if isinstance(product, dict) and product:
        lines.extend(markdown_table(["字段", "内容"], [[key, value] for key, value in product.items()]))
    else:
        lines.append("—")


def render_approved_points(data: dict[str, Any], lines: list[str]) -> None:
    lines.extend(["", "## 已审核通过的本品卖点", ""])
    points = data.get("approval_snapshot", {}).get("approved_selling_points", [])
    rows = []
    for point in points if isinstance(points, list) else []:
        if not isinstance(point, dict):
            continue
        rows.append(
            [
                point.get("卖点ID"),
                point.get("类别"),
                point.get("具体产品事实"),
                point.get("可转化利益"),
                sources(point.get("本品事实来源")),
            ]
        )
    lines.extend(markdown_table(["卖点ID", "类别", "具体产品事实", "利益表达", "本品依据"], rows))


def render_identity_lock(data: dict[str, Any], lines: list[str]) -> None:
    lock = data.get("product_identity_lock", {})
    lines.extend(["", "## 产品视觉身份锁", ""])
    if not isinstance(lock, dict) or not lock:
        lines.append("—")
        return
    lines.extend(
        markdown_table(
            ["锁定项", "内容"],
            [
                ["锁定ID", lock.get("锁定ID")],
                ["锁定状态", lock.get("锁定状态")],
                ["主参考图ID", lock.get("主参考图ID")],
                ["允许变化", lock.get("允许变化")],
                ["条件变化", lock.get("条件变化")],
                ["禁止推断", lock.get("禁止推断")],
                ["未确认项", lock.get("未确认项")],
            ],
        )
    )
    lines.extend(["", "### 角度参考", ""])
    reference_rows = []
    for reference in lock.get("角度参考", []) if isinstance(lock.get("角度参考"), list) else []:
        if not isinstance(reference, dict):
            continue
        reference_rows.append(
            [
                reference.get("参考图ID"),
                reference.get("视角"),
                reference.get("角色"),
                reference.get("文件路径"),
                reference.get("可证明特征ID"),
            ]
        )
    lines.extend(markdown_table(["参考图ID", "视角", "角色", "文件路径", "可证明特征ID"], reference_rows))
    lines.extend(["", "### 不可变特征", ""])
    feature_rows = []
    for feature in lock.get("不可变特征", []) if isinstance(lock.get("不可变特征"), list) else []:
        if not isinstance(feature, dict):
            continue
        feature_rows.append(
            [
                feature.get("特征ID"),
                feature.get("类别"),
                feature.get("特征描述"),
                feature.get("重要级别"),
                sources(feature.get("本品事实来源")),
            ]
        )
    lines.extend(markdown_table(["特征ID", "类别", "特征描述", "重要级别", "本品依据"], feature_rows))


def render_comparison(options: list[dict[str, Any]], lines: list[str]) -> None:
    lines.extend(["", "## A/B/C方案快速对比", ""])
    rows = []
    for option in options:
        rows.append(
            [
                option.get("方案ID"),
                option.get("方案定位"),
                option.get("风格名称"),
                option.get("视觉世界观"),
                option.get("色彩策略"),
                option.get("光影策略"),
                option.get("版式语言"),
                option.get("文案模式"),
                option.get("文案语调指引"),
                option.get("期望图片数量"),
            ]
        )
    lines.extend(markdown_table(["方案", "定位", "风格", "视觉世界观", "色彩", "光影", "版式", "文案模式", "文案语调", "纯图数"], rows))


def render_option_links(options: list[dict[str, Any]], lines: list[str]) -> None:
    lines.extend(["", "## 详细方案入口", ""])
    for option in options:
        option_id = text(option.get("方案ID"))
        lines.append(f"- [方案{option_id}审核书](strategy-{option_id}.md)：完整文案、卖点卡片和逐图画面简报")
    lines.extend(["", "> S3A只用于选择方案；完整提示词和保真绑定将在选定方案后仅展开一次。", ""])


def matching_tasks(option: dict[str, Any], unit_id: str) -> list[dict[str, Any]]:
    tasks = option.get("图片简报", option.get("图片任务", []))
    if not isinstance(tasks, list):
        return []
    return [task for task in tasks if isinstance(task, dict) and text(task.get("关联单元")) == unit_id]


def copy_quality_by_unit(option: dict[str, Any]) -> dict[str, dict[str, Any]]:
    quality = option.get("文案质检", {})
    checks = quality.get("单元检查", []) if isinstance(quality, dict) else []
    return {
        text(item.get("单元ID")): item
        for item in checks
        if isinstance(item, dict) and text(item.get("单元ID"))
    }


def render_purchase_narrative(option: dict[str, Any], lines: list[str]) -> None:
    narrative = option.get("购买叙事", {})
    if not isinstance(narrative, dict):
        return
    lines.extend(["", "### 这套方案卖什么", ""])
    lines.extend(markdown_table(
        ["项目", "内容"],
        [
            ["核心购买主张", narrative.get("核心购买主张")],
            ["首屏承诺", narrative.get("首屏承诺")],
            ["主要购买顾虑", "；".join(text(item) for item in narrative.get("主要购买顾虑", []) if text(item))],
            ["文案气质", narrative.get("文案气质")],
        ],
    ))
    sequence = narrative.get("决策递进", [])
    if isinstance(sequence, list):
        lines.extend(["", "**12屏决策递进：** " + " → ".join(text(item) for item in sequence if text(item)), ""])


def render_copy_quality_summary(option: dict[str, Any], lines: list[str]) -> None:
    quality = option.get("文案质检", {})
    if not isinstance(quality, dict):
        return
    lines.extend(["", "### 文案质检结论", ""])
    lines.extend(markdown_table(
        ["检查项", "结果"],
        [
            ["状态", quality.get("状态")],
            ["本方案核心购买理由", quality.get("本方案核心购买理由")],
            ["泛化表达", "无" if not quality.get("泛化表达") else "；".join(text(item) for item in quality.get("泛化表达", []))],
            ["重复风险", "无" if not quality.get("重复风险") else "；".join(text(item) for item in quality.get("重复风险", []))],
        ],
    ))


def render_option_overview(option: dict[str, Any], lines: list[str]) -> None:
    option_id = text(option.get("方案ID"))
    lines.extend(["", f"## 方案 {option_id}｜{text(option.get('风格名称'))}", ""])
    lines.extend(
        markdown_table(
            ["策略项", "内容"],
            [
                ["方案定位", option.get("方案定位")],
                ["视觉世界观", option.get("视觉世界观")],
                ["色彩策略", option.get("色彩策略")],
                ["光影策略", option.get("光影策略")],
                ["版式语言", option.get("版式语言")],
                ["文案语调", option.get("文案语调指引")],
            ],
        )
    )
    render_purchase_narrative(option, lines)
    render_copy_quality_summary(option, lines)
    lines.extend(["", "### 文案与画面方向", ""])
    copy_data = option.get("文案成稿", {})
    if not isinstance(copy_data, dict):
        lines.append("—")
        return

    units: list[tuple[str, dict[str, Any]]] = []
    screens = copy_data.get("屏幕文案")
    if isinstance(screens, dict):
        units = [(name, value) for name, value in screens.items() if isinstance(value, dict)]
    else:
        content_units = copy_data.get("内容单元")
        if isinstance(content_units, list):
            units = [
                (text(value.get("单元ID")), value)
                for value in content_units
                if isinstance(value, dict)
            ]

    quality_by_unit = copy_quality_by_unit(option)
    for unit_id, unit in units:
        tasks = matching_tasks(option, unit_id)
        asset_ids = [task.get("资产ID") for task in tasks]
        scene_modes = list(
            dict.fromkeys(
                text(task.get("场景模式") or task.get("场景设计", {}).get("场景模式"))
                for task in tasks
                if isinstance(task.get("场景设计"), dict)
            )
        )
        directions = list(dict.fromkeys(text(task.get("镜头重点")) for task in tasks))
        lines.extend(
            [
                f"#### {unit_id}｜{text(unit.get('页面职责'))}",
                "",
                f"- **主标题（{visible_char_count(unit.get('主标题'))}/10）：** {text(unit.get('主标题'))}",
                f"- **副标题（{visible_char_count(unit.get('副标题'))}/10）：** {text(unit.get('副标题'))}",
                f"- **卖点短句（{visible_char_count(unit.get('卖点短句'))}/22）：** {text(unit.get('卖点短句'))}",
                f"- **说明文案（{visible_char_count(unit.get('说明文案'))}/42）：** {text(unit.get('说明文案'))}",
                f"- **CTA或承接语（{visible_char_count(unit.get('CTA或承接语'))}/14）：** {text(unit.get('CTA或承接语'))}",
                f"- **本屏解决的消费者问题：** {text(quality_by_unit.get(unit_id, {}).get('消费者决策问题'))}",
                f"- **画面类型：** {text(scene_modes)}",
                f"- **画面方向：** {text(directions)}",
                f"- **对应资产：** {text(asset_ids)}",
            ]
        )
        if unit_id == "第2屏":
            render_screen2(unit, lines)
        lines.append("")


def render_screen2(screen: dict[str, Any], lines: list[str]) -> None:
    points = screen.get("卖点总览", [])
    if not isinstance(points, list) or not points:
        return
    lines.extend(["", "#### 第2屏卖点卡片", ""])
    rows = []
    for point in points:
        if not isinstance(point, dict):
            continue
        copy_block = point.get("卖点三行文案", {})
        asset = point.get("对应纯图资产", {})
        rows.append(
            [
                point.get("卖点ID"),
                point.get("来源卖点ID"),
                copy_block.get("类别") if isinstance(copy_block, dict) else "",
                copy_block.get("具体特征") if isinstance(copy_block, dict) else "",
                copy_block.get("简短利益") if isinstance(copy_block, dict) else "",
                asset.get("卡位") if isinstance(asset, dict) else "",
                asset.get("生成比例") if isinstance(asset, dict) else "",
                asset.get("资产ID") if isinstance(asset, dict) else "",
                sources(point.get("对应的真实产品依据")),
            ]
        )
    lines.extend(markdown_table(["卡片", "来源卖点", "类别", "具体特征", "简短利益", "卡位", "比例", "资产", "真实依据"], rows))


def render_copy(option: dict[str, Any], lines: list[str]) -> None:
    lines.extend(["", "### 完整文案", ""])
    copy_data = option.get("文案成稿", {})
    if not isinstance(copy_data, dict):
        lines.append("—")
        return
    quality_by_unit = copy_quality_by_unit(option)
    screens = copy_data.get("屏幕文案")
    if isinstance(screens, dict):
        for screen_name, screen in screens.items():
            if not isinstance(screen, dict):
                continue
            lines.extend(
                [
                    f"#### {screen_name}｜{text(screen.get('页面职责'))}",
                    "",
                    f"- **主标题（购买结论，{visible_char_count(screen.get('主标题'))}/10）：** {text(screen.get('主标题'))}",
                    f"- **副标题（事实/利益补充，{visible_char_count(screen.get('副标题'))}/10）：** {text(screen.get('副标题'))}",
                    f"- **卖点短句（消费者结果，{visible_char_count(screen.get('卖点短句'))}/22）：** {text(screen.get('卖点短句'))}",
                    f"- **说明文案（事实＋利益，{visible_char_count(screen.get('说明文案'))}/42）：** {text(screen.get('说明文案'))}",
                    f"- **CTA或承接语（决策提示，{visible_char_count(screen.get('CTA或承接语'))}/14）：** {text(screen.get('CTA或承接语'))}",
                    f"- **本屏解决的消费者问题：** {text(quality_by_unit.get(screen_name, {}).get('消费者决策问题'))}",
                    f"- **真实产品依据：** {sources(screen.get('对应的真实产品依据'))}",
                ]
            )
            if screen_name == "第2屏":
                render_screen2(screen, lines)
            lines.append("")
        return

    units = copy_data.get("内容单元")
    if isinstance(units, list):
        for unit in units:
            if not isinstance(unit, dict):
                continue
            lines.extend(
                [
                    f"#### {text(unit.get('单元ID'))}｜{text(unit.get('页面职责'))}",
                    "",
                    f"- **主标题（购买结论，{visible_char_count(unit.get('主标题'))}/10）：** {text(unit.get('主标题'))}",
                    f"- **副标题（事实/利益补充，{visible_char_count(unit.get('副标题'))}/10）：** {text(unit.get('副标题'))}",
                    f"- **卖点短句（消费者结果，{visible_char_count(unit.get('卖点短句'))}/22）：** {text(unit.get('卖点短句'))}",
                    f"- **说明文案（事实＋利益，{visible_char_count(unit.get('说明文案'))}/42）：** {text(unit.get('说明文案'))}",
                    f"- **CTA或承接语（决策提示，{visible_char_count(unit.get('CTA或承接语'))}/14）：** {text(unit.get('CTA或承接语'))}",
                    f"- **本屏解决的消费者问题：** {text(quality_by_unit.get(text(unit.get('单元ID')), {}).get('消费者决策问题'))}",
                    f"- **真实产品依据：** {sources(unit.get('对应的真实产品依据'))}",
                    "",
                ]
            )


def render_image_tasks(option: dict[str, Any], lines: list[str]) -> None:
    lines.extend(["", "### 独立纯图任务", ""])
    tasks = option.get("图片任务", [])
    rows = []
    for task in tasks if isinstance(tasks, list) else []:
        if not isinstance(task, dict):
            continue
        rows.append(
            [
                task.get("资产ID"),
                task.get("关联单元"),
                task.get("关联卖点ID"),
                task.get("生成比例"),
                task.get("最终裁切比例"),
                task.get("保真执行", {}).get("生成方式") if isinstance(task.get("保真执行"), dict) else "",
                task.get("保真执行", {}).get("主参考图ID") if isinstance(task.get("保真执行"), dict) else "",
                task.get("场景设计", {}).get("场景模式") if isinstance(task.get("场景设计"), dict) else "",
                task.get("场景设计", {}).get("目标空间") if isinstance(task.get("场景设计"), dict) else "",
                task.get("镜头重点"),
                task.get("产品展示角度"),
            ]
        )
    lines.extend(markdown_table(["资产ID", "关联页面/单元", "关联卖点", "生成比例", "裁切比例", "生成方式", "主参考图", "场景模式", "目标空间", "镜头重点", "产品角度"], rows))
    lines.extend(["", "#### 图片任务完整说明", ""])
    for task in tasks if isinstance(tasks, list) else []:
        if not isinstance(task, dict):
            continue
        prompt = text(task.get("独立生图提示")).replace("```", "''' ")
        prohibited = task.get("禁止项", [])
        fidelity = task.get("保真执行", {}) if isinstance(task.get("保真执行"), dict) else {}
        scene = task.get("场景设计", {}) if isinstance(task.get("场景设计"), dict) else {}
        prohibited_lines = "\n".join(f"  - {text(item)}" for item in prohibited) if isinstance(prohibited, list) else f"  - {text(prohibited)}"
        lines.extend(
            [
                "<details>",
                f"<summary><strong>{text(task.get('资产ID'))}</strong> · {text(task.get('关联单元'))} · {text(task.get('生成比例'))}</summary>",
                "",
                f"- **平台安全区：** {text(task.get('平台安全区'))}",
                f"- **镜头重点：** {text(task.get('镜头重点'))}",
                f"- **产品展示角度：** {text(task.get('产品展示角度'))}",
                f"- **生成方式：** {text(fidelity.get('生成方式'))}",
                f"- **主参考图ID：** {text(fidelity.get('主参考图ID'))}",
                f"- **辅助参考图ID：** {text(fidelity.get('辅助参考图ID'))}",
                f"- **锁定特征ID：** {text(fidelity.get('锁定特征ID'))}",
                f"- **允许变化：** {text(fidelity.get('允许变化'))}",
                f"- **禁止变化：** {text(fidelity.get('禁止变化'))}",
                f"- **角度匹配说明：** {text(fidelity.get('角度匹配说明'))}",
                f"- **结构推断风险：** {text(fidelity.get('结构推断风险'))}",
                f"- **场景模式：** {text(scene.get('场景模式'))}",
                f"- **模式理由：** {text(scene.get('模式理由'))}",
                f"- **目标空间：** {text(scene.get('目标空间'))}",
                f"- **摆放与使用关系：** {text(scene.get('摆放与使用关系'))}",
                f"- **空间锚点：** {text(scene.get('空间锚点'))}",
                f"- **尺度参照：** {text(scene.get('尺度参照'))}",
                f"- **辅助元素：** {text(scene.get('辅助元素'))}",
                f"- **协调逻辑：** {text(scene.get('协调逻辑'))}",
                f"- **场景事实边界：** {text(scene.get('场景事实边界'))}",
                f"- **所用原图参考：** {text(task.get('所用原图参考'))}",
                f"- **真实产品依据：** {sources(task.get('对应的真实产品依据'))}",
                "- **完整生图提示：**",
                "",
                "```text",
                prompt,
                "```",
                "",
                "- **禁止项：**",
                prohibited_lines,
                "",
                "</details>",
                "",
            ]
        )


def render_image_briefs(option: dict[str, Any], lines: list[str]) -> None:
    lines.extend(["", "### 逐图画面简报", ""])
    briefs = option.get("图片简报", [])
    rows = []
    for brief in briefs if isinstance(briefs, list) else []:
        if not isinstance(brief, dict):
            continue
        rows.append(
            [
                brief.get("资产ID"),
                brief.get("关联单元"),
                brief.get("关联卖点ID"),
                brief.get("生成比例"),
                brief.get("最终裁切比例"),
                brief.get("场景模式"),
                brief.get("证明目标"),
                brief.get("镜头重点"),
                brief.get("产品展示角度"),
                brief.get("目标空间"),
            ]
        )
    lines.extend(markdown_table(["资产", "页面/单元", "卖点", "生成比例", "裁切比例", "画面类型", "证明目标", "镜头重点", "产品角度", "目标空间"], rows))


def render_option_review(data: dict[str, Any], option: dict[str, Any], source_name: str = "strategy-package.json") -> str:
    option_id = text(option.get("方案ID"))
    lines = [
        f"# 方案{option_id}审核书",
        "",
        "> **当前门控：等待你明确选择 A / B / C，尚未展开执行提示，也未允许生成图片。**",
        "",
        f"- 机器源文件：`{source_name}`",
        f"- 工作流ID：`{text(data.get('workflow_id'))}`",
        "",
    ]
    render_approved_points(data, lines)
    lines.extend(["", f"## 方案 {option_id}｜{text(option.get('风格名称'))}", ""])
    lines.extend(
        markdown_table(
            ["策略项", "内容"],
            [
                ["方案定位", option.get("方案定位")],
                ["转化重点", option.get("转化重点")],
                ["文案语调", option.get("文案语调指引")],
                ["视觉世界观", option.get("视觉世界观")],
                ["色彩策略", option.get("色彩策略")],
                ["光影策略", option.get("光影策略")],
                ["核心材质库", option.get("核心材质库")],
                ["版式语言", option.get("版式语言")],
                ["设计风格标签", option.get("设计风格标签")],
                ["纯图约束", option.get("纯图生成约束")],
            ],
        )
    )
    render_purchase_narrative(option, lines)
    render_copy_quality_summary(option, lines)
    render_copy(option, lines)
    render_image_briefs(option, lines)
    audit = data.get("audit_result", {})
    lines.extend(["", "## 审核状态", "", f"- **最终审核状态：** {text(audit.get('status') if isinstance(audit, dict) else '')}"])
    lines.extend(
        [
            "",
            "## 请你这样回复",
            "",
            f"- 直接选择：`选择方案{option_id}，按当前方案展开执行任务。`",
            f"- 局部修改：`修改方案{option_id}的第4屏：……；其他内容保留。`",
            "",
        ]
    )
    return "\n".join(lines)


def render_option(option: dict[str, Any], lines: list[str]) -> None:
    option_id = text(option.get("方案ID"))
    lines.extend(["", f"## 方案 {option_id}｜{text(option.get('风格名称'))}", ""])
    lines.extend(
        markdown_table(
            ["策略项", "内容"],
            [
                ["方案定位", option.get("方案定位")],
                ["目标平台", option.get("目标平台")],
                ["任务类型", option.get("任务类型")],
                ["期望图片数量", option.get("期望图片数量")],
                ["文案模式", option.get("文案模式")],
                ["文案语调", option.get("文案语调指引")],
                ["视觉世界观", option.get("视觉世界观")],
                ["色彩策略", option.get("色彩策略")],
                ["光影策略", option.get("光影策略")],
                ["核心材质库", option.get("核心材质库")],
                ["版式语言", option.get("版式语言")],
                ["设计风格标签", option.get("设计风格标签")],
                ["产品信息", option.get("产品信息")],
                ["产品参数", option.get("产品参数")],
                ["纯图生成约束", option.get("纯图生成约束")],
                ["下游执行注意事项", option.get("下游执行注意事项")],
            ],
        )
    )
    render_purchase_narrative(option, lines)
    render_copy_quality_summary(option, lines)
    render_copy(option, lines)
    render_image_tasks(option, lines)


def render_audit(data: dict[str, Any], lines: list[str]) -> None:
    audit = data.get("audit_result", {})
    lines.extend(["", "## 审核与红线检查", ""])
    lines.append(f"- **最终审核状态：** {text(audit.get('status') if isinstance(audit, dict) else '')}")
    perspectives = audit.get("perspectives", {}) if isinstance(audit, dict) else {}
    if isinstance(perspectives, dict):
        lines.extend(["", "### 四视角审核", ""])
        rows = []
        for name, result in perspectives.items():
            if isinstance(result, dict):
                rows.append([name, result.get("结论"), result.get("风险")])
        lines.extend(markdown_table(["审核视角", "结论", "风险"], rows))
    checks = audit.get("redline_checks", []) if isinstance(audit, dict) else []
    if isinstance(checks, list):
        lines.extend(["", "### R1–R12", ""])
        rows = []
        for check in checks:
            if isinstance(check, dict):
                rows.append([check.get("redline_id"), check.get("status"), check.get("findings"), check.get("corrections")])
        lines.extend(markdown_table(["红线", "状态", "发现", "修正"], rows))
    lines.extend(["", "### 修正记录", "", text(audit.get("correction_log") if isinstance(audit, dict) else "")])


def render_review(data: dict[str, Any], source_name: str = "strategy-package.json") -> str:
    options = [item for item in data.get("options", []) if isinstance(item, dict)]
    lines = [
        "# 电商视觉方案总览",
        "",
        "> **当前门控：等待你选择 A / B / C，尚未允许生成图片。**",
        "> 本文档由已校验的机器JSON自动生成。请先在这里比较三套方案；执行细节已拆分到独立方案书。",
        "",
        f"- 机器源文件：`{source_name}`",
        f"- 工作流ID：`{text(data.get('workflow_id'))}`",
        f"- 产品指纹：`{text(data.get('product_fingerprint'))}`",
        "",
        "## 项目概况",
        "",
    ]
    render_project_summary(data, lines)
    render_approved_points(data, lines)
    render_comparison(options, lines)
    render_option_links(options, lines)
    for option in options:
        render_option_overview(option, lines)
    audit = data.get("audit_result", {})
    lines.extend(["", "## 审核状态", "", f"- **最终审核状态：** {text(audit.get('status') if isinstance(audit, dict) else '')}"])
    lines.extend(
        [
            "",
            "## 请你这样回复",
            "",
            "- 直接选择：`选择方案A，按当前内容展开执行任务。`",
            "- 局部修改：`修改方案B的第4屏：……；其他内容保留。`",
            "- 重新组合：`以方案A为主，采用方案C的色彩和方案B的第8屏。`",
            "",
            "> 在你明确选择方案前，不会展开完整执行提示或生成图片。",
            "",
        ]
    )
    return "\n".join(lines)


def render_option_book(
    data: dict[str, Any], option: dict[str, Any], source_name: str = "strategy-package.json"
) -> str:
    option_id = text(option.get("方案ID"))
    lines = [
        f"# 方案{option_id}选定执行书",
        "",
        "> **当前门控：方案已选择并完成执行展开，等待你明确要求生成图片。**",
        "> 本文件包含选定方案的完整执行任务；尚未生成图片。",
        "",
        f"- 机器源文件：`{source_name}`",
        f"- 工作流ID：`{text(data.get('workflow_id'))}`",
        f"- 产品指纹：`{text(data.get('product_fingerprint'))}`",
        "",
        "## 项目概况",
        "",
    ]
    render_project_summary(data, lines)
    render_identity_lock(data, lines)
    render_approved_points(data, lines)
    render_option(option, lines)
    render_audit(data, lines)
    lines.extend(
        [
            "",
            "## 请你这样回复",
            "",
            f"- 开始生产：`按方案{option_id}当前执行书开始生成图片。`",
            f"- 局部修改：`修改方案{option_id}的第4屏执行任务：……；其他内容保留。`",
            "",
            "> 在你明确要求生产前，不会进入图片生成阶段。",
            "",
        ]
    )
    return "\n".join(lines)


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_strategy_handoff(data: dict[str, Any]) -> str:
    options = [item for item in data.get("options", []) if isinstance(item, dict)]
    lines = [
        "# A/B/C方案交付",
        "",
        "> 当前门控：等待选择方案，尚未展开完整执行提示，也未允许生图。",
        "",
    ]
    rows = [[item.get("方案ID"), item.get("方案定位"), item.get("转化重点"), item.get("风格名称"), item.get("色彩策略"), item.get("光影策略")] for item in options]
    lines.extend(markdown_table(["方案", "定位", "转化重点", "风格", "色彩", "光影"], rows))
    lines.extend(["", "## 阅读入口", "", "- [方案总览（推荐先看）](strategy-review.md)"])
    for option in options:
        option_id = text(option.get("方案ID"))
        lines.append(f"- [方案{option_id}审核书](strategy-{option_id}.md)")
    lines.extend(
        [
            "- [机器校验源（无需阅读）](strategy-package.json)",
            "",
            "## 回复方式",
            "",
            "- `选择方案A，按当前内容展开执行任务。`",
            "- `修改方案B的第4屏：……；其他内容保留。`",
            "- `以方案A为主，采用方案C的色彩和方案B的第8屏。`",
            "",
        ]
    )
    return "\n".join(lines)


def render_selected_handoff(data: dict[str, Any]) -> str:
    option_id = text(data.get("selected_strategy_id"))
    return "\n".join(
        [
            f"# 方案{option_id}执行展开完成",
            "",
            "> 当前门控：等待你明确要求生成图片。",
            "",
            f"> 一致性确认：执行书与已批准方案{option_id}的策略、文案、卖点与任务 ID 已通过机器校验，零差异。如发现任何不一致，请指出具体位置。",
            "",
            "- [选定方案执行书（推荐审核）](selected-strategy-review.md)",
            "- [机器校验源（无需阅读）](selected-strategy-package.json)",
            "",
            f"开始生产：`按方案{option_id}当前执行书开始生成图片。`",
            "",
        ]
    )


def write_package_manifest(path: Path, stage: str, workflow_id: Any, files: list[Path]) -> None:
    payload = {
        "schema_version": 3,
        "skill_version": "3.0.0",
        "workflow_stage": stage,
        "workflow_id": workflow_id,
        "files": [
            {"path": file.name, "sha256": file_sha256(file), "status": "GENERATED"}
            for file in files
            if file.is_file()
        ],
    }
    write_atomic(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("strategy_json", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.strategy_json.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.strategy_json}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 2
    errors = validate_data(data, args.strategy_json.resolve())
    if errors:
        print(f"ERROR: strategy JSON failed validation with {len(errors)} error(s)", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    hydrated, reference_errors = resolve_artifact_refs(data, args.strategy_json.resolve())
    if reference_errors:
        for error in reference_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    stage = hydrated.get("workflow_stage")
    if stage in {"S3_STRATEGY_REVIEW", "S3_STRATEGY_AND_FULL_DELIVERY"}:
        output = args.output or args.strategy_json.with_name("strategy-review.md")
        options = [item for item in hydrated.get("options", []) if isinstance(item, dict)]
        write_atomic(output, render_review(hydrated, args.strategy_json.name))
        detail_paths = []
        for option in options:
            option_id = text(option.get("方案ID"))
            detail_path = output.with_name(f"strategy-{option_id}.md")
            content = render_option_review(hydrated, option, args.strategy_json.name) if stage == "S3_STRATEGY_REVIEW" else render_option_book(hydrated, option, args.strategy_json.name)
            write_atomic(detail_path, content)
            detail_paths.append(detail_path)
        handoff_path = output.with_name("strategy-handoff.md")
        write_atomic(handoff_path, render_strategy_handoff(hydrated))
        files = [args.strategy_json, output, *detail_paths, handoff_path]
        manifest_path = output.with_name("review-package-manifest.json")
        write_package_manifest(manifest_path, stage, hydrated.get("workflow_id"), files)
        print(f"PASS: strategy review package written beside {args.strategy_json}")
    elif stage == "S3_SELECTED_STRATEGY_EXECUTION":
        output = args.output or args.strategy_json.with_name("selected-strategy-review.md")
        option = hydrated.get("selected_strategy")
        write_atomic(output, render_option_book(hydrated, option, args.strategy_json.name))
        handoff_path = output.with_name("selected-strategy-handoff.md")
        write_atomic(handoff_path, render_selected_handoff(hydrated))
        manifest_path = output.with_name("review-package-manifest.json")
        write_package_manifest(manifest_path, stage, hydrated.get("workflow_id"), [args.strategy_json, output, handoff_path])
        print(f"PASS: selected-strategy execution review written beside {args.strategy_json}")
    else:
        print("ERROR: readable strategy review can only be generated from S3A/S3B", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
