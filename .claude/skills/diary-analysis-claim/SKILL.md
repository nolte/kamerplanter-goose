---
name: diary-analysis-claim
description: "Drives the Kamerplanter diary-analysis handshake end to end — selecting a pending entry, claiming it under a lease, and submitting a completed or failed result so the claim is always released. Use when a recipe processes entries from the AI-analysis queue, when asked to take the next pending diary analysis, or whenever a run must claim a diary entry before working on it. Handles lease sizing, the always-submit guarantee, and the refusal path for entries that cannot be analysed."
---

# Claim and release a diary analysis

Owns the handshake, not the analysis. What happens between claiming and submitting is the caller's subject; this skill guarantees that a claimed entry is never left under a dangling lease.

Tools are on the `kamerplanter` MCP server, addressed as `mcp__kamerplanter__<tool>`.

## The invariant

**Every claim is released by the same run that opened it.** From the moment `mcp__kamerplanter__claim_diary_analysis` succeeds, exactly one thing must still happen: `mcp__kamerplanter__submit_diary_analysis`, with either outcome. A failed submit is a correct ending. An abandoned lease is not, because it blocks the entry for up to an hour with nothing to show for it.

Order the work so that everything refusable happens *before* the claim.

## Procedure

### 1. Check permissions before claiming

Call `mcp__kamerplanter__list_tenants` and read `mcp_permissions`. The cycle needs `mcp.write`. Without it, stop here and report the missing permission — claiming an entry that cannot be submitted parks it for the full lease duration for no benefit.

### 2. Select one entry

Use the `entry_key` the caller supplies. Otherwise call `mcp__kamerplanter__list_pending_diary_analyses` and take the oldest by `requested_at`.

Skip, without claiming, any entry whose `photo_count` is 0 when the analysis needs images. Report it as skipped and name why.

Set `include_stale: true` to also pick up entries whose previous lease expired.

### 3. Claim

Call `mcp__kamerplanter__claim_diary_analysis` with:

- `entry_key`
- `worker_id` — identifies this recipe and run, stored as `analysis_claimed_by`. Use a stable recipe identifier plus a per-run discriminator.
- `lease_seconds` — sized to the expected run, **not** the 3600 maximum. A crashed run holds the entry for exactly this long, so a shorter lease costs nothing and frees the queue sooner. 900 (the default) suits a single-entry image analysis.

Keep the returned `lease_token`. Without it the result cannot be submitted and the lease can only expire.

### 4. Hand off

The caller performs its analysis. This skill's contract resumes at step 5 regardless of how that goes — including when a tool errors, the context runs short, or the material turns out to be unusable.

### 5. Submit

Call `mcp__kamerplanter__submit_diary_analysis` with `entry_key`, `lease_token`, and a `status`.

On `status: "completed"`, supply:

| Field | Constraint |
|-------|------------|
| `summary` | Required. One to three sentences, 2000 characters maximum |
| `findings` | Up to 10, each with `label`, `confidence` (0.0–1.0), and `rationale` |
| `recommended_actions` | Up to 10 concrete actions |
| `analyzed_photo_ids` | Up to 5 ids that actually informed the result |
| `model` | Max 200 characters |
| `recipe_version` | Max 50 characters |

On `status: "failed"`, `error` is required and names the cause: no legible photo, no plant depicted, missing context, or a named tool failure.

An analysis that found nothing wrong is `completed` with an empty `findings` list and a summary saying the plant appears normal for its species and phase. Healthy is a result, not a reason to invent a marginal finding.

## Hard rules

- Never read an entry's photos before the claim succeeds.
- Never end a run that holds a claim without calling `mcp__kamerplanter__submit_diary_analysis`. If the analysis collapsed, submit `failed` with the cause.
- Never pass `lease_seconds` above 3600; the call fails validation. Never reach for the maximum as a default.
- Never call a state-changing tool other than `mcp__kamerplanter__claim_diary_analysis` and `mcp__kamerplanter__submit_diary_analysis` for the entry this run claimed. Specifically out of bounds: `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, and `mcp__kamerplanter__add_plant_diary_entry`.
- Never print an API key or token, not even partially, and not the `lease_token` either.

## Gotchas

- `mcp__kamerplanter__claim_diary_analysis` is a lease plus compare-and-set. A second worker holding the same entry loses; treat a rejected claim as "someone else has it", pick the next entry, and say so.
- `dry_run: true` on either write tool returns the planned effect without persisting — useful for a rehearsal, but a dry-run claim yields no usable `lease_token`, so do not mix a dry-run claim with a real submit.
- An `idempotency_key` replays the original result for 24 hours for an identical call from the same account, tenant, and tool. Derive it from the entry and run so a retried run does not double-write.
- `mcp__kamerplanter__list_pending_diary_analyses` returns no free text and no images by design. It is a work queue, not a data source; the entry's content comes from `mcp__kamerplanter__get_diary_entry`.
- `limit` above 100 fails validation. The default of 20 is ample when the run handles one entry.

## Source

Derived from `spec/process/plant-health-image-analysis/` §"The process", measured against the reference instance on 2026-08-05.
