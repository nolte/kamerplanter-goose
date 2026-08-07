# Pest Pressure Assessment

Status: draft
Portfolio-Scope: local

## Context

Naming a pest is not diagnosing one. A catalogue of 34 pests will always return the closest match to a described symptom, and the closest match is right often enough that a wrong one reads as plausible. The cost of the wrong name is not academic: it selects a treatment. Recommending a predatory mite against thrips that turn out to be aphids wastes a release; recommending a broad-spectrum insecticide alongside a beneficial neutralises the beneficial; recommending anything at all within the safety interval of a crop about to be harvested is a food-safety error, not a gardening one.

**What separates a real identification from a plausible one is rarely the symptom. It is whether the organism's biology fits the plant, the medium, the season, and the enclosure it is supposed to be living in.** That check is mechanical where the record supports it — a mite recorded as `pest_type: insect` is wrong regardless of how well its symptoms match — and impossible where the record is silent.

This spec exists because the record is silent in specific, knowable places. Measured, `get_pest` carries a temperature optimum and a generation time but **no humidity range, no host-plant list, no prevention or monitoring guidance, and no severity rating**. The most valuable single check in the source procedure this process inherits — that spider mites are favoured by *dry* air, so raising humidity is a control and not an aggravation — cannot be made against the record at all. `get_disease` does carry `environmental_triggers`, so the same reasoning holds for diseases and not for pests. A process that does not know where its data stops will fill those gaps from the model's own knowledge and present the result in the same voice as a recorded fact.

It is the counterpart to [plant health image analysis](../plant-health-image-analysis/en.md), not a part of it, and it composes with it the same way [nutrient imbalance detection](../nutrient-imbalance-detection/en.md) does. There, a pest reading is one possible finding among deficiency, disease, and drought, and the image is the primary evidence. Here, the pest question is the whole subject, the inspection history and the catalogue are the primary evidence, and the image corroborates or contradicts.

Everything marked *measured* was read from the reference instance on 2026-08-07.

Readers: authors of pest-related recipes in this repository, and anyone reviewing a control measure one proposes before acting on it.

## Goals

- An identification is accepted only when the organism's recorded biology fits the plant and its situation, never on symptom resemblance alone
- Every claim names whether it came from the record or from general knowledge of the taxon, because the two are not equally checkable
- A control measure is proposed only when the identification carries enough evidence to select one, and the refusal names what would resolve it
- The distinction between sucking, rasping, and chewing damage is applied as a falsification test, since it contradicts more wrong identifications than any other single check
- The safety interval of any named treatment is stated against the plant's harvest situation
- Where the record cannot answer — humidity ecology, host range, monitoring method — the process says so instead of answering anyway

## Non-Goals

- Applying a treatment, confirming a care task, or recording an inspection; this process reads and judges
- Replacing a laboratory determination or a microscope; it reasons over the record Kamerplanter holds plus what is visible
- Authoring the pest, disease, or treatment catalog — that is the backend's, and correcting it belongs in `nolte/kamerplanter`
- Diagnosing nutrient disorders or drought, except to exclude them as competing explanations — that is [nutrient imbalance detection](../nutrient-imbalance-detection/en.md)
- Reading images; a suspicion arrives from [plant health image analysis](../plant-health-image-analysis/en.md) or from a diary entry
- Recipe mechanics and MCP transport, auth, and tenancy — specified in [the recipe project pattern](../../goose/recipe-project-pattern/en.md) and [the server spec](../../mcp/kamerplanter-mcp-server/en.md)

## Measured baseline

### The plant's own history

`get_plant_inspections` returns a plant's IPM inspection history — pressure level, findings, symptoms. Measured on a plant never inspected it answers `count: 0` with an empty `items` array and a plain-text summary saying so. **An empty history is the ordinary case**, not an error and not evidence of absence; it means only that nobody looked, or that nobody recorded looking.

### The catalogue, and where it stops

Measured, `list_pests` reports 34 pests and `list_diseases` 34 diseases. `get_pest` on `Tetranychus urticae` returned exactly these fields:

