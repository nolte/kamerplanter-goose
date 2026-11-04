---
name: crop-rotation-planning
description: "Turns a garden's rotation history, the caller's beds, bed history, rotation interval, demand order and constraints, and a list of candidate crops into a multi-season rotation plan: one family group per bed and season, a verdict for every crop considered (clear, conflict, repeat — interval unknown, caution, unknown) with its rule and evidence, every conflict named, every unplaced crop listed with its reason, and an apply contract. Use after rotation-history-collect, when a person must review a rotation before anything is recorded, or when bed layout needs the families per bed and season. Uses no built-in interval, family or demand convention. Read-only and tool-free: the plan is a function of the blocks it is given."
---

# Plan the crop rotation

Turns a rotation history into a rotation plan a person can review. It makes no tool call: everything it needs is in the blocks it is handed, which is what lets two runs over the same blocks give the same plan. It writes nothing. Reading the history is `rotation-history-collect`, the weight of a claim is `decision-policy`, planting dates are `planting-calendar` and `plant-planning`, placing crops inside a bed is bed layout's work (nolte/kamerplanter-goose#46).

## Input

- **The rotation history block** from `rotation-history-collect`: per crop `family_key`, `nutrient_demand_level`, `green_manure_suitable`; the catalog read status; the mapped and unmapped history; the inspections.
- **The garden context block** from `garden-context`, for the garden's planting runs, context only.
- **Caller inputs**, each taken as written and marked `caller`:
  - **crops** (required): entries `species_key` or `species_key:cultivar_key`, separated by commas;
  - **seasons** (required): consecutive years, separated by commas;
  - **beds**: entries `name` or `name:area_or_volume`, separated by commas; the name is the text before the first colon;
  - **bed history**: entries `bed:season:species_key[:cultivar_key]` or `bed:season:none`, separated by commas;
  - **rotation_years**: a whole number N, the smallest distance in seasons at which a family may stand in a bed again;
  - **demand_sequence**: values separated by commas, compared as text with `nutrient_demand_level`; the value `green_manure` also matches a crop whose `green_manure_suitable` is `true`;
  - **constraints**: entries separated by semicolons, each `pin=bed:season:species_key[:cultivar_key]`, `exclude=bed:species_key[:cultivar_key]`, or free text.

Without the rotation history block, stop and say that `rotation-history-collect` must run first. Without crops or seasons, stop and name the missing one. When the seasons, sorted, are not consecutive whole years, stop and name the gap; never fill it.

## Procedure

### 1. Normalise the inputs

- Key every crop as `species_key/cultivar_key`, with `none` for no cultivar. This is the prefix of a `plant-planning` run identifier.
- A crop named in a pin and not in `crops` becomes a candidate too.
- The plan's beds are the union of the `beds` names, the beds in the bed history and the beds in a pin, ordered by name as text. When the union is empty, there is nothing to place: report every crop under `NOT PLACED` with the reason `no bed supplied`.
- A crop's **family** is its `family_key` from the history block. When it is absent, the family is `unknown`. Never take one from anywhere else.
- A crop's **demand class** is its `nutrient_demand_level`, the cultivar's before the species'; absent means `unknown`.
- Every entry that does not parse, every free-text constraint, every history entry after the last planned season and every pin outside the planned seasons goes, verbatim, to `not evaluated` in the header.

### 2. Bed history

Per bed, the history is the caller's entries for it plus the mapped catalog plants at it (season = the year of `planted_on`, or `unknown`). Keep both when they name the same bed and season; list a disagreement between them in `BED HISTORY` and use both.

A bed's history is **established** when the caller gave at least one entry for it, `none` included, or when the catalog read was `complete` and mapped at least one plant to it. An established history is taken as complete: a season it does not name held no crop. Say in `BED HISTORY` that this is an assumption resting on the caller. Any other bed's history is **not established**; a partial or failed catalog read never makes a bed's history "none".

A history entry in a planned season **occupies** that bed and season: nothing is selected there, the slot is reported `occupied`, and the entry counts as history for later seasons. A history entry with season `unknown` is listed and cannot fall inside any window; it makes the bed's verdicts `unknown` (history) wherever its family is the candidate's family or unknown.

