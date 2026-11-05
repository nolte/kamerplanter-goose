---
name: companion-spacing-collect
description: "Collects what a bed layout reads from the Kamerplanter catalog over the kamerplanter MCP server — each crop's compatible_companions list with its scores and its seed_profile.sowing_density_per_m2 as context — once per distinct species, and reports every field as present or absent with its origin, level or reason. Use before bed-layout-planning, or when asked which companions the catalog lists for a set of crops. Never infers an incompatibility, never reads an unlisted pair as incompatible, and never supplies a spacing or a density."
---

# Collect companions and seed density

Reads, once and with sources, the two catalog fields a bed layout uses. Gathering is a separate unit of work from laying out: this skill places nothing, ranks nothing and writes nothing. Laying out is `bed-layout-planning`, the weight of a claim is `decision-policy`.

Every tool below is on the `kamerplanter` MCP server and is addressed as `mcp__kamerplanter__<tool>`. The one it calls is read-only. **Not re-measured**: tool and field names come from `spec/mcp/kamerplanter-mcp-server/en.md` and `spec/process/species-baseline-verification/en.md`; the range and direction of `score`, the shape of a companion entry beyond the species it names, and the unit of `sowing_density_per_m2` are unrecorded.

## Input

- **crops**: entries `species_key` or `species_key:cultivar_key`, or crop keys `species_key/cultivar_key` with `none` for no cultivar, as the planting runs carry them. Split every list at its commas and every entry at its first colon or slash; never pass the joined text on as a key.

## Procedure

### 1. Read each species once

Call `mcp__kamerplanter__get_species_info` once per **distinct** `species_key` among the crops, with `include_cultivars` when any crop of that species names a cultivar. Call no other tool. The species record returns only its populated fields: an absent key means not populated for that species, never "does not apply".

### 2. Record per crop

For each crop, keyed `species_key/cultivar_key` (`none` for no cultivar):

- **companions**: `compatible_companions[]` as recorded. Take the cultivar's list when the cultivar record carries one, and the species list otherwise; record which (`cultivar` or `species`). For each entry record the species it names, as text, and its `score` exactly as recorded, with `numeric` or `not comparable` beside it. An entry that names no species key you can read is listed verbatim as `entry not comparable`. An absent list is `absent — not populated`.
- **seed density**: `seed_profile.sowing_density_per_m2` as recorded, with its origin (`cultivar` or `species`), marked `context only — unit semantics not recorded`. Absent is `absent — not populated`.

Every present field carries the tool, the retrieval time and level 4.

Do not read any other field for this purpose. A pair that the list does not name is `unknown`, never incompatible and never compatible; no field records an incompatibility, so this skill reports none. Never derive a spacing from the seed density, from the thousand-seed weight or from anything else, and never supply one from memory.

### 3. Report

Return one block:

```
COMPANION SPACING: <tenant, or catalog — shared across gardens>
CROPS:
  <species_key/cultivar_key|none>:
    companions:   (<cultivar|species>, get_species_info, <retrieved>, level 4)
      <species named>: score <value as recorded> (numeric | not comparable)
      entry not comparable: <entry verbatim>
    | absent — not populated | error: <verbatim>
    seed density: <value> (<cultivar|species>, get_species_info, <retrieved>, level 4; context only — unit semantics not recorded) | absent — not populated
NOT RECORDED: incompatibility (no field), spacing (no field), the range and direction of score
ABSENT FIELDS: <crop: field (reason), ...>
```

## Hard rules

- Never read an unlisted pair as incompatible, and never report an incompatibility.
- Never supply a spacing, a plant count or a density, and never turn the seed density into one.
- Never fill an absent field. Absent goes into the absent-fields line with its reason.
- Read each species once; `get_species_info` serves the shared catalog and takes no `tenant`.
- Call no tool that changes state. Forbidden by name: `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`, `mcp__kamerplanter__submit_diary_analysis`, `mcp__kamerplanter__transition_plant_phase`, `mcp__kamerplanter__assign_species_phase_sequence`, `mcp__kamerplanter__assign_nutrient_plan`, `mcp__kamerplanter__record_feeding_event`, `mcp__kamerplanter__create_inspection`, `mcp__kamerplanter__clone_nutrient_plan`, `mcp__kamerplanter__set_nutrient_plan_phase_targets`, `mcp__kamerplanter__create_substrate_mix`, `mcp__kamerplanter__set_plant_substrate`.
- Report a tool error verbatim, mark the affected fields absent with that error as the reason, and continue.

## Gotchas

- `compatible_companions[]` with `score` was observed on two species on 2026-08-07; whether every species carries it, and what a score of a given value means, is unrecorded. A block full of `absent` lists is the honest result, not a failed run.
- `sowing_density_per_m2` was measured on `Allium porrum` only. It may count seeds rather than plants; that is why it is context and never a capacity.
- Whether a cultivar record carries its own companion list is not recorded; most crops will report `species`.
- This skill itself was not run against a live instance.

## Source

Governed by `spec/process/bed-layout-and-succession-planning/en.md` §A and §B; fields from `spec/process/species-baseline-verification/en.md` (measured 2026-08-07) and `spec/mcp/kamerplanter-mcp-server/en.md`.
