# MarketMind AI — Engineering Changelog

## v1.2 (current)
- Added `agents/task_planner.py` with conservative typed `TaskContract`, explicit abstention and supported research intents.
- Added `verification/task_verifier.py`: required tools/metrics/chart artifact check before final COMPLETED.
- Replaced silent user/model scope changes with explicit SCOPE_CONFLICT warning / INCOMPLETE.
- Updated quality gate to evaluate trade dependency and trade match rate; quote-only remains eligible under WARN.
- Enriched `ResearchReport` with contract, sourced metric claims and profile-only output; corrected seed metadata for early failures.
- Added SQLite `run_details` with contract JSON, planner version and artifact digest; model ID optional, not auto-captured.
- Streamlit clears stale previous run and displays TaskContract.
- Live evaluation runner selects all 5 categories; introduced independent dry-run selection utility; 100 cases remain pending actual API tests.
- New `tests/test_v12_task_contract.py` expands mock-client, policy and eval-selection tests; 62/62 local checks and 45/45 offline baseline pass.
- Updated PRD, architecture, English product case study, risks and acceptance protocols; archived superseded v1.1 documents.

## Deliberately not included
General-purpose semantic planner, conversation memory, live data, broker APIs, user login, robust token cost telemetry, complete natural-language claim-grounding validator, trade-dependent Agent endpoint, browser-tested deployment, user research results. None should be claimed as implemented.
