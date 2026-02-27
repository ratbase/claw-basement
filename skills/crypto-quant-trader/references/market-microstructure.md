# Market Microstructure for Crypto Futures

## Overview

Market microstructure studies how markets execute trades at the granular level. For crypto futures traders, understanding microstructure gives a significant edge in:
- Entry/exit timing
- Order impact minimization
- Short-term price prediction (~65% of 1-5 minute moves explained by OBI)

---

## Order Book Analysis

### Order Book Imbalance (OBI)

The single most predictive microstructure signal for short-term price direction.

```python
def order_book_imbalance(bids, asks, depth=1):
    """
    Calculate OBI at specified depth.
    
    L1 (depth=1): Best bid/ask — ~65% predictive power for 1-min moves
    L5 (depth=5): 5 levels — signals 2-5 min moves
    L10 (depth=10): 10 levels — signals 5-15 min moves
    
    Returns: Float [-1, +1]
    +1 = Maximum buy pressure
    -1 = Maximum sell pressure
    """
    bid_vol = sum(float(b[1]) for b in bids[:depth])
    ask_vol = sum(float(a[1]) for a in asks[:depth])
    total = bid_vol + ask_vol
    if total == 0:
        return 0.0
    return (bid_vol - ask_vol) / total

# Multi-depth OBI signal
def multi_depth_obi_signal(order_book):
    bids = order_book['bids']  # [[price, qty], ...]
    asks = order_book['asks']

    obi = {
        'L1': order_book_imbalance(bids, asks, depth=1),
        'L5': order_book_imbalance(bids, asks, depth=5),
        'L10': order_book_imbalance(bids, asks, depth=10),
    }

    # Composite signal (weighted toward L1)
    composite = obi['L1'] * 0.6 + obi['L5'] * 0.3 + obi['L10'] * 0.1

    return {**obi, 'composite': composite}

# Entry signals from OBI
def obi_trade_signal(composite_obi, threshold=0.3):
    if composite_obi > threshold:
        return 'LONG'
    elif composite_obi < -threshold:
        return 'SHORT'
    return 'NEUTRAL'
```

### Real-Time Order Book via WebSocket

```python
import asyncio
import websockets
import json
from collections import OrderedDict

class OrderBook:
    def __init__(self, symbol):
        self.symbol = symbol
        self.bids = OrderedDict()  # price → qty
        self.asks = OrderedDict()  # price → qty

    async def start_stream(self):
        uri = f"wss://fstream.binance.com/ws/{self.symbol.lower()}@depth@100ms"
        async with websockets.connect(uri) as ws:
            async for message in ws:
                update = json.loads(message)
                self._apply_update(update)

    def _apply_update(self, update):
        for price, qty in update.get('b', []):
            price, qty = float(price), float(qty)
            if qty == 0:
                self.bids.pop(price, None)
            else:
                self.bids[price] = qty

        for price, qty in update.get('a', []):
            price, qty = float(price), float(qty)
            if qty == 0:
                self.asks.pop(price, None)
            else:
                self.asks[price] = qty

    def get_obi(self, depth=5):
        sorted_bids = sorted(self.bids.items(), reverse=True)[:depth]
        sorted_asks = sorted(self.asks.items())[:depth]

        bid_vol = sum(qty for _, qty in sorted_bids)
        ask_vol = sum(qty for _, qty in sorted_asks)
        total = bid_vol + ask_vol
        return (bid_vol - ask_vol) / total if total > 0 else 0
```

### Spread Analysis

```python
def spread_analysis(best_bid, best_ask, mark_price):
    """
    Analyze market quality and execution cost.
    """
    spread = best_ask - best_bid
    spread_bps = (spread / mark_price) * 10000  # Basis points

    return {
        'absolute_spread': spread,
        'spread_bps': spread_bps,
        'mid_price': (best_bid + best_ask) / 2,
        'market_quality': 'tight' if spread_bps < 1 else 'normal' if spread_bps < 5 else 'wide',
        'execution_cost_roundtrip_bps': spread_bps  # Min cost for taker round-trip
    }
```

---

## Trade Flow Analysis

### Trade Flow Imbalance (TFI)

Measures aggressive buyer vs. seller pressure from actual trades (not quotes).

