# Species Baseline Verification

Status: draft
Portfolio-Scope: local

## Context

Every judgement this repository makes about a plant is measured against a baseline: what is normal for this species, in this phase, at this time of year. Collecting that baseline is a solved problem — the server returns it, and the `plant-context-collect` skill normalises it. **Whether the baseline is correct is not checked anywhere**, and a wrong baseline does not fail loudly. It produces a confident, well-reasoned, wrong answer downstream: a light-germinating seed buried a centimetre deep because `sowing_depth_cm` said so, a harvest window judged overdue against months that belong to a different growing period, a frost warning that never fires because `frost_sensitivity` reads `hardy` on a tropical foliage plant.

The baseline is also the place where absence is most easily mistaken for a fact. Measured, `get_species_info` returns **only the populated fields**, and the set differs per species: `Allium porrum` came back with 23 fields including a complete `seed_profile`; `Spathiphyllum wallisii` with 18 and no `seed_profile` at all. Neither carried `toxicity`, though the tool's own description advertises it. A consumer that reads a missing key as "does not apply" will tell someone a peace lily is safe around cats.

This spec covers two questions that share one data source and one discipline:

- **Is the recorded baseline plausible** for this species — germination parameters, sowing depth against light requirement, hardiness against habitat, harvest against growth habit?
- **What is the plant's lifecycle** — annual, biennial or perennial; the sowing, bloom and harvest windows; dormancy and frost sensitivity — where the record is silent or contradicts itself?

They are one spec because the lifecycle windows *are* baseline fields. Separating them would put `bloom_months` in one document as a value to check and in another as a value to establish.

The discipline they share is the reason this is worth specifying at all. Botanical facts are exactly the kind of thing a language model produces fluently and wrongly. **No claim here may rest on recall.** The rule inherited from the source procedure is three independent sources before a value counts as established, a ranked source hierarchy, and — the part that does the work — a confidence level that decides whether anything happens at all. Below *established*, the recorded value stands and the doubt is reported. That refusal is the deliverable.

Everything marked *measured* was read from the reference instance on 2026-08-07.

Readers: authors of recipes that consume a species baseline, and anyone reviewing a correction one proposes before it reaches `nolte/kamerplanter`.

## Goals

- A baseline field is judged against the species' actual biology, not merely against the schema that allowed it
- A missing field is reported as unpopulated, never read as a negative fact
- Lifecycle windows are resolved against the instance's own frost dates rather than against a generic calendar
- Every botanical claim carries a confidence level and its sources, and only the highest level licenses a proposed correction
- Cross-field contradictions are surfaced, because a field can be individually plausible and jointly impossible
- The difference between the botanical cycle and the cultivated one is stated where they diverge, since most edible biennials are grown as annuals

## Non-Goals

- Writing to the species catalog, the plant, or any Kamerplanter record; corrections are proposals directed at `nolte/kamerplanter`
- Authoring species master data or plant profiles — that pipeline lives in `nolte/kamerplanter` and operates on files this repository does not hold
- Judging an individual plant's health, nutrition, or pest pressure; those are [image analysis](../plant-health-image-analysis/en.md), [nutrient imbalance detection](../nutrient-imbalance-detection/en.md), and [pest pressure assessment](../pest-pressure-assessment/en.md)
- Replacing a seed-testing laboratory; this reasons over published horticultural knowledge and the record
- Recipe mechanics and MCP transport, auth, and tenancy — specified in [the recipe project pattern](../../goose/recipe-project-pattern/en.md) and [the server spec](../../mcp/kamerplanter-mcp-server/en.md)

## Measured baseline

### What `get_species_info` carries

Measured on two species chosen to differ — a field crop and a houseplant:

| Group | Fields observed |
|-------|-----------------|
| Identity | `species_key`, `scientific_name`, `common_names[]`, `genus`, `family_key`, `native_habitat` |
| Form | `growth_habit`, `root_type`, `plant_category`, `traits[]` |
| Timing | `direct_sow_months[]`, `harvest_months[]`, `bloom_months[]`, `sowing_indoor_weeks_before_last_frost`, `growing_periods[]` |
| Climate | `hardiness_zones[]`, `frost_sensitivity`, `base_temp_gdd` |
| Culture | `nutrient_demand_level`, `green_manure_suitable`, `allows_harvest` |
| Seed | `seed_profile` — `germination_temp_min_c`, `germination_temp_max_c`, `sowing_depth_cm`, `days_to_germination`, `seed_viability_years`, `light_germination`, `pretreatment[]`, `thousand_seed_weight_g`, `sowing_density_per_m2` |
| Related | `compatible_companions[]` (with `score`), `cultivars[]` (with `traits[]`, `days_to_maturity`, `seed_type`) |

