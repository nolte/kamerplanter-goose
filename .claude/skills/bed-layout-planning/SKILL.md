---
name: bed-layout-planning
description: "Turns the planting runs, the rotation plan and the successions of one season, the catalog's companion lists, and the caller's beds, capacities, spacing, quantities, bed attributes and constraints into a reviewable bed layout: which run stands in which bed, the area or volume it needs, the capacity per bed and month (within, over by, or not validated with the missing input), every conflict, every run not placed with its reason, and an apply contract. Use after plant-planning, crop-rotation-planning, succession-planning and companion-spacing-collect, when a person must review a layout before anything is recorded. Places a crop only where the rotation plan admits it; companions rank and never guarantee; uses no spacing from general knowledge. Read-only and tool-free: the layout is a function of the blocks it is given."
---

# Lay out the beds

Allocates planting runs to beds for one season and checks that they fit, month by month. It makes no tool call: everything it needs is in the blocks it is handed, which is what lets two runs over the same blocks give the same layout. It writes nothing. Windows are `plant-planning`'s, families per bed are `crop-rotation-planning`'s, successions are `succession-planning`'s, companion lists are `companion-spacing-collect`'s, and the weight of a claim is `decision-policy`'s. It allocates area or volume per bed, never positions inside a bed.

## Input

- **The plant-planning block**: `PLANTING RUNS` and `NOT PLANNED`.
- **The crop-rotation-planning block** for the season: `ROTATION PLAN` and `CONFLICTS`.
- **The succession block** from `succession-planning`: `SUCCESSIONS`.
- **The companion block** from `companion-spacing-collect`.
- **Caller inputs**, each taken as written and marked `caller`:
  - **season** (required): one year;
  - **beds**: entries separated by commas, each `name`, `name:<n>m2` (`m²` reads as `m2`) for a bed by area, or `name:<n>l` for a container by volume; the name is the text before the first colon;
  - **bed_attributes**: entries separated by semicolons, each `bed:light=<text>`, `bed:access=<text>` or `bed:irrigation=<text>`;
  - **spacing**: entries separated by commas, each `species_key[:cultivar_key]=<n>/m2` (plants per m²) or `species_key[:cultivar_key]=<n>l` (litres per plant);
  - **quantities**: entries separated by commas, each `species_key[:cultivar_key]=<plants>`;
  - **constraints**: entries separated by semicolons: `pin=bed:season:species_key[:cultivar_key]`, `exclude=bed:species_key[:cultivar_key]`, `avoid=species_key[:cultivar_key]+species_key[:cultivar_key]`, or free text.

Without the plant-planning, rotation or succession block, stop and name the skill that must run first. Without a season, stop and say so. The companion block may be missing; then every companion pair is `unknown` and the header says the block was not received.

## Procedure

### 1. Normalise the inputs

- A run's **crop key** is the first two parts of its identifier, `species_key/cultivar_key`.
- A **crop entry** `species_key[:cultivar_key]` in spacing, quantities, `exclude` or `avoid` matches a crop when the species is equal and, if the entry names a cultivar, the cultivar is equal too. For spacing and quantities, a matching cultivar entry is used before a matching species entry; record which.
- A bed's **capacity** is `<n> m2` or `<n> l` from its entry. Any other text after the colon is kept verbatim with capacity `unknown`; a bare name is a bed of capacity `unknown`. The layout's beds are the `beds` entries plus every other bed the rotation plan has a slot for in the season, the latter with capacity `unknown`; they are processed by name as text.
- Bed attributes are kept per bed as written. An attribute key other than `light`, `access` or `irrigation`, or an attribute for a bed that is not in `beds`, goes to `not evaluated`.
- Every entry that does not parse, and every free-text constraint, goes verbatim to `not evaluated` in the header.
- **Method not chosen**: when two runs share species, cultivar and period and differ only in method, neither is placed; both get `method not chosen — set planting_method`. Runs of different periods are separate plantings.

### 2. Occupancy and need

A run's **occupancy** is a range of months within the season: from the lowest month of its sowing window (`direct_sow`) or the month of its transplant start (`indoor_then_transplant`) to the highest month of its harvest window, the months exactly as the block gives them. An unknown bound makes it `unknown`, missing that window; a harvest month lower than the start month makes it `unknown — spans the season boundary`. Two occupancies **overlap** when they share a month; an unknown occupancy overlaps every month.

A run's **need** in a bed:

- bed in `m2` and spacing `<d>/m2` and quantity q: q ÷ d m²;
- container in `l` and spacing `<v>l` and quantity q: q × v l;
- otherwise `unknown`, missing the spacing, the quantity, or `spacing unit does not match bed`.

