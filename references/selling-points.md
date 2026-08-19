# Selling-point derivation and approval

## Two-lane evidence model

Keep two lanes separate:

1. **Current-product fact lane**: current files, specifications, certificates, user statements, and directly visible current-product evidence. This lane determines truth.
2. **Market-insight lane**: completed research about concerns, expected sections, commoditized claims, platform language, and expression gaps. This lane determines relevance and demonstration strategy.

Competitor evidence never upgrades a candidate into a current-product fact.

## Candidate generation

Do not force six candidates. Generate all useful, non-duplicative candidates supported by current-product evidence. Categories are dynamic and category-appropriate.

Each candidate contains:

- `卖点ID`, category, exact product fact, restrained consumer benefit
- `消费者决策问题`, `利益类型`, `具体消费者结果`, and `表达边界`
- nonempty structured current-product source references
- linked research sample IDs and market judgment
- evidence type, evidence strength, recommendation level
- visual proof method and risk or pending confirmation

Use stable candidate IDs such as `CSP-001`. Reserve `SP-01` style IDs for the sequence of Screen 2 cards.

## Fact-source structure

Each `本品事实来源` entry contains `source_id`, `source_type`, `location`, and `claim`. Allowed source types are current product file, current product image, certificate, or explicit user statement. A competitor, inspiration, media, or research source is invalid as current-product proof.

## Benefit language

Translate facts into restrained, direct consumer outcomes using `ecommerce-copy.md` and `copy-quality.md`. `可转化利益` and `具体消费者结果` answer `这对购买者有什么实际好处` in one scannable line. Prefer a product-specific selection or use result over abstract mood. A generic phrase such as `更清楚` or `更有质感` is insufficient unless the current product fact, object, context, or result makes it specific.

Reject literary atmosphere, design criticism, curatorial language, evidence-reporting narration, and internal process language. Do not use benefits such as `形成视觉节奏`, `成为空间底色`, `更具诗意`, `真实信息清楚呈现`, or `逐项确认产品事实`.

Do not turn visible form into unverified safety, durability, environmental, ergonomic, health, medical, compatibility, or performance promises. Put weak inferences into `风险或待确认项`.

## Review output and approval

Output the S2 contract and stop. Let the user retain, delete, rewrite, add evidence, and reorder candidates.

After explicit approval:

- freeze approved candidate IDs, wording, order, benefits, decision map, and sources
- save the approval excerpt and product fingerprint
- never silently add, replace, or reorder a selling point in S3
- use only approved selling points for copy claims and selling-point image tasks

The recommended core set is not approval.

## Screen 2 count

The detail-page default is six cards. If fewer than six valid selling points are approved, request more evidence or explicit approval of a different card count. Record the approved override in state and S3. Never fill a gap with repetition, generic marketing language, or a competitor claim.
