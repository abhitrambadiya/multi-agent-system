# Acceptance checks

| Area | Evidence required |
|---|---|
| Real data | Source archive hashes, table counts and revenue join invariant |
| Purchases | Mandatory exact owner approval; reject, expiry, changed offer/stock/budget, duplicate and rollback tests |
| Delivery | On-hand unchanged at order time, updated once at receipt |
| Persistence | Pending LangGraph approval restored from a new Engine/process |
| Retrieval | Policy support returned, citations resolve and versions change |
| Reuse | Exact/semantic hit; near entity/date/metric/negation/qualifier rejected; state mutation misses |
| Generation | Local Qwen digest recorded; schema/citations/monetary claims checked; failure/repair usage logged |
| UI | Visible backend tasks, approved/rejected states, evidence, refresh/reconnect and mobile layout |
| Research | Fixed family splits, dev threshold, held-out per-request logs for A0–A3, errors and limitations |
| Offline | Preinstalled assets/weights, local inference with external Python network denied |

No finite test suite establishes that software has no defects. These checks cover the specified workflows and failure boundaries; expand the suite when adding new business actions or integration providers.
