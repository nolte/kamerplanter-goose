# Bed Layout and Succession Planning

Status: draft
Portfolio-Scope: local

## Context

A planting plan says when each crop goes in and comes out; a rotation plan says which plant family may stand in which bed in a season. Neither says how much of a bed a crop takes, whether the crops given to one bed fit into it month by month, which crops stand next to each other, or which crop follows another in the same bed. That is bed layout and succession. It is also where a process working from general knowledge is most tempted to fill in numbers: a remembered spacing, a remembered list of bad neighbours, a remembered "sow every two weeks". A layout built on those reads as a gardener's plan and rests on nothing the garden told it.

The issue that asked for this, nolte/kamerplanter-goose#46, assumed that spacing, light, access, irrigation and incompatible companions are catalog data. The measured surface holds much less. Beds and containers have no source ([the garden decision policy](../garden-decision-policy/en.md)); light and exposure, area and volume, and water have none ([site analysis](../site-analysis-and-crop-selection/en.md) §A); no field for access occurs anywhere in this repository's specs. `get_species_info` carries `compatible_companions[]` with a `score`, whose value range and direction are not recorded, and no incompatible or antagonist field; a pair that is not listed is unknown, never incompatible. `seed_profile.sowing_density_per_m2` exists, measured on one species, and whether it counts seeds or plants is not recorded. No in-row, between-row or plant-spacing field is named. So this spec takes beds, capacity, spacing, quantities, bed attributes and incompatibilities from the caller, uses the catalog's companion list as a ranking input only, and reports everything else unknown.

This spec specifies three steps. Collecting companions and density reads, once per distinct species, the companion list with its scores and the seed density as context. Succession planning finds, in the planting runs of [the plant planning spec](../plant-planning-and-planting-calendar/en.md) and the slots of [the crop rotation plan](../crop-rotation-planning/en.md), the runs that can follow each other in one bed and the runs that can be sown in staggered sets. Bed layout allocates runs and successions to the caller's beds, validates capacity per bed and month, and explains every placement and every run left out. All three are read-only. A layout is a document; recording it is a separate step, and the measured catalog has no tool that could do it (section G).

Everything about the tool surface below is quoted from [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) and from [the species baseline process](../species-baseline-verification/en.md), whose measurements were taken against the reference instance on 2026-08-07 and 2026-08-16. **Nothing here was re-measured when this spec was written**: the `kamerplanter` MCP server was unreachable in the session that drafted it (`INVALID_CONFIG`). A tool or field name is quoted from those specs; whether it still exists, and what a response carries beyond what they record, is unestablished until a `tools/list` and a read-only call against a reachable instance say so.

Boundaries: [the garden decision policy](../garden-decision-policy/en.md) owns the weight a claim carries, the recommendation shape and the garden context; [the plant planning spec](../plant-planning-and-planting-calendar/en.md) owns the planting runs and their windows; [the crop rotation planning spec](../crop-rotation-planning/en.md) owns the family per bed and season and the rotation verdicts. This spec reads all three and restates none: it never recomputes a window and never re-derives a rotation. The `-apply` half of nolte/kamerplanter-goose#46 is split into nolte/kamerplanter-goose#74, blocked. The audit that decides which artifact owns what is nolte/kamerplanter-goose#39 and nothing here pre-empts it. [The recipe project pattern](../../goose/recipe-project-pattern/en.md) owns recipe mechanics and [the server spec](../../mcp/kamerplanter-mcp-server/en.md) owns transport, authentication and tenancy.

Readers: authors of garden skills and recipes in this repository, and anyone reviewing a layout or a succession before acting on it.

## Goals

- Every placement and every succession names the rule that produced it, the inputs it rests on, their sources and the evidence level
- A capacity that cannot be computed from caller inputs is reported `not validated` with the missing input, never estimated
- A companion pairing is a ranking input, stated as not a guarantee; an incompatibility exists only where the caller names it
- A rotation is consumed, never re-derived: a crop stands only where the rotation plan admits it
- The layout is a function of its input blocks, so two runs over the same blocks give the same plan facts
- Read-only planning and recording are separate, and a layout can be reviewed before anything is recorded

## Non-Goals

