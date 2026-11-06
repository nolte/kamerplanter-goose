---
name: harvest-planning
description: "Judges whether one plant is ready to harvest — ready, approaching, not ready, not harvestable, or insufficient evidence — from an observed maturity indicator weighed against the harvest months of its growing period, its position against the cultivar's days to maturity and the growth-stage hand-off, adds a pre-harvest safety-interval gate from treatments the person says were applied, and, for up to five plants, orders them into a harvest plan with windows, workload counts and storage constraints. Use when a recipe must say whether a plant can be picked, or when several plants' harvests must be sequenced. Never decides from the calendar or the plant's age alone, never computes a harvest date from days to maturity, never invents a yield, a storage limit or an effort, and records nothing."
---

# Plan the harvest

Asks two questions of what is already known. Scope `readiness`: is this one plant ready to harvest? Scope `plan`: in what order do up to five plants come ready, and how much work falls in which month? It does not re-read the plant: the context comes from `plant-context-collect`, the measurements from `diary-measurements-read`, the photo findings from `plant-photo-read`, the growth stage and its hand-off block from `growth-stage-assessment`, the weather exposures from `weather-impact-analysis`, the garden from `garden-context`. Its own reads are the two below. The weight of a claim is `decision-policy`. It writes nothing: the measured catalog has no harvest write tool, and a harvest is a person's act.

Every tool below is on the `kamerplanter` MCP server, addressed as `mcp__kamerplanter__<tool>`, and read-only. Tool behaviour is quoted from `spec/mcp/kamerplanter-mcp-server/en.md`, measured 2026-08-16 and not re-measured for this skill.

## Input

- **Scope**: `readiness` (one plant) or `plan` (up to five plants, or none).
- **Per plant**: the plant context block from `plant-context-collect` (`plant_key`, `species_key`, `cultivar_key`, `planted_on`, the species' `allows_harvest`, `harvest_pattern`, `harvest_months`, `growing_periods[]`, the cultivar's `days_to_maturity`, the inspections, the gaps list); optionally the diary read report and measurements, photo findings, the growth-stage assessment with its `HAND-OFF: HARVEST PLANNING` block, and the weather findings with their impact areas.
- **The garden context block** from `garden-context`, for scope `plan`.
- **Caller facts**, each optional, taken as written and marked `caller`: the person's own observation of the plant; the intended use (for example fresh eating, storage, seed saving); applied treatments as `treatment_key:YYYY-MM-DD`; storage conditions; harvest capacity with its unit; the assessment date.

Without the plant context block for a plant, judge nothing for it and say that `plant-context-collect` must run first.

## Procedure

### 1. Fix the assessment date

Take it from the caller. Without one, take the date the growth-stage assessment fixed (its `assessed as of`). **When the person's own observation is supplied and the caller gave no assessment date, compute neither the month-window position nor the safety-interval gate**: report both as `not computed (observation undated)`, because the observation that speaks to the present carries no date, and never fall back to an older diary date for them (the same exception `growth-stage-assessment` §1 makes). Without any date, every comparison that needs one (the month window, the position against `days_to_maturity`, the safety-interval gate) is `not computed (no assessment date)`. Never read today's date.

### 2. Is it harvestable at all

Read `allows_harvest` from the species fields. `false` gives `not harvestable`: judge nothing further about maturity, and carry the plant into the plan as such. Absent gives `insufficient evidence` with `allows_harvest` named as missing. Report `harvest_pattern` as read; its value set is not recorded, so do not interpret it.

### 3. Collect the timing priors

These are **priors**, level 4, and decide nothing alone:

- **The harvest window**: the `harvest_months` of the `growing_periods[]` entry that applies, saying which; never the top-level months when periods exist, since those are the union. With several periods and nothing to choose between them, the window is `unknown (growing period not chosen)`. Compare the assessment month: before, inside or after the window.
- **The maturity position**: from the hand-off block, "days since `planted_on`: n of `days_to_maturity` m". Carry it as a position. **Never compute a harvest date from it**: what `days_to_maturity` counts from, sowing or transplanting, is not recorded, and neither is what `planted_on` denotes.
- **The growth stage**: the hand-off block's result and direction, as returned. Without the growth-stage assessment, this prior is absent with that reason.
- **Accumulated growing degree days**: from the hand-off block, with their base, method and span, as returned, and `no level`: a derivation, not a source. State `GDD target for maturity: no source`; the sum is context and never decides.

### 4. Collect the maturity indicators

These are the only things that speak to whether this plant is ready now:

| Indicator | Level |
|-----------|-------|
| a diary measurement of this plant whose key and unit unambiguously describe ripeness, recent enough for the question | 1 (2 when older) |
| the person's own observation of the plant (`caller`), for example "pods dry and rattling" | 3, a confirmed observation; the spec names this placement as open |
| a recorded inspection that states ripeness | 3 |
| a `plant-photo-read` finding about ripeness (colour, size, drying, splitting) | no level: a reading that may corroborate or contradict, never decide alone |

