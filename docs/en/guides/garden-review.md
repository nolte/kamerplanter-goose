---
title: Garden review
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Garden review

`garden-review` looks back over a garden in the middle of a season, up to a date: **what was recorded for each plant, what you say about it, what the season teaches, and what the next plan should keep or reconsider.** It ends in a next-cycle block you can hand to [`garden-plan`](garden-plan.md) or [`crop-selection`](crop-selection.md). For a whole finished season, archived plants included, use [`season-review`](season-review.md).

The run **only reads**. It writes the review nowhere — no file, no diary entry — has no apply recipe and calls no Home Assistant tool.

!!! note "Not yet run against a live instance"
    The recipe and the skill were written while the Kamerplanter MCP server was unreachable. Tool names come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md), measured on 2026-08-16. Treat the first real run as the measurement.

## What a review will and will not say

- **Yield comes only from you.** The record has no yield field, and a diary measurement is never read as one. Give it as `plant_key:amount unit`.
- **Care is never the cause.** A pattern in the care log is linked to an outcome only as "consistent with", a suspicion, never as the reason something happened.
- **Cultivars stand side by side.** No score, no ranking, no average; two cultivars are compared only on the same field in the same unit.
- **Plant health is not assessed here.** The review runs no plant health assessment and reports plant health as not supplied; run plant-health-assessment separately for a plant's present state. Pest history comes from the recorded inspections only; the review runs no assessment of a plant's present state.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `garden-context`, `plant-context-collect`, `diary-measurements-read`, `growth-stage-assessment`, `decision-policy` and `garden-review` from `.claude/skills/`. Started elsewhere, the skills are lost silently.

## Run it

```sh
goose run --recipe garden-review \
  --params tenant=my-garden \
  --params plants=42,43 \
  --params yields="42:1.2 kg,43:14 fruit" \
  --params notes="43: blossom end rot in July; slugs everywhere after the wet June" \
  --params as_of=2026-08-15
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `plants` | no | the garden level only: crops, planting runs and due tasks |
| `yields` | no | every yield is absent |
| `harvest_results` | no | every harvest result is absent; give `plant_key:result[:YYYY-MM-DD]`, for example copied from `harvest-readiness-check` closing lines |
| `notes` | no | nothing from you about plants or the garden |
| `weather` | no | the season's weather is absent; it is context only either way |
| `as_of` | no | the date of the newest diary entry read |

At most five plants are reviewed: the first five by plant key, sorted as text. `;` and `:` separate the entries of `yields`, `harvest_results` and `notes`; a free-text part that contains them is shown verbatim and not parsed further. Each plant's diary is read for at most eight entries, and the review says how far back that reached.

## Read the outcome

The report shows six blocks: the header, one history record per plant, cultivar performance, the lessons (each an observation, or a recommendation with evidence, confidence, uncertainty and missing data), the next-cycle block, and the domain status. Each crop in the next-cycle block is marked `reconsider` when a record or your note names a problem with it, which wins over everything else; `keep` only when you report a success (a note, or a yield you call a success) and no problem is recorded; and `no evidence` otherwise. A yield figure on its own is `no evidence`. `constraints` carries only site and environmental observations; lessons go to `goals`.

| Closing line | Means |
|--------------|-------|
| `GARDEN REVIEW: <n> reviewed, <m> not reviewed — <slug>` | `<n>` plants have a history record; `<m>` were named beyond the limit or could not be read |

## Sources

- [`recipes/garden-review.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/garden-review.yaml) — the parameters and the report format
- [`.claude/skills/garden-review/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/garden-review/SKILL.md) — the history record, the lessons and the next-cycle block
- [`spec/process/garden-and-season-review/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/garden-and-season-review/en.md) — the process this recipe implements
