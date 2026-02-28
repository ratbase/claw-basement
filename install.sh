#!/usr/bin/env bash
# install.sh — Install skills and/or picoclaw workspace files
#
# Usage:
#   ./install.sh                  Interactive: choose component + skills
#   ./install.sh --all            Install everything without prompts
#   ./install.sh --skills         Skills only (interactive menu)
#   ./install.sh --skills --all   All skills, no prompts
#   ./install.sh --workspace      Workspace config files only (picoclaw)
#   ./install.sh --dry-run        Preview changes without applying
#   SKILLS_DST=/custom/path ./install.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_DIR/skills"
WORKSPACE_SRC="$REPO_DIR/workspace"
_CLAUDE_DST="$HOME/.claude/skills"
_PICO_DST="$HOME/.picoclaw/workspace/skills"
SKILLS_DST="${SKILLS_DST:-}"
DRY_RUN=false
INSTALL_ALL=false
COMPONENT=""   # "skills" | "workspace" | "both" | "" = prompt

# ── Parse args ────────────────────────────────────────────────────────────────
for arg in "$@"; do
  case "$arg" in
    --dry-run)    DRY_RUN=true ;;
    --all)        INSTALL_ALL=true ;;
    --skills)     COMPONENT="skills" ;;
    --workspace)  COMPONENT="workspace" ;;
    --help|-h)
      echo "Usage: ./install.sh [OPTIONS]"
      echo ""
      echo "  --all         Install everything without prompting"
      echo "  --skills      Install skills only (use with --all to skip menu)"
      echo "  --workspace   Install workspace config files only (picoclaw)"
      echo "  --dry-run     Preview changes without applying"
      echo ""
      echo "  SKILLS_DST=/custom/path ./install.sh"
      exit 0
      ;;
    *) echo "Unknown option: $arg"; exit 1 ;;
  esac
