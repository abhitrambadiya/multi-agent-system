# Verification record

Implementation verification completed, 15 October 2026.

- Olist import: 99,441 orders, 112,650 item rows; no orphan order items; raw item-price total equals sales-view total (1,359,164,370 centavos).
- Local multilingual MiniLM loaded from project files and retrieved versioned evidence.
- Production frontend TypeScript/Vite build passed.
- Initial automated suite: 65 tests passed, including atomic rollback, parallel duplicate approval, receipt idempotency, persisted graph approval after restart, cache scope/version checks, invalid model JSON/citations and API owner boundary.
- Browser: replenishment reached AWAITING_APPROVAL, survived refresh, accepted a simulated owner approval, and exposed separate delivery recording.
- Development-only threshold calibration: .82 retained; 10/12 equivalent pairs admitted, 0 unsafe scope matches among the development near-misses. This is not a held-out accuracy claim.

The early checks above are retained as an implementation record; final results follow.

## Completed real-runtime checks

- Final automated suite: **83 passing tests**. Logs: `results/test-build.log`.
- Qwen3:4b downloaded and running through Ollama 0.40.3. Multilingual MiniLM loaded entirely from project files.
- Live-model testing exposed a centavos/reais error. Fixed by converting structured monetary evidence to explicit BRL strings before prompting and rejecting unsupported monetary amounts. Added regression tests and one audited repair allowance.
- Citation generation constrained to an enum of actual supplied evidence IDs. Unsupported citation IDs and invalid JSON are still validated at the application boundary.
- The browser's live May–June furniture/decor investigation correctly reported BRL 53,706.45 → BRL 42,042.22, -21.72%, and avoided claiming a historical cause.
- Browser paraphrase “Please explain our return policy.” reused the prior answer with **zero new generation tokens**.
- Browser policy mutation 30 → 14 days caused fresh generation and correctly cited the new version. The live response used 609 measured tokens in one call.
- Browser purchase: approval reserved BRL 2,500; delivery later changed on-hand from 4 to 24. No console errors were observed in this journey.
- Local-only inference check completed with Python external sockets denied, while localhost remained available; no external socket attempt occurred. A real local-model answer and simulated replenishment rejection succeeded. See `results/offline/verification.json`. Ollama ran separately with cloud disabled; this is not a claim that OS networking was disconnected.
- Responsive layout inspected at 390 × 844 and the normal desktop viewport. Temporary viewport override reset. `results/ui/office.jpg` records the connected UI.

## Evaluation audit

A partial v1 benchmark was stopped and explicitly excluded after discovering that boundary near-misses could repeat another split's base question. Manifest v2 confines alternatives to their own split; a regression test checks that identical requests do not cross splits. Development calibration was rerun and retained .82. The final evaluation uses v2 and retains its own frozen backend/evaluation code snapshot.

An additional edge-case check found early historical categories with zero baseline sales. The application now says percentage change is undefined and flags periods below ten delivered orders. This formatting branch is outside the held-out June/July category cases; the experiment's executed code snapshot is preserved separately.

- Additional crash-window tests passed: retry after the atomic order commit and retry after graph completion both recovered without duplicate orders or budget changes.

## Final research and build checks

- Held-out run `20261014T124545Z`: 240 completed requests, zero failures; A3 21,912 tokens versus A0 48,513 (54.83% reduction), zero scope-mismatched A3 hits. A2 had 11 scope mismatches. See `results/benchmark/RESULTS.md`; the metric does not establish factual correctness of all prose.
- Separate eight-request policy mutation experiment completed: A0/A1/A3 generated the updated 14-day policy, while A2 reused the stale 30-day response. Saved as `results/benchmark/mutations.json`.
- Fresh-process embedding constructor: 9.63 seconds; initial 136-document corpus/index: 1.00 second. Already downloaded files and possibly warm OS cache; excludes Ollama load. See `results/startup/timings.json`.
- Final `scripts/check.sh`: 83 passed; TypeScript/Vite production build passed; Python compilation passed.
- Benchmark comparison figure inspected for clipping and label readability.

- Final reset UI inspection caught stale agent completion badges after clearing the selected workflow. Updated event synchronization to clear agent state when no workflow is selected; rebuilt the frontend and verified the reset in-browser.

- Final live generation exposed a contradictory claim that simulated stock was sufficient while the structured shortfall was 20. Added a narrow contradiction guard with bounded repair, three regression cases, and a cache-version bump. This is an additional deterministic guard, not complete semantic validation of prose. The published experiment retains its pre-guard code snapshot; its token results are not relabeled as a rerun of the final version.

- The bounded repair correctly expressed a negative sales delta as “decreased by BRL 11,664.23”; adjusted the currency guard to accept that exact magnitude only when its negative value exists in evidence. An unsupported decrease remains rejected. Two regression cases added.

- Final guarded live investigation completed with a correct 20-unit simulated shortfall and the exact sales decline. Both inference attempts were counted (2,424 tokens). Reset returned all eight agents to Ready. Screenshot and workflow record saved under `results/ui/`.
