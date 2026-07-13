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
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# ============================================================
# HEADERS
# ============================================================

HEADERS = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept":
        "*/*",
    "Accept-Encoding":
        "gzip, deflate, br",
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

                symbol_col = None

                for col in df.columns:

                    if "symb" in col.lower():

                        symbol_col = col

                        break

                if symbol_col is None:

                    symbol_col = df.columns[0]

                stocks = df[symbol_col].dropna().unique().tolist()

                if "FinInstrmTp" in df.columns:

                    eq_stocks = (

                        df[
                            df["FinInstrmTp"] == "EQ"
                        ][symbol_col]

                        .dropna()

                        .unique()

                        .tolist()

                    )

                    if eq_stocks:

                        stocks = eq_stocks

                tickers = []

                for stock in stocks:

                    stock = str(stock).strip()

                    if not stock:

                        continue

                    if stock.isdigit():

                        continue

                    if stock in BAD_SYMBOLS:

                        continue

                    tickers.append(
                        stock + ".NS"
                    )

                tickers = sorted(
                    list(
                        set(tickers)
                    )
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

    close_df = pd.DataFrame(close_data)

    volume_df = pd.DataFrame(volume_data)

    if close_df.empty:

        return (
            pd.DataFrame(),
            pd.DataFrame(),
        )

    close_df = close_df.dropna()

    volume_df = volume_df.loc[
        close_df.index
    ]

    common = close_df.columns.intersection(
        volume_df.columns
    )

    close_df = close_df[common]

    volume_df = volume_df[common]

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
        tickers
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
    logger.info(
        "Market Data Ready"
    )
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

    print(
        "TOTAL STOCKS :",
        len(stocks),
    )

    print(
        "PRICE SHAPE :",
        close_df.shape,
    )

    print(
        "VOLUME SHAPE :",
        volume_df.shape,
    )

    print("=" * 60)