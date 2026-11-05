---
title: Bed layout plan
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Bed layout plan

A bed layout says which crop stands in which bed or container in a season, and whether it fits. `bed-layout-plan` takes the crops you want to grow, one season, your beds and containers with their area or volume, and, if you give them, the spacing and the number of plants per crop. It computes the planting runs, a crop rotation and the successions for that season, then places each run in a bed the rotation admits it to and checks the capacity of every bed month by month. Every placement says why it went where it did and which beds it did not go to; every run left out is listed with the reason.

The layout is a **document for review**. It records nothing, and the Kamerplanter tools this repository has measured include none that creates a bed, records a bed assignment or a layout, or creates a planting run. The recipe that would record a layout, `bed-layout-plan-apply`, is tracked, blocked, in [#74](https://github.com/nolte/kamerplanter-goose/issues/74) and does not exist yet.

This run **only reads**. It changes no record.

!!! note "Not yet run against a live instance"
    The recipe and its three new skills, `companion-spacing-collect`, `succession-planning` and `bed-layout-planning`, were written while the Kamerplanter MCP server was unreachable. Tool names and species fields come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md) and the [species baseline spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/en.md), measured on 2026-08-07 on two species. What a companion `score` means and what the seed density counts is not measured. Treat the first real run as the measurement.

## Before you start

- **Start the run from this repository checkout.** The recipe loads eleven project skills from `.claude/skills/` — the nine of the [succession plan](succession-plan.md) plus `companion-spacing-collect` and `bed-layout-planning` — and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.
- **Know what the catalog cannot tell the run.** The catalog has no beds, no area or volume, no spacing, no light, access or irrigation, and no list of bad neighbours. It has a list of compatible companions with a score, and a seed density whose unit is not recorded. Everything else comes from you, or it stays unknown.

## Run it

```sh
goose run --recipe bed-layout-plan \
  --params tenant=my-garden \
  --params crops="lactuca-sativa,cichorium-endivia,phaseolus-vulgaris,pisum-sativum" \
  --params season=2027 \
  --params beds="bed-1:2m2,bed-2:3m2,tub-1:20l" \
  --params bed_history="bed-1:2026:none,bed-2:2026:none,tub-1:2026:none" \
  --params rotation_years=3 \
  --params spacing="lactuca-sativa=10/m2,pisum-sativum=2l" \
  --params quantities="lactuca-sativa=12,pisum-sativum=6" \
  --params constraints="avoid=phaseolus-vulgaris+pisum-sativum"
```

The keys above are examples; use the species keys your garden's catalog carries.

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `crops` | yes | — |
| `season` | yes | — |
| `beds` | no | only the beds named in `bed_history` or in a pin are planned, and their capacity is unknown |
| `spacing` | no | no need is computed, and every capacity is `not validated` |
| `quantities` | no | no need is computed, and every capacity is `not validated` |
| `bed_attributes` | no | the layout reports light, access and irrigation as not supplied |
| `constraints` | no | no pin, no exclusion and no avoided pair |
| `bed_history`, `rotation_years`, `demand_sequence` | no | as in the [crop rotation plan](crop-rotation-plan.md) |
| `stagger_weeks` | no | as in the [succession plan](succession-plan.md) |
| `tenant`, `planting_method`, `goals`, `harvest_window`, `light`, `area_or_volume`, `water`, `hardiness_zone` | no | as in the [garden plan](garden-plan.md) |
| `site_constraints` | no | no environmental constraint of the site; this is what the garden plan takes as its `constraints` parameter |

## Supply beds, spacing, quantities and constraints

- **Beds** are comma-separated: `bed-1:2m2` is a bed of 2 m², `tub-1:20l` a container of 20 litres, and a bare `bed-3` a bed of unknown size. Any other text after the colon is reported as written, with capacity unknown. A bed the rotation plans that you did not list in `beds`, one named only in `bed_history` or a pin, is laid out too, with capacity unknown and the source `rotation plan`.
- **Spacing** is plants per square metre for a bed, `lactuca-sativa=10/m2`, or litres per plant for a container, `pisum-sativum=2l`. A cultivar entry, `species:cultivar=…`, wins over the species entry. A bed needs a `/m2` spacing and a container an `l` spacing; a mismatch leaves the capacity not validated.
- **Quantities** are plants per planting run, `lactuca-sativa=12`. A crop with two growing periods has two runs, and each needs the quantity.
- **`avoid`** in `constraints` keeps two crops out of one bed in overlapping months: `avoid=phaseolus-vulgaris+pisum-sativum`. Pairs are separated by semicolons. A pair you do not name is never treated as incompatible.
- **`constraints` here is not the garden plan's.** It carries `pin=`, `exclude=` and `avoid=`. The environmental constraints of the site, which the garden plan takes as `constraints`, go into `site_constraints`.
- **`exclude=bed:crop`** keeps a crop out of a bed. Use it when a bed's light, access or irrigation rules a crop out; the attributes themselves decide nothing.
- **`bed_attributes`** are semicolon-separated, `bed-1:light=full sun;tub-1:irrigation=drip`. They appear per bed and in each placement's reason, as context.