done

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YEL='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ── Detect destination ────────────────────────────────────────────────────────
if [[ -z "$SKILLS_DST" ]]; then
  _dsts=() _dlabels=()
  [[ -d "$_CLAUDE_DST" ]] && { _dsts+=("$_CLAUDE_DST"); _dlabels+=("~/.claude/skills               (opencode / claude)"); }
  [[ -d "$_PICO_DST" ]]   && { _dsts+=("$_PICO_DST");   _dlabels+=("~/.picoclaw/workspace/skills   (picoclaw)"); }

  if [[ ${#_dsts[@]} -eq 0 ]]; then
    SKILLS_DST="$_CLAUDE_DST"
  elif [[ ${#_dsts[@]} -eq 1 ]]; then
    SKILLS_DST="${_dsts[0]}"
  else
    echo ""
    echo -e "  ${BOLD}Multiple destinations detected — choose one:${NC}"
    for _i in "${!_dsts[@]}"; do
      echo -e "  ${CYAN}$((_i+1)))${NC}  ${_dlabels[$_i]}"
    done
    echo ""
    printf "  › [1]: "
    read -r _choice
    _idx=$(( ${_choice:-1} - 1 ))
    [[ $_idx -ge 0 && $_idx -lt ${#_dsts[@]} ]] && SKILLS_DST="${_dsts[$_idx]}" || SKILLS_DST="${_dsts[0]}"
    unset _choice _idx
  fi
  unset _dsts _dlabels _i
fi

# Derive workspace destination (picoclaw only)
IS_PICO=false
WORKSPACE_DST=""
if [[ "$SKILLS_DST" == *"/.picoclaw/"* ]]; then
  IS_PICO=true
  WORKSPACE_DST="${SKILLS_DST%/skills}"
fi

# Workspace only applies to picoclaw — downgrade silently if not
if [[ "$IS_PICO" == false ]]; then
  if [[ "$COMPONENT" == "workspace" || "$COMPONENT" == "both" ]]; then
    echo -e "  ${YEL}Note:${NC} workspace files only apply to picoclaw. Installing skills only."
    echo ""
    COMPONENT="skills"
  fi
fi

# --all with no explicit component → install everything available
if [[ "$INSTALL_ALL" == true && -z "$COMPONENT" ]]; then
  [[ "$IS_PICO" == true ]] && COMPONENT="both" || COMPONENT="skills"
fi

# ── Discover skills ───────────────────────────────────────────────────────────
skill_names=()
skill_descs=()

for skill_dir in "$SKILLS_SRC"/*/; do
  [[ -d "$skill_dir" ]] || continue
  skill=$(basename "$skill_dir")
  skill_md="$skill_dir/SKILL.md"
  if [[ -f "$skill_md" ]]; then
    desc=$(grep -m1 '^description:' "$skill_md" \
      | sed 's/^description: *//' \
      | tr -d '"' \
      | cut -c1-65)
    skill_names+=("$skill")
    skill_descs+=("${desc:-—}")
  fi
done

if [[ "$COMPONENT" != "workspace" && ${#skill_names[@]} -eq 0 ]]; then
  echo -e "${RED}No skills found in $SKILLS_SRC${NC}"
  exit 1
fi

# ── Header ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══ Claw Installer ═════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║${NC}  src:       ${DIM}$REPO_DIR${NC}"
echo -e "${BOLD}║${NC}  skills  →  ${CYAN}$SKILLS_DST${NC}"
if [[ "$IS_PICO" == true ]]; then
  echo -e "${BOLD}║${NC}  workspace →  ${CYAN}$WORKSPACE_DST${NC}"
fi
echo -e "${BOLD}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ── Interaction guard ─────────────────────────────────────────────────────────
# Workspace-only never needs interactive input. Everything else does.
if [[ "$INSTALL_ALL" == false && "$COMPONENT" != "workspace" && ! -t 0 ]]; then
  echo -e "  ${YEL}No interactive terminal detected.${NC}"
  echo -e "  ${DIM}  ./install.sh --all              Install everything${NC}"
  echo -e "  ${DIM}  ./install.sh --skills --all     Install all skills${NC}"
  echo -e "  ${DIM}  ./install.sh --workspace        Install workspace files${NC}"
  echo ""
  exit 1
fi

# ── Component selection ───────────────────────────────────────────────────────
if [[ -z "$COMPONENT" ]]; then
  if [[ "$IS_PICO" == true ]]; then
    echo -e "  ${BOLD}What to install?${NC}"
    echo -e "  ${CYAN}1)${NC}  Skills only        ${DIM}→ $SKILLS_DST${NC}"
    echo -e "  ${CYAN}2)${NC}  Workspace files    ${DIM}→ $WORKSPACE_DST${NC}  ${DIM}(AGENTS, HEARTBEAT, IDENTITY…)${NC}"
    echo -e "  ${CYAN}3)${NC}  Both"
    echo ""
    printf "  › [3]: "
    read -r _comp
    case "${_comp:-3}" in
      1) COMPONENT="skills" ;;
      2) COMPONENT="workspace" ;;
      *) COMPONENT="both" ;;
    esac
    echo ""
  else
    COMPONENT="skills"
  fi
fi

# ── Skills menu ───────────────────────────────────────────────────────────────
selected=()

_menu_select() {
  echo -e "  ${BOLD}Available Skills${NC}\n"
  local i
  for i in "${!skill_names[@]}"; do
    local _inst=""
    [[ -d "$SKILLS_DST/${skill_names[$i]}" ]] && _inst=" ${YEL}(installed)${NC}"
    printf "  ${CYAN}%2d)${NC}  ${BOLD}%-28s${NC}  ${DIM}%s${NC}%b\n" \
      "$((i+1))" "${skill_names[$i]}" "${skill_descs[$i]}" "$_inst"
  done
  echo ""
  echo -e "  ${YEL}Enter numbers (e.g. 1 3 5), ranges (1-3), or 'all':${NC}"
  printf "  › "
  read -r _minput
  if [[ "$_minput" == "all" ]]; then
    selected=("${skill_names[@]}")
  else
    local token
    for token in $_minput; do
      if [[ "$token" =~ ^([0-9]+)-([0-9]+)$ ]]; then
        local n
        for ((n=${BASH_REMATCH[1]}; n<=${BASH_REMATCH[2]}; n++)); do
          local _idx=$((n - 1))
          [[ $_idx -ge 0 && $_idx -lt ${#skill_names[@]} ]] && selected+=("${skill_names[$_idx]}")
        done
      elif [[ "$token" =~ ^[0-9]+$ ]]; then
        local _idx=$((token - 1))
        [[ $_idx -ge 0 && $_idx -lt ${#skill_names[@]} ]] && selected+=("${skill_names[$_idx]}")
      fi
    done
  fi
}

# ── Skills selection ──────────────────────────────────────────────────────────
if [[ "$COMPONENT" != "workspace" ]]; then
  if [[ "$INSTALL_ALL" == true ]]; then
    selected=("${skill_names[@]}")
  else
    _menu_select
  fi
fi

if [[ "$COMPONENT" != "workspace" && ${#selected[@]} -eq 0 ]]; then
  echo -e "  ${YEL}No skills selected.${NC}"
  exit 0
fi

# ── Plan preview ──────────────────────────────────────────────────────────────
echo ""
echo -e "  ${BOLD}Plan:${NC}"
echo "  ─────────────────────────────────────────────"

if [[ "$COMPONENT" != "workspace" ]]; then
  for s in "${selected[@]}"; do
    if [[ -d "$SKILLS_DST/$s" ]]; then
      echo -e "  ${YEL}↻${NC}  ${BOLD}$s${NC}  ${DIM}(update)${NC}"
    else
      echo -e "  ${GREEN}+${NC}  ${BOLD}$s${NC}  ${GREEN}(new)${NC}"
    fi
  done
fi

if [[ "$COMPONENT" != "skills" && "$IS_PICO" == true ]]; then
  echo -e "  ${CYAN}⚙${NC}  ${BOLD}workspace files${NC}  ${DIM}→ $WORKSPACE_DST${NC}"
  for _f in "$WORKSPACE_SRC"/*.md; do
    [[ -f "$_f" ]] || continue
    _fname=$(basename "$_f")
    if [[ -f "$WORKSPACE_DST/$_fname" ]]; then
      echo -e "     ${YEL}↻${NC}  ${DIM}$_fname (update)${NC}"
    else
      echo -e "     ${GREEN}+${NC}  ${DIM}$_fname (new)${NC}"
    fi
  done
fi

echo ""

# ── Dry run ───────────────────────────────────────────────────────────────────
if [[ "$DRY_RUN" == true ]]; then
  echo -e "  ${BLUE}─── Dry run (no changes applied) ───${NC}"

  if [[ "$COMPONENT" != "workspace" ]]; then
    for s in "${selected[@]}"; do
      echo -e "\n  ${BOLD}$s${NC}:"
      rsync -av --dry-run --delete \
        "$SKILLS_SRC/$s/" \
        "$SKILLS_DST/$s/" \
        2>&1 | grep -v '^sending\|^sent\|^total\|^$' | sed 's/^/    /' | head -20
    done
  fi

  if [[ "$COMPONENT" != "skills" && "$IS_PICO" == true ]]; then
    echo -e "\n  ${BOLD}workspace files${NC}:"
    rsync -av --dry-run \
      --include='*.md' --exclude='*' \
      "$WORKSPACE_SRC/" \
      "$WORKSPACE_DST/" \
      2>&1 | grep -v '^sending\|^sent\|^total\|^$' | sed 's/^/    /' | head -20
  fi

  echo ""
  echo -e "  ${YEL}Dry run complete. Run without --dry-run to apply.${NC}"
  exit 0
fi

# ── Confirm ───────────────────────────────────────────────────────────────────
_summary=""
[[ "$COMPONENT" != "workspace" ]] && _summary="${#selected[@]} skill(s)"
if [[ "$COMPONENT" != "skills" && "$IS_PICO" == true ]]; then
  [[ -n "$_summary" ]] && _summary="$_summary + workspace files" || _summary="workspace files"
fi

printf "  ${BOLD}Apply %s? [y/N]: ${NC}" "$_summary"
read -r confirm
echo ""

if [[ "${confirm,,}" != "y" ]]; then
  echo -e "  ${YEL}Cancelled.${NC}"
  exit 0
fi

# ── Install skills ────────────────────────────────────────────────────────────
skill_success=0
skill_failed=0

if [[ "$COMPONENT" != "workspace" && ${#selected[@]} -gt 0 ]]; then
  mkdir -p "$SKILLS_DST"
  for s in "${selected[@]}"; do
    printf "  Installing ${BOLD}%-28s${NC}" "$s"
    if rsync -a --delete \
        "$SKILLS_SRC/$s/" \
        "$SKILLS_DST/$s/" \
        2>/dev/null; then
      echo -e "${GREEN}✓${NC}"
      ((skill_success++))
    else
      echo -e "${RED}✗ failed${NC}"
      ((skill_failed++))
    fi
  done
fi

# ── Install workspace files ───────────────────────────────────────────────────
ws_success=0
ws_failed=0

if [[ "$COMPONENT" != "skills" && "$IS_PICO" == true ]]; then
  mkdir -p "$WORKSPACE_DST"
  printf "  Installing ${BOLD}%-28s${NC}" "workspace files"
  if rsync -a \
      --include='*.md' --exclude='*' \
      "$WORKSPACE_SRC/" \
      "$WORKSPACE_DST/" \
      2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
    ws_success=1
  else
    echo -e "${RED}✗ failed${NC}"
    ws_failed=1
  fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "  ─────────────────────────────────────────────"

_total_fail=$(( skill_failed + ws_failed ))
if [[ $_total_fail -eq 0 ]]; then
  if [[ $skill_success -gt 0 && $ws_success -gt 0 ]]; then
    echo -e "  ${GREEN}${BOLD}✓ $skill_success skill(s) + workspace files installed${NC}"
  elif [[ $skill_success -gt 0 ]]; then
    echo -e "  ${GREEN}${BOLD}✓ $skill_success skill(s) installed${NC}"
  else
    echo -e "  ${GREEN}${BOLD}✓ workspace files installed${NC}"
  fi
else
  echo -e "  ${GREEN}$((skill_success + ws_success)) installed${NC}  ${RED}$_total_fail failed${NC}"
fi

[[ $skill_success -gt 0 ]] && echo -e "  ${DIM}skills    → $SKILLS_DST${NC}"
[[ $ws_success -gt 0 ]]    && echo -e "  ${DIM}workspace → $WORKSPACE_DST${NC}"
echo ""
