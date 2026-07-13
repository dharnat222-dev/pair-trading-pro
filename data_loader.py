"""
PairTradingPro v1.0
data_loader.py

Downloads:
1. Latest NSE F&O Stock List
2. Historical Price Data
"""

from __future__ import annotations

import io
import logging
import zipfile
from datetime import datetime, timedelta

import pandas as pd
import requests
import yfinance as yf

from config import LOOKBACK_DAYS, MIN_HISTORY

# ============================================================
# LOGGER
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
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

# ============================================================
# BAD SYMBOLS
# ============================================================

BAD_SYMBOLS = {
    "NIFTY",
    "BANKNIFTY",
    "FINNIFTY",
    "MIDCPNIFTY",
    "NIFTYNXT50"
}

# ============================================================
# DOWNLOAD NSE F&O LIST
# ============================================================

def get_latest_fno_list(days_back: int = 10) -> list[str]:

    logger.info("Downloading latest NSE F&O List...")

    for i in range(days_back):

        date = datetime.today() - timedelta(days=i)

        date_str = date.strftime("%Y%m%d")

        urls = [

            f"https://nsearchives.nseindia.com/content/fo/"
            f"BhavCopy_NSE_FO_0_0_0_{date_str}_F_0000.csv.zip",

            f"https://nsearchives.nseindia.com/content/fo/"
            f"BhavCopy_NSE_FO_0_0_0_{date_str}.csv.zip"

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
                    .str.strip()
                    .unique()
                    .tolist()
                )

                tickers = []

                for symbol in symbols:

                    if (
                        symbol == ""
                        or symbol.isdigit()
                        or symbol in BAD_SYMBOLS
                    ):
                        continue

                    tickers.append(symbol + ".NS")

                tickers = sorted(list(set(tickers)))

                logger.info(
                    "Loaded %d F&O Stocks",
                    len(tickers)
                )

                return tickers

            except Exception:

                continue

    logger.warning("Unable to download NSE F&O list.")

    return []

# ============================================================
# DOWNLOAD HISTORICAL PRICE DATA
# ============================================================

def download_price_data(
    tickers: list[str],
    lookback_days: int = LOOKBACK_DAYS,
):

    if not tickers:
        return pd.DataFrame(), pd.DataFrame()

    end_date = datetime.today()

    start_date = end_date - timedelta(days=lookback_days)

    logger.info(
        "Downloading historical prices for %d stocks...",
        len(tickers)
    )

    try:

        data = yf.download(
            tickers=tickers,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=8,
        )

    except Exception as e:

        logger.error(
            "Yahoo download failed : %s",
            e
        )

        return (
            pd.DataFrame(),
            pd.DataFrame(),
        )

    close_data = {}

    volume_data = {}

    failed = []

    for ticker in tickers:

        try:

            close = data[ticker]["Close"]

            volume = data[ticker]["Volume"]

            if len(close.dropna()) < MIN_HISTORY:
                failed.append(ticker)
                continue

            name = ticker.replace(".NS", "")

            close_data[name] = close

            volume_data[name] = volume

        except Exception:

            failed.append(ticker)

    close_df = pd.DataFrame(close_data)

    volume_df = pd.DataFrame(volume_data)

    close_df.dropna(
        axis=1,
        inplace=True,
    )

    volume_df.dropna(
        axis=1,
        inplace=True,
    )

    common = close_df.columns.intersection(
        volume_df.columns
    )

    close_df = close_df[common]

    volume_df = volume_df[common]

    logger.info(
        "Successfully loaded %d stocks",
        len(common)
    )

    if failed:

        logger.warning(
            "%d symbols skipped",
            len(failed)
        )

    return (
        close_df,
        volume_df,
    )