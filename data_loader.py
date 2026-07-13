"""
PairTradingPro v1.0
data_loader.py

Handles:
- NSE F&O List
- Yahoo Finance Data Download
- Data Validation
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

# ----------------------------------------------------
# Logger
# ----------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ----------------------------------------------------
# NSE Headers
# ----------------------------------------------------

HEADERS = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept":
        "*/*",
    "Accept-Encoding":
        "gzip, deflate, br",
}


# ----------------------------------------------------
# Download Latest NSE F&O List
# ----------------------------------------------------

def get_latest_fno_list():

    logger.info("Downloading latest NSE F&O list...")

    for days_back in range(10):

        date = datetime.now() - timedelta(days=days_back)

        date_string = date.strftime("%Y%m%d")

        url = (
            f"https://nsearchives.nseindia.com/content/fo/"
            f"BhavCopy_NSE_FO_0_0_0_{date_string}_F_0000.csv.zip"
        )

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30
            )

            if response.status_code != 200:
                continue

            with zipfile.ZipFile(
                io.BytesIO(response.content)
            ) as zip_file:

                csv_name = zip_file.namelist()[0]

                with zip_file.open(csv_name) as csv_file:

                    df = pd.read_csv(csv_file)

            symbol_column = None

            for col in df.columns:

                if "symb" in col.lower():
                    symbol_column = col
                    break

            if symbol_column is None:
                continue

            symbols = (
                df[symbol_column]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            tickers = []

            for symbol in symbols:

                symbol = symbol.strip()

                if symbol:

                    tickers.append(symbol + ".NS")

            logger.info(
                "Loaded %d F&O Stocks",
                len(tickers)
            )

            return sorted(list(set(tickers)))

        except Exception:

            continue

    logger.warning(
        "Unable to download NSE list."
    )

    return []
# ----------------------------------------------------
# Batch Price Download
# ----------------------------------------------------

def download_price_data(
    tickers,
    lookback_days=LOOKBACK_DAYS,
):
    """
    Download historical OHLCV data
    """

    if len(tickers) == 0:
        return pd.DataFrame(), pd.DataFrame()

    end_date = datetime.today()

    start_date = end_date - timedelta(days=lookback_days)

    logger.info(
        "Downloading %d stocks...",
        len(tickers)
    )

    try:

        data = yf.download(
            tickers=tickers,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            auto_adjust=True,
            progress=True,
            group_by="ticker",
            threads=True
        )

    except Exception as e:

        logger.error(e)

        return pd.DataFrame(), pd.DataFrame()

    close_data = {}
    volume_data = {}

    for ticker in tickers:

        try:

            close = data[ticker]["Close"]

            volume = data[ticker]["Volume"]

            if len(close.dropna()) < MIN_HISTORY:
                continue

            name = ticker.replace(".NS", "")

            close_data[name] = close

            volume_data[name] = volume

        except Exception:

            continue

    close_df = pd.DataFrame(close_data)

    volume_df = pd.DataFrame(volume_data)

    close_df = close_df.dropna(axis=1)

    volume_df = volume_df.dropna(axis=1)

    common = close_df.columns.intersection(
        volume_df.columns
    )

    close_df = close_df[common]

    volume_df = volume_df[common]

    logger.info(
        "Loaded %d Stocks",
        len(common)
    )

    return close_df, volume_df


# ----------------------------------------------------
# Complete Loader
# ----------------------------------------------------

def load_market_data():

    tickers = get_latest_fno_list()

    if len(tickers) == 0:

        logger.error(
            "F&O List Empty"
        )

        return (
            [],
            pd.DataFrame(),
            pd.DataFrame()
        )

    close_df, volume_df = download_price_data(
        tickers
    )

    return (
        tickers,
        close_df,
        volume_df
    )