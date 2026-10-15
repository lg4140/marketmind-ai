"""Interval-end LOB aggregation with explicit bin semantics."""
from __future__ import annotations
import numpy as np
import pandas as pd


def coefficient_of_variation(x: pd.Series) -> float:
    x=x.dropna()
    return float(x.std(ddof=1) / x.mean()) if len(x) > 1 and x.mean() != 0 else (0.0 if len(x) == 1 else np.nan)


def count_price_changes(x: pd.Series) -> int:
    return int(x.diff().ne(0).iloc[1:].sum())


def _realized_quote_vol(x: pd.Series) -> float:
    x=x.dropna()
    if len(x) < 2 or (x<=0).any(): return np.nan
    return float(np.sqrt(np.square(np.diff(np.log(x.to_numpy(dtype=float)))).sum()))


def downsample_one_group(key, group: pd.DataFrame, interval_minutes: int = 10) -> pd.DataFrame:
    if not isinstance(interval_minutes, int) or not 1 <= interval_minutes <= 60: raise ValueError("interval_minutes must be between 1 and 60")
    ordered=group.sort_values("datetime").set_index("datetime")
    r=ordered.resample(f"{interval_minutes}min", closed="right", label="right")
    out=r.last()
    out["maxBid1p"]=r["bid1p"].max()
    out["minBid1p"]=r["bid1p"].min()
    out["timesBid1pChanged"]=r["bid1p"].apply(count_price_changes)
    out["coefBid1p"]=r["bid1p"].apply(coefficient_of_variation)
    out["bid1p_realized_quote_vol"]=r["bid1p"].apply(_realized_quote_vol)
    out["observations"]=r["bid1p"].count()
    out=out.dropna(subset=["bid1p"]).reset_index()
    out["id"],out["date"]=key
    out["time"]=out["datetime"].dt.strftime("%H:%M:%S")
    return out


def downsample_market_data(df: pd.DataFrame, interval_minutes: int=10) -> pd.DataFrame:
    parts=[downsample_one_group(k,g,interval_minutes) for k,g in df.groupby(["id","date"],sort=False)]
    if not parts: return pd.DataFrame()
    return pd.concat(parts,ignore_index=True).sort_values(["id","date","datetime"]).reset_index(drop=True)
