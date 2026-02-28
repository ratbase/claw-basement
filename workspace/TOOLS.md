# Tools

## Binance Futures CLI — `bf.py`

**Location:** `~/.picoclaw/workspace/skills/binance-futures/scripts/bf.py`
**Credentials:** `~/.binance_config` (read-only API key, chmod 600)
**Dependencies:** Python 3 stdlib only — no pip installs needed

```bash
python3 bf.py account                              # Full account summary (margin, PnL)
python3 bf.py balance                              # USDT wallet + available balance
python3 bf.py positions                            # Active open positions only
python3 bf.py income                               # Realized PnL + funding (90 days)
python3 bf.py income --days 365                    # Full year
python3 bf.py income --symbol BTCUSDT              # Filter by symbol
python3 bf.py income --type FUNDING_FEE            # Funding costs only
python3 bf.py income --type REALIZED_PNL           # Realized PnL only
python3 bf.py trades --symbol ETHUSDT --days 30    # Trade history
python3 bf.py rr 50000 48000                       # Risk:reward calculator
python3 bf.py rr 50000 48000 --balance 1000 --risk 2 --leverage 10
```

All endpoints use Binance Futures **v3 API**. No order placement — read-only by design.

---

## Performance analytics

**Location:** `~/.picoclaw/workspace/skills/trading-journal/scripts/`
**Dependencies:** `pip install requests numpy pandas quantstats python-dotenv`

```bash
# Full performance report
python3 advanced_metrics.py --days 30

# With Monte Carlo simulation (10,000 iterations)
python3 advanced_metrics.py --days 90 --monte-carlo

# Per-symbol breakdown
python3 symbol_trades.py --symbol BTCUSDT --days 90

# Behavioral bias detection
python3 behavioral_analytics.py --days 30
```

**Key metrics produced:** Sharpe, Sortino, Calmar, SQN (Van Tharp scale), K-Ratio, Profit Factor, Expectancy, VaR, CVaR, Max Drawdown, Ulcer Index.

**Behavioral flags:** revenge trading (15-min loss window), tilt/size spikes, overtrading streaks, time-of-day edge, day-of-week performance.

---

## Skills (context for analysis)

| Skill | Location | Purpose |
|-------|----------|---------|
| `binance-futures` | `skills/binance-futures/SKILL.md` | API reference, endpoint guide, WebSocket specs |
| `crypto-quant-trader` | `skills/crypto-quant-trader/SKILL.md` | Regime detection, ICT/SMC, Kelly sizing, backtesting |
| `trading-journal` | `skills/trading-journal/SKILL.md` | Performance metrics, behavioral analytics interpretation |

---

## Credentials

| File | Contents | Permissions |
|------|----------|-------------|
| `~/.binance_config` | `BINANCE_API_KEY` + `BINANCE_API_SECRET` | `chmod 600` |

Load pattern:
```bash
source ~/.binance_config
# or
export $(grep -v '^#' ~/.binance_config | xargs)
```

Never log or expose credential values. Keys are read-only — no trading or withdrawal permissions.

---

## API reference

| Endpoint | Version | Purpose |
|----------|---------|---------|
| `/fapi/v3/account` | v3 | Account balances, margin |
| `/fapi/v3/balance` | v3 | Wallet balance |
| `/fapi/v3/positionRisk` | v3 | Open positions |
| `/fapi/v1/income` | v1 | PnL, funding, commissions |
| `/fapi/v1/userTrades` | v1 | Trade history |
| `/fapi/v1/algoOrder` | v1 | Conditional orders (reference only — not used) |

Note: v2 endpoints (`/fapi/v2/*`) are deprecated and return errors.
