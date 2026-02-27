---
name: binance-futures
description: Interact with Binance Futures API — account data, positions, orders, WebSocket streams, funding rates, liquidations, and advanced order types. Production-grade with v3 endpoints, rate limiting, and proper secret management.
metadata: {"nanobot":{"emoji":"💹","requires":{"bins":["curl","python3"],"libs":[]}}}
---

# Binance Futures Skill 💹

Production-grade Binance Futures API interaction — account monitoring, position management, order placement, real-time WebSocket streams, funding rate analysis, and liquidation tracking.

## ⚠️ Secret Management (CRITICAL)

**NEVER hardcode API keys in scripts or commit them to version control.**

### Canonical Secret Location: `~/.binance_config`

```bash
# ~/.binance_config (chmod 600 this file!)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

Set permissions immediately after creating:
```bash
chmod 600 ~/.binance_config
```

### Loading in Shell Scripts

```bash
#!/bin/bash
source ~/.binance_config || {
  echo "ERROR: ~/.binance_config not found."
  echo "Copy references/.binance_config.example to ~/.binance_config and fill in your keys."
  exit 1
}
```

### Loading in Python Scripts

```python
import os
from pathlib import Path
from dotenv import load_dotenv

def load_binance_credentials():
    """Load credentials with fallback priority."""
    # Priority 1: Environment variables (CI/CD, shell export)
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    if api_key and api_secret:
        return api_key, api_secret

    # Priority 2: ~/.binance_config
    config_file = Path.home() / '.binance_config'
    if config_file.exists():
        load_dotenv(config_file)
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        if api_key and api_secret:
            return api_key, api_secret

    # Priority 3: ~/.config/binance/credentials (XDG standard)
    xdg_config = Path.home() / '.config' / 'binance' / 'credentials'
    if xdg_config.exists():
        load_dotenv(xdg_config)
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        if api_key and api_secret:
            return api_key, api_secret

    raise ValueError(
        "No Binance credentials found.\n"
        "Create ~/.binance_config with BINANCE_API_KEY and BINANCE_API_SECRET."
    )
```

### API Key Permissions (Minimum Required)

| Permission | Setting | Reason |
|---|---|---|
| Futures Trading | ✅ Enable | Required for trading |
| Spot Trading | ❌ Disable | Not needed |
| Withdrawals | ❌ NEVER | Massive security risk |
| IP Restriction | ✅ Whitelist | Critical - lock to your IP |
| Margin Trading | ❌ Disable | Not needed |

---

## Prerequisites

```bash
# bf.py uses pure Python stdlib — zero pip installs needed
# Optional (only if using SDK-based Python scripts separately):
pip install python-binance ccxt python-dotenv
```


## 🚀 Quick Start — `bf.py` CLI

`scripts/bf.py` is the **unified data tool** — replaces all individual shell scripts.
Pure Python stdlib, zero dependencies, auto-loads credentials from `~/.binance_config`.

```bash
# Make executable once
chmod +x skills/binance-futures/scripts/bf.py

# Account summary (v3)
./bf.py account

# Quick balance
./bf.py balance

# Open positions (v3 — returns only active positions, not all 300 symbols)
./bf.py positions

# Income + PnL — last 90 days (auto-paginated)
./bf.py income

# Income — full year
./bf.py income --days 365

# Income — filter by symbol and type
./bf.py income --symbol BTCUSDT --type REALIZED_PNL

# Trade history — last 30 days
./bf.py trades

# Trade history — specific symbol
./bf.py trades --symbol ETHUSDT --days 90

# Raw JSON output (pipe to jq)
./bf.py positions --raw | jq '.[0]'

# Risk:Reward calculator (no API key needed)
./bf.py rr 50000 48000
./bf.py rr 50000 48000 --balance 1000 --risk 2 --leverage 10
./bf.py rr 0.50 0.46 --target 2.5
```

| Command | v3 Endpoint | Description |
|---------|-------------|-------------|
| `account` | `/fapi/v3/account` | Full account summary with margin usage |
| `balance` | `/fapi/v3/balance` | Quick wallet + available balance |
| `positions` | `/fapi/v3/positionRisk` | Active positions only (efficient) |
| `income` | `/fapi/v1/income` | Paginated income/PnL history |
| `trades` | `/fapi/v1/userTrades` | Historical trade records |
| `rr` | — | R:R calculator, position sizing, TP levels |


## Recommended: Python SDK (over raw curl)

Use the official `binance-futures-connector` or `ccxt` for production. Raw curl is fine for ad-hoc testing but not recommended for scripts.

### Option A: Official SDK

```python
from binance.futures import Futures