Report a need to two decimals and compare it unrounded. The catalog's seed density is never a spacing; show it beside the need as context only.

### 3. Admissibility

Read only the slots of the season. A crop is **admitted** in bed B when the slot B/S is pinned and a `pin=` names B, S and the crop; or the slot is not pinned, `selected` is a family key and the crop is listed in its `crops` with that `family_key` among its verdict's elements; or `selected` is `unknown/<crop key>` and the crop is that crop. An `open` or `occupied` slot admits nothing. Copy the crop's rotation verdict in that slot with its rule and level.

A run is **admissible** in B, given the runs already placed there, when its crop is admitted in B, no `exclude` names B and its crop, no `avoid` pair joins its crop to the crop of a run in B whose occupancy overlaps its own, and its method is chosen.

### 4. Capacity check

For a run R and a bed B, look at every month of R's occupancy (every month of the season when it is unknown) together with the runs already in B that occupy it:

- **fits**: B's capacity, R's need, every such run's need and every occupancy involved are known, and in every month the sum of the needs plus R's need is at most the capacity;
- **exceeds**: all of that is known, and in some month the sum is above the capacity; record the largest excess and its month;
- **not validated**: anything involved is unknown; record what.

### 5. Companion sum

For R in B, look at each run O already in B whose occupancy is known and overlaps R's known occupancy. The pair's score is the entry in R's companion list that names O's species, else the entry in O's list that names R's species; record which. A numeric score is added. A non-numeric one adds 0 and is listed as `score not comparable`. A pair neither list names is `unknown` and adds 0; it is never incompatible. A run whose occupancy, or whose candidate neighbour's occupancy, is unknown is listed as `overlap unknown` and not counted. The ranking reads a higher sum as better; the direction of `score` is not recorded, so the rationale says so.

### 6. Place

1. **Pinned runs first.** Every run whose crop a `pin=` names for this season goes to the pinned bed (the first by name when the crop is pinned in several beds), in the order of step 7, whatever its capacity check, its `avoid` or its `exclude`. A pin is never moved. List under `CONFLICTS` every month it makes a validated bed exceed its capacity, every `avoid` it breaks and every `exclude` it contradicts.
2. **Then every other run** that is not `method not chosen` and whose crop is admitted somewhere, in the order of step 7. Its **candidate beds** are the beds where it is admissible and whose capacity check is `fits` or `not validated`. Rank them by these keys, strictly in order, each later key breaking only a tie on every earlier one:
   1. the bed holds a run that the succession block lists as this run's sequential predecessor in that bed's slot (yes before no);
   2. capacity check `fits` before `not validated`;
   3. the higher companion sum;
   4. the bed name as text.
   Place the run in the first. A run with no candidate bed is not placed (step 8).

A placed run becomes an occupant for every later run. Neither the order of the input nor the current date plays a part.

### 7. Order of the runs

Within each of the two passes, take the runs by occupancy start month, unknown last, then by run identifier as text.

### 8. Not placed

Every run that is not placed is listed under `NOT PLACED` with one reason:

- `method not chosen — set planting_method`;
- `outside rotation plan` when no slot of the season admits its crop;
- `not placed — capacity` when every bed admitting its crop was stopped by the capacity check alone, naming per bed the excess and its month;
- `not placed — no admissible bed` otherwise, naming per bed the check that stopped it (`excluded`, `avoid with <run id>`, `over by <x> in <month>`).

A crop the rotation plan admits in a slot of the season but that has no planting run is listed too, as `<crop key>: no planting run — <its NOT PLANNED reason verbatim | not in the plan>`.

### 9. Capacity per bed and month

For each bed, list every month of the season in which a placed run occupies it, and every month when a placed run's occupancy is unknown: `within (<sum> of <capacity>)`, `over by <x>` (a conflict, only ever caused by a pin), or `not validated — <missing input>`. A bed without placements is `empty`.

### 10. Levels and rationale

The elements of a placement are the run's windows (their levels), the rotation verdict (its level), the season, the bed's capacity, the spacing and the quantity when used (`caller`), and the companion scores used (level 4). The level is `caller` when any element is `caller`, otherwise the weakest level, the highest number. Apply `decision-policy` to each placement.

Every placement's rationale states: the ranking values in the chosen bed; every other bed that admits its crop, with its ranking values or the check that stopped it; the beds the rotation did not admit it to, as one list; the rotation verdict copied with its rule and level; the bed's attributes as context (`no rule formed: no species field records the need`); and the sentence **A companion pairing is a planning input from the catalog, not a guarantee of any outcome.**

### 11. Report

Return six blocks, in this order and under these names:

