# personal-claw-skills

Personal skill library for [opencode](https://opencode.ai) / Claude. Install skills to `~/.claude/skills/` to extend Claude with domain-specific knowledge, scripts, and references.

---

## Install

```bash
# Interactive — pick which skills to install
./install.sh

# Install everything
./install.sh --all

# Dry run (preview only)
./install.sh --dry-run
```

Requires `rsync`. Uses `fzf` for interactive selection if available, numbered menu fallback otherwise.

```bash
# Remove installed skills
./uninstall.sh
```

---

## Skills

### Finance

| Skill | Description |
|-------|-------------|
| [`binance-futures`](skills/binance-futures/README.md) | Binance Futures API — account, positions, income history, WebSocket, funding rates. Unified `bf.py` CLI (pure stdlib). |
| [`crypto-quant-trader`](skills/crypto-quant-trader/README.md) | Senior quant researcher mode — regime detection, ICT/SMC, order flow (OBI/TFI), Kelly sizing, walk-forward backtesting. |
| [`trading-journal`](skills/trading-journal/README.md) | Performance analytics — Sharpe, SQN, K-Ratio, behavioral bias detection, Monte Carlo, equity curve analysis. |

### Dev Tools

| Skill | Description |
|-------|-------------|
| `github` | Interact with GitHub via `gh` CLI — issues, PRs, CI runs, API queries. |
| `tmux` | Remote-control tmux sessions — send keystrokes, scrape pane output for interactive CLIs. |
| `skill-creator` | Create or update skills — structure, scripts, references, and assets. |
| `summarize` | Summarize URLs, podcasts, and local files. Transcribe YouTube/video content. |

---

## Finance Skill Workflow

The three finance skills are designed to work together:

```
binance-futures          →   crypto-quant-trader   →   trading-journal
(pull live data)             (analyze & strategize)     (audit performance)

bf.py income --days 90   →   "Is my edge holding?"  →   advanced_metrics.py
bf.py positions          →   "Should I add here?"   →   behavioral_analytics.py
```

---

## Structure

```
personal-claw-skills/
├── install.sh                  Interactive rsync installer
├── uninstall.sh                Interactive skill remover
└── skills/
    ├── binance-futures/        Futures API + bf.py CLI
    ├── crypto-quant-trader/    Quant analysis & strategy
    ├── trading-journal/        Performance analytics
    ├── github/                 GitHub CLI wrapper
    ├── tmux/                   tmux session control
    ├── skill-creator/          Skill authoring helper
    └── summarize/              URL/video summarizer
```