api_key, api_secret = load_binance_credentials()
client = Futures(key=api_key, secret=api_secret)

# HMAC signing handled automatically
# Rate limit headers tracked automatically
```

### Option B: CCXT (Multi-exchange portability)

```python
import ccxt

api_key, api_secret = load_binance_credentials()
exchange = ccxt.binanceusdm({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,  # Built-in rate limit management
    'options': {'defaultType': 'future'}
})
```

---

## API Endpoints Reference (v3 — Current)

> **Important**: v2 account/balance/positionRisk endpoints are **deprecated**. Always use v3.

### Base URLs
- **USDⓈ-M Futures**: `https://fapi.binance.com`
- **COIN-M Futures**: `https://dapi.binance.com`
- **WebSocket USDⓈ-M**: `wss://fstream.binance.com`
- **WebSocket COIN-M**: `wss://dstream.binance.com`
- **WebSocket API**: `wss://ws-fapi.binance.com/ws-fapi/v1`

---

## Account Information

### Account Summary (v3 — use this, not v2)

```bash
#!/bin/bash
source ~/.binance_config

TIMESTAMP=$(python3 -c "import time; print(int(time.time() * 1000))")
SIGNATURE=$(echo -n "timestamp=$TIMESTAMP" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | awk '{print $2}')

curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v3/account?timestamp=$TIMESTAMP&signature=$SIGNATURE" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Wallet Balance:    {float(data[\"totalWalletBalance\"]):,.2f} USDT')
print(f'Margin Balance:    {float(data[\"totalMarginBalance\"]):,.2f} USDT')
print(f'Available:         {float(data[\"availableBalance\"]):,.2f} USDT')
print(f'Unrealized PnL:    {float(data[\"totalUnrealizedProfit\"]):+,.2f} USDT')
print(f'Portfolio Heat:    {(float(data[\"totalPositionInitialMargin\"]) / float(data[\"totalMarginBalance\"]) * 100):.1f}%')
"
```

### Balance (v3)

```bash
source ~/.binance_config
TIMESTAMP=$(python3 -c "import time; print(int(time.time() * 1000))")
SIGNATURE=$(echo -n "timestamp=$TIMESTAMP" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | awk '{print $2}')

curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v3/balance?timestamp=$TIMESTAMP&signature=$SIGNATURE" | jq '.[] | select(.balance | tonumber > 0)'
```

### Positions — Open Only (v3 — more efficient than v2)

```bash
source ~/.binance_config
TIMESTAMP=$(python3 -c "import time; print(int(time.time() * 1000))")
SIGNATURE=$(echo -n "timestamp=$TIMESTAMP" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | awk '{print $2}')

# v3 returns ONLY symbols with active positions (v2 returns all symbols = 300+ rows)
curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v3/positionRisk?timestamp=$TIMESTAMP&signature=$SIGNATURE" | \
  python3 -c "
import sys, json
positions = json.load(sys.stdin)
for p in positions:
    side = 'LONG' if float(p['positionAmt']) > 0 else 'SHORT'
    pnl_pct = float(p['unRealizedProfit']) / (abs(float(p['positionAmt'])) * float(p['entryPrice'])) * 100
    print(f\"{p['symbol']:<15} {side:<6} | Entry: {float(p['entryPrice']):>10.4f} | Mark: {float(p['markPrice']):>10.4f} | PnL: {float(p['unRealizedProfit']):>+10.2f} ({pnl_pct:+.1f}%) | Lev: {p['leverage']}x\")
"
```

### Symbol & Account Config (NEW 2024)

```bash
# User symbol configuration (leverage, margin type per symbol)
curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v1/symbolConfig?timestamp=$TIMESTAMP&signature=$SIGNATURE"

# Account-level configuration
curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v1/accountConfig?timestamp=$TIMESTAMP&signature=$SIGNATURE"
```