```python
from collections import deque
from datetime import datetime, timedelta

class TradeFlowAnalyzer:
    def __init__(self, window_seconds=60):
        self.trades = deque()
        self.window_seconds = window_seconds

    def add_trade(self, price, quantity, is_buyer_maker, timestamp_ms):
        """
        is_buyer_maker=True: Sell aggressor (maker was buyer = passive)
        is_buyer_maker=False: Buy aggressor (taker was buyer = aggressive)
        """
        self.trades.append({
            'price': float(price),
            'qty': float(quantity),
            'is_sell': is_buyer_maker,  # Confusingly named in Binance API
            'time': datetime.fromtimestamp(timestamp_ms / 1000)
        })
        self._cleanup()

    def _cleanup(self):
        cutoff = datetime.now() - timedelta(seconds=self.window_seconds)
        while self.trades and self.trades[0]['time'] < cutoff:
            self.trades.popleft()

    def get_tfi(self):
        """Returns Trade Flow Imbalance in [-1, +1]."""
        buy_vol = sum(t['qty'] for t in self.trades if not t['is_sell'])
        sell_vol = sum(t['qty'] for t in self.trades if t['is_sell'])
        total = buy_vol + sell_vol
        return (buy_vol - sell_vol) / total if total > 0 else 0

    def get_large_trade_alert(self, size_threshold_usd=50000):
        """Detect whale-size aggressive trades."""
        alerts = []
        for t in self.trades:
            value = t['price'] * t['qty']
            if value > size_threshold_usd:
                alerts.append({
                    'side': 'SELL' if t['is_sell'] else 'BUY',
                    'value': value,
                    'price': t['price'],
                    'time': t['time']
                })
        return alerts
```

---

## Volume Profile

Identifies price levels where the most volume has traded — these become support/resistance.

```python
import pandas as pd
import numpy as np

def calculate_volume_profile(df, n_bins=100):
    """
    Build volume profile from OHLCV data.
    
    Returns:
    - POC: Point of Control (max volume price)
    - VAH: Value Area High (upper boundary of 70% volume zone)
    - VAL: Value Area Low (lower boundary of 70% volume zone)
    - Profile: Full price→volume mapping
    """
    price_min = df['low'].min()
    price_max = df['high'].max()
    bins = np.linspace(price_min, price_max, n_bins + 1)

    # Approximate volume at each price level
    # (True volume profile needs tick data; this is OHLCV approximation)
    volume_by_price = np.zeros(n_bins)
    for _, row in df.iterrows():
        candle_range = row['high'] - row['low']
        if candle_range == 0:
            continue
        for i, (low_edge, high_edge) in enumerate(zip(bins[:-1], bins[1:])):
            overlap_low = max(row['low'], low_edge)
            overlap_high = min(row['high'], high_edge)
            if overlap_high > overlap_low:
                overlap_frac = (overlap_high - overlap_low) / candle_range
                volume_by_price[i] += row['volume'] * overlap_frac

    # Find key levels
    poc_idx = np.argmax(volume_by_price)
    poc = (bins[poc_idx] + bins[poc_idx + 1]) / 2

    # Value Area (70% of total volume)
    total_volume = volume_by_price.sum()
    target_volume = total_volume * 0.70

    # Expand from POC outward until 70% captured
    va_low_idx = poc_idx
    va_high_idx = poc_idx
    captured_volume = volume_by_price[poc_idx]

    while captured_volume < target_volume:
        can_expand_up = va_high_idx < n_bins - 1
        can_expand_down = va_low_idx > 0

        if can_expand_up and can_expand_down:
            add_up = volume_by_price[va_high_idx + 1]
            add_down = volume_by_price[va_low_idx - 1]
            if add_up >= add_down:
                va_high_idx += 1
                captured_volume += add_up
            else:
                va_low_idx -= 1
                captured_volume += add_down
        elif can_expand_up:
            va_high_idx += 1
            captured_volume += volume_by_price[va_high_idx]
        elif can_expand_down:
            va_low_idx -= 1
            captured_volume += volume_by_price[va_low_idx]
        else:
            break

    vah = bins[va_high_idx + 1]
    val = bins[va_low_idx]

    return {
        'poc': poc,
        'vah': vah,
        'val': val,
        'profile': dict(zip((bins[:-1] + bins[1:]) / 2, volume_by_price))
    }

# Trading rules from volume profile
def volume_profile_signal(current_price, profile_levels):
    poc = profile_levels['poc']
    vah = profile_levels['vah']
    val = profile_levels['val']

    if current_price < val:
        return {'signal': 'LONG', 'reason': 'Below Value Area Low', 'target': poc}
    elif current_price > vah:
        return {'signal': 'SHORT', 'reason': 'Above Value Area High', 'target': poc}
    elif abs(current_price - poc) / poc < 0.005:
        return {'signal': 'NEUTRAL', 'reason': 'At POC — wait for direction'}
    elif current_price > poc:
        return {'signal': 'LONG_TARGET', 'reason': 'Above POC, target VAH', 'target': vah}
    else:
        return {'signal': 'SHORT_TARGET', 'reason': 'Below POC, target VAL', 'target': val}
```

---

## VWAP Strategies