Discard a `measurements` key whose meaning or unit is ambiguous, and say that you did. A use-specific indicator (ripe for storage, ripe for seed) comes from the caller or is general knowledge labelled level 8 and not from the record, and never decides alone. Never fabricate an indicator.

### 5. Read the harvest readiness tool

If the tool is present, call `mcp__kamerplanter__get_harvest_readiness` once with the plant and the garden, and nothing else; if it is absent, say so by name as the result of this step (`not called (tool absent: get_harvest_readiness)`). Its arguments and its response fields are not recorded in any spec here: report the response as returned, assume no field name, and assign it **no level**. On a `validation.error` or any other error, report it verbatim and continue: no result depends on this call.

### 6. Read the weather risk

From the weather findings, take only the exposures whose impact area is harvest timing. Each is a **risk** to the harvest (for example a forecast frost before a frost-sensitive crop is in), stated with its threshold and level as `weather-impact-analysis` returned it. It is never a maturity indicator and never moves the result. Without weather findings, the risk is `no source`.

### 7. Gate on the safety interval

For each treatment the caller supplied as `treatment_key:YYYY-MM-DD`, call `mcp__kamerplanter__get_treatment` with that key and read `safety_interval_days`, the pre-harvest Karenz. The gate date is the application date plus that many days.

Each supplied treatment is first judged on its own: `blocked until <gate date>` when the gate date lies after the assessment date, `passed` when it lies on or before it, and `unknown (<reason>)` when its read failed, it carries no `safety_interval_days`, or there is no assessment date. The plant's gate is the aggregate, with the precedence `blocked` over `unknown` over `clear`:

| What is known | Gate |
|---------------|------|
| no treatment supplied | `unknown (no treatment date supplied)` |
| any treatment `blocked until` a date | `blocked until <latest gate date>`, whatever the others are |
| no treatment blocked, and any treatment `unknown` | `unknown (<reason of each unknown treatment>)` |
| every treatment `passed` | `clear` |

A failed read is never a passed interval: `a:2026-07-01,b:2026-08-20` with the read of `b` failing is `unknown`, not `clear`, even when `a` has passed. The undated-observation case of step 1 gives `not computed (observation undated)` instead.

Never infer from the care log, the inspections or the diary that a treatment was or was not applied: no described field records an application date.

### 8. Decide

| What is known | Result |
|---------------|--------|
| `allows_harvest: false` | `not harvestable` |
| `allows_harvest` absent | `insufficient evidence` |
| an indicator at level 1 to 3 that the crop is ripe for the intended use | `ready` |
| an indicator at level 1 to 3 of development toward ripeness that has not reached it | `approaching` |
| an indicator at level 1 to 3 that the crop is not developing toward ripeness yet | `not ready` |
| a photo reading of ripeness, corroborated by a timing prior of step 3 | `ready`, `approaching` or `not ready`, with the confidence stated as `level 4 prior + photo reading (level 3 corroboration)` |
| only priors, the readiness tool's response, or an uncorroborated photo reading | `insufficient evidence` |
| no maturity indicator | `insufficient evidence` |

When indicators disagree, the higher level stands and the lower is listed as contradicting it (`decision-policy` step 4). A prior that disagrees with the indicator is reported as a contradiction and does not move the result. `insufficient evidence` is the ordinary result for a plant nobody has looked at recently: name the observation that would settle it, usually the person's own look at the crop.

### 9. Weigh it

Apply `decision-policy`: evidence (level, source, retrieved-at, one entry each), confidence from the highest level that supports the result, uncertainty (what would change it), missing data (each input it did not have, with the observation that would supply it).

### 10. Plan, for scope `plan`

- **Which plants**: at most five, the first five by plant key as text; every further plant is `not planned (limit of five)`, and a plant whose context could not be read is `not planned (<error verbatim>)`; both count as not planned. With none given, report the crops and planting runs from the garden context as context only, compute no window and no readiness, and name the `plants` parameter as what would supply them.
- **Readiness per plant**: steps 1 to 9 for each.
- **Order**: by the window's start month, the first month of the selected period's `harvest_months` as recorded, a plant with an unknown window after every known one; then by readiness (`ready`, `approaching`, `not ready`, `insufficient evidence`, `not harvestable`); then by plant key, as text. The window start is the calendar month of the window's first month within the season, so a window that crosses the year boundary (for example November to February) sorts by its calendar start month; that is intended, not a defect. The order of the input has no effect. A plant whose gate is `blocked until <date>` is listed with its gate and never as harvestable before that date.
- **Workload**: count plants per window start month, and plants `ready` or `approaching`. State hours or effort only from the caller's capacity, and "over capacity" only when that capacity is in the same unit as the counts (for example plants per week); otherwise say the counts cannot be compared with it.
- **Storage and use**: the caller's storage conditions and intended use, marked `caller`; without them, `not modeled in the measured catalog`. No yield, harvest amount or shelf life is recorded, so none is stated.

