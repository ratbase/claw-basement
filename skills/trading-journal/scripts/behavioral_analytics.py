#!/usr/bin/env python3
"""
Behavioral Analytics for Trading
Detects psychological patterns that hurt performance:
- Revenge trading (re-entry within 15min of loss)
- Tilt detection (position size spikes after losses)
- Time-of-day performance analysis
- Day-of-week performance analysis
- Holding period analysis
- Streak analysis (win/loss streaks)
- Overtrading detection

Usage:
    python3 behavioral_analytics.py --days 90
    python3 behavioral_analytics.py --days 30 --verbose
"""

import os
import sys
import argparse
import hmac
import hashlib
import time
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

import requests

try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / '.binance_config')
except ImportError:
    config = Path.home() / '.binance_config'
    if config.exists():
        for line in config.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()

API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
BASE_URL = 'https://fapi.binance.com'


# ─────────────────────────────────────────────────────────
# API Client
# ─────────────────────────────────────────────────────────

def sign(params: dict) -> dict:
    params['timestamp'] = int(time.time() * 1000)
    query = urllib.parse.urlencode(sorted(params.items()))
    params['signature'] = hmac.new(
        API_SECRET.encode(), query.encode(), hashlib.sha256
    ).hexdigest()
    return params


def api(endpoint: str, params: dict = None) -> list | dict:
    if not API_KEY or not API_SECRET:
        print("ERROR: BINANCE_API_KEY / BINANCE_API_SECRET not found in ~/.binance_config")
        sys.exit(1)
    params = sign(params or {})
    r = requests.get(
        f"{BASE_URL}{endpoint}",
        headers={'X-MBX-APIKEY': API_KEY},
        params=params,
        timeout=15
    )
    r.raise_for_status()
    return r.json()


def fetch_income(days: int) -> list:
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - days * 24 * 3600 * 1000
    all_income = []
    cursor = start_ms

    while cursor < end_ms:
        batch = api('/fapi/v1/income', {
            'startTime': cursor,
            'endTime': end_ms,
            'limit': 1000
        })
        if not batch:
            break
        all_income.extend(batch)
        if len(batch) < 1000:
            break
        cursor = int(batch[-1]['time']) + 1

    return all_income


def build_trades(income: list) -> list:
    """Build trade list from income records."""
    trades = []
    records = [r for r in income if r['incomeType'] == 'REALIZED_PNL' and float(r['income']) != 0]
    records.sort(key=lambda x: x['time'])

    for r in records:
        pnl = float(r['income'])
        dt = datetime.fromtimestamp(r['time'] / 1000)
        trades.append({
            'symbol': r['symbol'],
            'pnl': pnl,
            'win': pnl > 0,
            'time': dt,
            'hour': dt.hour,
            'day_name': dt.strftime('%A'),
            'day_num': dt.weekday(),  # 0=Monday
        })
    return trades


# ─────────────────────────────────────────────────────────
# Behavioral Detectors
# ─────────────────────────────────────────────────────────

def detect_revenge_trading(trades: list, window_minutes: int = 15) -> dict:
    """
    Detect revenge trading: new trade opened within X minutes of a losing trade.
    
    Research shows revenge trades have 34% lower win rate than baseline.
    """
    revenge_trades = []
    baseline_trades = []

    for i, trade in enumerate(trades):
        if i == 0:
            baseline_trades.append(trade)
            continue

        prev = trades[i - 1]
        time_since_prev = (trade['time'] - prev['time']).total_seconds() / 60

        if not prev['win'] and time_since_prev <= window_minutes:
            revenge_trades.append({**trade, 'time_after_loss_min': time_since_prev})
        else:
            baseline_trades.append(trade)

    rt_win_rate = sum(1 for t in revenge_trades if t['win']) / len(revenge_trades) if revenge_trades else 0
    bl_win_rate = sum(1 for t in baseline_trades if t['win']) / len(baseline_trades) if baseline_trades else 0

    return {
        'revenge_count': len(revenge_trades),
        'total_trades': len(trades),
        'revenge_pct': len(revenge_trades) / len(trades) if trades else 0,
        'revenge_win_rate': rt_win_rate,
        'baseline_win_rate': bl_win_rate,
        'performance_hit': bl_win_rate - rt_win_rate,
        'revenge_pnl': sum(t['pnl'] for t in revenge_trades),
        'revenge_trades': revenge_trades,
    }


