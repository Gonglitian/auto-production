# RESOLVER.md — Helper 3-Layer Resolver Chain

> 借鉴 ARIS 的 strict-safe 3-layer resolver（见 ARIS `shared-references/integration-contract.md`）。

## 为什么需要

SKILL.md 写 `python3 tools/promise_check.py` 时，到底跑哪个 `tools/`？取决于：

- 用户当前 project 是否有 override？
- 仓库本身的 tools/ 是否还在（开发环境）？
- 全局安装是否齐备？

3-layer fallback 让 skill 在所有场景都能找到 helper：

## 查找顺序

```
1. .auto-production/tools/<name>     # project-local override (highest priority)
2. tools/<name>                       # repo-local (most common in dev)
3. $AUTO_PRODUCTION_REPO/tools/<name> # global install (when symlinked)
```

## SKILL.md 内 invoke 规范

```bash
# 推荐写法：用 AUTO_PRODUCTION_REPO env var 兜底
TOOL=$(
  for p in .auto-production/tools/promise_check.py \
           tools/promise_check.py \
           "$AUTO_PRODUCTION_REPO/tools/promise_check.py"; do
    [ -f "$p" ] && { echo "$p"; break; }
  done
)
python3 "$TOOL" "$@"
```

或更简单（在仓库或 install 完整时）：

```bash
python3 tools/promise_check.py "$@"
```

## Failure policies

| 状况 | 行为 |
|---|---|
| 任一 layer 找到 | 用该 layer，不继续找 |
| 全找不到 | exit 2 + 错误信息「`promise_check.py` not found in resolver chain」 |
| 多 layer 都有但版本不同 | 用最高优先级（Layer 1） |

## 何时该 override 到 .auto-production/tools/

- `vla_audit_loader.py` —— 每个 project 的 loader 不同（dataset shape 不同），**必须**在 Layer 1 写自己的
- 临时 patch 上游 bug（先在 project 内改，再 PR 回上游）

## 与 ARIS 的差异

| 维度 | ARIS | auto-production |
|---|---|---|
| Layer 名 | `.aris/tools/` → `tools/` → `$ARIS_REPO/tools/` | `.auto-production/tools/` → `tools/` → `$AUTO_PRODUCTION_REPO/tools/` |
| 失败策略 | 5 种 (A/B/C/D1/D2/E)，advisory CI lint 检查 | 简化版 3 种 |
| Cache 位置 | `$ARIS_CACHE_DIR/skills/<name>/scripts/` 作为 Layer 0b | 暂未实现 |
