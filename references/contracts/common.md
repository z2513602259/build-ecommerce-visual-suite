# Common v3 contract

Use schema version `3`, `skill_version: 3.0.0`, and `workflow_contract_version: 3` for every new artifact.

Every artifact contains `workflow_id`, `product_fingerprint`, component `fingerprints`, `workflow_stage`, `task_profile`, `visual_mode`, `style_direction`, `visual_mode_reason`, `input_classification`, `task_config`, `approval_snapshot`, `artifact_refs`, and `audit_result`.

`fingerprints` contains `product_fact`, `product_image`, `style_reference`, `task_config`, `research`, and `product`. `product_fingerprint` equals `fingerprints.product`.

Large authoritative artifacts are referenced instead of copied when possible. Each `artifact_refs` entry contains a sibling-relative `path` and lowercase SHA-256 `sha256`. New S3 and S4 artifacts reference `product-identity-lock.json` and `research.json`; the validator resolves and verifies them before semantic validation.

Keep `approval_snapshot` embedded because it is the gate evidence. Approved selling points include their exact IDs, wording, order, benefits, and current-product sources.

Legacy schema-v2 artifacts remain read-only compatible. Do not create new v2 artifacts or silently treat an old v2 approval as current after source or rule changes.