| Present | Value measured |
|---------|----------------|
| `pest_key`, `scientific_name`, `common_name`, `common_name_de` | `8974`, `Tetranychus urticae`, `Spider Mites`, `Spinnmilben` |
| `pest_type` | `arachnid` |
| `damage_symptoms`, `detection_symptom_hint` | free German prose naming stippling, webbing, bronzing |
| `lifecycle_days` | `21` |
| `optimal_temp_min`, `optimal_temp_max` | `25.0`, `30.0` |
| `description` | `null` |
| `treatments[]` | `treatment_key`, `name`, `treatment_type`, `active_ingredient`, `application_method`, `safety_interval_days`, `dosage_per_liter`, `protective_equipment[]` |
| `beneficials[]` | `common_name`, `scientific_name`, `preys_on[]`, `description` |

**Absent, and load-bearing for the checks this process inherits:** `optimal_humidity_min`/`max`, `host_plants`, `prevention_tips`, `monitoring_hints`, `affected_plant_parts`, any severity or detection-difficulty rating, any GBIF taxon key. Their absence is not a gap to be filled silently; it is the boundary of what an assessment can assert as recorded.

`get_disease` is the better-equipped half. Measured, it carries `pathogen_type`, `incubation_period_days`, `affected_plant_parts[]`, and **`environmental_triggers[]`** with values including `low_humidity`, `high_humidity`, `warm_temperature`, `cool_temperature`, `poor_air_circulation`, `condensation`, `drought_stress`. `Erysiphe spp.` is triggered by `low_humidity` and `Botrytis cinerea` by `high_humidity` — the same moisture axis that is missing on the pest side.

### The situation

The plant's context is established by the collect step, not here: `get_plant`, `get_species_info`, `list_phase_definitions`, `get_plant_care_log`. Three of its fields decide pest plausibility and are named here because this process consumes them: `plant_category` (measured `tropical_foliage` on a houseplant) bounds which organisms are possible at all; `growth_habit` and `root_type` decide whether damage is above or below ground; `allows_harvest` decides whether a safety interval applies.

Enclosure is not a recorded field. It is inferred from the site type and the species' `frost_sensitivity` and `hardiness_zones`, and that inference is itself a claim that has to be stated.

## The evidence ladder

Rank every claim by what it rests on. A lower tier corroborates or contradicts a higher one; it never overrides it. The tier travels with the claim into the output.

| Tier | Evidence | Weight |
|------|----------|--------|
| 1 | A recorded inspection naming the organism, with pressure level and findings | Establishes presence on its own |
| 2 | Catalogue fields — `pest_type`, `lifecycle_days`, `optimal_temp_*`, `damage_symptoms`, or a disease's `environmental_triggers` | Confirms or falsifies a candidate; cannot establish presence |
| 3 | Situation fit — species `plant_category`, phase, season, care history, enclosure | Narrows the candidate set, never selects from it |
| 4 | Visible symptoms from a photo | Localises and stages; establishes presence only for an organism visible as itself, never for one inferred from damage |
| 5 | General knowledge of the taxon not in the record — host range, humidity ecology, monitoring method, natural enemies beyond `beneficials[]` | Reasoning aid only. **Always labelled as not from the record** |

**A treatment is proposed only when the identification rests on tier 1, or on tier 4 plus an uncontradicted tier 2.** Below that, the deliverable is the observation that would resolve it — which is usually a named monitoring method, not another photo.

## The falsification tests

Applied in order. Each one can only reject a candidate, never confirm it. A candidate surviving all four is *not contradicted*, which is a weaker statement than *identified*, and the output must not blur them.

### 1. Feeding mode against damage signature

The sharpest test, and the one that catches the most confident errors:

| Feeding mode | Organisms | Signature | Excluded |
|--------------|-----------|-----------|----------|
| Phloem-sucking with honeydew | aphids, whitefly, scale, mealybug | sticky honeydew, sooty mould, curled shoot tips, visible colonies | — |
| Cell-sucking without honeydew | spider mites, thrips | stippling, silvering, bronzing, webbing (mites), black frass specks (thrips) | **Honeydew. A record pairing mites or thrips with honeydew is wrong** |
| Chewing | caterpillars, flea beetles, beetles, slugs | hole and margin feeding, frass, slime trails | Sucking damage of any kind |
| Root and substrate | fungus gnat larvae, nematodes | wilting, root damage; above ground non-specific | A specific above-ground signature |

### 2. Taxon against `pest_type`

Mites and spiders are `arachnid`, insects `insect`, slugs and snails `gastropod`, roundworms `nematode`, vertebrates `mammal`. A spider mite recorded as `insect` is a catalogue defect and a finding in its own right — report it, do not silently correct it, and do not let it change the identification.

