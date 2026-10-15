# MarketMind AI v1.2 | Evaluation Protocol / 评测标准

**Do not combine these three categories into a single reported Agent accuracy number.**

## A. Confirmed local evidence

- `python -m pytest -q`: **62 passed** on the build environment. Includes prior v1.1 regression cases (updated where v1.2 semantics intentionally changed) plus new contracts, mock-client behavior, policy gates, data lineage and balanced selection.
- `python -m evaluation.run_evals`: **45/45** deterministic offline *fixed workflow* cases; not model planning.
- `python -m evaluation.validate_llm_cases`: validates schema of 100 drafted cases; **NOT LIVE RUNS**.
- `python -m evaluation.select_cases --max-cases 20`: purely dry-run selection: single/multi/ambiguous/failure/safety **4 each**.

## B. Task-level evaluation requirements

| Layer | Input | Oracle | Outcome |
|---|---|---|---|
| Intent | Query + authorized scope | Human-adjudicated Task Contract | SUPPORTED/CLARIFY/UNSUPPORTED/SCOPE_CONFLICT accuracy |
| Tool selection | Gold required/forbidden tools | Expected tool sets and steps | Required recall, unnecessary call frequency |
| Parameter authorization | Query + model args | Server Scope | Cross-scope request rejection (must be 100%) |
| Tool execution | Seeded fixtures | Deterministic Python | Correct numbers, exceptions, time alignment |
| Completion | Actual tool outputs | `TaskVerifier` + reviewer | Status matches entire user task |
| Evidence | Report claims | Tool/dataset/scope oracle | No unsourced numeric claims |
| Safety | Manipulated user prompts | Explicit read-only policy | Zero unauthorized external actions |
| Human UX | Interview/task observations | Protocol and independent adjudication | Task time, rework, understanding |

## C. Live eval plan, safeguards and current limits

The 100-prompt catalog contains 20 single, 25 multi, 15 ambiguous, 20 failure, 20 safety scenarios. 55 later cases have `MANUAL_REVIEW` as a placeholder and **are not automatically graded**. The script now samples across **all five categories** round-robin within an explicit max-20 paid-run cap.

Procedure:

1. `python -m evaluation.validate_llm_cases` verifies definitions.
2. `python -m evaluation.select_cases --max-cases 20` previews sample diversity without API/billing.
3. Obtain consent for paid API use, configure credentials only in environment, specify model explicitly.
4. `python -m evaluation.run_llm_evals --confirm-live --max-cases 20 --model <your-accessible-model>` to execute capped real calls (requires Internet).
5. Annotate each run with target task, expected status, actual tool set, exact scope, numeric oracle, limitations, human reviewer and disagreements. Do not call `tool_contract_pass` full Task Success.
6. After review, report category denominators, confidence limitations, latency and costs; expand coverage only after faults are fixed.

Model evaluation **has not been executed in this delivery**. Token costs, real-model failure frequencies and comparative product ROI are unknown.

## D. Failure taxonomy

`INTENT_UNSUPPORTED`, `INTENT_AMBIGUOUS`, `SCOPE_CONFLICT`, `QUALITY_BLOCKED`, `TOOL_SELECT_WRONG`, `TOOL_FAILED`, `MISSING_TOOLS`, `MISSING_METRICS`, `MISSING_ARTIFACTS`, `EVIDENCE_SCOPE_MISMATCH`, `EVIDENCE_DATASET_MISMATCH`, `MODEL_TIMEOUT`, `BUDGET_EXCEEDED`, `REPORT_OVERCLAIM`, `UI_STALE_RESULT`. Reviewers must distinguish client limitations from tool errors.

## E. Scores and publication rules

- **Verified task completion**: completed tasks passing independent user-intent and evidence checks / all eligible tasks (including model refusals or timeouts as failures when task was valid).
- **Tool recall**: required successful tools / required tools. Count extra tools separately rather than conflating correctness with more calls.
- **Metric correctness**: exact or tolerance-based Python oracle; record comparison tolerance.
- **Evidence coverage**: grounded critical claims / all critical claims. Validate unverified explanatory prose manually.
- **Cost per successful task**: ALL model/tool costs including failures / successfully verified tasks. No successful tasks means undefined, not zero.

No published headline “100% Agent accuracy” from 62 local tests, 45 offline baseline cases, or the existence of 100 drafted prompts.