---

## Orders

### Place Standard Orders

```python
from binance.futures import Futures
api_key, api_secret = load_binance_credentials()
client = Futures(key=api_key, secret=api_secret)

# Market order
order = client.new_order(
    symbol='BTCUSDT',
    side='BUY',
    type='MARKET',
    quantity='0.001',
    positionSide='LONG'  # Required in hedge mode
)

# Limit order with Self-Trade Prevention (NEW 2024)
order = client.new_order(
    symbol='BTCUSDT',
    side='BUY',
    type='LIMIT',
    timeInForce='GTC',
    quantity='0.001',
    price='90000',
    selfTradePreventionMode='EXPIRE_TAKER'  # NONE | EXPIRE_TAKER | EXPIRE_MAKER | EXPIRE_BOTH
)

# Limit order with Price Match (NEW 2024) — auto-set price at best bid/ask
order = client.new_order(
    symbol='BTCUSDT',
    side='BUY',
    type='LIMIT',
    timeInForce='GTC',
    quantity='0.001',
    priceMatch='OPPONENT'  # OPPONENT | OPPONENT_5 | QUEUE | QUEUE_5 | etc.
)

# Iceberg order (hidden quantity) — up to 50 parts (100 from March 2026)
order = client.new_order(
    symbol='BTCUSDT',
    side='BUY',
    type='LIMIT',
    timeInForce='GTC',
    quantity='1.0',
    price='90000',
    icebergQty='0.1'  # Visible portion; 0.9 BTC hidden
)
```

### Advanced Algo Orders (NEW Dec 2025 — Mandatory)

> **CRITICAL**: Conditional orders (STOP_MARKET, TAKE_PROFIT_MARKET, etc.) moved to Algo Service.
> The old `/fapi/v1/order` endpoints for these types now return `-4120` error.

```python
# NEW: Place conditional/trailing stop via algo service
import requests, hmac, hashlib, time, urllib.parse

def place_algo_order(symbol, side, order_type, quantity, **kwargs):
    api_key, api_secret = load_binance_credentials()
    params = {
        'symbol': symbol,
        'side': side,
        'type': order_type,
        'quantity': quantity,
        'timestamp': int(time.time() * 1000),
        **kwargs
    }
    query = urllib.parse.urlencode(params)
    signature = hmac.new(api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    params['signature'] = signature

    response = requests.post(
        'https://fapi.binance.com/fapi/v1/algoOrder',
        headers={'X-MBX-APIKEY': api_key},
        params=params
    )
    return response.json()

# Trailing Stop (via algo service)
order = place_algo_order(
    symbol='BTCUSDT',
    side='SELL',
    order_type='TRAILING_STOP_MARKET',
    quantity='0.001',
    trailingDelta=100,    # 100 BIPs = 1% trailing
    reduceOnly=True,
    workingType='MARK_PRICE'
)

# Stop Loss (via algo service)
order = place_algo_order(
    symbol='BTCUSDT',
    side='SELL',
    order_type='STOP',
    quantity='0.001',
    stopPrice='85000',
    price='84900'
)

# Take Profit (via algo service)
order = place_algo_order(
    symbol='BTCUSDT',
    side='SELL',
    order_type='TAKE_PROFIT',
    quantity='0.001',
    stopPrice='100000',
    price='99900'
)
```

### TWAP Orders (Institutional Execution — NEW 2025)

Time-Weighted Average Price orders split execution across a time window to minimize market impact.

```python
# POST /sapi/v1/algo/futures/newOrderTwap
params = {
    'symbol': 'BTCUSDT',
    'side': 'BUY',
    'quantity': '0.1',
    'duration': 3600,     # 1 hour window [300s to 86400s]
    'clientAlgoId': 'my-twap-001',  # Unique ID, max 32 chars
    'timestamp': int(time.time() * 1000)
}
# Constraints: notional 1,000–1,000,000 USDT, max 30 open TWAP orders
```

### Query / Cancel Algo Orders