```
LAYOUT HEADER
  garden:          <tenant> (given | discovered)
  made from:       <the blocks received: planting runs, rotation plan, successions, companions | companions not received>
  season:          <year>                                        (source caller)
  beds:            <name: <n> m2 | <n> l | unknown (<text verbatim>)>, ...   (source caller)
  spacing:         <entries | not supplied>                      (source caller)
  quantities:      <entries | not supplied>                      (source caller)
  constraints:     <avoid and exclude entries | none>            (source caller)
  not modeled:     geometry; light, access and irrigation as rules
  not evaluated:   <entries verbatim | none>
BED LAYOUT
  BED <name>   capacity <n> m2 | <n> l | unknown
    attributes:  light <text | not supplied>; access <text | not supplied>; irrigation <text | not supplied>   (caller, context only)
    PLACEMENT <run id>
      pinned:     yes | no
      occupancy:  <months | unknown — reason>
      need:       <x> m2 | <x> l | unknown — <missing>   (spacing <entry>, quantity <entry>, cultivar | species; seed density <value> context only)
      rotation:   <verdict> rule <n> level <l>
      successor of: <run id | none>
      companions: <neighbour run: score <s> (numeric | not comparable | unknown), ...>; sum <n>
      rationale:  <ranking values; other beds and why; beds not admitted; attributes; the companion sentence>
      level:      <caller | n>
      confidence / uncertainty / missing_data
CAPACITY
  <bed> <month>: within (<sum> of <capacity>) | over by <x> | not validated — <missing input>
  <bed>: empty
CONFLICTS
  <bed> <month> <run id>: over by <x> — pinned
  <bed> <run id>: avoid with <run id> | excluded — pinned
  rotation: <the rotation plan's conflicts for the season, verbatim | none>
NOT PLACED
  <run id>: <reason>
  <crop key>: no planting run — <reason>
APPLY CONTRACT
  per placement: <what a later apply step would record: the bed and its capacity, the run, its need, the season, its successor>
  The measured catalog has no tool that creates a bed, records a bed assignment or a layout, or creates a planting run. The write and setup tools it records are the twelve listed under Gotchas; none does. The one that moves a plant moves a plant that exists, while a layout places crops that are not plants yet, and the setup tool creates a site root, not a bed with an area.
  The apply recipe, bed-layout-plan-apply, is tracked in the blocked follow-up split out of nolte/kamerplanter-goose#46.
```

Return no field that was not read; list an unread field as absent with its reason. The plan facts that two runs over the same blocks must agree on are the placements, the needs, the capacity per bed and month, the conflicts, the not-placed reasons, the successions placed and the levels; prose may differ, and this property is checked on a fixed fixture, not on a live garden.

## Hard rules

- Never call a tool. Everything is in the blocks.
- Never place a run where the rotation plan does not admit its crop, and never re-derive a rotation.
- Never move a pin, and never hide what a pin breaks.
- Never put two crops of an `avoid` pair in one bed in overlapping months, unless a pin does it, and then list it.
- Never read an unlisted companion pair as incompatible, and never call a companion pairing a guarantee.
- Never supply a spacing, a quantity, a capacity or a density; absent is `not validated` with the missing input.
- Never let a bed attribute decide a placement.
- Never place positions, rows or coordinates.
- Never let input order or the current date decide a plan fact.
- Never write an apply recipe's effect as done: the layout changes nothing, and says what recording it would take.

## Gotchas

- The apply contract names no tool, because the measured catalog has none that records a layout. The write tools it records are `add_plant_diary_entry`, `confirm_care_task`, `archive_plant`, `set_plant_location`, `claim_diary_analysis`, `submit_diary_analysis`, `transition_plant_phase`, `assign_species_phase_sequence`, `assign_nutrient_plan`, `record_feeding_event` and `create_inspection`, and the setup tool `create_site` (`spec/mcp/kamerplanter-mcp-server/en.md`). `set_plant_location` moves a plant that exists; `create_site` creates a site root. Reproduce this list in the report as the twelve tools the catalog records; it is explanation, never a call.
- Without spacing and quantities every capacity is `not validated`. That is the honest result, not a failure; the runs are still placed by rotation, successions and companions.
- An `over by` can only come from a pin, because an unpinned run never goes to a bed it would overfill.
- A run that spans the season boundary has unknown occupancy, so its bed's capacity is `not validated` in every month, and it blocks every `avoid` partner from that bed.
- This skill itself was not run against a live instance; it has no tool calls to get wrong, and its input blocks inherit that status.

## Source

Governed by `spec/process/bed-layout-and-succession-planning/en.md` §A and §C to §G.
