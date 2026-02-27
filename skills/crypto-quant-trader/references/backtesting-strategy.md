# Backtesting Strategy Reference

## Overview

Backtesting validates trading strategies using historical data. It reveals if a strategy would have been profitable in the past and helps optimize parameters before risking real capital.

## Core Principles

### Garbage In, Garbage Out
- Quality data is essential
- Include accurate OHLCV (Open, High, Low, Close, Volume)
- Account for fees and slippage
- Use realistic execution assumptions

### Survivorship Bias
- Only trade assets that existed during backtest period
- Don't exclude delisted coins
- Market conditions change - past ≠ future

### Overfitting Warning
- Optimizing too many parameters = curve fitting
- Strategy works on historical data but fails live
- Keep parameters simple and robust

## Backtesting Workflow

### 1. Define Strategy

**Clear Entry Rules**
- When to enter (conditions)
- What to buy (asset)
- How much (position size)
- Example: "Buy when 50 EMA crosses above 200 EMA on 4H, RSI > 50"

**Clear Exit Rules**
- Take profit (multiple targets)
- Stop loss (technical or ATR-based)
- Time-based exit (if no movement)
- Example: "TP1 at 1:2 R:R, TP2 at 1:3 R:R, SL at 1.5x ATR"

**Risk Management**
- Maximum drawdown tolerance
- Maximum open positions
- Maximum daily/weekly loss limit

### 2. Gather Data

**Data Sources**
- **Free**: Binance historical data, CoinGecko, TradingView
- **Paid**: CoinMetrics, Kaiko, TickSuite

**Timeframes**
- Tick-by-tick (most accurate, heaviest)
- 1m, 5m, 15m, 1H, 4H, Daily
- Match trading timeframe

**Data Quality Checks**
- Missing candles (fill or exclude)
- Outliers (filter spikes)
- Volume anomalies

### 3. Build Framework

**Language Options**
- **Python**: Backtrader, VectorBT, PyAlgoTrade
- **JavaScript**: Tradestation.js, Tulip.js
- **TradingView**: Pine Script (visual backtest)

**Python Example (Backtrader):**
```python
import backtrader as bt

class EMACrossStrategy(bt.Strategy):
    params = (
        ('fast_period', 50),
        ('slow_period', 200),
        ('risk_per_trade', 0.02)
    )

    def __init__(self):
        self.ema_fast = bt.indicators.EMA(period=self.p.fast_period)
        self.ema_slow = bt.indicators.EMA(period=self.p.slow_period)
        self.rsi = bt.indicators.RSI()

    def next(self):
        if not self.position:
            if self.ema_fast[0] > self.ema_slow[0] and self.rsi[0] > 50:
                size = self.broker.getcash() * self.p.risk_per_trade / self.data.close[0]
                self.buy(size=size)
        else:
            if self.ema_fast[0] < self.ema_slow[0]:
                self.sell(size=self.position.size)
```

**Pine Script Example:**
```pine
//@version=5
strategy("EMA Cross", overlay=true)

fastEMA = ta.ema(close, 50)
slowEMA = ta.ema(close, 200)
rsi = ta.rsi(close, 14)

longCondition = ta.crossover(fastEMA, slowEMA) and rsi > 50
exitCondition = ta.crossunder(fastEMA, slowEMA)

if longCondition
    strategy.entry("Long", strategy.percent_of_equity, 10)

if exitCondition
    strategy.close("Long")
```

### 4. Run Backtest

**Execution Model**
- **Market order**: Next candle open (realistic)
- **Limit order**: At specific price (can miss)
- **Stop order**: When price hits level

**Slippage**
- Bid-ask spread impact
- Market impact (large orders move price)
- Typical: 0.05-0.1% for large caps, more for small caps

**Fees**
- Trading fees: 0.1% per trade (typical)
- Funding fees (for futures)
- Example: 0.1% per trade = 0.2% roundtrip

**Optimization**
- Test parameter ranges (e.g., EMA 45-55, 195-205)
- Walk-forward optimization (train on period A, test on B)
- Avoid excessive optimization

### 5. Analyze Results

**Key Metrics**

**Profitability**
- **Total Return**: Net profit %
- **CAGR**: Compound Annual Growth Rate
- **Profit Factor**: Gross Profit / Gross Loss (>1 = profitable)

