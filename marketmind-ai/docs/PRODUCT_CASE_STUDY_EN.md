# MarketMind AI v1.2 — Task-Verified Market Research Agent

**Project type:** AI Agent Product Management & Python prototyping | **Data:** Fully synthetic market microstructure | **Status:** Local verified MVP; live-model and user outcomes not yet evaluated.

## 1. Product problem and user hypothesis
The predecessor was a high-frequency-market-data notebook with reusable analysis modules but manual execution. Hypothesis: research analysts could benefit from translating bounded, multi-step questions into traceable deterministic tools—provided the system knows when a user task is NOT complete. Persona assumptions are hypotheses, not interview findings.

## 2. Why Agent, rather than another dashboard?
Simple fixed metrics still work better as direct controls; a tool-selecting Agent may be useful when analysis combines quality checks, spread/OBI interpretation, visible-price-level event detection, charting and uncertainty. The product avoids trading execution, real-time claims, and RAG/multi-agent complexity without a demonstrated need.

## 3. Iteration based on observed engineering failure
**v1.0:** function calling wrapped preexisting analysis utilities, but unverified model answers and failing data checks could lead to apparently completed research.  
**v1.1:** introduced read-only tool whitelist, scope-bound metric reports, quality gate, run trace and offline regression baseline.  
**v1.2:** audit uncovered *semantic completion* and *sampling coverage* gaps: completing an unrelated tool could pass; a coverage-only task could be marked incomplete; missing trades were not dependency-aware; a paid-model sample could select only one category. We addressed these with TaskContract, TaskVerifier, scope conflict diagnostics, trade-aware gate policy and balanced eval selector.

## 4. Product decisions and engineering scope
- Put intent-to-task requirements in an auditable typed contract, not a prompt suggestion.
- Keep the LLM optional. Require deterministic evidence for numeric claims and a server-supplied authorization boundary.
- Abstain when a request is unclear instead of guessing the missing analysis.
- Declare low trade matching as WARN for quote-only research and BLOCK when dependent on trades. Note: this policy is implemented and tested, while no dedicated trade-dependent Agent tool is available.
- Treat report `COMPLETED` as a task-level assertion, never merely a non-empty tool trace.
- Preserve test failures as regression cases and distinguish local verification from model/user performance.

## 5. Verification versus remaining unknowns
Locally reran **62 automated tests**, **45/45 deterministic offline cases** and **balanced 20-case selection across five categories**. A 100-prompt semantic catalog is present but **not executed as live model evaluation**. No user interviews, comparative workflow timing, retention, production security or financial trading performance have been measured.

## 6. Next experiments
Run a capped mixed-category API pilot; have human adjudicators assess full-task compliance, expected tools, metric correctness, unsupported-action handling, token/latency and any cases that should have asked a question. In parallel, complete Streamlit UAT and a small within-subject Notebook vs Agent research task comparison. Update PRD and shipping criteria only with measured results.

## 7. Responsible resume wording (do not imply live model metrics)
**MarketMind AI | AI Agent Product & Engineering Project**
- Scoped a synthetic-market research copilot and defined typed task contracts mapping supported user intents to required analytical tools, metrics and deliverables, with explicit clarify/unsupported/scope-conflict states.
- Designed and implemented server-side task completion checks, data-quality policy, authorization, evidence-bound descriptive reports and traceable run artifacts using Python, Pydantic and a bounded optional LLM tool interface.
- Validated 62 local automated tests and a 45-case deterministic workflow baseline; designed a 100-case real-model evaluation catalog and balanced sampling harness while explicitly labeling live-model and user impact results as pending.
