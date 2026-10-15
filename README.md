# AI-EOS

An offline college research prototype: eight business departments share evidence, investigate sales, and prepare simulated replenishment. The owner must approve the exact purchase proposal before budget is committed. No live payments, emails, social posting, or cloud LLM calls are implemented.

## Run on this Mac

The Python environment, frontend dependencies, real Olist dataset and embedding model have been prepared in this project. The generation model is `qwen3:4b` in the project-local Ollama store. Exact model manifests and embedding hashes are in `data/model-manifest.json`.

```bash
./scripts/start.sh
```

Open **http://localhost:8010**. Keep the terminal open. Ctrl-C stops the application and any Ollama process started by this script. If a separately started Ollama is already running, it is left running.

For a visibly labeled deterministic fallback:

```bash
AIEOS_MODE=TEMPLATE ./scripts/start.sh
```

Template mode exercises workflows and approvals, but does not generate text or claim LLM-token savings. Check the runtime badge and Research Lab before a demonstration.

## Architecture

- React / TypeScript / Vite / Zustand. Office artwork adapted from the supplied Agent HQ reference; workflow progress comes from persisted backend events.
- FastAPI API, one background worker, LangGraph task routing and SQLite checkpoints. Awaiting-approval workflows survive restart; interrupted inference is marked failed so it can be resubmitted.
- Eight logical roles: Manager, Sales, Inventory, Research, Marketing, Procurement, Finance, Email. Numeric tools, policy checks and approvals use deterministic code; the Manager uses one shared local LLM for cited synthesis. The prototype does **not** run eight independent models or unconstrained autonomous agents.
- Olist relational analytics plus BM25 / multilingual MiniLM reciprocal-rank retrieval. Numeric totals use SQL, not vector search. Review excerpts are order-level and retain Portuguese text.
- Exact and guarded semantic answer cache; financial requests bypass it. Cache scopes include workspace, category, period, metric, negation, unresolved qualifiers and source/model versions.
- All money is integer BRL centavos. Approval digest, fresh offer/stock/budget checks, transaction rollback, unique action IDs and separate receipt operations protect simulation integrity.

The reference folders remain separate. The new backend adapts their domain flow rather than retaining their cloud-provider, PostgreSQL or non-atomic purchase implementation.

## Dataset and provenance

[Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), published by Olist, license **CC BY-NC-SA 4.0**. The downloaded archive contains 99,441 orders and 112,650 item records. Eight tables are imported; geolocation is omitted. See `data/processed/manifest.json` for SHA-256 hashes, schema, counts, coverage and aggregation checks. Preserve attribution and the dataset's license when redistributing data or derived material; this repository has no blanket relicensing of third-party data/artwork.

`REAL_PUBLIC` means historical published data, not current company operations. `SIMULATED` stock, offers, budget, campaign constraints and `SIMULATED_POLICY` documents are fictional. No historical stockout or advertising conversion is inferred from missing orders. Workspace currency is BRL throughout. Reviews and payments do not multiply item revenue through joins.

## Fresh setup

Use Python 3.12 and Node 20+ (tested here with Python 3.12 and Node 24). Install Ollama from its official distribution or Homebrew. No API keys are needed.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
(cd frontend && npm ci && npm run build)
mkdir -p data/raw
curl -L --fail https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce -o data/raw/olist.zip
.venv/bin/python scripts/ingest.py
.venv/bin/python scripts/download_embeddings.py
OLLAMA_MODELS="$PWD/data/models/ollama" OLLAMA_NO_CLOUD=1 ollama serve
# In another terminal, while that server is running:
ollama pull qwen3:4b
```

All downloads are one-time setup. `scripts/start.sh` sets offline Hugging Face flags and disables Ollama cloud. It binds only to loopback. There is no production authentication: the local single-owner session token plus origin/host checks protect the local demo from cross-origin mutation. Do not expose this server publicly.

## Verify

```bash
./scripts/check.sh
```

Tests create isolated databases in pytest temporary directories. `pytest.ini` excludes the supplied reference tests. Real Olist analytics tests require the ingested dataset. No tests mutate the reference database or place real orders.

## Research

```bash
.venv/bin/python -m eval.build_manifest
.venv/bin/python -m eval.calibrate
.venv/bin/python -m eval.runner --split test --mode LOCAL_LLM
```

The manifest has 48 question families / 240 requests, split 24 design, 12 development, 12 test. Each family has seed, exact repeat, paraphrase and two near-misses. One test pass is 60 requests × 4 arms. A0 disables caching; A1 exact cache; A2 similarity-only **evaluation sandbox**; A3 scope/state guards. The application API rejects A2.

Per-request JSONL, SQLite invocation ledgers, CSV summaries and configs live in timestamped `results/` directories. The most recent full local-model pass is exposed in Research Lab. Input/output counts are Ollama's measured token counts, including failed calls when available. Cache hits do not create invented usage records. Timing includes retrieval and checkpoint overhead; the ledger retains model-load duration separately.

`incorrect_hits` in the initial automated evaluation means a mismatch against the independently declared question scope, **not independent human verification of every generated claim**. Review generated prose with `docs/research-rubric.md`. Family-level splits and negative cases reduce leakage but this small synthetic query benchmark does not establish broad real-world reliability.

## Known boundaries

- One workflow computes at a time. Specialist steps are bounded and ordered; there is one explicit Marketing/Inventory challenge and revision. This is a demonstrable task graph, not a general business operating system.
- Supported analytics: delivered product sales, item/order counts for the top 30 categories, complete months in 2017 and Jan–Jul 2018. No forecast, margin calculation, private-company account access or causal proof.
- Simulated SKU is `DEMO-CHAIR`; default target 24, on-hand 4, two offers, BRL 5,000 budget. Every order needs approval. BRL 10,000 per-order cap cannot override available budget.
- The free-text resolver is conservative and bounded. Use the category/date/workflow controls for precise scope. Unsupported intents fail explicitly. Unrecognized qualifiers block cross-query semantic reuse.
- Citation IDs are validated, but that alone cannot prove the model's prose is fully supported. Verified deterministic facts remain visible next to the generated summary.
- A simulated reset clears local stock/order effects and invalidates pending/executed actions. Audit and workflow history remain available. Evaluation databases are separate.

See `TASKS.md`, `docs/demo.md` and `docs/verification.md` for current completion and actual verification evidence.

## Completed submission artifacts

- `TASKS.md`: completed implementation checklist.
- `docs/demo.md`: demonstration sequence.
- `docs/submission-report.md`: system, research method, results and limitations.
- `results/benchmark/RESULTS.md`: held-out four-arm results (54.83% fewer generation tokens with A3 than A0 on this trace).
- `results/benchmark/comparison.png` and `.pdf`: exportable research figure.
- `results/benchmark/mutations.json`: separate stale-policy experiment.
- `docs/verification.md`: 83 passing tests and browser/runtime checks.
- `output/AI-EOS_Source.zip`: source, dependency locks, documentation and compact research evidence; excludes downloaded datasets, weights, runtime databases and environments. Frozen benchmark code is included under its timestamped result directory. Rebuild using Fresh setup above.

After running a new full experiment, regenerate analysis and figures:

```bash
.venv/bin/python -m eval.analyze
.venv/bin/python -m eval.plot_results
.venv/bin/python scripts/package_source.py
```
