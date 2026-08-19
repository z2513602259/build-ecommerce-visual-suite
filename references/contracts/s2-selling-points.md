# S2 selling-point contract

Use `workflow_stage: S2_PRODUCT_SELLING_POINT_REVIEW`. Include the product, routed inputs, task configuration, research synthesis, candidate selling points, recommended set, rejected claims, missing evidence, and approval request.

Truth comes only from current-product evidence. Research establishes relevance and presentation opportunities. Output no A/B/C strategy, final page copy, image brief, execution prompt, or image.

Pause for explicit approval. Freeze approved IDs, wording, order, benefits, current-product sources, approval excerpt, and component fingerprints.

After the user approves, record the approval snapshot in `state.json` and run `complete_stage.py s2 <selling-point-review.json> <state.json>`. Its PASS receipt records the review in `delivery_receipts.S2`, sets `SELLING_POINTS_APPROVED`, and opens S3A. The script refuses approval without explicit evidence, refuses non-object entries in the approved list, refuses approved IDs that are not in the reviewed candidate set, refuses duplicate approved IDs, and refuses any approved point whose field set or field values differ from the reviewed candidate in any way. The approved point must carry exactly the candidate's fields — core fields, extended fields, and research metadata alike. Reordering approved points is allowed; adding, deleting, duplicating, or rewriting any frozen field is not.
