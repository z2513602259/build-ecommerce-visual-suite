# S3A strategy-review contract

Use `workflow_stage: S3_STRATEGY_REVIEW`. Selling points are approved; strategy approval is still false.

Hoist shared product information and parameters into `shared_product_data`. Produce exactly A, B, and C. Each option contains complete consumer-facing copy and one lightweight `图片简报` per future asset. A brief contains asset ID, related unit and selling point, generation and crop ratios, scene mode, proof goal, lens focus, product angle, and target context. It contains no complete generation prompt, fidelity execution object, source-path inventory, or prohibition list.

For detail pages, Screen 2 still has one independent brief per approved card. Default count is `screen_count - 1 + screen2_card_count`.

A/B/C must differ in conversion emphasis and in at least three visual dimensions among worldview, palette, light, layout, scene-mode distribution, target contexts, and proof priorities. Renaming fields or changing only background color is invalid.

Run `complete_stage.py s3a <strategy-package.json> <state.json>` to generate `strategy-review.md`, `strategy-A.md`, `strategy-B.md`, `strategy-C.md`, `strategy-handoff.md`, `review-package-manifest.json`, and the S3A state receipt. A/B/C selection is blocked until that command passes. Wait for explicit A/B/C selection.