A family- or superfamily-rank `scientific_name` (`Aphididae`, `Sciaridae`, `Coccoidea`) is deliberate, not an error, as long as `common_name` and `pest_type` stay consistent with the rank.

### 3. Development against the recorded temperature window

`lifecycle_days` is a generation time at the recorded optimum, and the two have to be consistent with each other and with the observation's timeline. An infestation that escalated in a week is inconsistent with a candidate whose generation takes a month, at any temperature. Orders of magnitude are what this test resolves; it does not support arithmetic on a single reading.

Where the site's actual temperature is far from `optimal_temp_min`–`optimal_temp_max`, development is slower than the record implies, and a rapid escalation makes the candidate less likely rather than more.

### 4. Situation

Whether the organism can be where the plant is. A greenhouse whitefly on an indoor foliage plant is ordinary; a slug on a windowsill is not. Season and overwintering matter outdoors and almost not at all in a heated room.

**This test runs on tier 5 for pests.** The record carries no host range and no humidity ecology, so the answer comes from general knowledge of the taxon and is labelled accordingly. For diseases it runs on tier 2, because `environmental_triggers` is recorded — and the difference between the two is worth stating in the output rather than smoothing over.

## From identification to control

Once a candidate survives, the control side is better served by the record than the identification was.

**Beneficials.** `beneficials[].preys_on` states what each natural enemy actually takes. Check the named enemy against the identified pest rather than trusting the association: measured, the beneficials attached to `Tetranychus urticae` lead with `Coccinellidae`, which is a generalist aphid predator and not the specialist a mite infestation calls for. An enemy that does not list the pest in `preys_on` is a finding.

Indoor and outdoor differ in kind here, not degree: under glass or in a tent, beneficials are *introduced* deliberately and the question is which species and when; outdoors they are *encouraged and conserved*, and a release recommendation is usually the wrong shape of advice.

**Treatments.** `treatment_type` and `application_method` place a measure in the IPM hierarchy — cultural and physical before biological, biological before chemical. A recommendation that opens with a chemical, without stating why the earlier tiers are exhausted or unavailable, is incomplete regardless of whether the chemical works.

`safety_interval_days` is the pre-harvest Karenz and is checked against the plant, not quoted in the abstract. When `allows_harvest` is true and a harvest is near, a treatment whose interval exceeds the remaining time is excluded, and saying so is the recommendation.

Two measures sharing an active ingredient or a mode of action must not be recommended in sequence as if they were alternatives; that is how resistance is selected for. Where `active_ingredient` is `null`, the mode of action is unknown from the record and the rotation claim cannot be made.

**Contraindications are not recorded.** No field pairs a treatment with one it conflicts with, so the classic conflict — a broad-spectrum insecticide applied after a beneficial release, wiping out the release — has to be reasoned rather than looked up, and stated as tier 5.

## Output and boundaries

The result names the candidate, the tier that supports it, which falsification tests it survived, and which could not be run because the record is silent. A candidate that survives every runnable test is reported as *not contradicted*, with the tests that could not run listed by name.

Findings carry a severity: a claim that would lead to a wrong or harmful control measure ranks above one that is merely incomplete, which ranks above a refinement. A catalogue defect found along the way — a wrong `pest_type`, a honeydew-bearing mite — is reported as a finding against the catalogue and directed at `nolte/kamerplanter`, never corrected here.

The process writes nothing. Recording an inspection or a diary entry is a separate, `-apply`-suffixed step.

## Requirements

