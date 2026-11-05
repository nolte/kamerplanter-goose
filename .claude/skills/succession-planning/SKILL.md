---
name: succession-planning
description: "Turns a plant-planning block of planting runs and a crop-rotation-planning block for one season into reviewable succession proposals: sequential successions where one run's harvest ends before another run in the same rotation slot starts, and staggered sowings inside a known direct sowing window at the caller's interval, each naming its run identifiers and copying the windows it rests on, every run without a succession listed with its reason, and an apply contract. Use after plant-planning and crop-rotation-planning, when a person must review successions, or when bed-layout-planning needs them. Uses no typical interval or date. Read-only and tool-free: the plan is a function of the blocks it is given."
---

# Plan the successions

Finds which planting runs can follow each other in one bed, and which can be sown in staggered sets. It makes no tool call: everything it needs is in the blocks it is handed, which is what lets two runs over the same blocks give the same proposals. It writes nothing. Windows are `planting-calendar`'s and `plant-planning`'s, the family per bed and season is `crop-rotation-planning`'s, the weight of a claim is `decision-policy`'s, and placing runs in beds is `bed-layout-planning`'s.

## Input

- **The plant-planning block**: `PLAN HEADER`, `PLANTING RUNS` (each `RUN <run_id>` with its method, windows, succession note and levels) and `NOT PLANNED`.
- **The crop-rotation-planning block** for the season: `ROTATION PLAN` (each `SLOT <bed>/<season>` with `selected`, `pinned` and `crops`) and `CONFLICTS`.
- **Caller inputs**, each taken as written and marked `caller`:
  - **season** (required): one year;
  - **stagger_weeks**: a whole number of weeks;
  - **constraints**: entries separated by semicolons; only the `pin=bed:season:species_key[:cultivar_key]` entries are read here.

Without the plant-planning block or the rotation block, stop and name the skill that must run first. Without a season, or when it is not one whole year, stop and say so. A `stagger_weeks` that is not a whole number above 0 is `not evaluated`, verbatim, and treated as not supplied.

## Procedure

### 1. Normalise the runs

- A run's **crop key** is the first two parts of its identifier, `species_key/cultivar_key`; this is the key the rotation plan uses.
- **Method not chosen**: when two runs share species, cultivar and period and differ only in method, both are `method not chosen — set planting_method`. They take part in nothing below.
- A run's **occupancy** is a range of months within the season. Its **start** is the lowest month of the sowing window for `direct_sow`, and the month of the transplant start for `indoor_then_transplant`. Its **end** is the highest month of the harvest window. Use the months exactly as the block gives them; never recompute a window.
  - A start or end that the block reports unknown makes the occupancy `unknown`, missing that window.
  - A harvest month lower than the start month, or a sowing or transplant month higher than the end month, means the run reaches across the season boundary: occupancy `unknown — spans the season boundary`. Examples: direct sowing in 4, 5 and 8 with harvest in 6 and 7; sowing in 11, 12, 1 and 2 with harvest in 5 and 6.

### 2. Admissibility

Read only the slots of the season. A crop is **admissible** in slot B/S by the first of these clauses, read in this order:

1. **Pin first**: a `pin=` constraint names B, S and that crop. It admits the crop whatever the slot's state, `occupied` included.
2. **Otherwise the selection**, only for a slot that is not pinned: `selected` is a family key and the crop is listed in the slot's `crops` with that `family_key` among its verdict's elements; or `selected` is `unknown/<crop key>` and the crop is that crop.

Apart from clause 1, a slot that is `open` or `occupied` admits nothing. Record, per admissible crop, its rotation verdict with rule and level as the slot gives it. A run whose crop no slot admits is `outside rotation plan`.

### 3. Sequential successions

For every slot, walk the pairs of runs (X, Y) whose crops are both admissible in it and that are not `method not chosen`, ordered by X's run identifier, then Y's, as text. X precedes Y when both occupancies are known and X's end month is lower than Y's start month. Each such pair is one `SEQUENTIAL` succession of that slot. Pairs of runs of one crop are included; for them, copy plant-planning's own `precedes` and `follows` notes verbatim beside the succession.

Each succession carries: the slot; both run identifiers; X's harvest window and Y's sowing or transplant window, each copied with its rule, fields, source and level; both rotation verdicts with their levels; the season; and the gap in months (Y's start minus X's end).

Never propose a succession from general knowledge, from a window the block reports unknown, or across a crop the slot does not admit.

### 4. Staggered successions

For every run with method `direct_sow`, a known sowing window, a known occupancy, and a crop admissible in at least one slot. Sowing dates lie only inside the run's occupancy months, never outside; a run whose occupancy is unknown, or spans the season boundary, gets no staggered entry and is reported only under `NOT SUCCEEDED` if it is in no sequential succession.

