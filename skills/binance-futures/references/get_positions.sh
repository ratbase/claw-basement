#!/bin/bash

# Get formatted positions from Binance
BINANCE_API_KEY="b3WeLglIQ1bieqvFNTjZWK0NmIiLywJEGMhQ0IWindRbLMIP5gQSNTtEc1GLEyqi"
BINANCE_API_SECRET="SnJO6fWg7zZAl02YG2Zx9gk39NTUxbYlFhnSfzk0e5d706k82l5YgmvMZqUtNisw"

# Get current timestamp
TIMESTAMP=$(python3 -c "import time; print(int(time.time() * 1000))")

# Generate signature
SIGNATURE=$(echo -n "timestamp=$TIMESTAMP" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | awk '{print $2}')

# Get positions and format
curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v2/positionRisk?timestamp=$TIMESTAMP&signature=$SIGNATURE" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)

print(\"=\"*80)
print(\"BINANCE FUTURES POSITIONS\")
print(\"=\"*80)

# Filter positions with non-zero amounts
open_positions = [p for p in data if float(p['positionAmt']) != 0]

if open_positions:
    print(f\"{'Symbol':<15} {'Side':<8} {'Size':<15} {'Entry':<12} {'Mark':<12} {'Unrealized PnL':<15}\")
    print(\"-\"*80)
    for p in open_positions:
        amt = float(p['positionAmt'])
        side = 'LONG' if amt > 0 else 'SHORT'
        size = abs(amt)
        entry = p['entryPrice']
        mark = p['markPrice']
        pnl = p['unRealizedProfit']
        print(f\"{p['symbol']:<15} {side:<8} {size:<15.4f} {float(entry):<12.6f} {float(mark):<12.6f} {float(pnl):<15.4f}\")
else:
    print(\"No open positions found.\")
print(\"-\"*80)
"
