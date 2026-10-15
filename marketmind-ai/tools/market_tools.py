"""Whitelisted, read-only market research tools for the Agent runtime."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Literal
import json
from uuid import uuid4
from verification.quality_gate import classify_quality, require_acceptable
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, model_validator
from src.data_loader import validate_market_data
from src.sample_data_generator import generate_synthetic_market_data
from src.feature_engineering import add_bid_ask_imbalance, merge_trade_snapshot, add_price_features
from src.resampling import downsample_market_data
from src.order_book_analysis import classify_last_price, detect_free_hole_additions
from src.visualization import plot_cumulative_return_liquidity
import matplotlib.pyplot as plt

TOOLS = ["profile_dataset", "validate_dataset", "analyze_microstructure", "analyze_liquidity_events", "generate_chart"]

class AnalysisScope(BaseModel):
    stock_id: int = Field(ge=1, description="A synthetic stock ID")
    trading_date: int = Field(ge=20000101, le=20991231, description="YYYYMMDD")
    start_time: str = Field(description="HH:MM")
    end_time: str = Field(description="HH:MM")
    interval_minutes: int = Field(default=10, ge=1, le=60)

    @model_validator(mode="after")
    def check_time(self):
        try:
            day = datetime.strptime(str(self.trading_date), "%Y%m%d")
            start=datetime.strptime(self.start_time,"%H:%M").time()
            end=datetime.strptime(self.end_time,"%H:%M").time()
        except ValueError as exc:
            raise ValueError("trading_date must be YYYYMMDD and times HH:MM") from exc
        if start>=end: raise ValueError("start_time must precede end_time")
        return self


def to_jsonable(item):
    return json.loads(json.dumps(item, default=lambda x: x.isoformat() if hasattr(x,"isoformat") else (x.item() if isinstance(x,np.generic) else str(x)),allow_nan=False))

class MarketToolbox:
    def __init__(self, output_dir: str | Path = "reports/generated", seed: int=42):
        self.output_dir=Path(output_dir)
        snap, trade=generate_synthetic_market_data(n_stocks=3,dates=[20210104],n_snapshots=1200,seed=seed)
        self.snapshot=add_bid_ask_imbalance(snap)
        self.trade=trade
        self.merged=add_price_features(merge_trade_snapshot(self.snapshot,trade,max_staleness_seconds=60))
        self.dataset_id=f"synthetic-demo-seed-{seed}"

    def subset(self, scope:AnalysisScope, source:str="snapshot") -> pd.DataFrame:
        df=self.snapshot if source=="snapshot" else self.merged
        start=pd.Timestamp(f"{scope.trading_date} {scope.start_time}")
        end=pd.Timestamp(f"{scope.trading_date} {scope.end_time}")
        matched=df.loc[(df["id"]==scope.stock_id)&(df["date"]==scope.trading_date)&df["datetime"].between(start,end)].copy()
        if matched.empty: raise ValueError(f"No records for stock={scope.stock_id}, date={scope.trading_date}, range={scope.start_time}-{scope.end_time}")
        return matched

    def execute(self, tool_name:str, payload:dict)->dict:
        if tool_name not in TOOLS: raise ValueError(f"Tool not allowed: {tool_name}")
        scope=AnalysisScope.model_validate(payload)
        subset=self.subset(scope)
        # A direct tool invocation may not bypass validation.
        if tool_name not in ('profile_dataset', 'validate_dataset'):
            quality=self.execute('validate_dataset', scope.model_dump())['result']
            require_acceptable(quality,require_trade=False)
        evidence={"dataset":self.dataset_id,"stock_id":scope.stock_id,"trading_date":scope.trading_date,
                  "start_time":scope.start_time,"end_time":scope.end_time,"interval_minutes":scope.interval_minutes,"source_rows":int(len(subset)),
                  "data_kind":"synthetic","tool":tool_name}
        if tool_name=="profile_dataset":
            result={"stocks_available":[int(i) for i in sorted(self.snapshot["id"].unique())],
                    "date_available":[int(i) for i in sorted(self.snapshot["date"].unique())],
                    "records_in_scope":len(subset),"snapshot_update_seconds":3,"trade_update_seconds":15}
        elif tool_name=="validate_dataset":
            s=validate_market_data(subset,kind="snapshot")
            tr=self.trade.loc[(self.trade.id==scope.stock_id)&(self.trade.date==scope.trading_date)&self.trade.datetime.between(subset.datetime.min(),subset.datetime.max())]
            t=validate_market_data(tr,kind="trade") if len(tr) else {"passed":False,"issues":[{"code":"no_trades_in_window"}]}
            m=self.subset(scope,source="merged")
            result={"snapshot_quality":s,"trade_quality":t,"trade_match_rate":round(float(m["trade_datetime"].notna().mean()),6),
                    "exact_trade_match_rate":round(float(m["trade_observed"].mean()),6),"unmatched_snapshot_rows":int(m["last"].isna().sum())}
            result['quality_gate'] = classify_quality(result,require_trade=False)
        elif tool_name=="analyze_microstructure":
            d=self.subset(scope,source="merged")
            first,last=d.iloc[0],d.iloc[-1]
            def f(x): return round(float(x),8) if pd.notna(x) else None
            result={"n_snapshots":len(d),"first_timestamp":str(first.datetime),"last_timestamp":str(last.datetime),
                    "bid_quote_return_pct":f(100*(last.bid1p/first.bid1p-1)),"ask_quote_return_pct":f(100*(last.ask1p/first.ask1p-1)),
                    "mean_spread":f(d.spread.mean()),"mean_relative_spread_bps":f(d.relative_spread.mean()*10000),
                    "mean_best_level_imbalance":f(d.bid_ask_imba.mean()),"mean_obi5":f(d.obi5.mean()),
                    "mean_bid_depth_5":f(d.bid_depth_5.mean()),"mean_ask_depth_5":f(d.ask_depth_5.mean()),
                    "caution":"Descriptive quote/depth metrics; no causal effect or trading signal implied."}
        elif tool_name=="analyze_liquidity_events":
            # Include one preceding snapshot for correct boundary comparison; only count events in requested range.
            full=self.snapshot.loc[(self.snapshot.id==scope.stock_id)&(self.snapshot.date==scope.trading_date)]
            events=detect_free_hole_additions(full)
            if not events.empty:
                event_dt=pd.to_datetime(events["date"].astype(str)+" "+events["time"].astype(str))
                begin=pd.Timestamp(f"{scope.trading_date} {scope.start_time}")
                finish=pd.Timestamp(f"{scope.trading_date} {scope.end_time}")
                events=events.loc[event_dt.between(begin,finish)]
            counts=events.groupby("side").size().to_dict() if not events.empty else {}
            result={"candidate_new_visible_levels":int(len(events)),"by_side":{"bid":int(counts.get("bid",0)),"ask":int(counts.get("ask",0))},
                    "example_rows":to_jsonable(events.head(3).to_dict("records")),
                    "methodology":"A current visible price absent from prior top-5 levels, inside prior side range; not confirmed new orders/queue position."}
        elif tool_name=="generate_chart":
            merged=self.subset(scope,source="merged")
            down=downsample_market_data(merged,interval_minutes=scope.interval_minutes)
            # Unique per run, including sampling interval; never silently overwrite a prior artifact.
            run_id = str(payload.get('_run_id') or uuid4())
            filename=(f"stock_{scope.stock_id}_{scope.trading_date}_"
                      f"{scope.start_time.replace(':','')}_{scope.end_time.replace(':','')}_"
                      f"{scope.interval_minutes}m_{run_id}.png")
            path=self.output_dir/filename
            fig,_=plot_cumulative_return_liquidity(down,scope.stock_id,scope.trading_date,path)
            plt.close(fig)
            result={"image_path":str(path),"interval_minutes":scope.interval_minutes,"buckets":int(len(down)),
                    "note":"Bars show last snapshot best-level depth per interval; not trading volume."}
        return to_jsonable({"status":"ok","evidence":evidence,"result":result})


def function_schemas():
    base=AnalysisScope.model_json_schema()
    return [{"type":"function","function":{"name":t,"description":{
        "profile_dataset":"Check what synthetic data and timestamps are covered in a selected scope",
        "validate_dataset":"Validate LOB schema, duplicates, cumulative trades and alignment coverage",
        "analyze_microstructure":"Compute spread, top-five OBI, depth and descriptive quote returns",
        "analyze_liquidity_events":"Count CANDIDATE newly visible LOB price levels, not orders",
        "generate_chart":"Generate chart of quote returns and best-level depth"
    }[t],"parameters":base}} for t in TOOLS]
