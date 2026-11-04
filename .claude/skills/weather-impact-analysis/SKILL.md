---
name: weather-impact-analysis
description: "Turns the weather and forecast a person supplies, and optionally one Home Assistant weather reading, into exposures for one plant: per factor (temperature extremes, rainfall, wind, humidity, heat and cold events, forecast changes) exposure, no exposure in the supplied data, or no source, each with the threshold it was judged against and the area it is likely to affect (care, health, harvest timing). Use when a recipe must say what the weather means for named plants, or when the daily check needs the weather domain. Never turns weather into a plant symptom or into evidence about the plant's present state, keeps symptoms in a block of their own linked only as consistent with, never averages two weather sources, and reports every factor as no source when nothing was supplied."
---

# Assess what the weather means for a plant

Turns weather into exposures a person can weigh: what the plant is exposed to, against which threshold, and which part of its care, health or harvest timing that may touch. A weather fact is about the site, never about the plant: it says what the plant is exposed to, not what happened to it. A symptom comes only from a photo reading, a diary entry or a recorded inspection, and stays in a block of its own. Gathering the plant's facts is `plant-context-collect`, the weight of a claim is `decision-policy`. It writes nothing; an assessment is a statement to a person, never an instruction to a device.

## Input

- **The plant context block** from `plant-context-collect`: species (`frost_sensitivity`, `hardiness_zones`), the resolved phase and its definition (`stress_tolerance`), `location_name`, the inspections, the gaps list.
- **Caller facts**, each optional, taken as written and marked `caller`: weather and forecast, in the caller's words and units; where the plant stands (outdoors, sheltered, indoors); and thresholds the caller wants a factor judged against.
- **Symptoms**, optional: findings of `plant-photo-read`, diary entries and recorded inspections already in the blocks. This skill reads no photo and no diary itself.
- **Whether a Home Assistant read is permitted**, from the caller, or **a reading the caller already made** with `GetLiveContext`. Without an explicit permission it is not: the daily check, for one, calls no Home Assistant tool. A reading the caller hands over is used as given, and this skill makes no call of its own.

Without the plant context block, rate the factors only (steps 1, 2 and 4), say that no plant impact can be stated, and say that `plant-context-collect` must run for one.

## Procedure

### 1. Collect the weather

- **The caller's weather** is the first source. Mark it `caller`.
- **Home Assistant**, only where the caller permitted it and did not hand over a reading already: if a tool named `GetLiveContext` is present, call it once with `domain: weather` and keep what it returns, as returned, marked `home_assistant (unmeasured)` with its retrieval time. Whether the instance exposes a weather entity, and its fields, is not measured. If the tool is absent, say so by name; if it returns no weather entity, say so. Never read another domain, and never use a sensor of any kind as evidence about the plant: no mapping from a sensor to a plant is recorded. A snapshot is one point in time; it is not a series and not a forecast.
- **Neither source**: every factor is `no source`. Say what cannot be concluded: whether the plant is or will be exposed to frost, heat, rain, wind or a humidity extreme, and therefore whether care, health or harvest timing is affected by the weather at all.

Both sources are level 6. When they disagree on the same factor, report the contradiction with both values side by side, and never average them or pick the more fluent one.

### 2. Rate each factor

For each of these six factors, give exactly one status:

| Factor | `exposure` when the supplied data |
|--------|-----------------------------------|
| temperature extremes | name a minimum or maximum that reaches a threshold of step 3, or name frost or a heat spell |
| rainfall | name rain, heavy rain, hail or a dry spell |
| wind | name strong wind, gusts or a storm |
| humidity | give a relative humidity, or name fog, persistent wet or very dry air |
| heat and cold events | name a heatwave, a frost night or a cold snap |
| forecast changes | describe a change between now and the forecast (a drop, a rise, rain arriving, frost returning) |

`no exposure in the supplied data` when the data cover the factor and name nothing of the above; `no source` when no data cover it. A forecast is a forecast: report it as expected, never as having happened.

### 3. Judge against a threshold

An exposure is judged only against a threshold that has a source, named with its level:

- a caller threshold (`caller`);
- the species `frost_sensitivity` or `hardiness_zones` and the phase's `stress_tolerance` (level 4), read literally: their value sets are not recorded, so state the value as read and do not assume its meaning;
- general knowledge, only labelled as level 8 and not from the record (for example "air at or below 0 °C is frost").

With no threshold, say `no threshold recorded` and leave the impact `not assessed`. The comparison of a weather value with a threshold is level 6 at best: a claim that rests on two items takes the level of the weaker.

### 4. Derive the vapour pressure deficit, where possible

Only from a temperature and a relative humidity taken at the same time and place, both from the caller or both from the same Home Assistant reading. Use

`VPD (kPa) = 0.6108 × exp(17.27 × T / (T + 237.3)) × (1 − RH / 100)`, `T` in °C,

and state the formula and both inputs. The value is air VPD, `no level`, and is reported without judgement: no species or phase VPD target is recorded. `search_glossary` defines VPD; a definition is not evidence. Refuse a diary `measurements` key whose meaning or unit is ambiguous, and say that you did.

