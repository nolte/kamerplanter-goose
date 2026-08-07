---
name: pest-pressure-assess
description: "Judges whether a suspected pest or disease on a Kamerplanter plant is biologically tenable, by testing the candidate's recorded biology against the plant, the medium, the season and the enclosure rather than against the symptom. Use when a recipe must confirm or reject a pest suspicion, decide whether a control measure is warranted, check a treatment's safety interval before a harvest, or answer what is eating a plant. Refuses to name a control when the identification cannot be established, and states which checks the record could not support."
---

# Assess pest pressure

Decides **tenability** before treatment. A catalogue of 34 pests always returns the closest match to a described symptom, and the closest match is right often enough that a wrong one reads as plausible — then selects a treatment, wastes a beneficial release, or breaks a pre-harvest interval.

The plant's context must already be established by `plant-context-collect`. This skill never reads photos and never writes. Tools are on the `kamerplanter` MCP server as `mcp__kamerplanter__<tool>`, all read-only.

## Evidence ladder

Rank every claim by what it rests on. A lower tier corroborates or contradicts a higher one; it never overrides it. The tier travels with the claim into the output.

| Tier | Evidence | Weight |
|------|----------|--------|
| 1 | A recorded inspection naming the organism, with pressure level and findings | Establishes presence on its own |
| 2 | Catalogue fields — `pest_type`, `lifecycle_days`, `optimal_temp_*`, `damage_symptoms`, or a disease's `environmental_triggers` | Confirms or falsifies a candidate; never establishes presence |
| 3 | Situation fit — species `plant_category`, phase, season, care history, enclosure | Narrows the candidate set, never selects from it |
| 4 | Visible symptoms from a photo | Localises and stages. Establishes presence only for an organism visible as itself, never for one inferred from its damage |
| 5 | General knowledge of the taxon not in the record | Reasoning aid only. **Always labelled "not recorded"** |

**Propose a treatment only on tier 1, or on tier 4 plus an uncontradicted tier 2.** Below that the deliverable is the observation that would resolve it — usually a named monitoring method, not another photo.

## What the record does not carry

Measured 2026-08-07. Read this before writing a finding, because these are the fields a plausible answer gets invented from:

`mcp__kamerplanter__get_pest` carries **no** `optimal_humidity_min`/`max`, **no** `host_plants`, **no** `prevention_tips`, **no** `monitoring_hints`, **no** `affected_plant_parts`, no severity or detection-difficulty rating, and no GBIF key. Any claim about humidity ecology, host range, or monitoring method is therefore tier 5 and must say so.

The single most useful check in classic IPM practice — spider mites are favoured by *dry* air, so raising humidity is a control — **cannot be made against this record**. State it as taxon knowledge or leave it out.

`mcp__kamerplanter__get_disease` is the better-equipped half: it carries `environmental_triggers[]` (`low_humidity`, `high_humidity`, `poor_air_circulation`, `condensation`, `drought_stress`, …), `incubation_period_days`, `pathogen_type`, and `affected_plant_parts[]`. For a disease the moisture argument is tier 2. Say which of the two you are in.

## Procedure

### 1. Read the plant's own history

Call `mcp__kamerplanter__get_plant_inspections` with the `plant_key`.

Measured on a plant never inspected it returns `count: 0` and an empty `items`. **An empty history means nobody looked, not that nothing is there.** Report it as "not inspected" — never as absence of pressure, and never as a reason to lower a suspicion.

### 2. Resolve the candidate against the catalogue

Never from memory. Search with `mcp__kamerplanter__list_pests` or `mcp__kamerplanter__list_diseases` using a `query` drawn from the observed symptom, then read the full record with `mcp__kamerplanter__get_pest` or `mcp__kamerplanter__get_disease`.

Name the tool you read in the output. A candidate that does not appear in either catalogue is reported as outside the catalogue, not approximated to the nearest entry.

### 3. Run the falsification tests, in order

Each can only reject. A candidate surviving all four is **not contradicted** — a weaker statement than *identified*, and the two must not be blurred.

**3a — Feeding mode against damage signature.** The sharpest test and the one that catches the most confident errors:

