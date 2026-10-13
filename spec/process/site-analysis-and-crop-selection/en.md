# Site Analysis and Crop Selection

Status: draft
Portfolio-Scope: local

## Context

Choosing what to grow comes before every care question this repository answers, and it is the choice most likely to be made from a plausible-sounding default. A crop is "suitable" for a site only against facts about the site, and most of the facts a grower reaches for first — how much light the bed gets, how much room there is, whether water is on hand — are the ones the Kamerplanter catalog does not hold. A process that fills those from general knowledge produces a confident list of candidates that rests on nothing the garden told it.

This spec specifies two steps. Site analysis turns what is known about a site into a profile that says, parameter by parameter, what is known, what is unknown, and where each value came from. Crop selection judges candidate species and cultivars against that profile and against the grower's goals, and returns for each candidate a verdict with its reasons and the constraints it failed. Both state unknown as unknown. A parameter nobody supplied is never met and never failed: it leaves the constraint it feeds undetermined.

Everything about the tool surface below is quoted from [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) and from [the species baseline process](../species-baseline-verification/en.md), whose measurements were taken against the reference instance on 2026-08-07. **Nothing here was re-measured when this spec was written**: the `kamerplanter` MCP server was unreachable in the session that drafted it (`INVALID_CONFIG`). A tool name or a field name is quoted from those specs; whether it still exists, and what a response carries beyond what they record, is unestablished until a `tools/list` and a read-only call against a reachable instance say so.

Boundaries: [the garden decision policy](../garden-decision-policy/en.md) owns how evidence is ranked, which rules a recommendation may not break and what it must expose; this spec applies them and does not restate them. The same spec's garden context owns the field names for what a garden holds, and `plant-context-collect` owns the context of one plant. Crop-rotation planning is a separate piece of work tracked as nolte/kamerplanter-goose#47, and the planting plan that consumes this spec's output is tracked as nolte/kamerplanter-goose#42; neither is specified here. The audit that decides which artifact owns what is tracked as nolte/kamerplanter-goose#39 and nothing here pre-empts it. [The recipe project pattern](../../goose/recipe-project-pattern/en.md) owns recipe mechanics and [the server spec](../../mcp/kamerplanter-mcp-server/en.md) owns transport, authentication and tenancy.

Readers: authors of garden skills and recipes in this repository, the author of the planting plan that consumes the candidate list, and anyone reviewing a crop recommendation before acting on it.

## Goals

- A site profile states, for every parameter, whether it is known or unknown, its value, and its source
- A parameter that is unknown stays unknown: it is never counted as met and never as failed
- Every candidate carries a verdict, the reasons for it, and the hard constraints it failed, each with its source and evidence level
- Hard constraints and preferences are kept apart, so a preference can never reject a crop and a failed hard constraint can never be traded off
- Cultivar data is used when present and species data otherwise, and the record says which
- The result can be consumed by the planting plan without re-deriving anything

## Non-Goals

- Planning when and where to plant, bed layouts, succession or crop rotation — nolte/kamerplanter-goose#42 and #47
- Judging a single plant's health, nutrition or pests — those are the processes that own them
- Writing any record, creating a site, or assigning a plan
- Supplying site facts the catalog does not hold. Where there is no source, the caller supplies the value or it stays unknown
- Inferring light, area or water from a site's name or type
- Replacing a grower's judgement about their own site

## Requirements

### A. The site profile

The profile has seven parameters. Each is reported `known` or `unknown`; a `known` parameter carries its value, its source (a tool, or `caller`), its retrieval time and its evidence level per [the garden decision policy](../garden-decision-policy/en.md).

| Parameter | Source in the measured catalog | Not established |
|-----------|--------------------------------|-----------------|
| Light and exposure | **No source measured.** A search of the server spec for light, sun, shade and exposure finds no field | Everything; the caller may supply it |
| Available area and container volume | **No source measured.** No area or volume field is named | Everything; the caller may supply it |
| Soil and substrate | `list_substrates`, with `ph_base`, `ec_base_ms`, `buffer_capacity` and `cec_meq_per_100g` per [the nutrient process](../nutrient-imbalance-detection/en.md); a plant's `substrate_key` from `list_plants` | Which substrate a bed or container holds: only a plant carries the key |
| Climate and local season | `get_sowing_calendar` with a `query` returned frost dates, per [the species baseline process](../species-baseline-verification/en.md); `list_hardiness_zones` lists zones | Which zone the garden is in: no field says so. The response fields of both tools beyond the above are not recorded |
| Water availability | **No source measured.** No irrigation or water field is named | Everything; the caller may supply it |
| Environmental constraints | **No source measured** as a field; supplied by the caller as free text | Everything |
| Existing observations and measurements | The garden context's fields for current measurements and historical observations, collected per plant | Not collected at garden level |

