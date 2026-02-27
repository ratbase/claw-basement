---
name: trading-journal
description: Track, analyze, and improve Binance Futures trading performance with institutional-grade analytics. Includes advanced metrics (Sharpe/Sortino/Calmar/SQN), behavioral analytics (revenge trading detection, tilt detection, time-of-day analysis), risk analytics (VaR/CVaR/drawdown), R-multiple distribution, Monte Carlo simulation, trade grading, and equity curve analysis.
metadata: {"nanobot":{"emoji":"📊","requires":{"bins":["python3"],"libs":["requests","numpy","pandas","quantstats","python-dotenv"]}}}
---

# Trading Journal 📊

Institutional-grade trading performance analytics for Binance Futures. Goes far beyond PnL — behavioral detection, risk metrics, equity curve analysis, and Monte Carlo simulation.

## Installation

```bash
pip install requests numpy pandas quantstats python-dotenv
```

## Prerequisites

```bash
# Configure credentials
echo "BINANCE_API_KEY=your_key" >> ~/.binance_config
echo "BINANCE_API_SECRET=your_secret" >> ~/.binance_config
chmod 600 ~/.binance_config
```

---

## Scripts

### Core Scripts

| Script | Purpose |
|--------|---------|
| `analyze_trades.py` | Main analysis — PnL, positions, win rate |
| `symbol_trades.py` | Per-symbol trade breakdown |
| `scripts/calculate_metrics.py` | Advanced performance metrics |
| `scripts/calculate_position_safety.py` | Position risk assessment |
| `scripts/fetch_trades.sh` | Fetch raw trade data |
| `scripts/advanced_metrics.py` | **NEW** — Institutional analytics (Sharpe, Sortino, etc.) |
| `scripts/behavioral_analytics.py` | **NEW** — Behavioral pattern detection |

### Usage

```bash
# Quick analysis
python3 analyze_trades.py --limit 100
python3 analyze_trades.py --limit 500

# With account balance
python3 analyze_trades.py --with-balance

# Advanced institutional metrics
python3 scripts/advanced_metrics.py --days 30
python3 scripts/advanced_metrics.py --days 90 --monte-carlo

# Behavioral analytics
python3 scripts/behavioral_analytics.py
```

---

## Output: Standard Analysis

```
============================================================
📊 TRADING PERFORMANCE ANALYSIS
============================================================

💰 Account Summary:
   Total Trades Tracked: 100
   Unique Positions: 12
   Period: 2026-01-28 to 2026-02-27

📈 PnL Breakdown:
   Gross Realized PnL:  +480.41 USDT
   Trading Fees:         -18.77 USDT
   Funding Fees:         -12.20 USDT
   Net PnL (total):     +449.44 USDT

🎯 Performance Metrics:
   Win Rate:           62.5% (7.5 / 12)
   Profit Factor:      2.14 (gross wins / gross losses)
   Expectancy:         +0.38R per trade
   Avg Win:            +89.20 USDT / +1.85R
   Avg Loss:           -41.67 USDT / -1.00R
   Max Win:            +210.50 USDT (BTCUSDT)
   Max Loss:            -95.30 USDT (ETHUSDT)

📉 Risk Metrics:
   Max Drawdown:       -8.4% (peak to trough)
   Drawdown Duration:  6 days
   Sharpe Ratio:       1.87
   Sortino Ratio:      2.43
   Calmar Ratio:       1.12
   SQN Score:          2.89 (Good)
   Recovery Factor:    2.1x

⚠️ Behavioral Alerts:
   ✅ No revenge trading detected
   ⚠️ 2 position size spikes after losses
   ✅ No overtrading detected

🏆 Best Trade: BTCUSDT +210.50 USDT
📉 Worst Trade: ETHUSDT -95.30 USDT

💡 Key Insight: Your Wednesday trades win at 80% — focus here.
   ETHUSDT win rate only 33% — review thesis or skip.
============================================================
```

---

## Performance Metrics — Complete Reference

### Core Ratios

#### Sharpe Ratio
**What**: Risk-adjusted return per unit of total volatility
```
Sharpe = (Mean Return - Risk Free Rate) / Std Dev of Returns × √252
```
- < 0: Below risk-free
- 0-1: Acceptable
- 1-2: Good (professional standard)
- > 2: Excellent
- > 3: Suspicious if sustained long-term

**Limitation**: Penalizes upside volatility (large wins hurt Sharpe)

#### Sortino Ratio
**What**: Return per unit of DOWNSIDE volatility only (better than Sharpe for crypto)
```
Sortino = (Mean Return - Target) / Downside Deviation × √252
```
**Why better**: Traders don't worry about winning too much — only about losing.

