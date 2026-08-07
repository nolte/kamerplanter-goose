# Nutrient Imbalance Detection

Status: draft
Portfolio-Scope: local

## Context

Too little fertiliser and too much fertiliser look the same on a leaf. Marginal necrosis, interveinal chlorosis, stunted new growth, a dulled leaf surface — each appears both when a nutrient is missing and when the root zone is too concentrated to take it up. A process that reads the photo and reaches for the more familiar explanation will recommend feeding a plant that is already over-fed, and the recommendation makes the plant worse.

**The direction of a nutrient problem is not visible in the image. It is a property of the supply balance**, and that balance is reconstructible from Kamerplanter: a nutrient plan states the target EC and NPK ratio per phase, the substrate states its own baseline EC, pH, and buffering, the care log states when feeding was confirmed, and diary entries may carry measured values. This spec specifies how those are combined into a direction, a confidence, and a correction that points the right way.

It is the counterpart to [plant health image analysis](../plant-health-image-analysis/en.md), not a part of it. There, a deficiency reading is one possible finding among pests, disease, and drought, and the image is the primary evidence. Here, the nutrient question is the whole subject, the supply record is the primary evidence, and the image is one input that can corroborate or contradict it. The two are meant to compose: the image process may hand a suspected deficiency to this one, and this one returns a direction the image alone could not establish.

A third case sits between the two and is the reason this spec exists at all. A plant can show a textbook deficiency while being supplied correctly, because the nutrient is present and not available — locked out by pH drift, by an EC high enough to impede uptake, or by antagonism between ions. The visible symptom is a deficiency; the correct correction is the opposite of feeding.

Everything marked *measured* was read from the reference instance on 2026-08-05.

Readers: authors of the nutrient recipe in this repository, and anyone reviewing a correction it proposes before acting on it.

## Goals

- The direction of an imbalance — undersupply, oversupply, or unavailability at adequate supply — is decided from the supply record, never from the symptom alone
- A correction points the right way, and a run that cannot establish direction proposes no correction at all
- The substrate is part of the diagnosis, because the same feeding regime is safe in one medium and damaging in another
- Every claim names the evidence tier it rests on, so a reader can tell a measured EC from an inferred one
- The absence of a nutrient plan degrades the analysis in a stated way instead of silently inventing targets
- What the process cannot know from the record — how much was actually applied — is stated rather than estimated

## Non-Goals

- Applying fertiliser, confirming a feeding task, or changing a plant's nutrient plan
- Replacing a substrate or tissue laboratory analysis; this process reasons over the record Kamerplanter holds
- Authoring nutrient plans or fertiliser products — the catalog is the backend's
- Diagnosing pests, disease, or drought, except to exclude them as competing explanations for the same symptom — that is [plant health image analysis](../plant-health-image-analysis/en.md)
- Recipe mechanics and MCP transport, auth, and tenancy — specified in [the recipe project pattern](../../goose/recipe-project-pattern/en.md) and [the server spec](../../mcp/kamerplanter-mcp-server/en.md)
- Irrigation scheduling; water frequency enters only where it changes the salt balance

## Measured baseline

### The target side

`get_plant_nutrient_plan` returns the plan assigned to a plant, and `get_nutrient_plan` returns one by key. Measured, a plan carries `is_template`, `is_global_template`, `recommended_substrate_type`, `version`, `tags`, and a `phases` array whose entries carry `phase_name`, `sequence_order`, `week_start`, `week_end`, `is_recurring`, `npk_ratio` as `[N, P, K]`, and `target_ec_ms`. The reference instance holds 38 plans, mostly global templates.

**A plan is not guaranteed.** Measured on the reference plant: `get_plant_nutrient_plan` answered `{"plan": null}` — no plan assigned. This is the ordinary case for a plant that was never put on a feeding programme, and the process must produce something useful anyway.

### The actual side, and its limits

Three sources describe what the plant actually received, and none of them is a dosage record:

