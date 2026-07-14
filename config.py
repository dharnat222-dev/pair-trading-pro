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
# DATA SOURCE
# =========================
# CSV MODE (OFF - We use Angel API)
USE_CSV_DATA = True
CSV_FILE_PATH = DATA_DIR / "stock_data.csv"

# =========================
# ANGEL ONE API - ENABLED
# =========================
USE_ANGEL_API = False
ANGEL_API_KEY = "your_api_key"
ANGEL_CLIENT_ID = "your_client_id"
ANGEL_PASSWORD = "your_password"
ANGEL_TOTP = ""  # 2FA હોય તો

# =========================
# DATA SETTINGS
# =========================
LOOKBACK_DAYS = 365
ROLLING_WINDOW = 30
MIN_HISTORY = 250

# =========================
# SCANNER FILTERS
# =========================
MIN_CORRELATION = 0.60
MIN_ROLLING_CORRELATION = 0.50
MAX_COINTEGRATION_PVALUE = 0.15
MAX_ADF_PVALUE = 0.15

MIN_BETA = 0.30
MAX_BETA = 2.00

MIN_ZSCORE = 1.20

MAX_VOLATILITY = 0.70
MIN_AVG_VOLUME = 30000

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

ANGEL_API_KEY = "3k16AOie"
ANGEL_CLIENT_ID = "K202720" 
ANGEL_PASSWORD =  "1992"
ANGEL_TOTP = ""  # 2FA હોય તો TOTP આપો