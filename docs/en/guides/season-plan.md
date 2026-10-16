---
title: Season plan
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-10-14
---

# Season plan

The same plan, laid on a year. `season-plan` makes the plan of [`garden-plan`](garden-plan.md) for the crops you name and shows its runs month by month, with the successions the plan names. It is built from the plan only: it adds no date.

It applies nothing, and the Kamerplanter tools this repository has measured include none that could ([#59](https://github.com/nolte/kamerplanter-goose/issues/59)).

This run **only reads**. It changes no record.

!!! note "Not yet run against a live instance"
    The recipe and its six skills were written while the Kamerplanter MCP server was unreachable. Tool names and species fields come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md) and the [species baseline spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/en.md), measured on 2026-08-07 on two species. Treat the first real run as the measurement.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `garden-context`, `site-analysis`, `crop-selection`, `planting-calendar`, `plant-planning` and `decision-policy` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.

## Run it

```sh
goose run --recipe season-plan \
  --params tenant=my-garden \
  --params crops="allium-porrum"
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `crops` | yes | — |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `goals` | no | no goal is judged; none is reported met |
| `harvest_window` | no | the harvest preference is reported unknown; it never drops a crop |
| `light`, `area_or_volume`, `water`, `constraints` | no | the matching site parameter is unknown: the server has no field for them |
| `hardiness_zone` | no | the hardiness check is undetermined: no tool says which zone a garden is in |
| `beds` | no | no beds are listed for bed layout |
| `planting_method` | no | every method with a known sowing window is offered, each as its own run |

`crops` is a comma-separated list; each entry is a species key, or a species key and a cultivar key joined by a colon. `beds` is a comma-separated list of `name:area_or_volume`, for example `bed-1:2m2,tub-1:10l`. `planting_method` is `direct_sow` or `indoor_then_transplant`; any other text is not a preference.

## What the month view shows

One row per run, twelve month columns. A month is marked **S** where the sowing window covers it, **I** for the month of the indoor sowing date, **T** from the start of the transplant window, and **H** where the harvest window covers it. A window that is unknown is not placed, and the view says it is incomplete and names it.

The successions listed are the ones the plan names (`precedes` and `follows`, with both run identifiers) and no others.

## Read the outcome

| Closing line | Means |
|--------------|-------|
| `SEASON: <r> runs, <s> successions — <slug>` | how many runs the view shows and how many successions the plan names |
| `NOT PLACED: <windows>` | each window that could not be put on the calendar, with its reason |

## Sources

- [`recipes/season-plan.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/season-plan.yaml) — the parameters and the report format
- [`.claude/skills/plant-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/plant-planning/SKILL.md) — the runs, their identifiers and the apply contract
- [`.claude/skills/planting-calendar/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/planting-calendar/SKILL.md) — the windows behind each run
- [`.claude/skills/crop-selection/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/crop-selection/SKILL.md) — which crops may be planned
- [`spec/process/plant-planning-and-planting-calendar/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/plant-planning-and-planting-calendar/en.md) — the process this recipe implements
