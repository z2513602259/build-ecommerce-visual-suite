# Detail-page strategy, copy, and image contract

## Default progression

Default to 12 screens. The user may explicitly override `screen_count` during S1; store the override and validate against it.

| Screen | Default responsibility |
|---|---|
| 1 | Product hook, positioning, and first purchase reason |
| 2 | Approved selling-point overview |
| 3 | Core material, ingredient, component, or foundational product understanding |
| 4 | Construction, craft, technology, or process proof |
| 5 | Design details and product recognition |
| 6 | Function, usage, or experience |
| 7 | Dimensions, specification, fit, or compatibility |
| 8 | Usage scenario, lifestyle, or ownership feeling |
| 9 | Evidence, detail proof, and trust |
| 10 | Purchase objection resolution |
| 11 | Parameters and purchase confirmation |
| 12 | Brand trust, transition, and action |

Adapt category terms without changing the communication role. If screen count is overridden, preserve the sequence hook → understanding → evidence → fit → trust → action and record the revised responsibility map.

Every screen contains exactly these seven copy fields:

1. 页面职责
2. 主标题
3. 副标题
4. 卖点短句
5. 说明文案
6. CTA或承接语
7. 对应的真实产品依据

All copy is complete in S3 and intended for direct use in post-layout. `主标题`, `副标题`, `卖点短句`, `说明文案`, and `CTA或承接语` are consumer-visible ecommerce copy, not planning labels or production notes.

For S3A, record one internal `消费者决策问题` and one current-product `事实锚点` for every screen in `文案质检`. The readable review must display the decision question so the user can judge the copy in context; neither audit field is typeset into the final page.

Apply `ecommerce-copy.md` to all screens. Keep field duties distinct:

- `主标题`: the purchase conclusion or strongest reason to care
- `副标题`: a supporting fact, difference, number, material, or benefit
- `卖点短句`: the consumer result in one scannable line
- `说明文案`: one verified product fact connected to one restrained consumer benefit
- `CTA或承接语`: a decision cue or natural transition, never repetitive document navigation

State an approved product fact directly; never explain to consumers where the fact was found. Phrases such as `产品资料明确写明`, `产品资料标注`, `资料显示`, `参数文件注明`, `根据产品图可见`, and `原图中可以看到` belong to evidence review, not ecommerce copy. Put source narration and locators only in `对应的真实产品依据`.

- Invalid consumer copy: `产品资料明确写明采用乌金原木。`
- Valid consumer copy: `精选乌金原木，木纹自然舒展。`

Apply these fixed title limits to every screen:

- `主标题`: at most 10 visible characters
- `副标题`: at most 10 visible characters

Count after removing whitespace; count every remaining Chinese character, letter, digit, and punctuation mark as one visible character. Write all consumer-visible fields in concise, natural, purchase-oriented language that consumers can understand directly. Keep every claim restrained and supported by current-product evidence.

## Customer-facing explanation copy

`说明文案` is final consumer-facing ecommerce copy that will be typeset into the finished detail page. It must describe or expand the screen's core selling point by connecting a verified product fact to a restrained benefit, experience, use, fit, or purchase reason.

Write it as one or two concise sentences, normally 16–42 visible characters, suitable for direct publication. It must not contain:

- strategy commentary, page-planning rationale, camera direction, visual direction, or production notes
- placeholders such as `待补充`, `待完善`, `暂无`, `说明文案`, or `这里写文案`
- source IDs, file paths, evidence labels, asset IDs, or audit language
- evidence-provenance narration such as `产品资料写明`, `参数文件显示`, or `原图可见`
- instructions to designers such as `此处展示`, `后期排版`, or `用于说明`
- literary or curatorial atmosphere used in place of a purchase reason
- design-review language such as visual rhythm, narrative, spatial base tone, or staged aesthetic commentary
- reporting language such as `已确认产品事实`, `真实信息一次看清`, `逐项呈现`, `本页已整理`, or `集中确认`

Keep citations and factual locators only in `对应的真实产品依据`. Keep action language in `CTA或承接语`. Do not repeat the title or selling-point line as the entire explanation.

## Screen 2 overview

Default to six cards selected only from the user-approved set. Categories remain dynamic. Use sequence IDs `SP-01` onward plus `来源卖点ID` to preserve the S2 candidate mapping.

Each card contains:

- a three-line block: `[类别]`, exact feature, short benefit
- current-product basis copied from the approved selling point
- unique independent pure-image asset, lens focus, product angle, source images, prompt, prohibitions, ratio, and card position

The three-line block is also consumer-visible ecommerce copy. Keep it natural, concise, evidence-bounded, and free of planning labels, production instructions, placeholders, source IDs, or asset IDs. The 10-character limit applies only to the screen-level `主标题` and `副标题`, not to these three card lines.

The `简短利益` line must state a direct consumer outcome, not an aesthetic interpretation or evidence-report summary. It remains identical to the user-approved S2 `可转化利益`, so correct non-commercial benefit wording in S2 before approval rather than rewriting it silently in S3.

Default six-card hierarchy:

| Card | Position | Suggested generation ratio |
|---|---|---|
| SP-01 | Left vertical hero | about 4:7 |
| SP-02 | Upper-right horizontal | about 1.15:1 |
| SP-03 | Middle-right horizontal | about 1.15:1 |
| SP-04 | Full-width horizontal | about 2.35:1 |
| SP-05 | Lower-left half-width | about 1:1 |
| SP-06 | Lower-right half-width | about 1:1 |

If the user approves another card count, `screen2_layout_spec` must contain one unique position and ratio for each card. Do not apply the six-card layout to a different count.

Generate all card images independently as complete compositions. Share color, light direction, background texture, and product-fidelity standards. Build rounded cards and overlay copy only in post-production; do not reserve text space in generation.

Choose the scene mode independently for every card. Material, finish, construction, and design-detail cards often work better as `产品肖像` or `细节证据`; do not force them into a vague residential set. Use `真实使用场景` only when the card's selling point benefits from showing placement, fit, interaction, storage behavior, or ownership context, and then supply the complete spatial relationship defined in `scene/planning.md`.

Count generation tasks separately from final screens. By default, every non-overview screen uses one pure-image task and Screen 2 uses one task per card, so `image_count = screen_count - 1 + screen2_card_count`.

## Strategy differentiation

Produce exactly A, B, and C. Keep target platform, task configuration, product truth, and approved selling points consistent. Differentiate worldview, palette, light, scene language, layout philosophy, and conversion emphasis. Apply the selected visual mode from `routing.md`.

All three options remain `电商转化型`. Differentiate their emphasis—such as direct facts, quality confidence, or lifestyle benefit—without allowing any option to become brand prose or a design essay.

## Purchase narrative before screens

Before drafting the 12 screens, set one `购买叙事` for each option: core purchase proposition, first-screen promise, main buyer concerns, decision progression, and copy tone. The progression must cover desire or positioning, product proof, fit, concern removal, and action. Use it to make the page feel like a purchase path rather than twelve disconnected descriptions.
