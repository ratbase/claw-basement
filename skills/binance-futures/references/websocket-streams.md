# Binance Futures WebSocket Streams Reference

## Base URLs

| Market | REST | WebSocket |
|--------|------|-----------|
| USDⓈ-M Futures | `https://fapi.binance.com` | `wss://fstream.binance.com` |
| COIN-M Futures | `https://dapi.binance.com` | `wss://dstream.binance.com` |
| WebSocket Trading API | — | `wss://ws-fapi.binance.com/ws-fapi/v1` |

## Connection Limits (2025-2026)

- **Max streams per connection**: 1,024 (increased from 200)
- **Message rate limit**: 10 messages/second per connection (exceed = disconnect)
- **Ping interval**: Send ping every 3 minutes
- **Pong timeout**: 10 minutes (no pong = disconnect)
- **Max connection lifetime**: 24 hours (auto-disconnect at 24h mark)
- **New connection limit**: 300 connections per 5 minutes per IP

## Connecting to Multiple Streams

```python
# Method 1: Combined stream endpoint (most efficient)
# wss://fstream.binance.com/stream?streams=<stream1>/<stream2>/...

import asyncio
import websockets
import json

async def multi_stream(symbol='BTCUSDT'):
    symbol = symbol.lower()
    streams = [
        f"{symbol}@markPrice@1s",
        f"{symbol}@bookTicker",
        f"{symbol}@aggTrade",
        f"{symbol}@forceOrder"
    ]
    uri = f"wss://fstream.binance.com/stream?streams={'/'.join(streams)}"

    async with websockets.connect(uri) as ws:
        # Keep alive with ping every 3 minutes
        asyncio.create_task(keep_alive(ws))

        async for message in ws:
            data = json.loads(message)
            stream_name = data.get('stream', '')
            payload = data.get('data', data)
            await handle_stream(stream_name, payload)

async def keep_alive(ws):
    while True:
        await asyncio.sleep(180)  # 3 minutes
        await ws.ping()
```

---

## Market Data Streams

### 1. Mark Price Stream (Funding Rate + Mark Price)

**Name**: `<symbol>@markPrice` or `<symbol>@markPrice@1s`

**Update**: 3s (default) or 1s

```json
{
  "e": "markPriceUpdate",
  "E": 1562305380000,     // Event time
  "s": "BTCUSDT",
  "p": "11794.15",        // Mark price
  "i": "11784.62",        // Index price
  "P": "11784.25",        // Estimated settle price (only relevant at delivery)
  "r": "0.00038167",      // Funding rate (multiply by 100 for %)
  "T": 1562306400000      // Next funding time (ms)
}
```

**Use cases**:
- Monitor funding rate changes (positive = longs pay, negative = shorts pay)
- Calculate basis = mark price - index price
- Funding arb signals when rate deviates from fair value

### 2. Aggregate Trade Stream (Trade Flow)

**Name**: `<symbol>@aggTrade`

**Update**: ~100ms (every trade)

```json
{
  "e": "aggTrade",
  "E": 123456789,
  "s": "BTCUSDT",
  "a": 5933014,           // Aggregate trade ID
  "p": "0.001",           // Price
  "q": "100",             // Total quantity (ALL market trades)
  "nq": "100",            // Normal quantity (RPI orders excluded)
  "f": 100,               // First trade ID
  "l": 105,               // Last trade ID
  "T": 123456785,         // Trade time
  "m": true               // Is buyer maker? (true = sell aggressor)
}
```

**Use cases**:
- Trade flow imbalance: `buy_vol - sell_vol / total_vol`
- Detect large single trades (whale activity)
- Volume-weighted price movement analysis

```python
def calculate_trade_flow_imbalance(trades_window):
    """Calculate buy/sell pressure over a time window."""
    buy_vol = sum(t['q'] for t in trades_window if not t['m'])   # buyer is taker = buy
    sell_vol = sum(t['q'] for t in trades_window if t['m'])       # buyer is maker = sell
    total_vol = buy_vol + sell_vol
    if total_vol == 0:
        return 0.0
    return (buy_vol - sell_vol) / total_vol  # +1 = pure buy pressure, -1 = pure sell pressure
```

### 3. Book Ticker Stream (Best Bid/Ask)

**Name**: `<symbol>@bookTicker`

**Update**: Real-time on change

> **Note**: RPI orders are excluded from this stream. Use `<symbol>@rpiDepth@500ms` for RPI-inclusive book.

```json
{
  "e": "bookTicker",
  "u": 400900217,
  "s": "BNBUSDT",
  "b": "25.35190000",     // Best bid price
  "B": "31.21000000",     // Best bid quantity
  "a": "25.36520000",     // Best ask price
  "A": "40.66000000"      // Best ask quantity
}
```

