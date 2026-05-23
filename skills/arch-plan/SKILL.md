---
name: arch-plan
description: "大改动 (>3 文件) 之前先画依赖图 + 改动计划，确认后再动手。**所有外部 ref（line# / API / partition / env var）必须配 _verify 守门函数 runtime fail-loud**，不能盲信 WebFetch 结果。Use when user says \"arch plan\", \"改动计划\", \"画依赖图\", \"重构前\", \"big change\", \"多文件改\", \"先规划\", \"monkey patch\", \"插入点\"."
argument-hint: "[--files file1,file2,...] [--goal '...']"
allowed-tools: Bash(*), Read, Write, Grep, Glob, Agent
---

# /arch-plan — Multi-File Architecture Plan + External-Ref Verification

> 借鉴 AutoResearchClaw CodeAgent v2。METHOD gate 软前置。
> v2 (2026-05) 加 **WebFetch-drift 守门要求**——vla3d 实战发现 cc WebFetch 出来的
> lerobot line# (~1130) 跟真实 (871) 差 259 行，没守门直接成 silent bug。

## Overview

任何改动涉及 >3 文件，强制先：

1. 列待改文件 + 每个 file:line 计划改动
2. 画依赖图（who-calls-who，谁会被牵动）
3. **每条外部引用（line# / API / module path / env / partition / weight URL）必须配 runtime 守门**
4. emit Markdown 计划 → AskUserQuestion 是否 approve
5. approve 后才允许 Edit / Write

## When to Use

- 任何 monkey-patch、跨 repo 改动、改动 ≥3 文件
- 引用外部 codebase 具体 line# / 函数 / API（WebFetch 来的）
- 涉及外部资源标识（slurm partition / conda env / wandb project / HF repo）

## Critical principle — WebFetch drift kills

Agent 用 WebFetch 拿 GitHub URL 看具体 line# 是常见但 **危险** 操作：

- WebFetch 抓的可能是默认分支 master/main，但用户机器装的版本可能是 0.5.2 或 fork
- GitHub URL 路径 `/blob/main/foo.py#L1130` 的 line# 跟用户实际安装的 line# 大概率漂
- 一处漂全 plan 漂——arch_plan 里每个数字都是潜在炸弹

**vla3d 案例**：arch_plan 9 处引用 `modeling_pi05.py::denoise_step ~line 1130`，
真实是 line 871。差 259 行。如果没在 stub 里写 `_verify_patch_site()` 守门，部署
hpcc 后 monkey-patch 会 silently patch 错位置（最坏 case patch 到完全无关函数）。

**强制规则**：

```
所有外部 ref 必须配一个 runtime `_verify_<thing>()` 函数，
在第一次实际调用前 assert，fail 时大声崩 + 提供修复线索。
```

## Workflow

### Phase 1 — collect改动 files

```bash
# Glob + Grep 找待改 + 调用关系
find . -name '*.py' | xargs grep -l '<symbol>'
```

### Phase 2 — emit plan with verify hooks

每条计划必须含 4 字段：

```
File: <path>:<line-guess>
Change: <what>
External refs:
  - lerobot.policies.pi05.modeling_pi05::denoise_step (line ~871 in v0.5.2)
  - paligemma_with_expert.forward (signature: inputs_embeds=[None, suffix_embs])
Verify hook: _verify_denoise_step_signature() asserts def 存在 & 接受 4 args & body 含 "embed_suffix"
```

### Phase 3 — write verify stub for every external ref

通常一个 `<package>_verify.py` 或 inline `_verify_*()` 函数。模板见
`templates/verify_external_ref.py`。

每个 verify 函数返回：

- `True` / silently → pass
- `raise AssertionError("expected X at line ~Y, got Z; lerobot may have upgraded — re-grep ...")` → fail-loud

放在 `__init__` 或 `setup_hook` 的第一行，**不能延后**。

### Phase 4 — AskUserQuestion approve

```
计划 + 11 个外部 ref + 11 个对应 verify 都写好。
PROCEED / EDIT_PLAN / ABORT?
```

### Phase 5 — write arch_plan.md + audit trace

```bash
echo "{...}" > .auto-production/audit/arch_plan.approved
cp arch_plan.md .auto-production/arch_plan_$(date +%Y%m%d).md
```

## Output

- `docs/arch_plan.md`（main artifact，每个 verify 函数 link 到 SKILL.md）
- `.auto-production/audit/arch_plan.approved`
- `.auto-production/arch_plan_<date>.md`（versioned copy）

## Verify hook 模板（关键）

```python
def _verify_denoise_step_site(lerobot_module) -> None:
    """Fail-loud check that lerobot pi05 hasn't drifted from our assumed structure.

    Run this BEFORE any monkey-patch. If lerobot upgrades and shifts/renames
    things, we want to crash with a clear hint, not silently patch the wrong line.
    """
    import inspect
    fn = getattr(lerobot_module, "denoise_step", None)
    if fn is None:
        raise AssertionError(
            f"lerobot {lerobot_module.__file__}: denoise_step not found. "
            f"lerobot may have renamed/removed this method — regenerate arch_plan."
        )
    src, lineno = inspect.getsourcelines(fn)
    body = "".join(src)
    # Sentinel substrings that MUST exist:
    for sentinel in ["embed_suffix", "paligemma_with_expert.forward", "outputs_embeds[1]"]:
        if sentinel not in body:
            raise AssertionError(
                f"lerobot denoise_step body missing sentinel `{sentinel}` "
                f"(found at line {lineno}). lerobot likely upgraded — re-read source."
            )
    # Soft sanity on line range
    if not (700 <= lineno <= 1000):
        import warnings
        warnings.warn(
            f"denoise_step at line {lineno}, expected ~700-1000. "
            f"Not fatal but worth re-checking arch_plan numbers."
        )
```

放在 `pi05_wrapper.__init__` 或 `setup()` 调用：

```python
class Pi05With3DGaussians:
    def __init__(self, ...):
        from lerobot.policies.pi05 import modeling_pi05
        _verify_denoise_step_site(modeling_pi05.PI05Pytorch)  # <-- fail-loud here
        ...
```

## Composition

- 前置：`/idea-perspective` + `/sprint-contract --sign`（明确方向）
- 后置：`/ast-validate` + METHOD gate 可选检查 `arch_plan.approved`
- 联动：每个 verify 函数应在 `tests/test_external_refs.py` 单测覆盖（即使无 GPU 也可跑 isinstance / source-inspect check）

## Failure modes

| 现象 | 处理 |
|---|---|
| WebFetch line# 跟真实差 N 行 | verify 函数报警 + 给修复线索；driver 用 `/driver-findings` 跟 sub-agent reconcile |
| 外部 ref API rename | verify fail-loud，sub-agent 重新 inspect source 重写 plan |
| sub-agent 嫌 verify 麻烦想跳过 | METHOD gate 拒绝放行无 verify 的 arch_plan |
| verify 函数本身 wrong（false fail） | 单测覆盖 + driver 一次性 patch（不 silently disable） |

## Real example sentinel-pattern (from vla3d)

```yaml
external_refs:
  lerobot_pi05_denoise_step:
    path: lerobot/policies/pi05/modeling_pi05.py
    symbol: PI05Pytorch.denoise_step
    line_at_time_of_plan: 871         # lerobot 0.5.2; verify hook checks symbol presence not line
    body_sentinels: ["embed_suffix", "paligemma_with_expert.forward", "outputs_embeds[1]"]
    verify_function: src.pi05_wrapper._verify_denoise_step_site
    fallback: "if verify fails — abort init, write FAIL message containing actual line + body excerpt"
```
