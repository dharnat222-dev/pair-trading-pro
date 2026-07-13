"""
PairTradingPro v1.0
scanner.py
"""

from __future__ import annotations

from itertools import combinations
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

import traceback
import numpy as np
import pandas as pd

from config import (
    MAX_WORKERS,
    TOP_PAIRS,
    OUTPUT_DIR,
    MIN_ZSCORE,
    MAX_VOLATILITY,
    MIN_AVG_VOLUME,
    ROLLING_WINDOW,
)

from data_loader import (
    load_market_data,
)

from statistics import (
    calculate_correlation,
    calculate_rolling_correlation,
    calculate_cointegration,
    calculate_beta,
    calculate_spread,
    calculate_adf,
    calculate_half_life,
    calculate_hurst,
    calculate_zscore,
    calculate_mean_reversion_score,
    calculate_risk_reward,
    validate_pair,
    get_trade_signal,
    get_position_size,
    get_trade_quality,
)


# ============================================================
# ANALYZE ONE PAIR
# ============================================================

def analyze_pair(
    ticker1: str,
    ticker2: str,
    close_prices: pd.DataFrame,
    volume_data: pd.DataFrame,
):

    try:

        s1 = close_prices[ticker1]

        s2 = close_prices[ticker2]

        correlation = calculate_correlation(
            s1,
            s2,
        )

        if np.isnan(correlation):
            return None

        rolling_corr = calculate_rolling_correlation(
            s1,
            s2,
            ROLLING_WINDOW,
        )

        if rolling_corr.dropna().empty:
            return None

        rolling_last = float(
            rolling_corr.dropna().iloc[-1]
        )

        _, coint_pvalue = calculate_cointegration(
            s1,
            s2,
        )

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

        _, adf_pvalue = calculate_adf(
            spread,
        )

        if not validate_pair(
            correlation,
            rolling_last,
            coint_pvalue,
            adf_pvalue,
            beta,
        ):
            return None

        half_life = calculate_half_life(
            spread,
        )

        hurst = calculate_hurst(
            spread,
        )

        zscore = calculate_zscore(
            spread,
            ROLLING_WINDOW,
        )

        if np.isnan(zscore):
            return None

        if abs(zscore) < MIN_ZSCORE:
            return None

        volatility = float(
            s1.pct_change().std()
            * np.sqrt(252)
        )

        if np.isnan(volatility):
            return None

        if volatility > MAX_VOLATILITY:
            return None

        avg_volume1 = float(
            volume_data[ticker1]
            .tail(20)
            .mean()
        )

        avg_volume2 = float(
            volume_data[ticker2]
            .tail(20)
            .mean()
        )

        if (
            avg_volume1 < MIN_AVG_VOLUME
            or
            avg_volume2 < MIN_AVG_VOLUME
        ):
            return None

        action1, action2 = get_trade_signal(
            zscore,
        )

        score = calculate_mean_reversion_score(
            correlation,
            coint_pvalue,
            adf_pvalue,
            hurst,
            half_life,
        )

        trade_quality = get_trade_quality(
            score,
        )

        position_size = get_position_size(
            volatility,
        )

        rolling_mean = (
            spread
            .rolling(ROLLING_WINDOW)
            .mean()
            .iloc[-1]
        )

        rolling_std = (
            spread
            .rolling(ROLLING_WINDOW)
            .std()
            .iloc[-1]
        )

        if pd.isna(rolling_mean) or pd.isna(rolling_std):
            return None

        entry_spread = float(
            spread.iloc[-1]
        )

        target_spread = float(
            rolling_mean
        )

        if entry_spread > target_spread:

            stop_spread = (
                entry_spread
                + (2 * rolling_std)
            )

        else:

            stop_spread = (
                entry_spread
                - (2 * rolling_std)
            )

        risk_reward = calculate_risk_reward(
            entry_spread,
            target_spread,
            stop_spread,
        )

        if np.isnan(risk_reward):
            risk_reward = 0.0

        return {

            "Ticker1": ticker1,
            "Action1": action1,

            "Ticker2": ticker2,
            "Action2": action2,

            "Correlation": round(correlation, 4),

            "RollingCorrelation": round(
                rolling_last,
                4,
            ),

            "CointegrationPValue": round(
                coint_pvalue,
                4,
            ),

            "ADFPValue": round(
                adf_pvalue,
                4,
            ),

            "Beta": round(
                beta,
                4,
            ),

            "HalfLife": round(
                half_life,
                2,
            ),

            "Hurst": round(
                hurst,
                4,
            ),

            "ZScore": round(
                zscore,
                2,
            ),

            "Volatility": round(
                volatility,
                4,
            ),

            "AverageVolume1": int(avg_volume1),

            "AverageVolume2": int(avg_volume2),

            "EntrySpread": round(
                entry_spread,
                4,
            ),

            "TargetSpread": round(
                target_spread,
                4,
            ),

            "StopSpread": round(
                stop_spread,
                4,
            ),

            "RiskReward": round(
                risk_reward,
                2,
            ),

            "Score": round(
                score,
                2,
            ),

            "TradeQuality": trade_quality,

            "PositionSize": position_size,

        }

    except Exception:

        return None


# ============================================================
# RUN SCANNER
# ============================================================

def run_scanner():

    tickers, close_prices, volume_data = load_market_data()

    if close_prices.empty:

        print("No market data found.")

        return pd.DataFrame()

    pairs = list(
        combinations(
            close_prices.columns,
            2,
        )
    )

    print(
        f"Stocks Loaded : {len(close_prices.columns)}"
    )

    print(
        f"Pairs To Scan : {len(pairs):,}"
    )

    results = []
    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS,
    ) as executor:

        futures = {

            executor.submit(
                analyze_pair,
                t1,
                t2,
                close_prices,
                volume_data,
            ): (t1, t2)

            for t1, t2 in pairs

        }

        processed = 0

        for future in as_completed(futures):

            result = future.result()

            if result is not None:

                results.append(result)

            processed += 1

            if processed % 500 == 0:

                print(
                    f"Processed {processed:,}/{len(pairs):,}"
                )

    if not results:

        print("No qualified pairs found.")

        return pd.DataFrame()

    df = pd.DataFrame(results)

    df.sort_values(
        by=[
            "Score",
            "RiskReward",
            "ZScore",
        ],
        ascending=False,
        inplace=True,
    )

    OUTPUT_DIR.mkdir(
        exist_ok=True,
    )

    df.to_excel(
        OUTPUT_DIR / "pair_signals.xlsx",
        index=False,
    )

    df.head(
        TOP_PAIRS,
    ).to_excel(
        OUTPUT_DIR / "pair_signals_top10.xlsx",
        index=False,
    )

    print()
    print("=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)
    print(f"Qualified Pairs : {len(df)}")
    print(f"Top {TOP_PAIRS} Pairs Saved")
    print("=" * 60)

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PairTradingPro Scanner")
    print("=" * 60)

    df = run_scanner()

    if not df.empty:

        print()

        print(
            df.head(
                TOP_PAIRS
            ).to_string(
                index=False
            )
        )


if __name__ == "__main__":

    main()
