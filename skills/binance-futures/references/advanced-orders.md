# Advanced Order Types — Binance Futures (Reference)

> **Note**: This file is a reference for understanding order types and parameters.
> Order placement is performed manually via Binance UI or your own trading system — not via clawbot.

---

## ⚠️ Critical Change: Algo Service Migration (Dec 2025)

Conditional orders are now exclusively on the **Algo Service**. These order types via `/fapi/v1/order` now return error `-4120`:
- `STOP_MARKET`
- `TAKE_PROFIT_MARKET`
- `STOP`
- `TAKE_PROFIT`
- `TRAILING_STOP_MARKET`

**Algo order endpoints:**

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Cancel specific | `DELETE /fapi/v1/algoOrder` | Requires `algoId` |
| Cancel all open | `DELETE /fapi/v1/algoOpenOrders` | Requires `symbol` |
| Query single | `GET /fapi/v1/algoOrder` | Requires `algoId` |
| Open orders | `GET /fapi/v1/openAlgoOrders` | Optional `symbol` filter |
| History | `GET /fapi/v1/allAlgoOrders` | Paginated |

---

## Trailing Stop Orders

Trailing stops automatically adjust the stop price as the market moves in your favor.

### Trailing Delta

- 1 BIP = 0.01%
- 100 BIPs = 1% trailing distance
- Range: **10 to 2000 BIPs** (0.1% to 20%)

| Direction | Side | Behavior |
|-----------|------|----------|
| Long protection | SELL | Trails DOWN as price falls. Triggers when price drops X% from peak |
| Short protection | BUY | Trails UP as price rises. Triggers when price rises X% from trough |

### Key Parameters

| Parameter | Values | Notes |
|-----------|--------|-------|
| `trailingDelta` | 10–2000 | In BIPs (1 BIP = 0.01%) |
| `workingType` | `MARK_PRICE` / `CONTRACT_PRICE` | Mark price recommended (manipulation-resistant) |
| `reduceOnly` | `true` | Always set for position protection |
| `positionSide` | `LONG` / `SHORT` / `BOTH` | Required in hedge mode |

---

## Stop Loss & Take Profit (Algo Service)

### Order Types

| Type | Behavior | Use Case |
|------|----------|----------|
| `STOP` | Limit order triggered at `stopPrice` | SL with slippage control |
| `STOP_MARKET` | Market order triggered at `stopPrice` | Guaranteed fill, more slippage |
| `TAKE_PROFIT` | Limit order triggered at `stopPrice` | TP with price control |
| `TAKE_PROFIT_MARKET` | Market order triggered at `stopPrice` | Guaranteed TP fill |

### Key Parameters

| Parameter | Description |
|-----------|-------------|
| `stopPrice` | Trigger price (mark price or last price, per `workingType`) |
| `price` | Limit price (for STOP / TAKE_PROFIT types only) |
| `workingType` | `MARK_PRICE` or `CONTRACT_PRICE` |
| `reduceOnly` | `true` — prevents opening new positions |

### Key Behavior Changes (vs Old Conditional Orders)

1. **No margin check** before trigger — order placed regardless of available margin
2. **GTE_GTC** depends only on positions, not open orders
3. **Modification** of untriggered orders not supported — cancel and replace
4. **Events**: Rejections appear in `ALGO_UPDATE` WebSocket event, not `CONDITIONAL_ORDER_TRIGGER_REJECT`

---

## TWAP Orders (Time-Weighted Average Price)

Splits large orders across time to minimize market impact. Institutional-grade execution.

### Constraints

| Parameter | Limit |
|-----------|-------|
| Duration | 300s (5 min) to 86400s (24 h) |
| Notional | 1,000 to 1,000,000 USDT |
| Max open | 30 simultaneous TWAP orders |
| Availability | USDT-M Futures only |

### Parameters

| Parameter | Description |
|-----------|-------------|
| `symbol` | Trading pair |
| `side` | BUY / SELL |
| `quantity` | Total quantity to execute |
| `duration` | Execution window in seconds |
| `limitPrice` | (Optional) Max/min price — won’t fill beyond this |
| `clientAlgoId` | Unique ID, max 32 chars |

**Endpoint**: `POST /sapi/v1/algo/futures/newOrderTwap` (SAPI, not FAPI)

---

## Iceberg Orders (Hidden Quantity)

Hides true order size by showing only a fraction at a time.

| Parameter | Description |
|-----------|-------------|
| `quantity` | Total quantity (e.g. 1.0 BTC) |
| `icebergQty` | Visible portion per slice (e.g. 0.1 BTC = 10 slices) |

- Max iceberg parts: **50** (increases to **100** in March 2026)
- Requires `LIMIT` order type with `GTC` time-in-force
- Only via standard `/fapi/v1/order` (not Algo Service)

