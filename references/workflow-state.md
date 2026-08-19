# Workflow state, migration, and gates

## Storage

Maintain `ecommerce-visual-suite/state.json` in the current product workspace. Product artifacts never belong in the Skill folder.

## State v3

```json
{
  "schema_version": 3,
  "skill_version": "3.0.0",
  "workflow_contract_version": 3,
  "workflow_id": "stable-workflow-id",
  "product_key": "brand-or-unconfirmed/model-or-folder",
  "product_fingerprint": "combined-product-fingerprint",
  "fingerprints": {
    "product_fact": "",
    "product_image": "",
    "style_reference": "",
    "task_config": "",
    "research": "",
    "product": ""
  },
  "product_identity_lock_id": "PIL-current-product",
  "product_identity_lock_status": "READY",
  "source_inventory": [],
  "current_stage": "S1_RESEARCH",
  "task_profile": "DETAIL_PAGE",
  "visual_mode": "FREE_FISSION_MODE",
  "task_config": {
    "target_platform": "未明确",
    "image_count": 17,
    "screen_count": 12,
    "screen_count_override": false,
    "screen2_card_count": 6,
    "screen2_card_count_override": false,
    "output_ratios": [],
    "platform_safe_area": "待调研确认"
  },
  "flags": {
    "COMPETITOR_RESEARCH_COMPLETE": false,
    "SELLING_POINTS_APPROVED": false,
    "STRATEGY_APPROVED": false,
    "EXECUTION_PACKAGE_READY": false
  },
  "approval_snapshot": {
    "selling_points_approved": false,
    "selling_point_approval_evidence": "",
    "approved_selling_points": [],
    "strategy_approved": false,
    "approved_strategy_id": "",
    "strategy_approval_evidence": ""
  },
  "delivery_receipts": {},
  "production_authorization": null,
  "updated_at": "YYYY-MM-DDTHH:mm:ss+08:00"
}
```

## Resume logic

1. Inventory current sources and calculate the current fingerprint.
2. Migrate v1 or v2 state before trusting it.
3. Compare component fingerprints and apply the rollback matrix in `fingerprints.md`.
4. Rebuild and validate `product-identity-lock.json`; require its source fingerprint and current product images to match.
5. Keep approvals only when the fingerprint and identity lock match and the corresponding explicit approval evidence exists.
6. If only non-factual files changed, record the change without invalidating approvals.
7. Present the resumed stage, task profile, visual mode, identity-lock status, approved overrides, and next gate.

## v1/v2 migration

Run:

```powershell
py -3 "<skill-dir>\scripts\migrate_state.py" <state.json> --fingerprints <fingerprints.json>
```

Resolve `<skill-dir>` to the absolute path of the folder containing `SKILL.md`, never the user's working directory.

The script creates a sibling `.v1-backup.json`, converts fields to schema v2, and preserves selling-point approval only when fingerprint and approval evidence match. Preserve strategy approval only when its own evidence exists; otherwise return to S3. Use `--dry-run` to inspect without writing.

## Transitions and rollback

Every transition runs through `complete_stage.py`, which writes the receipt that opens the next gate:

| From | Requirement | To |
|---|---|---|
| S1_RESEARCH | `complete_stage.py s1` receipts verified `research.json` with traceable evidence or a disclosed valid niche limitation | S2_PRODUCT_SELLING_POINT_REVIEW |
| S2_PRODUCT_SELLING_POINT_REVIEW | `complete_stage.py s2` receipts verified `selling-point-review.json` plus explicit approval evidence and frozen points | S3_STRATEGY_REVIEW |
| S3_STRATEGY_REVIEW | `complete_stage.py s3a` receipts the verified S3A Markdown package plus explicit selection of A/B/C | S3_SELECTED_STRATEGY_EXECUTION |
| S3_SELECTED_STRATEGY_EXECUTION | `complete_stage.py s3b` receipts the verified S3B Markdown package plus explicit production authorization | S4_IMAGE_PRODUCTION |

- Selling-point wording, membership, order, or Screen 2 count changes: clear both approvals and return to S2.
- Brand, model, category, core fact, target comparison set, product-image changes, or identity-lock changes: clear all flags and return to S1.
- Strategy-only changes: clear strategy approval and return to S3_STRATEGY_REVIEW.
- Pre-receipt v3 states (approvals recorded by hand before the s1/s2 scripts existed) recover with the `--backfill` mode. Run `complete_stage.py s2 <selling-point-review.json> <state.json> --backfill` first — it verifies the approval, receipts S2, and advances a state still sitting at `S2_PRODUCT_SELLING_POINT_REVIEW` into a valid `S3_STRATEGY_REVIEW`. Then run `complete_stage.py s1 <research.json> <state.json> --backfill` to receipt S1. Both receipts are required: S3A refuses states missing either the S1 or the S2 receipt, so skipping the s1 backfill blocks further execution.

**Approval-evidence rules in this section are the single source of truth.** Other documents restate them; on any conflict, this section wins.

Count only unambiguous approval such as `确认`, `通过`, `按这组继续`, or an equally explicit statement. Explanation, comparison, deletion, addition, or revision is not approval. Image production has the stricter separate requirement of an action statement naming the selected option and images, such as `开始生成方案B图片`.

## S4 production recovery

A failed asset stops at its retry limit and reports the asset-specific blocker. Recovery is an explicit, rule-driven path, not an ad-hoc decision:

1. The user corrects the input that caused the blocker (product image, constraint, or scene request).
2. Re-run `authorize_production.py` with the new explicit request; the scope may name only the failed or remaining assets.
3. Keep already-PASS assets and their manifest entries; retry only blocked assets.
4. A correction that changes product facts, the identity lock, or the selected strategy follows the rollback matrix above instead of this recovery path.