def detect_tilt(trades: list, rolling_window: int = 10, size_spike_threshold: float = 1.25) -> dict:
    """
    Detect tilt: position size spikes ≥ threshold × rolling avg after a loss.
    
    Uses PnL as proxy for position size (absolute value).
    """
    tilt_instances = []

    for i, trade in enumerate(trades):
        if i < rolling_window:
            continue

        prev = trades[i - 1]
        if prev['win']:
            continue  # Tilt only relevant after losses

        # Rolling average absolute PnL (proxy for position size)
        recent_pnls = [abs(t['pnl']) for t in trades[i - rolling_window:i]]
        avg_size = sum(recent_pnls) / len(recent_pnls)
        current_size = abs(trade['pnl'])

        if avg_size > 0 and current_size > avg_size * size_spike_threshold:
            tilt_instances.append({
                **trade,
                'size_ratio': current_size / avg_size,
                'avg_size': avg_size,
                'current_size': current_size
            })

    tilt_pnl = sum(t['pnl'] for t in tilt_instances)
    tilt_win_rate = sum(1 for t in tilt_instances if t['win']) / len(tilt_instances) if tilt_instances else 0

    return {
        'tilt_count': len(tilt_instances),
        'tilt_pct': len(tilt_instances) / len(trades) if trades else 0,
        'tilt_win_rate': tilt_win_rate,
        'tilt_pnl': tilt_pnl,
        'avg_size_spike': sum(t['size_ratio'] for t in tilt_instances) / len(tilt_instances) if tilt_instances else 0,
        'tilt_instances': tilt_instances,
    }


def time_of_day_analysis(trades: list) -> dict:
    """
    Performance breakdown by hour and session.
    """
    sessions = {
        'Asian (0-7 ET)': range(0, 7),
        'London (7-9 ET)': range(7, 9),
        'NY Open (9-12 ET)': range(9, 12),
        'NY Afternoon (12-16 ET)': range(12, 16),
        'Evening (16-24 ET)': range(16, 24),
    }

    # UTC offset — adjust if needed based on your timezone
    # All times below are in whatever timezone your system clock is in
    hour_stats = defaultdict(lambda: {'trades': [], 'wins': 0, 'losses': 0, 'pnl': 0})

    for trade in trades:
        hour = trade['hour']
        hour_stats[hour]['trades'].append(trade['pnl'])
        hour_stats[hour]['pnl'] += trade['pnl']
        if trade['win']:
            hour_stats[hour]['wins'] += 1
        else:
            hour_stats[hour]['losses'] += 1

    # Compile
    hours_with_data = []
    for h, stats in hour_stats.items():
        n = stats['wins'] + stats['losses']
        if n >= 2:
            hours_with_data.append({
                'hour': h,
                'n': n,
                'win_rate': stats['wins'] / n,
                'pnl': stats['pnl'],
                'avg_pnl': stats['pnl'] / n,
            })

    hours_with_data.sort(key=lambda x: x['win_rate'], reverse=True)
    best_hours = [h for h in hours_with_data if h['win_rate'] >= 0.6]
    worst_hours = [h for h in hours_with_data if h['win_rate'] < 0.4]

    return {
        'by_hour': hours_with_data,
        'best_hours': best_hours,
        'worst_hours': worst_hours,
    }


def day_of_week_analysis(trades: list) -> list:
    """Performance breakdown by day of week."""
    day_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0, 'name': ''})

    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for trade in trades:
        d = trade['day_num']
        day_stats[d]['name'] = day_names[d]
        day_stats[d]['pnl'] += trade['pnl']
        if trade['win']:
            day_stats[d]['wins'] += 1
        else:
            day_stats[d]['losses'] += 1

    result = []
    for d in range(7):
        if d in day_stats:
            s = day_stats[d]
            n = s['wins'] + s['losses']
            if n >= 1:
                result.append({
                    'day': s['name'],
                    'n': n,
                    'win_rate': s['wins'] / n,
                    'pnl': s['pnl'],
                    'avg_pnl': s['pnl'] / n,
                })

    return sorted(result, key=lambda x: x['win_rate'], reverse=True)


