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
    USE_CSV_DATA,
    CSV_FILE_PATH,
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
# FALLBACK STOCKS (NIFTY 50 + BANK NIFTY)
# ============================================================

def get_fallback_stocks():
    """NIFTY 50 + BANK NIFTY stocks as fallback"""
    return [
        # NIFTY 50
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
        "ICICIBANK.NS", "HINDUNILVR.NS", "ITC.NS", "SBIN.NS",
        "BHARTIARTL.NS", "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS",
        "WIPRO.NS", "HCLTECH.NS", "ASIANPAINT.NS", "MARUTI.NS",
        "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "NTPC.NS",
        "ONGC.NS", "POWERGRID.NS", "NESTLEIND.NS", "M&M.NS",
        "TECHM.NS", "JSWSTEEL.NS", "BAJFINANCE.NS",
        "ADANIPORTS.NS", "COALINDIA.NS", "GRASIM.NS", "INDUSINDBK.NS",
        "TATASTEEL.NS", "BRITANNIA.NS", "APOLLOHOSP.NS", "SBILIFE.NS",
        "HINDALCO.NS", "UPL.NS", "EICHERMOT.NS", "SHREECEM.NS",
        "CIPLA.NS", "DRREDDY.NS", "HEROMOTOCO.NS", "TATAMOTORS.NS",
        "TATACONSUM.NS", "BAJAJFINSV.NS",
        # BANK NIFTY
        "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "IDFCBANK.NS",
        "FEDERALBNK.NS", "RBLBANK.NS", "UNIONBANK.NS", "BANDHANBNK.NS",
        "AUBANK.NS",
    ]

# ============================================================
# LOAD FROM CSV
# ============================================================

def load_from_csv():
    """Load stock data from CSV file"""
    try:
        if not CSV_FILE_PATH.exists():
            logger.warning("CSV file not found: %s", CSV_FILE_PATH)
            return None, None
        
        df = pd.read_csv(CSV_FILE_PATH, index_col=0, parse_dates=True)
        
        if df.empty:
            logger.warning("CSV file is empty")
            return None, None
        
        # Clean column names
        df.columns = [col.strip().upper() for col in df.columns]
        
        # Create volume DataFrame (dummy - we only have price data)
        volume_df = pd.DataFrame(1, index=df.index, columns=df.columns)
        
        logger.info("✅ Loaded %d stocks from CSV: %s", len(df.columns), CSV_FILE_PATH)
        return df, volume_df
        
    except Exception as e:
        logger.error("Failed to load CSV: %s", str(e))
        return None, None

# ============================================================
# DOWNLOAD NSE F&O LIST
# ============================================================

def process_bhavcopy_data(df: pd.DataFrame, symbol_col: str):
    """Process BhavCopy DataFrame and extract tickers"""
    
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
        tickers.append(f"{stock}.NS")

    return sorted(set(tickers))

def get_latest_fno_list(days_back: int = 10):
    """Download NSE F&O list"""
    
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

                tickers = process_bhavcopy_data(df, symbol_col)
                
                if tickers:
                    logger.info("✅ Loaded %d F&O Stocks from BhavCopy", len(tickers))
                    return tickers

            except Exception as e:
                logger.debug(f"BhavCopy attempt failed: {e}")
                continue

    # If BhavCopy fails, use fallback
    logger.warning("⚠️ BhavCopy failed. Using fallback NIFTY 50 stocks...")
    fallback_stocks = get_fallback_stocks()
    logger.info("✅ Loaded %d fallback stocks", len(fallback_stocks))
    return fallback_stocks

# ============================================================
# DOWNLOAD FROM YFINANCE
# ============================================================