```bash
source ~/.binance_config
TIMESTAMP=$(python3 -c "import time; print(int(time.time() * 1000))")
SIGNATURE=$(echo -n "timestamp=$TIMESTAMP" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | awk '{print $2}')

# Open algo orders
curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v1/openAlgoOrders?timestamp=$TIMESTAMP&signature=$SIGNATURE" | jq '.'

# All algo orders history
curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v1/allAlgoOrders?timestamp=$TIMESTAMP&signature=$SIGNATURE" | jq '.'
```

---

## Funding Rates

### Current Funding Rate + Next Funding Time

```bash
# No auth required for public data
curl -s "https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT" | \
  python3 -c "
import sys, json
from datetime import datetime
d = json.load(sys.stdin)
funding_rate = float(d['lastFundingRate']) * 100
next_funding = datetime.fromtimestamp(d['nextFundingTime']/1000).strftime('%H:%M:%S')
print(f\"Funding Rate:   {funding_rate:+.4f}% (every 8h)\")
print(f\"Next Funding:   {next_funding}\")
print(f\"Mark Price:     {float(d['markPrice']):,.2f}\")
print(f\"Index Price:    {float(d['indexPrice']):,.2f}\")
print(f\"Basis:          {float(d['markPrice']) - float(d['indexPrice']):+.2f}\")
"
```

### Historical Funding Rates

```python
import requests
from datetime import datetime

def get_funding_history(symbol, limit=100):
    response = requests.get(
        'https://fapi.binance.com/fapi/v1/fundingRate',
        params={'symbol': symbol, 'limit': limit}
    )
    rates = response.json()
    for r in rates:
        dt = datetime.fromtimestamp(r['fundingTime']/1000).strftime('%Y-%m-%d %H:%M')
        rate = float(r['fundingRate']) * 100
        print(f"{dt}  {rate:+.4f}%  (mark: {float(r['markPrice']):,.2f})")

get_funding_history('BTCUSDT')
```

### All Symbols Funding Rate Scan (for funding arb opportunities)

```python
import requests

def scan_funding_rates(threshold_pct=0.05):
    """Find symbols with extreme funding rates (arb opportunities)."""
    response = requests.get('https://fapi.binance.com/fapi/v1/premiumIndex')
    rates = response.json()

    extreme = [(r['symbol'], float(r['lastFundingRate'])*100) for r in rates
               if abs(float(r['lastFundingRate'])*100) > threshold_pct]
    extreme.sort(key=lambda x: abs(x[1]), reverse=True)

    print(f"{'Symbol':<20} {'Funding Rate':>15}")
    print("-" * 40)
    for symbol, rate in extreme[:20]:
        arrow = "🔴" if rate > 0 else "🟢"  # Positive = longs pay, negative = shorts pay
        print(f"{symbol:<20} {rate:>+14.4f}% {arrow}")

scan_funding_rates()
```

---

## Liquidation Monitoring

### Force Liquidation Stream (WebSocket)

```python
import asyncio
import websockets
import json

async def monitor_liquidations(symbol='BTCUSDT'):
    """Monitor forced liquidations in real-time."""
    uri = f"wss://fstream.binance.com/ws/{symbol.lower()}@forceOrder"

    async with websockets.connect(uri) as ws:
        print(f"Monitoring liquidations for {symbol}...")
        async for message in ws:
            data = json.loads(message)
            order = data['o']
            side = order['S']
            qty = float(order['q'])
            price = float(order['ap'])  # Average fill price
            value = qty * price
            print(f"LIQUIDATION {side}: {qty} @ {price:,.2f} = ${value:,.0f}")

asyncio.run(monitor_liquidations())
```

### Insurance Fund Balance

```bash
source ~/.binance_config

curl -s "https://fapi.binance.com/fapi/v1/insuranceBalance" | \
  python3 -c "import sys, json; d = json.load(sys.stdin); [print(f\"{b['asset']}: {float(b['balance']):,.2f}\") for b in d['balances']]"
```

### ADL Risk (Auto-Deleverage Risk Score)

