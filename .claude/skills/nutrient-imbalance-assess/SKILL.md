---
name: nutrient-imbalance-assess
description: "Determines whether a Kamerplanter plant is undersupplied, oversupplied, or unable to take up nutrients it already has, by ranking the supply record on an evidence ladder rather than reading the symptom. Use when a recipe must judge a suspected deficiency, decide whether feeding would help or harm, interpret an EC or pH reading, or answer whether a plant needs more fertiliser. Refuses to propose a dosage when the evidence cannot establish the direction."
---

# Assess a nutrient imbalance

Decides **direction** before magnitude. Too little and too much fertiliser produce the same leaf: marginal necrosis, interveinal chlorosis, stunted new growth. Reading the symptom and reaching for the familiar explanation gets the sign wrong half the time, and feeding an already over-fed plant makes it worse.

The plant's context — species, phase, care history — must already be established. Tools are on the `kamerplanter` MCP server as `mcp__kamerplanter__<tool>`.

## Evidence ladder

Rank every claim by what it rests on. A lower tier corroborates or contradicts a higher one; it never overrides it. The tier travels with the claim into the output.

| Tier | Evidence | Weight |
|------|----------|--------|
| 1 | A measured value with a recognisable unit — EC, pH, runoff reading — from a diary entry | Decides direction on its own when recent enough |
| 2 | Phase `target_ec_ms` and `npk_ratio` against confirmed feeding frequency with recorded dose amounts, and substrate baseline; frequency without amounts is tier 3 | Decides direction when tier 1 is absent, at reduced confidence |
| 3 | Care-log pattern alone — feeding frequent, rare, or snoozed; repotting overdue | Supports a direction, never establishes one |
| 4 | Visible symptoms | Localises which nutrient and how far advanced, never the direction |
| 5 | Species `nutrient_demand_level` and phase expectation | Sets the prior only |

**When the highest available tier is 3 or below, propose no dosage change.** Name the measurement that would resolve it instead. That refusal is the deliverable, not a failure of the run.

## Procedure

### 1. Gather the target side

Call `mcp__kamerplanter__get_plant_nutrient_plan`. When a plan exists, resolve the phase that applies at the observation's date using `phase_started_at` against each phase's `week_start` and `week_end`, then read that phase's `target_ec_ms` and `npk_ratio`.

When it returns `{"plan": null}` — an ordinary and common state — say so, fall back to the species `nutrient_demand_level` and the phase definition, and confine the result to a qualitative direction. Do not synthesise a `target_ec_ms`.

### 2. Gather the actual side

From `mcp__kamerplanter__get_plant_care_log`: feeding frequency, the most recent confirmation, and any `snoozed` entries.

From `mcp__kamerplanter__get_plant_diagnostics`: the recorded feedings, under `feeding_events`. Pass `window_days` reaching back to the start of the plant's current phase where the context gives that date, at least 14 and at most 365, and state the window you used. Each event carries `volume_applied_liters`, `fertilizers_used`, `measured_ec_before` / `_after`, `measured_ph_before` / `_after`, `runoff_ec`, `runoff_ph`, `runoff_volume_liters` and a `timestamp` — these are the recorded dose amounts tier 2 needs. An empty `feeding_events` means none was recorded inside the window, not that the plant was never fed. Rank an event's EC and pH readings at tier 2, as part of the supply record, not at tier 1 — the spec has not decided whether they count as tier 1 — and say that you did.

From the diary entries' `measurements`: any EC, pH, or runoff value.

**Somebody has to fetch those entries, and this skill does not.** They arrive from the caller, which loads `diary-measurements-read` to list them with `mcp__kamerplanter__list_diary_entries` for the plant and read each with `mcp__kamerplanter__get_diary_entry`. `plant-context-collect` does **not** do this: it establishes what is normal for a plant, and a dated reading is evidence for one question.

Decide *read but empty* against *not read* on the caller's read report — how many entries were listed, opened, and carried no `measurements` — never on an empty measurement list. An empty diary is the common case, and reading emptiness as a caller bug turns the ordinary run into a reported defect. Where no read report arrived, say the diary was not read and name that as the gap.

An empty result after a real read is ordinary. It puts the assessment at tier 3 or below, which is a legitimate outcome and not a failed run.

`measurements` is an open object with no declared schema, so normalise the keys before use and **discard any value whose unit or provenance is ambiguous**, stating that you did. A number labelled `ec` may be millisiemens or microsiemens, from the tank or the runoff; guessing turns tier 1 evidence into a wrong answer with high confidence.

### 3. Read the substrate

