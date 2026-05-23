"""templates/verify_external_ref.py — fail-loud runtime verifier for external refs.

Copy into your project and adapt per `/arch-plan` SKILL.md guidance.

Pattern: every external ref (third-party line#, API signature, env var,
module path) in your arch_plan gets ONE verify function. Called at __init__
or setup() time — BEFORE the first real use — so drift between WebFetch
research time and real install time fails loudly with a fix hint.

Source proven in vla3d: arch_plan said lerobot pi05 denoise_step at line
~1130, actual was line 871 in v0.5.2. A verify hook would have caught the
259-line drift before any monkey-patch.
"""
from __future__ import annotations
from typing import Any, Iterable
import inspect
import warnings


def verify_callable_exists(module: Any, attr: str, *, fix_hint: str = "") -> None:
    """Assert that `module.attr` exists and is callable; fail-loud with hint."""
    obj = getattr(module, attr, None)
    if obj is None:
        raise AssertionError(
            f"{module.__file__}: missing callable `{attr}`. "
            f"{fix_hint}".rstrip()
        )
    if not callable(obj):
        raise AssertionError(
            f"{module.__file__}.{attr} is not callable (got {type(obj).__name__}). "
            f"{fix_hint}".rstrip()
        )


def verify_callable_body_contains(
    module: Any,
    attr: str,
    sentinels: Iterable[str],
    *,
    fix_hint: str = "",
) -> None:
    """Assert that `module.attr`'s source body contains all sentinel substrings.

    Use this to detect upstream refactors. The sentinels are 'must-have' tokens
    you depend on (function calls, attribute names, etc.). If any is missing,
    the function has likely been refactored and your plan is stale.
    """
    fn = getattr(module, attr, None)
    if fn is None:
        raise AssertionError(f"{module.__file__}: missing `{attr}`. {fix_hint}".rstrip())
    try:
        src, lineno = inspect.getsourcelines(fn)
    except (OSError, TypeError) as e:
        warnings.warn(f"cannot inspect source of {attr}: {e}")
        return
    body = "".join(src)
    missing = [s for s in sentinels if s not in body]
    if missing:
        raise AssertionError(
            f"{module.__file__}.{attr} (line {lineno}) is missing sentinel(s) "
            f"{missing}. Upstream likely refactored — re-read source + update arch_plan. "
            f"{fix_hint}".rstrip()
        )


def verify_callable_signature(
    module: Any,
    attr: str,
    expected_params: Iterable[str],
    *,
    fix_hint: str = "",
) -> None:
    """Assert that `module.attr` accepts exactly `expected_params` (positional or keyword)."""
    fn = getattr(module, attr, None)
    if fn is None:
        raise AssertionError(f"{module.__file__}: missing `{attr}`. {fix_hint}".rstrip())
    try:
        sig = inspect.signature(fn)
    except (ValueError, TypeError) as e:
        warnings.warn(f"cannot get signature of {attr}: {e}")
        return
    actual = set(sig.parameters)
    expected = set(expected_params)
    missing = expected - actual
    extra = actual - expected - {"self", "cls", "args", "kwargs"}
    if missing or extra:
        raise AssertionError(
            f"{module.__file__}.{attr} signature mismatch. "
            f"missing={sorted(missing)} extra={sorted(extra)}. {fix_hint}".rstrip()
        )


def verify_env_var(name: str, *, allow_empty: bool = False,
                   must_match_prefix: str | None = None,
                   fix_hint: str = "") -> str:
    """Read env var, fail-loud if absent or wrong shape. Returns value."""
    import os
    val = os.environ.get(name)
    if val is None or (not allow_empty and not val):
        raise AssertionError(
            f"env var {name} is unset/empty. {fix_hint}".rstrip()
        )
    if must_match_prefix and not val.startswith(must_match_prefix):
        raise AssertionError(
            f"env var {name}={val!r} does not start with required prefix "
            f"{must_match_prefix!r}. {fix_hint}".rstrip()
        )
    return val


def verify_path_exists(path: str, *, fix_hint: str = "") -> None:
    """Fail-loud if filesystem path missing (typical: dataset / ckpt / mount point)."""
    from pathlib import Path
    if not Path(path).exists():
        raise AssertionError(
            f"required path {path!r} does not exist. {fix_hint}".rstrip()
        )


# ---------------------------------------------------------------------------
# Example usage — copy + adapt this block to YOUR-PROJECT/src/setup_hook.py
# ---------------------------------------------------------------------------

def verify_all_external_refs() -> None:
    """Run all verify hooks at __init__ / setup time. Crash loudly on drift.

    Adapt this list for your project.
    """
    # Example: lerobot pi05 denoise_step (vla3d case)
    # from lerobot.policies.pi05.modeling_pi05 import PI05Pytorch
    # verify_callable_exists(
    #     PI05Pytorch, "denoise_step",
    #     fix_hint="lerobot may have renamed; regenerate arch_plan §3.1",
    # )
    # verify_callable_body_contains(
    #     PI05Pytorch, "denoise_step",
    #     sentinels=["embed_suffix", "paligemma_with_expert.forward", "outputs_embeds[1]"],
    #     fix_hint="lerobot refactored — update src/pi05_wrapper._patched_denoise_step",
    # )

    # Example: HF_HOME env var (vla3d hot-list)
    # verify_env_var("HF_HOME", must_match_prefix="/data4/",
    #                fix_hint="export HF_HOME=/data4/hf_cache before launching train.py")

    # Example: dataset path
    # verify_path_exists("/data4/datasets/libero/",
    #                    fix_hint="run docs/DEPLOYMENT.md §2 to mount/download LIBERO")

    pass


if __name__ == "__main__":
    verify_all_external_refs()
    print("✅ all external refs verified")
