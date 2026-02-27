# Smart Money Concepts (ICT) for Crypto Futures

## Overview

Smart Money Concepts (SMC), pioneered by Michael Huddleston (ICT — Inner Circle Trader), models how institutional market makers engineer liquidity, accumulate positions, and distribute them. These concepts explain the "why" behind price movements that appear random.

**Core insight**: Market makers need liquidity to fill large orders. They engineer price to sweep liquidity pools (equal highs/lows, stop clusters) before reversing.

**Python library**: `pip install smartmoneyconcepts`

---

## Key Concepts

### 1. Structure (Trend Direction)

**Break of Structure (BoS)**: Price breaks a significant swing high (uptrend) or swing low (downtrend). Confirms trend continuation.

**Change of Character (ChoCH)**: A BoS in the OPPOSITE direction. Signals potential trend reversal. (More significant than regular BoS)

```python
from smartmoneyconcepts import smc
import pandas as pd

# Detect swing highs/lows
swings = smc.swing_highs_lows(df, swing_length=5)
# Returns: df with 'HighLow' column (1=swing high, -1=swing low)

# Detect BoS and ChoCH
bos_choch = smc.bos_choch(df, close_break=True)
# Returns: df with columns for BoS/ChoCH direction and level

print(bos_choch[bos_choch['BOS'] != 0])  # Print BoS events
print(bos_choch[bos_choch['CHOCH'] != 0])  # Print ChoCH events
```

**Trading Rules**:
```
BoS = Trend continuation signal → trade with trend
ChoCH = Potential reversal → reduce position or prepare for counter-trend

In uptrend:
- Wait for ChoCH (lower low breaks)
- This signals potential accumulation complete / distribution starting
- Look for short setup on first pullback after ChoCH
```

### 2. Order Blocks (OB)

**Definition**: The LAST opposing candle before a significant directional move. This represents where institutions placed their orders.

```
Bullish Order Block:
- Last RED candle before a strong move UP
- Price returns to this candle → strong long opportunity
- Stop: Below the OB's low

Bearish Order Block:
- Last GREEN candle before a strong move DOWN
- Price returns to this candle → strong short opportunity
- Stop: Above the OB's high
```

```python
# Detect order blocks
ob = smc.ob(df, swing_length=5, close_mitigation=False)
# Returns: df with OB zones (level, top, bottom, type)

# Filter for unmitigated OBs (price hasn't returned yet)
bullish_obs = ob[(ob['OB'] == 1) & ob['MitigatedIndex'].isna()]
bearish_obs = ob[(ob['OB'] == -1) & ob['MitigatedIndex'].isna()]

# Check if current price is in an OB
current_price = df['close'].iloc[-1]
for _, ob_zone in bullish_obs.iterrows():
    if ob_zone['Bottom'] <= current_price <= ob_zone['Top']:
        print(f"🟢 PRICE IN BULLISH ORDER BLOCK: {ob_zone['Bottom']:.2f} - {ob_zone['Top']:.2f}")
```

