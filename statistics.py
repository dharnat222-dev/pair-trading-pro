"""
PairTradingPro v1.0
statistics.py

Statistical Engine
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from statsmodels.tsa.stattools import (
    coint,
    adfuller,
)

from config import (
    ROLLING_WINDOW,
)

# ============================================================
# CORRELATION
# ============================================================

def calculate_correlation(
    series1: pd.Series,
    series2: pd.Series,
) -> float:

    returns1 = series1.pct_change().dropna()

    returns2 = series2.pct_change().dropna()

    if len(returns1) < 50 or len(returns2) < 50:
        return np.nan

    return returns1.corr(returns2)


# ============================================================
# ROLLING CORRELATION
# ============================================================

def calculate_rolling_correlation(
    series1: pd.Series,
    series2: pd.Series,
    window: int = ROLLING_WINDOW,
):

    returns1 = series1.pct_change()

    returns2 = series2.pct_change()

    rolling_corr = (
        returns1
        .rolling(window)
        .corr(returns2)
    )

    return rolling_corr


# ============================================================
# COINTEGRATION
# ============================================================

def calculate_cointegration(
    series1: pd.Series,
    series2: pd.Series,
):

    try:

        score, pvalue, _ = coint(
            series1,
            series2,
        )

        return score, pvalue

    except Exception:

        return np.nan, 1.0


# ============================================================
# BETA / HEDGE RATIO
# ============================================================

def calculate_beta(
    series1: pd.Series,
    series2: pd.Series,
):

    try:

        X = sm.add_constant(series2)

        model = sm.OLS(
            series1,
            X,
        ).fit()

        beta = model.params.iloc[1]

        alpha = model.params.iloc[0]

        return beta, alpha

    except Exception:

        return np.nan, np.nan

# ============================================================
# ADF TEST
# ============================================================

def calculate_adf(
    spread: pd.Series,
):

    try:

        result = adfuller(
            spread.dropna(),
            autolag="AIC",
        )

        adf_stat = result[0]

        pvalue = result[1]

        return adf_stat, pvalue

    except Exception:

        return np.nan, 1.0


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
# HALF LIFE
# ============================================================

def calculate_half_life(
    spread:

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
# MEAN REVERSION SCORE
# ============================================================

def calculate_mean_reversion_score(
    correlation: float,
    coint_pvalue: float,
    adf_pvalue: float,
    hurst: float,
):

    score = 0

    if correlation >= 0.90:
        score += 30
    elif correlation >= 0.80:
        score += 25
    elif correlation >= 0.70:
        score += 20

    if coint_pvalue <= 0.01:
        score += 30
    elif coint_pvalue <= 0.05:
        score += 25
    elif coint_pvalue <= 0.10:
        score += 20

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

    return min(score, 100)


# ============================================================
# RISK REWARD
# ============================================================

def calculate_risk_reward(
    entry_spread: float,
    target_spread: float,
    stop_spread: float,
):

    reward = abs(
        target_spread - entry_spread
    )

    risk = abs(
        stop_spread - entry_spread
    )

    if risk == 0:
        return np.nan

    return reward / risk


# ============================================================
# VALIDATE PAIR
# ============================================================

def validate_pair(
    correlation,
    rolling_corr,
    coint_pvalue,
    adf_pvalue,
    beta,
):

    if np.isnan(correlation):
        return False

    if np.isnan(beta):
        return False

    if correlation < 0.70:
        return False

    if rolling_corr < 0.60:
        return False

    if coint_pvalue > 0.05:
        return False

    if adf_pvalue > 0.05:
        return False

    if beta < 0.50 or beta > 1.50:
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
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("PairTradingPro Statistics Engine")
    print("=" * 60)

    s1 = pd.Series(
        np.random.normal(
            100,
            2,
            300
        )
    )

    s2 = pd.Series(
        np.random.normal(
            98,
            2,
            300
        )
    )

    corr = calculate_correlation(
        s1,
        s2
    )

    beta, alpha = calculate_beta(
        s1,
        s2
    )

    spread = calculate_spread