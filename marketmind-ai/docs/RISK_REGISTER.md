# MarketMind AI v1.2 — Risk Register

| Risk | Probability / Impact (qualitative) | Mitigation in v1.2 | Remaining gap / trigger |
|---|---|---|---|
| Incorrect COMPLETED | high/high (from v1.1 audit) | TaskContract + TaskVerifier | Unknown intents, implicit clauses, cross-turn requests |
| Scope mismatch | medium/high | Reject explicit scope disagreement | User confirmation UI not implemented |
| Missing/late trade records | medium/high | Quote WARN, trade-dependent BLOCK policy | Calibrate threshold on real authorized data |
| Unverified market interpretation | high/high | Metric-derived claims only; no causal inference | Natural-language evidence checker not available |
| Unsafe trading request | low execution risk, medium confusion | No broker tools, unsupported-intent detector | Classifier remains pattern based |
| Prompt injection from uploaded data | medium/high | Demo uses only synthetic controlled inputs | File-upload data untrusted handling not designed |
| Overstated AI accuracy | high/high | Explicit NOT RUN reporting | Live LLM and human gold grading required |
| Model expense | medium/medium | Max 20 live eval calls/run + workflow call cap | No live token or cost accounting |
| Browser stale output | medium/medium | Clear previous result on new run | Browser UAT required |
| Multi-user data isolation | medium/high | Demo local only | Auth/multi-tenancy not implemented |
| Confidential materials | high/high | Synthetic only, no private records | GitHub final scan/manual review |
