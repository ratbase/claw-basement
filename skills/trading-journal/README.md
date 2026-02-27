# trading-journal 📓

Institutional-grade performance analytics for Binance Futures trades — Sharpe, Sortino, Calmar, SQN, K-Ratio, behavioral bias detection, Monte Carlo simulation, and equity curve analysis.

**Read-only.** Pulls your trade history for analysis. No orders placed.

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

**API key permissions needed**: Futures Read only.

### 2. Dependencies

```bash
pip install requests numpy pandas quantstats python-dotenv
```

---

## Scripts

### `scripts/advanced_metrics.py` — Full Performance Report

```bash
# Last 30 days
python3 scripts/advanced_metrics.py --days 30

# With Monte Carlo simulation (10,000 iterations)
python3 scripts/advanced_metrics.py --days 90 --monte-carlo

# With equity curve chart
python3 scripts/advanced_metrics.py --days 30 --equity-curve

# Filter by symbol
python3 scripts/advanced_metrics.py --symbol BTCUSDT --days 90

# Full institutional report
python3 scripts/advanced_metrics.py --days 365 --monte-carlo --equity-curve
```

**Outputs**: Sharpe, Sortino, Calmar, SQN (Van Tharp scale), K-Ratio, Profit Factor, Expectancy, Win Rate, VaR, CVaR, Ulcer Index, Max Drawdown, Recovery Factor.

---

### `scripts/behavioral_analytics.py` — Bias Detection

```bash
# Full behavioral analysis
python3 scripts/behavioral_analytics.py --days 90

# Check for revenge trading patterns
python3 scripts/behavioral_analytics.py --days 30 --check revenge

# Time-of-day performance heatmap
python3 scripts/behavioral_analytics.py --days 90 --heatmap
```

**Detects**: Revenge trading (15-min loss window), tilt/size spikes, overtrading streaks, day-of-week edge, session performance (Asia/London/NY), loss aversion asymmetry.

---

### `analyze_trades.py` — Trade-Level Summary

```bash
python3 analyze_trades.py
python3 analyze_trades.py --days 30
```

---

### `symbol_trades.py` — Per-Symbol Breakdown

```bash
python3 symbol_trades.py --symbol BTCUSDT
python3 symbol_trades.py --symbol ETHUSDT --days 90
```

---

## Metrics Reference

| Metric | Good | Exceptional |
|--------|------|-------------|
| Sharpe Ratio | > 1.0 | > 2.0 |
| Sortino Ratio | > 1.5 | > 3.0 |
| Calmar Ratio | > 1.0 | > 3.0 |
| SQN (Van Tharp) | > 2.0 | > 5.0 ("Holy Grail") |
| K-Ratio | > 1.0 | > 2.0 |
| Profit Factor | > 1.5 | > 2.0 |
| Max Drawdown | < 20% | < 10% |
| Win Rate | > 45% | > 60% |

---

## What Claude Can Help With

When this skill is active, Claude can:

- **Interpret your metrics**: Explain what your Sharpe/SQN numbers mean in practice
- **Identify weaknesses**: Which symbols, sessions, or setups drag performance
- **Behavioral audit**: Flag revenge trading, overtrading, and tilt patterns from your data
- **Drawdown analysis**: Classify drawdown (normal variance vs strategy failure), estimate recovery time
- **Expectancy modeling**: Is your edge sufficient to compound? What position size is sustainable?
- **Monte Carlo**: Probability of ruin, confidence intervals for future returns
- **Strategy comparison**: A/B test two timeframes or setups by PnL and risk-adjusted metrics
- **Trade grading**: Score individual trades on execution quality vs planned setup

---

## Files

```
trading-journal/
├── SKILL.md                            AI skill instructions (586 lines)
├── analyze_trades.py                   Trade-level summary
├── symbol_trades.py                    Per-symbol breakdown
├── trading-journal.sh                  Shell wrapper
└── scripts/
    ├── advanced_metrics.py             Full performance report (616 lines)
    ├── behavioral_analytics.py         Bias detection (561 lines)
    ├── calculate_metrics.py            Core metric calculations
    ├── calculate_position_safety.py    Margin/liquidation safety checks
    └── fetch_trades.sh                 Raw trade fetcher
```

---

## Key Notes

- **Works best with `binance-futures`**: Use `bf.py income` or `bf.py trades` to pull data, then this skill to analyze it.
- **SQN scale**: < 1.6 poor, 1.6–1.9 below avg, 2.0–2.4 average, 2.5–2.9 good, 3.0–5.0 excellent, > 5.0 "Holy Grail"
- **Revenge trading window**: Behavioral script flags any trade entered within 15 minutes of a losing close.
- **Sample size**: Most metrics need 30+ trades to be statistically meaningful; 100+ for reliable Sharpe.
- **Pair with `crypto-quant-trader`**: Use this skill to audit your journal, then that skill to rebuild the strategy.
