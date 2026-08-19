# Task profile contracts

## Shared configuration

Every S3 package declares:

- `task_profile`
- `target_platform`
- `image_count`
- `output_ratios`
- `platform_safe_area`
- `screen_count`, `screen_count_override`, `screen2_card_count`, and `screen2_card_count_override`

For non-detail tasks, set screen and Screen 2 counts to `0`. User-specified counts and ratios override defaults and must be written into state and S3.

## Profile defaults

| Profile | Default deliverable | Ratio behavior | Copy contract |
|---|---|---|---|
| `DETAIL_PAGE` | 12 final screens and 17 independent pure-image tasks | Platform width plus per-asset ratios | Seven fields per screen |
| `MAIN_IMAGE` | 5 images | Use platform-required square/portrait ratios | Seven fields per image unit |
| `PROMO_POSTER` | 3 images | Use campaign placement ratio | Seven fields per poster unit |

These are defaults, not platform specifications. Confirm live platform requirements when exact pixels or safe areas matter.

For a detail page, `image_count` is the number of independent generation tasks, not the number of final screens. With one image for every non-overview screen and one image per Screen 2 card, calculate it as `screen_count - 1 + screen2_card_count`; the default is `12 - 1 + 6 = 17`.

## Generic content unit

For every non-detail image, produce one content unit containing:

1. `单元ID`
2. `页面职责`
3. `主标题`
4. `副标题`
5. `卖点短句`
6. `说明文案`
7. `CTA或承接语`
8. `对应的真实产品依据`

Copy is for post-layout. Do not instruct the image model to render it or reserve room for it. `主标题`, `副标题`, `卖点短句`, `说明文案`, and `CTA或承接语` are consumer-visible ecommerce copy. Limit both `主标题` and `副标题` to 10 visible characters after removing whitespace; count letters, digits, punctuation, and Chinese characters individually.

For every profile and every A/B/C option, use `文案模式: 电商转化型` and follow `ecommerce-copy.md`. All consumer-visible fields must be scan-first, purchase-oriented, and bounded by current-product evidence. State the approved product fact directly instead of saying that product materials, parameter files, or source images `写明`, `标注`, `显示`, or are `可见`; keep that provenance in `对应的真实产品依据`.

Use these default density limits unless a category-specific legal or platform requirement is recorded: `卖点短句` 6–22 visible characters, `说明文案` 16–42 visible characters and no more than two sentences, `CTA或承接语` at most 14 visible characters. `说明文案` uses one concrete fact plus one restrained consumer benefit; it is not an article paragraph, strategy note, camera instruction, evidence citation, or placeholder.

## Independent image task

Every image task contains a unique asset ID, related unit, ratio, platform safe area, lens focus, product angle, source product images, structured `保真执行`, structured `场景设计`, a complete generation prompt, explicit prohibited elements, and current-product evidence. Generate one complete composition per task.

In S3A, create only lightweight image briefs. In S3B, use `fidelity/task-binding.md` to choose the least destructive method. Prefer actual-product compositing, then locked-product background replacement, then multi-reference generation, and use single-reference generation only when the source angle directly supports the requested view. Do not use text-only product recreation. Never chain generated images as product identity references.

Classify the asset before writing its prompt:

- `真实使用场景`: the product has a credible role and placement in a named environment; apply every relationship and anchoring requirement in `scene/planning.md`.
- `产品肖像`: a controlled presentation intended to show the whole product; use a neutral or explicitly stylized backdrop and do not claim it is a real use environment.
- `细节证据`: a close-up or proof view for material, construction, interface, ingredient, texture, or workmanship; do not force a room scene when it weakens the evidence.

Do not use generic phrases such as `现代居住空间`, `真实生活场景`, or a room name without specifying how the product belongs there. A product placed in front of decorative walls, panels, or stage lighting without use relationships is a product portrait, not a real usage scene.

## Ratio policy

- Do not apply one global ratio to every task.
- Record generation ratio and intended final crop separately when they differ.
- Use the user's specified ratio first; otherwise use current platform evidence; otherwise use the profile default and label it as a baseline.
- Never distort the current product to fill a crop.
