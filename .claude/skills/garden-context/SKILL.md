---
name: garden-context
description: "Collects and normalises the context of one Kamerplanter garden over the kamerplanter MCP server — site and location keys, crops and cultivars, planting runs, growth stage, substrates, due care tasks — and reports every field as present or absent with its source or its reason. Use when a recipe or another skill must know what a garden holds before advising on it, before planning anything across plants, or when asked what is and is not known about a garden. Never fills a field it could not read: beds, containers, weather and user goals have no source in the measured catalog and come back absent."
---

# Collect a garden's context

Establishes what is known about one garden, and what is not, so a later step can advise on it without guessing. Gathering is a separate unit of work from deciding: this skill never recommends, never diagnoses, never reads a photo and never writes. Weighing what it returns is `decision-policy`; the context of a single plant is `plant-context-collect`.

Every tool below is on the `kamerplanter` MCP server and is addressed as `mcp__kamerplanter__<tool>`. All of them are read-only.

## Input

- **tenant** (optional): the garden's slug. When absent, resolve it as in step 1.
- **goals** (optional): the grower's goals and constraints, if the caller holds them. The server has no source for these, so they enter only from the caller and are marked as such.

## Procedure

### 1. Resolve the garden and permissions

Call `mcp__kamerplanter__list_tenants`. Take the `tenant` slug from the caller when given. Without one, use the slug `list_tenants` returns only when it returns exactly one, and say in the report that it was discovered; several slugs and none given is a stop, not a guess. Record the `mcp_permissions` array verbatim. Pass `tenant` on every later call.

### 2. Read the plants

Call `mcp__kamerplanter__list_plants` with `limit 200` and `include_archived` false. Page with `offset` while the response reports `truncated: true`, and stop after 20 pages: report the field as incomplete with that as the reason rather than looping. The cap is a guard, not a measured limit. `matched` is the denominator; `total_in_tenant` counts archived plants and is not.

Record, per plant: `species_key`, `site_key`, `location_key`, `substrate_key`, `planted_on`, `current_phase_key`. These fields come back on the list response, so a per-plant `mcp__kamerplanter__get_plant` adds a round trip and nothing else.

This step fills **site and location** (the keys only), **growth stage** (the phase key only) and the plant side of **crops and cultivars** and **soil and substrate**.

### 3. Crops and cultivars

Call `mcp__kamerplanter__get_species_info` once per **distinct** `species_key`, never once per plant. Call `mcp__kamerplanter__get_cultivar` only for a cultivar a plant references. The cultivar's data is the more specific of the two and is carried as such.

### 4. Planting runs

Call `mcp__kamerplanter__list_planting_runs`. Pass nothing but `tenant`; the server spec names no filter for it. Pagination behaviour is unmeasured: if the response looks partial, say so in the field's value; never report a partial list as complete.

### 5. Substrates

Call `mcp__kamerplanter__list_substrates` and match each plant's `substrate_key`. A key with no match is a gap, not a default.

### 6. Care state

Call `mcp__kamerplanter__get_due_care_tasks`. A due task is a request from the schedule, not a measurement of the plant's state; carry it as that. This is the only care source read at garden level: the care log is per-plant. State in the value that it holds due tasks only, and that an empty list is not evidence of recent care.

### 7. Everything the garden level does not hold

Mark these fields absent and give the reason. The reason names its kind: `no source` (the measured catalog offers none) or `not collected` (a source exists but is read per plant, not at garden level):

| Field | Reason |
|-------|--------|
| Beds and containers | `no source`: the server spec names no tool that says whether a location is a bed or a container |
| Weather | `no source` |
| Current measurements, historical observations | `not collected`: per-plant evidence, collected by `plant-context-collect` and the diary, not at garden level |
| Site attributes (beyond the keys) | `no source`: no read tool for a site's own attributes is named in the server spec |
| User goals and constraints | Present only if the caller supplied them; otherwise `no source` |

### 8. Report

Return one block with an entry per field of the policy's garden context, each `present` or `absent`:

```
GARDEN CONTEXT: <tenant> (given | discovered)
<field>: present | absent
  source:    <tool, or "caller">        (present)
  retrieved: <timestamp>                 (present)
  value:     <what was read>             (present)
  reason:    <kind>: <why>               (absent)
PLANTS:  <matched>
SPECIES: <distinct species_key, with cultivar_key where a plant has one>
ABSENT FIELDS: <field (kind), field (kind), ...>
```

The absent-fields line is its own line at the end, separate from the data. A missing field means the corresponding question cannot be asked, and the caller narrows its analysis instead of substituting a general assumption about gardens.

## Hard rules

- Never fill an absent field with a typical value, a default, or a guess. Absent goes into the absent-fields line with its reason.
- Never read beyond what the garden holds: a field with no source in the measured catalog is absent even if a plausible value is obvious.
- Never call a per-plant tool for every plant. Plant-level evidence is the caller's request, made for the plants it names.
- Pass `tenant` on every call; never rely on a default membership.
- Call no tool that changes state. Forbidden by name: `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`, `mcp__kamerplanter__submit_diary_analysis`, `mcp__kamerplanter__transition_plant_phase`, `mcp__kamerplanter__assign_species_phase_sequence`, `mcp__kamerplanter__assign_nutrient_plan`, `mcp__kamerplanter__record_feeding_event`, `mcp__kamerplanter__create_inspection`.
- Report a tool error verbatim, mark the affected field absent with that error as the reason, and continue. A partial context with a named gap is useful; one that hides a failed call is not.

## Gotchas

- `mcp__kamerplanter__list_plants` carries `matched` and `total_in_tenant`; only `matched` is the page-completion denominator, measured on the reference garden for `recipes/plant-master-data-check.yaml` as `matched: 9` against `total_in_tenant: 11` with `truncated: false`; that earlier measurement is the only one behind this step.
- `mcp__kamerplanter__get_plant_phase_status` can answer `phase_state: unresolved`, which reads as a normal result and is not. This skill reads the phase key from the list response and does not call it; a caller that narrows to a plant checks it there.
- The tenant argument is optional only when the key grants exactly one garden. With several, omitting it fails.
- This skill itself was not run against a live instance; tool names and field names come from `spec/mcp/kamerplanter-mcp-server/en.md` and `recipes/plant-master-data-check.yaml`.

## Source

Governed by `spec/process/garden-decision-policy/en.md` §D, "The garden context"; list-response fields measured against the reference instance on 2026-08-15 (`recipes/plant-master-data-check.yaml`).
