---
name: species-baseline-verify
description: "Checks whether the species baseline Kamerplanter holds is agronomically plausible — germination parameters, sowing depth against light requirement, hardiness against native habitat, timing against the instance's own frost dates — before a later step reasons on top of it. Use when a recipe depends on species master data being right, when a value looks implausible, or when asked whether a species record can be trusted. Reports absent fields as unpopulated rather than as negative facts, and proposes a correction only under the three-source rule."
---

# Verify a species baseline

Every judgement about a plant is measured against what is normal for its species. **Whether that baseline is right is checked nowhere**, and a wrong one does not fail loudly — it produces a confident, well-reasoned, wrong answer downstream.

Read-only throughout. Tools are on the `kamerplanter` MCP server as `mcp__kamerplanter__<tool>`. Corrections are proposals directed at `nolte/kamerplanter`, where the species data actually lives; this skill writes nothing.

For the cycle type and the sowing, bloom, harvest and dormancy windows, use `plant-lifecycle-resolve` — the two share this spec and this discipline.

## Absence is not a fact

Measured 2026-08-07: `mcp__kamerplanter__get_species_info` returns **only the populated fields**, and the set differs per species. `Allium porrum` came back with 23 fields including a full `seed_profile`; `Spathiphyllum wallisii` with 18 and no `seed_profile` at all.

**Neither carried `toxicity`, although the tool's own description advertises it.** Whether the field is unpopulated or unexposed is unresolved. Until it is, never report a plant as non-toxic because the field is missing — that is how someone is told a peace lily is safe around cats.

Measured absent on both species, so their checks cannot run at all: `photosynthesis_type`, `light_compensation_point_ppfd_*`, `shade_tolerance`, `salt_tolerance_*`, `waterlogging_tolerance`, `soil_ph_preference`, `effective_root_depth_cm`, `climacteric`, `harvested_part`, `harvest_pattern`, `propagation_configs`, `allergen_info`, `cycle_type`. Report these as *not run*, never as *passed*.

## The evidence rule

**No botanical value may be asserted from recall.** Every claim is either read from the record and labelled as such, or researched and cited. This is the failure mode the skill exists to prevent: a fluent, authoritative, invented number.

A **correction** requires three independent sources in agreement. Independent means not quoting one another — three pages repeating one nursery's catalogue text are one source.

| Rank | Source | Reliability |
|------|--------|-------------|
| 1 | University horticulture institutes, agricultural chambers and extension services, RHS, ISTA | Highest |
| 2 | Reference works and botanical databases — Missouri Botanical Garden, PFAF, POWO/WCVP, FAO | High |
| 3 | Seed houses and nurseries, for timing specifically | High for timing |
| 4 | Gardening portals with an editorial desk | Medium |
| 5 | Forums and community posts | Supporting only |

**Never sufficient alone:** Wikipedia, AI-generated text, unattributed blog posts, or any page whose only content cites another source. Search in at least two phrasings — scientific and common name, German and English for Central European crops — because one phrasing selects one publishing tradition.

| Confidence | Basis | Licenses |
|------------|-------|----------|
| **Established** | Three or more independent sources agree | A proposed correction, with sources |
| **Probable** | Two agree, or three with minor divergence | A finding. The recorded value stands |
| **Uncertain** | Sources conflict, or only one found | A finding naming the conflict. The value stands |
| **Unverifiable** | No usable source | A named gap. The value stands |

Only the top level moves anything. **A run that finds twelve doubtful values and proposes no correction has done its job**; one that "improves" a value at *probable* has not.

## Procedure

### 1. Read the record

Call `mcp__kamerplanter__get_species_info` with the `species_key`. Where a cultivar is in play, also `mcp__kamerplanter__get_cultivar` — its `traits` and `days_to_maturity` narrow the species expectation.

List which of the fields below are present and which are absent, before checking anything. That list is half the deliverable.

### 2. Select the growing period

