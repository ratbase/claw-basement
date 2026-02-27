#!/bin/bash
# trading-journal.sh - Analyze your Binance Futures trades
#
# Usage:
#   ./trading-journal.sh              # Analyze last 100 trades
#   ./trading-journal.sh --limit 500  # Analyze last 500 trades
#   ./trading-journal.sh --full       # Analyze with account balance

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/analyze_trades.py"

# Check if config exists
if [ ! -f ~/.binance_config ]; then
    echo "❌ Error: ~/.binance_config not found!"
    echo "Please create ~/.binance_config with your Binance API credentials:"
    echo ""
    echo "BINANCE_API_KEY=your_api_key_here"
    echo "BINANCE_API_SECRET=your_api_secret_here"
    exit 1
fi

# Run the Python script
python3 "$PYTHON_SCRIPT" "$@"
