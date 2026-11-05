---
name: garden-review
description: "Assembles a retrospective of one Kamerplanter garden — scope garden, up to the assessment date, or scope season, over a bounded span — from blocks other skills already collected: one history record per plant with fixed fields, cultivar performance side by side, lessons that are each an observation or a recommendation with evidence, confidence, uncertainty and missing data, and a next-cycle block whose crops, goals, constraints and harvest window strings the planning recipes take as parameters. Use when a recipe must say what a garden or a season recorded and what the next plan should keep or reconsider. Calls no tool, never states care as the cause of an outcome, never reads a diary key as yield, never scores or averages cultivars, and writes nothing."
---

# Review a garden or a season

Looks back over what was recorded and what the person says, and hands the result forward. It makes no tool call: the garden comes from `garden-context`, each plant from `plant-context-collect` (its care log and inspections included), the diary coverage from `diary-measurements-read`, and, where the caller supplies them, the growth stage from `growth-stage-assessment`, the harvest results as the caller copied them from earlier harvest readiness checks, nutrient or pest results from `nutrient-imbalance-assess` and `pest-pressure-assess`, and a plant health finding from `plant-health-assessment`. The weight of a claim is `decision-policy`. It runs no assessment of a plant's present state, and it writes nothing: the review is text, handed to a person and to the next planning run.

## Input

- **Scope**: `garden` or `season`. For `season`, the span as the caller gave it, and the plant listing with archived plants and its status (`complete`, `partial: <reason>`, `failed: <error verbatim>`).
- **The garden context block** from `garden-context`: crops, planting runs, due tasks, absent fields.
- **Per reviewed plant, at most five**: the plant context block, the diary read report with the dates of the entries it opened; optionally a growth-stage assessment with its hand-off block, nutrient or pest results, and a plant health finding.
- **Not reviewed**: each plant key that was named but not reviewed, with the reason.
- **Caller facts**, each optional, marked `caller`: yields as `plant_key:amount unit`; harvest results as `plant_key:<readiness result>[:YYYY-MM-DD]`, typically copied from the final lines of earlier harvest readiness checks; notes on a plant or on the season; the season's weather; the assessment date. `;` and `:` are the separators of these parameters: a free-text part that contains them is reported verbatim and not parsed further.

Without the garden context block, stop and say that `garden-context` must run first.

## Procedure

### 1. Check the span

Scope `season` needs a span: `YYYY`, read as `YYYY-01-01..YYYY-12-31`, or `YYYY-MM-DD..YYYY-MM-DD` with the start not after the end. Anything else stops the review: say what is wrong with the span, and return only the review header with that problem. Scope `garden` runs up to the assessment date from the caller, or, without one, up to the newest dated entry read, and says which; never read today's date.

### 2. Build one history record per plant

One record per reviewed plant, ordered by plant key as text. Each field is present with its source, level and retrieval time, or absent with its reason (`no source` or `not collected`). Fill none.

| Field | From |
|-------|------|
| plant, species, cultivar, location name, `planted_on` | the plant context block |
| recorded phase | the plant context block's `current_phase` |
| archived | the season listing: `archived` or `live`; in scope `garden`, `not collected` |
| care confirmations | the care log: per `reminder_type`, the count of confirmations and the latest `confirmed_at` (level 3) |
| snoozes | the care log entries whose `action` is `snoozed` (level 3) |
| inspections | the recorded inspections, each with its date and what it names (level 3); an empty list is no recorded pest, not a clean bill of health |
| diary coverage | listed, opened, with no `measurements`; the oldest and newest opened date; in scope `season`, `covers span` or `does not cover <start or end>` |
| growth stage | the hand-off block's result and direction, as returned, or absent |
| harvest result | the caller's harvest result for this plant, its readiness result and date as given, marked `caller`; otherwise absent (`no source: no harvest result supplied`) |
| plant health | the caller's plant health finding for this plant, its overall result and surviving candidates as given, marked `caller`; otherwise absent (`no source: no plant health finding supplied`) |
| yield | the caller's `plant_key:amount unit`, level 3, marked `caller`; never a diary `measurements` key |
| notes | the caller's notes for this plant, marked `caller` |

A diary read of at most eight entries may not reach back over a season: state the coverage, and never assume the unread entries.

### 3. Set cultivar performance side by side

Group the records by `species_key:cultivar_key` (`species_key:-` without a cultivar). Per group, list the fields side by side: plants, archived, yield per plant in its own unit, inspections, harvest results, snoozes. **No score, no rank, no average.** Two cultivars are compared only on the same field in the same unit; yields in different units stand side by side uncompared, and say so.

### 4. Draw the lessons

Each lesson has exactly one kind:

- an **observation**: what a record or the caller said, with its source and level;
- a **recommendation** for the next cycle (keep, change or drop a crop, a location, a practice): it carries the four blocks of `decision-policy` (evidence, confidence, uncertainty, missing data) and rests on at least one item at level 1 to 3 or a caller statement. General knowledge alone carries no recommendation.

Care and outcome are linked only as "consistent with" (rule 1 of `decision-policy`): "the snoozed feedings are consistent with the low yield the person reports" is a suspicion, never a cause. Pest, nutrient and plant health history come only from the inspections and the results the caller supplied. A plant health finding is an observation: it enters a lesson as one, citing its overall result, and never as a cause or a diagnosis. The season's weather, from the caller, is context at level 6 and never a cause either.

