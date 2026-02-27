#!/usr/bin/env bash
# uninstall.sh — Remove installed personal claw skills from detected destination
#
# Usage:
#   ./uninstall.sh            Interactive selection of which to remove
#   ./uninstall.sh --all      Remove all skills that exist in this repo

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_DIR/skills"
_CLAUDE_DST="$HOME/.claude/skills"
_PICO_DST="$HOME/.picoclaw/workspace/skills"
SKILLS_DST="${SKILLS_DST:-}"
REMOVE_ALL=false

for arg in "$@"; do
  case "$arg" in
    --all)    REMOVE_ALL=true ;;
    --help|-h)
      echo "Usage: ./uninstall.sh [--all]"
      echo "  --all   Remove all installed skills from this repo"
      exit 0
      ;;
    *) echo "Unknown option: $arg"; exit 1 ;;
  esac
done

RED='\033[0;31m'
GREEN='\033[0;32m'
YEL='\033[0;33m'
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

# ── Find skills that are actually installed ───────────────────────────────────
installed=()

for skill_dir in "$SKILLS_SRC"/*/; do
  [[ -d "$skill_dir" ]] || continue
  skill=$(basename "$skill_dir")
  [[ -d "$SKILLS_DST/$skill" ]] && installed+=("$skill")
done

if [[ ${#installed[@]} -eq 0 ]]; then
  echo -e "\n  ${YEL}No skills from this repo are currently installed in $SKILLS_DST${NC}\n"
  exit 0
fi

echo ""
echo -e "${BOLD}╔══ Claw Skills Uninstaller ════════════════════════════════╗${NC}"
echo -e "${BOLD}║${NC}  target: ${CYAN}$SKILLS_DST${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ── Select ────────────────────────────────────────────────────────────────────
selected=()

if [[ "$REMOVE_ALL" == true ]]; then
  selected=("${installed[@]}")

elif command -v fzf &>/dev/null; then
  mapfile -t selected < <(
    printf '%s\n' "${installed[@]}" | \
    fzf \
      --multi \
      --prompt="  Remove › " \
      --header="TAB=select  ENTER=confirm  CTRL-A=all" \
      --preview="bash -c 'ls -la \"$SKILLS_DST/{}/\" 2>/dev/null | head -30 || echo Not installed' " \
      --preview-window="right:50%:wrap" \
      --height="70%" \
      --border="rounded" \
      --color="header:italic,border:red,prompt:bright-red,pointer:bright-red" \
      --bind="ctrl-a:select-all" \
      --marker="✓" \
      2>/dev/null
  ) || true

else
  echo -e "  ${BOLD}Installed Skills (from this repo)${NC}\n"
  for i in "${!installed[@]}"; do
    printf "  ${CYAN}%2d)${NC}  ${BOLD}%s${NC}\n" "$((i+1))" "${installed[$i]}"
  done
  echo ""
  echo -e "  ${YEL}Enter numbers to remove (e.g. 1 3), or 'all':${NC}"
  printf "  › "
  read -r input

  if [[ "$input" == "all" ]]; then
    selected=("${installed[@]}")
  else
    for token in $input; do
      if [[ "$token" =~ ^[0-9]+$ ]]; then
        idx=$((token - 1))
        [[ $idx -ge 0 && $idx -lt ${#installed[@]} ]] && selected+=("${installed[$idx]}")
      fi
    done
  fi
fi

if [[ ${#selected[@]} -eq 0 ]]; then
  echo -e "  ${YEL}Nothing selected.${NC}"
  exit 0
fi

echo ""
echo -e "  ${BOLD}Will remove:${NC}"
for s in "${selected[@]}"; do
  echo -e "  ${RED}✗${NC}  ${BOLD}$s${NC}  ${DIM}($SKILLS_DST/$s)${NC}"
done

echo ""
printf "  ${BOLD}${RED}Remove ${#selected[@]} skill(s)? [y/N]: ${NC}"
read -r confirm
echo ""

if [[ "${confirm,,}" != "y" ]]; then
  echo -e "  ${YEL}Cancelled.${NC}"
  exit 0
fi

count=0
for s in "${selected[@]}"; do
  printf "  Removing ${BOLD}%-28s${NC}" "$s"
  rm -rf "${SKILLS_DST:?}/$s"
  echo -e "${RED}✗ removed${NC}"
  ((count++))
done

echo ""
echo -e "  ${RED}${BOLD}$count skill(s) removed.${NC}"
echo ""