**Quality OB checklist**:
- ✅ HTF aligned (1D/4H OB for 1H/15m entries)
- ✅ Strong move away from OB (big candles after)
- ✅ Not yet "mitigated" (price hasn't returned)
- ✅ OB at key S/R level
- ✅ FVG between OB and current price (extra strength)

### 3. Fair Value Gaps (FVG / Imbalance)

**Definition**: A 3-candle pattern where the wicks of candles 1 and 3 DON'T overlap — creating a "gap" of unfilled orders. Price tends to return to fill these gaps.

```
Bullish FVG:
Candle 1 High < Candle 3 Low
The gap between them = unfilled buy orders
Price returns to fill → potential long entry

Bearish FVG:
Candle 1 Low > Candle 3 High  
The gap between them = unfilled sell orders
Price returns to fill → potential short entry
```

```python
# Detect Fair Value Gaps
fvg = smc.fvg(df, join_consecutive=False)
# Returns: df with FVG zones (FVG=1 bullish, -1 bearish, MitigatedIndex, etc.)

# Active (unmitigated) FVGs
active_bull_fvgs = fvg[(fvg['FVG'] == 1) & fvg['MitigatedIndex'].isna()]
active_bear_fvgs = fvg[(fvg['FVG'] == -1) & fvg['MitigatedIndex'].isna()]

def check_price_at_fvg(current_price, fvg_df):
    """Check if price is in an active FVG zone."""
    for _, gap in fvg_df.iterrows():
        if gap['Bottom'] <= current_price <= gap['Top']:
            direction = "BULLISH" if gap['FVG'] == 1 else "BEARISH"
            return {
                'in_fvg': True,
                'type': direction,
                'bottom': gap['Bottom'],
                'top': gap['Top'],
                'midpoint': (gap['Bottom'] + gap['Top']) / 2
            }
    return {'in_fvg': False}
```

**FVG entry rules**:
- Enter at 50% of FVG (midpoint) for best risk/reward
- Stop below FVG bottom (bullish) or above FVG top (bearish)
- Target: Next liquidity pool, OB, or swing high/low

### 4. Liquidity Pools

**Definition**: Price levels where stop losses cluster. Market makers need to sweep these to fill their orders.

```
Types of Liquidity:
- Equal Highs (EQH): Two or more highs at same level = sell-side SL cluster
- Equal Lows (EQL): Two or more lows at same level = buy-side SL cluster
- Previous Day High (PDH) / Previous Day Low (PDL): Common SL placements
- Round Numbers ($90,000, $100,000): Psychological SL clusters
- Previous Week High/Low (PWH/PWL): Institutional reference levels
```

```python
# Detect liquidity levels
liquidity = smc.liquidity(df, range_percent=0.01)
# Returns: Levels where liquidity is stored (equal highs/lows)

# Check for recent liquidity sweeps
def detect_liquidity_sweep(df, liquidity_levels, lookback=5):
    """
    Detect when price sweeps a liquidity level and immediately reverses.
    This is a strong signal for entry opposite the sweep direction.
    """
    recent_high = df['high'].tail(lookback).max()
    recent_low = df['low'].tail(lookback).min()
    current_close = df['close'].iloc[-1]

    for level in liquidity_levels['BuySide']:  # Buy-side = sell stops above
        if recent_high > level and current_close < level:
            return {'sweep': 'BUY_SIDE', 'level': level, 'signal': 'SHORT'}

    for level in liquidity_levels['SellSide']:  # Sell-side = buy stops below
        if recent_low < level and current_close > level:
            return {'sweep': 'SELL_SIDE', 'level': level, 'signal': 'LONG'}

    return None
```

### 5. Premium / Discount Zones

```
Equilibrium = 50% of current swing range (fair value)
Premium = Above 50% equilibrium (expensive) → look for shorts
Discount = Below 50% equilibrium (cheap) → look for longs

Formula:
Range High = Recent swing high
Range Low = Recent swing low
Equilibrium = (Range High + Range Low) / 2
Premium = > 75% of range
Discount = < 25% of range

Entry rules:
- Buy in DISCOUNT zone (ideally at OB or FVG)
- Short in PREMIUM zone (ideally at OB or FVG)
- Never buy premium in downtrend / never short discount in uptrend
```

---

## ICT Model Setups

### ICT 2022 Model (High Probability Framework)

**Timeframe**: 15m entries, 1H bias, 4H/1D trend

```
Step 1: Determine HTF Bias (1D/4H)
- Is price in uptrend or downtrend?
- Are we above or below major OBs?
- HTF OB or FVG nearby?

Step 2: Wait for AM Session (9:30-10:30 ET) or London (3-5 AM ET)
- Institutional sessions create most significant moves
- 9:30-10:30 AM ET: Primary liquidity sweep time

Step 3: Identify Liquidity Target
- Where are equal highs/lows?
- What is the prevailing bias for liquidity sweep?

Step 4: Wait for Sweep
- Price grabs liquidity (runs stops above/below key level)
- Wick beyond level + strong rejection

Step 5: Enter on FVG or OB
- 15m FVG inside the displacement after sweep
- Or 15m OB at 50% retracement of the move

Step 6: Target next liquidity
- Buy: Previous day high, equal highs, weekly high
- Sell: Previous day low, equal lows, weekly low
```

### Power of 3 (AMD: Accumulation, Manipulation, Distribution)

```
Asian Session (7 PM - 2 AM ET): Accumulation
- Market ranges, institutions accumulate
- Identify the Asian range (high and low)

London Session (2 AM - 7 AM ET): Manipulation
- Price sweeps one side of Asian range (false breakout)
- This is the liquidity grab

New York Session (7 AM - 12 PM ET): Distribution
- Price reverses from the manipulation
- Trend continues in the true direction (opposite the London sweep)

Trading the Setup:
1. Mark Asian session high and low
2. During London session, wait for sweep of one side
3. When price sweeps AND shows reversal (candle + OB/FVG)
4. Enter in the NY session direction
5. Target: Other side of Asian range × measured move
```

---

## Complete ICT Signal Implementation

```python
import pandas as pd
import numpy as np

class ICTAnalyzer:
    def __init__(self, df):
        self.df = df
        self.current_price = df['close'].iloc[-1]

    def get_full_analysis(self):
        """
        Returns complete ICT analysis with setup identification.
        """
        from smartmoneyconcepts import smc

        # 1. Market Structure
        swings = smc.swing_highs_lows(self.df, swing_length=5)
        bos_choch = smc.bos_choch(self.df, close_break=True)

        # 2. Order Blocks
        ob_data = smc.ob(self.df, swing_length=5)

        # 3. Fair Value Gaps
        fvg_data = smc.fvg(self.df)

        # 4. Liquidity
        liq_data = smc.liquidity(self.df)

        # 5. Premium/Discount
        recent_high = self.df['high'].tail(20).max()
        recent_low = self.df['low'].tail(20).min()
        equilibrium = (recent_high + recent_low) / 2
        range_size = recent_high - recent_low
        premium_threshold = recent_low + range_size * 0.75
        discount_threshold = recent_low + range_size * 0.25

        zone = (
            'PREMIUM' if self.current_price > premium_threshold else
            'DISCOUNT' if self.current_price < discount_threshold else
            'EQUILIBRIUM'
        )

        # Compile setups
        setups = []

        # Check for OB setup
        active_obs = ob_data[ob_data['MitigatedIndex'].isna()] if 'MitigatedIndex' in ob_data.columns else pd.DataFrame()
        for _, ob in active_obs.iterrows():
            if hasattr(ob, 'Top') and ob['Bottom'] <= self.current_price <= ob['Top']:
                ob_type = 'BULLISH' if ob.get('OB', 0) == 1 else 'BEARISH'
                setups.append({
                    'type': f'{ob_type} ORDER BLOCK',
                    'price': self.current_price,
                    'zone_bottom': ob['Bottom'],
                    'zone_top': ob['Top'],
                    'signal': 'LONG' if ob_type == 'BULLISH' else 'SHORT',
                    'confidence': 'HIGH' if zone == ('DISCOUNT' if ob_type == 'BULLISH' else 'PREMIUM') else 'MEDIUM'
                })

        # Check for FVG setup
        active_fvgs = fvg_data[fvg_data['MitigatedIndex'].isna()] if 'MitigatedIndex' in fvg_data.columns else pd.DataFrame()
        for _, gap in active_fvgs.iterrows():
            if hasattr(gap, 'Top') and gap['Bottom'] <= self.current_price <= gap['Top']:
                fvg_type = 'BULLISH' if gap.get('FVG', 0) == 1 else 'BEARISH'
                setups.append({
                    'type': f'{fvg_type} FAIR VALUE GAP',
                    'price': self.current_price,
                    'zone_bottom': gap['Bottom'],
                    'zone_top': gap['Top'],
                    'midpoint': (gap['Bottom'] + gap['Top']) / 2,
                    'signal': 'LONG' if fvg_type == 'BULLISH' else 'SHORT',
                    'confidence': 'MEDIUM'
                })

        # Last BOS/CHOCH
        recent_bos = bos_choch[bos_choch.get('BOS', pd.Series(0)) != 0].tail(1) if 'BOS' in bos_choch.columns else pd.DataFrame()
        recent_choch = bos_choch[bos_choch.get('CHOCH', pd.Series(0)) != 0].tail(1) if 'CHOCH' in bos_choch.columns else pd.DataFrame()

        return {
            'current_price': self.current_price,
            'market_zone': zone,
            'equilibrium': equilibrium,
            'premium_threshold': premium_threshold,
            'discount_threshold': discount_threshold,
            'active_setups': setups,
            'bias': 'LONG_BIAS' if zone == 'DISCOUNT' else 'SHORT_BIAS' if zone == 'PREMIUM' else 'NEUTRAL',
            'has_choch': len(recent_choch) > 0
        }
```

---

## Wyckoff + SMC Integration

```
Wyckoff = WHY price is moving (accumulation/distribution by composite operator)
ICT/SMC = HOW to enter (specific price levels for precision entries)

Combined Framework:

Accumulation Phase (Wyckoff PS → Spring):
- Identify Wyckoff structure (PS, SC, AR, ST, Spring)
- At Spring: Look for liquidity sweep below support = ICT sell-side liquidity grab
- At LPS (Last Point of Support): Look for bullish OB + FVG = entry

Distribution Phase (Wyckoff BC → LPSY):
- Identify distribution structure (BC, AR, UTAD, SOW)
- At UTAD: ICT buy-side liquidity grab above resistance
- At LPSY: Bearish OB + FVG = short entry
```

---

## Session Timing (Critical for ICT)

| Session | Time (ET) | Behavior | ICT Use |
|---------|-----------|----------|---------|
| Asian | 7 PM - 2 AM | Range, accumulation | Mark high/low for AMD setup |
| London | 2 AM - 7 AM | Manipulation sweep | Watch for false break of Asian range |
| New York Open | 7 AM - 10 AM | True direction | Enter after London manipulation |
| NY AM | 10 AM - 12 PM | Continuation | Trail positions |
| NY Close | 2 PM - 4 PM | Position squaring | Exit or reverse |

**Key times for reversals**:
- 9:30 AM ET: NY open, frequent liquidity sweeps
- 10:00-10:30 AM ET: Reversal from opening move
- 2:00-2:30 PM ET: Afternoon reversal time

---

## Setup Quality Checklist

Before entering any ICT setup, score it:

| Criteria | Score |
|----------|-------|
| HTF trend aligned with entry direction | +2 |
| In Premium (for short) or Discount (for long) zone | +2 |
| Confluent OB + FVG at same level | +2 |
| Liquidity sweep just occurred | +2 |
| During high-probability session (NY open, London) | +1 |
| Recent BoS in entry direction | +1 |
| No major S/R blocking the way to target | +1 |

**Score < 6**: Skip  
**Score 6-8**: Half size  
**Score > 8**: Full size

---

## Common Mistakes

❌ Trading OBs without HTF alignment (fighting the trend)
❌ Entering without a liquidity sweep first (need the "setup")
❌ Targeting too close (ICT setups are for measured moves, not scalps)
❌ Ignoring session timing (random entries have much lower probability)
❌ Using ICT concepts alone without considering macro/OI/funding
❌ Over-analyzing — one clear setup per session is enough
