#!/bin/bash

# Direct fetch of Binance account info
BINANCE_API_KEY="b3WeLglIQ1bieqvFNTjZWK0NmIiLywJEGMhQ0IWindRbLMIP5gQSNTtEc1GLEyqi"
BINANCE_API_SECRET="SnJO6fWg7zZAl02YG2Zx9gk39NTUxbYlFhnSfzk0e5d706k82l5YgmvMZqUtNisw"

# Get current timestamp
TIMESTAMP=$(python3 -c "import time; print(int(time.time() * 1000))")

# Generate signature
SIGNATURE=$(echo -n "timestamp=$TIMESTAMP" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | awk '{print $2}')

# Make request
curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v2/account?timestamp=$TIMESTAMP&signature=$SIGNATURE"