```bash
source ~/.binance_config
TIMESTAMP=$(python3 -c "import time; print(int(time.time() * 1000))")
SIGNATURE=$(echo -n "timestamp=$TIMESTAMP&symbol=BTCUSDT" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | awk '{print $2}')

# adlQuantile: 0-5, where 5 = highest risk of auto-deleveraging
curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v1/symbolAdlRisk?symbol=BTCUSDT&timestamp=$TIMESTAMP&signature=$SIGNATURE"
```

---

## WebSocket Streams

See [websocket-streams.md](references/websocket-streams.md) for full stream documentation.

### Quick Reference

| Stream | Name | Use Case |
|--------|------|----------|
| Mark Price | `<sym>@markPrice@1s` | Funding rate, mark price updates |
| Agg Trades | `<sym>@aggTrade` | Real-time trade flow (100ms) |
| Book Ticker | `<sym>@bookTicker` | Best bid/ask, OBI calculation |
| Force Order | `<sym>@forceOrder` | Liquidation cascade monitoring |
| User Data | Listen Key stream | Account updates, fills |

### User Data Stream (Account Updates)

```python
import requests, asyncio, websockets, json

def create_listen_key(api_key):
    """Create user data stream listen key (expires 60 min, renew every 30 min)."""
    response = requests.post(
        'https://fapi.binance.com/fapi/v1/listenKey',
        headers={'X-MBX-APIKEY': api_key}
    )
    return response.json()['listenKey']

def renew_listen_key(api_key, listen_key):
    """Renew listen key — call every 30 minutes."""
    requests.put(
        'https://fapi.binance.com/fapi/v1/listenKey',
        headers={'X-MBX-APIKEY': api_key},
        params={'listenKey': listen_key}
    )

async def stream_account_updates():
    api_key, _ = load_binance_credentials()
    listen_key = create_listen_key(api_key)

    uri = f"wss://fstream.binance.com/ws/{listen_key}"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            event = json.loads(message)
            event_type = event.get('e')

            if event_type == 'ORDER_TRADE_UPDATE':
                o = event['o']
                print(f"ORDER: {o['s']} {o['S']} {o['X']} qty={o['q']} price={o['p']}")
            elif event_type == 'ACCOUNT_UPDATE':
                for balance in event['a']['B']:
                    print(f"BALANCE: {balance['a']} = {balance['wb']}")
            elif event_type == 'MARGIN_CALL':
                print(f"⚠️ MARGIN CALL: {event}")
```

---

## Rate Limit Management

### Rate Limit Headers (check after every request)

| Header | Meaning |
|--------|---------|
| `X-MBX-USED-WEIGHT-1M` | IP weight used in current minute |
| `X-MBX-ORDER-COUNT-10S` | Orders placed in last 10 seconds |
| `X-MBX-ORDER-COUNT-1M` | Orders placed in last minute |

### Rate-Limit-Aware Client

```python
import time
import requests
from threading import Lock

class BinanceRateLimitedClient:
    """Tracks rate limits from response headers and backs off appropriately."""

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.weight_used = 0
        self.weight_limit = 6000  # Per minute
        self.lock = Lock()

    def request(self, method, endpoint, params=None, signed=True):
        if signed:
            params = params or {}
            params['timestamp'] = int(time.time() * 1000)
            query = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
            params['signature'] = hmac.new(
                self.api_secret.encode(), query.encode(), hashlib.sha256
            ).hexdigest()

        response = requests.request(
            method,
            f"https://fapi.binance.com{endpoint}",
            headers={'X-MBX-APIKEY': self.api_key},
            params=params
        )

        # Track weight usage
        weight = int(response.headers.get('X-MBX-USED-WEIGHT-1M', 0))
        with self.lock:
            self.weight_used = weight

        # Handle rate limit errors
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            return self.request(method, endpoint, params, signed)

        if response.status_code == 418:
            print("⛔ IP banned by Binance. Waiting 5 minutes...")
            time.sleep(300)
            return self.request(method, endpoint, params, signed)

        response.raise_for_status()
        return response.json()
```

### Error Handling for 503

