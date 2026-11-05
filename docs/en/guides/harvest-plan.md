---
title: Harvest plan
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Harvest plan

`harvest-plan` puts the harvests of up to five plants in one order: **which comes first, which month the work falls in, and what blocks or limits it.** For each plant it gives the same readiness answer as [`harvest-readiness-check`](harvest-readiness-check.md) — ready, approaching, not ready, not harvestable or not enough evidence — plus its harvest window and its safety-interval gate, then orders the plants by window start, then readiness, then plant key. The window start is the calendar month of the window's first month, so a window from November to February sorts under November.

The run **only reads**. It harvests and schedules nothing, records no harvest or yield, has no apply recipe and calls no Home Assistant tool.

!!! note "Not yet run against a live instance"
    The recipe and the skill were written while the Kamerplanter MCP server was unreachable. Tool names come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md), measured on 2026-08-16. Treat the first real run as the measurement.

## What the plan cannot know

The record has **no field for yield, storage or effort**. The plan therefore counts what it can count — plants per month of window start, and plants ready or approaching — and states storage and capacity only from what you supply. "Over capacity" appears only when your capacity is in the same unit as the counts, for example `3 plants per week`. Without your observations most plants come back `insufficient evidence`; that is honest, not a failure.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `garden-context`, `plant-context-collect`, `diary-measurements-read`, `growth-stage-assessment`, `weather-impact-analysis`, `decision-policy` and `harvest-planning` from `.claude/skills/`. Started elsewhere, the skills are lost silently.
- **You need the plants' `plant_key`s.** [plant-master-data-check](plant-master-data-check.md) prints them.

## Run it

```sh
goose run --recipe harvest-plan \
  --params tenant=my-garden \
  --params plants=42,43,44 \
  --params observations="42: pods dry; 43: first fruit colouring" \
  --params storage="cool cellar, room for two crates" \
  --params capacity="3 plants per week" \
  --params treatments=43:neem-oil:2026-08-20 \
  --params as_of=2026-09-01
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `plants` | no | nothing is planned; the garden's crops and planting runs are shown as context |
| `observations` | no | per plant, nothing from you about how the crop looks now |
| `intended_use` | no | ripeness is judged without a use |
| `storage` | no | storage is `not modeled in the measured catalog` |
| `capacity` | no | workload is counts only |
| `weather` | no | the weather risk is `no source` |
| `treatments` | no | every gate is `unknown (no treatment date supplied)` |
| `as_of` | no | each plant's growth stage date; with none, no timing and no gate for that plant. A plant with an observation and no `as_of` gets no harvest-month position and no gate |

At most five plants are planned: the first five by plant key, sorted as text, so the same list always gives the same five. The rest, and every plant that cannot be read (with the error), are listed as not planned. A gate is `clear` only when every listed treatment's interval is known and passed. A plant blocked by a safety interval is listed with its gate date and is never put before it.

## Read the outcome

| Closing line | Means |
|--------------|-------|
| `HARVEST PLAN: <n> planned, <m> not planned — <slug>` | `<n>` plants are in the order; `<m>` were named beyond the limit or could not be read, both counted |
| `HARVEST PLAN: not planned — <slug>` | every step failed |

## Sources

- [`recipes/harvest-plan.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/harvest-plan.yaml) — the parameters and the report format
- [`.claude/skills/harvest-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/harvest-planning/SKILL.md) — the order, the workload and the storage rule
- [`spec/process/harvest-readiness-and-planning/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/harvest-readiness-and-planning/en.md) — the process this recipe implements
