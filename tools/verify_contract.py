#!/usr/bin/env python3
"""tools/verify_contract.py — validate sprint_contract.yaml.

Two modes:
  --verify  (default)  : 5 required fields + threshold/seed lint
  --check-refs         : validate external refs in `validators:` block
                          (partition, conda env, HF repo, wandb, pkg version, arxiv)

Pure stdlib only (urllib for HF / arxiv / wandb HEAD checks).
"""
import argparse, json, os, re, ssl, subprocess, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

REQUIRED = ["goal", "scope", "metric", "verify", "guard"]
MIN_CHARS = 30
THRESHOLD_RE = re.compile(r"[<>≤≥]=?\s*\d|\d+\s*%|\d+\.\d+")
SEED_RE = re.compile(r"seed|baseline|run_0|run-0|run zero", re.IGNORECASE)
UA = "auto-production-verify-contract/0.1"

# Strip a ` # comment` suffix while preserving #s inside quoted segments.
# Conservative: only strip if there's a space-then-# pattern and no quote
# follows on the same line.
_INLINE_COMMENT = re.compile(r"\s+#(?!.*[\"\']).*$")

def _strip_inline_comment(s):
    return _INLINE_COMMENT.sub("", s).rstrip()

def _clean_value(v):
    return _strip_inline_comment(v).strip().strip('"').strip("'")


# ---------------------------------------------------------------------------
# YAML mini-parser (we already used this; extended to support `- ` lists and
# nested key blocks for the validators: section)
# ---------------------------------------------------------------------------

def parse_yaml(text):
    """Tiny YAML reader. Supports:
       - top-level scalars and pipe-multilines
       - one level of nested mappings (key: {subkey: val, ...})
       - 'validators:' list of dicts (each item starts with '- type: ...')
    """
    out, key, buf = {}, None, []
    in_validators = False
    validators = []
    cur_v = None

    def flush_field():
        nonlocal key, buf
        if key is not None and not in_validators:
            out[key] = "\n".join(buf).strip()

    for line in text.splitlines():
        raw = line.rstrip("\n")
        stripped = raw.strip()

        if stripped.startswith("#") or not stripped:
            if in_validators and cur_v is None:
                continue
            if not in_validators:
                if key is not None:
                    buf.append(raw)
            continue

        # validators block detection
        if re.match(r"^validators\s*:\s*$", raw) and not raw.startswith(" "):
            flush_field()
            in_validators = True
            key = None
            continue

        if in_validators:
            # end of validators block?
            if not raw.startswith(" ") and ":" in raw and not raw.lstrip().startswith("-"):
                # next top-level key
                if cur_v is not None:
                    validators.append(cur_v); cur_v = None
                in_validators = False
                # fall through to handle the new top-level key below
            else:
                m_item = re.match(r"^\s*-\s+(\w+)\s*:\s*(.+)$", raw)
                m_field = re.match(r"^\s+(\w+)\s*:\s*(.+)$", raw)
                if m_item:
                    if cur_v is not None:
                        validators.append(cur_v)
                    cur_v = {m_item.group(1): _clean_value(m_item.group(2))}
                elif m_field and cur_v is not None:
                    cur_v[m_field.group(1)] = _clean_value(m_field.group(2))
                continue

        # top-level scalar
        m = re.match(r"^([a-z_][a-z0-9_]*)\s*:\s*(.*)$", raw)
        if m and not raw.startswith(" "):
            flush_field()
            key = m.group(1)
            val = _clean_value(m.group(2))
            buf = [val] if val and val != "|" else []
        elif raw.startswith(" "):
            if key is not None and not in_validators:
                buf.append(raw)

    flush_field()
    if cur_v is not None:
        validators.append(cur_v)
    out["__validators__"] = validators
    return out


# ---------------------------------------------------------------------------
# Mode 1: --verify (existing functionality, preserved)
# ---------------------------------------------------------------------------