| Source | What it gives | What it does not give |
|--------|---------------|------------------------|
| `get_plant_care_log` | Confirmed reminders with `reminder_type`, `action` (`confirmed` / `snoozed`), `confirmed_at`, `interval_at_time_days`, `notes` | Which product, what concentration, what volume — a confirmed feeding is a boolean, not a dose |
| Diary `measurements` | Free-form measured values | Any schema at all: the field is an open object, documented only by the example `{'height_cm': 42, 'ph': 6.3}` |
| Diary entries typed `measurement` or `problem` | Observer text and tags around a reading | Units, method, or instrument calibration |

**`measurements` has no fixed key set.** Measured, its schema is `additionalProperties: true` with no declared properties. A process reading it must normalise keys and refuse ambiguous ones rather than assume that `ec` means mS/cm or that `ph` was taken from the runoff rather than the tank.

The care log's `action: "snoozed"` is evidence in its own right. Measured on the reference plant, `repotting` was snoozed twice — a plant kept in exhausted substrate accumulates a different problem than one repotted on schedule.

### The substrate

`list_substrates` returns, per medium, `type`, `ph_base`, `ec_base_ms`, `buffer_capacity`, `cec_meq_per_100g`, `water_retention`, `water_holding_capacity_percent`, `easily_available_water_percent`, `air_porosity_percent`, `irrigation_strategy`, `composition`, `reusable`, and `max_reuse_cycles`.

These decide how much a feeding error matters. A medium with high `cec_meq_per_100g` and high `buffer_capacity` absorbs a surplus and releases it slowly; an inert one passes it straight to the roots. The same weekly dose is unremarkable in the first and an oversupply in the second, and a plan's `recommended_substrate_type` is the plan's own statement about which it assumed.

### The correction tool

`calculate_mixing_protocol` computes per-fertiliser doses for a target volume and EC, in mixing order. Measured, it requires `fertilizer_keys`, `target_volume_liters`, and `target_ec_ms`, and accepts `base_water_ec` ("subtracted from the target — EC-net"), `target_ph`, `base_water_ph`, `alkalinity_ppm`, `substrate_type`, and `phase`. It carries **no** `dry_run` and no `idempotency_key`, which distinguishes it from the write tools: it calculates and persists nothing.

## The evidence ladder

Claims are ranked by what they rest on, and the rank travels with the claim into the result. A lower tier never overrides a higher one; it corroborates or contradicts it.

| Tier | Evidence | Weight |
|------|----------|--------|
| 1 | A measured value from a diary entry — EC, pH, runoff reading — with a recognisable unit | Decides direction on its own when recent enough |
| 2 | Plan target versus reconstructed supply: phase `target_ec_ms` and `npk_ratio` against confirmed feeding frequency and substrate baseline | Decides direction when tier 1 is absent, at reduced confidence |
| 3 | Care-log pattern alone — feeding confirmed often, rarely, or snoozed; repotting overdue | Supports a direction, never establishes one |
| 4 | Visible symptoms from the image process | Localises which nutrient and how advanced, never the direction |
| 5 | Species `nutrient_demand_level` and phase expectation | Sets the prior only; a `heavy_feeder` in fruit is not thereby deficient |

A run whose highest available tier is 3 or below reports a suspicion with its direction explicitly undetermined, and proposes no dosage change. Naming the missing measurement is the deliverable in that case.

## Deciding the direction

Three states must be distinguished, because their corrections differ and two of them share a symptom.

**Undersupply.** Symptoms consistent with a specific nutrient, supply below the phase target — low measured EC, feeding intervals longer than the plan, or a medium with low CEC that retains nothing — and no evidence of uptake blockage. Correction moves toward the phase target.

**Oversupply.** Measured EC above the phase target, or a supply frequency exceeding the plan in a medium that buffers little, typically with marginal or tip necrosis on older and newer leaves alike, crust or deposit visible on the medium surface, and no improvement after feeding. Correction reduces concentration or flushes; feeding is contraindicated.

