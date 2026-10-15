# Measured held-out results

Run `20261014T124545Z` · Qwen3:4b · LOCAL_LLM · one pass · 60 requests per arm.

| Arm | Tokens | Calls | Hits | Scope-mismatched hits | Failed requests | p50 seconds | p95 seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| A0 | 48,513 | 60 | 0 | 0 | 0 | 4.84 | 12.60 |
| A1 | 29,193 | 36 | 24 | 0 | 0 | 5.27 | 11.64 |
| A2 | 10,051 | 13 | 47 | 11 | 0 | 0.53 | 7.58 |
| A3 | 21,912 | 26 | 34 | 0 | 0 | 0.79 | 10.87 |

A3 used **54.83% fewer measured generation tokens** than A0 on this trace. Mean request latency was 48.53% lower.

Family-resampling sensitivity range for token reduction: 47.18%–63.19%. Descriptive family-resampling sensitivity range, not a confidence guarantee: sequential cache behavior makes family outcomes dependent. One pass, 12 held-out families, synthetic questions.

Scope-mismatched hits compare returned task context with predeclared oracle fields. They do not measure every factual or linguistic error in generated prose. A2 is deliberately unsafe and is unavailable in the live API. No paid API costs or energy savings were measured. Failed/repair generation attempts count toward token totals; unknown usage is reported separately.

Dataset SHA-256: `967e41e04fc306fe604e2a693f488995a8b41e5047418f8a5c8e4abd6deca784`
Query manifest SHA-256: `7dd86a93099a059954a2493309cb1de8ad4fad45ba5aef3afc0d86e03b4ef86a`
Model digest: `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`

See `requests.jsonl`, `error-cases.json`, `summary.csv`, the run SQLite ledgers and `code_snapshot/` for reproduction.