def streak_analysis(trades: list) -> dict:
    """
    Analyze win/loss streaks.
    """
    if not trades:
        return {}

    max_win = 0
    max_loss = 0
    cur_win = 0
    cur_loss = 0
    streaks_at_end = []

    for i, trade in enumerate(trades):
        if trade['win']:
            cur_win += 1
            cur_loss = 0
        else:
            cur_loss += 1
            cur_win = 0
        max_win = max(max_win, cur_win)
        max_loss = max(max_loss, cur_loss)

        # Track performance after streaks end
        if i > 0:
            prev_win = trades[i-1]['win']
            if trade['win'] != prev_win:
                streaks_at_end.append({'streak_ended': not trade['win'], 'next_win': trade['win']})

    # Post-streak performance
    post_loss_streak = [s['next_win'] for s in streaks_at_end if not s['streak_ended']]
    post_win_streak = [s['next_win'] for s in streaks_at_end if s['streak_ended']]

    return {
        'max_win_streak': max_win,
        'max_loss_streak': max_loss,
        'post_win_streak_win_rate': sum(post_win_streak) / len(post_win_streak) if post_win_streak else None,
        'post_loss_streak_win_rate': sum(post_loss_streak) / len(post_loss_streak) if post_loss_streak else None,
    }


def overtrading_check(trades: list, session_hours: int = 8, max_trades_per_session: int = 5) -> dict:
    """
    Detect overtrading: too many trades per session.
    Research shows win rate drops significantly after 5th trade in a session.
    """
    daily_counts = defaultdict(list)
    for trade in trades:
        date_key = trade['time'].date()
        daily_counts[date_key].append(trade)

    overtraded_days = []
    for date, day_trades in daily_counts.items():
        if len(day_trades) > max_trades_per_session:
            win_rate_first5 = sum(1 for t in day_trades[:5] if t['win']) / 5 if len(day_trades) >= 5 else None
            win_rate_after5 = sum(1 for t in day_trades[5:] if t['win']) / len(day_trades[5:]) if len(day_trades) > 5 else None
            overtraded_days.append({
                'date': str(date),
                'n_trades': len(day_trades),
                'win_rate_first_5': win_rate_first5,
                'win_rate_after_5': win_rate_after5,
            })

    return {
        'overtraded_days': len(overtraded_days),
        'total_days': len(daily_counts),
        'overtraded_details': overtraded_days,
        'avg_trades_per_day': sum(len(v) for v in daily_counts.values()) / len(daily_counts) if daily_counts else 0,
    }


def symbol_analysis(trades: list) -> list:
    """Performance breakdown by symbol."""
    sym_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0})

    for trade in trades:
        sym = trade['symbol']
        sym_stats[sym]['pnl'] += trade['pnl']
        if trade['win']:
            sym_stats[sym]['wins'] += 1
        else:
            sym_stats[sym]['losses'] += 1

    result = []
    for sym, s in sym_stats.items():
        n = s['wins'] + s['losses']
        result.append({
            'symbol': sym,
            'n': n,
            'win_rate': s['wins'] / n,
            'pnl': s['pnl'],
            'avg_pnl': s['pnl'] / n,
        })

    return sorted(result, key=lambda x: x['pnl'], reverse=True)


# ─────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────

def bar(win_rate: float, width: int = 20) -> str:
    filled = round(win_rate * width)
    return '█' * filled + '░' * (width - filled)


def wr_color(wr: float) -> str:
    if wr >= 0.60:
        return '🟢'
    elif wr >= 0.45:
        return '🟡'
    return '🔴'


