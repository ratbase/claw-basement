#!/usr/bin/env python3
"""
bf.py — Binance Futures CLI
Unified data tool. Pure stdlib — no pip installs needed.

Usage:
  ./bf.py account                              Account summary (v3)
  ./bf.py balance                              Quick wallet balance
  ./bf.py positions                            Open positions (v3)
  ./bf.py income [--days N] [--symbol SYM]    Income + PnL history (paginated)
  ./bf.py trades [--symbol SYM] [--days N]    User trade history
  ./bf.py rr ENTRY STOP [OPTIONS]             Risk:Reward calculator (no API)
  ./bf.py klines [SYMBOL] [--interval 4h] [--limit N]  Regime check — ADX, EMA, structure (no API)

Credentials (in priority order):
  1. BINANCE_API_KEY / BINANCE_API_SECRET env vars
  2. ~/.binance_config  (KEY=VALUE format)
  3. ~/.config/binance/credentials
"""

import os
import sys
import time
import hmac
import hashlib
import json
import argparse
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import HTTPError
from datetime import datetime, timezone
from collections import defaultdict

API_BASE = "https://fapi.binance.com"

# ── ANSI ─────────────────────────────────────────────────────────────────────
RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
RED   = "\033[91m"
GREEN = "\033[92m"
YEL   = "\033[93m"
CYAN  = "\033[96m"


# ── Credentials ───────────────────────────────────────────────────────────────
def load_creds() -> tuple:
    """Load API credentials from env vars or config file."""
    key    = os.environ.get("BINANCE_API_KEY", "")
    secret = os.environ.get("BINANCE_API_SECRET", "")

    if not key or not secret:
        paths = [
            os.path.expanduser("~/.binance_config"),
            os.path.expanduser("~/.config/binance/credentials"),
        ]
        for path in paths:
            if not os.path.exists(path):
                continue
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    v = v.strip().strip('"').strip("'")
                    if k.strip() == "BINANCE_API_KEY":
                        key = v
                    elif k.strip() == "BINANCE_API_SECRET":
                        secret = v
            if key and secret:
                break

    if not key or not secret:
        print("❌  Credentials not found.\n")
        print("    Option 1 — env vars:")
        print("      export BINANCE_API_KEY=xxx")
        print("      export BINANCE_API_SECRET=yyy\n")
        print("    Option 2 — ~/.binance_config:")
        print("      BINANCE_API_KEY=xxx")
        print("      BINANCE_API_SECRET=yyy")
        sys.exit(1)

    return key, secret


# ── HTTP / Signing ────────────────────────────────────────────────────────────
def _sign(params: dict, secret: str) -> str:
    qs = urlencode(params)
    return hmac.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()


def api_get(endpoint: str, params: dict, key: str, secret: str):
    p = dict(params)
    p["timestamp"] = int(time.time() * 1000)
    p["signature"] = _sign(p, secret)
    url = f"{API_BASE}{endpoint}?{urlencode(p)}"
    req = Request(url, headers={"X-MBX-APIKEY": key})
    try:
        with urlopen(req, timeout=15) as r:
            data = json.load(r)
    except HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code}: {body[:400]}")
        sys.exit(1)
    if isinstance(data, dict) and "code" in data:
        print(f"API error {data['code']}: {data.get('msg', '?')}")
        sys.exit(1)
    return data


# ── Public API (no auth) ─────────────────────────────────────────────────────
def public_get(endpoint: str, params: dict):
    """Public API call — no authentication required."""
    url = f"{API_BASE}{endpoint}?{urlencode(params)}"
    req = Request(url)
    try:
        with urlopen(req, timeout=15) as r:
            data = json.load(r)
    except HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code}: {body[:400]}")
        sys.exit(1)
    return data


# ── Formatting helpers ────────────────────────────────────────────────────────
def sep(width=72, ch="═"):
    print(ch * width)


