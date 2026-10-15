# Demonstration runbook

1. Run `./scripts/start.sh`. Open localhost:8010 and confirm LOCAL_LLM, Qwen3:4b and MiniLM. Show Olist provenance and simulation labels.
2. Open Business; reset the local simulation if needed. This reset is explicitly scoped and does not alter raw Olist files.
3. Investigate a real sales comparison using the visible month/category controls. The default furniture_decor May–June 2018 comparison declined 21.72%, verified from the imported data. June–July increased 7.97%; changing scope must change the narrative.
4. Follow Sales → Inventory → Research → Marketing → Finance → Email → Manager. Show the explicit inventory challenge and revised campaign plan. Inventory data is a fictional overlay, not an explanation proven about Olist.
5. Ask for chair replenishment. Open Approvals, inspect BRL 2,500 for 20 units from Cedar Supply, compare the alternate offer. Demonstrate rejection first if desired, then create a new proposal.
6. Approve the simulation. Budget falls from BRL 5,000 to BRL 2,500; stock remains 4. In Business, record the simulated delivery; stock becomes 24. Repeated decisions/receipts cannot duplicate effects.
7. Ask “What is our return policy?” then a paraphrase. Inspect the cache badge. Exact repetition always demonstrates A1-compatible reuse; semantic paraphrases depend on the measured similarity threshold and qualifier guards.
8. Change return days from 30 to 14 in Business, then repeat. Show a fresh answer with a new evidence ID/version; a stale answer must not be served.
9. Open Research Lab. Explain A0–A3, measured token counts, latency and scope-mismatched hits. Show the raw per-request file and calibration record.

If generation fails, show the error and runtime state. Relaunch with AIEOS_MODE=TEMPLATE only as an explicit fallback; do not mix its outputs into the local-model benchmark.
