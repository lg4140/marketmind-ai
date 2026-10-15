# MarketMind AI v1.2 — 中文运行手册

在解压后的仓库根目录运行：

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m evaluation.run_evals
python -m evaluation.validate_llm_cases
python -m evaluation.select_cases --max-cases 20
python run_demo.py --mode offline
```

`offline` 是固定流程，不理解自然语言也不调用模型。若需 UI：`python -m pip install -r requirements-ui.txt` 和 `streamlit run app/streamlit_app.py`。若需真实模型：`python -m pip install -r requirements-agent.txt`，在终端安全设置 `OPENAI_API_KEY`，并用 `python run_demo.py --mode llm --question "Analyze spread and five-level OBI"`；这会产生 API 费用，需要可联网的环境，不属于本次验证结果。

评测前仅预览分层选择：`python -m evaluation.select_cases --max-cases 20`。付费测试必须明确同意、准备人工审查，运行 `python -m evaluation.run_llm_evals --confirm-live --max-cases 20 --model YOUR_MODEL`。`--max-cases` 不超过 20，防止一次性消耗过多。切勿把密钥、原始保密行情、招聘材料上传到 GitHub。

常见解释：`INCOMPLETE` 表示必需结果缺失或问题不明确，不是成功；`SCOPE_CONFLICT` 表示文字/工具参数与授权范围不一致；`WARN` 表示特定依赖数据质量不足，但不一定妨碍独立报价分析。
