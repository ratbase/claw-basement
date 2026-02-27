#!/bin/bash

# Get formatted account summary from Binance
# Load credentials from ~/.binance_config (NEVER hardcode keys!)
source ~/.binance_config || { echo 'ERROR: ~/.binance_config not found. Copy references/.binance_config.example to ~/.binance_config'; exit 1; }

# Get current timestamp
TIMESTAMP=$(python3 -c "import time; print(int(time.time() * 1000))")

# Generate signature
SIGNATURE=$(echo -n "timestamp=$TIMESTAMP" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | awk '{print $2}')

# Get account info
RESULT=$(curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v3/account?timestamp=$TIMESTAMP&signature=$SIGNATURE")

echo "================================================================================"
echo "                    BINANCE FUTURES ACCOUNT SUMMARY"
echo "================================================================================"
echo ""

# Extract key values using Python
echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)

print(f\"📊 Account Status:\")
print(f\"  Trading:       {data['canTrade']}\")
print(f\"  Deposits:      {data['canDeposit']}\")
print(f\"  Withdrawals:   {data['canWithdraw']}\")
print(f\"  Fee Tier:      {data['feeTier']}\")
print()

print(f\"💰 Balance Summary (USDT):\")
print(f\"  Total Wallet Balance:      {float(data['totalWalletBalance']):,.2f}\")
print(f\"  Total Margin Balance:     {float(data['totalMarginBalance']):,.2f}\")
print(f\"  Available Balance:        {float(data['availableBalance']):,.2f}\")
print(f\"  Max Withdrawable:         {float(data['maxWithdrawAmount']):,.2f}\")
print()

print(f\"📈 Profit/Loss:\")
print(f\"  Total Unrealized Profit:  {float(data['totalUnrealizedProfit']):>+,.2f} USDT\")
print()

print(f\"💳 Margin Requirements:\")
print(f\"  Total Initial Margin:     {float(data['totalInitialMargin']):,.2f} USDT\")
print(f\"  Total Maint Margin:       {float(data['totalMaintMargin']):,.2f} USDT\")
print(f\"  Position Initial Margin:  {float(data['totalPositionInitialMargin']):,.2f} USDT\")
print(f\"  Open Order Initial Margin:{float(data['totalOpenOrderInitialMargin']):,.2f} USDT\")
print()

print(f\"🔁 Cross Wallet:\")
print(f\"  Cross Wallet Balance:     {float(data['totalCrossWalletBalance']):,.2f} USDT\")
print(f\"  Cross Unrealized PnL:     {float(data['totalCrossUnPnl']):>+,.2f} USDT\")
"

echo ""
echo "================================================================================"
