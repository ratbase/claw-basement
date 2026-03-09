# Heartbeat

Runs every 30 minutes. Send a Telegram message only when:
1. Pre-session analysis is due (1 hour before EU/US/ASIA open), OR
2. An alert condition is met

Otherwise stay silent.

---

## Pre-Session Market Analysis

**Runs 1 hour before each major trading session:**

| Session | Opens UTC | Pre-Session Alert UTC |
|---------|-----------|----------------------|
| ASIA    | 00:00     | 23:00 (prior day)    |
| EU      | 08:00     | 07:00                |
| US      | 13:30     | 12:30                |

### Execution

```bash
# BTC 4H regime
python3 ~/.picoclaw/workspace/skills/binance-futures/scripts/bf.py klines BTCUSDT --interval 4h --json

# BTC 1H structure (intraday)
python3 ~/.picoclaw/workspace/skills/binance-futures/scripts/bf.py klines BTCUSDT --interval 1h --json

# ETH 4H (altcoin proxy)
python3 ~/.picoclaw/workspace/skills/binance-futures/scripts/bf.py klines ETHUSDT --interval 4h --json
```

### Analysis Output

Compile and send a pre-session brief:

```
📊 [SESSION] Market Brief — HH:MM UTC+7

BTC 4H:
• Regime: [BULL/BEAR/RANGE]
• Structure: [bull_trend/bear_trend/ranging]
• ADX: XX.X
• Price: $XX,XXX
• Range: $XX,XXX – $XX,XXX

ETH 4H:
• Regime: [BULL/BEAR/RANGE]
• Price: $X,XXX

Alt Setup Gate:
• LONG: ✅ Valid / ❌ Block
• SHORT: ✅ Valid / ❌ Block

Key Levels:
• BTC Support: $XX,XXX
• BTC Resistance: $XX,XXX

Bias: [BULLISH/BEARISH/NEUTRAL]
```

### When to Send

Send at **exactly** the pre-session times (07:00, 12:30, 23:00 UTC). If no alert triggered in the last cycle, still send the pre-session brief as scheduled.

---

## Funding Rate Monitor

```bash
python3 ~/.picoclaw/workspace/skills/binance-futures/scripts/bf.py income \
  --type FUNDING_FEE --days 1
```

**Alert if:**
- Any open position is paying > 0.05%/8h (wrong direction)
- Total funding paid today > 0.3% of account balance

**Silent if:** funding costs within normal range or receiving funding.

---

## State files

Update after every heartbeat:

| File | Contents |
|------|----------|
| `state/last_session.json` | Last sent session type (EU/US/ASIA) + timestamp |
| `state/last_heartbeat.json` | Timestamp + summary |
