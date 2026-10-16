---
title: Garden plan
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-10-14
---

# Garden plan

A plan says when each chosen crop is sown, when it is transplanted, when it is expected to be harvested, and where it goes. `garden-plan` turns the crops you name into planting-run proposals for one Kamerplanter garden: each run has a stable identifier, a method, windows with the rule behind each, and a confidence. What it cannot plan, it lists with the reason.

The plan is a **document for review**. It applies nothing, and the Kamerplanter tools this repository has measured include none that creates a planting run, a sowing or planting task, or a plan. The recipes that would apply a plan are tracked in [#59](https://github.com/nolte/kamerplanter-goose/issues/59) and do not exist yet.

This run **only reads**. It changes no record.

!!! note "Not yet run against a live instance"
    The recipe and its six skills were written while the Kamerplanter MCP server was unreachable. Tool names and species fields come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md) and the [species baseline spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/en.md), measured on 2026-08-07 on two species. Treat the first real run as the measurement.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `garden-context`, `site-analysis`, `crop-selection`, `planting-calendar`, `plant-planning` and `decision-policy` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.

## Run it

```sh
goose run --recipe garden-plan \
  --params tenant=my-garden \
  --params crops="allium-porrum" \
  --params beds="bed-1:2m2" \
  --params hardiness_zone=7b
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

## What becomes a run

- **Only an eligible crop with a known sowing window or indoor sowing date.** Every other crop is listed under *not planned*: rejected (with the failed constraint), undetermined (with the missing input), or window unknown (with the missing input).
- **One run per growing period and method.** A species with a summer and a winter period yields two runs. Without a method preference, a crop that qualifies for both methods appears twice; they are alternatives for you to choose between.
- **The identifier says what the run is**: species, cultivar or `none`, method, and the period's months. It does not depend on the order of the crops you listed.
- **No bed is assigned.** Bed layout does that. The beds you supplied are listed in the plan header.
- **Rotation is always unknown**, because rotation is not built yet; companions are not read as a rotation rule.
- **A succession is named only where the dates show one**: the last harvest month of one period before the first sowing month of another. Both runs say so, `precedes` on the earlier and `follows` on the later.

## How far "deterministic" goes

The plan facts are a function of what you supply: the run identifiers, methods, windows, locations, whether a succession is named, the rotation notes, the reasons for *not planned* and the confidence levels. Two runs over the same inputs give the same plan facts; the wording around them can differ. This was checked once, on one invented example of input blocks written out as text, not on a live garden; that example is not kept in this repository, so the check cannot be repeated from here.

## Read the outcome

The report is a table of the runs, then the crops that were not planned, then the plan header, the rationale and evidence behind each date, and the apply contract: what a later apply step would create, and that no tool for it is measured.

| Closing line | Means |
|--------------|-------|
| `PLAN: <r> runs, <n> not planned — <slug>` | how many runs were proposed and how many crops were left out |
| `APPLY: no write tool measured (nolte/kamerplanter-goose#59)` | the plan cannot be applied from here |

A plan with few runs and a long *not planned* list is the honest result when the garden's inputs were not supplied.

## Sources

- [`recipes/garden-plan.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/garden-plan.yaml) — the parameters and the report format
- [`.claude/skills/plant-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/plant-planning/SKILL.md) — the runs, their identifiers and the apply contract
- [`.claude/skills/planting-calendar/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/planting-calendar/SKILL.md) — the windows behind each run
- [`.claude/skills/crop-selection/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/crop-selection/SKILL.md) — which crops may be planned
- [`spec/process/plant-planning-and-planting-calendar/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/plant-planning-and-planting-calendar/en.md) — the process this recipe implements
