---
title: Diary analysis queue
audience: [queue-operator, self-hoster]
content_mode: how-to
track: developer-docs
last_updated: 2026-08-16
---

# Diary analysis queue

Diary entries with photos are waiting in Kamerplanter's AI-analysis queue, and you want a Goose run to work through them — once by hand, or unattended on a schedule. This page names the command for each of those shapes and what its final line means.

These runs **write to your garden**: each one claims an entry, submits an analysis back to it, and releases the claim. Read [what the recipes do](../references/index.md) before pointing one at a garden you care about.

## Before you start

- **Start every run from this repository checkout.** The recipes load project skills from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. A run started elsewhere loses the skill silently and still produces a plausible answer.
- **Load the environment**: `direnv allow`. It provides `KAMERPLANTER_URL`, `KAMERPLANTER_API_KEY` and `GOOSE_ADDITIONAL_CONFIG_FILES`, which the shared `extensions.yaml` is loaded through.
- **The API key needs the `mcp.write` permission.** Without it, a run stops before claiming anything and reports the missing permission.
- **Prove the connection first**: `goose run --recipe connectivity-check`. It names a bad URL, a revoked key, or a disabled MCP server before an analysis run misreports it.

## Analyse a single entry

```sh
goose run --no-session --max-turns 25 -q \
  --recipe diary-photo-analysis-apply \
  --params run_id=manual-$(date +%Y%m%d-%H%M%S)
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `run_id` | yes | — it is the discriminator in `worker_id` and the idempotency key, so a retry is traceable and does not double-write |
| `entry_key` | no | the run takes the oldest entry waiting in the queue |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |

Name an entry explicitly with `--params entry_key=<key>`.

The run prints a per-step table and closes with `SUBMITTED: completed`, `SUBMITTED: failed`, or `NOT CLAIMED: <reason>`.

## Work through the whole queue

Two shapes exist, and they differ in one property only: whether the entries share a context.

| | `scripts/analyse-queue.sh` | `diary-analysis-queue-apply` |
|---|---|---|
| Processes | one Goose process per entry | one process for the queue |
| An entry that crashes or exhausts its context | cannot reach the next entry | can take the rest of the run with it |
| Costs | one process start per entry | one process start |
| Output arrives | per entry, as each run ends | at the end |

Use the script for unattended runs; use the recipe when you are watching the run and want one continuous transcript.

### One process per entry

```sh
scripts/analyse-queue.sh 3 my-garden
```

Both arguments are optional and positional: `scripts/analyse-queue.sh [max_entries] [tenant]`. `max_entries` defaults to `3`; leave `tenant` off to let each run discover the garden slug itself. The script filters out entries without photos before it starts anything, so a run does not begin only to refuse.

It exits `2` on a rejected argument, `1` when the queue could not be read at all — that case processes nothing, and says so — and `0` otherwise, including when nothing is pending.

### One run for the whole queue

```sh
goose run --recipe diary-analysis-queue-apply \
  --params run_id=queue-$(date +%Y%m%d-%H%M%S) \
  --params max_entries=3
```

| Parameter | Required | Default |
|-----------|:--------:|---------|
| `run_id` | yes | — |
| `tenant` | no | discovered from `list_tenants` |
| `max_entries` | no | `3` |
| `include_stale` | no | `true` — also picks up entries whose previous lease expired |

Raise `max_entries` deliberately. Every entry costs a full analysis in the same context, and exhausting that context mid-queue is what leaves a claim open.

## Run it on a schedule

Cron gives a job neither the working directory nor the `.envrc` environment, and both are load-bearing here. Set the directory and let `direnv exec` supply the credentials:

```cron
17 * * * * cd /path/to/kamerplanter-goose && direnv exec . scripts/analyse-queue.sh 3 my-garden >> /var/log/kamerplanter-queue.log 2>&1
```

A systemd timer needs the same two things: `WorkingDirectory=` on the service unit, and `direnv exec .` in front of the script.

## Read the outcome without the transcript

Every shape closes with lines you can grep, so a scheduled run is judged without reading what the model said.

| Line | Emitted by | Means |
|------|-----------|-------|
| `SUBMITTED: completed` | single entry | the analysis was written back to the entry |
| `SUBMITTED: failed` | single entry | the entry was claimed, the analysis could not be made, and the failure was submitted |
| `NOT CLAIMED: <reason>` | single entry | nothing was claimed; the entry is untouched and stays in the queue |
| `PROCESSED: <n> ok, <n> failed, <n> not claimed` | script | per-entry outcome of this run |
| `REMAINING: <n> still pending with photos` | script | the backlog after this run |
| `QUEUE TOTAL: <n>` / `PROCESSED: <n> completed, <n> failed, <n> skipped` / `REMAINING: <n>` | recipe | the same three quantities from the in-run loop, in the recipe's own wording |

Grep for the wording of the shape you actually ran. The two report the same quantities and phrase them differently — only the script's `REMAINING` line carries the `still pending with photos` suffix, so that exact string never matches a `diary-analysis-queue-apply` run.

Their third counter also counts different things. The script's `not claimed` is an entry whose single-entry run printed `NOT CLAIMED` — it filtered photo-less entries out before starting, so this is a lease another worker held or a refusal. The recipe's `skipped` is an entry it never claimed because `photo_count` was 0.

`REMAINING` counts what actually completed, not what was attempted: a failed run's lease expires and requeues its entry, and a `NOT CLAIMED` run never held one.

A run that dies mid-analysis leaves a claim behind. That is not a state you have to repair: the lease expires on its own. Which run picks the entry up again depends on the shape, though. `scripts/analyse-queue.sh` always asks for stale entries and `diary-analysis-queue-apply` defaults to it, so both heal the backlog by themselves. `diary-photo-analysis-apply` has no `include_stale` parameter at all — a bare single-entry run can walk past the parked entry, so send one of the queue shapes after it.

## Sources

- [`recipes/diary-photo-analysis-apply.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/diary-photo-analysis-apply.yaml) and [`recipes/diary-analysis-queue-apply.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/diary-analysis-queue-apply.yaml) — the parameters and the report format
- [`scripts/analyse-queue.sh`](https://github.com/nolte/kamerplanter-goose/blob/develop/scripts/analyse-queue.sh) — the per-entry process loop and its exit codes
- [`spec/goose/recipe-project-pattern/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/goose/recipe-project-pattern/en.md) — why the working directory is load-bearing, and why neither shape uses Goose's `sub_recipes:`