`growing_periods[]` is the field a naive read misses. Measured, `Allium porrum` carries two — a summer and a winter leek — **each with its own `direct_sow_months` and `harvest_months`**. The top-level months are the union across periods, so judging against them without selecting the period first yields a window too wide to be wrong and too wide to be useful.

### 3. Check seed and germination

Only where `seed_profile` exists.

- `germination_temp_min_c` < `germination_temp_max_c`, and the range fits the species rather than a default. Cold germinators near 2–10 °C, warm ones near 20–30 °C. A catalogue where every species reads 20–25 °C has a default, not data.
- **`sowing_depth_cm` against `light_germination`.** A light germinator is pressed onto the surface, not buried — `light_germination: light` at 1 cm is a contradiction the schema permits and the seed does not survive. High severity. Measured, `Allium porrum` reads `dark` at 1.0 cm, which is consistent.
- `light_germination` against seed size: fine-seeded species tend to need light, large-seeded ones darkness.
- `pretreatment[]` against origin. Cold stratification belongs to temperate woody and cold-germinating species, scarification to hard-coated seeds, soaking to slow imbibers. **Stratification on a tropical species is a finding.**
- `seed_viability_years` and `days_to_germination` consistent with each other and with the temperature range.

### 4. Check climate and habitat

`frost_sensitivity` against `hardiness_zones` and `native_habitat`. Measured, `Spathiphyllum wallisii` reads `sensitive`, zones `10b`–`11a`, Central American habitat — internally consistent. The contradiction to look for is a `hardy` rating on a species whose zones start at 10.

`base_temp_gdd` against the same: measured 5.0 for leek, 15.0 for the peace lily. A tropical species with a temperate base temperature accumulates growth degree days that never happened.

### 5. Check timing against the instance's own calendar

Call `mcp__kamerplanter__get_sowing_calendar` **with a `query`** — measured, an unnarrowed call is refused with `validation.error` naming the 148 species covered and a `limit` ceiling of 25.

It returns `frost.last_frost_date`, `frost.first_frost_date`, and `frost.eisheilige_date` for this instance. Check `direct_sow_months` and `sowing_indoor_weeks_before_last_frost` against those dates, not against a remembered regional rule. Measured, `first_frost_date` was `null` — when it is, say the autumn half of the calendar is unanchored rather than substituting a date.

Bloom before harvest for a fruiting species; overlap is normal for a leaf or cut-and-come-again crop and suspicious for a fruit. `allows_harvest` consistent with `growth_habit` and the presence of `harvest_months`.

### 6. Check across fields

A field can be plausible alone and impossible in company. Check at least: seed profile present but no sowing months; harvest months present with `allows_harvest: false`; a cultivar's `days_to_maturity` incompatible with the species' sowing-to-harvest span; `compatible_companions` scored high for a species that cannot share the same site conditions.

`compatible_companions` concerns planting decisions. Do not carry it into a physiological judgement.

### 7. Report

Per field: what the record holds, whether the check ran, the finding, the confidence, the sources. **List fields whose check could not run separately from checks that ran and passed** — collapsing the two turns a gap into a false assurance.

Rank by consequence: a value that would cause a failed sowing, a dead plant, or a wrong safety claim above one merely misleading, above a refinement.

## Hard rules

- **Never** assert a botanical value from recall. Read it and label it, or research it and cite it.
- **Never** propose a correction below *established*. Report the doubt and leave the value.
- **Never** read a missing field as a negative fact. In particular, **never** report a plant as non-toxic because `toxicity` is absent.
- **Never** judge an observation against the union of `growing_periods[]` when more than one exists.
- **Never** call `mcp__kamerplanter__get_sowing_calendar` without `query`.
- **Never** substitute a frost date for a `null` one.
- **Never** call a tool that changes state.
  Forbidden by name:
  `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`,
  `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`,
  `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`,
  `mcp__kamerplanter__submit_diary_analysis`.
- Report an absent tool as an explicit step result naming the tool. Never substitute another.

Governed by `spec/process/species-baseline-verification/en.md`.
