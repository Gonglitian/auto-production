---
name: sync-to-remote
description: "把本地 project 推到远程 compute host（hpcc / bcc / tasl-labserver）+ 远端 bootstrap auto-production framework + 验证 stubs import 通。给 driver 用，跟 /cross-host-sync (run sync) 互补——后者管 run state，本 skill 管 code state。Use when user says \"sync to remote\", \"部署到 hpcc\", \"推到集群\", \"rsync project\", \"远程跑\", \"hpcc 上验证\", \"deploy 上去\"."
argument-hint: "[--target hpcc|bcc|tasl-labserver|<host>] [--remote-path /path] [--dry-run] [--verify]"
allowed-tools: Bash(*), Read, Write
---

# /sync-to-remote — Deploy Project Code to Remote Compute Host

> 实战由来：vla3d hpcc deploy round 3。10 分钟 rsync + bootstrap + verify probe
> 跑通后立刻抓到 9 处 stale line# + 1 个 import bug，省了一周盲打。

## Overview

3 步：

1. **Push code**：rsync local project → remote
2. **Bootstrap framework**：远端 git pull auto-production + 重 link `.claude/skills/`
3. **Verify**：跑 probe script 验 env / imports / SKILL.md 可用

跟 `/cross-host-sync` 互补：
- `/cross-host-sync`：管 **run state**（哪台跑了 wandb run id 啥）
- `/sync-to-remote`：管 **code state**（哪台有最新 commit）

## When to Use

- driver 写完 stubs，要去 hpcc 真启训前 sanity check
- 多机器协作（local 写 / hpcc 跑 / bcc 备份）
- 远程环境跟本地不一致（dep version / 路径 / GPU）
- `/research-pipeline` Stage 5 之前，Stage 4 末尾必跑（验证 env-readiness）

## Constants

- **DEFAULT_HOST** = `hpcc`（用户 ~/.ssh/config alias）
- **DEFAULT_REMOTE_PATH** = `${HOME_ON_REMOTE}/proj/<project-name>` 或 `/bigdata/<lab>/<user>/proj/<project-name>`
- **EXCLUDE** = `__pycache__/`, `*.pyc`, `.venv/`, `runs/`, `.driver_findings_*`
- **AUTO_PRODUCTION_REPO_PATH_ON_REMOTE** = 通常 `~/proj/auto-production` 或 lab-shared 路径

## Workflow

### Phase 1 — push code (rsync)

```bash
PROJECT_NAME=${PROJECT_NAME:-$(basename "$(pwd)")}
HOST=${HOST:-hpcc}
REMOTE_PATH=${REMOTE_PATH:-/bigdata/jlilab/lgong024/proj/${PROJECT_NAME}}

rsync -avzP --delete \
  --exclude '__pycache__' --exclude '*.pyc' \
  --exclude '.venv/' --exclude 'runs/' \
  --exclude '.driver_findings_*.md' \
  ./ ${HOST}:${REMOTE_PATH}/
```

注意 `--delete` 删远端多余文件——若 sub-agent 在远端 commit 过别的东西会丢。建议
第一次 deploy 用 `--delete`，后续增量 sync 去掉。

### Phase 2 — bootstrap auto-production framework on remote

```bash
ssh ${HOST} bash -lc '
set -e
REPO_PATH=${AUTO_PRODUCTION_REMOTE_PATH:-/bigdata/jlilab/lgong024/proj/auto-production}
PROJECT_PATH='${REMOTE_PATH}'

if [ ! -d "$REPO_PATH" ]; then
  git clone --depth 1 https://github.com/Gonglitian/auto-production.git "$REPO_PATH"
else
  cd "$REPO_PATH" && git pull --ff-only
fi

cd "$PROJECT_PATH"
rm -rf .claude/skills && mkdir -p .claude/skills
for s in "$REPO_PATH"/skills/*/; do
  ln -s "$s" .claude/skills/$(basename "$s")
done
cp "$REPO_PATH/templates/settings.json" .claude/settings.json
mkdir -p .auto-production/{audit,cache/citations,meta_opt,baseline}
echo "export AUTO_PRODUCTION_REPO=$REPO_PATH" > .auto-production/.env

echo "skills linked: $(ls .claude/skills | wc -l)"
'
```

