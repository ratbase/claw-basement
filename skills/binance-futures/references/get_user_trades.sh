#!/bin/bash
# get_user_trades.sh
# Get Binance Futures user trades (historical closed positions)

source ~/.binance_config

if [ -z "$BINANCE_API_KEY" ] || [ -z "$BINANCE_API_SECRET" ]; then
    echo "Error: BINANCE_API_KEY or BINANCE_API_SECRET not set"
    exit 1
fi

# Get all trades from all symbols (limit 1000 per symbol, most recent)
TIMESTAMP=$(date +%s)000
QUERY_STRING="timestamp=$TIMESTAMP&limit=1000"
SIGNATURE=$(echo -n "$QUERY_STRING" | openssl dgst -sha256 -hmac $BINANCE_API_SECRET | sed 's/^.* //')

# Fetch all user trades
curl -s -X GET "https://fapi.binance.com/fapi/v1/userTrades?$QUERY_STRING&signature=$SIGNATURE" \
  -H "X-MBX-APIKEY: $BINANCE_API_KEY" | jq .
