# v1.2 Release Readiness & UAT Gates

| Gate | Evidence required | Current result |
|---|---|---|
| Repository compiles | `compileall`, environment specification | PASS (local) |
| Regression | 62/62 local pytest | PASS (local) |
| Deterministic baseline | 45/45 offline cases | PASS (local) |
| Balanced selection | five classes represented in 20 selected cases | PASS (selection only) |
| Live LLM intent/plan | human-reviewed prompts, tool traces, gold statuses | NOT RUN |
| Cost and latency | per-run tokens, bill, P50/P95 | NOT MEASURED |
| Browser UAT | screenshot and interaction evidence for U01–U12 | NOT RUN |
| Data-rights review | confirmation input datasets synthetic & privacy-safe | Scoped to demo code; deployment review pending |
| Multi-user isolation | authenticating identities, storage segregation, race tests | NOT IMPLEMENTED |
| End-user task study | interview and crossover data | NOT RUN |

**Decision:** Eligible for local technical portfolio demo as a synthetic-data prototype; **not** certified as production/enterprise-ready or as a live-LLM Agent with measured success. Maintain this distinction in README and CV.

## Browser UAT (owner/date/evidence left blank until executed)

| ID | Test | Expected |
|---|---|---|
| U01 | Normal offline CLI + Streamlit run | fixed baseline clearly labeled |
| U02 | Valid tool-selected research | TaskContract, metrics and run trace match |
| U03 | Ambiguous question | INCOMPLETE / clarification, no fictional answer |
| U04 | Changed stock in user message | no silent scope substitution |
| U05 | Overridden model tool args | scope conflict, no unauthorized call |
| U06 | No trade data in quote-only task | WARN, no invented trade observation |
| U07 | Snapshot crossed market | BLOCK, no downstream analysis |
| U08 | New run fails after prior success | previous success not shown as current output |
| U09 | Two bucket intervals | distinct artifact names and hashes |
| U10 | Feedback | must attach to recorded Run ID |
| U11 | Keyboard and narrow viewport | accessible and legible |
| U12 | API failure, timeout, model refusal | clear error state, no completed fabricated research |
