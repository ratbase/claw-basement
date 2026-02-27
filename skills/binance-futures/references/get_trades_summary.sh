#!/bin/bash

# Get Binance Futures user trades (historical)
# Load credentials from ~/.binance_config (NEVER hardcode keys!)
source ~/.binance_config || { echo 'ERROR: ~/.binance_config not found. Copy references/.binance_config.example to ~/.binance_config'; exit 1; }

# Get current timestamp
TIMESTAMP=$(python3 -c "import time; print(int(time.time() * 1000))")

# Generate signature
SIGNATURE=$(echo -n "timestamp=$TIMESTAMP&limit=1000" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | awk '{print $2}')

# Get user trades
RESULT=$(curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v1/userTrades?timestamp=$TIMESTAMP&limit=1000&signature=$SIGNATURE")

echo "$RESULT" | python3 -c "
import sys, json
from datetime import datetime
from collections import defaultdict

data = json.load(sys.stdin)

# Group by symbol and analyze
symbol_stats = defaultdict(lambda: {
    'trades': 0,
    'total_qty': 0.0,
    'total_quote_qty': 0.0,
    'realized_pnl': 0.0,
    'buy_trades': 0,
    'sell_trades': 0,
    'fees': 0.0
})

total_realized_pnl = 0.0
total_fees = 0.0

for trade in data:
    symbol = trade['symbol']
    qty = float(trade['qty'])
    quote_qty = float(trade['quoteQty'])
    fee = float(trade['commission'])
    is_buyer = trade['side'] == 'BUY'

    symbol_stats[symbol]['trades'] += 1
    symbol_stats[symbol]['total_qty'] += qty if is_buyer else -qty
    symbol_stats[symbol]['total_quote_qty'] += quote_qty
    symbol_stats[symbol]['fees'] += fee

    if is_buyer:
        symbol_stats[symbol]['buy_trades'] += 1
    else:
        symbol_stats[symbol]['sell_trades'] += 1

print(\"================================================================================\")
print(\"                  BINANCE FUTURES - USER TRADES ANALYSIS\")
print(\"================================================================================\")
print()

print(f\"📊 Total Trades: {len(data)}\")
print()

# Calculate net position per symbol
print(\"📈 Net Positions from Trades:\")
print(f\"{'Symbol':<15} {'Trades':<8} {'Buys':<6} {'Sells':<6} {'Net Qty':<12} {'Fees (USDT)':<12}\")
print(\"-\" * 75)

for symbol in sorted(symbol_stats.keys()):
    s = symbol_stats[symbol]
    print(f\"{symbol:<15} {s['trades']:<8} {s['buy_trades']:<6} {s['sell_trades']:<6} {s['total_qty']:>12.4f} {s['fees']:>12.4f}\")

total_trades = len(data)
total_fees_sum = sum(s['fees'] for s in symbol_stats.values())
print()
print(f\"💰 Total Fees Paid: {total_fees_sum:.4f} USDT\")
print()

print(\"================================================================================\")
"
