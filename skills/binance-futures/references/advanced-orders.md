# Advanced Order Types — Binance Futures

## ⚠️ Critical Change: Algo Service Migration (Dec 2025)

Conditional orders are now exclusively on the **Algo Service**. These order types via `/fapi/v1/order` now return error `-4120`:
- `STOP_MARKET`
- `TAKE_PROFIT_MARKET`  
- `STOP`
- `TAKE_PROFIT`
- `TRAILING_STOP_MARKET`

**New endpoints:**

| Operation | Endpoint |
|-----------|----------|
| Place | `POST /fapi/v1/algoOrder` |
| Cancel | `DELETE /fapi/v1/algoOrder` |
| Cancel All | `DELETE /fapi/v1/algoOpenOrders` |
| Query | `GET /fapi/v1/algoOrder` |
| Open Orders | `GET /fapi/v1/openAlgoOrders` |
| History | `GET /fapi/v1/allAlgoOrders` |

---

## Trailing Stop Orders

Trailing stops automatically adjust the stop price as the market moves in your favor.

### Trailing Delta

- 1 BIP = 0.01%
- 100 BIPs = 1% trailing distance
- Range: 10 to 2000 BIPs (0.1% to 20%)

**Long position protection (sell trailing stop):**
```python
# Stops trail DOWN as price falls
# Triggers when price drops X% from peak
order = place_algo_order(
    symbol='BTCUSDT',
    side='SELL',
    order_type='TRAILING_STOP_MARKET',
    quantity='0.001',
    trailingDelta=150,      # 1.5% trailing
    workingType='MARK_PRICE',
    reduceOnly=True
)
```

**Short position protection (buy trailing stop):**
```python
# Stops trail UP as price rises
# Triggers when price rises X% from trough
order = place_algo_order(
    symbol='BTCUSDT',
    side='BUY',
    order_type='TRAILING_STOP_MARKET',
    quantity='0.001',
    trailingDelta=150,      # 1.5% trailing
    workingType='MARK_PRICE',
    reduceOnly=True
)
```

### workingType Options

| Value | Meaning |
|-------|---------|
| `MARK_PRICE` | Uses mark price (recommended — prevents manipulation) |
| `CONTRACT_PRICE` | Uses last traded price |

---

## Stop Loss & Take Profit (Algo Service)

```python
import requests, hmac, hashlib, time, urllib.parse
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path.home() / '.binance_config')
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

def place_algo_order(symbol, side, order_type, quantity, **kwargs):
    params = {
        'symbol': symbol,
        'side': side,
        'type': order_type,
        'quantity': str(quantity),
        'timestamp': int(time.time() * 1000),
        **{k: str(v) for k, v in kwargs.items()}
    }
    query = urllib.parse.urlencode(sorted(params.items()))
    params['signature'] = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

    r = requests.post(
        'https://fapi.binance.com/fapi/v1/algoOrder',
        headers={'X-MBX-APIKEY': API_KEY},
        params=params
    )
    r.raise_for_status()
    return r.json()

# --- Stop Loss ---
stop_loss = place_algo_order(
    symbol='BTCUSDT',
    side='SELL',               # Sell to close long
    order_type='STOP',
    quantity='0.001',
    stopPrice='85000',         # Trigger price
    price='84900',             # Limit price (below stop for buffer)
    workingType='MARK_PRICE',
    reduceOnly=True
)

# --- Take Profit ---
take_profit = place_algo_order(
    symbol='BTCUSDT',
    side='SELL',
    order_type='TAKE_PROFIT',
    quantity='0.001',
    stopPrice='100000',        # Trigger price
    price='99900',             # Limit price
    workingType='MARK_PRICE',
    reduceOnly=True
)

# --- Stop Market (market order on trigger) ---
stop_market = place_algo_order(
    symbol='BTCUSDT',
    side='SELL',
    order_type='STOP_MARKET',
    quantity='0.001',
    stopPrice='85000',
    workingType='MARK_PRICE',
    reduceOnly=True
)
```

### Key Behavior Changes (vs Old Conditional Orders)

1. **No margin check** before trigger — order placed regardless of available margin
2. **GTE_GTC** depends only on positions, not open orders
3. **Modification** of untriggered orders not supported (cancel and replace)
4. **Events**: Rejections appear in `ALGO_UPDATE` WebSocket event, not `CONDITIONAL_ORDER_TRIGGER_REJECT`

---

## TWAP Orders (Time-Weighted Average Price)

Split large orders across time to minimize market impact. Institutional-grade execution.

```python
def place_twap_order(symbol, side, quantity, duration_seconds, limit_price=None):
    """
    Place TWAP order splitting execution over duration.
    
    Constraints:
    - duration: 300s (5min) to 86400s (24h)
    - notional: 1,000 to 1,000,000 USDT
    - max 30 open TWAP orders simultaneously
    - USDT-M futures only
    """
    params = {
        'symbol': symbol,
        'side': side,
        'quantity': str(quantity),
        'duration': str(duration_seconds),
        'clientAlgoId': f"twap-{int(time.time())}",  # unique, max 32 chars
        'timestamp': int(time.time() * 1000)
    }
    if limit_price:
        params['limitPrice'] = str(limit_price)

    query = urllib.parse.urlencode(sorted(params.items()))
    params['signature'] = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

    r = requests.post(
        'https://api.binance.com/sapi/v1/algo/futures/newOrderTwap',
        headers={'X-MBX-APIKEY': API_KEY},
        params=params
    )
    return r.json()

# Example: Buy 0.1 BTC over 1 hour
twap = place_twap_order(
    symbol='BTCUSDT',
    side='BUY',
    quantity='0.1',
    duration_seconds=3600,  # 1 hour
    limit_price='96000'     # Don't pay more than this (optional)
)
```