**Use cases**:
- Order Book Imbalance (OBI) at L1: `(bid_qty - ask_qty) / (bid_qty + ask_qty)`
- Spread monitoring for execution quality
- Quote stuffing detection

```python
def order_book_imbalance_l1(book_ticker):
    """L1 Order Book Imbalance — explains ~65% of short-term price variance."""
    bid_qty = float(book_ticker['B'])
    ask_qty = float(book_ticker['A'])
    total = bid_qty + ask_qty
    if total == 0:
        return 0.0
    return (bid_qty - ask_qty) / total  # +1 = strong buy, -1 = strong sell
```

### 4. Depth (Order Book) Stream

**Name**: `<symbol>@depth<levels>@<speed>`

- Levels: 5, 10, or 20
- Speed: `@100ms` or `@500ms`

```json
{
  "e": "depthUpdate",
  "T": 1702517060000,
  "s": "BTCUSDT",
  "b": [["90000.0", "1.5"], ["89999.0", "2.3"]],   // [price, qty] bids
  "a": [["90001.0", "0.8"], ["90002.0", "1.1"]]    // [price, qty] asks
}
```

**Order Book Imbalance at Multiple Depths**:

```python
def multi_depth_obi(bids, asks, depths=[1, 5, 10]):
    """Calculate OBI at L1, L5, L10 for richer signal."""
    results = {}
    for d in depths:
        bid_vol = sum(float(b[1]) for b in bids[:d])
        ask_vol = sum(float(a[1]) for a in asks[:d])
        total = bid_vol + ask_vol
        results[f'L{d}'] = (bid_vol - ask_vol) / total if total > 0 else 0
    return results
```

### 5. Kline/Candlestick Stream

**Name**: `<symbol>@kline_<interval>`

Intervals: `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `8h`, `12h`, `1d`, `3d`, `1w`

```json
{
  "e": "kline",
  "k": {
    "t": 1499404860000,   // Kline start time
    "T": 1499404919999,   // Kline close time
    "s": "BTCUSDT",
    "i": "1m",
    "o": "0.01634790",   // Open
    "c": "0.01634190",   // Close
    "h": "0.01634800",   // High
    "l": "0.01634100",   // Low
    "v": "1020.00",      // Base volume
    "q": "1020.00",      // Quote volume
    "x": false           // Is candle closed?
  }
}
```

### 6. Force Order Stream (LIQUIDATIONS)

**Name**: `<symbol>@forceOrder` or `!forceOrder@arr` (all symbols)

```json
{
  "e": "forceOrder",
  "E": 1568014600893,
  "o": {
    "s": "BTCUSDT",
    "S": "SELL",          // Side of the liquidation
    "o": "LIMIT",
    "f": "IOC",
    "q": "0.014",         // Quantity
    "p": "9910",          // Price
    "ap": "9910",         // Average price
    "X": "FILLED",        // Status
    "l": "0.014",         // Last filled qty
    "z": "0.014",         // Cumulative filled qty
    "T": 1568014600000    // Trade time
  }
}
```

**Liquidation Cascade Detection**:

```python
from collections import deque
from datetime import datetime, timedelta

class LiquidationMonitor:
    def __init__(self, window_seconds=60, cascade_threshold=5):
        self.window = deque()
        self.window_seconds = window_seconds
        self.cascade_threshold = cascade_threshold

    def add_liquidation(self, order):
        now = datetime.now()
        self.window.append({'time': now, 'side': order['S'], 'qty': float(order['q'])})

        # Remove old entries
        cutoff = now - timedelta(seconds=self.window_seconds)
        while self.window and self.window[0]['time'] < cutoff:
            self.window.popleft()

        # Detect cascade
        if len(self.window) >= self.cascade_threshold:
            sides = [e['side'] for e in self.window]
            dominant = max(set(sides), key=sides.count)
            total_qty = sum(e['qty'] for e in self.window)
            print(f"⚡ LIQUIDATION CASCADE: {len(self.window)} liquidations in {self.window_seconds}s")
            print(f"   Dominant side: {dominant}, Total qty: {total_qty:.4f}")
            # After cascade: mean reversion likely if against trend
```

---

## User Data Streams (Account Events)

### Setup

```python
import requests, threading, time

