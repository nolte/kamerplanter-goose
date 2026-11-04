---
name: rotation-history-collect
description: "Collects what a crop rotation needs from one Kamerplanter garden over the kamerplanter MCP server — each crop's family_key, nutrient demand class and green-manure suitability, the garden's current and archived plants per location, and the inspections of plants at locations that match a caller's bed — and reports every field as present or absent with its source, level or reason. Use before crop-rotation-planning, or when asked what the catalog knows about a garden's bed history and crop families. Never recalls a family, never reads compatible_companions as rotation, and never treats a failed or partial read as no history."
---

# Collect the rotation history

Reads, once and with sources, what a rotation plan is judged against. Gathering is a separate unit of work from planning: this skill never selects a crop for a bed, never judges a rotation and never writes. Planning is `crop-rotation-planning`, the garden's general context is `garden-context`, the weight of a claim is `decision-policy`.

Every tool below is on the `kamerplanter` MCP server and is addressed as `mcp__kamerplanter__<tool>`. All of them are read-only. **Not re-measured**: tool and field names come from `spec/mcp/kamerplanter-mcp-server/en.md` and `spec/process/species-baseline-verification/en.md`; what an archived plant carries and what an inspection record carries beyond pressure level, symptoms and structured findings is unrecorded.

## Input

- **tenant**: from the `garden-context` block when the caller has one; otherwise resolve it as `garden-context` step 1 does (`mcp__kamerplanter__list_tenants`, the caller's slug checked against the list, a single slug used only when it is the only one).
- **crops**: entries `species_key` or `species_key:cultivar_key`, the candidate crops and every crop named in a pin.
- **history crops**: the crops named in the caller's bed history, same shape. `none` names no crop.
- **beds**: the bed names of the plan: the caller's beds, the beds in the bed history and the beds in a pin, each name being the text before the first colon.

Split every list at its commas and every entry at its colons; never pass the joined text on as a key.

## Procedure

### 1. The plants of the garden, archived included

Call `mcp__kamerplanter__list_plants` with `tenant`, `limit 200` and `include_archived: true`. Page with `offset` while the response reports `truncated: true`, and stop after 20 pages, reporting the read as `partial` with that reason. The cap is a guard, not a measured limit. Record the read as `complete`, `partial: <reason>` or `failed: <error verbatim>`.

Record, per plant: `plant_key`, `species_key`, `cultivar_key` if the record carries one, `location_key`, `planted_on`, and whether it is archived as the record states it. Which field marks a plant archived is not recorded: report `archived: not recorded` when no field says so, and never infer it from `matched` against `total_in_tenant`.

Then sort each plant's location:

- **mapped**: its `location_key` equals a bed name exactly, as text. Nothing else maps: no case folding, no prefix, no similarity, no site key.
- **unmapped**: every other location, kept as `unmapped location history`, context only.

A plant's season is the year of `planted_on`. A plant without `planted_on` has season `unknown`. A plant without `location_key` is unmapped with the reason `no location_key`.

### 2. Family, demand class, green manure

Call `mcp__kamerplanter__get_species_info` once per **distinct** `species_key` among the crops, the history crops and the plants at mapped locations. Do not read species of unmapped plants; they are context only. Call `mcp__kamerplanter__get_cultivar` only for a `cultivar_key` that an entry or a mapped plant names.

Record per crop, for each of `family_key`, `nutrient_demand_level` and `green_manure_suitable`:

- `present`, with the value as recorded, the tool, the retrieval time, level 4, and `cultivar` or `species` for where it came from. The cultivar's value comes first when the cultivar carries the field.
- `absent`, with the reason `not populated` when the response lacks the key, or the tool error verbatim. A missing key means not populated for that species, never "does not apply" and never "no family".

Do not read `compatible_companions[]` for this purpose; it is about planting side by side and is not a rotation relation. Do not derive a family from the genus, the scientific name or a common name, and never fill one from memory or research. Report every other soil effect as `not modeled`.

### 3. Inspections at mapped beds

For each plant at a mapped location, call `mcp__kamerplanter__get_plant_inspections` with `plant_key` and `tenant`. Record per plant: `none recorded` for an empty history, the inspection records as returned (date, and what the record names: a pest, a disease, a pressure level, symptoms, findings), or the tool error verbatim. Do not judge the content: no host range is recorded on `get_pest` or `get_disease`, so this skill does not say which future crop a recorded pressure affects. Do not call it for unmapped plants.

### 4. Report

Return one block:

```
ROTATION HISTORY: <tenant> (given | discovered)
CATALOG READ: complete | partial: <reason> | failed: <error>
CROPS:
  <species_key/cultivar_key|none>:
    family_key:            present <value> (<tool>, <retrieved>, level 4, cultivar|species) | absent: <reason>
    nutrient_demand_level: present <value> (...) | absent: <reason>
    green_manure_suitable: present <value> (...) | absent: <reason>
HISTORY CROPS:
  <species_key/cultivar_key|none>: <same three fields>
MAPPED HISTORY:
  <bed>: <plant_key> <species_key/cultivar_key|none> season <year|unknown> archived <yes|no|not recorded> (list_plants, <retrieved>, level 5)
UNMAPPED LOCATION HISTORY:
  <location_key|no location_key>: <plant_key> <species_key> season <year|unknown>   (context only)
INSPECTIONS:
  <bed>: <plant_key>: none recorded | <records as returned> (get_plant_inspections, <retrieved>, level 3) | error: <verbatim>
NOT MODELED: soil effects other than green_manure_suitable
ABSENT FIELDS: <field (reason), ...>
```

A bed with no mapped plant is listed under `MAPPED HISTORY` as `<bed>: none mapped`. That is not evidence that nothing grew there; say so when the catalog read was not `complete`.

## Hard rules

- Never fill an absent family, demand class or green-manure field. Absent goes into the absent-fields line with its reason.
- Never read `compatible_companions[]` as a rotation relation.
- Never attach a catalog plant to a bed except on exact `location_key` equality.
- Never report a partial or failed read as "no history".
- Never call a per-plant tool for an unmapped plant.
- Pass `tenant` on every call that takes it; `get_species_info` and `get_cultivar` serve the shared catalog and take none.
- Call no tool that changes state. Forbidden by name: `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`, `mcp__kamerplanter__submit_diary_analysis`, `mcp__kamerplanter__transition_plant_phase`, `mcp__kamerplanter__assign_species_phase_sequence`, `mcp__kamerplanter__assign_nutrient_plan`, `mcp__kamerplanter__record_feeding_event`, `mcp__kamerplanter__create_inspection`.
- Report a tool error verbatim, mark the affected field absent with that error as the reason, and continue.

## Gotchas

- `family_key` and `nutrient_demand_level` were observed on two species in a union table; whether every species carries them is unrecorded. A block with many `absent` families is the honest result, not a failed run.
- `matched` counts what the filter returned and `total_in_tenant` counts every plant; with `include_archived: true` the two may agree. Neither marks an individual plant archived.
- Whether an archived plant keeps `location_key` and `planted_on` is not recorded. An archived plant without them is unmapped or season `unknown`, never dropped.
- This skill itself was not run against a live instance.

## Source

Governed by `spec/process/crop-rotation-planning/en.md` §B and §C; fields from `spec/process/species-baseline-verification/en.md` (measured 2026-08-07) and `spec/mcp/kamerplanter-mcp-server/en.md`; list-response fields and paging from `.claude/skills/garden-context/SKILL.md`.