---

## Iceberg Orders (Hidden Quantity)

Hides the true order size by displaying only a fraction at a time.

```python
# Buy 1 BTC but show only 0.1 BTC at a time
order = client.new_order(
    symbol='BTCUSDT',
    side='BUY',
    type='LIMIT',
    timeInForce='GTC',
    quantity='1.0',          # Total quantity
    price='90000',
    icebergQty='0.1'         # Visible portion per slice
)
# Splits into 10 visible slices of 0.1 BTC each
# Max iceberg parts: 50 (increases to 100 in March 2026)
```

**When to use**: Large position entries where you don't want to telegraph your size to market makers.

---

## Self-Trade Prevention (NEW 2024)

Prevents your own orders from trading against each other.

```python
order = client.new_order(
    symbol='BTCUSDT',
    side='BUY',
    type='LIMIT',
    timeInForce='GTC',
    quantity='0.001',
    price='90000',
    selfTradePreventionMode='EXPIRE_TAKER'
    # Options:
    # NONE         - disabled (default)
    # EXPIRE_TAKER - cancel the taker order
    # EXPIRE_MAKER - cancel the maker order
    # EXPIRE_BOTH  - cancel both orders
)

# If STP triggers, order status = 'EXPIRED_IN_MATCH'
```

---

## Price Match Orders (NEW 2024)

Automatically price orders at or near the best bid/ask without specifying exact price.

```python
# Price match options
price_match_modes = {
    'OPPONENT':    'Best bid (for buy) or best ask (for sell)',
    'OPPONENT_5':  '5th level bid/ask',
    'OPPONENT_10': '10th level bid/ask',
    'OPPONENT_20': '20th level bid/ask',
    'QUEUE':       'Same as best bid (for buy) or best ask (for sell)',
    'QUEUE_5':     '5th level same side',
    'QUEUE_10':    '10th level same side',
    'QUEUE_20':    '20th level same side',
}

# Post as maker at best bid
order = client.new_order(
    symbol='BTCUSDT',
    side='BUY',
    type='LIMIT',
    timeInForce='GTX',       # Post-Only
    quantity='0.001',
    priceMatch='QUEUE'       # Match best bid automatically
)
```

---

## RPI (Retail Price Improvement) Orders (NEW Nov 2025)

RPI orders receive price improvement beyond the best public quote. Hidden from regular order book.

```python
# Place RPI order
order = client.new_order(
    symbol='BTCUSDT',
    side='BUY',
    type='LIMIT',
    timeInForce='RPI',       # RPI time-in-force
    quantity='0.001',
    price='90000'
)

# View RPI-inclusive order book
# GET /fapi/v1/rpiDepth?symbol=BTCUSDT
# Stream: <symbol>@rpiDepth@500ms

# Note: RPI orders excluded from:
# - GET /fapi/v1/depth
# - GET /fapi/v1/ticker/bookTicker
# - <symbol>@bookTicker stream
```

---

## OCO Orders (One-Cancels-Other)

Set simultaneous take profit and stop loss. First one to trigger cancels the other.

```python
# Not directly supported as single endpoint in Futures API
# Implement manually:

def place_oco(symbol, side, quantity, take_profit_price, stop_loss_price, entry_price=None):
    """
    Place take profit + stop loss pair.
    Cancel one when the other fills via USER_DATA stream.
    """
    # Take profit
    tp = place_algo_order(
        symbol=symbol,
        side=side,
        order_type='TAKE_PROFIT',
        quantity=quantity,
        stopPrice=take_profit_price,
        price=str(float(take_profit_price) * (0.999 if side == 'SELL' else 1.001)),
        reduceOnly=True
    )

    # Stop loss
    sl = place_algo_order(
        symbol=symbol,
        side=side,
        order_type='STOP',
        quantity=quantity,
        stopPrice=stop_loss_price,
        price=str(float(stop_loss_price) * (0.999 if side == 'BUY' else 1.001)),
        reduceOnly=True
    )

    return {'take_profit_order': tp, 'stop_loss_order': sl}

# Monitor USER_DATA stream for fills
# When TP fills -> cancel SL order
# When SL fills -> cancel TP order
```

---

## Order Lifecycle: Algo Orders

```
PLACED → NEW → ONGOING (for TWAP) → FILLED / CANCELLED / EXPIRED
                        ↓ (per child order)
              PARTIALLY_FILLED → ... → FILLED
```

### Query & Cancel

```bash
source ~/.binance_config
TIMESTAMP=$(python3 -c "import time; print(int(time.time() * 1000))")
SIG=$(echo -n "timestamp=$TIMESTAMP" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | awk '{print $2}')

# Cancel specific algo order (need algoId)
curl -s -X DELETE -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v1/algoOrder?algoId=12345&timestamp=$TIMESTAMP&signature=$SIG"

# Cancel ALL open algo orders for a symbol
curl -s -X DELETE -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v1/algoOpenOrders?symbol=BTCUSDT&timestamp=$TIMESTAMP&signature=$SIG"
```
