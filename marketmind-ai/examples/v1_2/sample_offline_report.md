# MarketMind AI | Verified Synthetic Research
**Run ID:** `1adaf0b4-573b-476d-87a8-0404977eef61`
**Status:** COMPLETED; **Mode:** offline-deterministic
**Data:** synthetic-demo-seed-42
**Authorized scope:** {'stock_id': 1, 'trading_date': 20210104, 'start_time': '09:40', 'end_time': '10:30', 'interval_minutes': 10}

## Tool-derived metrics
- **bid_quote_return_pct:** -1.48571429 %  — evidence: `analyze_microstructure` / `synthetic-demo-seed-42`
- **ask_quote_return_pct:** -1.47079823 %  — evidence: `analyze_microstructure` / `synthetic-demo-seed-42`
- **mean_spread:** 0.03492507 price units  — evidence: `analyze_microstructure` / `synthetic-demo-seed-42`
- **mean_relative_spread_bps:** 5.02231656 bps  — evidence: `analyze_microstructure` / `synthetic-demo-seed-42`
- **mean_best_level_imbalance:** -0.00704317 ratio  — evidence: `analyze_microstructure` / `synthetic-demo-seed-42`
- **mean_obi5:** -0.00136576 ratio  — evidence: `analyze_microstructure` / `synthetic-demo-seed-42`
- **mean_bid_depth_5:** 22526.002997 shares  — evidence: `analyze_microstructure` / `synthetic-demo-seed-42`
- **mean_ask_depth_5:** 22629.36463536 shares  — evidence: `analyze_microstructure` / `synthetic-demo-seed-42`
- **candidate_new_visible_levels:** 3514 candidate levels  — evidence: `analyze_liquidity_events` / `synthetic-demo-seed-42`

## Warnings
- Offline is a fixed baseline; no LLM used and no natural language intent parsing.

## Limitations
- All observations are seeded synthetic data, not live or historical market facts.
- Bid/ask quote changes are not trading returns or causal evidence.
- Candidate visible price levels do not establish order placement or queue position.

## Generated artifacts
- `reports/generated/stock_1_20210104_0940_1030_10m_1adaf0b4-573b-476d-87a8-0404977eef61.png`

All numeric metrics above are copied from validated, scope-matched Python tool outputs. Model free text is not used as a numeric source.
