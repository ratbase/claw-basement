#!/usr/bin/env python3
"""
Calculate trading metrics from Binance Futures trades
Usage: ./calculate_metrics.py <trades_json_file>
"""

import json
import sys
from collections import defaultdict
from datetime import datetime

def calculate_metrics(trades):
    """Calculate R:R, Risk%, and other metrics from trades"""
    
    # Group trades by symbol and side
    positions = defaultdict(lambda: {'trades': [], 'realized_pnl': 0})
    
    for trade in trades:
        symbol = trade['symbol']
        side = trade['side']
        price = float(trade['price'])
        qty = float(trade['qty'])
        commission = float(trade['commission'])
        real_pnl = float(trade['realizedPnl'])
        
        positions[(symbol, side)]['trades'].append({
            'price': price,
            'qty': qty,
            'commission': commission,
            'realized_pnl': real_pnl,
            'time': trade['time']
        })
        positions[(symbol, side)]['realized_pnl'] += real_pnl
    
    # Calculate metrics for each position
    results = []
    for key, data in positions.items():
        symbol, side = key
        trades_list = sorted(data['trades'], key=lambda x: x['time'])
        
        entry = trades_list[0]
        exit = trades_list[-1]
        
        # Calculate entry and exit prices
        entry_price = entry['price']
        exit_price = exit['price']
        
        # Calculate position value (using entry)
        position_value = entry_price * entry['qty']
        
        # Assume stop loss based on typical risk (you can customize this)
        # For now, estimate based on trade PnL and position value
        risk_amount = abs(data['realized_pnl']) if data['realized_pnl'] < 0 else position_value * 0.01
        
        # Estimate account balance (you should update this)
        estimated_balance = 10000  # Update with your actual balance
        
        # Calculate metrics
        risk_pct = (risk_amount / estimated_balance) * 100
        
        # Estimate R:R based on PnL
        reward = abs(data['realized_pnl']) if data['realized_pnl'] > 0 else 0
        rr = reward / risk_amount if risk_amount > 0 else 0
        
        results.append({
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'realized_pnl': data['realized_pnl'],
            'risk_pct': risk_pct,
            'rr': rr,
            'is_winner': data['realized_pnl'] > 0
        })
    
    return results

def print_summary(results):
    """Print trading summary"""
    if not results:
        print("No trades found")
        return
    
    total_trades = len(results)
    winners = sum(1 for r in results if r['is_winner'])
    win_rate = (winners / total_trades) * 100
    
    total_pnl = sum(r['realized_pnl'] for r in results)
    avg_rr = sum(r['rr'] for r in results) / total_trades
    avg_risk = sum(r['risk_pct'] for r in results) / total_trades
    
    print("\n=== Trading Journal Analysis ===\n")
    
    print(f"📈 Recent Trades (Last {total_trades}):")
    for i, trade in enumerate(results[-10:], 1):
        status = "✅" if trade['is_winner'] else "❌"
        emoji = "📈" if trade['is_winner'] else "📉"
        side_emoji = "🟢" if trade['side'] == 'BUY' else "🔴"
        print(f"[{i}] {side_emoji} {trade['symbol']} {trade['side']} | {emoji} ${trade['realized_pnl']:+.2f} (1:{trade['rr']:.2f} R:R) | Risk: {trade['risk_pct']:.2f}% {status}")
    
    print(f"\n📊 Performance Summary:")
    print(f"- Total Trades: {total_trades}")
    print(f"- Win Rate: {win_rate:.1f}% ({winners}/{total_trades})")
    print(f"- Avg R:R: 1:{avg_rr:.2f}")
    print(f"- Avg Risk per Trade: {avg_risk:.2f}%")
    print(f"- Net PnL: ${total_pnl:+.2f}")
    
    # Risk compliance
    low_risk = sum(1 for r in results if r['risk_pct'] <= 2)
    high_rr = sum(1 for r in results if r['rr'] >= 2)
    
    print(f"\n📉 Risk Management:")
    print(f"- Trades with Risk% ≤ 2%: {low_risk}/{total_trades} ({low_risk/total_trades*100:.0f}%)")
    print(f"- Trades with R:R ≥ 1:2: {high_rr}/{total_trades} ({high_rr/total_trades*100:.0f}%)")
    print(f"- Risk Compliance: {(low_risk/total_trades * 100):.0f}%")
    
    # Suggestions
    print(f"\n💡 Suggestions:")
    
    if avg_risk > 2:
        print("1. ⚠️ Risk% is above 2% average - reduce position sizes")
    elif avg_risk > 1.5:
        print("1. ✅ Risk% is in acceptable range (1-2%) - consider reducing to 1-1.5% for optimal risk management")
    else:
        print("1. ✅ Excellent risk discipline! Risk% well within optimal range")
    
    if avg_rr < 2:
        print("2. ⚠️ R:R below 1:2 target - be more selective on entries, wait for clearer setups")
    elif avg_rr < 3:
        print("2. ✅ R:R is decent (target 1:2+) - look for opportunities with 1:3+ for better returns")
    else:
        print("2. ✅ Excellent R:R! Great trade selection")
    
    if win_rate < 33:
        print("3. ⚠️ Win rate low - with 1:2 R:R you need 33%+ to break even. Review entry quality")
    elif win_rate < 40:
        print("3. ✅ Win rate acceptable - focus on maintaining discipline and R:R")
    else:
        print("3. ✅ Strong win rate! Keep doing what you're doing")
    
    # Check for consecutive losses
    consecutive_losses = 0
    max_consecutive = 0
    for trade in reversed(results):
        if not trade['is_winner']:
            consecutive_losses += 1
            max_consecutive = max(max_consecutive, consecutive_losses)
        else:
            consecutive_losses = 0
    
    if max_consecutive >= 3:
        print(f"4. ⚠️ {max_consecutive} consecutive losses detected - consider taking a trading break")
    
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./calculate_metrics.py <trades_json_file>")
        print("Example: ./calculate_metrics.py trades.json")
        sys.exit(1)
    
    with open(sys.argv[1], 'r') as f:
        trades = json.load(f)
    
    results = calculate_metrics(trades)
    print_summary(results)
