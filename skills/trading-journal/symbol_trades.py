#!/usr/bin/env python3
"""Fetch recent trades for a specific symbol from Binance Futures"""
import json
import os
from urllib.parse import urlencode
import hmac
import hashlib
import requests
from datetime import datetime

def load_credentials():
    """Load Binance API credentials from ~/.binance_config"""
    with open(os.path.expanduser('~/.binance_config')) as f:
        creds = {}
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                creds[key] = value
    return creds['BINANCE_API_KEY'], creds['BINANCE_API_SECRET']

def get_symbol_trades(api_key, api_secret, symbol, limit=50):
    """Fetch trades for specific symbol from Binance Futures API"""
    base_url = 'https://fapi.binance.com'
    endpoint = '/fapi/v1/userTrades'

    timestamp = requests.get(f'{base_url}/fapi/v1/time').json()['serverTime']
    params = {'timestamp': timestamp, 'symbol': symbol, 'limit': limit}
    query_string = urlencode(params)
    signature = hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    headers = {'X-MBX-APIKEY': api_key}
    response = requests.get(f'{base_url}{endpoint}?{query_string}&signature={signature}', headers=headers)
    return response.json()

def format_time(ms):
    """Convert milliseconds to readable datetime"""
    return datetime.fromtimestamp(ms / 1000).strftime('%Y-%m-%d %H:%M:%S')

def print_trades(trades):
    """Print trades in readable format"""
    if not trades or isinstance(trades, dict) and 'code' in trades:
        print(f"❌ Error fetching trades: {trades.get('msg', 'Unknown error')}")
        return

    print("\n" + "="*80)
    print(f"📊 RECENT TRADES FOR {trades[0]['symbol']} ({len(trades)} trades)")
    print("="*80)

    print(f"\n{'Time':<20} {'Side':<6} {'Qty':<12} {'Price':<12} {'Fee':<12} {'Realized PnL'}")
    print("-"*80)

    total_pnl = 0
    for trade in trades:
        time_str = format_time(trade['time'])
        side = trade['side']
        qty = trade['qty']
        price = trade['price']
        fee = f"{float(trade['commission']):.4f}"
        pnl = f"{float(trade['realizedPnl']):+.2f}"
        total_pnl += float(trade['realizedPnl'])

        print(f"{time_str:<20} {side:<6} {qty:<12} {price:<12} {fee:<12} {pnl}")

    print("-"*80)
    print(f"Total Realized PnL: {total_pnl:+.2f} USDT")
    print("="*80)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Fetch trades for specific symbol')
    parser.add_argument('symbol', help='Trading pair symbol (e.g., SOLUSDT)')
    parser.add_argument('--limit', type=int, default=50, help='Number of trades to fetch')
    args = parser.parse_args()

    api_key, api_secret = load_credentials()
    trades = get_symbol_trades(api_key, api_secret, args.symbol, limit=args.limit)
    print_trades(trades)
