#!/usr/bin/env python3
"""
Get 1 year of Binance Futures PnL history using python-binance
"""

from binance.client import Client
from binance.enums import *
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Initialize client
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

if not api_key or not api_secret:
    print("ERROR: BINANCE_API_KEY or BINANCE_API_SECRET not set")
    sys.exit(1)

client = Client(api_key, api_secret)

# Calculate date range (1 year ago to today)
end_time = datetime.now()
start_time = end_time - timedelta(days=365)

print("="*80)
print(f"BINANCE FUTURES - 1 YEAR INCOME HISTORY")
print("="*80)
print(f"Period: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
print()

# Fetch income history
all_income = []
current_start = int(start_time.timestamp() * 1000)
end_timestamp = int(end_time.timestamp() * 1000)
limit = 1000

print("Fetching income records...")
while current_start < end_timestamp:
    try:
        income = client.futures_income_history(
            symbol=None,  # All symbols
            startTime=current_start,
            endTime=end_timestamp,
            limit=limit
        )
        if not income:
            break

        all_income.extend(income)
        print(f"  Fetched {len(income)} records (total: {len(all_income)})")

        if len(income) < limit:
            break

        # Update start_time for next batch
        current_start = int(income[-1]['time']) + 1

    except Exception as e:
        print(f"Error fetching income: {e}")
        break

print()

if not all_income:
    print("No income records found.")
    sys.exit(0)

# Calculate totals
total_pnl = 0
total_funding = 0
total_commission = 0
realized_pnl_by_symbol = {}
funding_by_symbol = {}
commission_by_symbol = {}

for record in all_income:
    income_type = record['incomeType']
    symbol = record['symbol']
    amount = float(record['income'])

    if income_type == 'REALIZED_PNL':
        total_pnl += amount
        realized_pnl_by_symbol[symbol] = realized_pnl_by_symbol.get(symbol, 0) + amount
    elif income_type == 'FUNDING_FEE':
        total_funding += amount
        funding_by_symbol[symbol] = funding_by_symbol.get(symbol, 0) + amount
    elif income_type == 'COMMISSION':
        total_commission += amount
        commission_by_symbol[symbol] = commission_by_symbol.get(symbol, 0) + amount

# Print summary
print("="*80)
print("INCOME SUMMARY")
print("="*80)
print(f"  Total Realized PnL:      {total_pnl:+.2f} USDT")
print(f"  Total Funding:           {total_funding:+.2f} USDT")
print(f"  Total Commission:        {total_commission:+.2f} USDT")
print(f"  Net (PnL - Commission):   {total_pnl - total_commission:+.2f} USDT")
print()

# Get all unique symbols
all_symbols = sorted(set(list(realized_pnl_by_symbol.keys()) +
                        list(funding_by_symbol.keys()) +
                        list(commission_by_symbol.keys())))

print("="*80)
print("REALIZED PnL BY SYMBOL (1 YEAR)")
print("="*80)
print(f"{'Symbol':<20} {'PnL':>15} {'Funding':>12} {'Commission':>12} {'Net':>12}")
print("-" * 80)

# Calculate net and sort by net PnL
symbol_stats = []
for symbol in all_symbols:
    pnl = realized_pnl_by_symbol.get(symbol, 0)
    funding = funding_by_symbol.get(symbol, 0)
    commission = commission_by_symbol.get(symbol, 0)
    net = pnl - commission
    symbol_stats.append((symbol, pnl, funding, commission, net))

# Sort by net PnL
symbol_stats.sort(key=lambda x: x[4], reverse=True)

for symbol, pnl, funding, commission, net in symbol_stats:
    pnl_emoji = "🟢" if pnl >= 0 else "🔴"
    net_emoji = "🟢" if net >= 0 else "🔴"
    print(f"{symbol:<20} {pnl:>+13.2f} {pnl_emoji} {funding:>+11.2f} {commission:>+12.2f} {net:>+11.2f} {net_emoji}")

print()
print("="*80)
print("INCOME TYPE BREAKDOWN")
print("="*80)
print(f"  REALIZED_PNL              {total_pnl:+.2f} USDT {'🟢' if total_pnl >= 0 else '🔴'}")
print(f"  COMMISSION                {total_commission:+.2f} USDT {'🟢' if total_commission >= 0 else '🔴'}")
print(f"  FUNDING_FEE               {total_funding:+.2f} USDT {'🟢' if total_funding >= 0 else '🔴'}")
print()
print("="*80)
