"""Readable synthetic-demo research charts; no trading signal claim."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def plot_cumulative_return_liquidity(df_down:pd.DataFrame,stock_id:int,trading_date:int,save_path:str|Path|None=None):
    data=df_down.loc[(df_down["id"]==stock_id)&(df_down["date"]==trading_date)].sort_values("datetime")
    if data.empty: raise ValueError("No data for stock/date")
    data=data.copy()
    fig,(ax,vol)=plt.subplots(2,1,figsize=(12,7),sharex=True,gridspec_kw={"height_ratios":[2,1]},layout="constrained")
    for col,label,c in [("ask1p","Best ask","#2563eb"),("bid1p","Best bid","#f97316")]:
        ax.plot(data["datetime"],100*(data[col]/data[col].iloc[0]-1),marker="o",markersize=3,lw=1.8,label=label,color=c)
    ax.axhline(0,color="#64748b",linestyle="--",lw=.9)
    ax.set_title(f"Best-quote returns and displayed depth | stock {stock_id} | {trading_date}",fontweight="semibold")
    ax.set_ylabel("Cumulative quote return (%)")
    ax.grid(alpha=.17)
    ax.legend(frameon=False,ncol=2)
    # Short grouped bars aligned at the same sampling timestamps
    interval_width=pd.Timedelta(minutes=2)
    bw=interval_width/pd.Timedelta(days=1)
    vol.bar(data["datetime"]-interval_width/2,data["ask1q"]/1000,width=bw,label="Best ask depth",color="#2563eb",alpha=.80)
    vol.bar(data["datetime"]+interval_width/2,data["bid1q"]/1000,width=bw,label="Best bid depth",color="#f97316",alpha=.80)
    vol.set_ylabel("Displayed quantity (thousands)")
    vol.set_xlabel("End of time bucket (local dataset time)")
    vol.legend(frameon=False,ncol=2)
    vol.grid(axis="y",alpha=.17)
    vol.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    fig.text(.02,.004,"Synthetic data only | bucket-end snapshot, not cumulative traded volume",color="#64748b",fontsize=8)
    if save_path:
        path=Path(save_path);path.parent.mkdir(parents=True,exist_ok=True);fig.savefig(path,dpi=160,bbox_inches="tight")
    return fig,(ax,vol)
