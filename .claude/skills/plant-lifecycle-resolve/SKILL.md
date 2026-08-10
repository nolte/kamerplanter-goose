---
name: plant-lifecycle-resolve
description: "Establishes a Kamerplanter plant's lifecycle — annual, biennial or perennial, its sowing, bloom and harvest windows, dormancy and frost sensitivity — where the species record does not state it outright, by inferring from the phase assignment, the growing periods and the instance's own frost dates before falling back to cited research. Use when a recipe must judge whether a plant is on schedule, when overwintering or lifting is due, or whether a sowing window has passed. States the botanical and the cultivated cycle separately and marks every unverified value rather than guessing it."
---

# Resolve a plant's lifecycle

`cycle_type` **is not a field.** Measured 2026-08-07, `mcp__kamerplanter__get_species_info` returns no explicit annual/biennial/perennial value on either species probed. The cycle is inferred — and every inference here is a claim, not a lookup.

Read-only throughout. Tools are on the `kamerplanter` MCP server as `mcp__kamerplanter__<tool>`. Companion to `species-baseline-verify`, which checks the same record's plausibility; both are governed by one spec and share its evidence rule.

## The evidence rule

**No botanical value may be asserted from recall.** Read it from the record and label it, or research it and cite it. Three independent, non-quoting sources before anything counts as *established*; source ranking, the four confidence levels, and the rule that only *established* licenses a change are all in `species-baseline-verify` — apply them identically here rather than restating them.

Where a value cannot be established, mark it as missing and say what would settle it. **Never fill a window with a plausible month.**

## Resolution order

Each step can settle the question without the next. Stop at the first that does.

### 1. The instance's own assignment

The plant's `current_phase` from `mcp__kamerplanter__get_plant`, matched against `mcp__kamerplanter__list_phase_definitions` (29 definitions measured).

**A plant assigned `dormancy` is being treated as perennial by the system**, whatever the species record implies. `active_growth` at 180 days and `dormancy` at 120 carry `typical_duration_days`, `stress_tolerance` and `watering_interval_days`; a phase whose `phase_started_at` plus `typical_duration_days` is already past reframes "not flowering yet" from normal to notable.

This is the strongest single signal because it is what the system actually does with the plant.

### 2. Growing periods and month fields

From `mcp__kamerplanter__get_species_info`:

| Pattern | Indicates |
|---------|-----------|
| Sowing and harvest inside one calendar year, no dormancy phase | Annual |
| Bloom window in the year after sowing | Biennial |
| Recurring bloom and harvest with a dormancy phase | Perennial |

Read `growing_periods[]` before the top-level months. Measured, `Allium porrum` carries two periods — summer and winter leek — each with its own `direct_sow_months` and `harvest_months`; the top-level fields are their union and are too wide to reason with.

### 3. Overwintering profile

`mcp__kamerplanter__list_overwintering_profiles` returns per plant: `hardiness_zone_min`, `hardiness_rating`, `winter_action` with `winter_action_month`, `spring_action` with `spring_action_month`, plus `auto_generated`, `user_overridden` and `derived_path`.

**An `auto_generated: true` profile with `user_overridden: false` is a derivation, not an observation.** It inherits any error in the species baseline it came from, so it corroborates and never establishes. A `user_overridden: true` profile is an observation and outranks the species record.

### 4. Researched, under the three-source rule

Only where the record is silent or self-contradictory. Resolve the accepted scientific name against POWO/WCVP or GBIF first — a wrong name makes every subsequent source the wrong plant.

Research per plant: life form; germination and sowing windows, including whether the species is started indoors or direct-sown and any stratification or vernalisation requirement; bloom window; harvest window; dormancy and overwintering method; frost sensitivity.

## Anchor timing to this instance, not to a rule of thumb

Call `mcp__kamerplanter__get_sowing_calendar` **with a `query`** — measured, an unnarrowed call is refused with `validation.error` naming the 148 species covered and a `limit` ceiling of 25.

It returns the instance's own `frost.last_frost_date`, `frost.first_frost_date` and `frost.eisheilige_date`, plus per-species bars. Measured for the reference instance: `2026-05-01`, `null`, `2026-05-15`.

`eisheilige_date` is this instance's answer to the mid-May frost question, and a sowing or planting-out recommendation is checked against it rather than against a remembered date. **Measured, `first_frost_date` was `null`** — when it is, every autumn claim (lifting tubers, bringing containers in, last harvest) is unanchored, and saying so is the answer. Do not substitute a date.

`sowing_indoor_weeks_before_last_frost` is counted back from `last_frost_date`; a direct-sowing window is counted forward from it.

## State both cycles

**Name the botanical cycle and the cultivated one separately whenever they differ.** Onion and leek are botanically biennial and grown as annual vegetables. Recording only one answers half the questions asked of it wrongly — "will it flower this year" and "when do I harvest" have different answers from the same plant.

This is the most common divergence in an edible catalogue and the reason the value cannot simply be copied out of a botanical reference.

## Report

State, per resolved value: the value, which step established it, the confidence, and the sources where researched. List separately:

- values read from the record
- values inferred, naming the inference
- values researched, with sources and confidence
- values that could not be established, naming what would settle each

Close with the resolved cycle — botanical and cultivated where they differ — and the windows anchored to the instance's frost dates.

## Hard rules

- **Never** invent a month, a window, or a cycle type. Establish it or mark it missing.
- **Never** treat an `auto_generated` overwintering profile as independent evidence.
- **Never** call `mcp__kamerplanter__get_sowing_calendar` without `query`.
- **Never** substitute a date for a `null` `first_frost_date`; report the autumn half as unanchored.
- **Never** judge against the union of `growing_periods[]` when more than one exists.
- **Never** collapse the botanical and cultivated cycle into one value where they differ.
- **Never** call a tool that changes state.
  Forbidden by name:
  `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`,
  `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`,
  `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`,
  `mcp__kamerplanter__submit_diary_analysis`.
- Report an absent tool as an explicit step result naming the tool. Never substitute another.

Governed by `spec/process/species-baseline-verification/en.md`.
