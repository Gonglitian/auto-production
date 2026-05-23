#!/bin/bash
# tools/resubmit_pipeline.sh — port a polished paper to a new venue.
# Text-only edits, bib frozen, framework unchanged.
set -u
SRC=${1:?need source paper dir}
TO=${TO_VENUE:?need TO_VENUE env}
FROM=${FROM_VENUE:-source}
NEW="paper-${TO}"

[ -d "$NEW" ] && { echo "❌ $NEW already exists — refusing to overwrite"; exit 1; }
echo "== phase 0: physical isolation =="
cp -r "$SRC" "$NEW"
echo "  ✓ copied $SRC → $NEW"

echo "== phase 1: 5-layer anonymity check =="
issues=0
for pat in 'author' 'thanks' 'acknowledg' 'github\.com' 'corresponding'; do
  hits=$(grep -rni "$pat" "$NEW" --include='*.tex' --include='*.bib' 2>/dev/null | wc -l)
  [ "$hits" -gt 0 ] && { echo "  ⚠️  '$pat' appears $hits time(s)"; issues=$((issues+1)); }
done
[ $issues -gt 0 ] && echo "  → user must redact above before phase 2"

echo "== phase 2: audits --soft-only =="
echo "  → run /citation-audit --soft-only inside $NEW"

echo "== phase 3: microedits =="
cat > "$NEW/RESUBMIT_REPORT.json" <<EOF
{
  "from": "$FROM",
  "to": "$TO",
  "started_at": "$(date -Iseconds)",
  "edit_whitelist": ["sections/*.tex", "abstract.tex"],
  "forbidden": ["references.bib", "configs/", "code/"],
  "anonymity_issues_found": $issues
}
EOF
echo "  ✓ wrote $NEW/RESUBMIT_REPORT.json"

echo "== phase 4-5: adversarial gate + compile =="
echo "  → run /kill-argument on main claims"
echo "  → finally: cd $NEW && pdflatex main.tex"
