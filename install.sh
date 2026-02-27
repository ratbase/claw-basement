#!/usr/bin/env bash
# install.sh — Install personal claw skills to ~/.claude/skills/
#
# Usage:
#   ./install.sh              Interactive selection (fzf if available, else menu)
#   ./install.sh --all        Install all skills without prompts
#   ./install.sh --dry-run    Show what would change without applying
#   SKILLS_DST=/custom/path ./install.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_DIR/skills"
SKILLS_DST="${SKILLS_DST:-$HOME/.claude/skills}"
DRY_RUN=false
INSTALL_ALL=false

# ── Parse args ────────────────────────────────────────────────────────────────
for arg in "$@"; do
  case "$arg" in
    --dry-run)   DRY_RUN=true ;;
    --all)       INSTALL_ALL=true ;;
    --help|-h)
      echo "Usage: ./install.sh [--all] [--dry-run]"
      echo "  --all       Install all skills without prompting"
      echo "  --dry-run   Preview changes without applying"
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

if [[ ${#skill_names[@]} -eq 0 ]]; then
  echo -e "${RED}No skills found in $SKILLS_SRC${NC}"
  exit 1
fi

# ── Header ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══ Claw Skills Installer ══════════════════════════════════╗${NC}"
echo -e "${BOLD}║${NC}  src: ${DIM}$SKILLS_SRC${NC}"
echo -e "${BOLD}║${NC}  dst: ${CYAN}$SKILLS_DST${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ── Select skills ─────────────────────────────────────────────────────────────
selected=()

if [[ "$INSTALL_ALL" == true ]]; then
  selected=("${skill_names[@]}")

elif command -v fzf &>/dev/null; then
  # fzf multi-select with SKILL.md preview
  mapfile -t selected < <(
    printf '%s\n' "${skill_names[@]}" | \
    fzf \
      --multi \
      --prompt="  Skills › " \
      --header="TAB=select  ENTER=confirm  CTRL-A=all  ·  src→dst" \
      --preview="
        f='$SKILLS_SRC/{}/SKILL.md'
        [[ -f \"\$f\" ]] && head -50 \"\$f\" || echo 'No SKILL.md found'
      " \
      --preview-window="right:55%:wrap" \
      --height="80%" \
      --border="rounded" \
      --color="header:italic,border:cyan,prompt:bright-cyan,pointer:bright-green" \
      --bind="ctrl-a:select-all" \
      --marker="✓" \
      2>/dev/null
  ) || true

else
  # Fallback: numbered checkbox menu
  echo -e "  ${BOLD}Available Skills${NC}\n"
  for i in "${!skill_names[@]}"; do
    installed=""
    [[ -d "$SKILLS_DST/${skill_names[$i]}" ]] && installed=" ${YEL}(installed)${NC}"
    printf "  ${CYAN}%2d)${NC}  ${BOLD}%-28s${NC}  ${DIM}%s${NC}%b\n" \
      "$((i+1))" "${skill_names[$i]}" "${skill_descs[$i]}" "$installed"
  done
  echo ""
  echo -e "  ${YEL}Enter numbers (e.g. 1 3 5), ranges (1-3), or 'all':${NC}"
  printf "  › "
  read -r input

  if [[ "$input" == "all" ]]; then
    selected=("${skill_names[@]}")
  else
    # Support ranges like 1-3 and individual numbers
    for token in $input; do
      if [[ "$token" =~ ^([0-9]+)-([0-9]+)$ ]]; then
        for ((n=${BASH_REMATCH[1]}; n<=${BASH_REMATCH[2]}; n++)); do
          idx=$((n - 1))
          [[ $idx -ge 0 && $idx -lt ${#skill_names[@]} ]] && selected+=("${skill_names[$idx]}")
        done
      elif [[ "$token" =~ ^[0-9]+$ ]]; then
        idx=$((token - 1))
        [[ $idx -ge 0 && $idx -lt ${#skill_names[@]} ]] && selected+=("${skill_names[$idx]}")
      fi
    done
  fi
fi

# ── Nothing selected ──────────────────────────────────────────────────────────
if [[ ${#selected[@]} -eq 0 ]]; then
  echo -e "  ${YEL}No skills selected.${NC}"
  exit 0
fi

# ── Preview plan ──────────────────────────────────────────────────────────────
echo ""
echo -e "  ${BOLD}Plan:${NC}"
echo "  ─────────────────────────────────────────────"

for s in "${selected[@]}"; do
  dst="$SKILLS_DST/$s"
  if [[ -d "$dst" ]]; then
    echo -e "  ${YEL}↻${NC}  ${BOLD}$s${NC}  ${DIM}(update)${NC}"
  else
    echo -e "  ${GREEN}+${NC}  ${BOLD}$s${NC}  ${GREEN}(new install)${NC}"
  fi
done

echo ""

# ── Dry run preview ───────────────────────────────────────────────────────────
if [[ "$DRY_RUN" == true ]]; then
  echo -e "  ${BLUE}─── Dry run (no changes applied) ───${NC}"
  for s in "${selected[@]}"; do
    echo -e "\n  ${BOLD}$s${NC}:"
    rsync -av --dry-run --delete \
      "$SKILLS_SRC/$s/" \
      "$SKILLS_DST/$s/" \
      2>&1 | grep -v '^sending\|^sent\|^total\|^$' | sed 's/^/    /' | head -20
  done
  echo ""
  echo -e "  ${YEL}Dry run complete. Run without --dry-run to apply.${NC}"
  exit 0
fi

# ── Confirm ───────────────────────────────────────────────────────────────────
printf "  ${BOLD}Apply ${#selected[@]} skill(s)? [y/N]: ${NC}"
read -r confirm
echo ""

if [[ "${confirm,,}" != "y" ]]; then
  echo -e "  ${YEL}Cancelled.${NC}"
  exit 0
fi

# ── Install ───────────────────────────────────────────────────────────────────
mkdir -p "$SKILLS_DST"

success=0
failed=0

for s in "${selected[@]}"; do
  printf "  Installing ${BOLD}%-28s${NC}" "$s"
  if rsync -a --delete \
      "$SKILLS_SRC/$s/" \
      "$SKILLS_DST/$s/" \
      2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
    ((success++))
  else
    echo -e "${RED}✗ failed${NC}"
    ((failed++))
  fi
done

echo ""
echo -e "  ─────────────────────────────────────────────"

if [[ $failed -eq 0 ]]; then
  echo -e "  ${GREEN}${BOLD}✓ $success skill(s) installed successfully${NC}"
else
  echo -e "  ${GREEN}$success installed${NC}  ${RED}$failed failed${NC}"
fi

echo -e "  ${DIM}→ $SKILLS_DST${NC}"
echo ""