- **MUST** report each of the seven parameters in every profile, in this order, as `known` or `unknown`, and **MUST NOT** omit a parameter that is unknown
- **MUST** accept light and exposure, area or container volume, water availability and environmental constraints from the caller, and **MUST** mark their source `caller` and not as a tool
- **MUST NOT** derive light, area, volume or water availability from a site's name, a location's name, or the type of a site
- **MUST** report the garden's hardiness zone as unknown unless the caller supplies it, since no tool is named that says which zone the garden is in
- **MUST** call `get_sowing_calendar` only with a `query` that narrows it, because the server refuses an unnarrowed call, and **MUST** report a refusal or an empty result as the reason a climate value is unknown
- **SHOULD** point to the garden context for existing observations and measurements, and **MUST NOT** restate them

### B. The candidate pool

- **MUST** take the pool from the caller when the caller names species or cultivars
- **MAY**, when the caller names none, read one bounded page of `list_species`, which was measured returning 210 species on 2026-08-07 and whose parameters are not recorded, and **MUST** then report the pool as a sample with its size and say that the rest was not considered
- **MUST NOT** report a pool read this way as the catalog or as the full set of options

### C. Hard constraints and preferences

Constraints are of two classes, and a candidate is judged against each class separately.

| Constraint | Class | Fields | What it does not cover |
|------------|-------|--------|------------------------|
| Frost sensitivity against the garden's frost dates | Hard, where both are known | `frost_sensitivity` on the species; frost dates from `get_sowing_calendar` | The value set of `frost_sensitivity` is not recorded, so the constraint is formed only where a value reads unambiguously; otherwise it is undetermined |
| Hardiness zone against the garden's zone | Hard, where both are known | `hardiness_zones[]` on the species; the zone supplied by the caller | The garden's zone has no catalog source |
| Sowing and harvest timing against the grower's harvest window | Preference | `direct_sow_months[]`, `harvest_months[]`, `bloom_months[]`, `sowing_indoor_weeks_before_last_frost`, and the right entry of `growing_periods[]` | The top-level months are the union across periods, so a period must be chosen first |
| Days to maturity against the frost-free span | Preference | the cultivar's `days_to_maturity`; frost dates | What `days_to_maturity` counts from, sowing or transplant, is not recorded |
| Companion fit | Preference | `compatible_companions[]` with its `score` | The field lists compatible companions: its absence for a pair is not an incompatibility |
| The grower's goals | Preference | caller input | — |
| Light, shade, waterlogging and soil pH | **No constraint can be formed** | `shade_tolerance`, `waterlogging_tolerance` and `soil_ph_preference` were measured absent on both species probed on 2026-08-07 | Whether other species carry them is not established; two of 210 were probed |

- **MUST** keep hard constraints and preferences as two separate lists in every candidate record
- **MUST** reject a candidate on a failed hard constraint, **MUST** list that constraint with its source and evidence level, and **MUST NOT** weigh it against a preference
- **MUST NOT** reject a candidate on a preference; a preference ranks and is reported met, unmet or unknown
- **MUST NOT** form a hard constraint from a field that was not observed present, and **MUST** report a constraint whose species or site side is missing as undetermined
- **MUST NOT** treat the absence of a companion entry, or of any list, as evidence of incompatibility or compatibility
- **MUST** select the applicable entry of `growing_periods[]` before comparing timing, and **MUST** say which entry was used

### D. Suitability and the verdict

- **MUST** give each constraint one of `met`, `failed` or `undetermined`; an unknown site parameter or an absent species field makes the constraint `undetermined`, never `met` and never `failed`
- **MUST** give each candidate one verdict: `rejected` when at least one hard constraint failed, `eligible` when every hard constraint that could be formed is met and none is undetermined, and `undetermined` otherwise
- **MUST NOT** return `eligible` for a candidate with an undetermined hard constraint
- **MUST** return the reasons for the verdict in words a grower can check, each tied to a field and its value

### E. The candidate record