class UserDataStream:
    def __init__(self, api_key):
        self.api_key = api_key
        self.listen_key = None

    def start(self):
        """Create listen key and start renewal thread."""
        self.listen_key = self._create_listen_key()
        # Renew every 30 minutes (expires after 60 min)
        threading.Thread(target=self._renewal_loop, daemon=True).start()
        return self.listen_key

    def _create_listen_key(self):
        r = requests.post(
            'https://fapi.binance.com/fapi/v1/listenKey',
            headers={'X-MBX-APIKEY': self.api_key}
        )
        return r.json()['listenKey']

    def _renewal_loop(self):
        while True:
            time.sleep(1800)  # 30 minutes
            requests.put(
                'https://fapi.binance.com/fapi/v1/listenKey',
                headers={'X-MBX-APIKEY': self.api_key},
                params={'listenKey': self.listen_key}
            )
```

### Event Types

#### `ORDER_TRADE_UPDATE` — Order fills, status changes

```json
{
  "e": "ORDER_TRADE_UPDATE",
  "T": 1568879465651,
  "o": {
    "s": "BTCUSDT",            // Symbol
    "c": "TEST",               // Client order ID
    "S": "SELL",               // Side
    "o": "TRAILING_STOP_MARKET", // Order type
    "f": "GTC",                // Time in force
    "q": "0.001",              // Original quantity
    "p": "0",                  // Price
    "sp": "7103.04",           // Stop price
    "X": "NEW",                // Order status: NEW|PARTIALLY_FILLED|FILLED|CANCELED|EXPIRED
    "i": 8886774,              // Order ID
    "l": "0",                  // Last filled qty
    "z": "0",                  // Cumulative filled qty
    "L": "0",                  // Last filled price
    "N": "USDT",               // Commission asset
    "n": "0",                  // Commission amount
    "T": 1568879465651,        // Trade time
    "t": 0,                    // Trade ID
    "b": "0",                  // Bids notional
    "a": "9.91",               // Ask notional
    "m": false,                // Is maker?
    "R": false,                // Is reduce-only?
    "ot": "TRAILING_STOP_MARKET",
    "ps": "LONG",              // Position side (hedge mode)
    "cp": false,               // Close all? (for conditional orders)
    "rp": "0",                 // Realized PnL (on close)
    "pm": "NONE",              // Price match mode
    "V": "NONE"                // Self-trade prevention mode
  }
}
```

#### `ACCOUNT_UPDATE` — Balance and position changes

```json
{
  "e": "ACCOUNT_UPDATE",
  "T": 1564745798939,
  "a": {
    "m": "ORDER",              // Event reason
    "B": [
      {"a": "USDT", "wb": "122624.12345678", "cw": "100.12345678", "bc": "50.12345678"}
    ],
    "P": [
      {
        "s": "BTCUSDT",
        "pa": "0",             // Position amount
        "ep": "0.00000",       // Entry price
        "bep": "0",            // Break-even price
        "cr": "-45.36",        // Accumulated realized PnL
        "up": "8.12",          // Unrealized PnL
        "mt": "cross",         // Margin type
        "iw": "0.00000000",    // Isolated wallet
        "ps": "BOTH"           // Position side
      }
    ]
  }
}
```

#### `MARGIN_CALL` — Margin warning

```json
{
  "e": "MARGIN_CALL",
  "cw": "3.16812045",         // Cross wallet balance
  "p": [
    {
      "s": "ETHUSDT",
      "ps": "LONG",
      "pa": "1.327",
      "mt": "CROSSED",
      "iw": "0",
      "mp": "187.17",         // Mark price
      "up": "-1.166",         // Unrealized PnL
      "mm": "1.614"           // Maintenance margin required
    }
  ]
}
```

**Action**: Immediately reduce positions when MARGIN_CALL received.

#### `TRADE_LITE` — Lightweight fill event (NEW Sept 2024)

Lower latency than `ORDER_TRADE_UPDATE` — only contains fields needed for fill tracking (HFT use).

---

## WebSocket Trading API (REST via WebSocket — NEW 2024)

Trade without REST calls using WebSocket for lower latency.

```python
# Base URL: wss://ws-fapi.binance.com/ws-fapi/v1
# Same authentication and rate limits as REST API

import asyncio
import websockets
import json
import time
import hmac
import hashlib

async def ws_place_order(api_key, api_secret, symbol, side, quantity, price):
    """Place order via WebSocket API for lower latency."""
    uri = "wss://ws-fapi.binance.com/ws-fapi/v1"

    params = {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": str(quantity),
        "price": str(price),
        "timestamp": int(time.time() * 1000),
        "apiKey": api_key
    }

    # Sign
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    params["signature"] = hmac.new(api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()

    request = {
        "id": "order-001",
        "method": "order.place",
        "params": params
    }

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps(request))
        response = json.loads(await ws.recv())
        return response
```
