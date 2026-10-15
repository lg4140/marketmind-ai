# MarketMind AI v1.2 — 产品指标字典与用户实验计划

> 全部未标记为“本地验证”的数值仅是提议指标和实验设计；没有真实用户行为数据。

## 1. North Star 指标与质量漏斗

`Verified Research Task Completion Rate = 满足任务且全部关键数值有证据、范围合法、状态为COMPLETED的任务数 / 有明确成功判据的有效任务数`。

漏斗：发起任务 → Scope 合法 → 质量 PASS/WARN → 必需分析工具成功 → Evidence report 合格 → 用户验收。统计按用户类型、任务难度、模型版本、失败阶段分组；不能通过筛掉失败任务人为抬高完成率。

## 2. 指标定义与埋点设计

| 指标 | 分子/分母或计算规则 | 数据源 | 风险 |
|---|---|---|---|
| Task Success | 验证通过的任务/全部有效任务 | 人工 Evals + `runs` | 自动状态不等于语义成功 |
| Tool Accuracy | 正确必要调用/期望必要工具 | Tool Trace + Gold Set | 多余调用也应扣分 |
| Claim Accuracy | 被独立计算确认的定量陈述/审查的全部定量陈述 | Metrics vs Python Oracle | 无证据数字属于 FAIL |
| Evidence Coverage | 可追溯的关键声明/全部关键声明 | ResearchReport | 定义关键声明清单 |
| P50/P95 Latency | 从提交到完成的端到端秒数 | UI/API Run Timings | 网络与缓存混杂 |
| Cost / Successful Task | 全部运行 Token、计算和部署成本 / 成功任务数 | 计费日志+RunStore | 不能只算成功调用费用 |
| Rework Rate | 需人工返工的任务数/完成任务数 | 用户任务观察 | 事先定义何为返工 |
| Unsupported Action Rate | 未授权执行次数/违规请求数 | 安全用例 + Trace | 必须为 0，含工具级越权 |

当前 SQLite 只持久化运行元数据、工具步骤与反馈；尚未完整埋点 Token 用量、P95、用户会话和产物 checksum，相关指标目前不可计算。

## 3. Notebook vs Agent 对照实验（待实施）

**研究问题：** 使用 Agent 是否在不牺牲正确性的前提下减少人工步骤及完成时间？

**人群：** 5–8 名有基础市场数据知识的研究员/分析师；使用匿名参与编号，不在公共仓库保存个人身份信息。

**设计：** Within-subject crossover，A/B 任务同难度，随机分配先用 Notebook 或先用 Agent，限制同一研究范围并使用同一合成数据。先练习 5 分钟再开始测试，记录完成时间、操作次数、数值错误、用户自行修复次数、证据理解测试题与主观信任评分。

**成功判定：** 两条件任务均按同一黄金指标与口径评分；任务错误首先视为失败，不应只比较速度。对小样本报告中位数和个体差值，不宣称有统计显著性或代表全行业。

**待填写模板：** Participant ID / Task A or B / Order / Mode / Time sec / Tool actions / Errors / Rework / Evidence comprehension / Interview notes。未执行前不得填写虚构数字。

## 4. 决策触发

- 如果实际 Agent 工具选择成功率不足预期，则优先修复分类与提示词/工具定义，而不是引入多 Agent。
- 如果用户仍需要频繁解释查询范围，则优化 Scope/Intent 澄清流程和 UI。
- 如果 Agent 完成速度快但数值错误更多，先保证正确性，不把速度优势当作发布依据。
- 如果大部分用户只需 1–2 个固定指标，考虑将常见任务做成一键按钮，而不是强制使用 LLM。

**结果状态：** 当前尚未开展实验。任何效能提升、复用率、留存和商业收入都不能在简历上作为实测成果引用。


## v1.2 任务层指标修订

`COMPLETED` 由 `TaskVerifier` 对 Required Tools + Required Metrics + Required Artifacts 进行静态验收；这不是人类用户对真实研究完成的独立验收。规则式意图识别必须另测 coverage/abstention rate；真实模型的工具选择仍为 NOT RUN。RunStore 新增合同元数据与图表摘要，但 Token、费用及 P95 尚未埋点。
