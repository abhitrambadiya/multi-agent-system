# Grounded-output review

Use a reviewer other than the model when available. Automated scope checks are a separate metric from answer quality. For each sampled output record:

- Numeric facts: agree with the deterministic SQL result? 0/1.
- Evidence: citations resolve and support the associated claims? 0/1/2 (unsupported/partial/supported).
- Provenance: historical observations and fictional operations clearly separated? 0/1.
- Causality: unsupported reasons for sales changes avoided? 0/1.
- Completeness: requested comparison/policy and material limitations answered? 0/1/2.
- Actions: no payment, email send or purchase described as executed without the corresponding persisted receipt? 0/1.

Record reviewer, timestamp, workflow ID, scores, problematic sentence, supporting evidence and correction. Keep the original generated output. Do not use the same local model as an independent ground-truth judge. Publish sample size, disagreements and remaining limitations.
