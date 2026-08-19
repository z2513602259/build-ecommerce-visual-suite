---
name: build-ecommerce-visual-suite
description: Build reusable cross-brand and cross-product ecommerce visual suites from product files and images. Use for 电商套图、电商详情页、主图、促销海报、竞品调研、本品卖点提炼与验收、A/B/C视觉企划、完整文案、纯图生图任务, or final ecommerce image production. Supports detail pages, main images, and promotional posters only.
---

# Build Ecommerce Visual Suite

Build ecommerce visual work for one current product without carrying facts from any earlier product. Keep the executable workflow in this Skill; treat historical prompt files as reference only.

## Mandatory workflow

Create new artifacts with schema v3 and Skill version `3.0.0`. Legacy v2 artifacts are read-only compatible but must be migrated or regenerated before further execution. Never infer approval from silence, explanation, revision requests, or ordinary follow-up.

1. **S1 — identify, route, fingerprint, and research**
   - Inventory authoritative sources, classify every image, choose one visual mode, build the current-product identity lock, and research matching or comparable products.
   - Write `research.json`, run `complete_stage.py s1`, and only after its PASS receipt deliver the research summary and enter S2.
   - Read [routing.md](references/routing.md), [fingerprints.md](references/fingerprints.md), [identity-lock.md](references/fidelity/identity-lock.md), [research.md](references/research.md), the relevant part of [strategy-matrices.md](references/strategy-matrices.md), [common contract](references/contracts/common.md), and [S1 contract](references/contracts/s1-research.md).
2. **S2 — derive and review this product's selling points**
   - Use current-product evidence for truth and research evidence for relevance. Output only the research summary and selling-point review, then stop for explicit approval.
   - After explicit approval, record the approval in `state.json` and run `complete_stage.py s2`; only its PASS receipt opens S3A.
   - Read [selling-points.md](references/selling-points.md), [ecommerce-copy.md](references/ecommerce-copy.md), [copy-quality.md](references/copy-quality.md), the matching section of [category-copy-playbooks.md](references/category-copy-playbooks.md), [common contract](references/contracts/common.md), and [S2 contract](references/contracts/s2-selling-points.md).
3. **S3A — compare A/B/C and approve one strategy**
   - Start only after `complete_stage.py s2` receipts the approved frozen selling-point set. Produce A/B/C, complete final consumer copy, and lightweight image briefs. Do not write 51 execution prompts for three unselected options.
   - Keep all options `电商转化型`; titles and subtitles are at most 10 visible characters. `说明文案` is publishable fact-plus-benefit copy. Evidence provenance stays only in `对应的真实产品依据`.
   - This is a document-delivery stage, never a chat-summary stage. Write `strategy-package.json`, run `complete_stage.py s3a`, and only after its PASS receipt deliver the generated `strategy-handoff.md` content with its actual clickable links. Do not ask for A/B/C selection, call a three-row table a strategy, create a hand-written execution file, or advance `state.json` until this succeeds. Stop for explicit A/B/C selection.
   - Read [task-profiles.md](references/task-profiles.md), [ecommerce-copy.md](references/ecommerce-copy.md), [copy-quality.md](references/copy-quality.md), the matching section of [category-copy-playbooks.md](references/category-copy-playbooks.md), [scene planning](references/scene/planning.md), [human-review.md](references/human-review.md), [common contract](references/contracts/common.md), [S3A contract](references/contracts/s3-strategy-review.md), and [detail-page.md](references/detail-page.md) only for detail pages.
4. **S3B — expand only the selected strategy**
   - After explicit A/B/C selection, preserve the approved strategy and copy unchanged and expand only its briefs into complete executable image tasks. No second strategy approval is needed unless the expansion changes approved content.
   - Bind every task to current-product references and choose one honest scene mode. `complete_stage.py s3b` accepts only a receipted S3A state; run it and then return the generated `selected-strategy-handoff.md` with actual clickable links. A manually written execution Markdown file is not an S3B artifact. Only then wait for an explicit image-production request.
   - Read [task binding](references/fidelity/task-binding.md), [scene planning](references/scene/planning.md), [audit-and-compliance.md](references/audit-and-compliance.md), [common contract](references/contracts/common.md), and [S3B contract](references/contracts/s3-selected-execution.md).
5. **S4 — produce images and post-layout manifest**
   - Generate independent pure images only after `authorize_production.py` records an explicit request naming the selected option and requested assets. “继续” and “确定” never authorize production. Use the selected execution package; never regenerate from an unselected option.
   - Enforce bounded retries and itemized pure-image, product-fidelity, and scene-fit checks. Stop at the retry limit and report the asset-specific blocker.
   - Read [fidelity output audit](references/fidelity/output-audit.md), [scene output audit](references/scene/output-audit.md), [audit-and-compliance.md](references/audit-and-compliance.md), [common contract](references/contracts/common.md), and [S4 contract](references/contracts/s4-production.md).

