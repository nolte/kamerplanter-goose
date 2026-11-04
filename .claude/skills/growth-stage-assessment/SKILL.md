---
name: growth-stage-assessment
description: "Reconciles one plant's recorded growth phase with what is known about it — the person's and the diary's observations, photo readings, its age since planting, its time in the phase, the cultivar and species expectations, and, where the inputs are supplied, growing degree days and photoperiod — and returns recorded stage consistent, recorded stage questionable (with a direction ahead, behind or unclear), or insufficient evidence, with evidence, confidence, uncertainty and missing data. Use when a recipe must say whether a plant is where its record says in its development, or when the daily check or harvest planning needs the growth stage. Reports an unresolved phase as an absent stage, never places a stage from accumulated warmth or a timing expectation alone, names the phase transition a person might record and never calls it."
---

# Assess the growth stage

Asks one question of the record: does the phase it holds for this plant match what is known about the plant now? It does not re-read the plant: the context comes from `plant-context-collect`, the measurements from `diary-measurements-read`, the photo findings from `plant-photo-read`. Its own reads are the two phase tools below, because the context block does not carry them. The weight of a claim is `decision-policy`. It writes nothing: a questionable stage is a statement to a person, and recording a different phase is a separate, later decision.

Every tool below is on the `kamerplanter` MCP server, addressed as `mcp__kamerplanter__<tool>`, and read-only. Tool behaviour is quoted from `spec/mcp/kamerplanter-mcp-server/en.md`, measured 2026-08-16 and not re-measured for this skill.

## Input

- **The plant context block** from `plant-context-collect`: `plant_key`, `species_key`, `cultivar_key`, `current_phase`, `phase_started_at`, `planted_on`, the phase definition (`typical_duration_days`, `stress_tolerance`), the species fields (`bloom_months`, `harvest_months`, `growing_periods[]`, `base_temp_gdd`), the cultivar's `days_to_maturity`, the gaps list.
- **The diary read report and measurements** from `diary-measurements-read`, optional.
- **Photo findings** from `plant-photo-read`, optional.
- **The lifecycle report** from `plant-lifecycle-resolve`, optional: the resolved cycle and windows.
- **Caller facts**, each optional, taken as written and marked `caller`: the person's own observation of the plant (for example "first flower buds open"); a daily temperature series (date, minimum, maximum, unit); the latitude of the garden; the indoor light schedule (hours of light per day); the assessment date.

Without the plant context block, stop and say that `plant-context-collect` must run first.

## Procedure

### 1. Fix the assessment date

Take it from the caller. Without one, take the recorded date of the newest dated observation used: a diary entry of this plant that `diary-measurements-read` actually read, including the entry whose photos were read only when it was among those entries and belongs to this `plant_key`. A photo finding carries no date of its own, and neither does the person's own observation. **When the person's own observation is supplied and the caller gave no assessment date, compute no time-based comparison or derivation** (days in the phase, days since `planted_on`, month windows, growing degree days, photoperiod) and say why: the observation that speaks to the present carries no date, and a diary date would judge it against another day. Without any date there is no assessment date either. In both cases every timing comparison below is `not computed (<reason>)`. Never read today's date; the date is an input, so two runs over the same input give the same result.

### 2. Read the phase status

Call `mcp__kamerplanter__get_plant_phase_status` with `plant_key` and `tenant`. **`phase_state: unresolved` reads like a normal answer and is not**: it means the open record points at no phase. Report the recorded stage as absent, with that reason, and the result can only be `insufficient evidence`. A phase status that disagrees with the context block's `current_phase` is a contradiction: report both.

### 3. Read the phase history

Call `mcp__kamerplanter__get_plant_phase_history` with `plant_key` and `tenant`. Its response fields are not recorded in any spec here: report what it returns, as returned, and assume no field name. Use it only where an entry plainly states a phase and a date; otherwise report it and carry nothing forward from it.

### 4. Collect the observations of the present development

These are the only things that speak to where the plant is now:

| Observation | Level |
|-------------|-------|
| a diary measurement of this plant whose key and unit unambiguously describe development, recent enough for the question | 1 (2 when older) |
| the person's own observation of the plant (`caller`) | 3, a confirmed observation; the spec names this placement as open |
| a recorded inspection that states development | 3 |
| a `plant-photo-read` finding about development (buds, flowers, fruit, senescence) | no level: a reading that may corroborate or contradict, never decide alone |

Discard a `measurements` key whose meaning or unit is ambiguous, and say that you did. Never fabricate an observation.

### 5. Collect the timing expectations

These are **priors**, level 4 (the cultivar before the species), and decide nothing alone:

- days in the phase (`phase_started_at` to the assessment date) against `typical_duration_days`; a phase past it is overdue;
- days since `planted_on` against the cultivar's `days_to_maturity`;
- the assessment month against `bloom_months` and `harvest_months`, from the selected `growing_periods[]` entry when there are several, never their union;
- the lifecycle report's windows, when supplied.

### 6. Derive, where the inputs exist

Each derivation is `no level`, states its inputs, and is reported absent with its reason otherwise.

- **Growing degree days**: only from the caller's daily series and the species `base_temp_gdd`, read as °C (its unit is not recorded; the measured 5.0 and 15.0 fit Celsius), converting a series given in °F. Per day `max(0, (Tmax + Tmin) / 2 − Tbase)`, summed from `planted_on` to the assessment date. State the method, the base, and the span the series covers; a span that does not reach back to `planted_on` is partial and says so. Never from a single reading, a Home Assistant snapshot or a forecast. No GDD target for a stage or for maturity is recorded, so the sum is context and **places no stage**. A tropical species with a temperate base accumulates degree days that never happened (`species-baseline-verify`); say so when the base looks implausible for the species.
- **Photoperiod**: outdoors, only from the caller's latitude `φ` and the assessment date (day of year `N`): declination `δ = 23.44° × sin(360° × (284 + N) / 365)`, day length `= (24 / π) × arccos(−tan φ × tan δ)` hours, clamped to 0 or 24 beyond the polar circles. Indoors, the caller's light schedule as given. No species field records photoperiod sensitivity, so whether the species responds to day length is `no source`; researching it under the three-source rule is outside this skill.