```python
def safe_request_with_retry(func, max_retries=5):
    """Handle Binance 503 responses correctly."""
    for attempt in range(max_retries):
        try:
            response = func()
            return response
        except requests.HTTPError as e:
            if e.response.status_code == 503:
                msg = e.response.json().get('msg', '')
                if 'Unknown error' in msg:
                    # Status UNKNOWN — check via WebSocket before retrying
                    # DO NOT duplicate the order without confirming it failed
                    print("⚠️ Unknown 503 — verify order status before retry")
                    return None
                # 'Service Unavailable' = definite failure, safe to retry
            backoff = min(0.2 * (2 ** attempt), 5.0)
            time.sleep(backoff)
    raise Exception(f"Failed after {max_retries} attempts")
```

---

## RSA Key Signing (More Secure Than HMAC)

```bash
# 1. Generate RSA key pair (do this once)
openssl genpkey -algorithm RSA -out ~/.binance_rsa_private.pem 2048
openssl rsa -in ~/.binance_rsa_private.pem -pubout -out ~/.binance_rsa_public.pem
chmod 600 ~/.binance_rsa_private.pem

# 2. Upload public key to Binance API settings
# 3. Use private key to sign requests
```

```python
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import base64

def sign_with_rsa(payload: str, private_key_path: str) -> str:
    """Sign payload with RSA private key."""
    with open(private_key_path, 'rb') as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    signature = private_key.sign(payload.encode(), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(signature).decode()
```

---

## Multi-Asset & Margin Configuration

### Check and Set Leverage

```python
# Get current leverage for a symbol
result = client.futures_leverage_bracket(symbol='BTCUSDT')

# Set leverage
client.futures_change_leverage(symbol='BTCUSDT', leverage=10)
```

### Margin Type (Cross vs Isolated)

```python
# Switch to isolated margin
client.futures_change_margin_type(symbol='BTCUSDT', marginType='ISOLATED')

# Switch to cross margin
client.futures_change_margin_type(symbol='BTCUSDT', marginType='CROSSED')
```

### Position Mode (One-Way vs Hedge)

```python
# Check current mode
result = client.futures_get_position_mode()
# {'dualSidePosition': True} = Hedge Mode

# Enable hedge mode (hold LONG + SHORT simultaneously)
client.futures_change_position_mode(dualSidePosition=True)
```

---

## Income History & PnL Analysis

```python
from binance.client import Client
from datetime import datetime, timedelta

api_key, api_secret = load_binance_credentials()
client = Client(api_key, api_secret)

def get_income_history(days=30, income_types=None):
    """Fetch income history with breakdown by type."""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    all_income = []
    current_start = int(start_time.timestamp() * 1000)
    end_ts = int(end_time.timestamp() * 1000)

    while current_start < end_ts:
        batch = client.futures_income_history(
            startTime=current_start,
            endTime=end_ts,
            limit=1000
        )
        if not batch:
            break
        all_income.extend(batch)
        if len(batch) < 1000:
            break
        current_start = int(batch[-1]['time']) + 1

    # Aggregate by type
    totals = {}
    for record in all_income:
        income_type = record['incomeType']
        totals[income_type] = totals.get(income_type, 0) + float(record['income'])

    return totals

totals = get_income_history(days=30)
print(f"Realized PnL:  {totals.get('REALIZED_PNL', 0):+.2f} USDT")
print(f"Funding Fees:  {totals.get('FUNDING_FEE', 0):+.2f} USDT")
print(f"Commission:    {totals.get('COMMISSION', 0):+.2f} USDT")
net = totals.get('REALIZED_PNL', 0) + totals.get('COMMISSION', 0)
print(f"Net:           {net:+.2f} USDT")
```

---

## Portfolio Risk Dashboard

