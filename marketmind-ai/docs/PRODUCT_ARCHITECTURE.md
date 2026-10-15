# MarketMind AI v1.2 | 产品技术架构与执行安全边界

## 1. 产品架构

`Streamlit / CLI` → `AnalysisScope (server authorization)` → `Task Planner (rule-based TaskContract)` → `Validation + Task-aware Quality Gate` → `LLM Tool Selector (optional)` → `allowlisted Python tools` → `TaskVerifier` → `ResearchReport (metric-based claims)` → `RunStore / feedback / artifacts`.

**设计取舍**：有明确数学定义的指标一律由 Python 计算。LLM（可选）仅进行工具选择，不得成为数字来源。固定离线模式仍是面向回归测试的工作流，不是自主 Agent。此项目目前仍为同步单任务架构，非生产多用户部署。

## 2. 执行路径和主要接口

| Stage | Main file | Deterministic contract |
|---|---|---|
| Request | `tools/market_tools.py` | Pydantic `AnalysisScope`, stock/date/time/interval enforced |
| Intent | `agents/task_planner.py` | `TaskContract`; unsupported or unclear tasks abstain |
| Validation | `verification/quality_gate.py` | quote-only data requirements vs optional trade dependencies |
| Tool choice | `agents/workflow.py` | five allowlisted functions, call and round budgets |
| Analytics | `src/` and `tools/market_tools.py` | price/OBI/spread/depth/events/charts computed in Python |
| Finish | `verification/task_verifier.py` | required tools + metrics + artifact refs check |
| Report | `schemas/research_report.py` | metrics tied to same dataset, scope and tool output |
| History | `agents/run_store.py` | SQLite run, steps, feedback and metadata hash fields |

## 3. Authorization invariant

Scope is always server owned. The LLM can request an allowlisted tool and optionally echo scope parameters; changes to `stock_id`, `trading_date`, `start_time`, `end_time`, or `interval_minutes` are rejected. Unknown tool fields are rejected. Dataset strings, uploaded text and tool results are untrusted as instructions. No broker, live data, arbitrary Python or secrets tool exists.

## 4. Data quality dependencies

Snapshot anomalies including duplicates, invalid prices/quantities and invalid levels can BLOCK quote-related analysis. Absent or insufficiently aligned trade records WARN for quote-only tasks, but BLOCK trade-dependent research (`require_trade=True`, default threshold 80%). **There is currently no trade-dependent Agent tool**: its gating behavior is verified through policy unit tests, not a complete trade research workflow. Quality thresholds and calendars require domain validation before real data deployment.

## 5. Completion invariants

A run can be `COMPLETED` only when all contract-required tools succeed and required numerical fields/artifacts exist. A successful irrelevant tool is insufficient. Models cannot supply arbitrary numeric claims. `profile_dataset` alone may legitimately complete a coverage task; a liquidity request cannot be satisfied by spread calculations alone. `CLAIM` objects record metric evidence and limitations, but do **not** establish causality or proof for arbitrary free-form conclusions.

## 6. States, recovery and failure handling

Current final states: `COMPLETED`, `INCOMPLETE`, `FAILED`, `BLOCKED`; `PARTIAL` remains a reserved Schema status. `NEEDS_CLARIFICATION`, `UNSUPPORTED_ACTION`, and `SCOPE_CONFLICT` are contract decisions mapped to final workflow states. Failure reason and trace are inspectable. Tool rounds/calls/time are bounded, but **there is no durable async checkpoint, cancellation or model-token budget**. These remain P1/P2.

## 7. Observability and risk

RunStore tracks step timings, tool results metadata, task-contract version, optional model identifier and SHA-256 of existing chart artifacts. It does not currently persist prompt tokens, token cost, raw messages, model sampling settings, user login, encryption or retention policy enforcement. Report lineage for failing runs retains the instantiated toolbox dataset ID rather than assuming seed 42.

## 8. Why not Multi-Agent / RAG now?

The scarce risk is not number of agents but correctness of a single task. Multi-Agent adds coordination/failure surfaces; RAG is useful only when grounded document retrieval is a validated user need. Reconsider after live Evals and user interviews. For fixed metrics, deterministic UI controls may be preferable to an LLM.