Example: Strategy with high Sharpe but occasional big wins has LOW Sharpe, HIGH Sortino. Sortino recognizes this is BETTER.

#### Calmar Ratio
**What**: Annual return / Maximum Drawdown (worst-case benchmark)
```
Calmar = CAGR / |Max Drawdown|
```
- < 0.5: Poor
- 0.5-1.5: Acceptable
- 1.5-3.0: Good
- > 3.0: Excellent

#### SQN (System Quality Number) — Van Tharp
**What**: Captures expectancy × consistency × opportunity volume
```
SQN = √N × Mean(R-multiple) / Std Dev(R-multiple)
```
Van Tharp Scale:
- 1.6-1.9: Tradeable but below average
- 2.0-2.4: Average
- 2.5-2.9: Good
- 3.0-5.0: Excellent
- 5.1+: Superb

**Minimum for statistical significance: 30 trades**

#### K-Ratio (Equity Curve Linearity)
**What**: Measures PATH quality — how linear/smooth is the equity curve?
```
K-Ratio = Slope / Standard Error of Slope
(Linear regression on cumulative equity)
```
**Unique value**: Two strategies with identical Sharpe/Sortino/Calmar can have very different K-ratios. Higher K = smoother path = less psychological pressure.

#### Profit Factor
```
Profit Factor = Total Gross Profits / Total Gross Losses
```
- < 1.0: Losing system
- 1.0-1.5: Marginal
- 1.5-2.0: Good
- > 2.0: Strong

#### Expectancy (Edge per Trade)
```
Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)
Or in R-multiples: Sum of all R / Number of trades
```
**Must be positive** for long-term profitability.

#### Recovery Factor
```
Recovery Factor = CAGR / Max Drawdown Duration
```
Higher = faster recovery. Low recovery factor = psychological suffering despite good returns.

#### Ulcer Index
```
Ulcer Index = √(Sum of drawdown²) / N periods
```
**What**: Combines depth AND duration of drawdowns into one "pain" metric. Lower is better.

---

### Drawdown Analysis

```python
# Full drawdown metrics from scripts/advanced_metrics.py
drawdown_analysis = {
    'max_drawdown': -12.3,              # % worst peak-to-trough
    'max_drawdown_duration': 14,         # Days underwater
    'avg_drawdown': -4.2,               # Average depth
    'drawdown_frequency': 3,             # Times per month in drawdown
    'current_drawdown': 0.0,            # Currently at peak = 0
    'recovery_time': 6,                 # Days to recover from worst DD
}
```

---

### R-Multiple Distribution

**R-multiple = Trade PnL / Initial Risk (distance to stop loss)**

```
+2R = Won twice your risk
-1R = Lost your full risk (standard stop)
+0.5R = Weak winner (didn't reach target)

Distribution analysis:
- Mean R > 0: Positive expectancy
- Median R: Most representative typical trade
- Std Dev R: Consistency of returns
- % trades > 1R: How often you exceed risk
- % trades > 2R: Home run frequency
```

### MAE / MFE Analysis

**MAE (Maximum Adverse Excursion)**: Worst price reached AFTER entry
**MFE (Maximum Favorable Excursion)**: Best price reached AFTER entry

```
MAE tells you: Was your stop loss too tight?
If many trades: MAE near SL then recovered → stops too tight, widen SL

MFE tells you: Are you leaving money on the table?
If many trades: MFE >> actual exit → exiting too early, let winners run

MAE/MFE Efficiency = Actual PnL / MFE
Close to 1.0 = You captured most of the available profit
Close to 0.0 = You exited too early consistently
```

---

## Behavioral Analytics

### Revenge Trading Detection

**Definition**: Opening a new trade within 15 minutes of a losing trade.

**Evidence**: Revenge trades have 34% lower win rate than baseline trades.

**Signals**:
1. Re-entry within 15 min of a loss
2. Position size increased ≥20% above recent average after a loss
3. Win rate degradation in 5th+ trade of same session

```bash
# Run behavioral analytics
python3 scripts/behavioral_analytics.py
```

