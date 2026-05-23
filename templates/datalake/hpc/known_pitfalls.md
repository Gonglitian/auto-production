# HPC datalake — known pitfalls

Seeded template for `datalake/hpc/known_pitfalls.md`. Copy + append your own as
discovered. Sourced from vla3d hpcc deploy round 3 + open-source community
patterns. See `/datalake` skill.

---

## [PITFALL] ssh non-interactive shell misses conda / slurm

**Symptom**: `ssh hpcc "conda activate myenv && python ..."` → `conda: command not found`

**Root cause**: Default `ssh host "cmd"` runs a non-interactive non-login shell that
does NOT source `~/.bashrc` or `/etc/profile.d/*.sh`. conda's `/opt/conda/etc/...`
init script is not on PATH.

**Fix**:
- Force login shell: `ssh host bash -lc "cmd"` or `ssh host bash -l /path/to/script.sh`
- Explicit source inside script: `source $(conda info --base)/etc/profile.d/conda.sh`

**vla3d source**: hpcc deploy round 3 W1 D1 probe — first 3 attempts silently failed
because conda missing; bash -l fix was 1-line.

---

## [PITFALL] conda activate <name> fails but env exists

**Symptom**:
```
conda info --envs    # shows /bigdata/.../envs/dynamem_pi05
conda activate dynamem_pi05    # → EnvironmentNameNotFound
```

**Root cause**: Multi-conda-install scenario. Envs at `/bigdata/.../envs/` are
NOT in the named registry of the default conda — only known by full path.

**Fix**: `conda activate /full/path/to/env`

---

## [PITFALL] HF_HOME silently pollutes root snapshot

**Symptom**: After `huggingface-cli download ...`, root disk fills up; or worse,
hpcc snapshot symlink farm gets thousands of cached blobs.

**Root cause**: HF default `HF_HOME=~/.cache/huggingface` which often = root disk
on HPC. Not noticed until `df -h ~` shows 100% or admin emails about snapshot bloat.

**Fix**: Always `export HF_HOME=/data4/hf_cache` (or your shared disk) BEFORE any
HF call. Add to `task_notes.yaml::environment_setup::required_env_vars`. `train.py`
entry MUST `assert os.environ.get('HF_HOME','').startswith('/data4')` for fail-loud.

---

## [PITFALL] sprint_contract partition stale

**Symptom**: `sprint_contract.yaml` says `partition: raise@hpcc`, sbatch returns
`Invalid partition name`.

**Root cause**: Partition names change as admins reorganize. `raise` is one example.

**Fix**: `/sprint-contract --check-refs` runs `sinfo -p $PARTITION` and validates
non-empty before `--sign`. Update partition list with `sinfo -o '%P %T'` at sprint
start.

Current hpcc partitions as of 2026-05: `batch / epyc / gpu / highclock / highmem`.

---

## [PITFALL] rsync --delete eats remote sub-agent work

**Symptom**: `rsync -av --delete local/ remote:/path/` deletes commits sub-agent
made on remote between syncs.

**Root cause**: `--delete` removes remote files not in source. If sub-agent has
been working on remote, those files vanish.

**Fix**:
- First deploy only: use `--delete` (clean slate desired)
- Incremental sync: omit `--delete`
- Better: have ONE source of truth (local or remote), other is read-only mirror

---

## [PITFALL] WebFetch source line# drifts from real install

**Symptom**: `arch_plan.md` says `lerobot/.../modeling_pi05.py::denoise_step at
line ~1130`. Real install shows line 871. 259-line drift.

**Root cause**: Agent WebFetch reads GitHub default branch (newest main); real
machine has pinned version (here lerobot 0.5.2 which is older). Versions drift.

**Fix**:
- Never trust line# from WebFetch as ground truth
- Use sentinel-substring `_verify_*()` runtime checks (see `/arch-plan` v2 +
  `templates/verify_external_ref.py`)
- On hpcc verify, `inspect.getsourcelines(fn)` is the only reliable source

---

## [PITFALL] lerobot in-place op on inputs_embeds[1] (older versions)

**Symptom**: Monkey-patched cross-attn module silently gets zero gradient.

**Root cause**: Older lerobot `paligemma_with_expert.forward` does in-place op on
`inputs_embeds[1]` that breaks autograd through patched downstream modules.

**Status (2026-05, lerobot 0.5.2)**: PROBABLY-RESOLVED — no in-place op pattern
found in `modeling_pi05.py`. Still recommended: `.clone()` defensive copy + run
`tests/test_xattn_grad.py` to confirm grad flow before real training.

---

## [PITFALL] lerobot LIBERO eval uses same-init × 10 (vs openpi 10-different-inits)

**Symptom**: LIBERO SR reported via lerobot vanilla `evaluate_libero` is inflated
compared to openpi / paper numbers.

**Root cause**: lerobot LIBERO eval entrypoint does `same-init × 10 rollouts`
per task (10 episodes with same env reset seed), while openpi does
`10-different-inits × 1 rollout`. Different distributions.

**Fix**: Override seed sampler in `eval/libero_eval.py`:

```python
libero_n_inits_per_task: 10
libero_rollouts_per_init: 1   # MUST be 1
```

Reference: huggingface/lerobot#2375.

---

## [PITFALL] /tmp on hpcc not persistent across nodes

**Symptom**: Write to `/tmp/X` on login node, can't find on compute node.

**Root cause**: HPC nodes typically have node-local `/tmp` (not shared).

**Fix**: Use shared filesystem for cross-node files: `/bigdata/<lab>/<user>/tmp/`
or `~/scratch/` (varies by cluster).