**Use when**: Entering large positions without telegraphing size to market makers.

---

## Self-Trade Prevention (STP) — NEW 2024

| Mode | Behavior |
|------|----------|
| `NONE` | Disabled (default) |
| `EXPIRE_TAKER` | Cancel the incoming taker order |
| `EXPIRE_MAKER` | Cancel the resting maker order |
| `EXPIRE_BOTH` | Cancel both orders |

- Parameter: `selfTradePreventionMode`
- When triggered: order status = `EXPIRED_IN_MATCH`

---

## Price Match Orders — NEW 2024

| Mode | Meaning |
|------|---------|
| `OPPONENT` | Best bid (buy) or best ask (sell) |
| `OPPONENT_5` | 5th level bid/ask |
| `OPPONENT_10` | 10th level bid/ask |
| `OPPONENT_20` | 20th level bid/ask |
| `QUEUE` | Same as best bid (buy) or best ask (sell) |
| `QUEUE_5` | 5th level same side |
| `QUEUE_10` | 10th level same side |
| `QUEUE_20` | 20th level same side |

- Parameter: `priceMatch`
- Best combined with `GTX` (Post-Only) time-in-force for maker fills

---

## RPI (Retail Price Improvement) Orders — NEW Nov 2025

RPI orders receive price improvement beyond the best public quote. Hidden from regular order book.

- Time-in-force: `RPI` (special TIF)
- Hidden from: `GET /fapi/v1/depth`, `bookTicker`, `@bookTicker` stream
- Visible in: `GET /fapi/v1/rpiDepth?symbol=BTCUSDT` and `@rpiDepth@500ms` stream
- Only fills against designated RPI liquidity providers

---

## OCO Pattern (One-Cancels-Other)

OCO is not a single endpoint in Futures API — must be managed manually via your own system.

### Flow

1. Place TP order (via Binance UI / your system)
2. Place SL order (via Binance UI / your system)
3. Monitor `ORDER_TRADE_UPDATE` on USER_DATA WebSocket stream
4. On `FILLED` → cancel the paired order

```
ORDER_TRADE_UPDATE
  → orderStatus: "FILLED"
  → TP filled → cancel SL algoId
  → SL filled → cancel TP algoId
```

---

## Order Lifecycle: Algo Orders

```
PLACED → NEW → ONGOING (TWAP) → FILLED / CANCELLED / EXPIRED
                     ↓ (per child order)
           PARTIALLY_FILLED → ... → FILLED
```

---

## Query & Cancel Algo Orders

```bash
source ~/.binance_config
TIMESTAMP=$(python3 -c "import time; print(int(time.time() * 1000))")
SIG=$(echo -n "timestamp=$TIMESTAMP" | openssl dgst -sha256 -hmac "$BINANCE_API_SECRET" | awk '{print $2}')

# List open algo orders
curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v1/openAlgoOrders?timestamp=$TIMESTAMP&signature=$SIG" | jq .

# Query specific algo order
curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v1/algoOrder?algoId=12345&timestamp=$TIMESTAMP&signature=$SIG" | jq .

# Historical algo orders
curl -s -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v1/allAlgoOrders?timestamp=$TIMESTAMP&signature=$SIG" | jq .

# Cancel specific
curl -s -X DELETE -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v1/algoOrder?algoId=12345&timestamp=$TIMESTAMP&signature=$SIG"

# Cancel all for symbol
curl -s -X DELETE -H "X-MBX-APIKEY: $BINANCE_API_KEY" \
  "https://fapi.binance.com/fapi/v1/algoOpenOrders?symbol=BTCUSDT&timestamp=$TIMESTAMP&signature=$SIG"
```

---

## Standard Order Parameters Quick Reference

| Parameter | Type | Notes |
|-----------|------|-------|
| `symbol` | string | e.g. `BTCUSDT` |
| `side` | enum | `BUY` / `SELL` |
| `type` | enum | `MARKET` / `LIMIT` / `STOP` / `TAKE_PROFIT` / etc. |
| `quantity` | decimal string | Base asset quantity |
| `price` | decimal string | Required for LIMIT types |
| `stopPrice` | decimal string | Trigger price for conditional types |
| `timeInForce` | enum | `GTC` / `IOC` / `FOK` / `GTX` (post-only) / `RPI` |
| `positionSide` | enum | `LONG` / `SHORT` / `BOTH` (hedge mode) |
| `reduceOnly` | bool | Prevents position increase |
| `workingType` | enum | `MARK_PRICE` / `CONTRACT_PRICE` |
| `priceMatch` | enum | See Price Match section |
| `selfTradePreventionMode` | enum | See STP section |
| `trailingDelta` | int | BIPs, for trailing stops |