- Recording a layout, a bed, a bed assignment, a succession or a planting run. The measured catalog has no tool for it (section G)
- Geometry: rows, positions, coordinates or drawings. A layout allocates area or volume per bed, not positions inside it
- Light, access and irrigation as placement rules. No species field records a crop's need for them, so the caller's bed attributes are context, and an exclusion is the caller's rule mechanism
- Recomputing a planting window or a rotation verdict, or changing what [plant planning](../plant-planning-and-planting-calendar/en.md) or [crop rotation planning](../crop-rotation-planning/en.md) require
- A spacing, a density, an incompatibility, a stagger interval or a companion effect from general knowledge
- A layout across several seasons. One run plans one season

## Requirements

### A. Inputs

| Input | Source | Not established |
|-------|--------|-----------------|
| Planting runs | [Plant planning](../plant-planning-and-planting-calendar/en.md), its `PLANTING RUNS` and `NOT PLANNED` blocks | — |
| Rotation plan | [Crop rotation planning](../crop-rotation-planning/en.md), its `ROTATION PLAN` and `CONFLICTS` blocks, for the one season | — |
| Season | The caller: one year | — |
| Beds | The caller: entries `name`, `name:<n>m2` (a bed, by area) or `name:<n>l` (a container, by volume), separated by commas; and every other bed the rotation plan has a slot for in the season, with capacity `unknown` and source `rotation plan` | No source in the measured catalog |
| Bed attributes | The caller: entries `bed:light=<text>`, `bed:access=<text>` or `bed:irrigation=<text>`, separated by semicolons | No source; no species field records the need |
| Spacing | The caller: entries `species_key[:cultivar_key]=<n>/m2` (plants per m²) or `species_key[:cultivar_key]=<n>l` (litres per plant), separated by commas | No spacing field is named in the catalog |
| Quantities | The caller: entries `species_key[:cultivar_key]=<plants>`, separated by commas | No source |
| Stagger interval | The caller: `stagger_weeks`, a whole number | No source; no number is built in |
| Constraints | The caller: entries separated by semicolons, `avoid=species_key[:cultivar_key]+species_key[:cultivar_key]`, `exclude=bed:species_key[:cultivar_key]`, the rotation's `pin=`, or free text | — |
| Companions | `get_species_info`: `compatible_companions[]` with `score`, level 4 | The range and direction of `score`; the shape of an entry beyond the species it names |
| Seed density | `get_species_info`: `seed_profile.sowing_density_per_m2`, level 4 | Whether it counts seeds or plants, and whether a cultivar carries it |

- **MUST** split every list at its separator and each entry at its colons, equals signs and plus signs, and **MUST NOT** pass the joined text on as a name; a bed name is the text before the first colon of a `beds` entry
- **MUST** read a bed's capacity only from the forms `<n>m2`, `<n>m²` and `<n>l`, **MUST** report any other capacity text verbatim with capacity `unknown`, and **MUST** treat a bare name as a bed of unknown capacity
- **MUST** mark beds, bed attributes, spacing, quantities, the stagger interval, the season and the constraints as source `caller`, and **MUST** report each as not supplied when the caller left it empty
- **MUST** take a crop's spacing and quantity from its cultivar entry when one exists and from its species entry otherwise, and **MUST** say which
- **MUST** list every entry that cannot be parsed, and every free-text constraint, verbatim as `not evaluated`, and **MUST NOT** interpret free text as a rule
- **MUST** stop and name the missing block when the planting runs or the rotation plan are not supplied

### B. Companions and seed density

- **MUST** read `get_species_info` once per distinct species among the crops of the planting runs, with `include_cultivars` when a cultivar is named, and **MUST NOT** call any other tool for this step
- **MUST** record `compatible_companions[]` with each entry's species and `score` as recorded, the cultivar's list before the species list, with its origin, and **MUST** report an absent list as `absent — not populated`
- **MUST** report `sowing_density_per_m2` as context only, with its origin and the note that its unit semantics are not recorded, and **MUST NOT** use it as a capacity, a spacing or a plant count
- **MUST NOT** read a pair that is not listed as incompatible, **MUST NOT** infer an incompatibility from any field, and **MUST NOT** supply a spacing or a density

### C. Succession

