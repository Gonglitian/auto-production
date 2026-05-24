#!/bin/bash
# install.sh — one-shot installer for auto-production skills.
# Mirrors ARIS install pattern: clone + symlink/copy skills + register hooks.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Gonglitian/auto-production/main/install.sh | bash
#   # or, from a local clone:
#   ./install.sh [--mode user|project|both] [--target /path/to/project]
#   ./install.sh --update                 # git pull + re-link any new skills
#   ./install.sh --uninstall [--target /path/to/project]
#
# Modes:
#   user      install skills to ~/.claude/skills/auto-production (default)
#   project   install to <target>/.claude/skills/ + hooks in <target>/.claude/settings.json
#   both      do both
#   update    git pull repo, re-link any new skills (user and current project)
#   uninstall remove install (user and/or project)

set -euo pipefail

MODE="${MODE:-user}"
TARGET="${TARGET:-$(pwd)}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while [ $# -gt 0 ]; do
  case "$1" in
    --mode) MODE="$2"; shift 2 ;;
    --target) TARGET="$2"; shift 2 ;;
    --update) MODE="update"; shift 1 ;;
    --uninstall) MODE="uninstall"; shift 1 ;;
    --help|-h) sed -n '2,21p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1"; exit 2 ;;
  esac
done

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m⚠\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; }

install_user() {
  bold "» installing to ~/.claude/skills/auto-production"
  local dest="$HOME/.claude/skills/auto-production"
  mkdir -p "$(dirname "$dest")"
  if [ -L "$dest" ] || [ -e "$dest" ]; then
    warn "exists at $dest — replacing symlink/dir"
    rm -rf "$dest"
  fi
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

  # register hooks (backup existing)
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

update_install() {
  bold "» updating auto-production at $REPO_DIR"
  if [ ! -d "$REPO_DIR/.git" ]; then
    fail "$REPO_DIR is not a git checkout — re-clone manually"
    exit 2
  fi

  # check dirty
  if ! git -C "$REPO_DIR" diff --quiet || ! git -C "$REPO_DIR" diff --cached --quiet; then
    warn "uncommitted changes in $REPO_DIR — refusing auto-pull"
    git -C "$REPO_DIR" status --short
    exit 2
  fi

  local before_commit; before_commit=$(git -C "$REPO_DIR" rev-parse --short HEAD)
  git -C "$REPO_DIR" pull --ff-only
  local after_commit; after_commit=$(git -C "$REPO_DIR" rev-parse --short HEAD)
  if [ "$before_commit" = "$after_commit" ]; then
    ok "already up-to-date ($after_commit)"
  else
    ok "updated $before_commit → $after_commit"
  fi

  # re-link user install if present
  if [ -L "$HOME/.claude/skills/auto-production" ]; then
    ok "user install — already a symlink, no relink needed"
  fi

  # re-link project install if current dir has one
  if [ -d "$TARGET/.claude/skills" ] && \
     find "$TARGET/.claude/skills" -maxdepth 1 -lname "*auto-production*" | grep -q .; then
    bold "» re-linking project skills at $TARGET (catches any new skills)"
    local pdest="$TARGET/.claude/skills"
    # remove old symlinks that point into our repo
    find "$pdest" -maxdepth 1 -lname "*$REPO_DIR/skills/*" -delete 2>/dev/null || true
    for s in "$REPO_DIR"/skills/*/; do
      local name; name=$(basename "$s")
      local link="$pdest/$name"
      [ -e "$link" ] || ln -s "$s" "$link"
    done
    ok "$(ls "$pdest" | wc -l) skills linked (incl. any new ones)"
  fi

  # show what changed
  if [ "$before_commit" != "$after_commit" ]; then
    echo
    bold "» commits since update:"
    git -C "$REPO_DIR" log --oneline "${before_commit}..${after_commit}"
  fi
}

uninstall_install() {
  bold "» uninstalling auto-production"

  local user_link="$HOME/.claude/skills/auto-production"
  if [ -L "$user_link" ] || [ -e "$user_link" ]; then
    rm -rf "$user_link"
    ok "removed user-scope $user_link"
  else
    warn "no user-scope install found"
  fi

  if [ -d "$TARGET/.claude/skills" ]; then
    # only remove skills that symlink into our repo
    local removed=0
    for link in "$TARGET/.claude/skills"/*; do
      [ -L "$link" ] || continue
      local target; target=$(readlink "$link")
      if echo "$target" | grep -qE "/auto-production(/|$)|/skills/[^/]+$"; then
        # check if target resolves under any auto-production repo
        if [ -e "$target" ] && \
           realpath "$target" 2>/dev/null | grep -qE "/auto-production/"; then
          rm -f "$link"
          removed=$((removed + 1))
        fi
      fi
    done
    ok "removed $removed project-scope skill symlinks from $TARGET/.claude/skills/"
  fi

  if [ -f "$TARGET/.claude/settings.json.bak" ]; then
    warn "$TARGET/.claude/settings.json was overwritten on install; restore from .bak if desired"
  fi

  if [ -d "$TARGET/.auto-production" ]; then
    warn "$TARGET/.auto-production/ still present — contains your project's audit/cache state; delete manually if desired"
  fi

  if grep -q "AUTO_PRODUCTION_REPO" "$HOME/.bashrc" 2>/dev/null; then
    warn "AUTO_PRODUCTION_REPO export still in ~/.bashrc — remove manually if desired"
  fi

  bold "✅ uninstall done."
}

case "$MODE" in
  user)      install_user ;;
  project)   install_project ;;
  both)      install_user; install_project ;;
  update)    update_install ;;
  uninstall) uninstall_install; exit 0 ;;
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
echo
echo "Maintenance:"
echo "  ./install.sh --update     # git pull + re-link new skills"
echo "  ./install.sh --uninstall  # remove install"
