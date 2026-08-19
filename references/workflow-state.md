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
py -3 "C:\Users\Administrator\.codex\skills\build-ecommerce-visual-suite\scripts\migrate_state.py" <state.json> --fingerprints <fingerprints.json>
```

The script creates a sibling `.v1-backup.json`, converts fields to schema v2, and preserves selling-point approval only when fingerprint and approval evidence match. Preserve strategy approval only when its own evidence exists; otherwise return to S3. Use `--dry-run` to inspect without writing.

## Transitions and rollback

| From | Requirement | To |
|---|---|---|
| S1_RESEARCH | Traceable research or disclosed valid niche limitation | S2_PRODUCT_SELLING_POINT_REVIEW |
| S2_PRODUCT_SELLING_POINT_REVIEW | Explicit approval of frozen selling points and optional count overrides | S3_STRATEGY_REVIEW |
| S3_STRATEGY_REVIEW | Verified S3A Markdown package plus explicit selection of A/B/C | S3_SELECTED_STRATEGY_EXECUTION |
| S3_SELECTED_STRATEGY_EXECUTION | Verified S3B Markdown package plus explicit production authorization | S4_IMAGE_PRODUCTION |

- Selling-point wording, membership, order, or Screen 2 count changes: clear both approvals and return to S2.
- Brand, model, category, core fact, target comparison set, product-image changes, or identity-lock changes: clear all flags and return to S1.
- Strategy-only changes: clear strategy approval and return to S3_STRATEGY_REVIEW.

Count only unambiguous approval such as `确认`, `通过`, `按这组继续`, or an equally explicit statement. Explanation, comparison, deletion, addition, or revision is not approval. Image production has the stricter separate requirement of an action statement naming the selected option and images, such as `开始生成方案B图片`.