def main():
    parser = argparse.ArgumentParser(description='Behavioral trading analytics')
    parser.add_argument('--days', type=int, default=90, help='Days of history')
    parser.add_argument('--verbose', action='store_true', help='Show individual revenge/tilt trades')
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"  🧠  BEHAVIORAL ANALYTICS  ({args.days}-day period)")
    print(f"{'='*70}")

    print(f"\nFetching {args.days} days of income history...")
    income = fetch_income(args.days)

    if not income:
        print("No income records found.")
        sys.exit(0)

    trades = build_trades(income)

    if not trades:
        print("No completed trades found.")
        sys.exit(0)

    n = len(trades)
    overall_wr = sum(1 for t in trades if t['win']) / n
    total_pnl = sum(t['pnl'] for t in trades)

    print(f"\n  Total trades: {n}  |  Win rate: {overall_wr:.1%}  |  Total PnL: {total_pnl:+.2f} USDT")

    # ─── Revenge Trading ───────────────────────────────────
    rt = detect_revenge_trading(trades, window_minutes=15)
    print(f"\n{'─'*70}")
    print("  ⚠️   REVENGE TRADING ANALYSIS")
    print(f"{'─'*70}")
    if rt['revenge_count'] == 0:
        print("  ✅  No revenge trading detected (< 15 min re-entry after loss)")
    else:
        icon = '🔴' if rt['revenge_pct'] > 0.10 else '⚠️'
        print(f"  {icon} Revenge trades: {rt['revenge_count']} / {n} ({rt['revenge_pct']:.1%})")
        print(f"     Revenge win rate:   {rt['revenge_win_rate']:.1%}  vs  Baseline: {rt['baseline_win_rate']:.1%}")
        perf_hit = rt['performance_hit']
        print(f"     Performance hit:    {perf_hit:+.1%} lower win rate on revenge trades")
        print(f"     PnL from revenge:   {rt['revenge_pnl']:+.2f} USDT")

        if args.verbose and rt['revenge_trades']:
            print(f"\n     Details:")
            for t in rt['revenge_trades'][:5]:
                icon_t = '✅' if t['win'] else '❌'
                print(f"       {icon_t} {t['time'].strftime('%m/%d %H:%M')} {t['symbol']} {t['pnl']:+.2f} USDT  ({t['time_after_loss_min']:.0f}min after loss)")

    # ─── Tilt Detection ────────────────────────────────────
    tilt = detect_tilt(trades, rolling_window=10, size_spike_threshold=1.25)
    print(f"\n{'─'*70}")
    print("  📈  TILT DETECTION (Position Size Spikes)")
    print(f"{'─'*70}")
    if tilt['tilt_count'] == 0:
        print("  ✅  No tilt detected (no abnormal size spikes after losses)")
    else:
        icon = '🔴' if tilt['tilt_count'] > 5 else '⚠️'
        print(f"  {icon} Tilt instances: {tilt['tilt_count']}  (avg spike: {tilt['avg_size_spike']:.1f}x normal size)")
        print(f"     Tilt win rate:   {tilt['tilt_win_rate']:.1%}")
        print(f"     PnL from tilt:   {tilt['tilt_pnl']:+.2f} USDT")

    # ─── Streak Analysis ───────────────────────────────────
    streaks = streak_analysis(trades)
    print(f"\n{'─'*70}")
    print("  🔁  STREAK ANALYSIS")
    print(f"{'─'*70}")
    print(f"  Longest win streak:    {streaks['max_win_streak']} consecutive wins")
    print(f"  Longest loss streak:   {streaks['max_loss_streak']} consecutive losses")
    if streaks.get('post_win_streak_win_rate') is not None:
        print(f"  After win streak WR:   {streaks['post_win_streak_win_rate']:.1%}  {'⚠️ Overconfidence?' if streaks['post_win_streak_win_rate'] < overall_wr - 0.10 else '✅'}")
    if streaks.get('post_loss_streak_win_rate') is not None:
        print(f"  After loss streak WR:  {streaks['post_loss_streak_win_rate']:.1%}  {'✅ Good recovery' if streaks['post_loss_streak_win_rate'] > overall_wr else '🔴 Still struggling'}")

    # ─── Time of Day ────────────────────────────────────────
    tod = time_of_day_analysis(trades)
    print(f"\n{'─'*70}")
    print("  🕐  TIME OF DAY PERFORMANCE")
    print(f"{'─'*70}")
    for h_data in sorted(tod['by_hour'], key=lambda x: x['hour']):
        h = h_data['hour']
        n_h = h_data['n']
        wr = h_data['win_rate']
        pnl = h_data['pnl']
        print(f"  {wr_color(wr)} {h:02d}:00  {bar(wr)} {wr:>5.0%}  ({n_h:>2} trades)  {pnl:>+8.2f} USDT")

    if tod['best_hours']:
        best = sorted(tod['best_hours'], key=lambda x: x['win_rate'], reverse=True)
        print(f"\n  ✅ Best hours: {', '.join(f\"{h['hour']:02d}:00\" for h in best)}")
    if tod['worst_hours']:
        worst = sorted(tod['worst_hours'], key=lambda x: x['win_rate'])
        print(f"  🔴 Avoid:     {', '.join(f\"{h['hour']:02d}:00\" for h in worst)}")

    # ─── Day of Week ────────────────────────────────────────
    dow = day_of_week_analysis(trades)
    print(f"\n{'─'*70}")
    print("  📅  DAY OF WEEK PERFORMANCE")
    print(f"{'─'*70}")
    for d in dow:
        print(f"  {wr_color(d['win_rate'])} {d['day']:<12}  {bar(d['win_rate'])} {d['win_rate']:>5.0%}  ({d['n']:>2} trades)  {d['pnl']:>+8.2f} USDT")

    # ─── Overtrading ────────────────────────────────────────
    ot = overtrading_check(trades, max_trades_per_session=5)
    print(f"\n{'─'*70}")
    print("  🔥  OVERTRADING CHECK")
    print(f"{'─'*70}")
    print(f"  Avg trades per day:    {ot['avg_trades_per_day']:.1f}")
    if ot['overtraded_days'] == 0:
        print("  ✅  No overtrading detected (≤ 5 trades/day)")
    else:
        print(f"  ⚠️  Overtraded sessions: {ot['overtraded_days']}")
        for day_info in ot['overtraded_details'][:3]:
            wr1 = f"{day_info['win_rate_first_5']:.0%}" if day_info['win_rate_first_5'] is not None else 'N/A'
            wr2 = f"{day_info['win_rate_after_5']:.0%}" if day_info['win_rate_after_5'] is not None else 'N/A'
            print(f"     {day_info['date']}: {day_info['n_trades']} trades  |  First 5: {wr1}  |  After 5: {wr2}")

    # ─── Symbol Analysis ────────────────────────────────────
    syms = symbol_analysis(trades)
    print(f"\n{'─'*70}")
    print("  💰  PERFORMANCE BY SYMBOL")
    print(f"{'─'*70}")
    print(f"  {'Symbol':<15} {'Trades':>6} {'Win%':>7} {'PnL':>12}")
    print(f"  {'─'*45}")
    for s in syms:
        icon = wr_color(s['win_rate'])
        print(f"  {icon} {s['symbol']:<13} {s['n']:>6} {s['win_rate']:>7.1%} {s['pnl']:>+12.2f} USDT")

    # ─── Action Summary ──────────────────────────────────────
    print(f"\n{'─'*70}")
    print("  🎯  ACTION ITEMS")
    print(f"{'─'*70}")
    actions = []

    if rt['revenge_count'] > 0 and rt['revenge_pct'] > 0.05:
        actions.append(f"🔴 Revenge trading: Implement mandatory 1-hour cooldown after any loss")

    if tilt['tilt_count'] > 3:
        actions.append(f"🔴 Tilt detected: Create position sizing rule — max size = recent 10-trade average")

    if streaks.get('max_loss_streak', 0) >= 4:
        actions.append(f"⚠️  Max {streaks['max_loss_streak']} consecutive losses — create circuit breaker rule at 3 losses")

    if tod['worst_hours']:
        worst_h = sorted(tod['worst_hours'], key=lambda x: x['win_rate'])[0]
        actions.append(f"⚠️  Avoid trading at {worst_h['hour']:02d}:00 — {worst_h['win_rate']:.0%} win rate ({worst_h['n']} trades)")

    losing_syms = [s for s in syms if s['pnl'] < 0 and s['n'] >= 5]
    if losing_syms:
        names = ', '.join(s['symbol'] for s in losing_syms[:3])
        actions.append(f"🔴 Losing symbols: {names} — review or remove from watchlist")

    if ot['overtraded_days'] > 0:
        actions.append(f"⚠️  Overtrading: Cap at 5 trades per day. Quality > quantity.")

    if not actions:
        print("  ✅  No major behavioral issues detected. Keep up the discipline!")
    else:
        for action in actions:
            print(f"  {action}")

    print(f"\n{'='*70}\n")


if __name__ == '__main__':
    main()
