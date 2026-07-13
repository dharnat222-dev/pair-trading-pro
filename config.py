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

OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# =========================
# DATA SETTINGS
# =========================
LOOKBACK_DAYS = 365
ROLLING_WINDOW = 60
MIN_HISTORY = 250

# =========================
# SCANNER FILTERS
# =========================
MIN_CORRELATION = 0.70
MIN_ROLLING_CORRELATION = 0.60
MAX_COINTEGRATION_PVALUE = 0.05
MAX_ADF_PVALUE = 0.05

MIN_BETA = 0.50
MAX_BETA = 1.50

MIN_ZSCORE = 1.20

MAX_VOLATILITY = 0.60
MIN_AVG_VOLUME = 50000

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
# GITHUB
# =========================
MAX_WORKERS = 8