### 5. Hand the next cycle forward

Build the next-cycle block from the records and lessons only:

- **crops**: every `species_key[:cultivar_key]` reviewed, comma-separated with no spaces in plant-key order without duplicates, the format the planning recipes take. Mark each, with the items it rests on:
  - `reconsider` when a level 1 to 3 item (an inspection, a snooze pattern) or a caller statement records a problem with it; this takes precedence over `keep`;
  - `keep` only when the caller reports a success (a note, or a yield the caller marks as a success) and no problem is recorded;
  - `no evidence` otherwise. A yield figure alone is `no evidence`: an amount says nothing about whether it was good. With no plant reviewed, list the garden context's crops, each `no evidence (not reviewed)`.
- **goals**: free text, drawn only from the lessons and the caller's notes; absent with the reason when nothing supplies them.
- **constraints**: free text carrying only recorded or caller-stated site and environmental observations (a wet June, slugs, shade); never a lesson, which goes to `goals` or stays in `LESSONS`. Absent with the reason when nothing supplies it.
- **harvest_window**: in the caller's month words, drawn only from the harvest results' windows and the caller's statements; absent with the reason otherwise.
- **location history**: one line per reviewed plant with a location name, `location_name:season:species_key[:cultivar_key]`, where `season` is the span's year or the span itself, labelled "location, not bed": the record has no bed source.

The block is text. Nothing writes it anywhere.

### 6. Report

Return these blocks, in this order and under these names:

```
REVIEW HEADER
  garden:       <tenant> (given | discovered)
  scope:        garden (up to <date>, caller | newest entry) | season <span>
  listing:      complete | partial: <reason> | failed: <error verbatim> | not collected (scope garden)
  archived:     <every plant the listing marks archived, key and species, reviewed or not> | none | not collected (scope garden)
  reviewed:     <plant keys>; not reviewed: <plant key: reason, each> | none named (garden level only; the plants parameter supplies them)
  absent:       <the blocks or fields that were not supplied, each with its reason>
  not claimed:  byte-identical prose outside the review facts
HISTORY RECORD
  <plant key>
    <field>: <value>  source <tool | caller>, level <n | no level>, retrieved <timestamp> | absent (<reason>)
CULTIVAR PERFORMANCE
  <species_key:cultivar_key>: <fields side by side>; compared on: <field and unit> | not compared (<why>)
LESSONS
  LESSON <n>: observation | recommendation
    statement / evidence / confidence / uncertainty / missing data
NEXT CYCLE
  crops:            <species_key[:cultivar_key], ...>
    <crop>: keep | reconsider | no evidence — <items>
  goals:            <text> | absent (<reason>)
  constraints:      <text> | absent (<reason>)
  harvest_window:   <month words> | absent (<reason>)
  location history (location, not bed):
    <location_name:season:species_key[:cultivar_key]>
DOMAIN STATUS
  care log: read | absent (<reason>); inspections: read | absent (<reason>); diary: <coverage>
  growth stage: supplied | not supplied; harvest: supplied | not supplied; nutrient, pest: supplied | not supplied
  plant health: supplied | not supplied
```

The `<n>` of a lesson numbers lessons by plant key (garden-wide lessons last), then by the history-record field the lesson rests on, in the order of the table in step 2, then by kind (observation before recommendation), never by statement text. Return no field that was not read. The facts two runs over the same blocks must agree on are the records, the groups, the lessons and their kinds, the next-cycle strings and the missing-data list; retrieval times and prose may differ.

## Hard rules

- Never call a tool. Everything is in the blocks.
- Never state care, weather or anything else as the cause of an outcome; link only as "consistent with".
- Never read a diary `measurements` key as yield, and never fill a yield, a field or a coverage.
- Never score, rank or average cultivars, and never compare across units.
- Never return a recommendation without its evidence, confidence, uncertainty and missing data.
- Never run, upgrade or restate a plant health finding, and never substitute another domain for an absent one.
- Never read the current date into the facts, and never write the review anywhere.
- Call no tool that changes state. Forbidden by name: `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`, `mcp__kamerplanter__submit_diary_analysis`, `mcp__kamerplanter__transition_plant_phase`, `mcp__kamerplanter__assign_species_phase_sequence`, `mcp__kamerplanter__assign_nutrient_plan`, `mcp__kamerplanter__record_feeding_event`, `mcp__kamerplanter__create_inspection`, `mcp__kamerplanter__clone_nutrient_plan`, `mcp__kamerplanter__set_nutrient_plan_phase_targets`, `mcp__kamerplanter__create_substrate_mix`, `mcp__kamerplanter__set_plant_substrate`. Call no Home Assistant tool.

## Gotchas

- A review of a garden tended only through reminders is mostly care-log confirmations and `no evidence` crops. That is the honest result, not a failure.
- Writing the review as a diary entry would be the obvious way to keep it, and that write is exactly what this skill must not do; persisting a review is a follow-up with its own apply recipe.
- Location history uses location names because the record has no bed source. Where location names equal bed names, the lines read like bed history; they are not a contract with any crop rotation work.
- Whether an archived plant carries an archive date is not recorded, so a season review cannot tell when an archived plant left the garden; it says so instead of guessing.
- This skill itself was not run against a live instance; it has no tool calls to get wrong, and its input blocks inherit that status.

## Source

Governed by `spec/process/garden-and-season-review/en.md` §A to §H.
