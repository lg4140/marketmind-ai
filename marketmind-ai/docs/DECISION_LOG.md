# MarketMind AI — v1.2 Product Decision Log

| Decision | Alternatives and trade-off | Current evidence | Revisit when |
|---|---|---|---|
| Use typed TaskContract before models | Freeform LLM-only plan easier but unverifiable | Three premature-COMPLETED scenarios turned into explicit tests | Genuine multilingual intent eval shows abstention too high |
| Deterministic conservative intent gate | General LLM classifier more flexible, harder to bound | Local 62 tests; no broad semantic accuracy claim | Human annotated intent corpus >=100 reviewed |
| Server owns AnalysisScope | Model flexibility reduced; prevents unauthorized changes | Scope conflict tests and tool arg rejection | Authenticated multi-dataset permissions available |
| Validate task, not merely calls | Adds typed contract rules | Missing-liquidity/OBI tests | Tool catalog expands |
| Snapshot vs trade-dependent quality | Avoid blocking quoted metrics due to missing trade prints | Policy tests for 0% match | Domain expert calibrates staleness threshold |
| Keep single Agent | Simpler reliability evaluation | No evidence multi-agent materially helps | User task complexity proves need |
| Do not make LLM prose a metric | Limits narrative richness | Evidence-bound claims and typed metrics | Grounded explanation checker is validated |
| Round-robin eval selection | Balanced coverage vs representative task prevalence | 4 samples per category in 20-case dry-run | Real benchmark stratification available |
| Keep SQLite metadata only | Private by default, lacks enterprise observability | Contract + artifact hashes linked to Run ID | Multi-user deployment and retention needs |
| Show not-tested status | Less glossy portfolio but accurate | Model/UX/ROI all still unmeasured | Validated results recorded |
