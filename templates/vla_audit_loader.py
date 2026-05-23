""".auto-production/tools/vla_audit_loader.py — project-specific loader for /vla-audit.

Copy this file to YOUR-PROJECT/.auto-production/tools/vla_audit_loader.py and fill
in the two functions for your stack. The /vla-audit skill resolves the loader
via the 3-layer chain documented in docs/RESOLVER.md.

Contract per /vla-audit SKILL.md Phase 0:
  - module MUST import without raising
  - MUST expose two callables: extract_train(cfg) -> dict, extract_eval(cfg) -> dict
  - both dicts MUST contain exactly these 6 keys (Phase 0 contract):
      'normalization', 'shape', 'dtype', 'collate_src',
      'action_range', 'image_pipeline'
  - body MAY return placeholder/sentinel values at stub stage,
    BUT MUST NOT raise — the test suite asserts presence + shape, not values

Source proven in production: extracted from `vla3d` test project after Stage 5
(see auto-production GitHub commits f1e6e06 + e42efd5).
"""
from __future__ import annotations
from typing import Any

# Keys mandated by /vla-audit SKILL.md Phase 0 contract.
# These mirror the REQUIRED_KEYS set in tests/test_vla_audit_loader.py.
_REQUIRED_KEYS: tuple[str, ...] = (
    "normalization",
    "shape",
    "dtype",
    "collate_src",
    "action_range",
    "image_pipeline",
)

# Sentinel value flag — used at stub stage so /vla-audit Phase 3 diff can
# safely report 'both sides agree on STUB_PENDING' rather than crashing.
# Replace with real introspection in your real implementation.
_STUB_SENTINEL: str = "STUB_PENDING_FILL_ME"


def _placeholder_dict(side: str) -> dict[str, Any]:
    """Return a fully-populated placeholder dict satisfying the 6-key contract.

    `side` is a free-form tag ('train' or 'eval') copied into each field so
    downstream /vla-audit Phase 3 diff can distinguish them even before the
    real loader is filled in.
    """
    base_tag = f"{_STUB_SENTINEL}::{side}"
    return {
        "normalization": {
            "image_mean": base_tag,           # e.g. [0.485, 0.456, 0.406]
            "image_std": base_tag,            # e.g. [0.229, 0.224, 0.225]
            "image_div": base_tag,            # e.g. 255.0 or 127.5 or None
        },
        "shape": {
            "image": base_tag,                # e.g. (B, V, 3, H, W)
            "state": base_tag,                # e.g. (B, S_dim)
            "action": base_tag,               # e.g. (B, T_chunk, A_dim)
        },
        "dtype": {
            "image": base_tag,                # e.g. 'float32' or 'bfloat16'
            "state": base_tag,
            "action": base_tag,
        },
        "collate_src": base_tag,              # function-qualified-name of collate_fn
        "action_range": {
            "low": base_tag,                  # e.g. [-1.0]*A_dim
            "high": base_tag,                 # e.g. [1.0]*A_dim
            "rad_or_unit": base_tag,          # one of {'rad', 'unit', 'metric', 'normalized'}
        },
        "image_pipeline": base_tag,           # ordered list of transform class names
    }


def extract_train(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Pull the 6-key /vla-audit dict from the TRAIN side.

    Real implementation outline:
        1. Resolve cfg (or default to configs/train.yaml; walk any _extends chain)
        2. Build dataset via the same code path as `python train.py`
        3. Sample one batch from collate_fn; introspect:
            - image_mean / image_std / image_div from cfg.data + transforms.Normalize
            - shape / dtype from the sample tensors
            - action_range from cfg.data.action_unnormalize_min/max
            - image_pipeline = [t.__class__.__name__ for t in dataset.transform.transforms]
        4. Return the populated dict.

    Stub: returns _placeholder_dict('train'). Never raises.
    """
    _ = cfg  # silence unused-arg warnings
    return _placeholder_dict("train")


def extract_eval(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Pull the 6-key /vla-audit dict from the EVAL side.

    Real implementation outline:
        1. Resolve cfg (or default to configs/eval.yaml)
        2. Build the eval env via your project's eval entrypoint
        3. Introspect the env's observation/action transforms; capture every
           field the train side captured, in the same shape.
        4. Return the populated dict.

    Stub: returns _placeholder_dict('eval'). Never raises.
    """
    _ = cfg
    return _placeholder_dict("eval")


# ---------------------------------------------------------------------------
# Self-validation helper — invoked by /vla-audit before its own Phase 1.
# ---------------------------------------------------------------------------

def self_check() -> tuple[bool, list[str]]:
    """Return (ok, missing_keys_per_side). Used by /vla-audit to refuse
    running with a malformed loader rather than silently diffing missing keys.
    """
    issues: list[str] = []
    for side, fn in (("train", extract_train), ("eval", extract_eval)):
        try:
            out = fn(cfg={})
        except Exception as e:  # contract: must not raise
            issues.append(f"{side}: raised {type(e).__name__}: {e}")
            continue
        if not isinstance(out, dict):
            issues.append(f"{side}: expected dict, got {type(out).__name__}")
            continue
        missing = set(_REQUIRED_KEYS) - set(out.keys())
        if missing:
            issues.append(f"{side}: missing keys {sorted(missing)}")
    return (not issues, issues)


if __name__ == "__main__":
    ok, issues = self_check()
    if ok:
        print(f"vla_audit_loader self_check: PASS (6/6 keys both sides; sentinel={_STUB_SENTINEL})")
    else:
        for i in issues:
            print(f"FAIL: {i}")
        raise SystemExit(1)
