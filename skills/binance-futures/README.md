# binance-futures 💹

Teaches Claude to interact with the Binance Futures API — account monitoring, position tracking, income history, WebSocket streams, funding rates, liquidation monitoring, and advanced order types.

**Read-only by design.** Order placement is done manually via Binance UI or your own system — not via Claude.

---

## Setup

### 1. Credentials

```bash
cat > ~/.binance_config << 'EOF'
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
EOF
chmod 600 ~/.binance_config
```

**API key permissions needed**: Futures Read only. No trading, no withdrawals.

### 2. Install the CLI

```bash
chmod +x scripts/bf.py
```

No pip installs — pure Python stdlib.

---

## `bf.py` — Unified CLI

All data fetching in one tool. Replaces 15 individual shell scripts.

```bash
# Account summary (v3)
./scripts/bf.py account

# Quick wallet balance
./scripts/bf.py balance

# Open positions (v3 — active only, not all 300 symbols)
./scripts/bf.py positions

# Income + realized PnL — last 90 days, auto-paginated
./scripts/bf.py income

# Income — full year by symbol
./scripts/bf.py income --days 365

# Filter by symbol or income type
./scripts/bf.py income --symbol BTCUSDT --type REALIZED_PNL

# Trade history
./scripts/bf.py trades
./scripts/bf.py trades --symbol ETHUSDT --days 90

# Raw JSON (pipe to jq)
./scripts/bf.py positions --raw | jq '.[0]'

# Risk:Reward calculator — no API key needed
./scripts/bf.py rr 50000 48000
./scripts/bf.py rr 50000 48000 --balance 1000 --risk 2 --leverage 10
./scripts/bf.py rr 0.50 0.46 --target 2.5
```

| Command | Endpoint | Returns |
|---------|----------|---------|
| `account` | `GET /fapi/v3/account` | Balances, margin, unrealized PnL |
| `balance` | `GET /fapi/v3/balance` | Wallet + available USDT |
| `positions` | `GET /fapi/v3/positionRisk` | Active positions only |
| `income` | `GET /fapi/v1/income` | Realized PnL, funding, commissions (paginated) |
| `trades` | `GET /fapi/v1/userTrades` | Historical fills |
| `rr` | — | Position sizing, TP/SL levels |

---

## What Claude Can Help With

When this skill is active, Claude understands:

- **v3 API**: All endpoints (account, balance, positionRisk) — v2 is deprecated and returns errors
- **Algo orders**: Conditional orders (STOP, TP, trailing stop) migrated to `/fapi/v1/algoOrder` in Dec 2025 — old endpoints return `-4120`
- **Funding rates**: Reading, annualizing, scanning all symbols for arb opportunities
- **WebSocket streams**: Mark price, aggTrade, bookTicker, forceOrder (liquidations), user data stream
- **Liquidation monitoring**: Force order stream, ADL risk score, insurance fund
- **Rate limits**: Weight tracking, 429/418 error handling, backoff strategy
- **RSA signing**: More secure alternative to HMAC for API authentication
- **Portfolio risk**: Portfolio heat formula, margin ratio, ADL quantile

---

## Files

```
binance-futures/
├── SKILL.md                        AI skill instructions (840 lines)
├── scripts/
│   └── bf.py                       Unified data CLI (pure stdlib)
└── references/
    ├── advanced-orders.md          Order types reference (no placement code)
    ├── websocket-streams.md        Stream specs, JSON schemas, keep-alive
    ├── .binance_config             Placeholder (do not commit real keys)
    └── .binance_config.example     Template for credential file
```

---

## Key Notes

- **v2 deprecated**: `/fapi/v2/account`, `/fapi/v2/balance`, `/fapi/v2/positionRisk` all deprecated. Always use v3.
- **Algo service**: `STOP_MARKET`, `TAKE_PROFIT_MARKET`, `TRAILING_STOP_MARKET` via `/fapi/v1/algoOrder` only since Dec 2025.
- **Income pagination**: `bf.py income` auto-paginates — fetches all records even beyond the 1000-record API limit.
- **Credentials priority**: env vars → `~/.binance_config` → `~/.config/binance/credentials`

---

## Error Codes

| Code | Meaning | Fix |
|------|---------|-----|
| `-1021` | Timestamp mismatch | Sync system clock |
| `-2015` | Invalid API key or IP | Check permissions + IP whitelist |
| `-4120` | Wrong order endpoint | Use `/fapi/v1/algoOrder` for conditional orders |
| `429` | Rate limit hit | Back off, respect `Retry-After` header |
| `418` | IP banned | Wait, do not retry |
