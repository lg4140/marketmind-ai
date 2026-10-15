# MarketMind AI v1.2 | Task Contract & Completion Semantics

## Why the contract exists
The v1.1 runner could label a run `COMPLETED` after any analytical tool, even if the user asked for a different deliverable. v1.2 separates **tool execution success** from **user-task completion**. The contract is defined before any optional LLM call and is evaluated by deterministic Python, not by self-reported model claims.

## Typed fields
`TaskContract` (`agents/task_planner.py`) includes `decision`, `intent`, the enforced server `scope`, `required_tools`, `required_metrics`, `required_artifacts`, `notes`, `query`, `planner_version`. Supported decisions: `SUPPORTED`, `NEEDS_CLARIFICATION`, `UNSUPPORTED_ACTION`, `SCOPE_CONFLICT`.

Scope mismatches are not resolved by silently changing the authorization. Requests to trade, reveal secrets, or use live quotes are outside product scope. Natural language parser uses conservative bilingual patterns and intentionally abstains outside its known grammar. **This is an MVP rules-based resolver and not a general-purpose language understanding benchmark.**

## Semantics and examples
| User intent | Required evidence | If absent |
|---|---|---|
| Only list available stocks/dates | successful `profile_dataset` | INCOMPLETE |
| Validate input dataset | `validate_dataset` passed task-aware gate | BLOCKED or FAILED |
| Spread/OBI | `analyze_microstructure` and selected metric fields | INCOMPLETE |
| Candidate new visible price levels | `analyze_liquidity_events` and `candidate_new_visible_levels` | INCOMPLETE |
| Chart request | successful `generate_chart` and run-linked artifact | INCOMPLETE |
| Unclear market question | no guessing | NEEDS_CLARIFICATION / INCOMPLETE |
| Scope mismatch in user text or model arguments | stop; preserve selected scope | SCOPE_CONFLICT / INCOMPLETE |
| Unauthorized transaction | do not offer any execution tool | UNSUPPORTED_ACTION / BLOCKED |

## Verification logic
Only successful tool results contribute. Required tools, metric labels and artifact references must all exist. `TaskVerifier` does not trust model prose. A model's unexpected `stock_id`, time or date is rejected; optional omitted arguments inherit the server scope. A successful profile-only task can have zero financial metrics.

Partial execution with missing deliverables currently returns `INCOMPLETE` (not `PARTIAL`); UI and evaluators must show its unmet requirements. No claim is made that every valid Chinese/English phrasing is supported. A larger semantic planner requires actual test cases, human adjudication and rollout safety evaluation.

## Known limitations to test next
Negation and synonyms outside the limited patterns may abstain or overtrigger; implicit time ranges, multiple stocks, cross-session follow-ups and external files are unsupported. `CLAIM` records currently attest to deterministic descriptive metrics only, not causal statements. Future phases should add ambiguity dialogs, user confirmation of plan, stricter artifact hashes in the verifier, and human-calibrated intent labels.
