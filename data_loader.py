"""
PairTradingPro v1.0
data_loader.py - Angel One API
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import yfinance as yf

from config import (
    LOOKBACK_DAYS,
    MIN_HISTORY,
    USE_ANGEL_API,
    USE_CSV_DATA,
    CSV_FILE_PATH,
    ANGEL_API_KEY,
    ANGEL_CLIENT_ID,
    ANGEL_PASSWORD,
    ANGEL_TOTP,
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
# ANGEL ONE API CONNECTION
# ============================================================

def get_angel_connection():
    """Create Angel One API connection"""
    try:
        from smartapi import SmartConnect
        
        obj = SmartConnect(api_key=ANGEL_API_KEY)
        data = obj.generateSession(
            clientCode=ANGEL_CLIENT_ID,
            password=ANGEL_PASSWORD,
            totp=ANGEL_TOTP if ANGEL_TOTP else None
        )
        if data.get('status'):
            logger.info("✅ Angel One API Connected")
            return obj
        else:
            logger.error("❌ Angel One login failed")
            return None
    except ImportError:
        logger.error("❌ smartapi-python not installed! Run: pip install smartapi-python")
        return None
    except Exception as e:
        logger.error(f"❌ Angel One error: {e}")
        return None

# ============================================================
# FALLBACK STOCKS
# ============================================================

def get_fallback_stocks():
    """NIFTY 50 stocks as fallback"""
    return [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
        "ICICIBANK.NS", "HINDUNILVR.NS", "ITC.NS", "SBIN.NS",
        "BHARTIARTL.NS", "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS",
        "WIPRO.NS", "HCLTECH.NS", "ASIANPAINT.NS", "MARUTI.NS",
        "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "NTPC.NS",
        "ONGC.NS", "POWERGRID.NS", "NESTLEIND.NS", "M&M.NS",
        "TECHM.NS", "JSWSTEEL.NS", "BAJFINANCE.NS", "ADANIPORTS.NS",
        "COALINDIA.NS", "GRASIM.NS", "INDUSINDBK.NS", "TATASTEEL.NS",
        "BRITANNIA.NS", "APOLLOHOSP.NS", "SBILIFE.NS", "HINDALCO.NS",
        "UPL.NS", "EICHERMOT.NS", "SHREECEM.NS", "CIPLA.NS",
        "DRREDDY.NS", "HEROMOTOCO.NS", "TATAMOTORS.NS", "TATACONSUM.NS",
        "BAJAJFINSV.NS", "ADANIENT.NS"
    ]

# ============================================================
# LOAD FROM CSV (fallback)
# ============================================================

def load_from_csv():
    """Load stock data from CSV file"""
    try:
        if not CSV_FILE_PATH.exists():
            return None, None
        df = pd.read_csv(CSV_FILE_PATH, index_col=0, parse_dates=True)
        if df.empty:
            return None, None
        df.columns = [col.strip().upper() for col in df.columns]
        df = df.dropna(axis=1, how='all')
        if df.empty:
            return None, None
        volume_df = pd.DataFrame(1, index=df.index, columns=df.columns)
        logger.info("✅ Loaded %d stocks from CSV", len(df.columns))
        return df, volume_df
    except Exception as e:
        logger.error(f"CSV load error: {e}")
        return None, None

# ============================================================
# GET STOCKS FROM ANGEL ONE
# ============================================================

def get_stocks_from_angel():
    """Get stocks from Angel One API"""
    try:
        obj = get_angel_connection()
        if not obj:
            return get_fallback_stocks()
        
        # Get master data
        response = obj.getMaster("NSE", "EQ")
        if response.get('status'):
            stocks = []
            for item in response.get('data', []):
                symbol = item.get('symbol')
                if symbol:
                    stocks.append(f"{symbol}.NS")
            if stocks:
                logger.info("✅ Loaded %d stocks from Angel One", len(stocks))
                return stocks[:200]  # Limit for performance
        return get_fallback_stocks()
    except Exception as e:
        logger.error(f"Angel stock list error: {e}")
        return get_fallback_stocks()

# ============================================================
# LOAD MARKET DATA
# ============================================================

def load_market_data():
    """Load market data - Angel API first, then CSV"""
    
    logger.info("=" * 60)
    logger.info("Loading Market Data")
    logger.info("=" * 60)
    
    # ====== OPTION 1: ANGEL ONE API ======
    if USE_ANGEL_API:
        logger.info("🌐 Attempting Angel One API...")
        tickers = get_stocks_from_angel()
        
        if tickers:
            logger.info(f"📥 Downloading prices for {len(tickers)} stocks...")
            close_data = {}
            success = 0
            total = len(tickers)
            
            for i, ticker in enumerate(tickers, 1):
                try:
                    df = yf.download(ticker, period="1y", interval="1d", progress=False)
                    if not df.empty:
                        close_data[ticker.replace(".NS", "")] = df["Close"]
                        success += 1
                        if i % 20 == 0:
                            logger.info(f"📊 {i}/{total} done ({success} successful)")
                except:
                    pass
            
            logger.info(f"✅ Success: {success}/{total} stocks")
            
            if close_data:
                close_df = pd.DataFrame(close_data)
                volume_df = pd.DataFrame(1, index=close_df.index, columns=close_df.columns)
                logger.info("✅ Market Data Ready from Angel One")
                logger.info("📊 Stocks: %d, Rows: %d", len(close_df.columns), len(close_df))
                logger.info("=" * 60)
                return list(close_df.columns), close_df, volume_df
    
    # ====== OPTION 2: CSV (fallback) ======
    if USE_CSV_DATA:
        logger.info("📂 Fallback to CSV...")
        close_df, volume_df = load_from_csv()
        if close_df is not None and not close_df.empty:
            logger.info("✅ Market Data Loaded from CSV")
            return list(close_df.columns), close_df, volume_df
    
    logger.error("❌ No data sources available!")
    return [], pd.DataFrame(), pd.DataFrame()