**Unavailability at adequate supply.** Deficiency symptoms while supply meets the phase target. The candidates are pH outside the range the substrate's `ph_base` and `buffer_capacity` would predict, an EC high enough to impede uptake despite adequate ratios, or antagonism where one ion in surplus suppresses another. **The correction here is not more of the missing nutrient.** A run that cannot separate this state from undersupply says so and proposes no feeding.

The separator between the first and the third is almost never the leaf. It is a pH or EC reading, and when none exists, obtaining one is the recommended action.

## What the species and the plant change

The species sets the prior; it does not set the diagnosis.

| Source | Shifts |
|--------|--------|
| `nutrient_demand_level` from `get_species_info` | The plausibility of undersupply at a given feeding frequency — a `medium_feeder` and a heavy one tolerate different intervals |
| Current phase and its `target_ec_ms` in the plan | The target the actual is compared against; the same EC is correct in one phase and excessive in the next |
| `phase_started_at` against the plan's `week_start` / `week_end` | Which plan phase actually applies now, which is what makes a target comparison legitimate rather than approximate |
| Substrate `ph_base`, `buffer_capacity`, `cec_meq_per_100g` | How far a reading may drift before it is a finding, and how quickly a correction will take effect |
| `recommended_substrate_type` versus the actual medium | Whether the plan's targets were even written for this plant's situation; a mismatch is a finding of its own |
| `allows_harvest` and `harvest_months` from the species | Whether a correction must respect an approaching harvest, including any treatment safety interval |
| Cultivar `days_to_maturity` and traits | The phase timeline the plan's week windows are read against |

When no plan is assigned — measured to be a real and common state — the process falls back to the species `nutrient_demand_level` and the phase definition, states that it did, and confines itself to a qualitative direction. It does not invent a `target_ec_ms`.

## Output and boundaries

The process is read-only by default: it reads the record, may call `calculate_mixing_protocol` because that tool only calculates, and reports. A variant that records its conclusion as a diary entry via `add_plant_diary_entry` writes, and is therefore a separate `-apply` recipe under the recipe project pattern's naming rule.

A proposed correction states the target it aims at, the tier of evidence behind it, and what it assumes about the base water. It is a proposal for a human, never an instruction to a device.

## Requirements

- **MUST** establish the direction — undersupply, oversupply, or unavailability at adequate supply — before proposing any correction, and **MUST NOT** derive that direction from visible symptoms alone
- **MUST** tag every claim with the evidence tier it rests on, and **MUST NOT** let a lower tier override a higher one
- **MUST** propose no dosage change when the highest available evidence tier is 3 or below, and **MUST** instead name the measurement that would resolve the direction
- **MUST** read the substrate's `ph_base`, `ec_base_ms`, `buffer_capacity`, and `cec_meq_per_100g` before judging whether a supply level is excessive, since the same dose differs by medium
- **MUST** compare against the plan phase that applies at the entry's date, resolved through `phase_started_at` and the phase's `week_start` / `week_end`, not against the plan as a whole
- **MUST** state that no plan is assigned and fall back to `nutrient_demand_level` and the phase definition when `get_plant_nutrient_plan` returns `plan: null`, and **MUST NOT** synthesise a `target_ec_ms` in that case
- **MUST** treat a confirmed feeding in the care log as evidence that feeding happened and **MUST NOT** treat it as a dose; where dose matters and is unrecorded, the gap is reported
- **MUST** normalise `measurements` keys before use and **MUST** discard a value whose unit or provenance is ambiguous rather than assume a convention the open schema does not define
- **MUST** consider unavailability whenever deficiency symptoms coincide with supply at or above the phase target, and **MUST NOT** recommend increasing the affected nutrient while that state is unexcluded
- **MUST** state its assumption about base water (`base_water_ec`, `alkalinity_ppm`) whenever it calls `calculate_mixing_protocol`, since the result is an EC-net calculation
- **MUST NOT** call any state-changing tool in the read-only variant; the write variant **MUST** carry the `-apply` suffix, declare its effect, and confine its writes to `add_plant_diary_entry`
- **MUST NOT** actuate irrigation, dosing, or any Home Assistant device, regardless of how clear the correction is
- **SHOULD** exclude drought, root damage, pest pressure, and light stress as competing explanations before settling on a nutrient cause, drawing on `get_plant_inspections` and the image process rather than repeating their work
- **SHOULD** report a mismatch between the plan's `recommended_substrate_type` and the plant's actual medium as a finding, since it undermines every target comparison downstream
- **SHOULD** read the care log for `snoozed` actions, particularly repotting, and weigh substrate exhaustion as a cause of apparent undersupply
- **SHOULD** respect an approaching harvest in any recommended correction when the species `allows_harvest`, and name the safety interval where a treatment is involved
- **SHOULD** state how long a correction needs to show an effect, derived from the substrate's buffering, so a human does not re-correct too early
- **MAY** call `calculate_mixing_protocol` to quantify a correction, since it persists nothing, and **MAY** read `list_fertilizers` with `organic_only` when the grower's regime requires it
- **MAY** hand a suspected deficiency back to the image process for symptom localisation, and **MAY** be invoked by it in turn

