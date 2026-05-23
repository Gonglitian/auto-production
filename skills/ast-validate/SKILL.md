---
name: ast-validate
description: "写完代码先用 AST parser 做静态分析（import 完整性、签名匹配、未定义符号），过了才执行。防 \"跑了 30 秒才发现 ImportError\"。Use when user says \"ast validate\", \"静态分析\", \"先检查\", \"语法检查\", \"import 验证\", \"static check\"."
argument-hint: "[--files file1.py,file2.py] [--strict]"
allowed-tools: Bash(*), Read, Write, Grep
---

# /ast-validate — Pre-Execution AST Sanity

> 借鉴 AutoResearchClaw CodeAgent v2。METHOD gate 前置。

## Overview

对刚改 / 刚写的 Python 文件跑：

| 检查 | 工具 |
|---|---|
| Syntax | `python -m py_compile` |
| Unresolved names | `ast.parse` + 自定义 walker（找未 import 也未定义的 Name） |
| Signature consistency | 跨文件 grep call site `foo(...)` vs `def foo(...)` 参数数对得上 |
| Import correctness | `import X` 后 `X.member` 真存在（基础 introspection） |

任何 fail → 报 file:line + 拒绝运行该文件。

## Workflow

```bash
# 简化版
for f in $files; do
  python -m py_compile "$f" || exit 1
  python3 tools/ast_walker.py "$f" >> .auto-production/audit/ast_diff.txt
done
[ -s .auto-production/audit/ast_diff.txt ] && exit 1
touch .auto-production/audit/ast_validate.passed
```

## Output

- `.auto-production/audit/ast_validate.passed`（pass 后）
- `.auto-production/audit/ast_diff.txt`（fail 后人审）

## Composition

前置：刚 Edit/Write 完任何 .py 文件
后置：METHOD gate 可检查 ast_validate.passed
