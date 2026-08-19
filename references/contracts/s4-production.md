# S4 production contract

Use `workflow_stage: S4_IMAGE_PRODUCTION`. Selling points and strategy are approved, the selected execution package and its verified S3B delivery receipt exist, and `production-authorization.json` records the user's exact explicit image-production request and requested asset scope. “继续” and “确定” are not valid authorization.

Every asset mirrors one selected execution task and adds output path, generation status, attempt count, maximum attempts, last error, retry decision, pure-image check, itemized product-fidelity check, and scene-fit check.

Default `max_attempts` is 3. Do not regenerate after the limit. Mark the asset `FAILED`, preserve the best prior output and error record, and report the blocking fidelity or generation issue. A user may explicitly authorize another bounded retry.

A generated asset requires an existing file and PASS for pure-image, product-fidelity, and scene-fit checks. Partial user-requested production may leave other assets PENDING, but the manifest must state the requested scope and may not claim suite completion.