`growing_periods[]` is the field a naive reader misses. Measured, `Allium porrum` carries two — a summer and a winter leek — **each with its own `direct_sow_months` and `harvest_months`**. The top-level months are the union across periods, so judging an observation against them without first selecting the period produces a window that is too wide to be wrong and too wide to be useful.

### What it does not carry

Measured absent on both species probed, despite being dimensions of the source procedure: `photosynthesis_type`, `light_compensation_point_ppfd_min`/`max`, `shade_tolerance`, `salt_tolerance_class` and its Maas-Hoffman threshold and slope, `waterlogging_tolerance`, `soil_ph_preference`, `effective_root_depth_cm`, `climacteric`, `harvested_part`, `harvest_pattern`, `propagation_configs`, `allergen_info`, and any explicit `cycle_type`.

**`toxicity` is the one to watch.** The tool description names it; neither probe returned it, including on a species with known calcium-oxalate toxicity. Whether the field is unpopulated or unexposed is unresolved, and until it is, no run may report a plant as non-toxic on the strength of its absence.

The absence of `cycle_type` means the annual/biennial/perennial question is not answered by the species record directly. It is inferred — from `growing_periods[]`, `bloom_months` against `harvest_months`, `hardiness_zones`, and the phase definitions the plant is actually assigned — and every such inference is a claim, not a lookup.

### The lifecycle sources

Three tools carry what the species record does not:

| Tool | Supplies | Measured |
|------|----------|----------|
| `get_sowing_calendar` | Per-species sowing, planting-out and harvest bars for one year, plus `frost.last_frost_date`, `frost.first_frost_date`, `frost.eisheilige_date` | `2026-05-01`, `null`, `2026-05-15` for the reference instance. **Refuses an unnarrowed call** — without `query` it answers `validation.error` naming the 148 species covered and a `limit` ceiling of 25 |
| `list_overwintering_profiles` | Per plant: `hardiness_zone_min`, `hardiness_rating`, `winter_action` + `winter_action_month`, `spring_action` + `spring_action_month`, `auto_generated`, `user_overridden`, `derived_path` | 5 profiles; the ones seen were `auto_generated: true`, `user_overridden: false` |
| `list_phase_definitions` | The lifecycle engine's vocabulary — `name`, `display_name`, `typical_duration_days`, `stress_tolerance`, `watering_interval_days`, `tags[]` | 29 definitions, including `dormancy` (120 days) and `active_growth` (180 days) |

`frost.eisheilige_date` is the instance's own answer to the mid-May frost question, and it is what a sowing recommendation is checked against — not a remembered rule of thumb. `first_frost_date` was `null` at measurement, so the autumn half of the calendar has no anchor and any claim about lifting tubers before first frost is unanchored.

An overwintering profile with `auto_generated: true` and `user_overridden: false` is a derivation, not an observation. It is evidence about what the system inferred, and it inherits any error in the species baseline it was derived from — which makes it a corroborating source, never an independent one.

## The source hierarchy and the three-source rule

**No botanical value may be asserted from recall.** Every claim about germination, timing, dormancy, hardiness or toxicity is either read from the record — and labelled as such — or researched and cited.

A correction requires **three independent sources in agreement**. Independent means not quoting one another; three pages repeating one nursery's catalogue text are one source.

| Rank | Source type | Reliability |
|------|-------------|-------------|
| 1 | University horticulture institutes, agricultural chambers and extension services, RHS, ISTA | Highest |
| 2 | Horticultural reference works and botanical encyclopaedias — Missouri Botanical Garden, PFAF, POWO/WCVP for taxonomy, FAO for salt tolerance | High |
| 3 | Seed houses and nurseries, for sowing and harvest timing specifically | High for timing |
| 4 | Gardening portals with an editorial desk | Medium |
| 5 | Forums and community posts | Low; supporting only |

**Never sufficient alone:** Wikipedia, AI-generated text, unattributed blog posts, or any page whose only content is a citation of another source.

Search in at least two phrasings — scientific and common name, and where the plant is grown in Central Europe, German and English — because a single phrasing selects a single publishing tradition.

## Confidence, and what each level licenses

| Level | Meaning | Licenses |
|-------|---------|----------|
| **Established** | Three or more independent sources agree | A proposed correction, with sources attached |
| **Probable** | Two sources agree, or three with minor divergence | A finding. The recorded value stands |
| **Uncertain** | Sources conflict, or only one was found | A finding naming the conflict. The recorded value stands |
| **Unverifiable** | No usable source | A gap, named. The recorded value stands |