def ts_to_date(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def pnl_dot(v: float) -> str:
    return "🟢" if v >= 0 else "🔴"


def colored(v: float, text: str) -> str:
    c = GREEN if v >= 0 else RED
    return f"{c}{text}{RESET}"


def bar_chart(values: dict, width: int = 20) -> dict:
    """Return ASCII bar strings scaled to max abs value."""
    if not values:
        return {}
    max_abs = max(abs(v) for v in values.values()) or 1
    result = {}
    for k, v in values.items():
        n = int(abs(v) / max_abs * width)
        c = GREEN if v >= 0 else RED
        result[k] = f"{c}{'█' * n}{RESET}"
    return result


# ── account ───────────────────────────────────────────────────────────────────
def cmd_account(key: str, secret: str, raw: bool = False):
    data = api_get("/fapi/v3/account", {}, key, secret)
    if raw:
        print(json.dumps(data, indent=2))
        return

    wb   = float(data["totalWalletBalance"])
    mb   = float(data["totalMarginBalance"])
    ab   = float(data["availableBalance"])
    upnl = float(data["totalUnrealizedProfit"])
    tim  = float(data["totalInitialMargin"])
    tmm  = float(data["totalMaintMargin"])
    mw   = float(data["maxWithdrawAmount"])

    sep()
    print(f"{BOLD}{'BINANCE FUTURES — ACCOUNT SUMMARY':^72}{RESET}")
    sep()

    print(f"\n{YEL}💰 Balances{RESET}")
    print(f"  Wallet Balance:      {BOLD}{wb:>13,.2f} USDT{RESET}")
    print(f"  Margin Balance:            {mb:>13,.2f} USDT")
    print(f"  Available Balance:   {BOLD}{ab:>13,.2f} USDT{RESET}")
    print(f"  Max Withdrawable:          {mw:>13,.2f} USDT")

    print(f"\n{YEL}📈 Unrealized PnL{RESET}")
    print(f"  Total:             {colored(upnl, f'{upnl:>+13,.2f} USDT')}  {pnl_dot(upnl)}")

    margin_usage = (tim / mb * 100) if mb > 0 else 0
    print(f"\n{YEL}💳 Margin{RESET}")
    print(f"  Initial Margin:          {tim:>13,.2f} USDT")
    print(f"  Maint Margin:            {tmm:>13,.2f} USDT")
    print(f"  Margin Usage:            {margin_usage:>13.1f}%")

    print(f"\n{YEL}⚙️  Settings{RESET}")
    print(f"  Fee Tier:          {data.get('feeTier', '—'):>16}")
    print(f"  Can Trade:         {str(data['canTrade']):>16}")
    print(f"  Can Deposit:       {str(data['canDeposit']):>16}")
    sep()


# ── balance ───────────────────────────────────────────────────────────────────
def cmd_balance(key: str, secret: str):
    data = api_get("/fapi/v3/balance", {}, key, secret)
    usdt = next((b for b in data if b["asset"] == "USDT"), None)
    if usdt:
        wb   = float(usdt["balance"])
        ab   = float(usdt["availableBalance"])
        upnl = float(usdt.get("crossUnPnl", 0))
        print(
            f"  Balance: {BOLD}{wb:,.2f} USDT{RESET}"
            f"  |  Available: {ab:,.2f}"
            f"  |  uPnL: {colored(upnl, f'{upnl:+,.2f}')}"
        )
    else:
        for b in data:
            if float(b["balance"]) > 0:
                print(f"  {b['asset']}: {float(b['balance']):,.6f}")


# ── positions ─────────────────────────────────────────────────────────────────
def cmd_positions(key: str, secret: str, raw: bool = False):
    data = api_get("/fapi/v3/positionRisk", {}, key, secret)
    if raw:
        print(json.dumps(data, indent=2))
        return

    open_pos = [p for p in data if float(p["positionAmt"]) != 0]

    sep()
    print(f"{BOLD}{'BINANCE FUTURES — OPEN POSITIONS':^72}{RESET}")
    sep()

    if not open_pos:
        print(f"\n  {DIM}No open positions.{RESET}\n")
        sep()
        return

    # Header
    print(
        f"\n  {'Symbol':<13} {'Side':<6} {'Size':>10} "
        f"{'Entry':>12} {'Mark':>12} {'Liq':>12} {'uPnL':>11}  {'Lev'}"
    )
    print("  " + "─" * 84)

    total_upnl = 0.0
    for p in sorted(open_pos, key=lambda x: abs(float(x["unRealizedProfit"])), reverse=True):
        amt   = float(p["positionAmt"])
        upnl  = float(p["unRealizedProfit"])
        entry = float(p["entryPrice"])
        mark  = float(p["markPrice"])
        liq   = float(p.get("liquidationPrice", 0))
        lev   = p.get("leverage", "?")
        total_upnl += upnl

        side_str = f"{GREEN}LONG{RESET}" if amt > 0 else f"{RED}SHORT{RESET}"
        liq_str  = f"{liq:,.4f}" if liq > 0 else "—"
        upnl_str = colored(upnl, f"{upnl:>+10,.2f}")

        # Side has ANSI codes — compensate padding manually
        print(
            f"  {p['symbol']:<13} {side_str}{'':>6} {abs(amt):>10.4f} "
            f"{entry:>12,.4f} {mark:>12,.4f} {liq_str:>12}  {upnl_str}  {lev}x"
        )

    print("  " + "─" * 84)
    print(f"  {'Total uPnL':>58}  {colored(total_upnl, f'{total_upnl:>+10,.2f}')}  ")
    sep()


# ── income ────────────────────────────────────────────────────────────────────
def cmd_income(
    key: str, secret: str,
    days: int = 90,
    symbol: str = None,
    income_type: str = None,
    raw: bool = False,
):
    end_ts   = int(time.time() * 1000)
    start_ts = end_ts - days * 86_400_000

    # Paginated fetch
    all_records = []
    cur_start   = start_ts
    print(
        f"  Fetching income [{ts_to_date(start_ts)} → {ts_to_date(end_ts)}]",
        end="", flush=True
    )
    while cur_start < end_ts:
        params = {"startTime": cur_start, "endTime": end_ts, "limit": 1000}
        if symbol:      params["symbol"]     = symbol
        if income_type: params["incomeType"] = income_type

        batch = api_get("/fapi/v1/income", params, key, secret)
        if not batch:
            break

        all_records.extend(batch)
        print(f" +{len(batch)}", end="", flush=True)

        if len(batch) < 1000:
            break
        cur_start = int(batch[-1]["time"]) + 1

    print(f"  ({len(all_records)} total)\n")

    if raw:
        print(json.dumps(all_records, indent=2))
        return

    if not all_records:
        print("  No income records found.")
        return

    # ── Aggregate ─────────────────────────────────────────────────────────────
    type_totals = defaultdict(float)
    sym_stats   = defaultdict(lambda: {"pnl": 0.0, "funding": 0.0, "commission": 0.0})
    monthly     = defaultdict(float)

    for rec in all_records:
        sym   = rec.get("symbol", "")
        itype = rec["incomeType"]
        amt   = float(rec["income"])
        month = datetime.fromtimestamp(int(rec["time"]) / 1000, tz=timezone.utc).strftime("%Y-%m")

        type_totals[itype]   += amt
        monthly[month]       += amt

        if   itype == "REALIZED_PNL": sym_stats[sym]["pnl"]        += amt
        elif itype == "FUNDING_FEE":  sym_stats[sym]["funding"]     += amt
        elif itype == "COMMISSION":   sym_stats[sym]["commission"]  += amt

    total_pnl  = type_totals.get("REALIZED_PNL", 0.0)
    total_fund = type_totals.get("FUNDING_FEE",  0.0)
    total_comm = type_totals.get("COMMISSION",   0.0)
    net        = total_pnl - total_comm

    # ── Print ─────────────────────────────────────────────────────────────────
    sep()
    print(f"{BOLD}{'INCOME & REALIZED PnL':^72}{RESET}")
    print(f"{DIM}{'Last ' + str(days) + ' days  ·  ' + str(len(all_records)) + ' records':^72}{RESET}")
    sep()

    print(f"\n{YEL}📊 Summary{RESET}")
    print(f"  Realized PnL:    {colored(total_pnl,  f'{total_pnl:>+13,.2f} USDT')}  {pnl_dot(total_pnl)}")
    print(f"  Funding Fees:    {colored(total_fund, f'{total_fund:>+13,.2f} USDT')}  {pnl_dot(total_fund)}")
    print(f"  Commissions:              {total_comm:>+13,.2f} USDT")
    print(f"  {'─' * 38}")
    print(f"  Net (PnL−Comm):  {colored(net, f'{net:>+13,.2f} USDT')}  {pnl_dot(net)}")

    # Monthly bar chart
    if len(monthly) > 1:
        bars = bar_chart(monthly)
        print(f"\n{YEL}📅 Monthly Breakdown{RESET}")
        for mo in sorted(monthly.keys()):
            v = monthly[mo]
            print(f"  {mo}  {colored(v, f'{v:>+10,.2f}'):}  {bars[mo]}")

    # By symbol
    sym_items = sorted(sym_stats.items(), key=lambda x: x[1]["pnl"], reverse=True)
    sym_items = [(s, v) for s, v in sym_items if v["pnl"] != 0 or v["funding"] != 0]

    if sym_items:
        print(f"\n{YEL}📈 By Symbol{RESET}")
        print(
            f"  {'Symbol':<16} {'Realized PnL':>14} {'Funding':>12} "
            f"{'Commission':>12} {'Net':>12}   "
        )
        print("  " + "─" * 68)
        for sym, s in sym_items:
            net_sym     = s["pnl"] - s["commission"]
            pnl_colored = colored(s["pnl"], f"{s['pnl']:>+12,.2f}")
            net_colored = colored(net_sym,  f"{net_sym:>+12,.2f}")
            print(
                f"  {sym:<16} {pnl_colored}  "
                f"{s['funding']:>+12,.2f}  {s['commission']:>+12,.2f}  "
                f"{net_colored}  {pnl_dot(s['pnl'])}"
            )

    # By type
    print(f"\n{YEL}💳 By Income Type{RESET}")
    for itype, amt in sorted(type_totals.items(), key=lambda x: abs(x[1]), reverse=True):
        print(f"  {itype:<28} {colored(amt, f'{amt:>+12,.2f} USDT')}  {pnl_dot(amt)}")

    sep()


# ── trades ────────────────────────────────────────────────────────────────────
def cmd_trades(
    key: str, secret: str,
    symbol: str = None,
    days: int = 30,
    raw: bool = False,
):
    end_ts   = int(time.time() * 1000)
    start_ts = end_ts - days * 86_400_000

    params = {"limit": 1000, "startTime": start_ts, "endTime": end_ts}
    if symbol:
        params["symbol"] = symbol

    print(
        f"  Fetching trades [{ts_to_date(start_ts)} → {ts_to_date(end_ts)}]...",
        end="", flush=True
    )
    data = api_get("/fapi/v1/userTrades", params, key, secret)
    print(f" {len(data)} trades")

    if raw:
        print(json.dumps(data, indent=2))
        return

    if not data:
        print("  No trades found.")
        return

    sym_stats = defaultdict(lambda: {
        "count": 0, "buys": 0, "sells": 0,
        "qty": 0.0, "volume": 0.0, "fees": 0.0,
    })

    for t in data:
        sym    = t["symbol"]
        qty    = float(t["qty"])
        is_buy = t["side"] == "BUY"

        sym_stats[sym]["count"]  += 1
        sym_stats[sym]["qty"]    += qty if is_buy else -qty
        sym_stats[sym]["volume"] += float(t["quoteQty"])
        sym_stats[sym]["fees"]   += float(t["commission"])
        if is_buy:
            sym_stats[sym]["buys"]  += 1
        else:
            sym_stats[sym]["sells"] += 1

    total_fees = sum(s["fees"]   for s in sym_stats.values())
    total_vol  = sum(s["volume"] for s in sym_stats.values())

    sep()
    print(f"{BOLD}{'USER TRADES SUMMARY':^72}{RESET}")
    print(f"{DIM}{'Last ' + str(days) + ' days  ·  ' + str(len(data)) + ' trades':^72}{RESET}")
    sep()

    print(
        f"\n  Trades: {len(data):,}"
        f"   Volume: {total_vol:,.0f} USDT"
        f"   Fees: {total_fees:,.4f} USDT\n"
    )
    print(
        f"  {'Symbol':<16} {'Trades':>7} {'Buys':>6} {'Sells':>6} "
        f"{'Net Qty':>12} {'Volume (USDT)':>14} {'Fees':>10}"
    )
    print("  " + "─" * 75)

    for sym in sorted(sym_stats.keys()):
        s = sym_stats[sym]
        print(
            f"  {sym:<16} {s['count']:>7} {s['buys']:>6} {s['sells']:>6} "
            f"{s['qty']:>+12.4f} {s['volume']:>14,.2f} {s['fees']:>10,.4f}"
        )

    sep()


# ── rr ────────────────────────────────────────────────────────────────────────
def cmd_rr(
    entry: float,
    stop: float,
    target_r: float = None,
    balance: float = None,
    risk_pct: float = 2.0,
    leverage: int = 10,
):
    if entry <= 0 or stop <= 0:
        print("ERROR: entry and stop must be positive")
        sys.exit(1)
    if entry == stop:
        print("ERROR: entry == stop")
        sys.exit(1)

    stop_dist = abs(entry - stop)
    stop_pct  = stop_dist / entry * 100
    is_long   = entry > stop
    direction = "LONG" if is_long else "SHORT"
    dir_c     = GREEN if is_long else RED

    sep()
    print(f"{BOLD}{'RISK : REWARD CALCULATOR':^72}{RESET}")
    sep()

    print(f"\n  Direction:   {dir_c}{BOLD}{direction}{RESET}")
    print(f"  Entry:       {entry:>16,.6f}")
    print(f"  Stop Loss:   {stop:>16,.6f}  ({stop_pct:.2f}% away)")

    risk_usdt = None
    if balance:
        risk_usdt  = balance * risk_pct / 100
        pos_size   = risk_usdt / stop_dist
        pos_value  = pos_size * entry
        margin     = pos_value / leverage
        margin_pct = margin / balance * 100

        print(f"\n{YEL}💰 Position Sizing  (balance {balance:,.2f} USDT){RESET}")
        print(f"  Risk:             {risk_pct:.1f}%  =  {risk_usdt:,.2f} USDT  (1R)")
        print(f"  Position Size:    {pos_size:,.4f} units")
        print(f"  Position Value:   {pos_value:,.2f} USDT")
        print(f"  Margin Required:  {margin:,.2f} USDT  ({margin_pct:.1f}% of account @ {leverage}x)")

    print(f"\n{YEL}🎯 Take Profit Levels{RESET}")
    r_levels = [(target_r, "Custom")] if target_r else [(1.0, "1R"), (2.0, "2R"), (3.0, "3R")]

    for mult, label in r_levels:
        tp = (entry + stop_dist * mult) if is_long else (entry - stop_dist * mult)
        extra = ""
        if risk_usdt is not None:
            profit = risk_usdt * mult
            extra  = f"  →  {GREEN}+{profit:,.2f} USDT{RESET}"
        print(f"  {label} ({mult}×):   {tp:>16,.6f}{extra}")

    r1 = (entry + stop_dist)     if is_long else (entry - stop_dist)
    r2 = (entry + stop_dist * 2) if is_long else (entry - stop_dist * 2)

    print(f"\n{YEL}📐 Trailing Stop Plan{RESET}")
    print(f"  At 1R ({r1:,.4f}):  move SL → {entry:,.4f}  (breakeven)")
    print(f"  At 2R ({r2:,.4f}):  move SL → 1R level    (lock profits)")

    if stop_pct > 5:
        print(f"\n  {RED}⚠️  Stop is {stop_pct:.1f}% away — consider reducing size{RESET}")

    be_wr = 1 / (1 + 3) * 100
    print(f"\n  Break-even win rate at 1:3 R/R: {be_wr:.0f}%")
    sep()


# ── Regime helpers ───────────────────────────────────────────────────────────
def _wilder_smooth(values: list, period: int) -> list:
    """Wilder's smoothing — EMA variant used by ATR and ADX."""
    if len(values) < period:
        return [None] * len(values)
    result = [None] * (period - 1)
    result.append(sum(values[:period]) / period)
    for v in values[period:]:
        result.append(result[-1] * (period - 1) / period + v)
    return result


def _calc_adx(highs: list, lows: list, closes: list, period: int = 14):
    """
    Compute ADX, +DI, -DI from OHLC arrays.
    Returns (adx, plus_di, minus_di) or (None, None, None) if insufficient data.
    """
    n = len(closes)
    if n < period * 2 + 5:
        return None, None, None
    tr_list, pdm_list, mdm_list = [], [], []
    for i in range(1, n):
        tr   = max(highs[i] - lows[i],
                   abs(highs[i]  - closes[i - 1]),
                   abs(lows[i]   - closes[i - 1]))
        up   = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        pdm  = up   if up > down and up > 0   else 0.0
        mdm  = down if down > up and down > 0 else 0.0
        tr_list.append(tr)
        pdm_list.append(pdm)
        mdm_list.append(mdm)
    atr  = _wilder_smooth(tr_list,  period)
    spdm = _wilder_smooth(pdm_list, period)
    smdm = _wilder_smooth(mdm_list, period)
    dx_list = []
    for i in range(len(atr)):
        if atr[i] is None or atr[i] == 0:
            dx_list.append(None)
            continue
        pdi   = (spdm[i] or 0) / atr[i] * 100
        mdi   = (smdm[i] or 0) / atr[i] * 100
        denom = pdi + mdi
        dx    = abs(pdi - mdi) / denom * 100 if denom > 0 else 0
        dx_list.append((dx, pdi, mdi))
    valid = [(i, v) for i, v in enumerate(dx_list) if v is not None]
    if len(valid) < period:
        return None, None, None
    adx_smooth = _wilder_smooth([v[0] for _, v in valid], period)
    adx = next((v for v in reversed(adx_smooth) if v is not None), None)
    _, last = valid[-1]
    return adx, last[1], last[2]


def _calc_ema(prices: list, period: int):
    """EMA of price list; returns last value or None."""
    if len(prices) < period:
        return None
    k   = 2.0 / (period + 1)
    ema = sum(prices[:period]) / period
    for p in prices[period:]:
        ema = p * k + ema * (1 - k)
    return ema


def _detect_structure(highs: list, lows: list, lookback: int = 20) -> str:
    """Classify price structure: 'bull_trend' | 'bear_trend' | 'ranging'."""
    h = highs[-lookback:] if len(highs) >= lookback else highs
    l = lows[-lookback:]  if len(lows)  >= lookback else lows
    n = len(h)
    if n < 6:
        return "ranging"
    swing_h, swing_l = [], []
    for i in range(1, n - 1):
        if h[i] >= h[i - 1] and h[i] >= h[i + 1]:
            swing_h.append(h[i])
        if l[i] <= l[i - 1] and l[i] <= l[i + 1]:
            swing_l.append(l[i])
    if len(swing_h) >= 2 and len(swing_l) >= 2:
        hh = swing_h[-1] > swing_h[-2]
        hl = swing_l[-1] > swing_l[-2]
        lh = swing_h[-1] < swing_h[-2]
        ll = swing_l[-1] < swing_l[-2]
        if hh and hl: return "bull_trend"
        if lh and ll: return "bear_trend"
        return "ranging"
    mid = n // 2
    if max(h[mid:]) > max(h[:mid]) and min(l[mid:]) > min(l[:mid]): return "bull_trend"
    if max(h[mid:]) < max(h[:mid]) and min(l[mid:]) < min(l[:mid]): return "bear_trend"
    return "ranging"


# ── klines ────────────────────────────────────────────────────────────────────
def cmd_klines(
    symbol:   str  = "BTCUSDT",
    interval: str  = "4h",
    limit:    int  = 100,
    json_out: bool = False,
):
    """Fetch OHLCV + compute ADX/EMA/structure regime. No API auth needed."""
    raw = public_get("/fapi/v1/klines", {
        "symbol":   symbol.upper(),
        "interval": interval,
        "limit":    limit,
    })
    if not raw:
        print("No kline data returned.")
        sys.exit(1)
    highs  = [float(k[2]) for k in raw]
    lows   = [float(k[3]) for k in raw]
    closes = [float(k[4]) for k in raw]
    price  = closes[-1]

    adx, plus_di, minus_di = _calc_adx(highs, lows, closes)
    ema20  = _calc_ema(closes, 20)
    ema50  = _calc_ema(closes, 50)
    struct = _detect_structure(highs, lows, lookback=20)

    # ADX > 60 is almost certainly a calculation artefact — trust structure instead
    adx_anomaly = adx is not None and adx > 60
    adx_ok      = adx is not None and not adx_anomaly

    # Regime: structure is primary signal; ADX < 20 overrides weak structure
    if struct == "bull_trend":   regime = "BULL"
    elif struct == "bear_trend": regime = "BEAR"
    else:                         regime = "RANGE"
    if adx_ok and adx < 20:       regime = "RANGE"

    range_high = max(highs[-20:])
    range_low  = min(lows[-20:])
    alt_long   = regime == "BULL"
    alt_short  = regime == "BEAR"

    if json_out:
        print(json.dumps({
            "symbol":          symbol.upper(),
            "interval":        interval,
            "price":           price,
            "adx":             round(adx, 1)      if adx      else None,
            "adx_anomaly":     adx_anomaly,
            "plus_di":         round(plus_di, 1)  if plus_di  else None,
            "minus_di":        round(minus_di, 1) if minus_di else None,
            "ema20":           round(ema20, 2)    if ema20    else None,
            "ema50":           round(ema50, 2)    if ema50    else None,
            "structure":       struct,
            "regime":          regime,
            "range_high":      range_high,
            "range_low":       range_low,
            "altcoin_long_ok": alt_long,
            "altcoin_short_ok":alt_short,
        }, indent=2))
        return

    # ── Human-readable output ───────────────────────────────────────────────
    adx_disp = f"{adx:.1f}" if adx else "n/a"
    if adx_anomaly:
        adx_disp += f"  {YEL}⚠ anomaly (>60) — structure used instead{RESET}"
    elif adx_ok:
        if adx >= 25:   adx_disp += f"  {GREEN}trending{RESET}"
        elif adx <= 20: adx_disp += f"  {YEL}ranging{RESET}"
        else:           adx_disp += f"  {DIM}transitional{RESET}"

    struct_c = {"bull_trend": GREEN, "bear_trend": RED, "ranging": YEL}.get(struct, DIM)
    regime_c = {"BULL": GREEN, "BEAR": RED, "RANGE": YEL}.get(regime, DIM)
    gate_l   = f"{GREEN}✅ Valid{RESET}"  if alt_long  else f"{RED}❌ Block{RESET}"
    gate_s   = f"{GREEN}✅ Valid{RESET}"  if alt_short else f"{RED}❌ Block{RESET}"
    pve20    = f"{GREEN}above{RESET}" if ema20 and price > ema20 else f"{RED}below{RESET}"
    pve50    = f"{GREEN}above{RESET}" if ema50 and price > ema50 else f"{RED}below{RESET}"

    sep()
    print(f"{BOLD}{f'REGIME CHECK — {symbol.upper()} {interval.upper()}':^72}{RESET}")
    sep()
    print(f"\n  Price:       {BOLD}{price:>16,.4f}{RESET}")
    if ema20: print(f"  EMA 20:      {ema20:>16,.4f}  (price {pve20})")
    if ema50: print(f"  EMA 50:      {ema50:>16,.4f}  (price {pve50})")
    print(f"  ADX (14):    {adx_disp}")
    if plus_di and minus_di:
        bias = f"{GREEN}bullish{RESET}" if plus_di > minus_di else f"{RED}bearish{RESET}"
        print(f"  +DI / \u2212DI:   {plus_di:.1f} / {minus_di:.1f}  ({bias} bias)")
    print(f"\n  Range 20b:   {range_low:,.4f} \u2013 {range_high:,.4f}")
    print(f"  Structure:   {struct_c}{struct.replace('_', ' ').upper()}{RESET}")
    print(f"\n  {BOLD}Regime:      {regime_c}{regime}{RESET}")
    print(f"\n  Altcoin LONG:   {gate_l}")
    print(f"  Altcoin SHORT:  {gate_s}")
    sep()


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        prog="bf.py",
        description="Binance Futures CLI — replaces all individual shell scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
commands:
  account         Full account summary (v3 API)
  balance         Quick wallet balance
  positions       Open positions with PnL (v3 API)
  income          Income history with auto-pagination
  trades          User trade history
  rr ENTRY STOP   Risk:Reward calculator (no API key needed)
  klines [SYM]    Regime check — ADX, EMA, structure (no API key needed)

examples:
  ./bf.py account
  ./bf.py account --raw                        Raw JSON
  ./bf.py positions
  ./bf.py income --days 365
  ./bf.py income --symbol BTCUSDT --type REALIZED_PNL
  ./bf.py trades --symbol ETHUSDT --days 90
  ./bf.py rr 50000 48000
  ./bf.py rr 50000 48000 --balance 1000 --risk 2 --leverage 10
  ./bf.py rr 0.50 0.46 --target 2.5
        """,
    )
    sub = ap.add_subparsers(dest="cmd", metavar="COMMAND")

    # account
    p = sub.add_parser("account", help="Account summary")
    p.add_argument("--raw", action="store_true", help="Raw JSON")

    # balance
    sub.add_parser("balance", help="Quick wallet balance")

    # positions
    p = sub.add_parser("positions", help="Open positions")
    p.add_argument("--raw", action="store_true", help="Raw JSON")

    # income
    p = sub.add_parser("income", help="Income / PnL history")
    p.add_argument("--days",   type=int, default=90,    help="Days of history (default: 90)")
    p.add_argument("--symbol",                          help="Filter by symbol, e.g. BTCUSDT")
    p.add_argument("--type",   dest="income_type",      help="REALIZED_PNL | FUNDING_FEE | COMMISSION")
    p.add_argument("--raw",    action="store_true",     help="Raw JSON")

    # trades
    p = sub.add_parser("trades", help="User trade history")
    p.add_argument("--symbol",                          help="Filter by symbol")
    p.add_argument("--days",   type=int, default=30,    help="Days of history (default: 30)")
    p.add_argument("--raw",    action="store_true",     help="Raw JSON")

    # klines
    p = sub.add_parser("klines", help="Regime check — ADX, EMA, structure (no API key)")
    p.add_argument("symbol",     nargs="?",  default="BTCUSDT", help="Symbol (default: BTCUSDT)")
    p.add_argument("--interval",             default="4h",      help="Candle interval (default: 4h)")
    p.add_argument("--limit",    type=int,   default=100,        help="Number of candles (default: 100)")
    p.add_argument("--json",     action="store_true",            help="Machine-readable JSON output")

    # rr
    p = sub.add_parser("rr", help="Risk:Reward calculator")
    p.add_argument("entry",             type=float,             help="Entry price")
    p.add_argument("stop",              type=float,             help="Stop loss price")
    p.add_argument("--target",          type=float,             help="Custom R-multiple, e.g. 2.5")
    p.add_argument("--balance",         type=float,             help="Account balance in USDT")
    p.add_argument("--risk",            type=float, default=2,  help="Risk %% per trade (default: 2)")
    p.add_argument("--leverage",        type=int,   default=10, help="Leverage (default: 10)")

    args = ap.parse_args()

    if not args.cmd:
        ap.print_help()
        sys.exit(0)

    # rr needs no API
    if args.cmd == "rr":
        cmd_rr(args.entry, args.stop, args.target, args.balance, args.risk, args.leverage)
        return
    if args.cmd == "klines":
        cmd_klines(args.symbol, args.interval, args.limit, args.json)
        return

    key, secret = load_creds()

    dispatch = {
        "account":   lambda: cmd_account(key, secret,  raw=args.raw),
        "balance":   lambda: cmd_balance(key, secret),
        "positions": lambda: cmd_positions(key, secret, raw=args.raw),
        "income":    lambda: cmd_income(
            key, secret,
            days=args.days,
            symbol=args.symbol,
            income_type=args.income_type,
            raw=args.raw,
        ),
        "trades":    lambda: cmd_trades(
            key, secret,
            symbol=args.symbol,
            days=args.days,
            raw=args.raw,
        ),
    }
    dispatch[args.cmd]()


if __name__ == "__main__":
    main()