A bed **has a caution** when the history block lists at least one recorded inspection for a plant mapped to it.

### 3. The verdict of one crop for one bed and season

For a crop c of family f, in bed B, in planned season S. The **window** is the seasons S−1 down to S−(N−1) when N is supplied (empty when N is 1), and every season before S when it is not. The **entries** are the history entries of B in the window and the plan's own placements in B in earlier planned seasons that fall in the window. Take the first that applies:

1. f is `unknown` → `unknown`, missing `family_key of <c>`.
2. N supplied, and an entry in the window has family f → `conflict`, naming that entry.
3. N not supplied, and any earlier entry has family f → `repeat — interval unknown`, naming that entry. Never `conflict`, never `clear`.
4. An entry in the window has family `unknown`, or B has a history entry with season `unknown` → `unknown`, missing the family or the season of that entry.
5. B's history is not established, and the window reaches a season before the first planned season (always, without N; with N, when S−(N−1) is before it) → `unknown`, missing `bed history for <B>`.
6. B has a caution → `caution`, level 3, missing `host range: not recorded`. A recorded pressure never makes a conflict.
7. Otherwise → `clear`.

A caution on B is listed beside every verdict in B, whichever verdict it is. Each verdict carries its rule (the number above), the fields on both sides (the candidate's `family_key` and the entry's), their sources (`get_species_info`, `list_plants`, `caller`, or the plan's own placement), their levels, and the missing data. A verdict resting on a caller-supplied history entry or on N says so: those have source `caller` and no level of their own. The **level of a verdict** is `caller` when any item it rests on is caller-supplied (a caller history entry, N, or a pin); otherwise it is the weakest level among its items (the highest number). A `conflict` always rests on N and is therefore `caller`.

### 4. Demand preference

With a demand sequence and exactly one known demand class among the crops in B in season S−1 (history or plan): the preferred class is the next value after it in the sequence, wrapping from the last to the first. A crop is `met` when its demand class equals the preferred class, or when the preferred class is `green_manure` and its `green_manure_suitable` is `true`; `unmet` when its class is known and differs; `unknown` otherwise. With no crop or several classes in S−1, or a class not in the sequence, every crop is `unknown`. Without a demand sequence, every crop is `not evaluated`. A group's preference is the best of its crops (`met`, then `unknown` or `not evaluated`, then `unmet`). Preference never makes a conflict.

### 5. Place

Walk the planned seasons in order and, within a season, the beds by name as text.

1. **Pins first.** Place every pinned crop in its bed and season, whatever its verdict. A pin is never moved. List it under `CONFLICTS` when its verdict is `conflict` or `repeat — interval unknown`, when the slot is `occupied`, when an exclusion names the same bed and crop, or when two pins put two families in one bed and season. A pinned slot takes no further group.
2. **Then every other slot that is not occupied.** Build the family groups: the candidate crops that share a `family_key`, with each crop of unknown family as a group of its own keyed `unknown/<crop key>`. Drop from each group the crops excluded from B. A group's verdict is its crops' verdict; crops of one known family share it.
3. **Qualifying groups** have the verdict `clear`, `caution` or `unknown`. `conflict` and `repeat — interval unknown` are never selected unless pinned.
4. **Rank** the qualifying groups by, in order: verdict (`clear`, `caution`, `unknown`); the number of beds that already hold the group in this season, fewer first; demand preference (`met`, then `unknown` or `not evaluated`, then `unmet`); known families before unknown ones; the group key as text. Select the first. When none qualifies, the slot is `open`.

The selection becomes part of the history of later seasons in that bed. The order of the input and the current date play no part.

`CONFLICTS` lists only what the plan places and what a pin contradicts: every pinned crop whose verdict is `conflict` or `repeat — interval unknown`, and every pin contradiction above. A candidate that was considered for a slot and not placed there is not a conflict of the plan; its verdict stays in that slot's crop list and under `NOT PLACED`.

### 6. Not placed

A candidate crop that no slot selected or pinned is listed under `NOT PLACED`, with one reason per bed and season: its verdict, `excluded`, `occupied`, or `outranked by <group key>`.

### 7. Report

Return six blocks, in this order and under these names:

```
ROTATION HEADER
  garden:          <tenant> (given | discovered)
  made from:       <the blocks received: rotation history, garden context>
  seasons:         <years>                                  (source caller)
  beds:            <names, with area_or_volume where given | none>   (source caller and pins)
  rotation_years:  <N | not supplied>                       (source caller)
  demand_sequence: <values | not supplied>                  (source caller)
  planting runs:   <from the garden context, context only | not read>
  not modeled:     soil effects other than green_manure_suitable
  not evaluated:   <entries verbatim | none>
BED HISTORY
  <bed>: established | not established — <why>
    <season>: <species_key/cultivar_key|none> family <family_key|unknown> (source caller | list_plants level 5)
    caution: <inspection records, level 3, host range: not recorded | none>
  assumption: an established history is taken as complete; it rests on the caller
  unmapped location history: <as received, context only>
ROTATION PLAN
  SLOT <bed>/<season>
    selected:    <family_key | unknown/<crop key>> | open | occupied
    pinned:      yes | no
    crops:       <species_key/cultivar_key>: <verdict> — rule <n>; <fields, sources, levels>; missing <...>
    demand:      met | unmet | unknown | not evaluated
    rationale:   <the ranking values; every group not chosen with its verdict>
    confidence / uncertainty / missing_data   (per decision-policy)
CONFLICTS
  <bed>/<season> <species_key/cultivar_key>: <verdict or contradiction> — rule <n>; this side <field, source, level>; other side <entry, field, source, level>; pinned yes|no
NOT PLACED
  <species_key/cultivar_key>: <bed>/<season> <reason>, ...
APPLY CONTRACT
  per placement: <what a later apply step would record: the bed, the season, the family group and its crops>
  The measured catalog has no tool that records a bed assignment, a rotation, a planting run or a plan. The write and setup tools it records are the twelve listed under Gotchas; none does, and the one that moves a plant moves a plant that exists, while a rotation plans crops that are not plants yet.
  The apply recipe is tracked in the blocked follow-up split out of nolte/kamerplanter-goose#47.
```

Return no field that was not read; list an unread field as absent with its reason. The plan facts that two runs over the same blocks must agree on are the placements, the verdicts with their rule numbers, the conflicts, the not-placed reasons and the evidence levels; retrieval times and prose may differ, and this property is checked on a fixed fixture, not on a live garden.

## Hard rules

- Never call a tool. Everything is in the blocks.
- Never supply a family, an interval, a demand order or a soil effect; absent is `unknown` or `not supplied`.
- Never report `clear` for a crop of unknown family, for a window the history does not cover, or for a same-family repeat.
- Never report a same-family repeat as `conflict` without a supplied interval.
- Never let a recorded pressure or a demand preference produce a conflict.
- Never move a pin, and never hide what a pin breaks.
- Never read `compatible_companions` as a rotation relation.
- Never place runs, area or spacing.
- Never let input order or the current date decide a plan fact.
- Never write an apply recipe's effect as done: the plan changes nothing, and says what recording it would take.

## Gotchas

- The apply contract names no tool, because the measured catalog has none that records a rotation. The write tools it records are `add_plant_diary_entry`, `confirm_care_task`, `archive_plant`, `set_plant_location`, `claim_diary_analysis`, `submit_diary_analysis`, `transition_plant_phase`, `assign_species_phase_sequence`, `assign_nutrient_plan`, `record_feeding_event` and `create_inspection`, and the setup tool `create_site` (`spec/mcp/kamerplanter-mcp-server/en.md`). `set_plant_location` moves a plant that exists. Reproduce this list in the report as the twelve tools the catalog records; it is explanation, never a call.
- A history block full of absent families gives a plan full of `unknown`. That is the honest result while the catalog's family coverage is unmeasured, not a failure.
- Without an interval, a family never returns to a bed within the plan, because a repeat does not qualify; a long plan over few families then ends in `open` slots. Supply `rotation_years` to let a family return.
- A bed with no history at all stays `unknown` in the first seasons. One `bed:season:none` entry establishes it.
- This skill itself was not run against a live instance; it has no tool calls to get wrong, and its input blocks inherit that status.

## Source

Governed by `spec/process/crop-rotation-planning/en.md` §A and §D to §G.
