# crypto-quant-trader 📊

Turns Claude into a senior quant researcher and algo developer — regime detection, multi-timeframe confluence, order flow analysis, ICT/SMC concepts, volatility-adjusted sizing, and institutional-grade backtesting.

**Analysis only.** No order placement. Claude reads markets and builds strategies — execution is yours.

---

## Setup

No credentials required. This is a pure analysis skill — no API calls, no keys.

Optional: pair with the `binance-futures` skill to pull live market data for analysis.

---

## What Claude Can Help With

When this skill is active, Claude operates as a quant researcher:

### Market Regime Detection
- **5 regimes**: Trending Bull, Trending Bear, Ranging, Volatile Breakout, Accumulation/Distribution
- Regime classification via ADX + Bollinger + volume profile
- Regime-appropriate strategy selection (trend-following vs mean-reversion)

### Multi-Timeframe Analysis
- HTF bias → MTF structure → LTF entry confluence
- Timeframe pyramid: 1D/4H bias, 1H/15m structure, 5m/1m entries
- Confluence scoring system (0–100) before any trade

### Order Flow & Microstructure
- **OBI** (Order Book Imbalance): bid/ask pressure ratio, spoofing detection
- **TFI** (Trade Flow Imbalance): buy vs sell aggression, delta analysis
- VWAP deviation, volume profile (POC, VAH, VAL, HVN/LVN)
- CVD (Cumulative Volume Delta) divergence signals

### ICT / Smart Money Concepts
- Order Blocks (OB): mitigation, breaker blocks, rejection candles
- Fair Value Gaps (FVG): imbalance identification, fill probability
- Break of Structure (BoS) and Change of Character (ChoCH)
- Liquidity pools: BSL/SSL, equal highs/lows, stop hunts
- Optimal Trade Entry (OTE): 62–79% Fibonacci retracement
- Market Maker Models: accumulation → manipulation → distribution

### Position Sizing & Risk
- **Kelly Criterion** (full + fractional): optimal f, ruin probability
- **CVaR** (Conditional Value at Risk): expected loss in tail scenarios
- Volatility-adjusted sizing: ATR-based, vol-targeting (10–20% annual)
- Correlation-adjusted portfolio heat (max 6 units)
- Pyramiding rules: 3 entries max, 50%/30%/20% scaling

### Backtesting & Strategy Development
- Walk-forward optimization (in-sample/out-of-sample split)
- Monte Carlo simulation: 10,000 iterations, confidence intervals
- Parameter sensitivity heatmaps (avoid "knife-edge" parameters)
- Overfitting detection: Sharpe ratio, Calmar, K-Ratio, SQN
- Live vs backtest performance degradation tracking

### Funding Rate Arbitrage
- Cross-exchange funding rate scanning
- Delta-neutral hedge construction
- Carry trade annualized yield calculation

---

## Reference Documents

| File | Contents |
|------|----------|
| `references/technical-indicators.md` | RSI, MACD, Bollinger, ATR, Ichimoku, custom signals |
| `references/on-chain-metrics.md` | Exchange flows, SOPR, MVRV, miner capitulation |
| `references/backtesting-strategy.md` | Walk-forward, Monte Carlo, overfitting tests |
| `references/trading-psychology.md` | Behavioral biases, discipline frameworks |
| `references/market-microstructure.md` | Order book dynamics, OBI/TFI, execution alpha |
| `references/smart-money-concepts.md` | ICT concepts, Order Blocks, FVG, liquidity |

---

## Example Prompts

```
"Analyze BTCUSDT on the 4H — what's the current regime and bias?"
"Should I long here? Walk me through confluence scoring."
"Build a mean-reversion strategy for ranging markets."
"What's my optimal position size for a 2% risk with 3R target?"
"Backtest this setup: OB + FVG confluence entry on 15m."
"Scan for high-funding-rate pairs worth delta-neutral arb."
"Review my last 20 trades for behavioral biases."
```

---

## Files

```
crypto-quant-trader/
├── SKILL.md                        AI skill instructions (755 lines)
└── references/
    ├── technical-indicators.md     Indicator formulas, signal logic
    ├── on-chain-metrics.md         Blockchain data interpretation
    ├── backtesting-strategy.md     Backtest methodology, validation
    ├── trading-psychology.md       Bias recognition, discipline
    ├── market-microstructure.md    Order flow, book dynamics (547 lines)
    └── smart-money-concepts.md     ICT/SMC concepts (411 lines)
```

---

## Key Notes

- **Pair with `binance-futures`**: Use `bf.py` to pull real positions/income data, then ask this skill to analyze it.
- **Confluence first**: Claude will always score confluence before recommending any entry — never trades on single signals.
- **Regime-aware**: Strategy suggestions adapt to detected market regime — what works in trending markets fails in ranging ones.
- **No black boxes**: All sizing formulas, scoring weights, and backtest logic are explained step by step.
