"""
PairTradingPro v1.0
statistics.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from statsmodels.tsa.stattools import coint, adfuller

from config import (
    ROLLING_WINDOW,
    MIN_CORRELATION,
    MIN_ROLLING_CORRELATION,
    MAX_COINTEGRATION_PVALUE,
    MAX_ADF_PVALUE,
    MIN_BETA,
    MAX_BETA,
)


def calculate_correlation(series1: pd.Series,
                          series2: pd.Series) -> float:

    r1 = series1.pct_change().dropna()
    r2 = series2.pct_change().dropna()

    if len(r1) < 50 or len(r2) < 50:
        return np.nan

    return float(r1.corr(r2))


def calculate_rolling_correlation(series1: pd.Series,
                                  series2: pd.Series,
                                  window: int = ROLLING_WINDOW):

    r1 = series1.pct_change()
    r2 = series2.pct_change()

    return r1.rolling(window).corr(r2)


def calculate_cointegration(series1: pd.Series,
                            series2: pd.Series):

    try:

        score, pvalue, _ = coint(series1, series2)

        return float(score), float(pvalue)

    except Exception:

        return np.nan, 1.0


def calculate_beta(series1: pd.Series,
                   series2: pd.Series):

    try:

        X = sm.add_constant(series2)

        model = sm.OLS(series1, X).fit()

        beta = float(model.params.iloc[1])

        alpha = float(model.params.iloc[0])

        return beta, alpha

    except Exception:

        return np.nan, np.nan

# ============================================================
# SPREAD
# ============================================================

def calculate_spread(
    series1: pd.Series,
    series2: pd.Series,
    beta: float,
):

    return series1 - (beta * series2)


# ============================================================
# ADF TEST
# ============================================================

def calculate_adf(
    spread: pd.Series,
):

    try:

        adf_stat, pvalue, *_ = adfuller(
            spread.dropna(),
            autolag="AIC",
        )

        return float(adf_stat), float(pvalue)

    except Exception:

        return np.nan, 1.0


# ============================================================
# HALF LIFE
# ============================================================

def calculate_half_life(
    spread: pd.Series,
):

    try:

        spread_lag = spread.shift(1).dropna()

        spread_diff = spread.diff().dropna()

        spread_lag = spread_lag.loc[
            spread_diff.index
        ]

        X = sm.add_constant(
            spread_lag
        )

        model = sm.OLS(
            spread_diff,
            X,
        ).fit()

        theta = model.params.iloc[1]

        if theta >= 0:
            return np.inf

        return float(
            -np.log(2) / theta
        )

    except Exception:

        return np.inf


# ============================================================
# Z SCORE
# ============================================================

def calculate_zscore(
    spread: pd.Series,
    window: int = ROLLING_WINDOW,
):

    rolling_mean = (
        spread
        .rolling(window)
        .mean()
    )

    rolling_std = (
        spread
        .rolling(window)
        .std()
    )

    if rolling_mean.dropna().empty:
        return np.nan

    last_mean = rolling_mean.iloc[-1]

    last_std = rolling_std.iloc[-1]

    if pd.isna(last_std) or last_std == 0:
        return np.nan

    return float(
        (spread.iloc[-1] - last_mean)
        / last_std
    )

# ============================================================
# HURST EXPONENT
# ============================================================

def calculate_hurst(
    spread: pd.Series,
    max_lag: int = 20,
):

    try:

        values = spread.dropna().values

        if len(values) < 100:
            return np.nan

        lags = range(2, max_lag)

        tau = []

        valid_lags = []

        for lag in lags:

            diff = values[lag:] - values[:-lag]

            std = np.std(diff)

            if std > 0:

                tau.append(np.sqrt(std))

                valid_lags.append(lag)

        if len(tau) < 5:
            return np.nan

        hurst = np.polyfit(
            np.log(valid_lags),
            np.log(tau),
            1
        )[0] * 2.0

        return float(hurst)

    except Exception:

        return np.nan


# ============================================================
# VALIDATE PAIR
# ============================================================

def validate_pair(
    correlation: float,
    rolling_corr: float,
    coint_pvalue: float,
    adf_pvalue: float,
    beta: float,
):

    if np.isnan(correlation):
        return False

    if np.isnan(rolling_corr):
        return False

    if np.isnan(beta):
        return False

    if correlation < MIN_CORRELATION:
        return False

    if rolling_corr < MIN_ROLLING_CORRELATION:
        return False

    if coint_pvalue > MAX_COINTEGRATION_PVALUE:
        return False

    if adf_pvalue > MAX_ADF_PVALUE:
        return False

    if beta < MIN_BETA:
        return False

    if beta > MAX_BETA:
        return False

    return True


# ============================================================
# TRADE SIGNAL
# ============================================================

def get_trade_signal(
    zscore: float,
):

    if np.isnan(zscore):
        return "NO TRADE", "NO TRADE"

    if zscore >= 2.0:
        return "SELL", "BUY"

    if zscore <= -2.0:
        return "BUY", "SELL"

    return "NO TRADE", "NO TRADE"

# ============================================================
# MEAN REVERSION SCORE
# ============================================================

def calculate_mean_reversion_score(
    correlation: float,
    coint_pvalue: float,
    adf_pvalue: float,
    hurst: float,
    half_life: float,
):

    score = 0

    if correlation >= 0.90:
        score += 25
    elif correlation >= 0.85:
        score += 20
    elif correlation >= 0.80:
        score += 15
    elif correlation >= 0.70:
        score += 10

    if coint_pvalue <= 0.01:
        score += 20
    elif coint_pvalue <= 0.05:
        score += 15
    elif coint_pvalue <= 0.10:
        score += 10

    if adf_pvalue <= 0.01:
        score += 20
    elif adf_pvalue <= 0.05:
        score += 15
    elif adf_pvalue <= 0.10:
        score += 10

    if not np.isnan(hurst):

        if hurst < 0.40:
            score += 20
        elif hurst < 0.50:
            score += 15
        elif hurst < 0.60:
            score += 10

    if half_life < 20:
        score += 15
    elif half_life < 40:
        score += 10
    elif half_life < 60:
        score += 5

    return min(score, 100)


# ============================================================
# POSITION SIZE
# ============================================================

def get_position_size(
    volatility: float,
):

    if np.isnan(volatility):
        return "SMALL"

    if volatility <= 0.20:
        return "LARGE"

    if volatility <= 0.35:
        return "MEDIUM"

    return "SMALL"


# ============================================================
# TRADE QUALITY
# ============================================================

def get_trade_quality(
    score: float,
):

    if score >= 90:
        return "A+"

    if score >= 80:
        return "A"

    if score >= 70:
        return "B+"

    if score >= 60:
        return "B"

    return "C"


# ============================================================
# RISK REWARD
# ============================================================

def calculate_risk_reward(
    entry_spread: float,
    target_spread: float,
    stop_spread: float,
):

    reward = abs(target_spread - entry_spread)

    risk = abs(stop_spread - entry_spread)

    if risk == 0:
        return np.nan

    return reward / risk


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("PairTradingPro Statistics Engine Loaded Successfully")
    print("=" * 60)