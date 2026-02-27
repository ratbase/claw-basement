#!/bin/bash

# Get Binance Futures income history (realized PnL, funding, fees)
BINANCE_API_KEY="b3WeLglIQ1bieqvFNTjZWK0NmIiLywJEGMhQ0IWindRbLMIP5gQSNTtEc1GLEyqi"
BINANCE_API_SECRET="SnJO6fWg7zZAl02YG2Zx9gk39NTUxbYlFhnSfzk0e5d706k82l5YgmvMZqUtNisw"

# Get current timestamp
TIMESTAMP=$(python3 -c "import time; print(int(time.time() * 1000))")

# Generate signature - get last 1000 income records
SIGNATURE=$(echo -n "timestamp=$TIMESTAMP&limit=1000" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | awk '{print $2}')

# Get income history
RESULT=$(curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v1/income?timestamp=$TIMESTAMP&limit=1000&signature=$SIGNATURE")

echo "$RESULT" | python3 -c "
import sys, json
from datetime import datetime
from collections import defaultdict

data = json.load(sys.stdin)

# Group by symbol and income type
symbol_stats = defaultdict(lambda: {
    'realized_pnl': 0.0,
    'funding': 0.0,
    'commission': 0.0,
    'transfer_in': 0.0,
    'transfer_out': 0.0
})

# Also track by income type
type_totals = defaultdict(float)

total_realized_pnl = 0.0
total_funding = 0.0
total_commission = 0.0

for income in data:
    symbol = income['symbol']
    income_type = income['incomeType']
    amount = float(income['income'])

    type_totals[income_type] += amount

    if income_type == 'REALIZED_PNL':
        symbol_stats[symbol]['realized_pnl'] += amount
        total_realized_pnl += amount
    elif income_type == 'FUNDING_FEE':
        symbol_stats[symbol]['funding'] += amount
        total_funding += amount
    elif income_type == 'COMMISSION':
        symbol_stats[symbol]['commission'] += amount
        total_commission += amount
    elif income_type == 'TRANSFER_IN':
        symbol_stats[symbol]['transfer_in'] += amount
    elif income_type == 'TRANSFER_OUT':
        symbol_stats[symbol]['transfer_out'] += amount

print(\"================================================================================\")
print(\"              BINANCE FUTURES - INCOME & REALIZED PNL ANALYSIS\")
print(\"================================================================================\")
print()

# Total Income Summary
print(f\"📊 Income Summary:\")
print(f\"  Total Realized PnL:      {total_realized_pnl:>+,.2f} USDT\")
print(f\"  Total Funding Paid:     {total_funding:>+,.2f} USDT\")
print(f\"  Total Commission Paid:  {total_commission:>+,.2f} USDT\")
print(f\"  Net (PnL - Commission): {total_realized_pnl - total_commission:>+,.2f} USDT\")
print()

# Breakdown by symbol with realized PnL
print(\"📈 Realized PnL by Symbol:\")
print(f\"{'Symbol':<15} {'Realized PnL':<15} {'Funding':<12} {'Commission':<12} {'Net':<12}\")
print(\"-\" * 78)

symbols_with_pnl = {k: v for k, v in symbol_stats.items() if v['realized_pnl'] != 0 or v['funding'] != 0}

for symbol in sorted(symbols_with_pnl.keys(), key=lambda x: symbols_with_pnl[x]['realized_pnl'], reverse=True):
    s = symbols_with_pnl[symbol]
    net = s['realized_pnl'] - s['commission']
    pnl_color = '🟢' if s['realized_pnl'] >= 0 else '🔴'
    net_color = '🟢' if net >= 0 else '🔴'
    print(f\"{symbol:<15} {s['realized_pnl']:>+14.2f} {pnl_color}  {s['funding']:>+12.2f} {s['commission']:>+12.2f} {net:>+12.2f} {net_color}\")

print()

# Income type breakdown
print(\"💳 Income Type Breakdown:\")
for itype in sorted(type_totals.keys(), key=lambda x: abs(type_totals[x]), reverse=True):
    amount = type_totals[itype]
    color = '🟢' if amount >= 0 else '🔴'
    print(f\"  {itype:<25} {amount:>+15.2f} USDT {color}\")

print()
print(\"================================================================================\")
"
