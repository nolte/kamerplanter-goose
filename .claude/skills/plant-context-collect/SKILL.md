---
name: plant-context-collect
description: "Collects and normalises the full analysis context for one Kamerplanter plant instance — instance master data, species baseline, resolved growth phase, care history, and IPM history — over the kamerplanter MCP server. Use when a recipe or another skill must judge an observation against what is normal for this specific plant, for example before reading a diary photo, before assessing a nutrient question, or when asked to establish what a plant's current state should look like. Returns a structured context block plus an explicit list of the fields that were absent."
---

# Collect plant instance context

Establishes what *normal* means for one plant, so a later step can measure an observation against it. Gathering this is a separate unit of work from interpreting it: this skill never diagnoses, never reads photos, and never writes.

Every tool below is on the `kamerplanter` MCP server and is addressed as `mcp__kamerplanter__<tool>`. All of them are read-only.

## Procedure

### 1. Resolve the garden and permissions

Call `mcp__kamerplanter__list_tenants`. Take the `tenant` slug from the caller when given, otherwise the single slug returned. Record the `mcp_permissions` array verbatim — a later write step depends on it, and role names are not a reliable substitute.

### 2. Anchor on the plant

With a `plant_key`, call `mcp__kamerplanter__get_plant`. With an `entry_key` instead, call `mcp__kamerplanter__get_diary_entry`, which already carries the plant context inline and saves a call.

Record: `plant_key`, `instance_id`, `species_key`, `cultivar_key`, `current_phase`, `phase_started_at`, `planted_on`, `location_name`.

### 3. Species baseline

Call `mcp__kamerplanter__get_species_info` with the `species_key`. When `cultivar_key` is set, also call `mcp__kamerplanter__get_cultivar` — its `traits` and `days_to_maturity` narrow the species expectation to the variety.

Carry these fields forward; each one shifts what counts as normal:

| Field | Governs |
|-------|---------|
| `plant_category` | Which pest, disease, light and humidity situations are plausible at all |
| `growth_habit` | Whether trailing or sprawling growth is the plant working correctly or a symptom |
| `root_type` | How fast drought stress appears and how it presents |
| `nutrient_demand_level` | Whether a deficiency reading is plausible under the recorded feeding history |
| `frost_sensitivity`, `hardiness_zones` | Whether cold damage is admissible at this date and location |
| `bloom_months`, `harvest_months` | Whether flowers or fruit are on schedule, early, or overdue |
| `allows_harvest`, `harvest_pattern` | Whether ripeness is a question worth asking |
| `base_temp_gdd` | How much growth to expect since `planted_on` |
| `toxicity` | Never the health reading — only handling and consumption advice |

`compatible_companions` concerns planting decisions, not plant health. Do not carry it into a health judgement.

### 4. Resolve the phase

Call `mcp__kamerplanter__list_phase_definitions` and match `current_phase`. The definition carries `stress_tolerance`, `watering_interval_days`, and `typical_duration_days`.

Compute and record: whether `phase_started_at` plus `typical_duration_days` is already in the past. An overdue phase reframes "not flowering yet" from normal to notable.

### 5. Care and pressure history

Call `mcp__kamerplanter__get_plant_care_log` and `mcp__kamerplanter__get_plant_inspections`.

From the care log, record the most recent `confirmed_at` per `reminder_type`, and every entry whose `action` is `snoozed`. A repeatedly snoozed repotting means exhausted substrate, which produces symptoms that look like undersupply.

From the inspections, record prior pest and disease pressure on this individual. An empty history is not an absence of pests — it is an absence of *recorded* pests, and must be reported as such rather than as a clean bill of health.

### 6. Report

Return one context block containing the fields above, plus a **gaps list**: every field consulted that was absent, null, or empty.

The gaps list is not a footnote. A missing field means the corresponding question cannot be asked, and the caller must narrow its analysis instead of substituting a general assumption about plants.

## Hard rules

- Never infer the species from anything other than `species_key`. If a caller reports a photo that appears to show a different plant, that contradiction is the caller's finding to report, not a reason to re-anchor this context.
- Never fill an absent field with a typical value, a genus-level guess, or a general assumption. Absent goes into the gaps list.
- Judge all timing against the date of the observation being analysed — a diary entry's `created_at` — never against today, unless the caller states there is no observation date.
- Call no tool that changes state. On this server that means these are out of bounds.
  Forbidden by name:
  `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`,
  `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`,
  `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`,
  `mcp__kamerplanter__submit_diary_analysis`.
- Report a tool error verbatim and continue with the remaining steps. A partial context with a named gap is useful; a context that hides a failed call is not.

## Gotchas

- `mcp__kamerplanter__get_diary_entry` returns the plant context inline but **no image data**. Photos come from `mcp__kamerplanter__get_diary_entry_photos`, which is a different concern and belongs to the caller.
- `mcp__kamerplanter__get_plant_nutrient_plan` frequently returns `{"plan": null}` — no plan assigned is an ordinary state, not an error. This skill does not call it; the nutrient path does.
- `mcp__kamerplanter__list_tenants` returns `mcp_permissions` directly. Deriving permissions from the role name is unreliable: undocumented roles exist on real instances.
- The tenant argument is optional only when the key grants exactly one garden. With several, omitting it fails.
- An empty `mcp__kamerplanter__get_plant_inspections` result is the normal state for a plant tended only through agents, because agents currently have no tool for writing an inspection back.

## Source

Derived from `spec/process/plant-health-image-analysis/` §"What the species changes" and §"What the instance changes", measured against the reference instance on 2026-08-05.
