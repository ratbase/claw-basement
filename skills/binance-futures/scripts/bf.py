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
