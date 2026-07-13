"""
PairTradingPro v1.0
data_loader.py - Angel One API
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import pandas as pd
from smartapi import SmartConnect

from config import (
    LOOKBACK_DAYS,
    MIN_HISTORY,
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
# ANGEL ONE API - CONNECT
# ============================================================

def get_angel_connection():
    """Create Angel One API connection"""
    try:
        obj = SmartConnect(api_key=ANGEL_API_KEY)
        
        # Login
        data = obj.generateSession(
            clientCode=ANGEL_CLIENT_ID,
            password=ANGEL_PASSWORD,
            totp=ANGEL_TOTP  # If 2FA enabled
        )
        
        if data.get('status'):
            logger.info("✅ Angel One API Connected")
            return obj
        else:
            logger.error("❌ Angel One login failed: %s", data.get('message'))
            return None
            
    except Exception as e:
        logger.error("❌ Angel One connection error: %s", str(e))
        return None

# ============================================================
# GET STOCK LIST FROM ANGEL ONE
# ============================================================

def get_stock_list_from_angel():
    """Get F&O stock list from Angel One"""
    try:
        obj = get_angel_connection()
        if not obj:
            return get_fallback_stocks()
        
        # Get F&O stock list
        # (Exchange = NSE, Segment = FO)
        response = obj.getOFSymbols(exchange="NSE")
        
        if response.get('status'):
            stocks = []
            for item in response.get('data', []):
                symbol = item.get('symbol')
                if symbol and not symbol in BAD_SYMBOLS:
                    stocks.append(f"{symbol}.NS")
            logger.info("✅ Loaded %d F&O stocks from Angel One", len(stocks))
            return stocks[:50]  # Limit to 50 for speed
        else:
            logger.warning("⚠️ Angel One stock list failed, using fallback")
            return get_fallback_stocks()
            
    except Exception as e:
        logger.error("❌ Error getting stock list: %s", str(e))
        return get_fallback_stocks()

# ============================================================
# DOWNLOAD FROM ANGEL ONE API
# ============================================================

def download_from_angel(tickers: list[str], lookback_days: int = LOOKBACK_DAYS):
    """Download price data from Angel One API"""
    
    if not tickers:
        return pd.DataFrame(), pd.DataFrame()

    obj = get_angel_connection()
    if not obj:
        return pd.DataFrame(), pd.DataFrame()

    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback_days)

    logger.info("Downloading prices for %d stocks from Angel One...", len(tickers))

    close_data = {}
    volume_data = {}
    success = 0
    total = len(tickers)

    for i, ticker in enumerate(tickers, start=1):
        try:
            # Convert "RELIANCE.NS" to "RELIANCE"
            symbol = ticker.replace(".NS", "")
            
            # Get historical data
            from_date = start_date.strftime("%Y-%m-%d")
            to_date = end_date.strftime("%Y-%m-%d")
            
            response = obj.getCandleData(
                exchange="NSE",
                symbol=symbol,
                interval="ONE_DAY",
                fromdate=from_date,
                todate=to_date
            )
            
            if response.get('status') and response.get('data'):
                candles = response['data']
                
                # Convert to DataFrame
                df = pd.DataFrame(candles, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                if len(df) >= MIN_HISTORY:
                    close_data[symbol] = df['close']
                    volume_data[symbol] = df['volume']
                    success += 1
            
            if i % 10 == 0:
                logger.info("Downloaded %d/%d stocks (%d successful)", i, total, success)

        except Exception as e:
            logger.debug(f"Failed {ticker}: {e}")
            continue

    logger.info("✅ Successfully loaded %d/%d stocks from Angel One", success, total)

    if not close_data:
        return pd.DataFrame(), pd.DataFrame()

    close_df = pd.DataFrame(close_data)
    volume_df = pd.DataFrame(volume_data)

    return close_df, volume_df

# ============================================================
# FALLBACK STOCKS
# ============================================================

BAD_SYMBOLS = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"}

def get_fallback_stocks():
    """NIFTY 50 stocks as fallback"""
    return [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
        "ICICIBANK.NS", "HINDUNILVR.NS", "ITC.NS", "SBIN.NS",
        "BHARTIARTL.NS", "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS",
        "WIPRO.NS", "HCLTECH.NS", "ASIANPAINT.NS", "MARUTI.NS",
        "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "NTPC.NS",
    ]

# ============================================================
# LOAD MARKET DATA
# ============================================================

def load_market_data():
    """Load market data from Angel One API"""
    
    logger.info("=" * 60)
    logger.info("Loading Market Data - Angel One API")
    logger.info("=" * 60)
    
    # Try Angel One API
    tickers = get_stock_list_from_angel()
    if not tickers:
        tickers = get_fallback_stocks()
    
    close_df, volume_df = download_from_angel(tickers)
    
    if close_df.empty:
        logger.error("❌ All data sources failed!")
        return [], pd.DataFrame(), pd.DataFrame()
    
    logger.info("✅ Market Data Ready")
    logger.info("📊 Stocks: %d, Rows: %d", len(close_df.columns), len(close_df))
    logger.info("=" * 60)
    
    return list(close_df.columns), close_df, volume_df

# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    stocks, close_df, volume_df = load_market_data()
    print()
    print("=" * 60)
    print("TOTAL STOCKS :", len(stocks))
    print("PRICE SHAPE  :", close_df.shape)
    print("=" * 60)