```
⚠️ BEHAVIORAL ANALYSIS
========================
Revenge Trading:
  Detected instances: 3 (8.3% of trades)
  Avg win rate (normal trades): 64%
  Avg win rate (revenge trades): 28% ← significant underperformance

Tilt Detection (Position Size Spikes):
  Instances of >20% size increase after loss: 2
  Impact on returns: -$89.40 from tilt trades

Time of Day Performance:
  🟢 09:00-12:00 ET: 71% win rate (7 trades)
  🟡 12:00-14:00 ET: 44% win rate (9 trades) ← lunch hour
  🟢 14:00-16:00 ET: 67% win rate (6 trades)
  🔴 16:00-20:00 ET: 33% win rate (3 trades) ← avoid

Day of Week:
  🟢 Tuesday:    80% win rate
  🟢 Wednesday:  75% win rate
  🟡 Thursday:   50% win rate
  🟡 Monday:     50% win rate
  🔴 Friday:     25% win rate ← avoid

Streak Analysis:
  Longest Win Streak:  5 trades
  Longest Loss Streak: 3 trades
  Post-win-streak win rate: 58% (slight overconfidence)
  Post-loss-streak win rate: 71% (you adapt well)

Holding Period:
  Scalp (<1h):     55% win rate, avg +0.6R
  Intraday (1-8h): 67% win rate, avg +1.2R ← your sweet spot
  Swing (8-48h):   50% win rate, avg +0.8R
  Position (>48h): 40% win rate, avg +0.3R ← underperforming
```

### Alerts to Act On

| Alert | Threshold | Action |
|-------|-----------|--------|
| Revenge trading | > 2 trades in 15min after loss | Stop trading for 1 hour |
| Size spike | > 25% above recent avg after loss | Review position sizing rules |
| Rolling Sharpe drop | > 30% drop in 30-day rolling Sharpe | Review strategy, paper trade |
| Portfolio heat | > 70% of equity | Close weakest position |
| Consecutive losses | 3+ in a row | Reduce size by 50% |
| Max daily loss | -3% of equity | Stop trading today |

---

## Risk Analytics

### Value at Risk (VaR)

```
Historical VaR 95%: "In worst 5% of cases, I'll lose more than X"
Historical VaR 99%: "In worst 1% of cases, I'll lose more than X"

For crypto futures: Always use 99% confidence (fat tails)
Update weekly from last 30 days of returns
```

### CVaR (Conditional VaR / Expected Shortfall)

```
CVaR 99% = Average loss in the worst 1% of scenarios

More useful than VaR for position sizing:
Position size = max_acceptable_loss / CVaR

Example:
CVaR 99% = -5% of equity
Max acceptable loss per trade = 2%
Position size multiplier = 2% / 5% = 0.4x → use 40% of normal size
```

### Portfolio Heat

```
Portfolio Heat = Total Open Position Notional / Total Equity

Target: < 300% (including leverage)
Warning: > 500%
Danger: > 700%

Check: Do your open positions have correlated P&L?
If BTC long AND ETH long AND SOL long = 3x correlated = 1 effective position
Treat correlated positions as single position for heat calculation
```

---

## Monte Carlo Simulation

**What it answers**: "What's the worst this strategy can do if my trades come in a different order?"

```bash
python3 scripts/advanced_metrics.py --days 90 --monte-carlo
```

```
MONTE CARLO SIMULATION (1000 paths)
=====================================
Current equity curve: +449 USDT (+12.3%)

5th percentile outcome:     +6.1%
Median outcome:             +12.8%
95th percentile outcome:    +21.4%

Max Drawdown Distribution:
  5th percentile:  -4.2%
  Median:         -9.8%
  95th percentile: -18.7%

Bust Probability (-30% drawdown): 3.2%  ✅ (< 5% = acceptable)
Goal Probability (+25% return):   38.4%

Key: If 95th percentile max DD is > your max tolerable DD,
     reduce position size until it fits.
```

---

## Trade Grading System

Grade your trades to separate execution quality from outcome quality.

### Grade Criteria

**Grade A (Excellent)** — All conditions met:
- ✅ Entry ≤ 1% from planned price
- ✅ Stop loss ≤ 5% from planned SL
- ✅ Position size within ±5% of planned
- ✅ Followed setup rules (can describe the setup)
- ✅ Not a revenge trade

**Grade B (Good)** — Most conditions met:
- Entry ≤ 2% from planned
- Stop ≤ 10% from planned
- Position size within ±15% of planned
- Followed setup rules partially

**Grade C (Poor)** — Conditions missed:
- Chased entry (> 2% from plan)
- Moved stop loss to avoid loss
- Position sized emotionally
- FOMO or revenge trade

**Grade D (Rule Break)** — Immediate review:
- No stop loss set
- Averaged down without plan
- Used maximum leverage
- Traded while angry/euphoric

### What to Do with Grades

```
Track win rate by grade:
Grade A trades should have 15-20% HIGHER win rate than Grade C
If they don't: Your plan needs work, not your execution

Grade A at 55% win rate + Grade C at 40%:
→ Execution matters, focus on following plans

Grade A at 45% + Grade C at 50%:
→ Your "plan" is actually hurting you, reassess setup rules
```

---

## Equity Curve Analysis

