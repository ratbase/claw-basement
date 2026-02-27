#!/bin/bash
# binance-account.sh
# Get full Binance Futures account information

source ~/.binance_config

if [ -z "$BINANCE_API_KEY" ] || [ -z "$BINANCE_API_SECRET" ]; then
    echo "Error: BINANCE_API_KEY or BINANCE_API_SECRET not set"
    echo "Please create ~/.binance_config with your credentials"
    exit 1
fi

TIMESTAMP=$(date +%s)000
QUERY_STRING="timestamp=$TIMESTAMP"
SIGNATURE=$(echo -n "$QUERY_STRING" | openssl dgst -sha256 -hmac $BINANCE_API_SECRET | sed 's/^.* //')

curl -s -X GET "https://fapi.binance.com/fapi/v2/account?$QUERY_STRING&signature=$SIGNATURE" \
  -H "X-MBX-APIKEY: $BINANCE_API_KEY"
