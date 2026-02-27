#!/bin/bash

# Get Binance Futures income history with pagination for 1 year
BINANCE_API_KEY="b3WeLglIQ1bieqvFNTjZWK0NmIiLywJEGMhQ0IWindRbLMIP5gQSNTtEc1GLEyqi"
BINANCE_API_SECRET="SnJO6fWg7zZAl02YG2Zx9gk39NTUxbYlFhnSfzk0e5d706k82l5YgmvMZqUtNisw"
API_BASE="https://fapi.binance.com"

# Calculate timestamps
NOW=$(python3 -c "import time; print(int(time.time() * 1000))")
ONE_YEAR_AGO=$(python3 -c "import time; print(int((time.time() - 365*24*60*60) * 1000))")

echo "================================================================================"
echo "              BINANCE FUTURES - 1 YEAR INCOME (WITH PAGINATION)"
echo "================================================================================"
echo "Fetching from $(date -d @$((ONE_YEAR_AGO/1000)) '+%Y-%m-%d') to $(date -d @$((NOW/1000)) '+%Y-%m-%d')"
echo ""

# Collect all records
TEMP_FILE=$(mktemp)
RECORD_COUNT=0
PAGE=1
CURRENT_START=$ONE_YEAR_AGO

while [ "$CURRENT_START" -lt "$NOW" ]; do
    TIMESTAMP=$(python3 -c "import time; print(int(time.time() * 1000))")
    SIGNATURE=$(echo -n "endTime=$NOW&limit=1000&startTime=$CURRENT_START&timestamp=$TIMESTAMP" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | awk '{print $2}')

    RESULT=$(curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
      "$API_BASE/fapi/v1/income?startTime=$CURRENT_START&endTime=$NOW&limit=1000&timestamp=$TIMESTAMP&signature=$SIGNATURE")

    # Check for error
    if echo "$RESULT" | grep -q '"code"'; then
        echo "Error fetching data: $RESULT" | head -c 200
        break
    fi

    # Parse and save records
    echo "$RESULT" >> "$TEMP_FILE"

    # Count new records
    NEW_COUNT=$(echo "$RESULT" | python3 -c "import sys,json; data=json.load(sys.stdin); print(len(data))")

    if [ "$NEW_COUNT" -eq 0 ]; then
        break
    fi

    RECORD_COUNT=$((RECORD_COUNT + NEW_COUNT))
    echo "  Page $PAGE: $NEW_COUNT records (total: $RECORD_COUNT)"

    if [ "$NEW_COUNT" -lt 1000 ]; then
        break
    fi

    # Get the last timestamp for next page
    LAST_TIME=$(echo "$RESULT" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data[-1]['time'])")
    CURRENT_START=$((LAST_TIME + 1))
    PAGE=$((PAGE + 1))
done

echo ""
echo "  ✓ Total records fetched: $RECORD_COUNT"
echo ""

# Combine and analyze all records
cat "$TEMP_FILE" | python3 -c "
import sys, json
from collections import defaultdict

# Read all records from stdin
all_data = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        data = json.loads(line)
        if isinstance(data, list):
            all_data.extend(data)
    except:
        pass

# Group by symbol and income type
symbol_stats = defaultdict(lambda: {
    'realized_pnl': 0.0,
    'funding': 0.0,
    'commission': 0.0
})

type_totals = defaultdict(float)

total_realized_pnl = 0.0
total_funding = 0.0
total_commission = 0.0

for income in all_data:
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

print(\"📊 Income Summary (1 Year):\")
print(f\"  Total Realized PnL:      {total_realized_pnl:>+,.2f} USDT\")
print(f\"  Total Funding:           {total_funding:>+,.2f} USDT\")
print(f\"  Total Commission:        {total_commission:>+,.2f} USDT\")
print(f\"  Net (PnL - Commission): {total_realized_pnl - total_commission:>+,.2f} USDT\")
print()

print(\"🟢 TOP WINNERS (Realized PnL):\")
winners = [(s, v) for s, v in symbol_stats.items() if v['realized_pnl'] > 0]
winners.sort(key=lambda x: x[1]['realized_pnl'], reverse=True)
for symbol, s in winners[:15]:
    net = s['realized_pnl'] - s['commission']
    r_units = s['realized_pnl'] / 24  # 1R = ~24 USDT
    print(f\"  {symbol:<20} {s['realized_pnl']:>+10.2f} USDT (net: {net:>+8.2f}, {r_units:+.2f}R)\")

print()

print(\"🔴 TOP LOSERS (Realized PnL):\")
losers = [(s, v) for s, v in symbol_stats.items() if v['realized_pnl'] < 0]
losers.sort(key=lambda x: x[1]['realized_pnl'])
for symbol, s in losers[:10]:
    net = s['realized_pnl'] - s['commission']
    r_units = s['realized_pnl'] / 24
    print(f\"  {symbol:<20} {s['realized_pnl']:>+10.2f} USDT (net: {net:>+8.2f}, {r_units:+.2f}R)\")

print()

print(\"💳 Income Type Breakdown:\")
for itype in sorted(type_totals.keys(), key=lambda x: abs(type_totals[x]), reverse=True):
    amount = type_totals[itype]
    color = '🟢' if amount >= 0 else '🔴'
    print(f\"  {itype:<25} {amount:>+15.2f} USDT {color}\")

print()
print(\"================================================================================\")
"

rm -f "$TEMP_FILE"
