# S1 research contract

S1 creates or refreshes `source-inventory.json`, `fingerprints.json`, `product-identity-lock.json`, and `research.json`.

Use `build_source_fingerprints.py` for deterministic hashes. Only current-product files and images enter product fingerprints. Style, layout, redesign, task configuration, and research use separate component hashes.

Research records an ISO access date, a maximum age in days, at least six useful samples across two sources by default, direct HTTP(S) URLs, access status, capture time, limitations, synthesis, and source-linked conclusions. A limited set requires fallback attempts and LOW or MEDIUM confidence. If responsible synthesis is impossible, use `S1_COMPETITOR_RESEARCH_BLOCKED` and stop.

The standalone identity lock uses only current-product images. Use `LIMITED` or `BLOCKED` when required views or immutable features cannot be established. Later execution requires `READY`.

Close S1 with `complete_stage.py s1 <research.json> <state.json>`. Its PASS receipt records `research.json` in `delivery_receipts.S1`, sets `COMPETITOR_RESEARCH_COMPLETE`, and opens S2. A research `BLOCKED` status is a stop signal, never a completion.
