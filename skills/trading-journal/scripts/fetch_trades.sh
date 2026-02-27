#!/bin/bash
# Fetch recent trades from Binance Futures for trading journal
# Usage: ./fetch_trades.sh [SYMBOL] [LIMIT]

source ~/.binance_config 2>/dev/null || {
    echo "Error: ~/.binance_config not found"
    echo "Create it with: BINANCE_API_KEY=your_key BINANCE_API_SECRET=your_secret"
    exit 1
}

SYMBOL=${1:-""}
LIMIT=${2:-100}
TIMESTAMP=$(date +%s)000

# Build query string
QUERY="limit=$LIMIT&timestamp=$TIMESTAMP"
if [ -n "$SYMBOL" ]; then
    QUERY="symbol=$SYMBOL&$QUERY"
fi

SIGNATURE=$(echo -n "$QUERY" | openssl dgst -sha256 -hmac $BINANCE_API_SECRET | sed 's/^.* //')

if [ -n "$SYMBOL" ]; then
    # Get trades for specific symbol
    curl -s -X GET "https://fapi.binance.com/fapi/v1/userTrades" \
        -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
        -G -d "$QUERY&signature=$SIGNATURE"
else
    # Get recent trades across all symbols
    curl -s -X GET "https://fapi.binance.com/fapi/v1/userTrades" \
        -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
        -G -d "$QUERY&signature=$SIGNATURE"
fi
