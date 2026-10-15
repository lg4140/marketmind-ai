# MarketMind AI v1.2 — PRD / Task-Verified Research Agent

**版本** v1.2 | **类型** AI Agent PM 作品集 + 可运行研究原型 | **数据** Seeded synthetic limit-order-book | **阶段** 本地代码验收通过，真实模型/用户/浏览器 UAT 未完成。

## 1. 产品机会与定位

高频订单簿分析需要重复清洗、对齐、指标、事件和解释。单纯 Notebook 对非程序化分析不友好，但并非所有查询都需要 LLM。MarketMind AI 针对**多步骤、可被工具验证的描述性市场微观结构研究**提供研究协作：系统根据明确意图选择只读计算工具，验证数据和任务完整性，形成带证据的报告。产品不提供实时行情、投资建议、买卖执行或真实交易收益分析。

## 2. 用户与待验证 JTBD

- 初级量化研究员：想要“不写重复脚本也能完成 Spread/OBI 和报告”，验收为正确指标+可追溯来源。
- 金融数据分析师：想要“发现错误或过期成交并限制分析”，验收为正确的 BLOCK/WARN 与问题定位。
- 研究审阅者：想要“知道 Agent 回答了哪些问题、哪些没完成”，验收为 Task Contract、Evidence 和 Limitations 一致。

以上均为**产品假设**，没有真实用户访谈证据。访谈设计见 `USER_RESEARCH_PLAN_CN.md`。

## 3. Agent 必要性与替代方案

| Task | Default solution | Agent need |
|---|---|---|
| 固定 Spread/OBI 查询 | deterministic tool / UI button | 低 |
| 预设图表输出 | fixed workflow | 低 |
| 多指标 + 事件 + 条件化解释 | bounded Agent orchestrator | 中高 |
| 模糊研究问题 | clarify before execution | 中 |
| 越权修改 Scope | reject/ask authorization | 不应自主完成 |

首版兼容确定性离线基准，避免把每项简单计算都强迫走 LLM。

## 4. 用户任务流程

配置授权股票/交易日期/时间/桶长 → 输入明确研究请求 → 系统生成 TaskContract（可检查）→ 质量门控 → 只读工具执行 → 任务验证 → 输出报告与证据 → Run ID 追踪 → 用户反馈。若请求模糊，先要求补全而不是用模型编造范围；若任务不完整，显示缺少的工具/指标/图表。

## 5. 功能矩阵、验收条件与优先级

| ID | P | Feature | Acceptance |
|---|---|---|---|
| F01 | P0 | Typed Task Contract | 需要的工具/指标/产物是机器可读的；不明确时 ABSTAIN |
| F02 | P0 | Semantic Completion Gate | 仅调用不相关工具时不得 COMPLETED；profile-only 可正确 COMPLETED |
| F03 | P0 | Scope Integrity | 用户文本和 LLM 工具参数与授权范围冲突不得静默改写 |
| F04 | P0 | Task-aware Data Quality | Snapshot BLOCK，非依赖 Trade 的报价研究可 WARN，Trade 依赖可 BLOCK |
| F05 | P0 | Evidence Claims | 所有数值来自对应 Tool+Scope+Dataset，限制说明保留 |
| F06 | P0 | Balanced Evaluation Sampling | 20 条评测 dry-run 能产生五类各 4 条 |
| F07 | P0 | Safety & Budget | 只读工具白名单，有限轮数/调用数，超限不标记完成 |
| F08 | P1 | UI Truthful States | 新任务清除旧结果，展示 TaskContract、证据、错误及 Run ID |
| F09 | P1 | Execution Lineage | 保存工具步骤、TaskContract、图表 SHA-256 及反馈关联 |
| F10 | P1 | Product Evidence | 访谈/对照实验/真实 LLM 评测需收集后更新，不伪造效果 |

## 6. 非功能性要求

只读、synthetic-only、不会使用实时或未经授权的交易数据；不上传专有原始 CSV、笔试材料、招聘信息、API Key。异常报告不得显示完成。所有模型生成的数字不作为数据源，调用结果经范围验证。当前项目仅为本地原型；多用户权限、机密管理、日志保留、成本计量、断点续跑均尚未达生产级。

## 7. KPI 与量化口径

**North Star**: Verified Task Completion Rate = 经过任务/证据独立验证的完成任务数 / 所有合格任务数。不是“执行成功的工具次数 / 工具调用数”。诊断指标：必需工具召回率、无关调用率、关键指标证据覆盖、数据门控正确率、scope-conflict 识别率、失败原因清晰率。下一阶段真实模型执行记录包括 P50/P95、输入/输出 Token、成本/成功任务；目前均 **NOT MEASURED**。

## 8. 发布门槛、用户研究与约束

- v1.2 本地工程验收：62 个 pytest、45 个离线案例、100 用例 Schema 校验、20-case balanced selection（详见验证报告）。
- 真实 LLM：先在 5 类场景做限额试运行，修复失败，再进行人工复核；未完成前不得声称真实模型成功率。
- UAT：关键路径与失败路径浏览器实测；现阶段只完成代码层状态隔离。
- 用户研究：5–8 人访谈、Notebook-vs-Agent 同条件任务实验；实验结果须有真实记录。
- v1.3 候选：适配多轮澄清、覆盖更多语言意图、完整性能成本 telemetry；不要先堆 Multi-Agent。

## 9. 项目治理

Owner 角色：PM 负责场景与验收；工程负责工具/状态与日志；量化专家负责指标定义和异常阈值；评审者负责人机评估。原始 v1.0、v1.1 文档保留在 archives，避免版本口径混淆。详细矩阵见 `TASK_CONTRACT_SPEC.md`、`RELEASE_READINESS_CHECKLIST.md`。
