#!/usr/bin/env python3
"""
Advanced Trading Performance Metrics
Institutional-grade analytics: Sharpe, Sortino, Calmar, SQN, Drawdown,
VaR/CVaR, K-Ratio, Ulcer Index, R-multiples, Monte Carlo simulation.

Usage:
    python3 advanced_metrics.py --days 30
    python3 advanced_metrics.py --days 90 --monte-carlo
    python3 advanced_metrics.py --equity-curve
"""

import os
import sys
import argparse
import hmac
import hashlib
import time
import urllib.parse
import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import requests

try:
    from dotenv import load_dotenv

    load_dotenv(Path.home() / ".binance_config")
except ImportError:
    # Fall back to manual parsing
    config = Path.home() / ".binance_config"
    if config.exists():
        for line in config.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
BASE_URL = "https://fapi.binance.com"


# ─────────────────────────────────────────────────────────
# API Client
# ─────────────────────────────────────────────────────────


def sign(params: dict) -> dict:
    params["timestamp"] = int(time.time() * 1000)
    query = urllib.parse.urlencode(sorted(params.items()))
    params["signature"] = hmac.new(
        API_SECRET.encode(), query.encode(), hashlib.sha256
    ).hexdigest()
    return params


def api(endpoint: str, params: dict = None) -> dict | list:
    if not API_KEY or not API_SECRET:
        print(
            "ERROR: BINANCE_API_KEY / BINANCE_API_SECRET not set in ~/.binance_config"
        )
        sys.exit(1)
    params = sign(params or {})
    r = requests.get(
        f"{BASE_URL}{endpoint}",
        headers={"X-MBX-APIKEY": API_KEY},
        params=params,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def fetch_income_history(days: int) -> list:
    """Fetch income history (REALIZED_PNL + FUNDING_FEE + COMMISSION)."""
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - days * 24 * 3600 * 1000
    all_income = []
    cursor = start_ms

    while cursor < end_ms:
        batch = api(
            "/fapi/v1/income", {"startTime": cursor, "endTime": end_ms, "limit": 1000}
        )
        if not batch:
            break
        all_income.extend(batch)
        if len(batch) < 1000:
            break
        cursor = int(batch[-1]["time"]) + 1

    return all_income


def build_trade_pnl(income_records: list) -> list:
    """
    Aggregate income records into trade-level PnL.
    Groups consecutive REALIZED_PNL records by symbol.
    """
    trades = []
    pnl_records = [r for r in income_records if r["incomeType"] == "REALIZED_PNL"]
    pnl_records.sort(key=lambda x: x["time"])

    # Simple grouping: each non-zero PnL record = one trade result
    for r in pnl_records:
        pnl = float(r["income"])
        if pnl != 0:
            trades.append(
                {
                    "symbol": r["symbol"],
                    "pnl": pnl,
                    "time": datetime.fromtimestamp(r["time"] / 1000),
                    "win": pnl > 0,
                }
            )
    return trades


# ─────────────────────────────────────────────────────────
# Performance Metrics
# ─────────────────────────────────────────────────────────


def sharpe_ratio(
    returns: np.ndarray, risk_free: float = 0.0, periods: int = 252
) -> float:
    """Annualized Sharpe Ratio."""
    if len(returns) < 2:
        return 0.0
    excess = returns - risk_free / periods
    std = np.std(excess, ddof=1)
    if std == 0:
        return 0.0
    return float(np.mean(excess) / std * np.sqrt(periods))


def sortino_ratio(
    returns: np.ndarray, risk_free: float = 0.0, periods: int = 252
) -> float:
    """Annualized Sortino Ratio (penalizes only downside volatility)."""
    if len(returns) < 2:
        return 0.0
    excess = returns - risk_free / periods
    downside = excess[excess < 0]
    if len(downside) == 0:
        return float("inf")
    downside_std = np.std(downside, ddof=1)
    if downside_std == 0:
        return 0.0
    return float(np.mean(excess) / downside_std * np.sqrt(periods))


def calmar_ratio(total_return: float, max_drawdown: float) -> float:
    """Calmar = Total Return / |Max Drawdown|."""
    if max_drawdown == 0:
        return 0.0
    return float(total_return / abs(max_drawdown))


def sqn(r_multiples: np.ndarray) -> float:
    """
    System Quality Number (Van Tharp).
    SQN = √N × Mean(R) / Std(R)
    Requires ≥ 30 trades for statistical significance.
    """
    if len(r_multiples) < 10:
        return float("nan")
    n = len(r_multiples)
    mean_r = np.mean(r_multiples)
    std_r = np.std(r_multiples, ddof=1)
    if std_r == 0:
        return float("nan")
    return float(np.sqrt(n) * mean_r / std_r)


def profit_factor(pnl_list: list) -> float:
    """Gross Profit / |Gross Loss|."""
    gross_win = sum(p for p in pnl_list if p > 0)
    gross_loss = abs(sum(p for p in pnl_list if p < 0))
    return gross_win / gross_loss if gross_loss > 0 else float("inf")


def expectancy(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Expected value per trade in currency units."""
    return (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))


def expectancy_r(r_multiples: np.ndarray) -> float:
    """Expectancy in R-multiples."""
    return float(np.mean(r_multiples)) if len(r_multiples) > 0 else 0.0


def max_drawdown(equity_curve: np.ndarray) -> tuple[float, int]:
    """
    Returns: (max_drawdown_pct as negative float, max_drawdown_duration_days)
    """
    if len(equity_curve) < 2:
        return 0.0, 0
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - peak) / peak
    max_dd = float(drawdown.min())

    # Duration
    max_duration = 0
    current_duration = 0
    for dd in drawdown:
        if dd < 0:
            current_duration += 1
            max_duration = max(max_duration, current_duration)
        else:
            current_duration = 0

    return max_dd, max_duration


def value_at_risk(returns: np.ndarray, confidence: float = 0.99) -> float:
    """Historical VaR at given confidence level. Returns negative float."""
    if len(returns) < 10:
        return float("nan")
    return float(np.percentile(returns, (1 - confidence) * 100))


def conditional_var(returns: np.ndarray, confidence: float = 0.99) -> float:
    """CVaR (Expected Shortfall) — mean of losses beyond VaR. Returns negative float."""
    if len(returns) < 10:
        return float("nan")
    var = value_at_risk(returns, confidence)
    tail = returns[returns <= var]
    return float(np.mean(tail)) if len(tail) > 0 else float("nan")


def ulcer_index(equity_curve: np.ndarray) -> float:
    """Ulcer Index = RMS of drawdown percentages. Lower is better."""
    if len(equity_curve) < 2:
        return 0.0
    peak = np.maximum.accumulate(equity_curve)
    drawdown_pct = (equity_curve - peak) / peak * 100
    return float(np.sqrt(np.mean(drawdown_pct**2)))


def k_ratio(equity_curve: np.ndarray) -> float:
    """
    K-Ratio = Slope / SE(Slope) from linear regression on log equity curve.
    Measures equity curve linearity (smoothness over time).
    """
    if len(equity_curve) < 3:
        return 0.0
    log_equity = np.log(equity_curve / equity_curve[0] + 1)
    x = np.arange(len(log_equity))
    n = len(x)
    slope = (n * np.sum(x * log_equity) - np.sum(x) * np.sum(log_equity)) / (
        n * np.sum(x**2) - np.sum(x) ** 2
    )
    y_hat = slope * x + (np.sum(log_equity) - slope * np.sum(x)) / n
    se = np.sqrt(
        np.sum((log_equity - y_hat) ** 2) / (n - 2) / np.sum((x - np.mean(x)) ** 2)
    )
    return float(slope / se) if se > 0 else 0.0


def recovery_factor(total_return: float, max_dd: float) -> float:
    """How much return per unit of max drawdown."""
    return float(total_return / abs(max_dd)) if max_dd != 0 else 0.0


# ─────────────────────────────────────────────────────────
# Monte Carlo Simulation
# ─────────────────────────────────────────────────────────


def monte_carlo(
    trade_pnl: list,
    starting_equity: float,
    n_sims: int = 1000,
    bust_threshold: float = -0.30,
    goal_threshold: float = 0.25,
) -> dict:
    """
    Monte Carlo simulation: shuffle trade sequence N times.
    Measures robustness of results to sequence randomness.

    bust_threshold: -0.30 = 30% drawdown = "bust" scenario
    goal_threshold:  0.25 = 25% return = "goal" scenario
    """
    import random

    final_returns = []
    max_drawdowns = []
    bust_count = 0
    goal_count = 0

    for _ in range(n_sims):
        shuffled = random.sample(trade_pnl, len(trade_pnl))
        equity = starting_equity
        peak = equity
        max_dd_sim = 0.0

        for pnl in shuffled:
            equity += pnl
            if equity > peak:
                peak = equity
            dd = (equity - peak) / peak
            if dd < max_dd_sim:
                max_dd_sim = dd

        final_ret = (equity - starting_equity) / starting_equity
        final_returns.append(final_ret)
        max_drawdowns.append(max_dd_sim)

        if max_dd_sim <= bust_threshold:
            bust_count += 1
        if final_ret >= goal_threshold:
            goal_count += 1

    final_returns = np.array(final_returns)
    max_drawdowns = np.array(max_drawdowns)

    return {
        "n_simulations": n_sims,
        "mean_return": float(np.mean(final_returns)),
        "p5_return": float(np.percentile(final_returns, 5)),
        "p50_return": float(np.percentile(final_returns, 50)),
        "p95_return": float(np.percentile(final_returns, 95)),
        "p5_max_drawdown": float(np.percentile(max_drawdowns, 5)),
        "median_max_drawdown": float(np.percentile(max_drawdowns, 50)),
        "p95_max_drawdown": float(np.percentile(max_drawdowns, 95)),
        "bust_probability": bust_count / n_sims,
        "goal_probability": goal_count / n_sims,
        "bust_threshold": bust_threshold,
        "goal_threshold": goal_threshold,
    }


# ─────────────────────────────────────────────────────────
# Display
# ─────────────────────────────────────────────────────────


def color(value: float, good_positive: bool = True) -> str:
    """Color coding: 🟢 = good, 🔴 = bad, 🟡 = neutral."""
    if good_positive:
        if value > 0:
            return f"🟢 {value:+.4f}"
        elif value < 0:
            return f"🔴 {value:+.4f}"
        return f"🟡 {value:.4f}"
    else:  # lower is better (e.g., drawdown)
        if value < 0:
            return f"🟢 {value:.4f}"
        return f"🔴 +{value:.4f}"


def sqn_label(sqn_val: float) -> str:
    if np.isnan(sqn_val):
        return "N/A (need 30+ trades)"
    if sqn_val >= 5.1:
        return f"{sqn_val:.2f} (Superb) 🚀"
    if sqn_val >= 3.0:
        return f"{sqn_val:.2f} (Excellent) ✅"
    if sqn_val >= 2.5:
        return f"{sqn_val:.2f} (Good) 🟢"
    if sqn_val >= 2.0:
        return f"{sqn_val:.2f} (Average) 🟡"
    if sqn_val >= 1.6:
        return f"{sqn_val:.2f} (Below Average) ⚠️"
    return f"{sqn_val:.2f} (Poor — review strategy) 🔴"


# ─────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Advanced trading metrics analyzer")
    parser.add_argument(
        "--days", type=int, default=30, help="Days of history to analyze"
    )
    parser.add_argument(
        "--monte-carlo", action="store_true", help="Run Monte Carlo simulation"
    )
    parser.add_argument(
        "--equity-curve", action="store_true", help="Show equity curve analysis"
    )
    parser.add_argument(
        "--sims", type=int, default=1000, help="Monte Carlo simulations (default: 1000)"
    )
    args = parser.parse_args()

    print(f"\n{'=' * 70}")
    print(f"  📊 ADVANCED TRADING METRICS  ({args.days}-day period)")
    print(f"{'=' * 70}")

    # Fetch data
    print(f"\nFetching {args.days} days of income history...")
    income = fetch_income_history(args.days)

    if not income:
        print("No income records found in this period.")
        sys.exit(0)

    # Separate by type
    trades_pnl_records = [
        float(r["income"])
        for r in income
        if r["incomeType"] == "REALIZED_PNL" and float(r["income"]) != 0
    ]
    funding_total = sum(
        float(r["income"]) for r in income if r["incomeType"] == "FUNDING_FEE"
    )
    commission_total = sum(
        float(r["income"]) for r in income if r["incomeType"] == "COMMISSION"
    )

    trades = build_trade_pnl(income)

    if not trades:
        print("No completed trades found.")
        sys.exit(0)

    # Get account balance for equity calculations
    try:
        account = api("/fapi/v3/account", {})
        starting_equity = float(account["totalWalletBalance"]) - sum(
            t["pnl"] for t in trades
        )
        current_equity = float(account["totalWalletBalance"])
    except Exception:
        current_equity = 10000
        starting_equity = current_equity - sum(t["pnl"] for t in trades)

    # Build arrays
    pnl_list = [t["pnl"] for t in trades]
    n_trades = len(pnl_list)
    wins = [p for p in pnl_list if p > 0]
    losses = [p for p in pnl_list if p < 0]
    win_rate = len(wins) / n_trades if n_trades > 0 else 0

    # Equity curve
    equity_curve = np.array(
        [starting_equity + sum(pnl_list[: i + 1]) for i in range(n_trades)]
    )
    if len(equity_curve) == 0:
        equity_curve = np.array([starting_equity])

    # Returns (normalized daily — approximation from trade P&L)
    returns = np.array(
        [p / equity_curve[max(0, i - 1)] for i, p in enumerate(pnl_list)]
    )

    # R-multiples (estimated — assumes 1R = avg loss)
    avg_loss_abs = abs(np.mean(losses)) if losses else 1.0
    r_multiples = np.array([p / avg_loss_abs for p in pnl_list])

    # ─── Core Metrics ───────────────────────────────────────
    total_pnl = sum(pnl_list)
    total_return = (
        (current_equity - starting_equity) / starting_equity
        if starting_equity != 0
        else 0
    )
    max_dd, max_dd_days = max_drawdown(equity_curve)
    sharpe = sharpe_ratio(returns)
    sortino = sortino_ratio(returns)
    calmar = calmar_ratio(total_return, max_dd)
    sqn_score = sqn(r_multiples)
    pf = profit_factor(pnl_list)
    exp_r = expectancy_r(r_multiples)
    exp_usd = expectancy(
        win_rate, np.mean(wins) if wins else 0, np.mean(losses) if losses else 0
    )
    rf = recovery_factor(total_return, max_dd)
    ulcer = ulcer_index(equity_curve)
    k = k_ratio(equity_curve)
    var_99 = value_at_risk(returns, 0.99)
    cvar_99 = conditional_var(returns, 0.99)

    # ─── Display ─────────────────────────────────────────────
    print(f"\n{'─' * 70}")
    print("  💰  PnL SUMMARY")
    print(f"{'─' * 70}")
    print(
        f"  Realized PnL:          {total_pnl:>+12.2f} USDT  {'🟢' if total_pnl > 0 else '🔴'}"
    )
    print(f"  Funding Fees:          {funding_total:>+12.2f} USDT")
    print(f"  Commission:            {commission_total:>+12.2f} USDT")
    net = total_pnl + funding_total + commission_total
    print(f"  Net (all costs):       {net:>+12.2f} USDT  {'🟢' if net > 0 else '🔴'}")
    print(f"  Total Return:          {total_return:>+12.1%}")
    print(f"  Trades Analyzed:       {n_trades:>12}")

    print(f"\n{'─' * 70}")
    print("  🎯  WIN / LOSS STATISTICS")
    print(f"{'─' * 70}")
    print(f"  Win Rate:              {win_rate:>12.1%}  ({len(wins)}/{n_trades})")
    print(f"  Avg Win:               {np.mean(wins) if wins else 0:>+12.2f} USDT")
    print(f"  Avg Loss:              {np.mean(losses) if losses else 0:>+12.2f} USDT")
    print(f"  Largest Win:           {max(wins) if wins else 0:>+12.2f} USDT")
    print(f"  Largest Loss:          {min(losses) if losses else 0:>+12.2f} USDT")
    print(
        f"  Profit Factor:         {pf:>12.2f}  {'✅' if pf > 1.5 else '⚠️' if pf > 1.0 else '🔴'}"
    )
    print(
        f"  Expectancy (R):        {exp_r:>+12.4f}R  {'✅' if exp_r > 0.2 else '⚠️' if exp_r > 0 else '🔴'}"
    )
    print(f"  Expectancy (USD):      {exp_usd:>+12.2f} USDT")

    print(f"\n{'─' * 70}")
    print("  📈  RISK-ADJUSTED RETURNS")
    print(f"{'─' * 70}")
    print(
        f"  Sharpe Ratio:          {sharpe:>12.2f}  {'✅' if sharpe > 1.0 else '⚠️' if sharpe > 0.5 else '🔴'}"
    )
    print(
        f"  Sortino Ratio:         {sortino:>12.2f}  {'✅' if sortino > 1.5 else '⚠️' if sortino > 0.8 else '🔴'}"
    )
    print(
        f"  Calmar Ratio:          {calmar:>12.2f}  {'✅' if calmar > 1.0 else '⚠️' if calmar > 0.5 else '🔴'}"
    )
    print(f"  SQN:                   {sqn_label(sqn_score)}")
    print(f"  Recovery Factor:       {rf:>12.2f}x")
    print(
        f"  Ulcer Index:           {ulcer:>12.2f}%  {'✅' if ulcer < 5 else '⚠️' if ulcer < 15 else '🔴'}"
    )
    print(
        f"  K-Ratio (linearity):   {k:>12.4f}  {'✅' if k > 0.5 else '⚠️' if k > 0.2 else '🔴'}"
    )

    print(f"\n{'─' * 70}")
    print("  📉  DRAWDOWN ANALYSIS")
    print(f"{'─' * 70}")
    print(
        f"  Max Drawdown:          {max_dd:>+12.1%}  {'✅' if max_dd > -0.10 else '⚠️' if max_dd > -0.20 else '🔴'}"
    )
    print(f"  Max DD Duration:       {max_dd_days:>10} trades underwater")

    print(f"\n{'─' * 70}")
    print("  ⚠️   RISK METRICS")
    print(f"{'─' * 70}")
    print(f"  VaR 99% (worst 1%):    {var_99:>+12.4%} of equity per trade")
    print(f"  CVaR 99% (tail avg):   {cvar_99:>+12.4%} of equity per trade")

    # R-multiple distribution
    print(f"\n{'─' * 70}")
    print("  🎲  R-MULTIPLE DISTRIBUTION")
    print(f"{'─' * 70}")
    print(f"  Mean R:                {np.mean(r_multiples):>+12.2f}R")
    print(f"  Median R:              {np.median(r_multiples):>+12.2f}R")
    print(f"  Std Dev R:             {np.std(r_multiples):>12.2f}R")
    print(f"  % Trades > 1R:         {(r_multiples > 1).mean():>12.1%}")
    print(f"  % Trades > 2R:         {(r_multiples > 2).mean():>12.1%}")
    print(f"  % Trades > 3R:         {(r_multiples > 3).mean():>12.1%}")
    print(f"  Best R:                {r_multiples.max():>+12.2f}R")
    print(f"  Worst R:               {r_multiples.min():>+12.2f}R")

    # Equity curve analysis
    if args.equity_curve:
        print(f"\n{'─' * 70}")
        print("  📊  EQUITY CURVE ANALYSIS")
        print(f"{'─' * 70}")
        print(f"  Starting Equity:       {starting_equity:>12,.2f} USDT")
        print(f"  Current Equity:        {current_equity:>12,.2f} USDT")
        print(f"  Peak Equity:           {equity_curve.max():>12,.2f} USDT")
        print(f"  K-Ratio (smoothness):  {k:>12.4f}")
        print(f"  Ulcer Index (pain):    {ulcer:>12.2f}%")
        # Rolling Sharpe
        window = min(20, len(returns) // 2)
        if window >= 5:
            rolling = [
                sharpe_ratio(returns[max(0, i - window) : i])
                for i in range(window, len(returns) + 1)
            ]
            print(f"  Rolling Sharpe (last): {rolling[-1] if rolling else 0:>12.2f}")
            print(f"  Rolling Sharpe (peak): {max(rolling) if rolling else 0:>12.2f}")

    # Monte Carlo
    if args.monte_carlo:
        print(f"\n{'─' * 70}")
        print(f"  🎲  MONTE CARLO SIMULATION ({args.sims:,} paths)")
        print(f"{'─' * 70}")
        print("  Running simulations...", end="\r")
        mc = monte_carlo(pnl_list, starting_equity, n_sims=args.sims)
        print(f"  {'─' * 65}")
        print(f"  Return Distribution:")
        print(f"    5th percentile:    {mc['p5_return']:>+12.1%}")
        print(f"    Median:            {mc['p50_return']:>+12.1%}")
        print(f"    95th percentile:   {mc['p95_return']:>+12.1%}")
        print(f"\n  Max Drawdown Distribution:")
        print(f"    5th percentile:    {mc['p5_max_drawdown']:>+12.1%}")
        print(f"    Median:            {mc['median_max_drawdown']:>+12.1%}")
        print(f"    95th percentile:   {mc['p95_max_drawdown']:>+12.1%}")
        print(f"\n  Probability Analysis:")
        bust = mc["bust_probability"]
        goal = mc["goal_probability"]
        print(
            f"    Bust probability ({mc['bust_threshold']:.0%} DD):  {bust:>8.1%}  {'✅' if bust < 0.05 else '⚠️' if bust < 0.15 else '🔴'}"
        )
        print(
            f"    Goal probability ({mc['goal_threshold']:+.0%} ret): {goal:>8.1%}  {'✅' if goal > 0.4 else '⚠️' if goal > 0.2 else '🔴'}"
        )

        if bust > 0.15:
            print(f"\n  ⚠️  HIGH BUST PROBABILITY. Consider reducing position sizes.")
            target_reduction = 0.05 / max(bust, 0.01)
            print(
                f"      Estimated size reduction needed: {(1 - target_reduction):.0%}"
            )

    print(f"\n{'=' * 70}\n")


if __name__ == "__main__":
    main()
