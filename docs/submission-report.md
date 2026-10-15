# AI-EOS: evidence-grounded business agents with guarded semantic reuse

**Implementation completed:** 15 October 2026. **Purpose:** college mega-project prototype.

## Problem and objective

Business owners ask questions that require several departments: sales measurement, stock availability, customer feedback, campaign feasibility and financial constraints. Repeating the same analysis for paraphrased questions wastes local generation work. Reusing answers solely by semantic similarity can serve stale facts or answers about the wrong product, period or business state.

AI-EOS implements a bounded business workforce and evaluates read-only answer reuse using scope and state guards. It also enforces exact owner approval for every simulated purchase. The contribution is an inspectable system and evaluation, not a claim to have invented semantic caching or autonomous businesses.

## System

Eight logical agents are implemented as LangGraph nodes with role-specific deterministic tools and result packets. Manager routes the request; Sales computes Olist SQL aggregates; Inventory reads a labeled simulation; Research retrieves versioned policies/reviews; Marketing proposes an action; Inventory challenges a shortage-sensitive discount; Finance checks constraints; Email drafts an update; Manager synthesizes cited results using one local Qwen3:4b model.

The procurement path compares supplier offers, validates the budget and pauses at a persistent approval interrupt. The local owner approves an exact digest. Execution rechecks state and commits the order/budget/audit in one SQLite transaction. A separate receipt updates on-hand stock. Unique action and receipt constraints prevent duplicate effects.

## Dataset

The Olist publisher archive is used under CC BY-NC-SA 4.0 with explicit attribution. It contains 99,441 orders and 112,650 items; eight tables are ingested, excluding geolocation. Item revenue is aggregated at item grain without multiplying payments or reviews. Data provenance and hashes are in `data/processed/manifest.json`.

Historical dates and BRL currency are retained. Stock, quotes, budgets and campaign constraints are fictional and labeled. A real association is demonstrated: furniture/decor delivered-product sales declined 21.72% from May to June 2018. The prototype does not establish a causal reason for Olist's historical sales change.

## RAG and reuse

Numeric evidence comes from parameterized SQL; textual evidence uses BM25 plus normalized multilingual MiniLM vectors with reciprocal-rank fusion. Reviews are token-bounded and order-level. Policy and evidence identifiers include source versions. Benchmark gold labels never enter retrieval or prompts.

A0 runs the same workforce without answer caching. A1 adds exact scoped reuse. A2 permits similarity-only reuse in an evaluation sandbox. A3 uses semantic candidates with critical scope and snapshot guards. Financial intents bypass all deployable answer caches. Unrecognized query qualifiers remain in the scope signature.

## Evaluation protocol

There are 48 synthetic question families over real analytics and fictional policies. Family-level splits contain 24 design, 12 development and 12 test families, balanced across policy, metrics and diagnosis. Five requests per family cover seed, identical repeat, equivalent paraphrase and two near-misses. One complete held-out pass runs 60 requests per arm (240 executions).

The .82 threshold was retained after development-only calibration: 10/12 equivalent pairs admitted and zero unsafe guarded matches among those negative cases. This is a development observation; the held-out results must be reported separately. Model, prompting, retrieval and settings remain fixed across the four arms. Individual generation attempts, including repairs, are logged with measured input/output token counts and latency.

## Results and interpretation

One held-out pass completed all 240 executions with zero failed requests:

| Arm | Generation tokens | Model calls | Cache hits | Scope-mismatched hits | Median latency |
|---|---:|---:|---:|---:|---:|
| A0: no cache | 48,513 | 60 | 0 | 0 | 4.84 s |
| A1: exact | 29,193 | 36 | 24 | 0 | 5.27 s |
| A2: similarity only | 10,051 | 13 | 47 | 11 | 0.53 s |
| A3: guarded semantic | 21,912 | 26 | 34 | 0 | 0.79 s |

A3 used **54.83% fewer generation tokens** than A0 on this workload. Its mean latency was 48.53% lower. A descriptive family-resampling sensitivity range was 47.18%–63.19%; this is not a confidence guarantee because sequential cache outcomes are dependent. A separate policy change from 30 to 14 days produced a fresh, correct-version answer in A0/A1/A3, while A2 returned the stale 30-day policy.

The completed run's measured table and figures are saved in `results/benchmark/`. This report must be read alongside the exact run ID, model digest, dataset hash, query-manifest hash and per-request records. Scope-mismatched reuse is an automated oracle metric; independent manual assessment of every generated claim remains separate. Use `docs/research-rubric.md` for that review.

No API cash-saving or energy-saving claim is made. Local generation uses machine time and electricity despite having zero paid API costs. Report raw token counts, calls, cache hits, scope mismatches, failures and response-time distributions. The small synthetic query sample limits generalization; one pass does not establish high-reliability bounds.

## Engineering verification

Eighty-three automated tests cover approval/rejection, exact digests, expiry, stock/offer/budget changes, atomic rollback, concurrent duplicate decisions, delivery idempotency, graph restart, cache versions/scope, citation validation, monetary-unit errors, API authority boundaries, retrieval and aggregation. Browser checks cover the connected office, real investigation, financial simulation, cache reuse, invalidation and narrow-screen layout. See the maintained verification log for the final counts.

The implementation caught a real local-model unit error during testing and now formats currency in prompts and validates monetary outputs. This illustrates why deterministic checks and visible evidence accompany generation. It does not prove unrestricted model correctness.

## Limitations and future work

The scope resolver is conservative, and the agent graph uses predefined task paths and one bounded revision. Specialist tool work is mostly deterministic; a single local model synthesizes results. True parallel specialist generation, a learned equivalence classifier, richer outcome feedback, forecasting, additional products, independent human evaluation and production authentication are future work. Live emails, payments, social publishing and private-company accounts are excluded.

## Sources

- [Olist publisher dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), CC BY-NC-SA 4.0.
- [GPTCache, Bang 2023](https://aclanthology.org/2023.nlposs-1.24/): prior semantic caching work.
- [ContextCache](https://arxiv.org/abs/2506.22791): context-aware caching prior work.
- [Multilingual MiniLM model card](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2).
- [Ollama generation API](https://docs.ollama.com/api/generate): local inference and token usage fields.
- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts): durable pause/resume mechanism.

## Benchmark interpretation notes

The trace deliberately includes repeated and paraphrased requests. Its reuse rate is a property of that workload, not an estimate of how often arbitrary business owners repeat themselves. Candidate search is linear over a small cache; embedding and SQLite overhead are included in end-to-end latency. The exact-cache baseline currently shares the candidate-vector preparation path, so its latency is not a claim about an optimally implemented exact-key store. Token counts are unaffected by that retrieval overhead.

A small developer inspection of generated outputs checked forecast/email/evidence/inventory policies, perfumery numeric comparison and one investigation against deterministic facts. The inspected numeric comparison matched BRL 26,963.93 → BRL 20,645.97 and 166 → 168 orders. One output contained a minor “on:hand” wording artifact. This inspection is not a blinded independent human quality study; retain that limitation in the submission.

The final application additionally rejects explicit sufficient/adequate-stock claims when structured inventory evidence has a positive shortfall. This guard was added after the benchmark following a live demonstration error, and its cache version was bumped. The benchmark represents its preserved execution snapshot, not a rerun of this final guard. Independent review of generated prose remains necessary.