`search_glossary` defines terms; a definition is not evidence.

### 7. Decide

| What is known | Result |
|---------------|--------|
| the recorded stage absent or `unresolved` | `insufficient evidence` |
| an observation at level 1 to 3 that matches the recorded phase, and none contradicting it | `recorded stage consistent` |
| an observation at level 1 to 3 that contradicts the recorded phase | `recorded stage questionable` |
| a photo reading that matches or contradicts, corroborated by a timing expectation of step 5 | `recorded stage consistent` or `recorded stage questionable` |
| only timing expectations, derivations, or an uncorroborated photo reading | `insufficient evidence` |
| no observation of the present development | `insufficient evidence` |

When observations disagree, the higher level stands and the lower is listed as contradicting it (`decision-policy` step 4). A questionable stage carries a **direction**: `ahead` when the plant shows development the recorded phase has not reached, `behind` when it lacks development the recorded phase implies, `unclear` when the evidence points neither way. The **estimated stage** is a phase key only when the evidence names one from the phase definitions; otherwise `not estimated`. Never invent a phase key.

`insufficient evidence` is the ordinary result for a plant tended only through reminders: say which observation would settle it, usually the person's own look at the plant or a photo of it.

### 8. Weigh it

Apply `decision-policy`: evidence (level, source, retrieved-at, one entry each), confidence from the highest level that supports the result, uncertainty (what would change it), missing data (each input it did not have, with the observation that would supply it).

### 9. Report

Return, in this order:

```
GROWTH STAGE ASSESSMENT
  plant:          <plant key>
  assessed as of: <date> (caller | newest observation) | none
  recorded stage: <phase key, phase_started_at> | absent (<reason, e.g. phase_state unresolved>)
  phase history:  <as returned> | absent (<reason>)
  result:         recorded stage consistent | recorded stage questionable | insufficient evidence
  direction:      ahead | behind | unclear      (questionable only)
  estimated stage: <phase key named by the evidence> | not estimated
  observations:   <each, with level and source>
  expectations:   <each timing prior, read as a prior only> | absent
  derivations:    GDD <value, base, method, span> | absent (<reason>); photoperiod <hours, from> | absent (<reason>); day-length response: no source   level: no level
  evidence:       <level, source, retrieved-at, one entry each>
  confidence:     <the level it rests on, or: no level applies>
  uncertainty:    <what would change the result>
  missing:        <each input it did not have, with the observation that would supply it>
HAND-OFF: HARVEST PLANNING
  recorded stage / estimated stage / result / direction
  days in phase: <n> of typical_duration_days <m> | not computed (<reason>)
  days since planted_on: <n> of days_to_maturity <m> (cultivar) | not computed (<reason>)
  accumulated GDD: <value with base, method and span> | absent (<reason>)
  photoperiod: <hours> | absent (<reason>)
FINDING
  domain: growth stage | subject: <plant key> | kind: recommendation (questionable) or observation (consistent, insufficient evidence)
  statement / evidence / confidence / what would change it / missing data, as above
  mutation (named, never called): mcp__kamerplanter__transition_plant_phase, target <estimated stage | target not established>   (questionable only)
  consequence: <only if an input states one, otherwise absent>
```

A questionable stage is a recommendation to a person to check the plant against its recorded phase; recording a new phase is a later apply step that this skill names and never calls. Return no field that was not read. The facts two runs over the same input must agree on are the result, the direction, the estimated stage, the evidence levels and the missing-data list; retrieval times and prose may differ, and byte-identical prose is not claimed.

## Hard rules

- Never report `phase_state: unresolved` as a normal stage.
- Never place a stage from growing degree days, a timing expectation or a photo reading alone.
- Never assume a field of `get_plant_phase_history`; report it as returned.
- Never fill an absent input, a phase key, a GDD target or a photoperiod sensitivity, and never fabricate an observation.
- Never read the current date into the facts.
- Call no Home Assistant tool.
- Call no tool that changes state. Forbidden by name: `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`, `mcp__kamerplanter__submit_diary_analysis`, `mcp__kamerplanter__transition_plant_phase`, `mcp__kamerplanter__assign_species_phase_sequence`, `mcp__kamerplanter__assign_nutrient_plan`, `mcp__kamerplanter__record_feeding_event`, `mcp__kamerplanter__create_inspection`. `transition_plant_phase` sits closest to this skill's subject: it is named as the mutation a later apply step would call, and never called here.
- Report a tool error verbatim and continue with what remains.

## Gotchas

- An overdue phase reframes "not flowering yet" from normal to notable, but it is a prior: on its own it makes a stage worth a look, not questionable.
- The cultivar's `days_to_maturity` counts days, not degree days; nothing converts one into the other.
- `plant-context-collect` judges timing against an observation's date, and so does this skill; a run with no observation and no caller date computes no timing at all.
- This skill itself was not run against a live instance; the field set of the phase history and the value set of `phase_state` beyond `unresolved` are not recorded. Treat the first real run as the measurement.

## Source

Governed by `spec/process/growth-stage-and-weather-impact/en.md` §A, §B, §C, §F, §G and §H.
