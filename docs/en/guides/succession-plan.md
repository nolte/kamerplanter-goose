---
title: Succession plan
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Succession plan

A succession uses a bed twice in one season: one crop comes out, the next goes in, or one crop is sown in staggered sets so the harvest does not all arrive at once. `succession-plan` takes the crops you want to grow and one season, computes their planting runs and a crop rotation for that season, and proposes which runs can follow each other in the same bed and which can be sown in staggered sets. Every succession names both planting runs and the planting-calendar windows it rests on; every run without a succession is listed with the reason.

The plan is a **document for review**. It records nothing, and the Kamerplanter tools this repository has measured include none that records a succession, a bed assignment or a planting run. The recipe that would record a layout, `bed-layout-plan-apply`, is tracked, blocked, in a follow-up issue split out of [#46](https://github.com/nolte/kamerplanter-goose/issues/46), and does not exist yet.

This run **only reads**. It changes no record.

!!! note "Not yet run against a live instance"
    The recipe and its new skill, `succession-planning`, were written while the Kamerplanter MCP server was unreachable. Tool names and species fields come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md) and the [species baseline spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/en.md), measured on 2026-08-07 on two species. Treat the first real run as the measurement.

## Before you start

- **Start the run from this repository checkout.** The recipe loads nine project skills from `.claude/skills/` — `garden-context`, `site-analysis`, `crop-selection`, `decision-policy`, `planting-calendar`, `plant-planning`, `rotation-history-collect`, `crop-rotation-planning` and `succession-planning` — and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.
- **Know what the catalog cannot tell the run.** The windows come from the species records through the planting calendar; the family per bed comes from the rotation step. The catalog has no beds, no bed history, no rotation interval and no stagger interval. Those come from you, or they stay unknown.

## Run it

```sh
goose run --recipe succession-plan \
  --params tenant=my-garden \
  --params crops="lactuca-sativa,cichorium-endivia,phaseolus-vulgaris" \
  --params season=2027 \
  --params beds="bed-1:2m2,bed-2:3m2" \
  --params bed_history="bed-1:2026:none,bed-2:2026:none" \
  --params rotation_years=3 \
  --params stagger_weeks=2
```

The keys above are examples; use the species keys your garden's catalog carries.

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `crops` | yes | — |
| `season` | yes | — |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `beds` | no | only the beds named in `bed_history` or in a pin are planned |
| `bed_history` | no | a bed's history comes from the catalog only; the rotation step reports what it cannot judge as `unknown` |
| `rotation_years` | no | no crop is `clear`; the rotation step still fills slots, at best with `unknown` verdicts |
| `demand_sequence` | no | the rotation step does not evaluate demand order |
| `constraints` | no | no pin and no exclusion |
| `stagger_weeks` | no | staggering is reported as possible, with the interval not supplied |
| `planting_method` | no | a crop offered under both methods for one growing period is not succeeded until you choose |
| `goals`, `harvest_window`, `light`, `area_or_volume`, `water`, `site_constraints`, `hardiness_zone` | no | as in the [garden plan](garden-plan.md) |

## Supply the inputs

- **The season** is one year. Windows are months in it. A crop whose harvest reaches into the next year, a winter crop for example, has no known occupancy in this season and is not succeeded.
- **Beds, bed history, `rotation_years` and `constraints`** go to the rotation step exactly as in the [crop rotation plan](crop-rotation-plan.md). A succession is proposed only between crops the rotation plan admits to the same bed and season; a bed that the rotation leaves `open` takes no succession.
- **`stagger_weeks`** is the number of weeks between staggered sowings, for example `2`. The run lists the sowing dates from the first day of the sowing window, every two weeks, as long as the date stays inside the window. No interval is built in.
- **Spacing, quantities and incompatible pairs** are not used here; the [bed layout plan](bed-layout-plan.md) takes them.

## What the results mean

| Result | Means |
|--------|-------|
| `SEQUENTIAL <bed>/<season> <run> -> <run>` | the earlier run's last harvest month comes before the later run's first sowing or transplant month, and the rotation admits both crops to that bed |
| `STAGGERED <run>` with dates | sowings of one run at your interval inside its sowing window |
| `staggering possible within <months> — interval not supplied` | the window allows staggering, and you gave no interval |
| `method not chosen — set planting_method` | the same crop and growing period is offered under both methods; choose one |
| `outside rotation plan` | the rotation admits this crop to no bed in the season |
| `spans the season boundary` | the harvest reaches into the next year |
| `no run follows or precedes it in <slot>` | the bed holds other runs, and their months do not line up |

Every succession is level `caller`, because the season you gave is one of the things it rests on.

## What the plan does not do

- **It records nothing.** There is no tool to record it with.
- **It does not place runs in beds.** It says which runs could follow each other in a bed. The [bed layout plan](bed-layout-plan.md) places them and checks that they fit.
- **It does not recall.** No stagger interval, sowing date or duration comes from general knowledge, and no succession crosses a rotation.
- **It does not plan across seasons.** One run plans one season.

## Read the outcome

The report shows which skills loaded, then a table of successions, then the runs not succeeded, the succession header and the apply contract.

| Closing line | Means |
|--------------|-------|
| `SUCCESSION: <s> successions, <u> unknown — <slug>` | how many sequential successions and dated staggered successions the plan contains, and how many staggered entries lack an interval or runs have an unknown occupancy |
| `APPLY: no write tool measured (the blocked follow-up split out of nolte/kamerplanter-goose#46)` | the plan cannot be recorded from here |

## How far "deterministic" goes

The plan facts are a function of what you supply: the successions with their slots and run identifiers, the sowing dates, the reasons for *not succeeded* and the evidence levels. Two runs over the same inputs should give the same plan facts; the wording around them can differ. This was checked three times on one invented example written out as text — five beds with a pinned slot and an open slot, a crop offered under two methods, a crop with two growing periods, a winter crop, once with and once without a stagger interval — not on a live garden. All three runs gave the same plan facts in both variants, and they matched the facts worked out by hand. The example is not kept in this repository.

## Sources

- [`recipes/succession-plan.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/succession-plan.yaml) — the parameters and the report format
- [`.claude/skills/succession-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/succession-planning/SKILL.md) — the successions and the apply contract
- [`spec/process/bed-layout-and-succession-planning/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/bed-layout-and-succession-planning/en.md) — the process this recipe implements