The asymmetry is deliberate and load-bearing: only the top level moves anything. Everything below it is reported. **A run that finds twelve doubtful values and proposes no correction has done its job**, and a run that "improves" a value at *probable* has not.

## The plausibility checks

Run against what the record actually carries. A check whose field is absent is reported as not run, never as passed.

### Seed and germination

- `germination_temp_min_c` < `germination_temp_max_c`, and the range fits the species rather than a default. Cold germinators sit near 2–10 °C, warm ones near 20–30 °C; a catalogue where every species reads 20–25 °C has a default, not data.
- `sowing_depth_cm` against `light_germination`. **A light germinator is pressed onto the surface, not buried** — `light_germination: light` with a `sowing_depth_cm` of 1 is a contradiction the schema permits and the seed does not survive. Measured, `Allium porrum` reads `dark` at 1.0 cm, which is consistent.
- `light_germination` against seed size: fine-seeded species tend to need light, large-seeded ones darkness.
- `pretreatment[]` against origin. Cold stratification belongs to temperate woody and cold-germinating species; scarification to hard-coated seeds; soaking to slow imbibers. **Stratification on a tropical species is a finding**, not a nicety.
- `seed_viability_years` and `days_to_germination` consistent with each other and with the temperature range.

### Climate and habitat

- `frost_sensitivity` against `hardiness_zones` and `native_habitat`. Measured, `Spathiphyllum wallisii` reads `sensitive` with zones `10b`–`11a` and a Central American habitat — internally consistent. `Allium porrum` reads `hardy` across ten zones. A `hardy` rating on a species whose zones start at 10 is the contradiction to look for.
- `base_temp_gdd` against the same: measured 5.0 for leek, 15.0 for the peace lily. A tropical species with a temperate base temperature will accumulate growth degree days that never happened.

### Timing

- Bloom before harvest for a fruiting species; the two overlapping is normal for a leaf or cut-and-come-again crop and suspicious for a fruit.
- Each entry in `growing_periods[]` internally coherent, and the top-level months equal to their union.
- `direct_sow_months` and `sowing_indoor_weeks_before_last_frost` consistent with `frost.last_frost_date` and `frost.eisheilige_date` from the instance's own calendar.
- `allows_harvest` against `growth_habit` and the presence of `harvest_months`.

### Cross-field

A field may be plausible alone and impossible in company. The pairs worth checking explicitly: seed profile present but no sowing months; harvest months present with `allows_harvest: false`; cultivar `days_to_maturity` incompatible with the species' own sowing-to-harvest span; `compatible_companions` scored high for a species that cannot share the same site conditions.

`compatible_companions` concerns planting decisions. It is not evidence about the plant's own physiology and must not be carried into one.

## Resolving the lifecycle

Where the cycle is not recorded, it is established in this order, and the order matters because each step can settle the question without the next:

1. **The instance's own assignment.** The plant's `current_phase` against `list_phase_definitions` — a plant assigned `dormancy` is being treated as perennial by the system, whatever the species record implies.
2. **`growing_periods[]` and the month fields.** Sowing and harvest inside one calendar year with no dormancy indicates an annual; a bloom window in the year after sowing indicates a biennial; recurring bloom and harvest with a dormancy phase indicates a perennial.
3. **`list_overwintering_profiles`** for the plant, remembering that an `auto_generated` profile corroborates and does not establish.
4. **Researched, under the three-source rule**, where the record is silent or self-contradictory.

**State the botanical cycle and the cultivated one separately whenever they differ.** Onion and leek are botanically biennial and grown as annual vegetables; recording only one of the two produces a wrong answer to half the questions asked of it. This is the single most common divergence in an edible catalogue and the reason the field cannot simply be copied from a botanical reference.

## Output and boundaries

The result reports, per field: what the record holds, whether the check ran, the finding if any, the confidence, and the sources. Fields whose check could not run because the field is absent are listed as unpopulated, separately from fields that were checked and passed — collapsing the two is what turns a gap into a false assurance.

Severity ranks by consequence: a value that would cause a failed sowing, a dead plant, or a safety claim about toxicity ranks above one that is merely misleading, which ranks above a refinement.

Proposed corrections are directed at `nolte/kamerplanter`, where the species data lives. This process writes nothing.

## Requirements