```bash
python3 scripts/advanced_metrics.py --equity-curve
```

**What to look for**:
1. **Linearity (K-ratio)**: Higher = smoother = better
2. **Drawdown periods**: Where and how long?
3. **Rolling Sharpe**: Trending down = strategy degrading
4. **Regime correlation**: Did performance change with market regime?

```
EQUITY CURVE ANALYSIS
=======================
K-Ratio:             0.84 (Good — fairly linear growth)
Ulcer Index:         3.2% (Moderate pain level)
Smoothness (R²):     0.78 (78% variance explained by trend)

Rolling 30-day Sharpe:
  Jan 27: 2.1
  Feb 3:  1.9
  Feb 10: 2.3
  Feb 17: 1.6 ← dip
  Feb 24: 1.8

Rolling Sharpe dropped 23% in Week 4. Review trades from that period.
```

---

## Performance by Segment

The journal automatically segments performance to find your edge:

```
BY SYMBOL:
  BTCUSDT:  68% win rate,  +$290, Profit Factor 2.8 ✅
  ETHUSDT:  33% win rate,  -$42,  Profit Factor 0.7 ❌
  SOLUSDT:  60% win rate,  +$180, Profit Factor 1.9 ✅
  → Action: Remove ETHUSDT from trading plan or review setup rules

BY SETUP TYPE (if tagged):
  Trend Following: 70% win rate, +$320, Avg +1.9R
  Mean Reversion: 50% win rate, +$89, Avg +0.8R
  Breakout: 44% win rate, -$18, Avg -0.2R ← kill this setup
  → Action: Focus only on trend following

BY DIRECTION:
  Longs: 65% win rate, +$380
  Shorts: 40% win rate, -$60
  → Action: In current bull market, long-only strategy

BY LEVERAGE:
  1-5x:  70% win rate, +$290
  5-10x: 55% win rate, +$210
  10x+:  35% win rate, -$89 ← overleveraged
  → Action: Cap at 5x, reduce stress
```

---

## Integration with Other Skills

```
binance-futures skill: Provides trade data via Binance API
crypto-quant-trader skill: Provides strategy frameworks to evaluate against

Cross-skill workflow:
1. Execute trades following crypto-quant-trader framework
2. Fetch data via binance-futures skill
3. Analyze with trading-journal skill
4. Identify patterns (behavioral, setup quality, timing)
5. Feed insights back to crypto-quant-trader to refine rules
```

---

## Periodic Reviews

### Daily (End of Session)

```
1. Log all trades (entry, exit, size, setup type, grade)
2. Check: Any revenge trades? Any size spikes?
3. Calculate session PnL and R-multiple
4. Note: Did I follow my rules?
5. Check current drawdown vs daily limit
```

### Weekly

```
1. Run: python3 scripts/advanced_metrics.py --days 7
2. Review win rate by day/time
3. Check rolling Sharpe trend
4. Identify weakest setup type
5. Portfolio heat check
6. Funding cost review (are fees eating profits?)
```

### Monthly

```
1. Full analysis: python3 scripts/advanced_metrics.py --days 30 --monte-carlo
2. Sharpe/Sortino/Calmar vs previous month
3. SQN update (need 30+ trades)
4. Trade grade distribution
5. Behavioral analytics review
6. Equity curve K-ratio and Ulcer Index
7. MAE/MFE analysis — are you optimizing exits?
8. Decision: Continue / Modify / Pause strategy
```

---

## Quick Reference Formulas

| Metric | Formula |
|--------|---------|
| Expectancy (R) | Σ R-multiples / N trades |
| Profit Factor | Σ Wins / \|Σ Losses\| |
| Sharpe | (μ - Rf) / σ × √252 |
| Sortino | (μ - Rf) / σ_down × √252 |
| Calmar | CAGR / \|Max DD\| |
| SQN | √N × Mean(R) / Std(R) |
| VaR 99% | 1st percentile of return distribution |
| CVaR 99% | Mean of returns < VaR |
| Ulcer Index | √(Σ DD²/ N) |
| K-Ratio | Slope / SE(Slope) of log equity curve |
| Portfolio Heat | Open Notional / Equity |
| R-Multiple | Trade PnL / Initial Risk |
| MAE Efficiency | \|MAE\| / \|MFE\| → ideally < 0.5 |

---

## Error Handling

| Error | Fix |
|-------|-----|
| `~/.binance_config not found` | Create file with API credentials |
| `No trades found` | Increase `--limit` or check date range |
| `quantstats not installed` | `pip install quantstats` |
| `Insufficient trades for SQN` | Need 30+ trades; report as N/A |
| API permission error | Ensure key has futures read permissions |
