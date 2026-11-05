---
title: Harvest readiness check
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Harvest readiness check

`harvest-readiness-check` answers "can I pick it?" for one plant: **ready, approaching, not ready, not harvestable, or not enough evidence to say.** Every answer says what it rests on, how sure it is, what would change it and what is missing. On top of the answer sits a **harvest gate**: if you say a treatment was applied, its pre-harvest safety interval (Karenz) can block the harvest until a date.

The run **only reads**. It harvests nothing, records no harvest or yield, writes no diary entry and has no apply recipe. It calls no Home Assistant tool, including the `TimeTillErnte` intent that looks like a harvest answer: its effect is unclassified.

!!! note "Not yet run against a live instance"
    The recipe and the skill were written while the Kamerplanter MCP server was unreachable. Tool names come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md), measured on 2026-08-16. Treat the first real run as the measurement.

## Expect "insufficient evidence"

The species' harvest months and the cultivar's days to maturity say what is **expected**. They are not a look at the crop, and on their own they decide nothing. No harvest date is computed from days to maturity at all: the record does not say whether it counts from sowing or from transplanting. Something has to say how the crop looks now: your own observation (`observations`), a diary measurement that clearly describes ripeness, or a photo reading backed by one of those expectations. Without any of them the honest answer is `insufficient evidence`, and the report names the observation that would settle it.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `plant-context-collect`, `diary-measurements-read`, `plant-photo-read`, `growth-stage-assessment`, `weather-impact-analysis`, `decision-policy` and `harvest-planning` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.
- **You need the plant's `plant_key`**, the numeric key. [plant-master-data-check](plant-master-data-check.md) prints it.
- Run [`connectivity-check`](connectivity-check.md) first against a new environment.

## Run it

```sh
goose run --recipe harvest-readiness-check \
  --params plant_key=42 \
  --params tenant=my-garden \
  --params observations="pods dry and rattling" \
  --params intended_use="seed saving" \
  --params treatments=neem-oil:2026-08-20 \
  --params as_of=2026-09-01
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `plant_key` | yes | — |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `observations` | no | nothing from you about how the crop looks now |
| `entry_key` | no | no photo is read |
| `intended_use` | no | ripeness is judged without a use; the record has no field for it |
| `weather` | no | the weather risk is `no source`; nothing is read from Home Assistant |
| `temperatures` | no | no growing degree days for the growth stage |
| `treatments` | no | the harvest gate is `unknown (no treatment date supplied)` |
| `as_of` | no | the date the growth stage assessment fixed; with none, no timing and no gate. **Give it with `observations`**: your observation carries no date, so without `as_of` the harvest-month position and the gate are `not computed (observation undated)` |

## What it decides

| What is known | Result |
|---------------|--------|
| the species does not allow harvest | `not harvestable` |
| your observation, an inspection or a clear measurement that the crop is ripe | `ready` |
| one of those showing ripening that is not complete | `approaching` |
| one of those showing the crop is not ripening yet | `not ready` |
| a photo reading backed by the harvest months or the growth stage | one of the three above |
| only the calendar, the plant's age, the growth stage or an unbacked photo | `insufficient evidence` |

- **Weather is a risk, never ripeness.** A frost or a storm you report becomes a harvest-timing risk next to the answer; it never moves the answer.
- **The gate needs your dates.** The record holds no application dates, so the gate reads only the treatments you list and their safety interval from `get_treatment`. One blocking treatment blocks the harvest. A treatment whose interval cannot be read makes the gate `unknown`, never `clear`: `clear` needs every listed interval known and passed.
- **Growing degree days are context.** If the growth stage computed them from your temperatures, they are shown as a prior with no level; no growing-degree-day target for maturity is recorded, so they never decide.
- **The readiness tool is reported as it comes back.** `get_harvest_readiness` is called when the server offers it (its absence is reported by name), but its fields are not recorded anywhere here, so it carries no weight and an error from it does not stop the run.

## Read the outcome

| Closing line | Means |
|--------------|-------|
| `HARVEST READINESS: ready (gate: clear) — <plant_key>` | an observation says the crop is ripe, and no treatment blocks it |
| `HARVEST READINESS: ready (gate: blocked until <date>) — <plant_key>` | ripe, but wait for the safety interval to pass |
| `HARVEST READINESS: approaching (gate: …) — <plant_key>` | ripening; look again soon |
| `HARVEST READINESS: not ready (gate: …) — <plant_key>` | not ripening yet |
| `HARVEST READINESS: not harvestable (gate: …) — <plant_key>` | the species is not grown for a harvest |
| `HARVEST READINESS: insufficient evidence (gate: …) — <plant_key>` | nothing says how the crop looks now; the report names what would |
| `… (gate: unknown) — <plant_key>` | no treatment was listed, or one listed treatment's interval could not be read |
| `… (gate: not computed) — <plant_key>` | an observation was given without `as_of`, or there is no date at all |
| `HARVEST READINESS: not assessed — <plant_key>` | a step failed and no judgement could be reached |

To order several plants, use [`harvest-plan`](harvest-plan.md).

## Sources

- [`recipes/harvest-readiness-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/harvest-readiness-check.yaml) — the parameters and the report format
- [`.claude/skills/harvest-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/harvest-planning/SKILL.md) — the decision table, the gate and the plan
- [`spec/process/harvest-readiness-and-planning/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/harvest-readiness-and-planning/en.md) — the process this recipe implements