A run's **occupancy** is the months from its first sowing month (`direct_sow`: the lowest month of the sowing window) or its transplant month (`indoor_then_transplant`: the month of the transplant start) to the highest month of its harvest window, within the season. An unknown bound makes the occupancy `unknown`. A harvest month lower than the start month, or a sowing or transplant month higher than the highest harvest month (direct sowing in months 4, 5 and 8 with harvest in 6 and 7; sowing in 11, 12, 1 and 2 with harvest in 5 and 6), means the run spans the season boundary, and its occupancy is `unknown — spans the season boundary`. A crop is **admissible** in a bed when one of two clauses holds, read in this order: first, a `pin=` names that bed, the season and the crop, whatever the slot's state, `occupied` included; otherwise, the slot is not pinned and the crop belongs to its selected family group. Apart from a pin, a slot that is `open` or `occupied` admits nothing.

- **MUST** propose a **sequential** succession only for two runs whose crops are both admissible in the same rotation slot, whose occupancies are both known, and where the earlier run's highest harvest month is lower than the later run's start month
- **MUST** name both run identifiers in every sequential succession, **MUST** copy each window it rests on with its rule, fields, source and level, and **MUST** carry plant planning's own `precedes` and `follows` notes over verbatim
- **MUST** propose a **staggered** succession only within a known direct sowing window, only for a run whose occupancy is known, only inside its occupancy months and only with the caller's `stagger_weeks`, listing the sowing dates as offsets of that many weeks from the first day of each contiguous block of the window's months in the season, and **MUST** report `staggering possible within <months> — interval not supplied` without it
- **MUST NOT** propose a succession from general knowledge, from months that cannot be compared, or across crops the rotation slot does not admit
- **MUST** list every run in no sequential succession under `NOT SUCCEEDED` with one reason, the first that applies: `method not chosen — set planting_method`, `outside rotation plan`, `occupancy unknown — <missing>`, `spans the season boundary`, `no other run in <slot>`, or `no run follows or precedes it in <slot>`

### D. Layout and capacity

A run's **need** is its quantity divided by the plants per m² for a bed, or its quantity multiplied by the litres per plant for a container, with the spacing unit matching the bed's unit. A bed's **capacity per month** is validated when the bed's capacity, the need of every run occupying it that month, and their occupancies are all known; it is then `within` or `over by <x>`, and `not validated — <missing input>` otherwise.

A run is **admissible** in a bed when its crop is admissible there (section C), no `exclude` names that bed and crop, no `avoid` pair joins it to a run in the bed whose occupancy overlaps it or is unknown, and its method is chosen. The planner places in two passes, each walking the runs in order of their occupancy start month, unknown last, then by run identifier as text. The first pass places the runs of a pinned crop in the pinned bed, the first by name when the crop is pinned in several. The layout's beds are the caller's `beds` entries plus every other bed the rotation plan has a slot for in the season, the latter with capacity `unknown`. The second pass places every other run in the first admissible bed by these keys, applied strictly in order: the bed holds a sequential predecessor of the run from the succession block; validated capacity fits, ahead of capacity not validated; the higher sum of numeric companion scores with the runs in the bed whose occupancy overlaps it; the bed name as text. A bed whose validated capacity would be exceeded is not a candidate for an unpinned run.

- **MUST** place a run only in a bed whose rotation slot admits its crop, and **MUST** report a run whose crop no slot admits as `not placed — outside rotation plan`
- **MUST** place a pinned crop's runs in the pinned bed even when capacity is exceeded, **MUST NOT** move a pin, and **MUST** list the overrun and any `avoid` or `exclude` the pin breaks under `CONFLICTS`; the method rule below takes precedence: a pinned crop whose method is not chosen is not placed and is listed under `CONFLICTS` as `pinned crop: method not chosen — set planting_method`, the pin unresolved, not moved
- **MUST** report a run that no bed can hold as `not placed — capacity` when capacity alone stopped it and as `not placed — no admissible bed` otherwise, naming per bed the check that stopped it
- **MUST** validate capacity per bed and per month of the season from the caller's capacity, spacing and quantities only, and **MUST** report `not validated` with the missing input when any of them is missing or their units do not match, and **MUST NOT** fill the gap from `sowing_density_per_m2` or from general knowledge
- **MUST** enforce `avoid` as a hard constraint: two avoided crops never occupy one bed in overlapping months, an unknown occupancy counting as overlapping
- **MUST** use the catalog's companion list as a ranking input only: a numeric `score` counts toward the sum, a non-numeric one counts 0 and is listed as `score not comparable`, an unlisted pair is `unknown`, and the plan **MUST** state verbatim that a companion pairing is a planning input from the catalog, not a guarantee of any outcome
- **MUST** rank a higher companion sum first and **MUST** state in every placement's rationale the fixed sentence "companion score assumed higher = more favourable; the record does not state its direction"
- **MUST** place neither run when plant planning offers the same species, cultivar and growing period under both methods, and **MUST** list both as `method not chosen — set planting_method`; runs of different growing periods are separate plantings
- **MUST** report the caller's bed attributes per bed and in each placement's rationale as context, and **MUST NOT** let them decide a placement
- **MUST** give every placement a rationale stating the ranking values, every bed not chosen with its reason, the rotation verdict copied with its level, the bed attributes, and the companion statement; and **MUST** give every run not placed exactly one reason