def run_verify(path):
    data = parse_yaml(path.read_text())
    errors, warns = [], []

    for field in REQUIRED:
        v = data.get(field, "")
        if not v:
            errors.append(f"missing field: {field}"); continue
        if len(v) < MIN_CHARS:
            errors.append(f"{field}: too short ({len(v)} < {MIN_CHARS})")

    if "guard" in data and not THRESHOLD_RE.search(data["guard"]):
        errors.append("guard: must contain a measurable threshold (e.g., 'SR<60%', 'loss>2.0')")
    if "verify" in data and not SEED_RE.search(data["verify"]):
        warns.append("verify: consider multi-seed verification (mention 'seed' or 'baseline')")

    for w in warns:
        print(f"⚠️  {w}")
    if errors:
        print("❌ CONTRACT INVALID:")
        for e in errors: print(f"   - {e}")
        return 1
    print("✅ contract valid")
    return 0


# ---------------------------------------------------------------------------
# Mode 2: --check-refs (new in v2)
# ---------------------------------------------------------------------------

def _http_head(url, timeout=8):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    ctx = ssl.create_default_context()
    return urllib.request.urlopen(req, timeout=timeout, context=ctx).status

def _http_get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read()

def verify_partition(entry):
    """{type: partition, name: gpu, host: hpcc (optional)}

    Uses `sinfo -h -p NAME` (no -o so we avoid quote-escaping through ssh).
    Then explicitly check that at least one row's first column matches NAME —
    sinfo prints the header anyway on some versions, so non-empty stdout is
    not enough.
    """
    name = entry.get("name")
    host = entry.get("host") or ""
    if not name:
        return False, "partition: missing 'name'"
    # Use full sinfo (default columns) so we don't fight quote-escaping through ssh.
    cmd = (["ssh", host] if host else []) + ["bash", "-l", "-c", f"sinfo -p {name} 2>&1"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout
    except Exception as e:
        return False, f"partition {name}@{host or 'local'}: {type(e).__name__}: {e}"

    # sinfo's first column is PARTITION; rows where that column starts with
    # the requested name are the proof. Header rows start with 'PARTITION'.
    rows = []
    for line in out.splitlines():
        line = line.strip()
        if not line or line.upper().startswith("PARTITION"):
            continue
        first_col = line.split()[0] if line.split() else ""
        # strip default-partition asterisk: "gpu*" -> "gpu"
        if first_col.rstrip("*") == name:
            rows.append(line)
    if not rows:
        # sinfo may print 'Unable to find partition' to stderr; surface that
        err_hint = ""
        for line in out.splitlines():
            if "partition" in line.lower() and ("not exist" in line.lower() or "unable" in line.lower()):
                err_hint = " (" + line.strip() + ")"; break
        return False, f"partition {name}@{host or 'local'}: no matching row{err_hint}"
    return True, f"partition {name}@{host or 'local'}: {len(rows)} row(s) — {rows[0][:80]}"

def verify_conda_env_path(entry):
    """{type: conda_env, path: /full/path/to/env, host: hpcc (optional)}"""
    path = entry.get("path")
    host = entry.get("host") or ""
    if not path:
        return False, "conda_env: missing 'path'"
    cmd = (["ssh", host] if host else []) + ["bash", "-l", "-c", f"[ -x {path}/bin/python ] && {path}/bin/python --version 2>&1"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except Exception as e:
        return False, f"conda env {path}@{host or 'local'}: {type(e).__name__}: {e}"
    if r.returncode != 0:
        return False, f"conda env {path}@{host or 'local'}: python missing or not executable"
    return True, f"conda env {path}@{host or 'local'}: {r.stdout.strip()}"

def verify_hf_repo(entry):
    """{type: hf_repo, id: org/model, kind: model|dataset (default model)}"""
    rid = entry.get("id")
    kind = entry.get("kind", "model")
    if not rid:
        return False, "hf_repo: missing 'id'"
    base = "https://huggingface.co"
    url = f"{base}/api/{kind}s/{urllib.parse.quote(rid, safe='/')}"
    try:
        body = _http_get(url)
        d = json.loads(body)
        return True, f"hf {kind} {rid}: ok (downloads={d.get('downloads','?')})"
    except urllib.error.HTTPError as e:
        return False, f"hf {kind} {rid}: HTTP {e.code}"
    except Exception as e:
        return False, f"hf {kind} {rid}: {type(e).__name__}: {e}"

def verify_wandb_project(entry):
    """{type: wandb_project, entity: my-team, project: my-proj}"""
    ent, proj = entry.get("entity"), entry.get("project")
    if not (ent and proj):
        return False, "wandb_project: need entity + project"
    url = f"https://wandb.ai/{urllib.parse.quote(ent)}/{urllib.parse.quote(proj)}"
    try:
        code = _http_head(url)
        return code < 400, f"wandb {ent}/{proj}: HTTP {code}"
    except urllib.error.HTTPError as e:
        return False, f"wandb {ent}/{proj}: HTTP {e.code}"
    except Exception as e:
        return False, f"wandb {ent}/{proj}: {type(e).__name__}: {e}"

def verify_pkg_version(entry):
    """{type: pkg_version, pkg: lerobot, expected: 0.5.2, conda_env_path: (optional)}"""
    pkg = entry.get("pkg"); expected = entry.get("expected")
    env_path = entry.get("conda_env_path") or entry.get("env_path") or ""
    host = entry.get("host") or ""
    if not pkg:
        return False, "pkg_version: missing 'pkg'"
    py = f"{env_path}/bin/python" if env_path else "python3"
    code = f"import {pkg}; print(getattr({pkg}, '__version__', 'unknown'))"
    cmd = (["ssh", host] if host else []) + ["bash", "-l", "-c", f"{py} -c \"{code}\" 2>&1"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except Exception as e:
        return False, f"pkg {pkg}: {type(e).__name__}: {e}"
    got = (r.stdout or r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr).strip() else ""
    if r.returncode != 0:
        return False, f"pkg {pkg}: import failed — {got}"
    if expected and got != expected:
        return False, f"pkg {pkg}: expected {expected}, got {got}"
    return True, f"pkg {pkg}: {got}"

def verify_arxiv_id(entry):
    """{type: arxiv, id: 2410.24164}"""
    arxid = entry.get("id")
    if not arxid:
        return False, "arxiv: missing 'id'"
    url = f"https://arxiv.org/abs/{arxid}"
    try:
        code = _http_head(url)
        return code == 200, f"arxiv {arxid}: HTTP {code}"
    except urllib.error.HTTPError as e:
        return False, f"arxiv {arxid}: HTTP {e.code}"
    except Exception as e:
        return False, f"arxiv {arxid}: {type(e).__name__}: {e}"

VALIDATORS = {
    "partition":     verify_partition,
    "conda_env":     verify_conda_env_path,
    "hf_repo":       verify_hf_repo,
    "wandb_project": verify_wandb_project,
    "pkg_version":   verify_pkg_version,
    "arxiv":         verify_arxiv_id,
}

def run_check_refs(path):
    data = parse_yaml(path.read_text())
    validators = data.get("__validators__") or []
    if not validators:
        print("ℹ️  no `validators:` block in contract — nothing to check")
        print("   add a validators: section per templates/sprint_contract.yaml v2")
        return 0
    n_fail = 0
    for entry in validators:
        t = entry.get("type")
        fn = VALIDATORS.get(t)
        if not fn:
            print(f"⚠️  unknown validator type: {t!r}; supported: {list(VALIDATORS)}")
            continue
        ok, msg = fn(entry)
        if ok:
            print(f"  ✓ {msg}")
        else:
            print(f"  ✗ {msg}")
            n_fail += 1
    if n_fail:
        print(f"\n❌ {n_fail} ref(s) failed — fix before /sprint-contract --sign")
        return 1
    print("\n✅ all external refs valid")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", help="path to sprint_contract.yaml")
    ap.add_argument("--verify", action="store_true", default=True,
                    help="run field/threshold/seed checks (default)")
    ap.add_argument("--check-refs", action="store_true",
                    help="validate external refs in `validators:` block")
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        sys.exit(f"❌ {p} not found")

    if args.check_refs:
        sys.exit(run_check_refs(p))
    sys.exit(run_verify(p))

if __name__ == "__main__":
    main()
