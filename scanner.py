"""
PairTradingPro v1.0
scanner.py
"""

from itertools import combinations
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
import pandas as pd
import numpy as np

from config import (
    MAX_WORKERS,
    MIN_ZSCORE,
    MAX_VOLATILITY,
    MIN_AVG_VOLUME,
    TOP_PAIRS,
    OUTPUT_DIR,
)

from data_loader import load_market_data

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

        rolling = calculate_rolling_correlation(
            s1,
            s2,
        )

        if rolling.dropna().empty:
            return None

        rolling_corr = rolling.iloc[-1]

        score, coint_p = calculate_cointegration(
            s1,
            s2,
        )

        beta, alpha = calculate_beta(
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

        adf_stat, adf_p = calculate_adf(
            spread,
        )

        if not validate_pair(
            correlation,
            rolling_corr,
            coint_p,
            adf_p,
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
        )

        if np.isnan(zscore):
            return None

        if abs(zscore) < MIN_ZSCORE:
            return None

        volatility = (
            s1.pct_change()
            .std()
            * np.sqrt(252)
        )

        if np.isnan(volatility):
            return None

        if volatility > MAX_VOLATILITY:
            return None

        volume1 = float(
            volume_data[ticker1]
            .tail(20)
            .mean()
        )

        volume2 = float(
            volume_data[ticker2]
            .tail(20)
            .mean()
        )

        if (
            volume1 < MIN_AVG_VOLUME
            or
            volume2 < MIN_AVG_VOLUME
        ):
            return None

        action1, action2 = get_trade_signal(
            zscore
        )

        score = calculate_mean_reversion_score(
            correlation,
            coint_p,
            adf_p,
            hurst,
            half_life,
        )

        quality = get_trade_quality(
            score
        )

        position = get_position_size(
            volatility
        )

        entry = float(spread.iloc[-1])

        target = float(
            spread.rolling(60).mean().iloc[-1]
        )

        std = float(
            spread.rolling(60).std().iloc[-1]
        )

        if entry > target:
            stop = entry + (2 * std)
        else:
            stop = entry - (2 * std)

        rr = calculate_risk_reward(
            entry,
            target,
            stop,
        )

        return {

            "Ticker1": ticker1,
            "Action1": action1,

            "Ticker2": ticker2,
            "Action2": action2,

            "Correlation": round(correlation, 4),
            "RollingCorrelation": round(rolling_corr, 4),

            "CointegrationPValue": round(coint_p, 4),

            "ADFPValue": round(adf_p, 4),

            "Beta": round(beta, 4),

            "HalfLife": round(half_life, 2),

            "Hurst": round(hurst, 4),

            "ZScore": round(zscore, 2),

            "Volatility": round(volatility, 4),

            "AverageVolume1": int(volume1),
            "AverageVolume2": int(volume2),

            "EntrySpread": round(entry, 4),
            "TargetSpread": round(target, 4),
            "StopSpread": round(stop, 4),

            "RiskReward": round(rr, 2),

            "Score": round(score, 2),

            "TradeQuality": quality,

            "PositionSize": position,

        }

    except Exception:

        traceback.print_exc()

        return None


# ============================================================
# RUN SCANNER
# ============================================================

def run_scanner():

    tickers, close_prices, volume_data = load_market_data()

    if close_prices.empty:

        print("No market data loaded.")

        return pd.DataFrame()

    pairs = list(
        combinations(
            close_prices.columns,
            2,
        )
    )

    print(f"Stocks Loaded : {len(close_prices.columns)}")
    print(f"Pairs To Scan : {len(pairs):,}")

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

    if len(results) == 0:

        print("No qualified pairs found.")

        return pd.DataFrame()

    df = pd.DataFrame(results)

    df = df.sort_values(
        by=[
            "Score",
            "RiskReward",
            "ZScore",
        ],
        ascending=False,
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
    print(
        f"Top {TOP_PAIRS} file saved."
    )

    return df


def main():

    print("=" * 60)
    print("PairTradingPro Scanner")
    print("=" * 60)

    df = run_scanner()

    if not df.empty:

        print()

        print(
            df.head(TOP_PAIRS).to_string(
                index=False
            )
        )


if __name__ == "__main__":

    main()