### E. The plans and their consumers

The succession plan has four blocks, in this order and under these names: `SUCCESSION HEADER` (the garden, the season, the stagger interval or `not supplied`, the blocks it was made from), `SUCCESSIONS`, `NOT SUCCEEDED` and `APPLY CONTRACT`. The layout has six: `LAYOUT HEADER` (the garden, the season, the beds with their capacity and source, the spacing, the quantities, the not-evaluated entries), `BED LAYOUT` (per bed: its capacity, its attributes, its placements with their need and rationale), `CAPACITY` (per bed and month), `CONFLICTS`, `NOT PLACED` and `APPLY CONTRACT`.

| Consumer | Reads |
|----------|-------|
| Bed layout | from the succession plan: each sequential succession's slot and its two run identifiers |
| A person reviewing a layout | per bed: the placements, the capacity per month, the conflicts; per run: where it stands or why it does not |
| The blocked `-apply` follow-up (nolte/kamerplanter-goose#74) | the `APPLY CONTRACT` block of an approved layout |

- **MUST** return the blocks in these orders with these names, and **MUST NOT** return a field that was not read, listing an unread field as absent with its reason
- **MUST** give every placement and every succession its rationale, confidence, uncertainty and missing data per [the garden decision policy](../garden-decision-policy/en.md), and **MUST** give it the level `caller` whenever any element of it comes from the caller, and the weakest level among its elements otherwise
- **MUST** copy the rotation plan's conflicts for the season into `CONFLICTS`, beside the layout's own

### F. Determinism

- **MUST** make each plan a function of the supplied input blocks and the policy, so that two runs over the same blocks give the same plan facts: the placements, the needs, the capacity per bed and month, the conflicts, the not-placed reasons, the successions and the evidence levels
- **MUST NOT** let the order of the input or the current date decide a plan fact; retrieval times are reported beside the facts and are not compared
- **MUST** state that byte-identical prose outside the plan facts is not claimed, and that the property is checked on a fixed fixture of input blocks and not on a live garden

### G. Separation and the apply contract

- **MUST** keep layout and succession planning read-only: the skills and recipes of this spec call no state-changing tool
- **MUST** include in every plan an `APPLY CONTRACT` block that states, per placement or succession, what a later `-apply` recipe would have to record (the bed, its capacity, the run, its need, the season, its predecessors), and **MUST** state that the measured catalog has no tool that creates a bed, records a bed assignment or a layout, or creates a planting run: the write tools it records are `add_plant_diary_entry`, `confirm_care_task`, `archive_plant`, `set_plant_location`, `claim_diary_analysis`, `submit_diary_analysis`, `transition_plant_phase`, `assign_species_phase_sequence`, `assign_nutrient_plan`, `record_feeding_event`, `create_inspection`, `clone_nutrient_plan`, `set_nutrient_plan_phase_targets`, `create_substrate_mix` and `set_plant_substrate`, and the setup tool `create_site`, and none of them does; `set_plant_location` moves a plant that exists, a layout places crops that are not plants yet, and `create_site` creates a site root, not a bed with an area
- **MUST** name nolte/kamerplanter-goose#74 as the place where `bed-layout-plan-apply` is tracked, and **MUST NOT** ship a recipe with the `-apply` suffix that does not write what its description says
- **MUST** leave recording a layout to a separate recipe that takes an approved layout, after a person has reviewed it

## Acceptance Criteria

- [ ] Every placement and every succession names its rule, its inputs with their sources and levels, and the missing data; one resting on a caller input says so
- [ ] A capacity without the caller's capacity, spacing or quantity is `not validated` with the missing input, and no spacing or density comes from the catalog's seed density or from recall
- [ ] A crop stands only in a bed whose rotation slot admits it, and a crop outside the rotation plan is listed with that reason
- [ ] A pin is never moved, and a pin over capacity or against a constraint is listed under `CONFLICTS`
- [ ] Two crops the caller marks `avoid` never share a bed in overlapping months, and an unlisted companion pair is `unknown`, never incompatible
- [ ] The plan states that a companion pairing is an input, not a guarantee
- [ ] A crop offered under two methods for one growing period is not placed until a method is set
- [ ] A sequential succession names both run identifiers and the windows it rests on; a staggered succession exists only with the caller's interval
- [ ] Bed attributes are reported and decide no placement
- [ ] Every run not placed or not succeeded has one reason
- [ ] The plans have their blocks in order, and the apply contract states that the measured catalog has no tool that records a layout
- [ ] Two runs over the same input blocks give the same plan facts on a fixed fixture, and the plan says what is not claimed
- [ ] The layout and succession skills and recipes call no state-changing tool
- [ ] Every claim about the tool surface cites a spec in this repository; a claim not re-measured says so
- [ ] The German and the English file have the same headings in the same order, the same number of requirement bullets and the same number of acceptance checkboxes

## Source

- [The Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) — the write and setup tools, `set_plant_location` moving an existing plant, `create_site` creating a site root, and `sowing_density_per_m2` measured on `Allium porrum`
- [The species baseline process](../species-baseline-verification/en.md) — `compatible_companions[]` with `score` and `seed_profile.sowing_density_per_m2` observed present on 2026-08-07, a missing key meaning not populated
- [The site analysis and crop selection spec](../site-analysis-and-crop-selection/en.md) — light, area, volume and water with no source, and an unlisted companion pair as unknown, never incompatible
- [The garden decision policy](../garden-decision-policy/en.md) — evidence levels, the recommendation output, and beds and containers as having no source
- [The plant planning spec](../plant-planning-and-planting-calendar/en.md) — the run identifier, the windows and the succession notes this spec reads
- [The crop rotation planning spec](../crop-rotation-planning/en.md) — the rotation slots, the crop keys and the conflicts this spec reads
- [The recipe project pattern](../../goose/recipe-project-pattern/en.md)
- Issue nolte/kamerplanter-goose#46 — the layout factors and the five criteria are taken from its body; nolte/kamerplanter-goose#74 — the blocked apply half; nolte/kamerplanter-goose#59 and #68 — the precedents for a blocked apply half; nolte/kamerplanter-goose#39 — the audit

## Open Questions

- **What `score` means.** The companion list carries a `score` whose range and direction are not recorded. The layout ranks a higher numeric sum first, which assumes a higher score is a better pairing; the rationale says so. `get_species_info` on ten or more vegetable species, with the score compared to a documented source, would settle it.
- **What `sowing_density_per_m2` counts.** It was observed on one species; whether it counts seeds or plants, and whether a cultivar carries it, is not recorded. Until it is, it is context only.
- **Whether a live instance has a tool that records a bed, a layout or a planting run.** The measured catalog has none, the server spec says to treat any tool count as a floor, and nobody has run `tools/list` against a reachable instance. The `-apply` recipe waits on it, in nolte/kamerplanter-goose#74.
- **Crops that span the season boundary.** A run whose harvest reaches into the next year has unknown occupancy here, because one run plans one season. A multi-season layout would need the rotation plan's later seasons and is out of scope.
- **How determinism is measured.** This spec defines the plan facts and requires them to be the same over the same input blocks. It is checked on a fixed fixture written out as text, repeated runs compared; that shows the property for that fixture and not for a live garden, and the number of runs needed to call it stable is not settled here.
- **Where the audit, nolte/kamerplanter-goose#39, places layout relative to planting and rotation.** Whether collection, succession and layout stay three skills is the audit's decision.
