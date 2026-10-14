---
name: planting-calendar
description: "Computes, for each candidate crop and growing period, the windows in which it can be sown, sown indoors, transplanted and harvested at one Kamerplanter garden, and says for every window which rule and which field produced it. Use when a plan or a recipe needs dates, when asked when a crop can go in at this garden, or before any planting is proposed. A window that cannot be computed from a recorded field is reported unknown with the missing input; it never uses a typical date, duration or offset from general knowledge."
---

# Compute a planting calendar

Turns candidate crops into windows, and says where each one came from. It proposes no planting run (that is `plant-planning`), judges no crop (that is `crop-selection`), recommends nothing and writes nothing. The weight a claim carries is `decision-policy`'s; the site profile it reads is `site-analysis`'s. Every tool below is on the `kamerplanter` MCP server and is addressed as `mcp__kamerplanter__<tool>`. All of them are read-only.

## Input

- **The site profile block** from `site-analysis`, with the garden's frost dates as it returned them. Without it, stop and say `site-analysis` must run first.
- **The candidates**: entries separated by commas, each a `species_key`, or a `species_key` and a `cultivar_key` joined by a colon (`<species_key>:<cultivar_key>`). Split at the commas and at the first colon of each entry and pass the parts to the tools one by one, never the joined text. When the entries come from `crop-selection`, each carries its verdict.
- **The target harvest window**, optional, in the caller's words, marked source `caller`.

## Procedure

### 1. Check the inputs and the pool

Both the site profile and at least one candidate must be present. Calendar at most 10 candidates per run, a guard and not a measured limit, and list the rest as not considered. A candidate whose verdict is `rejected` gets no calendar: list it as not computed, with the failed constraint. A candidate with verdict `undetermined`, or with none given, still gets one, and the calendar says so.

### 2. Read the candidate

Call `mcp__kamerplanter__get_species_info` with the `species_key`, and `include_cultivars` when a cultivar is named. The species record returns only its populated fields: an absent key means "not populated". Use the cultivar's value when it carries the attribute and the species' value otherwise, and record which, per attribute used.

### 3. Choose the growing period

If the record has `growing_periods[]`, compute the windows below for each entry, and identify an entry by the months it carries, never by its position. The top-level months are the union across periods: do not use them when periods exist. With no periods, use the top-level months and call the period `none`.

### 4. Compute the windows

A window is computed only from a field whose meaning is recorded. Otherwise it is `unknown`, and the reason names the missing input.

| Window | Method | Rule |
|--------|--------|------|
| Sowing | Direct sowing | The months of `direct_sow_months[]` of the period. For a frost-sensitive crop the garden's last frost date is a lower bound, applied only if `frost_sensitivity` reads unambiguously as tender and the frost date is readable; otherwise say "frost bound not applied" and why |
| Indoor sowing | Indoor, then transplant | The garden's last frost date minus `sowing_indoor_weeks_before_last_frost` weeks: one date. Unknown if either is absent or unreadable |
| Transplanting | Indoor, then transplant | For a frost-sensitive crop, not before the last frost date. The end is not recorded: report the start only, the end unknown |
| Harvest | Both | The months of `harvest_months[]` of the period |
| Maturity | Both | The cultivar's `days_to_maturity` is reported as a value. What it counts from is not recorded, so no harvest date is computed from it and the comparison is `unknown` |

Read the frost dates exactly as the site profile gives them and rename nothing. Their format is not recorded: when a date cannot be read as a date, every window that needs it is `unknown` for that reason. Use no typical date, no typical duration and no offset that no field supplies.

### 5. Compare with the harvest window

If the caller gave a target harvest window and the months of the harvest window are known and the caller's text reads as months, report the preference as `met`, `unmet` or `unknown`. It never drops a candidate.

### 6. Report

Return one block with these fields, in this order, for each candidate and period; apply `decision-policy` to every known window (evidence level, a confidence derived from the highest level that supports it, uncertainty, missing data).

```
PLANTING CALENDAR: <tenant> (given | discovered)
CANDIDATE: <species_key> / <cultivar_key | none>   verdict: <eligible | undetermined | rejected | none given>
  PERIOD: <the months it carries | none>
    sowing_window:      known | unknown   <value>; rule; fields; source; retrieved; level; or reason
    indoor_sowing:      known | unknown   <value>; rule; fields; source; retrieved; level; or reason
    transplant_window:  known | unknown   <start; end unknown>; rule; fields; source; retrieved; level; or reason
    harvest_window:     known | unknown   <value>; rule; fields; source; retrieved; level; or reason
    maturity:           days_to_maturity <n> (cultivar | species); comparison unknown (start point not recorded)
    harvest_preference: met | unmet | unknown
    attribute_origins:  <attribute>: cultivar | species
    confidence / uncertainty / missing_data
NOT COMPUTED: <candidate (reason), ...>
CALENDAR SUMMARY: <k> windows known, <u> unknown
UNKNOWN WINDOWS: <candidate / period / window (reason), ...>
```

## Hard rules

- Never fill an unknown window with a typical date, a typical duration or an offset.
- Never compute a harvest date from `days_to_maturity`.
- Never use the top-level months when growing periods exist.
- Never report a field the skill did not read.
- Never propose a planting run, a bed or a succession; hand the calendar to `plant-planning`.
- Never call `mcp__kamerplanter__get_sowing_calendar` yourself: the frost dates come from the site profile.
- Call no tool that changes state. Forbidden by name: `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`, `mcp__kamerplanter__submit_diary_analysis`, `mcp__kamerplanter__transition_plant_phase`, `mcp__kamerplanter__assign_species_phase_sequence`, `mcp__kamerplanter__assign_nutrient_plan`, `mcp__kamerplanter__record_feeding_event`, `mcp__kamerplanter__create_inspection`.
- Report a tool error verbatim, mark the affected window unknown with the error as the reason, and continue.

## Gotchas

- `get_species_info` was measured returning 23 fields for one species and 18 for another; a field that is missing for a species is not populated.
- `growing_periods[]` is the field a naive reading misses: one species carried a summer and a winter period, each with its own months.
- This skill itself was not run against a live instance. Field names come from `spec/process/species-baseline-verification/en.md`, measured on 2026-08-07 on two species.

## Source

Governed by `spec/process/plant-planning-and-planting-calendar/en.md` §A and §B.
