# Heartbeat

Runs every 30 minutes. Execute all three checks. Send a Telegram message only if at least one alert condition is met. If nothing is actionable, stay silent.

---

## Check 1 — Open positions (isolated margin)

```bash
python3 ~/.picoclaw/workspace/skills/binance-futures/scripts/bf.py positions
```

Compare against last state saved in `~/.picoclaw/workspace/state/positions.json`.

**Alert if:**
- Any new position opened or closed since last heartbeat
- Unrealized PnL on any position moved > ±3% since last check
- Any position has leverage > 10x
- Liquidation distance on any position < 15% (liq price within 15% of current price)

**Silent if:** positions unchanged, PnL within ±2%, all liq distances > 20%.

---

## Check 2 — Funding rate costs

```bash
python3 ~/.picoclaw/workspace/skills/binance-futures/scripts/bf.py income \
  --type FUNDING_FEE --days 1
```

**Alert if:**
- Any open position is paying > 0.05%/8h in funding (wrong direction)
- Total funding paid today > 0.3% of account balance

**Silent if:** funding costs are within normal range or positions are receiving funding.

---

## Check 3 — BTC market regime

Assess BTC/USDT 4H structure using the `crypto-quant-trader` skill.

Evaluate:
- **ADX**: > 25 = trending, 20–25 = transitional, < 20 = ranging
- **Structure**: higher highs/lows (bull trend), lower highs/lows (bear trend), compression (range)
- Compare to regime cached in `~/.picoclaw/workspace/state/regime.json`

**Alert if:**
- Regime changed since last heartbeat (trending ↔ ranging)
- Regime is ranging AND a directional trend position is open (mismatch warning)

**Silent if:** regime unchanged and no mismatch.

---

## Heartbeat message format

Only send if at least one alert triggered:

```
🔁 [HH:MM UTC+7]
[triggered check results — no boilerplate]
```

Example (two alerts):
```
🔁 14:30 UTC+7
• ETHUSDT SHORT: funding –0.041%/8h → ~$15/day cost
• BTC regime: trending → ranging (ADX 28→19)
  ↳ Check if ETHUSDT SHORT still valid in ranging market
```

If no alerts: **no message sent**.

---

## State files

Update these after every heartbeat:

| File | Contents |
|------|----------|
| `state/positions.json` | Last known positions snapshot |
| `state/regime.json` | Last known BTC regime + ADX value |
| `state/last_heartbeat.json` | Timestamp + summary of last run |
