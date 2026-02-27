#!/usr/bin/env python3
"""Fetch and analyze recent Binance Futures trades for trading journal"""
import json
import os
from urllib.parse import urlencode
import hmac
import hashlib
import requests
from datetime import datetime
from collections import defaultdict

def load_credentials():
    """Load Binance API credentials from ~/.binance_config"""
    with open(os.path.expanduser('~/.binance_config')) as f:
        creds = {}
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                creds[key] = value
    return creds['BINANCE_API_KEY'], creds['BINANCE_API_SECRET']

def get_user_trades(api_key, api_secret, limit=100):
    """Fetch user trades from Binance Futures API"""
    base_url = 'https://fapi.binance.com'
    endpoint = '/fapi/v1/userTrades'

    timestamp = requests.get(f'{base_url}/fapi/v1/time').json()['serverTime']
    params = {'timestamp': timestamp, 'limit': limit}
    query_string = urlencode(params)
    signature = hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    headers = {'X-MBX-APIKEY': api_key}
    response = requests.get(f'{base_url}{endpoint}?{query_string}&signature={signature}', headers=headers)
    return response.json()

def get_account_balance(api_key, api_secret):
    """Fetch account balance from Binance Futures API"""
    base_url = 'https://fapi.binance.com'
    endpoint = '/fapi/v2/account'

    timestamp = requests.get(f'{base_url}/fapi/v1/time').json()['serverTime']
    params = {'timestamp': timestamp}
    query_string = urlencode(params)
    signature = hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    headers = {'X-MBX-APIKEY': api_key}
    response = requests.get(f'{base_url}{endpoint}?{query_string}&signature={signature}', headers=headers)
    return response.json()

def analyze_trades(trades, account_data=None):
    """Analyze trades and generate performance metrics"""
    if not trades or isinstance(trades, dict) and 'code' in trades:
        print("❌ No trades found or error occurred")
        if isinstance(trades, dict):
            print(f"Error: {trades.get('msg', trades.get('message', 'Unknown error'))}")
        return

    # Group trades by symbol
    grouped = defaultdict(lambda: {'entries': [], 'exits': [], 'pnl': 0, 'fees': 0})

    for trade in trades:
        symbol = trade['symbol']
        pnl = float(trade['realizedPnl'])
        fee = float(trade['commission'])
        qty = float(trade['qty'])
        price = float(trade['price'])

        grouped[symbol]['pnl'] += pnl
        grouped[symbol]['fees'] += fee

        if trade['side'] == 'BUY':
            grouped[symbol]['entries'].append({'qty': qty, 'price': price, 'time': trade['time']})
        else:
            grouped[symbol]['exits'].append({'qty': qty, 'price': price, 'time': trade['time']})

    # Calculate metrics
    total_pnl = sum(g['pnl'] for g in grouped.values())
    total_fees = sum(g['fees'] for g in grouped.values())
    net_pnl = total_pnl - total_fees
    win_trades = sum(1 for g in grouped.values() if g['pnl'] > 0)
    total_trades = len(grouped)
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0

    # Find best and worst trades
    best_symbol = max(grouped.items(), key=lambda x: x[1]['pnl'])
    worst_symbol = min(grouped.items(), key=lambda x: x[1]['pnl'])

    # Print summary
    print("\n" + "="*60)
    print("📊 TRADING PERFORMANCE ANALYSIS")
    print("="*60)

    print(f"\n💰 Account Summary:")
    print(f"   Total Trades Tracked: {len(trades)} individual fills")
    print(f"   Unique Positions: {total_trades}")

    if account_data:
        print(f"\n💵 Current Balance:")
        print(f"   Total Balance: {account_data['totalWalletBalance']} USDT")
        print(f"   Unrealized PnL: {account_data['totalUnrealizedProfit']} USDT")
        print(f"   Available: {account_data['availableBalance']} USDT")

    print(f"\n📈 PnL Breakdown:")
    print(f"   Gross Realized PnL: {total_pnl:+.2f} USDT")
    print(f"   Trading Fees: {total_fees:.2f} USDT")
    print(f"   Net PnL (after fees): {net_pnl:+.2f} USDT")

    print(f"\n🎯 Win Rate:")
    print(f"   Winning Positions: {win_trades}/{total_trades}")
    print(f"   Win Rate: {win_rate:.1f}%")

    if net_pnl > 0:
        print(f"\n✅ Net Profit: {net_pnl:.2f} USDT")
    else:
        print(f"\n❌ Net Loss: {net_pnl:.2f} USDT")

    print(f"\n🏆 Best Trade: {best_symbol[0]}")
    print(f"   PnL: {best_symbol[1]['pnl']:+.2f} USDT")

    print(f"\n📉 Worst Trade: {worst_symbol[0]}")
    print(f"   PnL: {worst_symbol[1]['pnl']:+.2f} USDT")

    # Detailed breakdown by symbol
    print(f"\n" + "="*60)
    print("📋 DETAILED BREAKDOWN BY SYMBOL")
    print("="*60)

    sorted_trades = sorted(grouped.items(), key=lambda x: x[1]['pnl'], reverse=True)

    for symbol, data in sorted_trades:
        net = data['pnl'] - data['fees']
        emoji = "🟢" if data['pnl'] > 0 else "🔴"
        print(f"\n{emoji} {symbol}")
        print(f"   Gross PnL: {data['pnl']:+.2f} USDT | Fees: {data['fees']:.2f} USDT | Net: {net:+.2f} USDT")
        print(f"   Entries: {len(data['entries'])} | Exits: {len(data['exits'])}")

    # Trading insights
    print(f"\n" + "="*60)
    print("💡 TRADING INSIGHTS")
    print("="*60)

    if win_rate < 40:
        print("⚠️  Win rate is below 40%. Consider:")
        print("   - Reviewing your entry criteria")
        print("   - Improving stop-loss placement")
        print("   - Waiting for higher conviction setups")

    if win_rate >= 60 and net_pnl < 0:
        print("⚠️  Good win rate but net negative. This suggests:")
        print("   - Your losers are larger than winners")
        print("   - Consider improving risk:reward ratio")
        print("   - Cut losers earlier, let winners run")

    if net_pnl > 0 and win_rate >= 50:
        print("✅ Good performance! Keep tracking and refining.")

    # Check for overtrading
    for symbol, data in sorted_trades:
        total_actions = len(data['entries']) + len(data['exits'])
        if total_actions > 30:
            print(f"\n⚠️  {symbol}: High activity detected ({total_actions} actions)")
            print("   Consider if this frequency is optimal")

    print("\n" + "="*60)

    return {
        'total_pnl': total_pnl,
        'total_fees': total_fees,
        'net_pnl': net_pnl,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'win_trades': win_trades,
        'best_trade': {'symbol': best_symbol[0], 'pnl': best_symbol[1]['pnl']},
        'worst_trade': {'symbol': worst_symbol[0], 'pnl': worst_symbol[1]['pnl']}
    }

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Analyze Binance Futures trades')
    parser.add_argument('--limit', type=int, default=100, help='Number of trades to fetch')
    parser.add_argument('--with-balance', action='store_true', help='Include account balance')
    args = parser.parse_args()

    api_key, api_secret = load_credentials()

    account_data = None
    if args.with_balance:
        account_data = get_account_balance(api_key, api_secret)

    trades = get_user_trades(api_key, api_secret, limit=args.limit)
    analyze_trades(trades, account_data)
