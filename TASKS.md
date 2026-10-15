# AI-EOS implementation tasks

Approved 14 October 2026. Reference: `output/AI-EOS_Implementation_Plan.md`.
All purchases and communications are simulated. Paid providers are disabled.

- [x] 1. Create isolated backend/frontend and reproducible dependency manifests.
- [x] 2. Acquire and validate Olist data with provenance; set up local model and embeddings.
- [x] 3. Implement SQLite storage, metrics, evidence and invocation ledger.
- [x] 4. Implement approval-bound, atomic, idempotent replenishment and receipt handling.
- [x] 5. Implement bounded specialist graph, sales investigation and cited policy responses.
- [x] 6. Implement hybrid RAG and exact/semantic cache with state/scope guards.
- [x] 7. Connect reference office to real workflow events, evidence, approvals and research views.
- [x] 8. Add isolated safety, retrieval, cache, aggregation and API integration tests.
- [x] 9. Run local-model smoke tests and reproducible four-arm research evaluation.
- [x] 10. Verify browser journeys, restart/reconnect, production build and offline readiness.
- [x] 11. Deliver launch scripts, dataset attribution, demo guide and measured results.

## Verification record

Completed 15 October 2026.

- 83 automated tests passed; TypeScript production build and Python compilation passed.
- Olist imported and validated: 99,441 orders and 112,650 items; item-grain sales totals preserved.
- Qwen3:4b and multilingual MiniLM installed and verified locally with zero paid API calls.
- Browser journeys verified: investigation, persistent approval, purchase, separate delivery, semantic reuse, policy invalidation and responsive layout.
- Full held-out evaluation completed: 240 executions, four cache arms, 12 test families, zero failed requests. Guarded reuse reduced measured generation tokens by 54.83% against no caching, with zero scope-mismatched hits in this trace.
- Separate policy mutation check: A0/A1/A3 returned the updated 14-day policy; similarity-only A2 reused the stale 30-day policy as expected.
- Python external-socket denial check passed with local inference. This is not an OS-wide network-disconnection test.
- Reproduction scripts, source bundle, demo guide, attribution, measured results and limitations delivered. Independent human grading remains future research work.
