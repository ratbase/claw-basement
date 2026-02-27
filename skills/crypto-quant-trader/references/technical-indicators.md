# Technical Indicators Reference

## Trend Indicators

### Moving Averages (MA)

**Simple Moving Average (SMA)**
- Formula: Average of closing prices over N periods
- Usage: 50 SMA (short-term), 200 SMA (long-term trend)
- Signal: Price above = bullish, below = bearish

**Exponential Moving Average (EMA)**
- Formula: Gives more weight to recent prices
- Usage: 20 EMA (fast), 50 EMA (medium), 200 EMA (slow)
- Signal: Faster reaction to price changes

**EMA Ribbon**
- Multiple EMAs (e.g., 20, 50, 100, 200)
- All aligned up = strong uptrend
- All aligned down = strong downtrend
- Crossing/interwoven = consolidation

### Ichimoku Cloud

**Components:**
- Tenkan-sen (Conversion Line): 9-period high+low / 2
- Kijun-sen (Base Line): 26-period high+low / 2
- Senkou Span A: (Tenkan + Kijun) / 2, shifted 26 periods
- Senkou Span B: 52-period high+low / 2, shifted 26 periods
- Chikou Span: Close, shifted 26 periods back

**Signals:**
- Price above cloud = bullish trend
- Price below cloud = bearish trend
- Cloud thickness = support/resistance strength
- TK Cross above Kijun = buy signal
- TK Cross below Kijun = sell signal

## Momentum Indicators

### RSI (Relative Strength Index)

**Formula:**
```
RSI = 100 - (100 / (1 + RS))
RS = Average Gain / Average Loss
```
**Settings:** 14 periods (default)

**Interpretation:**
- RSI > 70: Overbought, potential reversal
- RSI < 30: Oversold, potential reversal
- RSI 50: Neutral level
- **Divergence**: Price makes new high/low but RSI doesn't = reversal signal

**Trading with RSI:**
- Buy on oversold (30) + bullish divergence
- Sell on overbought (70) + bearish divergence
- Use trend filter: Only buy oversold in uptrend

### MACD (Moving Average Convergence Divergence)

**Components:**
- MACD Line: 12 EMA - 26 EMA
- Signal Line: 9 EMA of MACD
- Histogram: MACD - Signal

**Signals:**
- MACD crosses above Signal = bullish
- MACD crosses below Signal = bearish
- Histogram increasing = momentum building
- **Divergence**: Price vs MACD direction mismatch = reversal warning

### Stochastic Oscillator

**Components:**
- %K: (Close - Low) / (High - Low) × 100
- %D: 3-period SMA of %K

**Settings:** 14, 3, 3 (default)

**Interpretation:**
- %K > 80: Overbought
- %K < 20: Oversold
- %K crosses above %D = bullish
- %K crosses below %D = bearish

## Volatility Indicators

### Bollinger Bands

**Components:**
- Middle Band: 20-period SMA
- Upper Band: 20 SMA + 2 × StdDev
- Lower Band: 20 SMA - 2 × StdDev

**Interpretation:**
- Band squeeze = low volatility, breakout coming
- Band expansion = high volatility
- Price at upper band = overbought
- Price at lower band = oversold
- Price outside bands = extreme, may mean-revert

**Bollinger Band Squeeze:**
- Narrowest bands in last N bars
- Watch for breakout direction
- Enter on close outside band with volume

### ATR (Average True Range)

**Formula:**
```
True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
ATR = Average True Range over N periods
```
**Settings:** 14 periods (default)

**Usage:**
- Measure volatility
- Set stop loss: Entry ± 1.5 × ATR
- Position sizing: Higher ATR = smaller position
- Identify quiet vs volatile periods

## Volume Indicators

### Volume

**Key Concepts:**
- Volume confirms price moves
- Upward move + high volume = strong bullish
- Upward move + low volume = weak bullish
- Downward move + high volume = strong bearish
- Downward move + low volume = weak bearish

**Volume Patterns:**
- Volume spike at support/resistance = rejection
- Rising volume in trend = trend continuation
- Declining volume in trend = trend weakening

### OBV (On-Balance Volume)

**Formula:**
```
If Close > PrevClose: OBV = OBV + Volume
If Close < PrevClose: OBV = OBV - Volume
If Close = PrevClose: OBV unchanged
```

**Interpretation:**
- Rising OBV + falling price = bullish divergence
- Falling OBV + rising price = bearish divergence
- OBV confirms price trend

## Support & Resistance

### Fibonacci Retracements

**Key Levels:**
- 23.6% - Shallow correction
- 38.2% - Moderate correction
- 50% - Halfway point (psychological)
- 61.8% - Golden ratio, deep correction
- 78.6% - Very deep correction

**Usage:**
- Draw from swing low to swing high (uptrend)
- Expect bounces at these levels
- Combine with other indicators for confluence

### Pivot Points

**Calculation:**
```
Pivot = (High + Low + Close) / 3
R1 = (2 × Pivot) - Low
R2 = Pivot + (High - Low)
R3 = High + 2 × (Pivot - Low)
S1 = (2 × Pivot) - High
S2 = Pivot - (High - Low)
S3 = Low - 2 × (High - Pivot)
```

**Usage:**
- Daily pivots for intraday trading
- Price at R1/R2 = potential resistance
- Price at S1/S2 = potential support

## Combination Strategies

### Trend Following Setup
1. Price > 200 EMA (long-term trend)
2. Price > 50 EMA (medium-term trend)
3. RSI between 30-70 (not extreme)
4. MACD bullish crossover
5. Volume spike on entry

### Mean Reversion Setup
1. Price within Bollinger Bands (not extreme)
2. RSI < 30 or > 70 (overbought/oversold)
3. Divergence on RSI/MACD
4. Price at key support/resistance
5. Volume drying up before reversal

## Indicator Settings by Timeframe

| Timeframe | RSI | MACD | MA | ATR |
|-----------|-----|------|----|-----|
| 5m        | 14  | 12,26,9 | 9,21 | 14 |
| 15m       | 14  | 12,26,9 | 20,50 | 14 |
| 1H        | 14  | 12,26,9 | 20,50,200 | 14 |
| 4H        | 14  | 12,26,9 | 50,200 | 14 |
| Daily     | 14  | 12,26,9 | 50,200 | 14 |

## Common Mistakes

❌ Using too many indicators (analysis paralysis)
❌ Ignoring higher timeframe for lower timeframe trades
❌ Trading against the trend without good reason
❌ Entering on single indicator signal
❌ Not adapting indicator settings for volatility

---

Remember: Indicators are tools, not crystal balls. Use them as part of a complete trading system with proper risk management.
