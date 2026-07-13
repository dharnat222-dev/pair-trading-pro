"""
PairTradingPro v1.0
main.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from config import (
    OUTPUT_DIR,
    LOG_DIR,
)

from scanner import (
    run_scanner,
)

from backtest import (
    run_backtest,
)


# ============================================================
# HEADER
# ============================================================

def print_header():

    print()

    print("=" * 70)

    print("PAIR TRADING PRO v1.0")

    print("=" * 70)

    print()


# ============================================================
# CREATE PROJECT FOLDERS
# ============================================================

def create_directories():

    OUTPUT_DIR.mkdir(
        exist_ok=True,
    )

    LOG_DIR.mkdir(
        exist_ok=True,
    )

# ============================================================
# RUN SCANNER
# ============================================================

def execute_scanner():

    print()

    print("-" * 70)

    print("Running Scanner...")

    print("-" * 70)

    start = time.time()

    df = run_scanner()

    elapsed = round(
        time.time() - start,
        2,
    )

    print()

    print(f"Scanner Finished : {elapsed} sec")

    return df


# ============================================================
# RUN BACKTEST
# ============================================================

def execute_backtest():

    print()

    print("-" * 70)

    print("Running Backtest...")

    print("-" * 70)

    start = time.time()

    run_backtest()

    elapsed = round(
        time.time() - start,
        2,
    )

    print()

    print(f"Backtest Finished : {elapsed} sec")

# ============================================================
# MAIN
# ============================================================

def main():

    print_header()

    create_directories()

    try:

        execute_scanner()

        execute_backtest()

        print()

        print("=" * 70)

        print("PROJECT COMPLETED SUCCESSFULLY")

        print("=" * 70)

    except KeyboardInterrupt:

        print()

        print("Execution Cancelled By User")

        sys.exit(0)

    except Exception as e:

        print()

        print("=" * 70)

        print("PROJECT FAILED")

        print("=" * 70)

        print(str(e))

        sys.exit(1)


if __name__ == "__main__":

    main()