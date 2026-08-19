# Human-readable strategy review

## Purpose

Never require the user to inspect `strategy-package.json` or one oversized document to understand or approve A/B/C. Keep JSON as the validated machine source and generate a layered Markdown review package from the same data.

## Deliverables

- `strategy-review.md`: the primary, concise approval interface. It contains project status, approved selling points, A/B/C comparison, and every option's copy plus image direction at screen/unit level. It excludes complete prompts, identity-lock internals, source-path inventories, and long audit tables.
- `strategy-A.md`, `strategy-B.md`, `strategy-C.md`: complete option-review books containing strategy, final copy, Screen 2 cards, and lightweight image briefs. They intentionally exclude executable prompts and fidelity bindings until one option is selected.
- `strategy-handoff.md`: deterministic chat-ready A/B/C comparison, current gate, file links, and reply examples.
- `review-package-manifest.json`: paths, SHA-256 hashes, stage, and generation status for every review file.
- `selected-strategy-review.md` and `selected-strategy-handoff.md`: generated in S3B for the chosen option and containing its complete execution tasks.
- `strategy-package.json`: machine validation source only; never the recommended reading surface.

The overview must remain sufficient for choosing A/B/C or requesting a screen-level revision. The option books must remain sufficient for execution and detailed audit.

## Generation sequence

1. Validate `strategy-package.json` with `validate_output.py`.
2. Run `complete_stage.py s3a` or `complete_stage.py s3b` against the JSON and current `state.json`.
3. Confirm the resulting delivery receipt and package manifest pass `validate_delivery_package.py`.
4. Use `strategy-handoff.md` as the chat handoff source.
5. Link the overview first, option books second, and JSON last.

Never manually maintain conflicting strategy content across these files. If the strategy changes, update and revalidate JSON, then regenerate the complete Markdown package.

## Required overview structure

`strategy-review.md` contains:

1. product, platform, task profile, visual mode, screen/image/card counts, and approval status
2. approved selling points in consumer-readable form
3. one A/B/C comparison table covering positioning, style, color, light, layout, copy tone, and image count
4. links to the three complete option books
5. one screen/unit-level review per option showing page duty, all final consumer copy, visible character counts, brief IDs, scene modes, and image direction
6. an expanded Screen 2 selling-point table for detail pages
7. a compact audit status and a clear reply template

Do not include complete generation prompts, prohibited-change inventories, source-path inventories, identity-lock internals, or full R1-R12 tables in the overview.

## Required option-book structure

Each S3A `strategy-{ID}.md` contains:

1. project and approval status
2. approved selling points and shared current-product facts needed to judge the option
3. the option's complete strategy fields and final consumer copy
4. the expanded Screen 2 card review when applicable
5. every lightweight image brief's ratios, scene mode, target context, proof goal, lens focus, and product angle
6. compact audit status and approval reply examples

The S3B selected-strategy review contains the identity lock, complete task bindings, prompts, prohibitions, evidence, four-perspective audit, R1-R12 result, and correction log.

Do not delete product facts, copy, evidence, ratios, prompts, risks, or corrections merely to shorten the overview. Move execution-heavy content into the relevant option book.

## Chat handoff

The chat response must include:

- current gate: `等待选择方案，尚未允许生图`
- compact A/B/C comparison
- overview link labeled `方案总览（推荐先看）`
- option-book links labeled `方案A审核书`, `方案B审核书`, and `方案C审核书`
- JSON link labeled `机器校验源（无需阅读）`, placed last
- explicit instructions: select A/B/C, or identify option, screen/unit, and requested change

Do not paste the entire long JSON or any complete option book into chat. The chat comparison must be sufficient for initial orientation; use `strategy-review.md` for full copy/image-direction review and the option books for execution detail.

Never claim that a scheme, selected execution book, or image-production gate is ready without the matching verified receipt. The chat response must contain actual clickable file links; plain filenames and an unrendered JSON claim are not a delivery.
