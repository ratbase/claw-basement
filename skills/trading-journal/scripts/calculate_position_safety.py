#!/usr/bin/env python3
"""
Calculate position safety metrics without requiring leverage input.
Only requires: Entry Price, Isolated Margin, Stop Loss
"""

import sys

def calculate_position_safety(entry_price, isolated_margin, stop_loss, side='SHORT', position_size=None, maintenance_margin=0.005):
    """
    Calculate position safety metrics.

    Args:
        entry_price: Entry price
        isolated_margin: Isolated margin allocated (USDT)
        stop_loss: Stop loss price
        side: 'LONG' or 'SHORT'
        position_size: Optional - position size (quantity). If not provided, will estimate.
        maintenance_margin: Maintenance margin ratio (default 0.5% for most pairs)

    Returns:
        Dictionary with all calculated metrics
    """

    entry = float(entry_price)
    margin = float(isolated_margin)
    sl = float(stop_loss)

    # Validate inputs
    if side == 'LONG' and sl >= entry:
        raise ValueError("For LONG positions, Stop Loss must be below Entry Price")
    if side == 'SHORT' and sl <= entry:
        raise ValueError("For SHORT positions, Stop Loss must be above Entry Price")

    # If position size not provided, estimate it based on margin and typical leverage range
    if position_size is None:
        # Calculate at different leverage levels to find realistic position size
        print("\n📊 Estimating position size based on margin...")
        print(f"{'Leverage':<12} {'Position Size':<15} {'Notional':<15} {'Liquidation':<15}")
        print("-" * 60)

        candidates = []
        for lev in [5, 10, 15, 20, 25, 30, 40, 50]:
            # Position Size = Margin × Leverage / Entry
            pos_size = margin * lev / entry
            notional = pos_size * entry

            # Calculate liquidation price
            if side == 'SHORT':
                # For SHORT: Liq = Entry × (1 + 1/Leverage + MM)
                liq = entry * (1 + 1/lev + maintenance_margin)
            else:
                # For LONG: Liq = Entry × (1 - 1/Leverage + MM)
                liq = entry * (1 - 1/lev + maintenance_margin)

            candidates.append({
                'leverage': lev,
                'position_size': pos_size,
                'notional': notional,
                'liquidation': liq
            })

            # Check if SL is safe
            if side == 'SHORT':
                sl_safe = sl < liq
                sl_diff = liq - sl
            else:
                sl_safe = sl > liq
                sl_diff = sl - liq

            status = "✅" if sl_safe else "❌"
            print(f"{lev}x{'':<9} {pos_size:<15.4f} {notional:<15.2f} ${liq:<14.4f} {status}")

        print()

        # Try to match a realistic position size
        # Use 20x as default starting point (can be adjusted)
        default_lev = 20
        position_size = candidates[3]['position_size']  # 20x at index 3
        leverage = default_lev

        print(f"Using estimated position size: {position_size:.4f} at {leverage}x leverage\n")

    else:
        position_size = float(position_size)
        # Calculate leverage from actual values
        # Leverage = Position Size × Entry / Margin
        leverage = (position_size * entry) / margin

    # Calculate notional value
    notional = position_size * entry

    # Calculate risk amount (distance to SL)
    if side == 'SHORT':
        risk_per_unit = sl - entry
    else:
        risk_per_unit = entry - sl

    total_risk = risk_per_unit * position_size

    # Calculate liquidation price
    if side == 'SHORT':
        # For SHORT: Liq = Entry × (1 + 1/Leverage + MM)
        liquidation = entry * (1 + 1/leverage + maintenance_margin)
    else:
        # For LONG: Liq = Entry × (1 - 1/Leverage + MM)
        liquidation = entry * (1 - 1/leverage + maintenance_margin)

    # Check if SL triggers before liquidation
    if side == 'SHORT':
        # For SHORT, SL should be BELOW liquidation (so it triggers first as price goes down)
        # Wait... SHORT means we profit when price goes DOWN
        # SL triggers when price goes UP (against us)
        # So liquidation should be ABOVE SL for safety
        sl_safe = liquidation > sl
        buffer = liquidation - sl
        # Current price position relative to SL and Liq
        current_zone = "SAFE" if sl_safe else "DANGER - Will liquidate before SL"
    else:
        # For LONG, SL should be ABOVE liquidation (so it triggers first as price goes down)
        sl_safe = liquidation < sl
        buffer = sl - liquidation
        current_zone = "SAFE" if sl_safe else "DANGER - Will liquidate before SL"

    # Calculate risk percentage of margin
    risk_of_margin = (total_risk / margin) * 100

    # Calculate R-multiple (what's the reward needed for 1:2 R:R?)
    target_reward = total_risk * 2
    if side == 'SHORT':
        target_take_profit = entry - target_reward / position_size
    else:
        target_take_profit = entry + target_reward / position_size

    results = {
        'entry_price': entry,
        'stop_loss': sl,
        'isolated_margin': margin,
        'position_size': position_size,
        'leverage': leverage,
        'notional_value': notional,
        'liquidation_price': liquidation,
        'total_risk': total_risk,
        'risk_per_unit': risk_per_unit,
        'risk_of_margin_pct': risk_of_margin,
        'sl_safe': sl_safe,
        'sl_buffer': buffer,
        'side': side,
        'maintenance_margin': maintenance_margin,
        'target_reward_2r': target_reward,
        'target_take_profit_2r': target_take_profit
    }

    return results


