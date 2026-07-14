"""
PairTradingPro v1.0
config.py
"""

from pathlib import Path

# =========================
# PROJECT PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# =========================
# DATA SOURCE - CSV MODE (ENABLED)
# =========================
USE_CSV_DATA = True
CSV_FILE_PATH = DATA_DIR / "stock_data_210.csv"

# =========================
# ANGEL ONE API - DISABLED
# =========================
USE_ANGEL_API = False
ANGEL_API_KEY = "your_api_key"
ANGEL_CLIENT_ID = "your_client_id"
ANGEL_PASSWORD = "your_password"
ANGEL_TOTP = ""

# =========================
# DATA SETTINGS
# =========================
LOOKBACK_DAYS = 365
ROLLING_WINDOW = 30
MIN_HISTORY = 250

# =========================
# SCANNER FILTERS (RELAXED)
# =========================
MIN_CORRELATION = 0.30
MIN_ROLLING_CORRELATION = 0.30
MAX_COINTEGRATION_PVALUE = 0.30
MAX_ADF_PVALUE = 0.30

MIN_BETA = 0.10
MAX_BETA = 4.00

MIN_ZSCORE = 0.80

MAX_VOLATILITY = 0.50
MIN_AVG_VOLUME = 20000

# =========================
# BACKTEST
# =========================
ENTRY_Z = 2.0
EXIT_Z = 0.30
STOP_Z = 3.0
MAX_HOLD_DAYS = 30

# =========================
# EXCEL
# =========================
TOP_PAIRS = 10

# =========================
# PERFORMANCE
# =========================
MAX_WORKERS = 8

# =========================
# STATISTICS
# =========================
MIN_TRADING_DAYS = 100
HURST_MAX_LAG = 20