```python
def calculate_vwap(df):
    """Calculate VWAP with standard deviation bands."""
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    cumulative_tp_vol = (typical_price * df['volume']).cumsum()
    cumulative_vol = df['volume'].cumsum()
    vwap = cumulative_tp_vol / cumulative_vol

    # Deviation bands
    squared_deviation = ((typical_price - vwap) ** 2 * df['volume']).cumsum() / cumulative_vol
    std_dev = np.sqrt(squared_deviation)

    return {
        'vwap': vwap,
        'upper_1': vwap + std_dev,
        'lower_1': vwap - std_dev,
        'upper_2': vwap + 2 * std_dev,
        'lower_2': vwap - 2 * std_dev,
    }

# VWAP trading rules
VWAP_RULES = """
Long setups:
- Price > VWAP + trending up: Buy pullbacks to VWAP
- Price at VWAP - 1σ band: Mean reversion long
- Price reclaims VWAP after trading below: Momentum long

Short setups:
- Price < VWAP + trending down: Short bounces to VWAP
- Price at VWAP + 1σ band: Mean reversion short
- Price loses VWAP after trading above: Momentum short

Targets:
- From -1σ: Target VWAP (mean reversion)
- From VWAP: Target +1σ or -1σ depending on direction
- Extreme: From ±2σ, target VWAP
"""
```

---

## Liquidation Analysis

### Liquidation Map (Estimated)

```python
def estimate_liquidation_levels(positions_data, mark_price):
    """
    Estimate where liquidations will occur based on open interest data.
    (Binance doesn't expose exact liquidation prices publicly)
    
    Logic: Traders enter at various prices with various leverage.
    At each level, calculate approximate liquidation price.
    
    Common leverage: 10x-25x for retail, 3x-10x for institutional
    """
    liquidation_density = {}

    for entry_price, oi_at_price in positions_data.items():
        for leverage in [5, 10, 20, 25]:
            # Long liquidation = Entry × (1 - 1/Leverage)
            long_liq = entry_price * (1 - 1/leverage)
            # Short liquidation = Entry × (1 + 1/Leverage)
            short_liq = entry_price * (1 + 1/leverage)

            long_liq_rounded = round(long_liq, -2)  # Round to nearest 100
            short_liq_rounded = round(short_liq, -2)

            liquidation_density[long_liq_rounded] = (
                liquidation_density.get(long_liq_rounded, 0) + oi_at_price
            )

    return {k: v for k, v in sorted(liquidation_density.items())}

# Liquidation cascade detection
def detect_cascade(recent_liquidations, window_seconds=60, threshold=10):
    """
    Detect if liquidation cascade is in progress.
    Cascades often produce strong mean-reversion opportunities.
    """
    if len(recent_liquidations) < threshold:
        return None

    sides = [liq['side'] for liq in recent_liquidations]
    dominant = max(set(sides), key=sides.count)
    dominance_ratio = sides.count(dominant) / len(sides)

    if dominance_ratio > 0.7:
        return {
            'cascade_detected': True,
            'cascade_side': dominant,           # Which side is being liquidated
            'mean_reversion_signal': 'LONG' if dominant == 'SELL' else 'SHORT',
            'confidence': dominance_ratio,
            'total_liquidations': len(recent_liquidations)
        }
    return None
```

### Reading Liquidation Events (from WebSocket)

```python
async def process_liquidation(event):
    order = event['o']
    side = order['S']    # SELL = long was liquidated; BUY = short was liquidated
    qty = float(order['q'])
    price = float(order['ap'])  # Average fill price
    value = qty * price

    # Track for cascade detection
    monitor.add_liquidation({'side': side, 'qty': qty, 'price': price, 'value': value})

    # High-value liquidation alert
    if value > 100000:
        print(f"🔥 LARGE LIQUIDATION: ${value:,.0f} {side} @ {price:,.2f}")
        # High-value liquidations often precede short-term mean reversals
```

---

## Funding Rate Microstructure

```python
def analyze_funding_microstructure(funding_history, current_funding):
    """
    Analyze funding rate dynamics for trading signals.
    """
    recent_rates = [f['fundingRate'] for f in funding_history[-24:]]  # Last 24 periods (8 days)
    avg_rate = sum(recent_rates) / len(recent_rates)
    std_rate = np.std(recent_rates)

    # Z-score of current funding
    z_score = (current_funding - avg_rate) / std_rate if std_rate > 0 else 0

    return {
        'current_funding': current_funding,
        'average_8d': avg_rate,
        'z_score': z_score,
        'annualized': current_funding * 3 * 365,
        'signal': (
            'EXTREME_LONG_CROWDING' if z_score > 2.5 else
            'HIGH_LONG_CROWDING' if z_score > 1.5 else
            'EXTREME_SHORT_CROWDING' if z_score < -2.5 else
            'HIGH_SHORT_CROWDING' if z_score < -1.5 else
            'NEUTRAL'
        ),
        # Contrarian signals
        'contrarian_bias': (
            'SHORT' if z_score > 2.5 else
            'LONG' if z_score < -2.5 else
            'NEUTRAL'
        )
    }
```