def print_position_report(results):
    """Print formatted position report"""
    side = results['side']
    side_emoji = "🔴 SHORT" if side == 'SHORT' else "🟢 LONG"

    print("=" * 70)
    print("📊 POSITION SAFETY REPORT")
    print("=" * 70)

    print(f"\n📍 Position: {side_emoji}")
    print(f"   Entry Price:     ${results['entry_price']:.4f}")
    print(f"   Stop Loss:       ${results['stop_loss']:.4f}")
    print(f"   Isolated Margin: ${results['isolated_margin']:.2f} USDT")

    print(f"\n💰 Position Details:")
    print(f"   Position Size:   {results['position_size']:.4f}")
    print(f"   Notional Value:  ${results['notional_value']:.2f}")
    print(f"   Effective Leverage: {results['leverage']:.1f}x")

    print(f"\n⚠️  Risk Analysis:")
    print(f"   Risk per Unit:   ${results['risk_per_unit']:.4f}")
    print(f"   Total Risk:      ${results['total_risk']:.2f} USDT")
    print(f"   Risk of Margin:  {results['risk_of_margin_pct']:.1f}%")

    print(f"\n💧 Liquidation:")
    print(f"   Liquidation Price: ${results['liquidation_price']:.4f}")

    print(f"\n🛑 Stop Loss Safety:")
    if side == 'SHORT':
        # SHORT: Entry < SL < Liq is BAD (liquidates first)
        # Entry < Liq < SL is GOOD (SL triggers first... wait no)

        # SHORT: We want price to go DOWN
        # If price goes UP past Entry, we lose money
        # SL triggers when price goes UP to SL level
        # Liquidation triggers when price goes UP to Liq level
        # We want SL < Liq so SL triggers FIRST
        print(f"   SL Position:     ${results['stop_loss']:.4f}")
        print(f"   Liq Position:    ${results['liquidation_price']:.4f}")
        print(f"   Buffer:          ${results['sl_buffer']:.4f}")
        if results['sl_safe']:
            print(f"   ✅ SAFE: Stop Loss will trigger BEFORE liquidation")
            print(f"      Price must rise to ${results['stop_loss']:.4f} to trigger SL")
            print(f"      Price must rise to ${results['liquidation_price']:.4f} to liquidate")
        else:
            print(f"   ❌ DANGER: Liquidation will trigger BEFORE Stop Loss!")
            print(f"      Price must rise to ${results['liquidation_price']:.4f} to liquidate")
            print(f"      Price must rise to ${results['stop_loss']:.4f} to trigger SL")
    else:
        print(f"   SL Position:     ${results['stop_loss']:.4f}")
        print(f"   Liq Position:    ${results['liquidation_price']:.4f}")
        print(f"   Buffer:          ${results['sl_buffer']:.4f}")
        if results['sl_safe']:
            print(f"   ✅ SAFE: Stop Loss will trigger BEFORE liquidation")
            print(f"      Price must fall to ${results['stop_loss']:.4f} to trigger SL")
            print(f"      Price must fall to ${results['liquidation_price']:.4f} to liquidate")
        else:
            print(f"   ❌ DANGER: Liquidation will trigger BEFORE Stop Loss!")
            print(f"      Price must fall to ${results['liquidation_price']:.4f} to liquidate")
            print(f"      Price must fall to ${results['stop_loss']:.4f} to trigger SL")

    print(f"\n🎯 Target for 1:2 R:R:")
    print(f"   Required Reward:  ${results['target_reward_2r']:.2f} USDT")
    print(f"   Target TP:        ${results['target_take_profit_2r']:.4f}")

    print(f"\n" + "=" * 70)

    # Recommendations
    print("💡 RECOMMENDATIONS:")
    print("-" * 70)

    if not results['sl_safe']:
        print("❌ CRITICAL: Stop Loss is NOT safe!")
        if side == 'SHORT':
            # For SHORT, Liq is above SL - need to increase Liq (reduce leverage)
            print(f"   Current Liq (${results['liquidation_price']:.4f}) is BELOW SL (${results['stop_loss']:.4f})")
            print(f"   Reduce leverage to ~{max(5, int(results['leverage'] * 0.6))}x or increase margin")
            print(f"   OR move SL down to ~${results['liquidation_price'] - 0.10:.4f} (below liquidation)")
        else:
            print(f"   Current Liq (${results['liquidation_price']:.4f}) is ABOVE SL (${results['stop_loss']:.4f})")
            print(f"   Reduce leverage to ~{max(5, int(results['leverage'] * 0.6))}x or increase margin")
            print(f"   OR move SL up to ~${results['liquidation_price'] + 0.10:.4f} (above liquidation)")
    else:
        print(f"✅ Stop Loss is safe with {results['sl_buffer']:.4f} buffer")

    if results['risk_of_margin_pct'] > 100:
        print("⚠️  WARNING: Risk exceeds 100% of margin - you'll lose entire margin before SL triggers!")
    elif results['risk_of_margin_pct'] > 50:
        print("⚠️  CAUTION: Risk is >50% of margin - consider reducing position size")
    elif results['risk_of_margin_pct'] > 30:
        print("⚠️  Note: Risk is >30% of margin - higher risk than recommended")
    else:
        print("✅ Risk level is acceptable")

    if results['leverage'] > 30:
        print(f"⚠️  WARNING: Leverage ({results['leverage']:.1f}x) is very high - consider 10-20x")

    print("=" * 70)


def main():
    """Main function to run from command line"""
    if len(sys.argv) < 4:
        print("Usage: python calculate_position_safety.py <entry_price> <isolated_margin> <stop_loss> [side] [position_size]")
        print("\nExample:")
        print("  python calculate_position_safety.py 29.47 53.69 31.00 SHORT")
        print("  python calculate_position_safety.py 50000 100 48000 LONG 0.02")
        print("\nParameters:")
        print("  entry_price    - Entry price (e.g., 29.47)")
        print("  isolated_margin - Isolated margin allocated (e.g., 53.69)")
        print("  stop_loss      - Stop loss price (e.g., 31.00)")
        print("  side           - LONG or SHORT (default: SHORT)")
        print("  position_size  - Optional: Actual position size quantity")
        sys.exit(1)

    entry_price = float(sys.argv[1])
    isolated_margin = float(sys.argv[2])
    stop_loss = float(sys.argv[3])
    side = sys.argv[4].upper() if len(sys.argv) > 4 else 'SHORT'
    position_size = float(sys.argv[5]) if len(sys.argv) > 5 else None

    try:
        results = calculate_position_safety(entry_price, isolated_margin, stop_loss, side, position_size)
        print_position_report(results)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