**Risk**
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Return / Volatility (Higher is better, >1 is good)
- **Sortino Ratio**: Return / Downside volatility (penalizes less for upside)
- **Calmar Ratio**: CAGR / Max Drawdown (>1 is good)

**Trade Quality**
- **Win Rate**: % of winning trades
- **Average Win/Loss**: Profit per trade
- **R:R Ratio**: Average risk/reward
- **Expectancy**: (Win% × Avg Win) - (Loss% × Avg Loss)

**Consistency**
- **Monthly returns**: Consistency over time
- **Streaks**: Max win/loss streak
- **Trade distribution**: Visual PnL distribution

**Example Analysis:**
```
Total Return: 150% over 2 years
CAGR: 58%
Max Drawdown: -25%
Sharpe Ratio: 1.8
Win Rate: 42%
Avg Win: $450, Avg Loss: $200
R:R Ratio: 2.25
Expectancy: $109 per trade
```

### 6. Forward Test (Paper Trading)

**Before Live Trading:**
1. Run strategy on paper trading account
2. Verify execution matches backtest
3. Monitor for slippage/fees differences
4. Adjust if necessary
5. Minimum: 1-3 months

**Paper Trading Platforms**
- TradingView
- Binance Testnet
- Bybit Testnet
- Custom bots with test APIs

## Optimization Techniques

### Walk-Forward Analysis

Split data into training and testing periods:
- Train on: 2020-2021
- Test on: 2022
- Train on: 2020-2022
- Test on: 2023

Prevents curve fitting to single period

### Monte Carlo Simulation

Randomize trade order to test robustness:
- Randomize trade sequence 1,000 times
- Generate distribution of outcomes
- 95% confidence interval of returns
- Tests if results are luck or skill

### Parameter Stability

Test sensitivity to parameter changes:
- If small change → big performance drop = overfit
- Robust strategies tolerate parameter variance
- Example: EMA 50/200 works, EMA 48/195 fails = fragile

## Common Pitfalls

❌ **Ignoring fees**: 0.1% per trade = 20% cost on 100 trades
❌ **Perfect fills**: Assuming all trades fill at desired price
❌ **Look-ahead bias**: Using future data (e.g., tomorrow's high)
❌ **Data mining**: Testing 1,000 strategies, picking best one
❌ **Short timeframes**: 3 months insufficient; need multiple market cycles
❌ **Changing markets**: Strategy that worked in bull may fail in bear
❌ **Not accounting for slippage**: Large orders move market
❌ **Survivorship bias**: Only backtesting winning coins

## Backtesting Checklist

- [ ] Strategy has clear entry/exit rules
- [ ] Historical data is complete and accurate
- [ ] Fees and slippage included
- [ ] Tested on multiple market conditions (bull/bear/sideways)
- [ ] Max drawdown is acceptable
- [ ] Expectancy is positive
- [ ] Win rate + R:R ratio = profitable
- [ ] Forward tested on paper trading
- [ ] Parameter stability verified
- [ ] Not over-optimized

## Quick Excel/Google Sheets Template

For simple strategy testing:

| Date | Entry | Stop Loss | Take Profit | Exit | PnL | PnL % |
|------|-------|-----------|-------------|------|-----|-------|
| 1/1  | $100  | $95       | $110        | $110 | $10 | 10%   |
| 1/5  | $100  | $95       | $110        | $96  | -$4 | -4%   |

Calculate:
- Total PnL = SUM(PnL)
- Win Rate = COUNTIF(PnL, ">0") / COUNT(PnL)
- Avg Win = AVERAGEIF(PnL, ">0")
- Avg Loss = AVERAGEIF(PnL, "<0")
- Expectancy = (Win% × Avg Win) - (Loss% × Avg Loss)

## Strategy Optimization Tips

1. **Optimize one parameter at a time**
2. **Use broader ranges first**, then narrow
3. **Prefer robustness over peak performance**
4. **Test out-of-sample** (data not used for optimization)
5. **Walk-forward analysis** is better than static optimization

---

Remember: Backtesting is necessary but not sufficient. A good backtest doesn't guarantee future profits, but a bad backtest guarantees future losses.
