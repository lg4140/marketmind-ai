# Synthetic Market Data Card

**Dataset ID:** `synthetic-demo-seed-42`  
**Source:** `src/sample_data_generator.py` (same synthetic generator code as sanitized supplied project)  
**Purpose:** verify calculation, tool schema, orchestration, visualization and UX  
**Not:** licensed real-time data; market backtest; real stock quote history; evidence of investment alpha.

## Generation settings

| Property | Value |
|---|---|
| Seed | 42 |
| Stocks | IDs 1, 2, 3 |
| Dates | 20210104 (synthetic date label only) |
| Snapshot cadence | 3 seconds |
| Trade record cadence | 15 seconds |
| Snapshots per stock | 1200 |
| Total snapshot records | 3600 |
| Total trade records | 720 |
| Depth | Five bid and five ask price/quantity levels |

Generated snapshots include per-level `bid1p…bid5p`, `ask1p…ask5p`, `bid1q…bid5q`, `ask1q…ask5q`. Trade records include `cum_volume`, `cum_amount`, and `last`. `id,date,time` plus a generated `datetime` identify observations.

## Limitations

- Brownian-like synthetic mid-price changes and random displayed quantities are not calibrated to any exchange or historical instrument.
- Some price-level patterns can appear plausible but do not represent real order-arrival, execution, cancellations or priority queues.
- `cum_amount` uses rounded generated amounts; appropriate only for demonstration of cumulative field handling.
- Sample covers one synthetic morning; no overnight, DST, auction, cross-market, outage, corporate action or price-limit cases.
- Dataset size is suitable for local demos only; it is not evidence of scaling to enterprise data volumes.

## Privacy and publishing

No proprietary stock identifiers, employer records, recruiter information, original assessment prompts or confidential files are needed to reproduce the project. The GitHub `.gitignore` excludes CSV/parquet/PDF as an additional check but is **not** a substitute for manual secret/data review. Ensure that prior git commits do not contain private data before publication.
