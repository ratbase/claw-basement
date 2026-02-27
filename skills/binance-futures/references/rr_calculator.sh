#!/bin/bash
# 📊 Risk:Reward Calculator for Binance Futures
# Usage: ./rr_calculator.sh [balance] [risk_percent] [entry_price] [stop_price]

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}              📊 RISK:REWARD CALCULATOR${NC}"
echo -e "${BLUE}================================================================================${NC}"

# Default values
BALANCE=${1:-600}           # Account balance in USDT
RISK_PCT=${2:-4}            # Risk percentage per trade
ENTRY_PRICE=${3:-9.50}      # Entry price
STOP_PRICE=${4:-9.00}       # Stop loss price
LEVERAGE=${5:-10}           # Leverage

# Calculate
RISK_AMOUNT=$(echo "scale=2; $BALANCE * $RISK_PCT / 100" | bc)
STOP_DISTANCE=$(echo "scale=4; $ENTRY_PRICE - $STOP_PRICE" | bc)
STOP_PCT=$(echo "scale=2; ($STOP_DISTANCE / $ENTRY_PRICE) * 100" | bc)

# Calculate position size
if [ $(echo "$STOP_DISTANCE > 0" | bc) -eq 1 ]; then
    POSITION_SIZE=$(echo "scale=2; $RISK_AMOUNT / $STOP_DISTANCE" | bc)
    POSITION_VALUE=$(echo "scale=2; $POSITION_SIZE * $ENTRY_PRICE" | bc)
    REQUIRED_MARGIN=$(echo "scale=2; $POSITION_VALUE / $LEVERAGE" | bc)
else
    echo -e "${RED}Error: Stop price must be below entry price for LONG trades${NC}"
    exit 1
fi

# Calculate take profit levels
TP1=$(echo "scale=4; $ENTRY_PRICE + $STOP_DISTANCE" | bc)
TP2=$(echo "scale=4; $ENTRY_PRICE + ($STOP_DISTANCE * 2)" | bc)
TP3=$(echo "scale=4; $ENTRY_PRICE + ($STOP_DISTANCE * 3)" | bc)

# Calculate potential profits
PROFIT_1R=$(echo "scale=2; $POSITION_SIZE * $STOP_DISTANCE" | bc)
PROFIT_2R=$(echo "scale=2; $PROFIT_1R * 2" | bc)
PROFIT_3R=$(echo "scale=2; $PROFIT_1R * 3" | bc)

# Margin usage percentage
MARGIN_USAGE=$(echo "scale=2; ($REQUIRED_MARGIN / $BALANCE) * 100" | bc)

echo ""
echo -e "${YELLOW}Trade Parameters:${NC}"
echo -e "  Account Balance:      $BALANCE USDT"
echo -e "  Risk per Trade:       $RISK_PCT% ($RISK_AMOUNT USDT = 1R)"
echo -e "  Entry Price:          $ENTRY_PRICE USDT"
echo -e "  Stop Loss:            $STOP_PRICE USDT"
echo -e "  Stop Distance:        $STOP_DISTANCE USDT ($STOP_PCT%)"
echo -e "  Leverage:             ${LEVERAGE}x"
echo ""
echo -e "${YELLOW}Position Sizing:${NC}"
echo -e "  Position Size:        $POSITION_SIZE units"
echo -e "  Position Value:       $POSITION_VALUE USDT"
echo -e "  Required Margin:      $REQUIRED_MARGIN USDT ($MARGIN_USAGE% of account)"
echo ""
echo -e "${YELLOW}Take Profit Levels:${NC}"
echo -e "  ${GREEN}TP1 (1R):   $TP1   →  Profit: $PROFIT_1R USDT${NC}"
echo -e "  ${GREEN}TP2 (2R):   $TP2   →  Profit: $PROFIT_2R USDT${NC}"
echo -e "  ${GREEN}TP3 (3R):   $TP3   →  Profit: $PROFIT_3R USDT${NC}"
echo ""

# Check if stop distance is too wide
if [ $(echo "$STOP_PCT > 5" | bc) -eq 1 ]; then
    echo -e "${RED}⚠️  WARNING: Stop distance is $STOP_PCT% (>5%)!${NC}"
    echo -e "${RED}   Consider reducing position size or skipping this trade.${NC}"
    echo ""
fi

# Check if R:R is good
RR_RATIO=$(echo "scale=2; 3 * $STOP_DISTANCE / $STOP_DISTANCE" | bc)
echo -e "${YELLOW}Risk:Reward:${NC}"
echo -e "  Risk:      $RISK_AMOUNT USDT (1R)"
echo -e "  Reward:    $PROFIT_3R USDT (3R)"
echo -e "  R:R Ratio: 1:3"
echo ""

# Calculate break-even win rate
BREAK_EVEN=$(echo "scale=1; 1 / 4 * 100" | bc)
echo -e "${BLUE}To Break Even:${NC}"
echo -e "  Need $BREAK_EVEN% win rate with 1:3 R:R"
echo ""

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}Trailing Stop Strategy:${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo -e "  At $TP1:  Move SL to $ENTRY_PRICE (breakeven)"
echo -e "  At $TP2:  Move SL to $TP1 (lock $PROFIT_1R profit)"
echo -e "  At $TP3:  Close full position or continue trailing"
echo ""

echo -e "${BLUE}================================================================================${NC}"