## What "not validated" means

The capacity of a bed is checked month by month: everything that stands in the bed that month must fit into its area or volume. A month is `within` when it fits, and `over by <x>` when a pinned crop overfills it; an unpinned crop never goes to a bed it would overfill. It is `not validated` when any number the check needs is missing: the bed's size, a crop's spacing or quantity, or the months a crop stands there. The missing input is named. The run never fills it in, not from the catalog's seed density and not from general knowledge; a layout without spacing and quantities is all `not validated`, and that is the honest result.

## Companions are an input, not a guarantee

The catalog lists compatible companions for some species, each with a score. The layout uses them only to choose between beds that are otherwise equal: it adds up the numeric scores with the crops already in each bed in the same months and prefers the higher sum. A score that is not a number counts 0 and is marked `score not comparable`; a pair the catalog does not list is `unknown`. What a score means is not recorded, so every placement says that a companion pairing is a planning input from the catalog, not a guarantee of any outcome, and that a higher score is assumed to be more favourable because the record does not state its direction.

## What the plan does not do

- **It records nothing.** There is no tool to record it with.
- **It does not draw.** It allocates area or volume per bed; rows, positions and coordinates are not planned.
- **It does not apply light, access or irrigation as rules.** No species field records what a crop needs, so the run reports your attributes and leaves the rule to `exclude`.
- **It does not re-derive the rotation.** A crop stands only in a bed the rotation plan admits it to; a crop outside the rotation plan is listed as such.
- **It does not recall.** No spacing, density, incompatibility or companion effect comes from general knowledge.

## Read the outcome

The report shows which skills loaded, then a table of beds and placements, then the capacity per bed and month, the conflicts, the runs not placed, the layout header with every placement's reason, and the apply contract.

| Closing line | Means |
|--------------|-------|
| `LAYOUT: <p> placements, <o> over capacity, <n> not validated — <slug>` | how many runs were placed, and how many bed-and-month entries are over capacity or not validated |
| `APPLY: no write tool measured (nolte/kamerplanter-goose#74)` | the layout cannot be recorded from here |

A pin always stands where you pinned it, even in a bed the rotation reports as `occupied`. When it overfills its bed or breaks an `avoid` or `exclude`, that is listed under the conflicts, never hidden. One exception: a pinned crop offered under both methods with no `planting_method` is not placed at all, and the conflicts list it as `pinned crop: method not chosen — set planting_method` until you choose.

## How far "deterministic" goes

The plan facts are a function of what you supply: the placements, the needs, the capacity per bed and month, the conflicts, the reasons for *not placed* and the evidence levels. Two runs over the same inputs should give the same plan facts; the wording around them can differ. This was checked three times on one invented example written out as text — a bed in m² with spacing and quantities, a bed with no size, an empty open bed, a container in litres, a pinned crop over capacity, an avoided pair, a crop offered under two methods, a crop with two growing periods, a winter crop and a companion score that is not a number — not on a live garden. All three runs gave the same placements, needs, capacities, conflicts and reasons, and they matched the facts worked out by hand. After the occupancy, bed-set and pin rules were sharpened, a second series of three on the same example, extended by a bed only the rotation plans and a crop sown after its harvest, again agreed on every placement, capacity, conflict and reason and matched the hand-worked facts; two runs wrote an excess as `1 m2` where the third wrote `1.00 m2`, after which the number format was stated. That last change was not re-measured. The example is not kept in this repository.

## Sources

- [`recipes/bed-layout-plan.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/bed-layout-plan.yaml) — the parameters and the report format
- [`.claude/skills/bed-layout-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/bed-layout-planning/SKILL.md) — the placement, the capacity check and the apply contract
- [`.claude/skills/companion-spacing-collect/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/companion-spacing-collect/SKILL.md) — what is read from the catalog
- [`.claude/skills/succession-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/succession-planning/SKILL.md) — the successions the layout keeps in one bed
- [`spec/process/bed-layout-and-succession-planning/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/bed-layout-and-succession-planning/en.md) — the process this recipe implements
