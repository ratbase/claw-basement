# Heartbeat

Runs every 30 minutes. Send a Telegram message only when:
1. Pre-session analysis is due (1 hour before ASIA/EU/US open), OR
2. An alert condition is met (funding)

Otherwise stay silent.

---

## Pre-Session Market Analysis

**Runs 1 hour before each major trading session:**

| Session | Market | Opens UTC | Pre-Session Alert UTC |
|---------|--------|-----------|----------------------|
| ASIA    | Tokyo  | 00:00     | 23:00 (prior day)    |
| EU      | London | 08:00     | 07:00                |
| US      | NYC    | 13:30     | 12:30                |

### Execution

```bash
# BTC 4H (primary)
python3 ~/.picoclaw/workspace/skills/binance-futures/scripts/bf.py klines BTCUSDT --interval 4h --json

# BTC 1H (intraday)
python3 ~/.picoclaw/workspace/skills/binance-futures/scripts/bf.py klines BTCUSDT --interval 1h --json

# ETH 4H (altcoin proxy)
python3 ~/.picoclaw/workspace/skills/binance-futures/scripts/bf.py klines ETHUSDT --interval 4h --json

# SOL 4H (high-beta alt)
python3 ~/.picoclaw/workspace/skills/binance-futures/scripts/bf.py klines SOLUSDT --interval 4h --json
```

### Analysis Output

Compile and send a pre-session brief:

```
📊 [SESSION] Market Brief — HH:MM UTC+7

BTC:
• 4H Regime: [BULL/BEAR/RANGE]
• Structure: [bull_trend/bear_trend/ranging]
• ADX: XX.X
• Price: $XX,XXX
• 4H Range: $XX,XXX – $XX,XXX
• 1H Regime: [BULL/BEAR/RANGE]

ETH:
• 4H Regime: [BULL/BEAR/RANGE]
• Price: $X,XXX

SOL:
• 4H Regime: [BULL/BEAR/RANGE]
• Price: $XX.XX

Alt Setup Gate:
• LONG: ✅ Valid / ❌ Block (based on BTC 4H)
• SHORT: ✅ Valid / ❌ Block

Key Levels (BTC):
• Support: $XX,XXX
• Resistance: $XX,XXX

Bias: [STRONGLY_BULLISH / BULLISH / NEUTRAL / BEARISH / STRONGLY_BEARISH]
```

### Bias Logic

Calculate from:
- BTC 4H regime (BULL = +2, BEAR = -2, RANGE = 0)
- BTC 1H regime (BULL = +1, BEAR = -1, RANGE = 0)
- ETH vs BTC performance (ETH up vs BTC = +1, ETH down vs BTC = -1)
- SOL vs BTC performance (SOL up vs BTC = +1, SOL down vs BTC = -1)

Sum: -4 to -5 = STRONGLY_BEARISH, -2 to -1 = BEARISH, 0 = NEUTRAL, +1 to +2 = BULLISH, +3 to +5 = STRONGLY_BULLISH

### When to Send

Send at **exactly** the pre-session times (23:00, 07:00, 12:30 UTC). Do not skip — this is the primary value Zai provides.

---

## Journal Prompt

After sending the pre-session brief, ask the user about new trades:

```
📝 Any new trades this session?

Reply: SYMBOL DIR SIZE @ENTRY [LEVERAGE] [notes]

Example: BTC LONG 0.05 @68000 5x breakout
```

When user replies, record with:

```bash
bf.py journal add BTCUSDT LONG 0.05 68000 5x breakout
```

To list current trades:

```bash
bf.py journal list --open
```

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
| `state/last_session.json` | Last sent session type + timestamp |
| `state/last_heartbeat.json` | Timestamp + summary |
