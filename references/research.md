# Competitor research protocol

## Objective

Learn what matching or comparable product pages discuss, how they sequence evidence, which concerns recur, how platforms differ, and where the current product may have a supportable opportunity. Never copy a competitor claim into the current product.

## Query design

Build and record queries from verified current-product dimensions:

- category, synonyms, model, and visually matching descriptors
- material, ingredient, style, function, construction, usage, or compatibility
- target platform and task type
- `详情页`, `主图`, `卖点`, `参数`, `材质`, `结构`, `成分`, or category-specific decision terms

## Source order and public fallback

1. Public JD, Tmall, and Taobao product, store, and search pages.
2. Public search engines that lead to accessible original pages.
3. Brand and manufacturer official sites, product pages, catalogs, and releases.
4. Industry media, buying guides, professional reviews, and public product databases.
5. Public user-content, article, and video pages for concerns and expression patterns.
6. Image search for visible layout evidence only; never infer hidden specifications.

Do not stop because one platform requires login or blocks access. Continue through the public fallback chain. Stop only after reasonable public routes are exhausted and responsible synthesis remains impossible.

## Evidence threshold

Target at least six useful samples across at least two distinct platforms or websites.

A smaller set is valid only when all of the following are recorded:

- `research_limitations.is_limited` is `true`
- a concrete limitation reason and attempted fallback routes
- reduced confidence of `LOW` or `MEDIUM`
- enough accessible evidence to explain why the synthesis remains responsible

If evidence is still insufficient, emit `S1_COMPETITOR_RESEARCH_BLOCKED` and stop.

## Sample record

Each sample contains:

- ID, source website/platform, source type, brand/product name, direct URL, and access date
- access status (`ACCESSIBLE`, `PARTIAL`, or `BLOCKED`) and ISO evidence-capture time
- similarity basis and source confidence
- visible page sections or sequence
- principal selling points and explanation/evidence style
- useful pattern, pattern to avoid, and source limitation

## Synthesis

Produce high-frequency sections, common persuasion sequence, consumer concerns, repeated language, evidence styles, platform differences, differentiated opportunities tied to current facts, and internal planning implications. Link each conclusion to sample IDs.

## Source integrity

- Treat search snippets as discovery leads when the original page can be opened.
- Prefer official sources for public product facts.
- Use media and user content mainly for concerns and expression analysis.
- Keep conflicting evidence visible and reduce confidence.
- Never transfer competitor price, parameter, material, ingredient, certification, performance, warranty, service, or claim to the current product.

## Recency

New schema-v3 research contains `research_policy.max_age_days` and `research_policy.as_of_date`. Default to 30 days unless the category has a justified slower refresh cycle. Refresh stale research before S2; do not disguise an old sample set by changing only its date.

## Blocked output

Use `contracts/s1-research.md`. Include attempted platforms, actual queries, fallback routes, accessible evidence, blockers, and specific inputs that would unblock research. Do not continue to S2.
