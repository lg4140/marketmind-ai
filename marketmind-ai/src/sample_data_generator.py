from __future__ import annotations

import numpy as np
import pandas as pd

from .data_loader import add_datetime_and_sort


def _make_book_side(
    top_price: float,
    side: str,
    rng: np.random.Generator,
    tick: float = 0.01,
) -> dict[str, float]:
    """Create five bid or ask price levels with occasional price gaps."""
    levels = {1: round(top_price, 2)}
    current = top_price

    for level in range(2, 6):
        # Randomly use 1-3 ticks to create realistic gaps between price levels.
        step = int(rng.integers(1, 4)) * tick
        current = current - step if side == "bid" else current + step
        levels[level] = round(current, 2)

    return levels


def generate_synthetic_market_data(
    n_stocks: int = 3,
    dates: list[int] | None = None,
    n_snapshots: int = 1200,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate synthetic high-frequency snapshot and trade data.

    The default snapshot frequency is 3 seconds and trade records are created
    every 5 snapshots, resulting in a 15-second trade frequency. The generated
    data follows the same general schema as limit order book snapshot and trade
    datasets, but it is not based on any proprietary data.
    """
    rng = np.random.default_rng(seed)

    if dates is None:
        dates = [20210104]

    snapshot_rows = []
    trade_rows = []

    for trading_date in dates:
        base_date = pd.to_datetime(str(trading_date), format="%Y%m%d")
        times = pd.date_range(
            base_date + pd.Timedelta(hours=9, minutes=30, seconds=3),
            periods=n_snapshots,
            freq="3s",
        )

        for stock_id in range(1, n_stocks + 1):
            mid = 50 + stock_id * 20 + rng.normal(0, 0.5)
            cum_volume = 0
            cum_amount = 0.0

            for idx, dt in enumerate(times):
                mid += rng.normal(0, 0.015)
                spread = 0.02 + rng.uniform(0, 0.03)
                tick = 0.01

                bid1 = round(mid - spread / 2, 2)
                ask1 = round(mid + spread / 2, 2)

                # Ensure ask1 is strictly greater than bid1.
                if ask1 <= bid1:
                    ask1 = round(bid1 + tick, 2)

                bid_levels = _make_book_side(bid1, "bid", rng, tick=tick)
                ask_levels = _make_book_side(ask1, "ask", rng, tick=tick)

                row = {
                    "id": stock_id,
                    "date": trading_date,
                    "time": dt.strftime("%H:%M:%S"),
                }

                for level in range(5, 0, -1):
                    row[f"bid{level}p"] = bid_levels[level]
                for level in range(1, 6):
                    row[f"ask{level}p"] = ask_levels[level]

                for level in range(5, 0, -1):
                    row[f"bid{level}q"] = int(rng.integers(100, 9000))
                for level in range(1, 6):
                    row[f"ask{level}q"] = int(rng.integers(100, 9000))

                snapshot_rows.append(row)

                # Lower-frequency trade records: one trade every 5 snapshots = 15 seconds.
                if idx % 5 == 0:
                    last = float(rng.choice([bid_levels[1], bid_levels[2], ask_levels[1], ask_levels[2], round(mid, 2)]))
                    volume = int(rng.integers(100, 5000))
                    cum_volume += volume
                    cum_amount += volume * last

                    trade_rows.append(
                        {
                            "id": stock_id,
                            "date": trading_date,
                            "time": dt.strftime("%H:%M:%S"),
                            "cum_volume": cum_volume,
                            "cum_amount": int(cum_amount),
                            "last": last,
                        }
                    )

    df_snapshot = add_datetime_and_sort(pd.DataFrame(snapshot_rows))
    df_trade = add_datetime_and_sort(pd.DataFrame(trade_rows))

    return df_snapshot, df_trade