- **MUST NOT** assert a botanical value from recall; every claim is either read from the record and labelled, or researched and cited
- **MUST** require three independent, non-quoting sources before proposing a correction, and **MUST** leave the recorded value in place at any lower confidence
- **MUST** attach the confidence level and the sources to every finding
- **MUST** report a field absent from `get_species_info` as unpopulated, and **MUST NOT** treat absence as a negative fact — in particular **MUST NOT** report a plant as non-toxic because `toxicity` is missing
- **MUST** select the applicable entry from `growing_periods[]` before judging any observation against `direct_sow_months` or `harvest_months`, when more than one period exists
- **MUST** check `sowing_depth_cm` against `light_germination` and report the light-germinator-buried contradiction as a high-severity finding
- **MUST** read frost dates from `get_sowing_calendar` for the instance rather than assuming a regional rule, and **MUST** state when `first_frost_date` is `null` rather than substituting one
- **MUST** pass `query` to `get_sowing_calendar`, since measured an unnarrowed call is refused with `validation.error`
- **MUST** state the botanical and the cultivated cycle separately where they diverge
- **MUST NOT** call any state-changing tool; corrections are proposals directed at `nolte/kamerplanter`
- **SHOULD** list checks that could not run because their field is absent, separately from checks that ran and passed
- **SHOULD** treat an `auto_generated: true` overwintering profile as corroboration only, since it is derived from the same baseline under examination
- **SHOULD** search in at least two phrasings, scientific and common, and in both German and English for species grown in Central Europe
- **SHOULD** rank findings by consequence, placing a failed sowing or a toxicity claim above a misleading value
- **SHOULD NOT** carry `compatible_companions` into a physiological judgement
- **MAY** read `get_cultivar` when a cultivar's `days_to_maturity` or `traits` narrows the species expectation
- **MAY** consult `search_glossary` for the project's own definition of a term before introducing an external one

## Acceptance Criteria

- [ ] Every finding carries a confidence level and its sources
- [ ] No correction is proposed below the *established* level
- [ ] Absent fields are reported as unpopulated and listed separately from passed checks
- [ ] No run reports a plant as non-toxic on the basis of a missing `toxicity` field
- [ ] A species with multiple `growing_periods[]` is judged against the applicable period, not the union
- [ ] Every `get_sowing_calendar` call passes `query`
- [ ] Frost-relative timing claims cite the instance's own `last_frost_date` or `eisheilige_date`
- [ ] A `null` `first_frost_date` is stated as unanchored rather than substituted
- [ ] The botanical and cultivated cycle are both stated wherever they differ
- [ ] No recipe under this spec calls a state-changing tool
- [ ] Cross-field contradictions are reported even when each field is individually plausible

## Open Questions

- Whether `toxicity` is unpopulated for the probed species or not exposed by the tool at all. Until this is settled, an entire class of safety question is unanswerable from the record, and that is a worse state than a documented gap.
- Whether the environmental-physiology fields — photosynthesis type, light compensation point, salt tolerance, soil pH preference — exist upstream. The source procedure checks all of them; none was observable here, so those dimensions are currently unreachable rather than passing.
- Whether `cycle_type` exists under another name, or whether the inference chain in this spec is the only route. If it exists, most of the lifecycle resolution collapses into a lookup.
- Why `first_frost_date` is `null` while `last_frost_date` and `eisheilige_date` are populated, and whether it becomes available later in the year. Autumn timing depends entirely on it.
- Whether `derived_path` on an overwintering profile identifies which rule produced it, which would make the derivation auditable rather than merely flagged.
- How a proposed correction should reach `nolte/kamerplanter` — an issue, a pull request against the seed data, or a report a human carries over. The `github` MCP extension is declared here, so the mechanism exists; the convention does not.

## Source

- Measured against the reference Kamerplanter instance on 2026-08-07 through `POST /api/v1/mcp`, read-only: `list_species` (210), `get_species_info` (`Allium porrum` 23 fields with full `seed_profile` and two `growing_periods`; `Spathiphyllum wallisii` 18 fields, no `seed_profile`, neither with `toxicity`), `get_sowing_calendar` (refused unnarrowed; with `query` returned frost dates and per-species bars), `list_overwintering_profiles` (5), `list_phase_definitions` (29), `list_plants`. No write tool was called.
- Domain procedure inherited from `nolte/kamerplanter`: `.claude/skills/check-seed-data/SKILL.md` for the seed, germination and cross-field dimensions, and `.claude/skills/plant-lifecycle/SKILL.md` for the three-source rule, the source hierarchy, the confidence levels, and the botanical-versus-cultivated cycle distinction. Those artefacts judge that repository's own YAML seed data; this spec governs the same judgement applied to what the MCP server returns.
- Companion processes: [pest pressure assessment](../pest-pressure-assessment/en.md), [nutrient imbalance detection](../nutrient-imbalance-detection/en.md), [plant health image analysis](../plant-health-image-analysis/en.md)
- Recipe mechanics: [the Goose recipe project pattern](../../goose/recipe-project-pattern/en.md)
- Server contract: [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md)
