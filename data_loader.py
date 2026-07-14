"""
PairTradingPro v1.0
data_loader.py - CSV Mode (No SmartAPI)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import pandas as pd

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

        # Remove any columns with all NaN
        df = df.dropna(axis=1, how='all')

        if df.empty:
            logger.warning("No valid columns in CSV")
            return None, None

        # Create volume DataFrame (dummy - we only have price data)
        volume_df = pd.DataFrame(1, index=df.index, columns=df.columns)

        logger.info("✅ Loaded %d stocks from CSV", len(df.columns))
        return df, volume_df

    except Exception as e:
        logger.error("Failed to load CSV: %s", str(e))
        return None, None

# ============================================================
# LOAD MARKET DATA
# ============================================================

def load_market_data():
    """Load market data from CSV"""
    
    logger.info("=" * 60)
    logger.info("Loading Market Data")
    logger.info("=" * 60)
    
    # ======= CSV MODE =======
    if USE_CSV_DATA:
        logger.info("📂 Loading from CSV: %s", CSV_FILE_PATH)
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
            logger.error("❌ CSV load failed!")
            logger.error("Please make sure stock_data.csv exists in the root folder")
            return [], pd.DataFrame(), pd.DataFrame()
    
    else:
        logger.error("❌ CSV mode is disabled!")
        logger.error("Set USE_CSV_DATA = True in config.py")
        return [], pd.DataFrame(), pd.DataFrame()