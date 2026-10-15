# MarketMind AI v1.2 — 交互与发布验收计划

**状态：未执行浏览器验收。** 以 `RELEASE_READINESS_CHECKLIST.md` 的 U01–U12 为正式清单；每一项执行时记录操作者、日期、环境、截图、实际状态、失败 ID、重试结果。

建议先从 `streamlit run app/streamlit_app.py` 的本地场景测试：正常离线与 LLM 分别标识、输入范围不合法、空任务、超 Scope、连续两次运行第二次失败、数据质量异常、图表证据、反馈与导出一致性。用户界面应将 INCOMPLETE/FAILED/BLOCKED 与 COMPLETED 采用不同明确文字解释。关闭数据或权限的操作不可伪造。

测试结果模板：`Case ID | Browser/OS | Expected | Actual | Screenshot | Pass/Fail | Issue ID | Owner | Retest Date`。当前全部为 `NOT TESTED`。