| Feeding mode | Organisms | Signature | Excluded |
|--------------|-----------|-----------|----------|
| Phloem-sucking with honeydew | aphids, whitefly, scale, mealybug | sticky honeydew, sooty mould, curled shoot tips, visible colonies | — |
| Cell-sucking without honeydew | spider mites, thrips | stippling, silvering, bronzing, webbing (mites), black frass specks (thrips) | **Honeydew. Mites or thrips paired with honeydew is wrong** |
| Chewing | caterpillars, flea beetles, beetles, slugs | hole and margin feeding, frass, slime trails | Sucking damage of any kind |
| Root and substrate | fungus gnat larvae, nematodes | wilting, root damage; above ground non-specific | A specific above-ground signature |

**3b — Taxon against `pest_type`.** Mites and spiders are `arachnid`, insects `insect`, slugs `gastropod`, roundworms `nematode`, vertebrates `mammal`. A spider mite recorded as `insect` is a catalogue defect: report it, do not correct it, and do not let it change the identification.

A family- or superfamily-rank `scientific_name` (`Aphididae`, `Sciaridae`, `Coccoidea`) is deliberate, not an error, as long as `common_name` and `pest_type` stay consistent with the rank.

**3c — Development against the temperature window.** `lifecycle_days` is a generation time at the recorded optimum. An infestation that escalated in a week is inconsistent with a candidate whose generation takes a month, at any temperature. This resolves orders of magnitude only — do not do arithmetic on a single reading. Where the site sits far outside `optimal_temp_min`–`optimal_temp_max`, development is slower than the record implies and rapid escalation makes the candidate *less* likely.

**3d — Situation.** Whether the organism can be where the plant is. A greenhouse whitefly on an indoor foliage plant is ordinary; a slug on a windowsill is not. For pests this test runs on tier 5, because host range and humidity ecology are absent; for diseases it runs on tier 2 via `environmental_triggers`. Say which.

### 4. Check the control side

**Beneficials.** `beneficials[].preys_on` states what each natural enemy actually takes. Check the listed enemy against the identified pest rather than trusting the association — measured, the beneficials attached to `Tetranychus urticae` lead with `Coccinellidae`, a generalist aphid predator and not the specialist a mite infestation calls for. An enemy that does not list the pest in `preys_on` is a finding.

Enclosed and open settings differ in kind: under glass or in a tent beneficials are *introduced* deliberately; outdoors they are *encouraged and conserved*, and a release recommendation is usually the wrong shape of advice.

**Treatments.** `treatment_type` and `application_method` place a measure in the IPM hierarchy — cultural and physical, then biological, then chemical. Opening with a chemical without stating why the earlier tiers are exhausted is incomplete regardless of efficacy.

`safety_interval_days` is the pre-harvest Karenz. When the species `allows_harvest` and a harvest is near, a treatment whose interval exceeds the time remaining is excluded — and saying so *is* the recommendation. Read `mcp__kamerplanter__get_treatment` when the nested summary is not enough.

Never offer two measures sharing an `active_ingredient` as alternatives; that selects for resistance. Where `active_ingredient` is `null` the mode of action is unknown from the record and the rotation claim cannot be made. Contraindications between treatments are **not recorded** — the classic broad-spectrum-after-release conflict is tier 5.

### 5. Report

State the candidate, the tier supporting it, which tests it survived, and **which could not be run because the record is silent**, by name. Rank findings by consequence: a claim that would cause a wrong or harmful measure above one merely incomplete, above a refinement.

A catalogue defect found along the way is reported as a finding against the catalogue and directed at `nolte/kamerplanter` — never corrected here.

## Hard rules

- **Never** call `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, `mcp__kamerplanter__claim_diary_analysis`, or `mcp__kamerplanter__submit_diary_analysis`. This skill reads and judges.
- **Never** state a pest's humidity preference, host range, or monitoring method as recorded. Those fields do not exist on `get_pest`.
- **Never** report an empty inspection history as absence of pressure.
- **Never** write *identified* where the evidence supports *not contradicted*.
- **Never** recommend a treatment whose `safety_interval_days` exceeds the time to harvest.
- **Never** correct a catalogue defect in place; report it.
- When a symptom fits a nutrient explanation equally well, hand it to `nutrient-imbalance-assess` rather than deciding between them here.
- Report an absent tool as an explicit step result naming the tool. Never substitute another.

Governed by `spec/process/pest-pressure-assessment/en.md`.