### 5. Name the likely impact

For each exposure, name the area it is likely to affect: **care** (watering, protection, moving the plant), **health** (stress, damage, a condition that favours a pest or disease), or **harvest timing** (development slowed or hastened, a crop at risk). State it as an exposure or an expected risk, with its threshold and level. When the caller did not say where the plant stands, make it conditional ("if the plant stands outdoors") and list the placement as missing: the record has no source for a site's attributes. A plant the caller places indoors is not exposed to outdoor weather; say so instead of listing the factor's impact.

### 6. Keep symptoms apart

List the symptoms in their own block, each with its source: a `plant-photo-read` finding (no level), a diary entry, or a recorded inspection (level 3). Never derive a symptom from the weather, and never state an exposure as a symptom ("the frost damaged the leaves" is a symptom claim no weather source can make). A symptom and an exposure may be linked only as "consistent with", which is a suspicion under rule 1 of `decision-policy`, never a diagnosis.

### 7. Weigh it

Apply `decision-policy`: evidence (level, source, retrieved-at, one entry each), confidence from the highest level that supports it, uncertainty (what would change it), and missing data (each input it did not have, with the observation that would supply it).

### 8. Report

Return, in this order:

```
WEATHER IMPACT
  plant:      <plant key>
  sources:    caller | home_assistant (unmeasured) | none; HA read: permitted | not permitted; <tool absent | no weather entity, where so>
  placement:  outdoors | sheltered | indoors (caller) | not stated
  contradictions: <factor: caller value vs home_assistant value> | none
FACTORS
  <factor>: exposure | no exposure in the supplied data | no source
    data:      <what the source said, with source and retrieved-at>
    threshold: <value, source, level> | no threshold recorded
    impact:    <care | health | harvest timing: the expected risk, conditional on placement where needed> | not assessed | none (indoors)
VPD
  value: <kPa, with both inputs and the formula> | absent (<reason>)   level: no level
CANNOT CONCLUDE
  <what the supplied data do not allow to be said>
SYMPTOMS (NOT FROM WEATHER)
  <symptom, source, level> | none supplied
  link: <symptom> consistent with <exposure> | none
HAND-OFF: PLANT HEALTH
  exposures: <factor and impact, one per exposure>
  symptoms:  <as above, kept separate>
FINDING
  domain: weather | subject: <plant key> | kind: recommendation or observation
  statement / evidence / confidence / what would change it / missing data
  consequence: <only if an input states one, otherwise absent>
```

Give one finding per exposure and one for the factors with no source. **An exposure judged against a recorded threshold (caller or level 4), for a plant the caller places outdoors or sheltered, is a recommendation**: a proposal to a person to protect, move or check the plant. Every other result is an observation, including an exposure judged only against general knowledge or with the placement not stated. No state-changing tool exists for any of it: a named mutation is `no tool measured`. Return no field that was not read. The facts two runs over the same input must agree on are the factor statuses, the thresholds and their levels, the impacts, the findings' kinds and the missing-data list; retrieval times and prose may differ, and byte-identical prose is not claimed.

## Hard rules

- Never state weather as a plant symptom or as evidence about the plant's present state.
- Never take a symptom from anything but a photo reading, a diary entry or a recorded inspection, and never link it to weather more strongly than "consistent with".
- Never average two weather sources; report a disagreement side by side.
- Never fill an absent factor, a threshold or the placement, and never invent a measurement.
- Never call a Home Assistant tool without the caller's permission, never call one other than `GetLiveContext`, and never read a domain other than `weather`. Never turn anything on or off, set a value, or run a script, scene or automation, and never call `TimeTillErnte` or `time_till`: their effect is unclassified.
- Never read the current date into the facts.
- Call no tool that changes state. Forbidden by name: `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`, `mcp__kamerplanter__submit_diary_analysis`, `mcp__kamerplanter__transition_plant_phase`, `mcp__kamerplanter__assign_species_phase_sequence`, `mcp__kamerplanter__assign_nutrient_plan`, `mcp__kamerplanter__record_feeding_event`, `mcp__kamerplanter__create_inspection`. This skill calls no Kamerplanter tool at all.

## Gotchas

- Most runs without a `weather` parameter end with every factor `no source`. That is the honest result: the measured Kamerplanter catalog has no weather tool.
- The value sets of `frost_sensitivity` (measured `sensitive` and `hardy`) and `stress_tolerance` are not recorded. A threshold read from them is quoted, not interpreted.
- The decision policy ranks species data (level 4) above weather (level 6), yet a frost is a question where the weather decides. This skill does not re-rank; it reports the exposure at level 6 and the threshold at its own level, and the open question stays with the decision policy.
- This skill itself was not run against a live instance, and the Home Assistant weather entity is unmeasured; treat the first real run as the measurement.

## Source

Governed by `spec/process/growth-stage-and-weather-impact/en.md` §A, §C, §D, §E, §F, §G and §H.
