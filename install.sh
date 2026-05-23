#!/bin/bash
# install.sh — one-shot installer for auto-production skills.
# Mirrors ARIS install pattern: clone + symlink/copy skills + register hooks.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/<you>/auto-production/main/install.sh | bash
#   # or, from a local clone:
#   ./install.sh [--mode user|project|both] [--target /path/to/project]
#
# Modes:
#   user     install skills to ~/.claude/skills/auto-production (default if no project dir)
#   project  install to <target>/.claude/skills/ + register hooks in <target>/.claude/settings.json
#   both     do both

set -euo pipefail

MODE="${MODE:-user}"
TARGET="${TARGET:-$(pwd)}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while [ $# -gt 0 ]; do
  case "$1" in
    --mode) MODE="$2"; shift 2 ;;
    --target) TARGET="$2"; shift 2 ;;
    --help|-h) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1"; exit 2 ;;
  esac
done

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m⚠\033[0m %s\n" "$1"; }

install_user() {
  bold "» installing to ~/.claude/skills/auto-production"
  local dest="$HOME/.claude/skills/auto-production"
  mkdir -p "$(dirname "$dest")"
  if [ -L "$dest" ] || [ -e "$dest" ]; then
    warn "exists at $dest — replacing symlink/dir"
    rm -rf "$dest"
  fi
  # symlink each skill, plus tools/templates/AGENT_GUIDE.md
  ln -s "$REPO_DIR" "$dest"
  ok "user-scope link: $dest → $REPO_DIR"
}

install_project() {
  bold "» installing to project: $TARGET"
  [ -d "$TARGET" ] || { echo "❌ $TARGET not found"; exit 2; }
  local pdest="$TARGET/.claude/skills"
  mkdir -p "$pdest"
  for s in "$REPO_DIR"/skills/*/; do
    local name; name=$(basename "$s")
    local link="$pdest/$name"
    [ -e "$link" ] && rm -rf "$link"
    ln -s "$s" "$link"
  done
  ok "linked $(ls "$pdest" | wc -l) skills to $pdest/"

  # register hooks
  local cfg="$TARGET/.claude/settings.json"
  if [ -f "$cfg" ]; then
    warn "$cfg exists — backing up to $cfg.bak"
    cp "$cfg" "$cfg.bak"
  fi
  cp "$REPO_DIR/templates/settings.json" "$cfg"
  ok "wrote hooks config: $cfg"

  # bootstrap .auto-production/
  mkdir -p "$TARGET/.auto-production/"{audit,cache/citations,meta_opt,baseline}
  ok "bootstrapped .auto-production/"

  # CLAUDE.md
  if [ ! -f "$TARGET/CLAUDE.md" ]; then
    cp "$REPO_DIR/templates/CLAUDE.md" "$TARGET/CLAUDE.md"
    ok "wrote CLAUDE.md"
  else
    warn "$TARGET/CLAUDE.md exists — see templates/CLAUDE.md for reference"
  fi

  # export AUTO_PRODUCTION_REPO
  if ! grep -q "AUTO_PRODUCTION_REPO" "$HOME/.bashrc" 2>/dev/null; then
    echo "export AUTO_PRODUCTION_REPO=$REPO_DIR" >> "$HOME/.bashrc"
    ok "appended AUTO_PRODUCTION_REPO export to ~/.bashrc"
  fi
}

case "$MODE" in
  user)    install_user ;;
  project) install_project ;;
  both)    install_user; install_project ;;
  *) echo "unknown mode: $MODE"; exit 2 ;;
esac

echo
bold "✅ done."
echo "Next steps:"
echo "  1.  cd $TARGET"
echo "  2.  /sprint-contract --init    # write your 5-tuple"
echo "  3.  /research-pipeline \"your research topic\""
echo
echo "Or for overnight autonomous mode:"
echo "  /sleep-research \"goal description\""
