# Creative review and compliance audit

## Review pipeline

Run three steps before final S3 delivery:

1. **Initial strategy pass**: create A/B/C from the approved selling points and routed visual mode.
2. **Four-perspective audit**:
   - commercial operator: platform fit, scan speed, decision sequence, concrete purchase reasons, and ecommerce conversion language
   - visual director: hierarchy, distinction, product prominence, aesthetic coherence, and product-scene integration
   - technical director: generation feasibility, ratio, angle-matched current-product references, identity-lock coverage, generation method, itemized product fidelity, declared scene mode, and scene-fit reviewability
   - conversion psychologist: one-glance comprehension, consumer outcomes, objections, evidence, trust, and action flow
3. **Correction pass**: repair every failed item and record the correction log.

Output conclusions, findings, and corrections only. Do not output hidden reasoning or role-play dialogue.

## R1–R12 redlines

| ID | Check |
|---|---|
| R1 | No invented current-product fact, parameter, certification, price, service, or performance |
| R2 | No competitor or reference-product fact used as current-product proof |
| R3 | Every image task binds to the current-product identity lock and angle-matched original references; product identity, structure, proportion, parts, color, material, texture direction, markings, and support details remain faithful |
| R4 | Every copy claim and visual task has traceable current-product evidence; consumer-visible copy states approved facts directly without narrating `产品资料写明`, `参数文件显示`, `原图可见`, or other evidence provenance; `说明文案` is final copy rather than an internal note |
| R5 | Selling-point IDs, wording, order, and sources match the approved snapshot |
| R6 | A/B/C are materially differentiated under the selected visual mode |
| R7 | Every option uses `文案模式: 电商转化型`; copy density matches the selected task profile; main title/subtitle are at most 10 visible characters, selling-point line is 6–22, explanation is normally 16–42 with at most two sentences, and CTA/transition is at most 14 |
| R8 | Platform strategy and safe-area behavior match current evidence or disclose a deviation |
| R9 | Image tasks are independent pure images with no collage, generated typography, or intentional text space; every task declares the correct scene mode and does not disguise a staged backdrop as a real usage scene |
| R10 | Each unit gives a one-glance purchase conclusion, supporting fact or difference, direct consumer outcome, and concise fact-plus-benefit explanation; no literary, curatorial, design-review, evidence-reporting, or mechanical document-navigation language remains |
| R11 | Identity-lock IDs, reference-view IDs, immutable-feature IDs, JSON, asset IDs, paths, prompts, and downstream instructions are complete and safe to execute; generated images are never the sole product-identity source |
| R12 | Category-sensitive language stays within lawful, supportable expression boundaries |

Each check contains `redline_id`, `status` (`PASS`, `FAIL`, or `NOT_APPLICABLE`), `findings`, and `corrections`. Final S3/S4 delivery may not contain `FAIL`. Use `NOT_APPLICABLE` only with a reason.

## Pure-image audit

Require the prohibition list to cover added text/gibberish, titles/subtitles, labels/prices/CTA, icons/dimension lines, collage/grid/card frames, intentional text space, and invented or altered product structure. Authentic markings may remain only when necessary for fidelity.

## Product-fidelity audit

Apply `fidelity/task-binding.md` in S3B and `fidelity/output-audit.md` in S4. Reject text-only recreation, unsupported viewpoints, generated-image reference chains, omitted critical feature IDs, or any generated asset whose itemized `产品保真检查` contains `FAIL` or `PENDING`.

## Scene-fit audit

Apply `scene/planning.md` in S3A/S3B and `scene/output-audit.md` in S4. For `真实使用场景`, reject generic stage sets, arbitrary decorative backgrounds, implausible placement, missing anchors, absent scale cues, material conflicts, or obstructive props. For other modes, verify honest presentation. Record the result in `场景适配检查`.

## Category-sensitive escalation

For beauty, food, maternal/child, safety, health-related, or regulated products, retain exact evidence wording. Flag legal review when a claim concerns treatment, prevention, absolute safety, guaranteed effects, certification scope, or measurable performance not directly supported by current evidence.
