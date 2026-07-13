"""
PairTradingPro v1.0
backtest.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from itertools import combinations
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

from config import (
    ENTRY_Z,
    EXIT_Z,
    STOP_Z,
    MAX_HOLD_DAYS,
    MAX_WORKERS,
    OUTPUT_DIR,
)

from data_loader import (
    load_market_data,
)

from statistics import (
    calculate_beta,
    calculate_spread,
    calculate_zscore,
)

# ============================================================
# BACKTEST ONE PAIR
# ============================================================

def backtest_pair(

    ticker1: str,
    ticker2: str,
    close_prices: pd.DataFrame,

):

    s1 = close_prices[ticker1]

    s2 = close_prices[ticker2]

    beta, _ = calculate_beta(
        s1,
        s2,
    )

    if np.isnan(beta):
        return None

    spread = calculate_spread(
        s1,
        s2,
        beta,
    )

    rolling_mean = (
        spread
        .rolling(60)
        .mean()
    )

    rolling_std = (
        spread
        .rolling(60)
        .std()
    )

    zscore = (
        spread
        - rolling_mean
    ) / rolling_std

    trades = []

    in_trade = False

    entry_date = None

    entry_spread = None

    direction = None

    for i in range(
        60,
        len(spread),
    ):

        current_z = zscore.iloc[i]

        if np.isnan(current_z):
            continue

        if not in_trade:

            if current_z >= ENTRY_Z:

                in_trade = True

                direction = "SHORT"

                entry_date = spread.index[i]

                entry_spread = spread.iloc[i]

                continue

            if current_z <= -ENTRY_Z:

                in_trade = True

                direction = "LONG"

                entry_date = spread.index[i]

                entry_spread = spread.iloc[i]

                continue

        else:

            exit_trade = False

            exit_reason = ""

            if abs(current_z) <= EXIT_Z:

                exit_trade = True

                exit_reason = "TARGET"

            elif abs(current_z) >= STOP_Z:

                exit_trade = True

                exit_reason = "STOPLOSS"

            elif (
                spread.index[i] - entry_date
            ).days >= MAX_HOLD_DAYS:

                exit_trade = True

                exit_reason = "TIME EXIT"

            if exit_trade:

                exit_spread = spread.iloc[i]

                if direction == "LONG":

                    pnl = (
                        exit_spread
                        - entry_spread
                    )

                else:

                    pnl = (
                        entry_spread
                        - exit_spread
                    )

                trades.append({

                    "Ticker1": ticker1,

                    "Ticker2": ticker2,

                    "Direction": direction,

                    "EntryDate": entry_date,

                    "ExitDate": spread.index[i],

                    "EntrySpread": round(
                        entry_spread,
                        4,
                    ),

                    "ExitSpread": round(
                        exit_spread,
                        4,
                    ),

                    "PnL": round(
                        pnl,
                        4,
                    ),

                    "ExitReason": exit_reason,

                })

                in_trade = False

                direction = None

                entry_date = None

                entry_spread = None

    if len(trades) == 0:

        return None

    return pd.DataFrame(trades)

# ============================================================
# RUN BACKTEST
# ============================================================

def run_backtest():

    _, close_prices, _ = load_market_data()

    if close_prices.empty:

        print("No market data found.")

        return

    pairs = list(
        combinations(
            close_prices.columns,
            2,
        )
    )

    print(f"Pairs To Test : {len(pairs):,}")

    results = []

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS,
    ) as executor:

        futures = {

            executor.submit(
                backtest_pair,
                t1,
                t2,
                close_prices,
            ): (t1, t2)

            for t1, t2 in pairs

        }

        processed = 0

        for future in as_completed(futures):

            try:

                trades = future.result()

                if trades is not None:

                    results.append(trades)

            except Exception:

                pass

            processed += 1

            if processed % 500 == 0:

                print(
                    f"Processed {processed:,}/{len(pairs):,}"
                )

    if not results:

        print("No backtest trades found.")

        return

    trades_df = pd.concat(
        results,
        ignore_index=True,
    )

    summary = (

        trades_df

        .groupby(
            [
                "Ticker1",
                "Ticker2",
            ]
        )

        .agg(

            Trades=("PnL", "count"),

            TotalPnL=("PnL", "sum"),

            AvgPnL=("PnL", "mean"),

            WinRate=("PnL",
                     lambda x:
                     round(
                         (x > 0).mean() * 100,
                         2,
                     )
            ),

        )

        .reset_index()

        .sort_values(
            "TotalPnL",
            ascending=False,
        )

    )

    OUTPUT_DIR.mkdir(
        exist_ok=True,
    )

    trades_df.to_excel(

        OUTPUT_DIR /
        "backtest_trades.xlsx",

        index=False,

    )

    summary.to_excel(

        OUTPUT_DIR /
        "backtest_summary.xlsx",

        index=False,

    )

    print()

    print("=" * 60)

    print("BACKTEST COMPLETE")

    print("=" * 60)

    print(
        f"Pairs Tested : {len(summary)}"
    )

    print(
        f"Trades : {len(trades_df)}"
    )

    print("=" * 60)

    print()

    print(
        summary.head(10).to_string(
            index=False
        )
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_backtest()