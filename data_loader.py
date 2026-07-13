"""
PairTradingPro v1.0
data_loader.py
"""

from __future__ import annotations

import io
import logging
import zipfile
from datetime import datetime, timedelta

import pandas as pd
import requests
import yfinance as yf

from config import (
    LOOKBACK_DAYS,
    MIN_HISTORY,
)

# ============================================================
# LOGGER
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

# ============================================================
# REQUEST HEADERS
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/137 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
}

BAD_SYMBOLS = {
    "NIFTY",
    "BANKNIFTY",
    "FINNIFTY",
    "MIDCPNIFTY",
    "NIFTYNXT50",
}

# ============================================================
# DOWNLOAD NSE F&O LIST
# ============================================================

def get_latest_fno_list(days_back: int = 10):

    logger.info("Downloading latest NSE F&O List...")

    for i in range(days_back):

        date = datetime.today() - timedelta(days=i)

        date_str = date.strftime("%Y%m%d")

        urls = [
            f"https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{date_str}_F_0000.csv.zip",
            f"https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{date_str}.csv.zip",
        ]

        for url in urls:

            try:

                response = requests.get(
                    url,
                    headers=HEADERS,
                    timeout=30,
                )

                if response.status_code != 200:
                    continue

                with zipfile.ZipFile(
                    io.BytesIO(response.content)
                ) as z:

                    csv_name = z.namelist()[0]

                    with z.open(csv_name) as f:

                        df = pd.read_csv(f)

                symbol_col = next(
                    (
                        c for c in df.columns
                        if "symb" in c.lower()
                    ),
                    df.columns[0],
                )

                stocks = (
                    df[symbol_col]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .unique()
                    .tolist()
                )

                if "FinInstrmTp" in df.columns:

                    eq = (
                        df[
                            df["FinInstrmTp"] == "EQ"
                        ][symbol_col]
                        .dropna()
                        .astype(str)
                    )

                    if not eq.empty:
                        stocks = eq.unique().tolist()

                tickers = []

                for stock in stocks:

                    stock = stock.strip()

                    if (
                        not stock
                        or stock.isdigit()
                        or stock in BAD_SYMBOLS
                    ):
                        continue

                    tickers.append(
                        f"{stock}.NS"
                    )

                tickers = sorted(
                    set(tickers)
                )

                logger.info(
                    "Loaded %d F&O Stocks",
                    len(tickers),
                )

                return tickers

            except Exception:

                continue

    logger.error(
        "Unable to download NSE F&O List."
    )

    return []

# ============================================================
# DOWNLOAD HISTORICAL PRICE DATA
# ============================================================

def download_price_data(
    tickers: list[str],
    lookback_days: int = LOOKBACK_DAYS,
):

    if not tickers:

        return (
            pd.DataFrame(),
            pd.DataFrame(),
        )

    end_date = datetime.today()

    start_date = (
        end_date
        - timedelta(days=lookback_days)
    )

    logger.info(
        "Downloading historical prices for %d stocks...",
        len(tickers),
    )

    close_data = {}

    volume_data = {}

    failed = []

    success = 0

    total = len(tickers)

    for i, ticker in enumerate(
        tickers,
        start=1,
    ):

        try:

            hist = yf.Ticker(
                ticker
            ).history(

                start=start_date.strftime("%Y-%m-%d"),

                end=end_date.strftime("%Y-%m-%d"),

                interval="1d",

                auto_adjust=True,

            )

            if hist.empty:

                failed.append(
                    ticker
                )

                continue

            hist = hist.tz_localize(None)

            if len(hist) < MIN_HISTORY:

                failed.append(
                    ticker
                )

                continue

            symbol = ticker.replace(
                ".NS",
                "",
            )

            close_data[symbol] = hist[
                "Close"
            ]

            volume_data[symbol] = hist[
                "Volume"
            ]

            success += 1

            if i % 20 == 0:

                logger.info(

                    "Downloaded %d/%d stocks (%d successful)",

                    i,

                    total,

                    success,

                )

        except Exception:

            failed.append(
                ticker
            )

            continue

    logger.info(
        "Successfully loaded %d/%d stocks",
        success,
        total,
    )

    if failed:

        logger.warning(
            "%d symbols skipped",
            len(failed),
        )

    close_df = pd.DataFrame(
        close_data
    )

    volume_df = pd.DataFrame(
        volume_data
    )

    if close_df.empty:

        return (
            pd.DataFrame(),
            pd.DataFrame(),
        )

    # Remove stocks having incomplete history
    close_df = close_df.dropna(
        axis=1,
    )

    volume_df = volume_df.dropna(
        axis=1,
    )

    # Keep only common stocks
    common = close_df.columns.intersection(
        volume_df.columns
    )

    close_df = close_df[
        common
    ]

    volume_df = volume_df[
        common
    ]

    # Keep only common dates
    common_index = close_df.index.intersection(
        volume_df.index
    )

    close_df = close_df.loc[
        common_index
    ]

    volume_df = volume_df.loc[
        common_index
    ]

    return (
        close_df,
        volume_df,
    )

# ============================================================
# LOAD MARKET DATA
# ============================================================

def load_market_data():

    logger.info("=" * 60)
    logger.info("Loading Market Data")
    logger.info("=" * 60)

    tickers = get_latest_fno_list()

    if not tickers:

        logger.error(
            "Unable to load NSE F&O List"
        )

        return (
            [],
            pd.DataFrame(),
            pd.DataFrame(),
        )

    close_df, volume_df = download_price_data(
        tickers=tickers,
    )

    if close_df.empty:

        logger.error(
            "Price data download failed"
        )

        return (
            [],
            pd.DataFrame(),
            pd.DataFrame(),
        )

    logger.info("=" * 60)
    logger.info("Market Data Ready")
    logger.info(
        "Stocks Loaded : %d",
        len(close_df.columns),
    )
    logger.info(
        "Rows Loaded : %d",
        len(close_df),
    )
    logger.info("=" * 60)

    return (
        list(close_df.columns),
        close_df,
        volume_df,
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    stocks, close_df, volume_df = load_market_data()

    print()

    print("=" * 60)
    print("TOTAL STOCKS :", len(stocks))
    print("PRICE SHAPE  :", close_df.shape)
    print("VOLUME SHAPE :", volume_df.shape)
    print("=" * 60)