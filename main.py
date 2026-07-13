"""
PairTradingPro v1.0
main.py
"""

import time
import pandas as pd

from config import OUTPUT_DIR
from data_loader import load_market_data
from scanner import run_scanner
from backtest import run_backtest


def main():
    print("=" * 60)
    print("PAIR TRADING PRO v1.0")
    print("=" * 60)

    # Load market data
    tickers, close_prices, volume_data = load_market_data()
    
    if close_prices.empty:
        print("\n❌ No market data found. Exiting.")
        return

    # Run Scanner
    print("\n" + "-" * 70)
    print("Running Scanner...")
    print("-" * 70)
    
    start = time.time()
    scanner_results = run_scanner()
    print(f"\nScanner Finished : {time.time() - start:.2f} sec")

    # Run Backtest if scanner results exist
    if not scanner_results.empty:
        print("\n" + "-" * 70)
        print("Running Backtest...")
        print("-" * 70)
        
        start = time.time()
        backtest_results = run_backtest()
        print(f"\nBacktest Finished : {time.time() - start:.2f} sec")

    print("\n" + "=" * 60)
    print("PROJECT COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()