def download_from_yfinance(tickers: list[str], lookback_days: int = LOOKBACK_DAYS):
    """Download price data from yfinance"""
    
    if not tickers:
        return pd.DataFrame(), pd.DataFrame()

    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback_days)

    logger.info("Downloading historical prices for %d stocks...", len(tickers))

    close_data = {}
    volume_data = {}
    failed = []
    success = 0
    total = len(tickers)

    for i, ticker in enumerate(tickers, start=1):
        try:
            # Retry mechanism
            for attempt in range(3):
                try:
                    hist = yf.Ticker(ticker).history(
                        start=start_date.strftime("%Y-%m-%d"),
                        end=end_date.strftime("%Y-%m-%d"),
                        interval="1d",
                        auto_adjust=True,
                    )
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    continue

            if hist.empty:
                failed.append(ticker)
                continue

            hist = hist.tz_localize(None)

            if len(hist) < MIN_HISTORY:
                failed.append(ticker)
                continue

            symbol = ticker.replace(".NS", "")
            close_data[symbol] = hist["Close"]
            volume_data[symbol] = hist["Volume"]
            success += 1

            if i % 20 == 0:
                logger.info("Downloaded %d/%d stocks (%d successful)", i, total, success)

        except Exception as e:
            failed.append(ticker)
            continue

    logger.info("✅ Successfully loaded %d/%d stocks", success, total)

    if failed:
        logger.warning("⚠️ %d symbols skipped", len(failed))

    close_df = pd.DataFrame(close_data)
    volume_df = pd.DataFrame(volume_data)

    if close_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Keep only common stocks
    common = close_df.columns.intersection(volume_df.columns)
    close_df = close_df[common]
    volume_df = volume_df[common]

    return close_df, volume_df

# ============================================================
# LOAD MARKET DATA (MAIN)
# ============================================================

def load_market_data():
    """Load market data - tries CSV first, then yfinance"""
    
    logger.info("=" * 60)
    logger.info("Loading Market Data")
    logger.info("=" * 60)
    
    # ======= OPTION 1: LOAD FROM CSV =======
    if USE_CSV_DATA:
        logger.info("📂 Attempting to load from CSV: %s", CSV_FILE_PATH)
        close_df, volume_df = load_from_csv()
        
        if close_df is not None and not close_df.empty:
            logger.info("✅ Market Data Loaded from CSV")
            logger.info("📊 Stocks Loaded : %d", len(close_df.columns))
            logger.info("📊 Rows Loaded   : %d", len(close_df))
            logger.info("📊 Date Range    : %s to %s", 
                       close_df.index[0].strftime("%Y-%m-%d"),
                       close_df.index[-1].strftime("%Y-%m-%d"))
            logger.info("=" * 60)
            return list(close_df.columns), close_df, volume_df
        else:
            logger.warning("⚠️ CSV load failed, falling back to yfinance...")
    
    # ======= OPTION 2: DOWNLOAD FROM YFINANCE =======
    logger.info("🌐 Downloading from yfinance...")
    
    tickers = get_latest_fno_list()
    if not tickers:
        logger.error("❌ No tickers available")
        return [], pd.DataFrame(), pd.DataFrame()
    
    close_df, volume_df = download_from_yfinance(tickers)
    
    if close_df.empty:
        logger.error("❌ Price data download failed")
        return [], pd.DataFrame(), pd.DataFrame()
    
    logger.info("✅ Market Data Ready from yfinance")
    logger.info("📊 Stocks Loaded : %d", len(close_df.columns))
    logger.info("📊 Rows Loaded   : %d", len(close_df))
    logger.info("📊 Date Range    : %s to %s", 
               close_df.index[0].strftime("%Y-%m-%d"),
               close_df.index[-1].strftime("%Y-%m-%d"))
    logger.info("=" * 60)
    
    return list(close_df.columns), close_df, volume_df

# ============================================================
# SAVE CSV TEMPLATE
# ============================================================

def save_csv_template():
    """Download data and save as CSV template"""
    
    logger.info("Creating CSV template...")
    
    tickers = get_fallback_stocks()[:20]  # Just 20 stocks for template
    
    close_df, volume_df = download_from_yfinance(tickers)
    
    if close_df.empty:
        logger.error("❌ Failed to create template")
        return
    
    # Save to CSV
    close_df.to_csv(CSV_FILE_PATH)
    logger.info("✅ Template saved to: %s", CSV_FILE_PATH)
    logger.info("📊 Stocks: %d, Rows: %d", len(close_df.columns), len(close_df))

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