Call `mcp__kamerplanter__list_substrates` with `tenant` and match the plant's medium; without `tenant` a mix the garden created itself is missing from the list. `ph_base`, `ec_base_ms`, `buffer_capacity`, and `cec_meq_per_100g` decide how far a reading may drift before it means anything, and how fast a correction will act.

The same weekly dose is unremarkable in a high-CEC, well-buffered medium and an oversupply in an inert one. A plan's `recommended_substrate_type` states which it assumed; a mismatch with the actual medium undermines every target comparison and is a finding in its own right.

### 4. Decide the direction

| State | Signature | Correction |
|-------|-----------|------------|
| **Undersupply** | Supply below the phase target — low measured EC, intervals longer than the plan, or a low-CEC medium retaining nothing — with no sign of blocked uptake | Move toward the phase target |
| **Oversupply** | Measured EC above target, or frequency exceeding the plan in a weakly buffering medium; marginal or tip necrosis on old and new leaves alike; deposit on the medium surface; no improvement after feeding | Reduce concentration or flush. Feeding is contraindicated |
| **Unavailability at adequate supply** | Deficiency symptoms while supply meets the target — pH outside what the substrate predicts, EC high enough to impede uptake, or ionic antagonism | **Not more of the missing nutrient.** Address availability |

The separator between the first and third state is almost never the leaf. It is a pH or EC reading. Where none exists, obtaining one *is* the recommended action.

### 5. Report

State the direction, the tier that established it, and — when a correction is proposed — what it assumes about the base water. Give the time a correction needs to show, derived from the substrate's buffering, so nobody re-corrects too early.

## Hard rules

- Never propose a correction without a stated direction and the tier behind it.
- Never recommend increasing a nutrient while unavailability at adequate supply is unexcluded.
- Never derive direction from symptoms alone, however characteristic they look.
- Never treat a confirmed feeding in the care log as a dose. It records that feeding happened, never how much of what. Where dose matters and is unrecorded, report the gap.
- Never actuate irrigation, dosing, or any Home Assistant device. A correction is a proposal for a human.
- Call no state-changing tool. Forbidden by name: `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`, `mcp__kamerplanter__submit_diary_analysis`, `mcp__kamerplanter__transition_plant_phase`, `mcp__kamerplanter__assign_species_phase_sequence`, `mcp__kamerplanter__assign_nutrient_plan`, `mcp__kamerplanter__record_feeding_event`, `mcp__kamerplanter__create_inspection`, `mcp__kamerplanter__clone_nutrient_plan`, `mcp__kamerplanter__set_nutrient_plan_phase_targets`, `mcp__kamerplanter__create_substrate_mix`, `mcp__kamerplanter__set_plant_substrate`. `mcp__kamerplanter__calculate_mixing_protocol` is safe — it carries no `dry_run` and no `idempotency_key` because it only calculates.

## Gotchas

- `mcp__kamerplanter__calculate_mixing_protocol` works on **EC-net**: `base_water_ec` is subtracted from the target. Omitting it silently overstates the dose, so state the assumption whenever you call it.
- `mcp__kamerplanter__get_plant_nutrient_plan` returning `plan: null` is the normal state for a plant never put on a programme — not an error and not a reason to stop.
- Most plans on this instance are global templates whose `tags` name a specific crop. A template tagged for one crop applied to another is a weaker target than a plant-specific plan; weigh it accordingly and say that you did.
- Repeated `snoozed` repotting in the care log points at exhausted substrate, which mimics undersupply and is not fixed by feeding.
- `mcp__kamerplanter__record_feeding_event` records a fertigation with its amount and the EC and pH before and after, but it writes, so a read-only run must not call it — the fertigation is recorded outside the run. It is read back only through `mcp__kamerplanter__get_plant_diagnostics` (measured 2026-11-05, #54); `mcp__kamerplanter__get_plant_care_log` returns none of it, so a plant with recorded feedings and an empty care log is ordinary. Confirmed reminders without amounts are still tier 3, and the honest output at tier 3 is a refusal plus a request to measure.
- `mcp__kamerplanter__get_plant_diagnostics` defaults to a 14-day window. A feeding older than the window is simply absent, so a too-short window turns a fed plant into an apparently unfed one.

## Source

Derived from `spec/process/nutrient-imbalance-detection/` §"The evidence ladder" and §"Deciding the direction", measured against the reference instance on 2026-08-05. The tool names and the write/read split come from `spec/mcp/kamerplanter-mcp-server/` instead, whose catalog was last re-measured on 2026-11-05, on a local instance; `spec/process/` names the feeding events `get_plant_diagnostics` returns as the fourth source of dose amounts, measured on 2026-11-05 (#54).