```python
def portfolio_risk_dashboard():
    """Print a comprehensive risk overview."""
    api_key, api_secret = load_binance_credentials()
    client = Futures(key=api_key, secret=api_secret)

    account = client.account()
    positions = client.get_position_risk()
    open_positions = [p for p in positions if float(p['positionAmt']) != 0]

    wallet = float(account['totalWalletBalance'])
    margin_balance = float(account['totalMarginBalance'])
    available = float(account['availableBalance'])
    unrealized_pnl = float(account['totalUnrealizedProfit'])
    initial_margin = float(account['totalPositionInitialMargin'])
    maint_margin = float(account['totalMaintMargin'])

    portfolio_heat = initial_margin / margin_balance * 100 if margin_balance > 0 else 0
    margin_ratio = maint_margin / margin_balance * 100 if margin_balance > 0 else 0

    print("=" * 65)
    print("PORTFOLIO RISK DASHBOARD")
    print("=" * 65)
    print(f"Wallet Balance:       {wallet:>12,.2f} USDT")
    print(f"Margin Balance:       {margin_balance:>12,.2f} USDT")
    print(f"Available Balance:    {available:>12,.2f} USDT")
    print(f"Unrealized PnL:       {unrealized_pnl:>+12,.2f} USDT")
    print(f"Portfolio Heat:       {portfolio_heat:>11.1f}%  {'⚠️' if portfolio_heat > 50 else '✅'}")
    print(f"Maintenance Margin:   {margin_ratio:>11.1f}%  {'🔴 HIGH RISK' if margin_ratio > 80 else '✅'}")
    print()
    print(f"{'Symbol':<15} {'Side':<6} {'Size':>10} {'Entry':>12} {'Mark':>12} {'PnL':>12} {'Lev':>5}")
    print("-" * 75)
    for p in sorted(open_positions, key=lambda x: abs(float(x['unRealizedProfit'])), reverse=True):
        side = "LONG" if float(p['positionAmt']) > 0 else "SHORT"
        pnl = float(p['unRealizedProfit'])
        print(f"{p['symbol']:<15} {side:<6} {float(p['positionAmt']):>10.4f} "
              f"{float(p['entryPrice']):>12.4f} {float(p['markPrice']):>12.4f} "
              f"{pnl:>+12.2f} {p['leverage']:>4}x")

portfolio_risk_dashboard()
```

---

## Key Metrics Explained

| Metric | Description | Risk Signal |
|--------|-------------|------------|
| `totalWalletBalance` | Total balance including unrealized PnL | Baseline |
| `availableBalance` | Can open new positions with this | < 20% = tight |
| `totalUnrealizedProfit` | Sum of all open position PnL | Volatile |
| `totalPositionInitialMargin` | Margin locked in positions | Portfolio heat |
| `totalMaintMargin` | Min margin to keep positions open | Liquidation risk |
| `totalCrossUnPnl` | Unrealized PnL in cross-margin positions | Contagion risk |
| `adlQuantile` | 0-5 ADL risk score (5 = highest) | > 3 = reduce position |

**Portfolio Heat** = `totalPositionInitialMargin / totalMarginBalance × 100`
- < 30%: Conservative
- 30-70%: Normal
- > 70%: ⚠️ High risk
- > 90%: 🔴 Liquidation danger zone

---

## Error Codes Reference

| Code | Meaning | Fix |
|------|---------|-----|
| `-1021` | Timestamp outside recvWindow | Sync system clock; increase recvWindow |
| `-2014` | API-key format invalid | Check key for extra spaces |
| `-2015` | Invalid API-key, IP, or permissions | Verify permissions + IP whitelist |
| `-4120` | STOP_ORDER_SWITCH_ALGO | Migrate to `/fapi/v1/algoOrder` endpoint |
| `429` | Rate limit exceeded | Back off, respect Retry-After header |
| `418` | IP banned | Wait 2 min to 3 days (don't retry) |
| `503` | Service unavailable | Check msg: Unknown = verify; Unavailable = retry |

---

## Common Tasks

| Goal | Command |
|------|---------|
| Account balance | `python get_1year_pnl.py` |
| Current positions | Positions script (v3 endpoint) |
| Open orders | `client.get_open_orders()` |
| Funding rates | `scan_funding_rates()` |
| Liquidation monitor | WebSocket forceOrder stream |
| Portfolio risk | `portfolio_risk_dashboard()` |
| Income history | `get_income_history(days=90)` |

---

## References

- [Binance Futures API Docs](https://developers.binance.com/docs/derivatives/usds-margined-futures)
- [Changelog](https://developers.binance.com/docs/derivatives/change-log)
- [Advanced Orders](references/advanced-orders.md)
- [WebSocket Streams](references/websocket-streams.md)
- [python-binance SDK](https://github.com/sammchardy/python-binance)
- [CCXT Library](https://github.com/ccxt/ccxt)
