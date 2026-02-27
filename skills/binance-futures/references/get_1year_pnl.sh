#!/bin/bash

# Binance Futures - 1 Year Income History Script
# Fetches all income records from 1 year ago to today

API_KEY=$(grep BINANCE_API_KEY "$HOME/.binance.env" 2>/dev/null | cut -d '=' -f2 | tr -d '"')
API_SECRET=$(grep BINANCE_API_SECRET "$HOME/.binance.env" 2>/dev/null | cut -d '=' -f2 | tr -d '"')
API_BASE="https://fapi.binance.com"

if [ -z "$API_KEY" ] || [ -z "$API_SECRET" ]; then
    echo "ERROR: API credentials not found"
    exit 1
fi

# Calculate timestamp: 1 year ago to now
END_TIME=$(date +%s)000
START_TIME=$(date -d "1 year ago" +%s)000
LIMIT=1000

echo "================================================================================"
echo "              BINANCE FUTURES - 1 YEAR INCOME HISTORY"
echo "================================================================================"
echo "Fetching records from $(date -d "@$((START_TIME/1000))" '+%Y-%m-%d') to $(date '+%Y-%m-%d')"
echo ""

# Function to generate signature
timestamp=$(date +%s)000

# Fetch first batch
echo "Fetching income records..."
RESPONSE=$(curl -s -X GET "${API_BASE}/fapi/v1/income?timestamp=${timestamp}&apiKey=${API_KEY}&startTime=${START_TIME}&endTime=${END_TIME}&limit=${LIMIT}&signature=$(echo -n "apiKey=${API_KEY}&endTime=${END_TIME}&limit=${LIMIT}&startTime=${START_TIME}&timestamp=${timestamp}" | openssl dgst -sha256 -hmac "$API_SECRET" | sed 's/^.* //')")

# Check if response is valid
if echo "$RESPONSE" | grep -q '"code"'; then
    echo "ERROR: API returned error"
    echo "$RESPONSE" | head -c 500
    exit 1
fi

# Save all records to a temp file
TEMP_FILE=$(mktemp)
echo "$RESPONSE" > "$TEMP_FILE"
RECORD_COUNT=$(jq 'length' "$TEMP_FILE" 2>/dev/null || echo "0")

echo "  Fetched $RECORD_COUNT records"

# Fetch more records if there are more than LIMIT
if [ "$RECORD_COUNT" -ge "$LIMIT" ]; then
    echo "  Fetching additional records..."
    LAST_TIME=$(jq -r '.[-1].time' "$TEMP_FILE")
    while [ -n "$LAST_TIME" ] && [ "$((LAST_TIME/1000))" -lt "$((END_TIME/1000))" ]; do
        NEW_START=$((LAST_TIME + 1))
        timestamp=$(date +%s)000

        NEW_RESPONSE=$(curl -s -X GET "${API_BASE}/fapi/v1/income?timestamp=${timestamp}&apiKey=${API_KEY}&startTime=${NEW_START}&endTime=${END_TIME}&limit=${LIMIT}&signature=$(echo -n "apiKey=${API_KEY}&endTime=${END_TIME}&limit=${LIMIT}&startTime=${NEW_START}&timestamp=${timestamp}" | openssl dgst -sha256 -hmac "$API_SECRET" | sed 's/^.* //')")

        if echo "$NEW_RESPONSE" | grep -q '"code"'; then
            break
        fi

        # Append new records (skip first 2 chars "[," and last "]")
        echo "$NEW_RESPONSE" | jq -r '.[]' >> "$TEMP_FILE.new"
        cat "$TEMP_FILE.new" >> "$TEMP_FILE"
        rm "$TEMP_FILE.new"

        NEW_COUNT=$(jq 'length' "$TEMP_FILE" 2>/dev/null || echo "0")
        LAST_TIME=$(jq -r '.[-1].time' "$TEMP_FILE")
        echo "    Total records: $NEW_COUNT"

        [ "$NEW_COUNT" -le "$RECORD_COUNT" ] && break
        RECORD_COUNT=$NEW_COUNT
    done
fi

# Process data with jq
echo ""
echo "================================================================================"
echo "INCOME SUMMARY (1 YEAR)"
echo "================================================================================"
echo "$RESPONSE" | jq -r '
    map(select(.incomeType == "REALIZED_PNL") | .income) |
    add |
    "  Total Realized PnL:      \(if . then "\(.)" else "0" end) USDT"
'

echo ""
echo "================================================================================"
echo "REALIZED PnL BY SYMBOL (1 YEAR)"
echo "================================================================================"
echo "$RESPONSE" | jq -r '
    group_by(.symbol) |
    map({
        symbol: .[0].symbol,
        pnl: map(select(.incomeType == "REALIZED_PNL") | .income) | add,
        funding: map(select(.incomeType == "FUNDING_FEE") | .income) | add,
        commission: map(select(.incomeType == "COMMISSION") | .income) | add
    }) |
    sort_by(.pnl - .commission) | reverse |
    .[] |
    "\(.symbol)\t\(.pnl // 0)\t\(.funding // 0)\t\(.commission // 0)\t\((.pnl // 0) - (.commission // 0))"
' | column -t -s $'\t' | awk '{
    pnl_emoji = ($2 >= 0 ? "🟢" : "🔴")
    net_emoji = ($5 >= 0 ? "🟢" : "🔴")
    printf "%-20s %+13.2f %s %+11.2f %+12.2f %+11.2f %s\n", $1, $2, pnl_emoji, $3, $4, $5, net_emoji
}'

echo ""
echo "================================================================================"

rm -f "$TEMP_FILE"