Read [workflow-state.md](references/workflow-state.md) only when starting, resuming, migrating, approving, or rolling back a workflow.

## Product-fact boundary

- Resolve brand, model, category, materials, dimensions, construction, finish, functions, ingredients, certifications, service terms, and performance claims from the current task only.
- Accept current user files, current product images, certificates, and explicit current-product statements as product-fact evidence.
- Use competitor information only for market priorities, page structure, expression patterns, concerns, and differentiation opportunities.
- Never use a competitor fact as proof for this product. Mark unsupported claims `未明确`, reject them, or request evidence.
- Treat each product workspace and `product_fingerprint` as an isolated case.

## Strategy precedence

Apply rules in this order:

1. verified current-product facts and legal/safety boundaries
2. explicit current user requirements and approved overrides
3. current live research evidence
4. task, platform, and category strategy baselines
5. creative preference

## Approval gates

- `COMPETITOR_RESEARCH_COMPLETE` requires a receipted S1 `research.json` with traceable evidence or a disclosed niche-research limitation.
- `SELLING_POINTS_APPROVED` requires a receipted S2 `selling-point-review.json` plus explicit user approval with the exact approved IDs, wording, order, sources, and approval excerpt.
- `STRATEGY_APPROVED` requires explicit selection of A, B, or C plus an approval excerpt.
- Selling-point changes return to S2. Product identity, category, core facts, target comparison set, or product-image changes return to S1. Strategy-only changes return to S3A. A faithful selected-option expansion proceeds through S3B without another strategy gate.
- Approval-evidence rules are authoritative in `workflow-state.md`; other documents defer to it on any conflict.

## Pure-image invariant

Generated images contain no added copy, gibberish, titles, subtitles, labels, prices, CTA, icons, dimensions, grids, card frames, split panels, or intentional text space. Preserve only authentic product markings required for fidelity. Generate one complete image per task; typeset the approved customer-facing copy, including `说明文案`, only during post-production.

## State and artifacts

Store product-specific artifacts under `ecommerce-visual-suite/` in the current product workspace, never inside this Skill:

- `state.json`
- `product-identity-lock.json`
- `research.json`
- `selling-point-review.json`
- `strategy-package.json`
- `strategy-review.md`, `strategy-A.md`, `strategy-B.md`, and `strategy-C.md`
- `strategy-handoff.md` and `review-package-manifest.json`
- `selected-strategy-package.json`, `selected-strategy-review.md`, and `selected-strategy-handoff.md`
- `image-manifest.json`
- generated pure-image files and post-layout manifests when requested

## Validation

All script paths below are relative to this Skill's directory. Resolve `<skill-dir>` to the absolute path of the folder containing this `SKILL.md` (injected when the Skill loads), never to the user's working directory. On Windows run scripts with `py -3`; on macOS/Linux use `python3`.

After writing a stage JSON, run the validator:

```powershell
py -3 "<skill-dir>\scripts\validate_output.py" <json-path>
```

Complete S1 or S2 as an evidence delivery operation. This validates the JSON, checks the prior gate and explicit approval evidence, writes a receipt into state, and only then permits the next gate:

```powershell
py -3 "<skill-dir>\scripts\complete_stage.py" s1 <research.json> <state.json>
py -3 "<skill-dir>\scripts\complete_stage.py" s2 <selling-point-review.json> <state.json>
```

Complete S3A or S3B as an atomic delivery operation. This validates JSON, renders Markdown, validates all required Markdown files and hashes, writes a receipt into state, and only then permits the next gate:

```powershell
py -3 "<skill-dir>\scripts\complete_stage.py" s3a <strategy-package.json> <state.json>
py -3 "<skill-dir>\scripts\complete_stage.py" s3b <selected-strategy-package.json> <state.json>
```

Before S4, record the user's exact, explicit production request and scope:

```powershell
py -3 "<skill-dir>\scripts\authorize_production.py" <selected-strategy-package.json> <state.json> --approval-text "开始生成方案B图片" --scope <asset-id> [...]
```

Validate `state.json` with `validate_state.py`. Build component hashes with `build_source_fingerprints.py`. Migrate v1/v2 state with `migrate_state.py` before resuming. Fix every validation error before presenting an artifact. A file that merely parses is not complete; a strategy without its verified Markdown delivery package is not complete either. Never write workflow-stage, approval, production-authorization, or execution files manually to bypass these commands.