- **MUST** call `get_plant_inspections` before assessing, and **MUST** report an empty history as "not inspected" rather than as absence of pressure
- **MUST** resolve a candidate against `get_pest` or `get_disease` rather than from the model's own knowledge, and **MUST** name the tool it read
- **MUST** apply the feeding-mode test to every candidate, and **MUST** reject a candidate whose recorded `damage_symptoms` contradicts its feeding mode
- **MUST** report a `pest_type` inconsistent with the taxon as a finding against the catalogue, and **MUST NOT** silently substitute the correct value
- **MUST** label every claim resting on host range, humidity ecology, monitoring method, or contraindication as not recorded, since measured none of these exists on `get_pest`
- **MUST NOT** state a humidity preference for a pest as though it were recorded; for a disease **MUST** cite `environmental_triggers` where it carries one
- **MUST** distinguish *not contradicted* from *identified* in the output, and **MUST** list the tests that could not be run
- **MUST** check `safety_interval_days` against the plant's harvest situation whenever `allows_harvest` is true, and **MUST** exclude a treatment whose interval exceeds the time remaining
- **MUST NOT** call `confirm_care_task`, `add_plant_diary_entry`, or any other state-changing tool from a recipe under this spec
- **SHOULD** verify each entry in `beneficials[]` against the identified pest via `preys_on`, and **SHOULD** report a mismatch as a finding
- **SHOULD** state whether a control measure is meant for an enclosed or an open setting, since introduction and conservation of natural enemies are different recommendations
- **SHOULD** name the monitoring method that would raise the evidence tier, in place of a treatment, whenever the identification rests below tier 2
- **SHOULD** respect the IPM hierarchy in the order measures are offered, and **SHOULD** state why an earlier tier is unavailable when opening with a later one
- **SHOULD** consult `search_glossary` for a term the report uses in a domain-specific sense, rather than defining it locally
- **MAY** read `get_treatment` for a measure's full record when the nested `treatments[]` summary is insufficient
- **MAY** hand a suspected deficiency to [nutrient imbalance detection](../nutrient-imbalance-detection/en.md) when the symptom fits both, and **MAY** be invoked by the image process in turn

## Acceptance Criteria

- [ ] Every identification names its evidence tier and the tool that supplied the record
- [ ] No result recommends a treatment on a tier-3-or-below identification
- [ ] A plant with no inspection history yields an assessment that states the history is empty
- [ ] Every candidate has been run through the feeding-mode test, and the outcome appears in the output
- [ ] No claim about host range, humidity ecology, or monitoring method is presented as recorded
- [ ] A disease assessment citing a moisture condition cites `environmental_triggers`
- [ ] Every named treatment carries its `safety_interval_days` and a statement about the plant's harvest situation
- [ ] Recommendations respect the IPM ordering, or state why not
- [ ] Beneficial recommendations are checked against `preys_on` and mismatches are reported
- [ ] A catalogue defect is reported as a finding, not corrected in place
- [ ] No recipe under this spec calls a state-changing tool
- [ ] The output distinguishes *not contradicted* from *identified*

## Open Questions

- Whether `optimal_humidity_min`/`max` exists upstream and is simply not exposed, or is absent from the model altogether. The distinction decides whether this process should ask for a field or accept a permanent tier-5 gap.
- Whether `host_plants` will follow. Until it does, the plausibility of a pest on a given species rests entirely on general knowledge, which is the weakest link in an otherwise record-backed chain.
- What `get_plant_inspections` actually returns on a plant that *has* been inspected. Measured only against an empty history; the field names for pressure level and findings are taken from the tool description, not from a populated response.
- Whether the disease and pest catalogs share a symptom vocabulary, or whether the same visible sign is described differently in each — which decides if a single symptom can be matched against both in one pass.
- Whether Home Assistant carries humidity or temperature sensors that could raise the situation test from tier 3 to tier 1, and how a sensor would be bound to a plant instance. The same open question as in the nutrient process, and the same missing mapping.
- Whether contraindications between treatments belong here, in the backend catalog, or in the glossary. Encoding them in this spec risks the drift this repository avoids for species data.

## Source

- Measured against the reference Kamerplanter instance on 2026-08-07 through `POST /api/v1/mcp`, read-only: `list_pests` (34), `get_pest` (`Tetranychus urticae`, full field set including nested `treatments[]` and `beneficials[]`), `list_diseases` (34, `environmental_triggers` observed), `get_plant_inspections` (empty history), `get_species_info` (`Allium porrum`, `Spathiphyllum wallisii`), `list_phase_definitions` (29). No write tool was called.
- Domain procedure inherited from `nolte/kamerplanter`, `.claude/skills/check-pest-data/SKILL.md` — the feeding-mode signature table, the taxon-to-`pest_type` mapping, the generation-time magnitudes, the indoor-versus-outdoor treatment distinction, and the IPM ordering. That skill judges the repository's own `ipm.yaml`; this spec governs the same judgement applied to what the MCP server returns.
- Companion processes: [plant health image analysis](../plant-health-image-analysis/en.md), [nutrient imbalance detection](../nutrient-imbalance-detection/en.md)
- Recipe mechanics: [the Goose recipe project pattern](../../goose/recipe-project-pattern/en.md)
- Server contract: [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md)