- With `stagger_weeks` n: split the window's months into contiguous blocks. For each block, the sowing dates are the first day of the block's first month in the season and every n weeks after it, while the date stays within the block's last month. List the dates as ISO dates, each with the window's rule, fields, source and level, and n with source `caller`. A block with one date only is listed with `one sowing — interval longer than the window`.
- Without `stagger_weeks`: one entry, `staggering possible within <months> — interval not supplied`.

A run with method `indoor_then_transplant` gets no staggered entry: its indoor sowing is one date. A staggered succession occupies its run's own area; it does not split the run's quantity.

### 5. Not succeeded

Every run that is in no sequential succession is listed under `NOT SUCCEEDED` with one reason, the first that applies:

1. `method not chosen — set planting_method`;
2. `outside rotation plan`;
3. `occupancy unknown — <missing window>`, when a window its occupancy needs is unknown;
4. `spans the season boundary`;
5. `no other run in <slot>` when its crop's slots admit no other run;
6. `no run follows or precedes it in <slot>`, naming each slot.

Every candidate in plant-planning's `NOT PLANNED` is carried over verbatim as context, not as a reason of this plan.

### 6. Levels

The elements of a succession are its windows (their levels as the block gives them), the rotation verdicts (their levels), the season (`caller`) and, for a staggered one, n (`caller`). The level of a succession is `caller` when any element is `caller`, otherwise the weakest level among them, the highest number. Apply `decision-policy` to each succession: confidence from the highest level that supports it, uncertainty, missing data.

### 7. Report

Return four blocks, in this order and under these names:

```
SUCCESSION HEADER
  garden:          <tenant> (given | discovered)
  made from:       <the blocks received: planting runs, rotation plan>
  season:          <year>                       (source caller)
  stagger_weeks:   <n | not supplied>           (source caller)
  not evaluated:   <entries verbatim | none>
SUCCESSIONS
  SEQUENTIAL <bed>/<season> <run X> -> <run Y>
    windows:     <X harvest_window ...; Y sowing or transplant window ...>   (rule, fields, source, level)
    gap:         <months>
    rotation:    <X crop>: <verdict> rule <n> level <l>; <Y crop>: <verdict> rule <n> level <l>
    plan notes:  <plant-planning precedes/follows notes verbatim | none>
    level:       <caller | n>
    confidence / uncertainty / missing_data
  STAGGERED <run id>
    dates:       <ISO dates, ...> | staggering possible within <months> — interval not supplied
    window:      <sowing_window> (rule, fields, source, level); stagger_weeks <n> (caller)
    level:       <caller | n>
NOT SUCCEEDED
  <run id>: <reason>
  not planned (carried over): <entries verbatim | none>
APPLY CONTRACT
  per succession: <what a later apply step would record: the slot, the runs in order, the sowing dates>
  The measured catalog has no tool that records a succession, a bed assignment, a layout or a planting run. The write and setup tools it records are the twelve listed under Gotchas; none does.
  The apply recipe is tracked in the blocked follow-up split out of nolte/kamerplanter-goose#46.
```

Return no field that was not read; list an unread field as absent with its reason. The plan facts that two runs over the same blocks must agree on are the successions (slot and both run identifiers, or run and dates), the not-succeeded reasons and the levels; prose may differ, and this property is checked on a fixed fixture, not on a live garden.

## Hard rules

- Never call a tool. Everything is in the blocks.
- Never use a typical interval, a typical date or a typical duration; every month comes from the planting runs and every interval from the caller.
- Never propose a succession across a crop the rotation slot does not admit, and never re-derive a rotation.
- Never compare months the block reports unknown, and never read a run across the season boundary.
- Never let input order or the current date decide a plan fact.
- Never write an apply recipe's effect as done: the plan changes nothing, and says what recording it would take.

## Gotchas

- The apply contract names no tool, because the measured catalog has none that records a succession. The write tools it records are `add_plant_diary_entry`, `confirm_care_task`, `archive_plant`, `set_plant_location`, `claim_diary_analysis`, `submit_diary_analysis`, `transition_plant_phase`, `assign_species_phase_sequence`, `assign_nutrient_plan`, `record_feeding_event` and `create_inspection`, and the setup tool `create_site` (`spec/mcp/kamerplanter-mcp-server/en.md`). Reproduce this list in the report as the twelve tools the catalog records; it is explanation, never a call.
- Every succession is level `caller`, because the season is the caller's. That is honest, not a defect.
- A rotation plan with `open` slots admits nothing there, so a plan with few families selected has few successions. Supplying `rotation_years` to the rotation step is what opens slots.
- Two runs of one crop in one slot are the common case of a succession; plant-planning already names them, and this skill only adds the slot.
- This skill itself was not run against a live instance; it has no tool calls to get wrong, and its input blocks inherit that status.

## Source

Governed by `spec/process/bed-layout-and-succession-planning/en.md` §C, §E, §F and §G.
