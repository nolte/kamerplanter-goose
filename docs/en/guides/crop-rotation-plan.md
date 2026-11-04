---
title: Crop rotation plan
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Crop rotation plan

A rotation keeps one plant family out of a bed for a few seasons after it stood there. `crop-rotation-plan` takes the crops you want to grow, your beds and what stood in them before, and proposes one family per bed and season for the seasons you name. Every crop it considered for a bed gets a verdict with the rule behind it; every conflict is listed, including one your own pin causes; every crop it left out is listed with the reason.

The plan is a **document for review**. It records nothing, and the Kamerplanter tools this repository has measured include none that records a bed assignment, a rotation or a planting run. The recipe that would record a plan is a blocked follow-up split out of [#47](https://github.com/nolte/kamerplanter-goose/issues/47) and does not exist yet.

This run **only reads**. It changes no record.

!!! note "Not yet run against a live instance"
    The recipe and its four skills were written while the Kamerplanter MCP server was unreachable. Tool names and species fields come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md) and the [species baseline spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/en.md), measured on 2026-08-07 on two species. Whether every species carries a family, and what an archived plant carries, is not measured. Treat the first real run as the measurement.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `garden-context`, `rotation-history-collect`, `crop-rotation-planning` and `decision-policy` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.
- **Know what the catalog cannot tell the run.** The family of a crop comes from the species record's `family_key` and nothing else. The catalog has no beds, no bed history, no rotation interval and no order of nutrient demand. Those come from you, or they stay unknown.

## Run it

```sh
goose run --recipe crop-rotation-plan \
  --params tenant=my-garden \
  --params crops="solanum-lycopersicum,phaseolus-vulgaris,brassica-oleracea" \
  --params seasons="2027,2028,2029" \
  --params beds="bed-1,bed-2,bed-3" \
  --params bed_history="bed-1:2026:solanum-lycopersicum,bed-2:2026:none" \
  --params rotation_years=4
```

The keys above are examples; use the species keys your garden's catalog carries.

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `crops` | yes | — |
| `seasons` | yes | — |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `beds` | no | only the beds named in `bed_history` or in a pin are planned |
| `bed_history` | no | a bed's history comes from the catalog only, and a bed the catalog does not cover stays unknown |
| `rotation_years` | no | a same-family repeat is reported as `repeat — interval unknown`, never as a conflict and never as clear |
| `demand_sequence` | no | demand order is not evaluated |
| `constraints` | no | no pin and no exclusion |

`crops` is a comma-separated list; each entry is a species key, or a species key and a cultivar key joined by a colon. `seasons` must be consecutive years; a gap stops the run. `beds` is a comma-separated list of names, each optionally followed by `:area_or_volume`.

## Supply the bed history and the interval

- **Bed history** is `bed:season:crop`, comma-separated, for example `bed-1:2026:solanum-lycopersicum`. Write `bed:season:none` for a season the bed stood empty. One entry is enough to make a bed's history count: the run then takes what you wrote as complete, so a season you did not name held no crop. A bed with no history at all stays `unknown` for the first seasons.
- **The catalog's history** is used too, but only where a plant's location key is exactly the bed name. Every other location is listed as context. The season of a catalog plant is the year it was planted. A failed or incomplete read is reported and never read as "nothing grew here".
- **`rotation_years`** is the smallest distance in seasons at which one family may stand in a bed again. With `4`, a family planted in 2026 is a conflict in 2027, 2028 and 2029, and allowed in 2030. No number is built in, because the catalog holds none.
- **`demand_sequence`** is an order of demand classes compared as text with the catalog's `nutrient_demand_level`, for example `heavy_feeder,medium_feeder,light_feeder,green_manure`. After a crop of one class, the next class in the order is preferred; `green_manure` also matches a crop the catalog marks as suitable for green manure. It only ranks and never makes a conflict.
- **`constraints`** are separated by semicolons. `pin=bed-1:2027:solanum-tuberosum` places that crop there, whatever its verdict, and lists any rule it breaks. `exclude=bed-3:brassica-oleracea` keeps that crop out of that bed. Any other text is listed as not evaluated.

## What the verdicts mean

| Verdict | Means |
|---------|-------|
| `clear` | no crop of the same family stood in the bed within the interval, and the history covers that span |
| `conflict` | a crop of the same family stood in the bed within the interval you gave |
| `repeat — interval unknown` | a crop of the same family stood in the bed earlier, and you gave no interval to judge it |
| `caution` | nothing else applies, and a plant at this bed has a recorded inspection; the catalog records no host range, so a pest cannot be tied to a family |
| `unknown` | the crop has no recorded family, a crop in the window has none, or the bed's history does not reach back far enough |

Per bed and season the run selects one family, preferring `clear`, then `caution`, then `unknown`, then a family that fewer beds already hold that season, then the demand order. A family with `conflict` or `repeat — interval unknown` is never selected unless you pinned it. A bed and season with nothing selectable is `open`.

## What the plan does not do

- **It records nothing.** There is no tool to record it with.
- **It does not lay out a bed.** It names a family and its crops per bed and season. Area, spacing, neighbours and succession are bed layout's work, tracked in [#46](https://github.com/nolte/kamerplanter-goose/issues/46).
- **It does not give dates.** Sowing and harvest windows come from the [garden plan](garden-plan.md). Each crop is keyed as `species_key/cultivar_key`, the same prefix as a garden-plan run, so the two can be read side by side.
- **It does not recall.** No family, interval or demand order comes from general knowledge, and companions are not read as a rotation rule.

## Read the outcome

The report shows which skills loaded, then a table of beds and seasons, then the conflicts, the crops not placed, the rotation header and bed history, and the apply contract.

| Closing line | Means |
|--------------|-------|
| `ROTATION: <p> placements, <c> conflicts, <u> unknown — <slug>` | how many beds and seasons got a family, how many conflicts were found, and how many crop verdicts were unknown |
| `APPLY: no write tool measured (blocked follow-up split out of nolte/kamerplanter-goose#47)` | the plan cannot be recorded from here |

A plan full of `unknown` is the honest result while the catalog's families are not populated or your bed history is missing. Supplying `bed_history` and `rotation_years` is what turns it into verdicts.

## How far "deterministic" goes

The plan facts are a function of what you supply: the placements, the verdicts with their rules, the conflicts, the reasons for *not placed* and the evidence levels. Two runs over the same inputs should give the same plan facts; the wording around them can differ. The order in which you list crops or beds does not change them. This was checked three times on one invented example written out as text — four beds, three seasons, one crop without a family, a conflicting pin, a same-family repeat and one inspection, once with and once without an interval — not on a live garden. The placements, the verdicts with their rules and the crops not placed agreed in all three runs; which conflicts are listed and which level a verdict carries did not, and the skill was made explicit on both afterwards without a fresh series. The example is not kept in this repository.

## Sources

- [`recipes/crop-rotation-plan.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/crop-rotation-plan.yaml) — the parameters and the report format
- [`.claude/skills/crop-rotation-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/crop-rotation-planning/SKILL.md) — the verdicts, the selection and the apply contract
- [`.claude/skills/rotation-history-collect/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/rotation-history-collect/SKILL.md) — what is read from the catalog
- [`spec/process/crop-rotation-planning/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/crop-rotation-planning/en.md) — the process this recipe implements
