"""Trade-position classification and *candidate* new visible level detection.

Snapshot transitions cannot prove order-level additions/cancels or queue positions.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

FREE_HOLE_COLUMNS=["id","date","time","side","price_level","price","quantity","sizeInFront"]


def classify_last_price(df: pd.DataFrame, observed_only: bool = True) -> pd.DataFrame:
    out=df.copy()
    valid = out["last"].notna()
    if observed_only:
        if "trade_observed" not in out: raise ValueError("trade_observed column required to avoid stale-trade classification")
        valid &= out["trade_observed"].fillna(False)
    last=out["last"]
    category=pd.Series(pd.NA,index=out.index,dtype="Int64")
    category.loc[valid & (out["bid1p"]<last) & (last<out["ask1p"])]=0
    for i in range(1,5):
        category.loc[valid & (out[f"bid{i+1}p"]<last) & (last<=out[f"bid{i}p"])]=-i
        category.loc[valid & (out[f"ask{i}p"]<=last) & (last<out[f"ask{i+1}p"])]=i
    category.loc[valid & (last<=out["bid5p"])]=-5
    category.loc[valid & (last>=out["ask5p"])]=5
    out["last_category"]=category
    return out


def category_proportions(df:pd.DataFrame)->pd.DataFrame:
    valid=df.loc[df["last_category"].notna()]
    if valid.empty: return pd.DataFrame(columns=range(-5,6),dtype=float)
    table=pd.crosstab(valid["id"],valid["last_category"],normalize="index")
    return table.reindex(columns=range(-5,6),fill_value=0)


def detect_free_hole_additions(df_snapshot:pd.DataFrame)->pd.DataFrame:
    """Return *candidate* new visible prices, not confirmed individual orders."""
    base=df_snapshot.sort_values(["id","date","datetime"]).copy()
    price_cols=[f"{s}{i}p" for s in ("bid","ask") for i in range(1,6)]
    for c in price_cols:
        base[f"prev_{c}"]=base.groupby(["id","date"],sort=False)[c].shift(1)
    matches=[]
    for side in ("bid","ask"):
        low=base[f"prev_{side}{5 if side=='bid' else 1}p"]
        high=base[f"prev_{side}{1 if side=='bid' else 5}p"]
        for i in range(1,6):
            price=base[f"{side}{i}p"]
            qty=base[f"{side}{i}q"]
            in_range=(price>low)&(price<high)
            unseen=pd.Series(True,index=base.index)
            for j in range(1,6):
                unseen &= ~pd.Series(np.isclose(price,base[f"prev_{side}{j}p"],atol=1e-9,rtol=0,equal_nan=False),index=base.index)
            mask=in_range & unseen & (qty>0)
            if not mask.any(): continue
            part=base.loc[mask,["id","date","time"]].copy()
            part["side"],part["price_level"]=side,i
            part["price"],part["quantity"]=price.loc[mask].to_numpy(),qty.loc[mask].to_numpy()
            part["sizeInFront"]=(sum((base[f"{side}{j}q"] for j in range(1,i)),start=pd.Series(0,index=base.index))).loc[mask].to_numpy()
            matches.append(part)
    if not matches: return pd.DataFrame(columns=FREE_HOLE_COLUMNS)
    return pd.concat(matches,ignore_index=True)[FREE_HOLE_COLUMNS]
