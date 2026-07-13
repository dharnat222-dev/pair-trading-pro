"""
create_csv.py - Run this on your local PC to create stock_data.csv
"""

import yfinance as yf
import pandas as pd
from pathlib import Path

# Create data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# NIFTY 50 + Bank NIFTY stocks
stocks = [
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
]

print("=" * 60)
print("Creating Stock Data CSV")
print("=" * 60)

data = {}
success = 0
failed = []

for stock in stocks:
    try:
        print(f"Downloading {stock}...", end=" ")
        df = yf.download(stock, period="1y", interval="1d", progress=False)
        if not df.empty:
            symbol = stock.replace(".NS", "")
            data[symbol] = df["Close"]
            success += 1
            print("✅")
        else:
            failed.append(stock)
            print("❌ (empty)")
    except Exception as e:
        failed.append(stock)
        print(f"❌ ({str(e)[:30]})")

print("\n" + "-" * 60)
print(f"✅ Success: {success}/{len(stocks)} stocks")
print(f"❌ Failed: {len(failed)} stocks")
if failed:
    print(f"   Failed: {', '.join(failed)}")

if data:
    df = pd.DataFrame(data)
    csv_path = DATA_DIR / "stock_data.csv"
    df.to_csv(csv_path)
    print(f"\n✅ CSV saved to: {csv_path}")
    print(f"📊 Shape: {df.shape} (rows x columns)")
else:
    print("\n❌ No data downloaded! Check your internet connection.")