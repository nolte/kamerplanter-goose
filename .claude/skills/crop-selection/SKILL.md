---
name: crop-selection
description: "Judges candidate species and cultivars against a site profile and the grower's goals: each candidate gets a verdict (eligible, rejected or undetermined), its reasons, the hard constraints it failed with source and evidence level, and its preferences met, unmet or unknown. Use when a recipe or skill must say what could be grown on a site, why a crop was ruled out, or what is not known well enough to decide. Hard constraints reject and are never traded off; preferences only rank; an unknown site parameter or an absent species field leaves a constraint undetermined, never met and never failed."
---

# Select crops for a site

Takes a site profile and a pool of candidates and returns, per candidate, a verdict with the reasons for it. It recommends no planting plan: when and where to plant is planning, not this skill. It writes nothing.

The profile comes from `site-analysis`; the weight a claim carries and the shape of a recommendation are `decision-policy`'s. Every tool below is on the `kamerplanter` MCP server and is addressed as `mcp__kamerplanter__<tool>`. All of them are read-only.

## Input

- **The site profile block** from `site-analysis`. Without it, stop and say `site-analysis` must run first.
- **The garden context block** from `garden-context`, for the crops already in the garden (companion fit).
- **The candidate pool**: entries separated by commas, each a `species_key`, or a `species_key` and a `cultivar_key` joined by a colon (`<species_key>:<cultivar_key>`). Split the string at the commas and at the first colon of each entry, and pass the parts to the tools one by one, never the joined text. An entry that is a name and not a key is resolved in step 2.
- **Goals and a harvest window**, both optional and taken from the caller verbatim.

## Procedure

### 1. Check the inputs

Both blocks must be present. A missing block is a stop, not something to collect here.

### 2. Fix the pool

Use the caller's pool. For a name instead of a key, read one bounded page of `mcp__kamerplanter__list_species` and match the name exactly; a name that does not match is a candidate with verdict `undetermined`, reason "not resolved". The parameters of `list_species` are not recorded in the specs, so pass nothing but what is needed and report the page size you got.

When the caller gave no pool, read one bounded page of `mcp__kamerplanter__list_species` and use it as a **sample**. Say so in the pool block, with its size, and that the rest of the catalog was not considered. Judge at most 10 candidates per run, a guard and not a measured limit, and list the rest as not considered.

### 3. Read each candidate

Call `mcp__kamerplanter__get_species_info` with the `species_key`, and `include_cultivars` when a cultivar is named. Take cultivar fields from the nested `cultivars[]`; the cultivar's value is used when it carries the attribute and the species' value otherwise, and every attribute used is recorded as `cultivar` or `species`. The species record returns only its populated fields: an absent key means "not populated", never "does not apply".

### 4. Judge the hard constraints

A hard constraint is formed only where the field was observed present and both sides are known. Otherwise it is `undetermined`.

| Constraint | Species side | Site side |
|------------|--------------|-----------|
| Frost sensitivity against the garden's frost dates | `frost_sensitivity` | the frost dates in the site profile |
| Hardiness zone against the garden's zone | `hardiness_zones[]` | the garden's zone, only if the caller supplied it |

The value set of `frost_sensitivity` is not recorded: form the constraint only where a value reads unambiguously, otherwise `undetermined`. No constraint is formed from light, shade, waterlogging or soil pH: `shade_tolerance`, `waterlogging_tolerance` and `soil_ph_preference` were measured absent on the two species probed, and substrate properties have no species-side requirement to meet. List those as not formed, not as met.

### 5. Judge the preferences

A preference ranks; it never rejects. Report each as `met`, `unmet` or `unknown`:

- **Timing against the harvest window**: choose the entry of `growing_periods[]` that applies and say which; the top-level `direct_sow_months[]`, `harvest_months[]` and `bloom_months[]` are the union across periods. `sowing_indoor_weeks_before_last_frost` is read against the frost dates.
- **Days to maturity against the frost-free span**: the cultivar's `days_to_maturity`. What it counts from, sowing or transplant, is not recorded: report the comparison with that stated, or `unknown` when the frost dates are not in a readable form.
- **Companion fit**: `compatible_companions[]` with its `score`, against the crops the garden context lists. The field lists compatible companions, so a pair that is not listed is `unknown`, never incompatible.
- **Goals**: a goal is `met`, `unmet` or `unknown` against the fields it can be read from. A goal no field speaks to is `unknown`.

### 6. Decide the verdict

Per constraint: `met`, `failed` or `undetermined`. Per candidate:

- `rejected` when at least one hard constraint failed. List it with its values, source tool, retrieval time and evidence level.
- `eligible` when every hard constraint that could be formed is met and none is undetermined.
- `undetermined` otherwise, including when no hard constraint could be formed at all.

Never return `eligible` with an undetermined hard constraint. Apply `decision-policy` to the verdict: evidence with levels, a confidence derived from the highest level that supports it, what would change it, and the inputs that were missing. A verdict resting on a caller-supplied site fact says so.

### 7. Report

Return three blocks, in this order and under these names. Copy the site profile block unchanged.

```
SITE PROFILE: <as received from site-analysis>
POOL: <caller | sample> (<n> candidates; <m> not considered)
CANDIDATE
  species_key:                 <key>
  cultivar_key:                <key | none>
  verdict:                     eligible | rejected | undetermined
  reasons:                     <one line each: field, value; met hard constraints are named here>
  failed_hard_constraints:     <constraint — values; tool; retrieved; evidence level>  (rejected)
  undetermined_constraints:    <constraint — what is missing>
  constraints_not_formed:      light, shade, waterlogging, soil pH
  preferences:                 <preference>: met | unmet | unknown — <why>; <tool>
  attribute_origins:           <attribute>: cultivar | species
  confidence:                  <level and what it rests on>
  uncertainty:                 <what would change the verdict>
  missing_data:                <inputs it would have used>
SELECTION: <e> eligible, <r> rejected, <u> undetermined
UNKNOWN SITE PARAMETERS: <as listed by site-analysis>
```

## Hard rules

- Never reject a candidate on a preference, and never weigh a failed hard constraint against a preference.
- Never return `eligible` for a candidate with an undetermined hard constraint.
- Never form a hard constraint from a field that was not observed present.
- Never treat a missing list, a missing field or a missing companion entry as evidence either way.
- Never report a pool read from `list_species` as the catalog.
- Never report a field the skill did not read.
- Pass `tenant` where a tool takes it; `get_species_info` does not.
- Call no tool that changes state. Forbidden by name: `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`, `mcp__kamerplanter__submit_diary_analysis`, `mcp__kamerplanter__transition_plant_phase`, `mcp__kamerplanter__assign_species_phase_sequence`, `mcp__kamerplanter__assign_nutrient_plan`, `mcp__kamerplanter__record_feeding_event`, `mcp__kamerplanter__create_inspection`.
- Report a tool error verbatim, mark the affected constraint `undetermined` with the error as the reason, and continue.

## Gotchas

- `get_species_info` was measured returning 23 fields for one species and 18 for another; a field that is missing for a species is not populated, and that is the whole reason a constraint becomes undetermined.
- `growing_periods[]` is the field a naive reading misses: one species carried a summer and a winter period, each with its own months.
- This skill itself was not run against a live instance. Field names come from `spec/process/species-baseline-verification/en.md`, measured on 2026-08-07, on two species; whether other species carry more is not established.

## Source

Governed by `spec/process/site-analysis-and-crop-selection/en.md` §B to §F.