- **MUST** return, per candidate: the species key, the cultivar key or none, the verdict, the reasons, the failed hard constraints with source and evidence level, the undetermined constraints with what is missing, and each preference as met, unmet or unknown with its source
- **MUST** use the cultivar's value when the cultivar carries the attribute and the species value otherwise, and **MUST** record, per attribute used, which of the two it was
- **MUST** return a confidence derived from the highest evidence level that supports the verdict, an uncertainty statement and a missing-data list, per [the garden decision policy](../garden-decision-policy/en.md)
- **MUST NOT** state a confidence for a verdict that rests on a caller-supplied site fact without saying so

### F. The output for the planting plan

The result has three blocks: the site profile (section A, seven parameters), the pool (its source, `caller` or `sample`, and its size), and the candidate records (section E). The planting plan reads, per candidate, `species_key`, `cultivar_key`, `verdict`, `failed_hard_constraints`, the preferences, the attribute origins and the confidence.

- **MUST** return the three blocks in this order and with these names, so that a consumer does not re-derive them
- **MUST NOT** return a field the skill did not read, and **MUST** list an unread field as absent with its reason

## Acceptance Criteria

- [ ] A site profile lists all seven parameters; each is known or unknown, with value, source and retrieval time when known
- [ ] Light and exposure, area or volume, water availability and environmental constraints are known only when the caller supplied them, and are marked `caller`
- [ ] The garden's hardiness zone is unknown unless the caller supplied it
- [ ] No candidate is rejected on a preference, and no candidate with an undetermined hard constraint is eligible
- [ ] Every rejected candidate lists the failed hard constraint with its source and evidence level
- [ ] Each candidate record names, per attribute used, whether the cultivar or the species supplied it
- [ ] A pool read from `list_species` is reported as a sample with its size
- [ ] No hard constraint is formed from light, shade, waterlogging or soil pH
- [ ] The three output blocks appear in order with the stated names
- [ ] Every claim about the tool surface cites a spec in this repository; a claim not re-measured says so
- [ ] The German and the English file have the same headings in the same order, the same number of requirement bullets and the same number of acceptance checkboxes

## Source

- [The Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) — the tool catalog, the refusal of an unnarrowed `get_sowing_calendar`, and tenancy
- [The species baseline process](../species-baseline-verification/en.md) — the species fields observed present and absent, `list_species` (210 species), and `get_sowing_calendar` with `query` returning frost dates, all measured against the reference instance on 2026-08-07
- [The nutrient imbalance process](../nutrient-imbalance-detection/en.md) — the substrate fields
- [The garden decision policy](../garden-decision-policy/en.md) — evidence levels, the recommendation output and the garden context
- [The recipe project pattern](../../goose/recipe-project-pattern/en.md)
- Issue nolte/kamerplanter-goose#41 — the scope lists and the five criteria are taken from its body; nolte/kamerplanter-goose#42, #47 and #39 — the consumer, the rotation work and the audit

## Open Questions

- **What each `frost_sensitivity` value means.** The field is recorded as present; its value set is not. A hard constraint built on it cannot be stated more precisely than the reader can interpret the value. Open because nobody has listed the values, and settling it needs a read of several species on a reachable instance.
- **Which zone the garden is in.** `list_hardiness_zones` lists zones and no recorded field says which one belongs to the garden. Until a tool or a field says so, the zone comes from the caller.
- **Whether other species carry light, shade, waterlogging or soil pH fields.** Two species were probed on 2026-08-07 and none carried them. Open because 208 of 210 were not read; if some carry them, constraints become formable for those species and the table in section C changes.
- **What `days_to_maturity` counts from.** Sowing and transplant give different spans against the frost dates. Open because no spec records the start point.
- **The response fields of `list_hardiness_zones` and `get_sowing_calendar`.** Only the existence of frost dates in the sowing calendar's response is recorded. The exact fields are unmeasured because the server was unreachable when this spec was written.
- **The parameters of `list_species`.** Whether it can be narrowed, paged or filtered is not recorded, which is why the pool read is one bounded page and a sample.
- **How rotation constraints will be fed once nolte/kamerplanter-goose#47 exists.** Until then rotation is unknown and `compatible_companions` is read only as a preference.
- **Where the audit, nolte/kamerplanter-goose#39, places site analysis relative to the garden context.** Both describe what a garden holds; this spec adds interpretation and the garden context only collects. Whether they stay two artifacts is the audit's decision.