## Acceptance Criteria

- [ ] Every proposed correction names a direction and the evidence tier that established it
- [ ] A run with no measurement and no plan proposes no dosage and names the measurement it needs
- [ ] A plant with `plan: null` still yields a qualitative assessment, explicitly marked as plan-less
- [ ] No result recommends increasing a nutrient while unavailability at adequate supply is unexcluded
- [ ] Substrate properties appear in the reasoning of any claim about excess
- [ ] Target comparisons cite the specific plan phase and its week window, not the plan as a whole
- [ ] A `measurements` value with an ambiguous unit is discarded with a stated reason, not silently interpreted
- [ ] The read-only recipe calls no state-changing tool; the write variant carries `-apply` and writes only diary entries
- [ ] No recipe under this spec calls a Home Assistant actuation tool
- [ ] Any `calculate_mixing_protocol` call in a result is accompanied by its base-water assumptions

## Open Questions

- Which `measurements` keys are actually in use across the instance's diary entries. The schema declares none, so the normalisation table this spec requires cannot yet be written from data — only from convention.
- Whether runoff EC and tank EC are distinguishable in the record. The distinction decides whether a reading describes what the plant receives or what remains in the medium, and nothing in the open schema separates them.
- Whether Home Assistant carries soil moisture or conductivity sensors that could supply tier-1 evidence per plant, and how a sensor would be bound to a plant instance. `GetLiveContext` exposes entity state, but no plant-to-entity mapping was found.
- Whether the antagonism cases worth naming (which ion suppresses which) belong in this spec, in the backend's glossary reachable via `search_glossary`, or in the knowledge base. Encoding them here risks the same drift this repository avoids for species data.
- How to weigh a plan whose `is_global_template` is true and whose `tags` name a different crop than the plant's species — measured, the reference instance's plans are largely cannabis-specific templates, while its plants are not.
- Whether "supply above target" can be reconstructed at all without dosage records, or whether tier 2 collapses to tier 3 in practice for growers who confirm reminders but log no amounts.

## Source

- Measured against the reference Kamerplanter instance on 2026-08-05 through `POST /api/v1/mcp`, read-only: `get_plant_nutrient_plan` (returned `plan: null`), `list_nutrient_plans` (38 plans), `get_nutrient_plan` for a global template's phase structure, `get_plant_care_log`, `list_substrates`, and `get_species_info`. No write tool was called.
- Input schemas for `calculate_mixing_protocol` and `add_plant_diary_entry` read live, including the open `measurements` object and the `DiaryEntryType` enum (`observation`, `problem`, `milestone`, `measurement`, `photo`, `note`)
- Companion process: [plant health image analysis](../plant-health-image-analysis/en.md)
- Recipe mechanics: [the Goose recipe project pattern](../../goose/recipe-project-pattern/en.md)
- Server contract: [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md)