---

## Composite Microstructure Signal

```python
def composite_signal(obi_l1, obi_l5, tfi, funding_z, liquidation_side=None):
    """
    Combine multiple microstructure signals into actionable direction.
    
    Returns: {'direction': 'LONG'|'SHORT'|'NEUTRAL', 'strength': 0-1, 'reasoning': [...]}
    """
    score = 0.0
    reasoning = []

    # OBI signals (short-term)
    if obi_l1 > 0.4:
        score += 0.3
        reasoning.append(f"OBI L1 strongly positive ({obi_l1:.2f})")
    elif obi_l1 < -0.4:
        score -= 0.3
        reasoning.append(f"OBI L1 strongly negative ({obi_l1:.2f})")

    if obi_l5 > 0.3:
        score += 0.2
        reasoning.append(f"OBI L5 positive ({obi_l5:.2f})")
    elif obi_l5 < -0.3:
        score -= 0.2
        reasoning.append(f"OBI L5 negative ({obi_l5:.2f})")

    # Trade flow (medium-term)
    if tfi > 0.3:
        score += 0.25
        reasoning.append(f"Buy flow dominant ({tfi:.2f})")
    elif tfi < -0.3:
        score -= 0.25
        reasoning.append(f"Sell flow dominant ({tfi:.2f})")

    # Funding (contrarian)
    if funding_z > 2:
        score -= 0.15
        reasoning.append(f"High long crowding (z={funding_z:.1f}) → short bias")
    elif funding_z < -2:
        score += 0.15
        reasoning.append(f"High short crowding (z={funding_z:.1f}) → long bias")

    # Liquidation cascade
    if liquidation_side == 'SELL':  # Long liquidations = longs flushed → rebound
        score += 0.1
        reasoning.append("Long liquidation cascade → mean reversion long")
    elif liquidation_side == 'BUY':  # Short liquidations = shorts flushed
        score -= 0.1
        reasoning.append("Short liquidation cascade → mean reversion short")

    direction = 'LONG' if score > 0.2 else 'SHORT' if score < -0.2 else 'NEUTRAL'
    return {'direction': direction, 'strength': abs(score), 'score': score, 'reasoning': reasoning}
```

---

## Open Interest Analysis

```python
def analyze_open_interest(oi_history, price_history):
    """
    OI + Price divergence analysis.
    
    OI Rising + Price Rising = Strong Bull (trend confirmed)
    OI Rising + Price Falling = Strong Bear (trend confirmed)
    OI Falling + Price Rising = Weak Rally (short covering)
    OI Falling + Price Falling = Weak Decline (long liquidation)
    """
    if len(oi_history) < 2 or len(price_history) < 2:
        return 'INSUFFICIENT_DATA'

    oi_change = (oi_history[-1] - oi_history[-2]) / oi_history[-2]
    price_change = (price_history[-1] - price_history[-2]) / price_history[-2]

    if oi_change > 0.01 and price_change > 0.005:
        return {'signal': 'STRONG_BULL', 'description': 'New longs entering at higher prices'}
    elif oi_change > 0.01 and price_change < -0.005:
        return {'signal': 'STRONG_BEAR', 'description': 'New shorts entering at lower prices'}
    elif oi_change < -0.01 and price_change > 0.005:
        return {'signal': 'WEAK_RALLY', 'description': 'Short covering, not fresh longs'}
    elif oi_change < -0.01 and price_change < -0.005:
        return {'signal': 'WEAK_DECLINE', 'description': 'Long liquidation, not fresh shorts'}
    return {'signal': 'NEUTRAL', 'description': 'No clear directional conviction'}
```

---

## Quick Reference

| Signal | Threshold | Meaning |
|--------|-----------|---------|
| OBI L1 > +0.5 | Strong | Aggressive buying, expect short-term upward |
| OBI L1 < -0.5 | Strong | Aggressive selling, expect short-term downward |
| TFI > +0.3 | Moderate | Buy flow dominates 1-min window |
| TFI < -0.3 | Moderate | Sell flow dominates 1-min window |
| Funding Z > +2.5 | Extreme | Longs overcrowded, contrarian short |
| Funding Z < -2.5 | Extreme | Shorts overcrowded, contrarian long |
| Liquidations > 10/min same side | Cascade | Mean reversion opposite direction |
| OI up + Price up | — | Strong trend, ride momentum |
| OI up + Price down | — | Heavy shorting, dangerous for longs |
