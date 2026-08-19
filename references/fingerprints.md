# Source inventory and component fingerprints

Create `source-inventory.json` with one entry per authoritative input. Each entry contains `path` and one scope: `PRODUCT_FACT`, `PRODUCT_IMAGE`, `STYLE_REFERENCE`, `LAYOUT_REFERENCE`, `REDESIGN_SOURCE`, `TASK_CONFIG`, or `RESEARCH_EVIDENCE`.

Run `build_source_fingerprints.py`. The script hashes file bytes and stable task-configuration content, then produces component and combined product fingerprints.

Rollback rules:

- product fact or product image change: clear all approvals and return to S1
- research comparison set change: keep product facts but return to S2 and clear both approvals
- style, layout, redesign, platform, ratio, count, or task configuration change: preserve approved selling points, clear strategy approval, and return to S3A
- generated outputs, Markdown reviews, logs, and other non-authoritative files never enter fingerprints
