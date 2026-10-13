---
name: site-analysis
description: "Builds the site profile for one Kamerplanter garden: seven parameters (light and exposure, area and container volume, soil and substrate, climate and season, water availability, environmental constraints, existing observations), each reported known or unknown with its value, source, retrieval time and evidence level. Use when crops are about to be judged against a site, before selecting or planning anything, or when asked what is and is not known about where something would grow. Light, area, volume and water have no source in the measured catalog and are known only when the caller supplies them; it never infers them from a site's name or type."
---

# Analyse a site

Turns what is known about a garden's site into a profile that says, parameter by parameter, what is known, what is unknown and where each value came from. It judges no crop: matching candidates to the profile is `crop-selection`. It recommends nothing, reads no photo and writes nothing.

The garden's own fields come from `garden-context`; the context of one plant is `plant-context-collect`. The weight a claim carries is `decision-policy`'s. Every tool below is on the `kamerplanter` MCP server and is addressed as `mcp__kamerplanter__<tool>`. All of them are read-only.

## Input

- **The garden context block** returned by `garden-context`, with the tenant already resolved. Without it, stop and say `garden-context` must run first; this skill does not re-collect the garden.
- **Site facts from the caller**, each optional: light and exposure, available area or container volume, water availability, environmental constraints, the garden's hardiness zone. They are taken verbatim and marked source `caller`.
- **A species name** to narrow the sowing calendar with (step 3), taken from the caller's candidates or from the garden's own plants.

## Procedure

### 1. Soil and substrate

Take the soil-and-substrate entry from the garden context. When it is present, copy its value and source; the substrate properties it carries come from `mcp__kamerplanter__list_substrates`. A bed or container's own substrate is not known: only a plant carries a `substrate_key`, so say the profile describes the substrates the garden's plants reference. When the entry is absent, the parameter is unknown, with that entry's reason.

### 2. Caller-supplied facts

Light and exposure, area or container volume, water availability and environmental constraints are known only when the caller supplied them. Copy the caller's words unchanged; do not translate "sunny" into hours of light or a bed into square metres. Otherwise the parameter is unknown, kind `no source`: the server spec names no field for it.

### 3. Climate and season

Call `mcp__kamerplanter__get_sowing_calendar` with `tenant` and a `query` naming the species from the input. Without a `query` the server refuses the call, so with no species to narrow it by, climate is unknown with that as the reason. Record the frost dates exactly as the response gives them and rename nothing. The response also carries per-species bars; read the frost dates only. That frost dates are the garden's and not the species' is the documented reading of this tool, not a measurement made here.

Call `mcp__kamerplanter__list_hardiness_zones` once. It lists zones; it does not say which one the garden is in. The garden's zone is the caller's value when given, and unknown otherwise. When the caller gave a zone that is not among the zones listed, report that mismatch and treat the zone as unknown (kind `error`: not a listed zone), showing the caller's text in the reason. A zone that cannot be validated is not used to reject a crop.

### 4. Existing observations and measurements

Mirror the two entries of the garden context for current measurements and historical observations, with their status and reason. They are collected per plant, so at garden level they are `not collected`. Do not restate them.

### 5. Report

Return one block with an entry for each of these seven parameters, in this order, each `known` or `unknown`: light and exposure; area and container volume; soil and substrate; climate and season; water availability; environmental constraints; existing observations and measurements.

```
SITE PROFILE: <tenant> (given | discovered)
<parameter>: known | unknown
  value:     <what was read or supplied>        (known)
  source:    <tool, or "caller">                (known)
  retrieved: <timestamp>                         (known)
  level:     <evidence level per decision-policy> (known)
  reason:    <kind>: <why>                       (unknown)
UNKNOWN: <parameter (kind), parameter (kind), ...>
```

Kinds of unknown: `no source` (the measured catalog offers none), `not supplied` (the caller could supply it and did not), `not collected` (a source exists but is read per plant), `error` (a call failed; quote the error). Caller-supplied and catalog site facts are site data, evidence level 5; the garden decision policy has no separate level for climate.

The unknown line is its own line at the end, separate from the data. An unknown parameter means the constraint it feeds is undetermined: a later step narrows its question rather than substituting a general assumption about gardens.

## Hard rules

- Never fill an unknown parameter with a typical value, a default or a guess.
- Never derive light, area, volume or water availability from a site's name, a location's name, or a site's type.
- Never report a hardiness zone as the garden's unless the caller supplied it.
- Never call `mcp__kamerplanter__get_sowing_calendar` without a `query`.
- Never judge a crop; hand the profile to `crop-selection`.
- Call no per-plant tool. Plant-level evidence is the caller's request.
- Pass `tenant` on every call; never rely on a default membership.
- Call no tool that changes state. Forbidden by name: `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`, `mcp__kamerplanter__submit_diary_analysis`, `mcp__kamerplanter__transition_plant_phase`, `mcp__kamerplanter__assign_species_phase_sequence`, `mcp__kamerplanter__assign_nutrient_plan`, `mcp__kamerplanter__record_feeding_event`, `mcp__kamerplanter__create_inspection`.
- Report a tool error verbatim, mark the affected parameter unknown with kind `error`, and continue. A partial profile with a named gap is useful; one that hides a failed call is not.

## Gotchas

- `mcp__kamerplanter__get_sowing_calendar` answered `validation.error` to an unnarrowed call, naming the species count and a `limit` ceiling of 25 (`spec/mcp/kamerplanter-mcp-server/en.md`). With a `query` it returned frost dates and per-species bars (`spec/process/species-baseline-verification/en.md`, measured 2026-08-07).
- The response fields of `mcp__kamerplanter__list_hardiness_zones` and the exact fields of the sowing calendar are not recorded in the specs. Report what comes back under its own names.
- This skill itself was not run against a live instance; tool names come from the specs named above.

## Source

Governed by `spec/process/site-analysis-and-crop-selection/en.md` §A, "The site profile".