### Phase 3 — verify probe

写一个 probe 脚本验 env 真就绪：

```bash
cat > /tmp/${PROJECT_NAME}_probe.sh <<'EOF'
#!/bin/bash
set -u
cd /bigdata/jlilab/lgong024/proj/${PROJECT_NAME}
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ${CONDA_ENV_PATH:-/bigdata/jlilab/<lab>/<user>/.conda/envs/<env>}

echo === env ===
python -c "import sys; print('python', sys.version.split()[0])"
python -c "import torch; print('torch', torch.__version__, torch.version.cuda)" 2>&1 | head -1

echo === skill count ===
ls .claude/skills | wc -l

echo === stub imports ===
python -c "
import sys; sys.path.insert(0, 'src')
for mod in ['<your_stubs>']:
    try: __import__(mod); print(mod, ': OK')
    except Exception as e: print(mod, ': FAIL', type(e).__name__)
"

echo === vla_audit_loader self_check ===
[ -f .auto-production/tools/vla_audit_loader.py ] && python -c "
import sys; sys.path.insert(0, '.auto-production/tools')
import vla_audit_loader as v
ok, issues = v.self_check()
print('ok:', ok)
[print(' -', i) for i in issues]
"
EOF

scp /tmp/${PROJECT_NAME}_probe.sh ${HOST}:/tmp/
ssh ${HOST} bash -l /tmp/${PROJECT_NAME}_probe.sh
```

### Phase 4 — collect findings

probe 输出里任何 FAIL / 异常 → driver 写 `.driver_findings_<round>_<context>.md`
（见 `/driver-findings` skill）反喂 sub-agent。

## Output

- 远端 `${REMOTE_PATH}/` 完整 mirror
- 远端 `.claude/skills/` 55+ 符号链接
- 远端 `.auto-production/.env` 含 `AUTO_PRODUCTION_REPO=` export
- 本地 `/tmp/<project>_probe.sh` 复用模板
- 本地 `.driver_findings_*.md`（如有 finding）

## Failure modes

| 现象 | 处理 |
|---|---|
| ssh non-interactive 找不到 conda / slurm | 用 `bash -l` 强制 login shell，或脚本头 source profile |
| `conda activate <name>` fail 但 env 存在 | 多 conda 安装情形——用 `conda activate /full/path/to/env` |
| rsync `--delete` 误删远端 sub-agent work | 第一次 deploy 用 `--delete`；之后增量 sync 去掉 `--delete` |
| 远端 disk full | 提前 `df -h $REMOTE_PATH | tail -1` 看；< 50G 警告 |
| auto-production repo 在远端 dirty | `git stash` 远端改动；driver 决策是 push origin（如有 push 权）还是 abort |
| skill 符号链接断（remote auto-production 路径漂） | 重新跑 Phase 2，所有 link 重建 |
| GitHub API 限流 | clone 一次后改用 `git pull`；不重新 clone |

## Composition

- 前置：`/sprint-contract --sign` + `/smoke-test`（local）
- 后置：`/driver-findings` 反喂 sub-agent；最终 `/cross-host-sync` push 一行 status
- 跟 `/slurm-hold` 配套：sync 完后立即 `/slurm-hold` 抢节点准备真启训

## Pre-built probe templates

`tools/sync_probe_${stack}.sh` 提供常见 stack 的 probe 模板：

- `sync_probe_pi05.sh` — lerobot pi05 stack（vla3d 用）
- `sync_probe_openpi.sh` — openpi stack
- `sync_probe_isaaclab.sh` — Isaac Lab stack
- `sync_probe_generic.sh` — fallback，只查 python / torch / cuda

driver 复制对应 probe 改路径/env_name 即可。

## Real-world example

vla3d 第一次 deploy 用时（round 3）：

```
local → hpcc rsync:        361 KB / 5 sec
bootstrap (clone + link):  18 sec
probe (5 phases):           4 sec
finding extraction:         instant
→ 总: ~30 sec
findings 文件 + sub-agent 修完: ~10 min
节省（vs. 盲跑 ssh debug）：~1 day
```
