"""Market data ingestion and safe, structured data quality diagnostics.

Diagnostics are stable even when prices/quantities arrive as malformed strings.
The quality *policy* (BLOCK/WARN) is applied separately in verification.quality_gate.
"""
from __future__ import annotations
from pathlib import Path
from typing import Iterable
import numpy as np
import pandas as pd

KEY_COLUMNS = ['id', 'date', 'time']
SNAPSHOT_COLUMNS = KEY_COLUMNS + [f'{side}{i}{suffix}' for side in ('bid', 'ask') for i in range(1, 6) for suffix in ('p', 'q')]
TRADE_COLUMNS = KEY_COLUMNS + ['cum_volume', 'cum_amount', 'last']


def validate_required_columns(df: pd.DataFrame, required_columns: Iterable[str]) -> None:
    missing = sorted(set(required_columns) - set(df.columns))
    if missing:
        raise ValueError(f'Missing required columns: {missing}')


def add_datetime_and_sort(df: pd.DataFrame) -> pd.DataFrame:
    validate_required_columns(df, KEY_COLUMNS)
    out = df.copy()
    parsed = pd.to_datetime(out['date'].astype(str) + ' ' + out['time'].astype(str), errors='coerce')
    if parsed.isna().any():
        raise ValueError(f'Invalid date/time in {int(parsed.isna().sum())} row(s)')
    out['datetime'] = parsed
    return out.sort_values(['id', 'date', 'datetime'], kind='stable').reset_index(drop=True)


def read_all_csv(folder: str | Path) -> pd.DataFrame:
    files = sorted(Path(folder).rglob('*.csv'))
    if not files:
        raise FileNotFoundError(f'No CSV files found under {folder}')
    frames = []
    for file in files:
        frame = pd.read_csv(file)
        frames.append(frame.loc[:, ~frame.columns.str.match(r'^Unnamed:')])
    return add_datetime_and_sort(pd.concat(frames, ignore_index=True))


def validate_market_data(df: pd.DataFrame, kind: str = 'generic') -> dict:
    """Return diagnostic issues; *never* coerce invalid input into apparently valid output.

    Does not silently drop/repair rows. Malformed level strings are returned as issues
    rather than throwing during float array conversion. Missing schema is a hard error.
    """
    validate_required_columns(df, KEY_COLUMNS)
    report = {
        'rows': int(len(df)), 'columns': int(len(df.columns)),
        'duplicated_keys': int(df.duplicated(KEY_COLUMNS).sum()),
        'missing_values': {str(k): int(v) for k, v in df.isna().sum().items()},
        'kind': kind, 'issues': [],
    }
    issues = report['issues']
    if not len(df):
        issues.append({'code': 'empty_dataset', 'count': 0})
    if report['duplicated_keys']:
        issues.append({'code': 'duplicate_key', 'count': report['duplicated_keys']})
    if kind in ('snapshot', 'trade'):
        validate_required_columns(df, SNAPSHOT_COLUMNS if kind == 'snapshot' else TRADE_COLUMNS)
        price_cols = ([f'{s}{i}p' for s in ('bid', 'ask') for i in range(1, 6)] if kind == 'snapshot' else ['last'])
        qty_cols = ([f'{s}{i}q' for s in ('bid', 'ask') for i in range(1, 6)] if kind == 'snapshot' else ['cum_volume', 'cum_amount'])
        converted = {}
        for col in price_cols + qty_cols:
            values = pd.to_numeric(df[col], errors='coerce')
            converted[col] = values
            bad = values.isna() | ~np.isfinite(values) | (values <= 0 if col in price_cols else values < 0)
            count = int(bad.sum())
            if count:
                issues.append({'code': 'invalid_price' if col in price_cols else 'invalid_quantity',
                               'field': col, 'count': count})
        if kind == 'snapshot':
            bid = pd.DataFrame({i: converted[f'bid{i}p'] for i in range(1, 6)}).to_numpy(dtype=float)
            ask = pd.DataFrame({i: converted[f'ask{i}p'] for i in range(1, 6)}).to_numpy(dtype=float)
            numeric_rows = np.isfinite(bid).all(axis=1) & np.isfinite(ask).all(axis=1)
            invalid = numeric_rows & (
                np.any(np.diff(bid, axis=1) >= 0, axis=1) |
                np.any(np.diff(ask, axis=1) <= 0, axis=1) | (bid[:, 0] >= ask[:, 0])
            )
            if invalid.any():
                issues.append({'code': 'crossed_or_invalid_levels', 'count': int(invalid.sum())})
        else:
            try:
                ordered = add_datetime_and_sort(df)
            except ValueError:
                issues.append({'code': 'invalid_timestamp', 'count': int(len(df))})
            else:
                for field in ('cum_volume', 'cum_amount'):
                    numbers = pd.to_numeric(ordered[field], errors='coerce')
                    delta = numbers.groupby([ordered['id'], ordered['date']]).diff()
                    count = int((delta < 0).sum())
                    if count:
                        issues.append({'code': 'non_monotonic_cumulative', 'field': field, 'count': count})
    report['passed'] = not issues
    return report
