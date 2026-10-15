"""Deterministic market-microstructure features and causal time alignment."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .data_loader import add_datetime_and_sort, validate_required_columns


def safe_imbalance(bid: pd.Series, ask: pd.Series) -> pd.Series:
    den = bid + ask
    return (bid - ask).div(den.where(den != 0))


def add_bid_ask_imbalance(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["bid_ask_imba"] = safe_imbalance(out["bid1q"], out["ask1q"])
    bid_depth = out[[f"bid{i}q" for i in range(1, 6)]].sum(axis=1)
    ask_depth = out[[f"ask{i}q" for i in range(1, 6)]].sum(axis=1)
    out["bid_depth_5"] = bid_depth
    out["ask_depth_5"] = ask_depth
    out["obi5"] = safe_imbalance(bid_depth, ask_depth)
    out["spread"] = out["ask1p"] - out["bid1p"]
    mid = (out["bid1p"] + out["ask1p"]) / 2
    out["mid_price"] = mid
    out["relative_spread"] = out["spread"].div(mid.where(mid != 0))
    return out


def reshape_bid1p_wide(df_snapshot: pd.DataFrame) -> pd.DataFrame:
    return df_snapshot.set_index(["date", "time", "id"])["bid1p"].unstack("id").rename_axis(columns=None).reset_index()


def merge_trade_snapshot(df_snapshot: pd.DataFrame, df_trade: pd.DataFrame, max_staleness_seconds: float | None = 60) -> pd.DataFrame:
    """Backward as-of join, individually by stock and date. Never matches future trades.

    A finite staleness limit defaults to 60s and marks stale observations missing;
    cumulative fields are NOT silently set to zero for missing trade history.
    """
    if max_staleness_seconds is not None and max_staleness_seconds < 0:
        raise ValueError("max_staleness_seconds must be nonnegative")
    snap = add_datetime_and_sort(df_snapshot.drop(columns=["datetime"], errors="ignore"))
    trades = add_datetime_and_sort(df_trade.drop(columns=["datetime"], errors="ignore"))
    validate_required_columns(trades, ["last", "cum_amount", "cum_volume"])
    if snap.duplicated(["id", "date", "datetime"]).any(): raise ValueError("Duplicate snapshot keys")
    if trades.duplicated(["id", "date", "datetime"]).any(): raise ValueError("Duplicate trade keys")
    aligned = []
    for key, s in snap.groupby(["id", "date"], sort=False):
        t = trades.loc[(trades["id"] == key[0]) & (trades["date"] == key[1]), ["datetime", "cum_volume", "cum_amount", "last"]].copy()
        t = t.rename(columns={"datetime": "trade_datetime"}).sort_values("trade_datetime")
        joined = pd.merge_asof(s.sort_values("datetime"), t, left_on="datetime", right_on="trade_datetime", direction="backward",
            tolerance=pd.Timedelta(seconds=max_staleness_seconds) if max_staleness_seconds is not None else None)
        joined["trade_observed"] = joined["datetime"].eq(joined["trade_datetime"])
        joined["trade_age_seconds"] = (joined["datetime"] - joined["trade_datetime"]).dt.total_seconds()
        aligned.append(joined)
    if not aligned: return snap.assign(trade_datetime=pd.NaT, cum_volume=np.nan, cum_amount=np.nan, last=np.nan, trade_observed=False, trade_age_seconds=np.nan)
    out = pd.concat(aligned, ignore_index=True).sort_values(["id", "date", "datetime"]).reset_index(drop=True)
    if len(out) != len(snap): raise RuntimeError("Unexpected loss of snapshot rows")
    return out


def add_price_features(df: pd.DataFrame, rolling_window: int = 10) -> pd.DataFrame:
    out = df.sort_values(["id", "date", "datetime"]).copy()
    group = out.groupby(["id", "date"], sort=False)["last"]
    out["high"] = group.cummax()
    out["low"] = group.cummin()
    out["rollingLastMean"] = group.transform(lambda x: x.rolling(window=rolling_window, min_periods=min(3, rolling_window)).mean())
    return out