### 11. Report

Return, in this order, one `HARVEST READINESS` block and one `FINDING` per plant, and the `HARVEST PLAN` block for scope `plan`:

```
HARVEST READINESS
  plant:          <plant key>
  assessed as of: <date> (caller | growth stage) | none
  harvestable:    allows_harvest <value as read> | absent; harvest_pattern <as read> | absent
  result:         ready | approaching | not ready | not harvestable | insufficient evidence
  intended use:   <caller words> | not stated
  indicators:     <each, with level and source> | none
  priors:         window <months, period, before | inside | after> | unknown (<reason>) | not computed (<reason>); maturity position <n of m> | not computed (<reason>); growth stage <result, direction> | absent (<reason>); accumulated GDD <value, base, method, span> | absent (<reason>), level: no level, GDD target for maturity: no source
  readiness tool: <as returned> | error <verbatim> | not called (tool absent: get_harvest_readiness)   level: no level
  weather risk:   <harvest-timing exposures, threshold, level> | none | no source
  gate:           clear | blocked until <date> | unknown (<reason>) | not computed (<reason>)
  evidence:       <level, source, retrieved-at, one entry each>
  confidence:     <the level it rests on, or: no level applies>
  uncertainty:    <what would change the result>
  missing:        <each input it did not have, with the observation that would supply it>
FINDING
  domain: harvest | subject: <plant key> | kind: recommendation (ready or approaching on a level 1 to 3 indicator) or observation (every other result)
  statement / evidence / confidence / what would change it / missing data, as above
  mutation (named, never called): no tool measured
  consequence: <only if an input states one, otherwise absent>
HARVEST PLAN
  garden:      <tenant>
  planned:     <n>; not planned: <plant key: reason, each>
  order:       <position. plant key — window start | unknown, result, gate>
  workload:    <month: n plants>; ready or approaching: <n>; capacity <caller value> | not supplied; over capacity: yes | no | not comparable (<why>)
  storage:     <caller text> | not modeled in the measured catalog
  context only (no plants given): <crops and planting runs from the garden context>
```

Return no field that was not read. The facts two runs over the same input must agree on are the results, the gates, the plan order, the workload counts, the evidence levels and the missing-data list; retrieval times and prose may differ, and byte-identical prose is not claimed.

## Hard rules

- Never decide a result from the harvest months, the maturity position, the accumulated growing degree days, the growth stage, the readiness tool's response or a photo reading alone.
- Never compute a harvest date from `days_to_maturity`.
- Never assume a field of `get_harvest_readiness`, and never give its response a level.
- Never fill a yield, a storage limit, an effort, a treatment date or an indicator, and never infer that a treatment was applied.
- Never read the current date into the facts.
- Call no Home Assistant tool. Two intents look like a harvest answer and have an unclassified effect. Forbidden by name: `TimeTillErnte`, `time_till`.
- Call no tool that changes state. Forbidden by name: `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`, `mcp__kamerplanter__submit_diary_analysis`, `mcp__kamerplanter__transition_plant_phase`, `mcp__kamerplanter__assign_species_phase_sequence`, `mcp__kamerplanter__assign_nutrient_plan`, `mcp__kamerplanter__record_feeding_event`, `mcp__kamerplanter__create_inspection`, `mcp__kamerplanter__clone_nutrient_plan`, `mcp__kamerplanter__set_nutrient_plan_phase_targets`, `mcp__kamerplanter__create_substrate_mix`, `mcp__kamerplanter__set_plant_substrate`.
- Report a tool error verbatim and continue with what remains.

## Gotchas

- `TimeTillErnte` ("time till harvest") on the reference Home Assistant instance looks like the answer to this skill's question. It is an unclassified custom intent, and calling it from a read-only run is forbidden.
- Upstream specifies harvest write tools that the measured catalog does not carry. A ready plant therefore names `no tool measured` as its mutation; recording the harvest happens outside the run.
- The pest process excludes a treatment whose safety interval exceeds the time to harvest; this skill answers the reverse question, whether a treatment already applied blocks a harvest now, and only from dates the person supplies.
- Most runs without an observation end with `insufficient evidence`. A plant in its harvest months and past its days to maturity is worth a look, not ready.
- This skill itself was not run against a live instance, and the readiness tool's signature is not recorded. Treat the first real run as the measurement.

## Source

Governed by `spec/process/harvest-readiness-and-planning/en.md` §A to §I.
