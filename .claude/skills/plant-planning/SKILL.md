---
name: plant-planning
description: "Turns crop candidates and their planting calendar into a reviewable plan of planting runs: a stable identifier, method, windows, rationale and confidence for each run, a list of what was not planned and why, and an apply contract stating what a later apply step would have to create. Use when a person must review a planting plan before anything is applied, or when care planning or bed layout need runs to read. Plans only eligible candidates with a known sowing window, assigns no bed, reports rotation as unknown, and invents no succession. Read-only and tool-free: the plan is a function of the blocks it is given."
---

# Plan the plantings

Turns a calendar into planting-run proposals a person can review. It makes no tool call: everything it needs is in the blocks it is handed, which is what lets two runs over the same blocks give the same plan. It writes nothing. Judging crops is `crop-selection`, computing windows is `planting-calendar`, the weight of a claim is `decision-policy`.

## Input

- **The calendar block** from `planting-calendar` (the windows, with rules, fields, sources and levels).
- **The candidate records** from `crop-selection` (verdict, failed hard constraints, confidence). When the candidates come without verdicts, every candidate is `undetermined` here and none is planned.
- **The garden context block** from `garden-context`, for the garden's existing planting runs.
- **Caller inputs**, each optional, taken as written and marked `caller`:
  - **beds and containers**: entries separated by commas, each `name:area_or_volume`; split at the commas and at the first colon of each entry, never pass the joined text on;
  - **the target harvest window**, in the caller's words;
  - **a method preference**: `direct_sow` or `indoor_then_transplant`; any other text is not a preference, say so.

Without the calendar block or the candidate records, stop and say which skill must run first.

## Procedure

### 1. Sort the candidates

For each candidate, in this order:

1. verdict `rejected`: not planned, reason `rejected` and the failed hard constraint with its source and level;
2. verdict `undetermined`, or none given: not planned, reason `undetermined` and the input that is missing;
3. verdict `eligible` with no method that has a known sowing window, that is neither a known direct sowing window nor a known indoor sowing date in any growing period: not planned, reason `window unknown` and the missing input the calendar named;
4. otherwise: planned (step 2).

### 2. Make the runs

For a planned candidate, make one run for each growing period and each method that has a known sowing window. The methods are `direct_sow` (sowing window known) and `indoor_then_transplant` (indoor sowing known). If the caller stated a method preference, make runs of that method only; without one, make a run for each method that qualifies, and say that both are offered for review.

A run's **identifier** is the species key, the cultivar key or `none`, the method and the period, joined by `/`, with the period copied unchanged from the calendar block's `PERIOD` line. Never build it from the order of the input, a counter or the time.

Each run carries, copied from the calendar block and not recomputed: the method, the sowing window, the indoor sowing date, the transplant window, the harvest window, and for each one its rule, fields, source, retrieval time and level. Add per run:

- **location**: `unassigned`. Assigning plants to beds is bed layout's work; the beds the caller supplied are listed in the plan header and not used here.
- **succession note**: a succession is named only where the calendar's own dates make two windows of one candidate follow each other: the last harvest month of one period before the first sowing month of another period. Name it on **both** runs of the pair: the earlier run says `precedes <run id>`, the later run says `follows <run id>`. A run in no such pair says `none`. Months that cannot be compared are no succession. Never name one that the dates do not show.
- **rotation note**: `unknown`. `compatible_companions` is not a rotation constraint, and rotation is not built yet.
- **rationale, confidence, uncertainty, missing data**: apply `decision-policy` to each date. The confidence comes from the highest evidence level that supports it, and a date resting on a caller-supplied fact says so.

### 3. Order

Order the runs by species key, cultivar key, method, then period, as text. The order of the input has no effect.

### 4. Report

Return four blocks, in this order and under these names:

```
PLAN HEADER
  garden:        <tenant> (given | discovered)
  made from:     <the blocks received: calendar, candidates, garden context>
  beds supplied: <name:area_or_volume, ... | none>   (source caller)
  existing runs: <from the garden context, as context | not read>
PLANTING RUNS
  RUN <run_id>
    method / sowing_window / indoor_sowing / transplant_window / harvest_window   (each with rule, fields, source, retrieved, level, or unknown and why)
    location:     unassigned
    succession:   precedes <run id> | follows <run id> | none
    rotation:     unknown
    harvest_preference: met | unmet | unknown
    confidence / uncertainty / missing_data
NOT PLANNED
  <species_key / cultivar_key>: <rejected | undetermined | window unknown> — <failed constraint or missing input>
APPLY CONTRACT
  per run: <what a later apply step would create: a planting run with species, cultivar, method, windows, location>
  The measured catalog has no tool that creates a planting run, a sowing or planting task, or a plan. The write tools it records are add_plant_diary_entry, confirm_care_task, archive_plant, set_plant_location, claim_diary_analysis, submit_diary_analysis, transition_plant_phase, assign_species_phase_sequence, assign_nutrient_plan, record_feeding_event and create_inspection, and the setup tool create_site; none does.
  The apply recipes are tracked in nolte/kamerplanter-goose#59.
```

Return no field that was not read; list an unread field as absent with its reason. Facts that two runs over the same blocks must agree on are the run identifiers, methods, windows, locations, the not-planned reasons and the confidence levels; retrieval times and prose may differ.

## Hard rules

- Never call a tool. Everything is in the blocks.
- Never plan a candidate that is not `eligible` with a known sowing window or indoor sowing date.
- Never assign a run to a bed.
- Never name a succession the calendar's dates do not show, and never read `compatible_companions` as a rotation constraint.
- Never use a typical date, duration or offset; every date is copied from the calendar block.
- Never read the current date into the plan facts.
- Never write an apply recipe's effect as done: the plan changes nothing, and says what applying would take.

## Gotchas

- A calendar block full of unknown windows gives a plan with no runs and a long `NOT PLANNED`; that is the honest result when the garden's inputs were not supplied, not a failure.
- With no method preference, one crop can appear twice (once per method). They are alternatives for the reviewer, not two plantings.
- This skill itself was not run against a live instance; it has no tool calls to get wrong, and its input blocks inherit that status.

## Source

Governed by `spec/process/plant-planning-and-planting-calendar/en.md` §C, §E and §F.
