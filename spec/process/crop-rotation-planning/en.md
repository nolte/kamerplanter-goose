# Crop Rotation Planning

Status: draft
Portfolio-Scope: local

## Context

A rotation keeps one plant family from standing in the same bed season after season, because soil-borne pests and diseases of that family build up there and the family draws on the soil the same way each time. Rotation is a multi-season decision about a bed: it needs to know what stood in each bed before, which family each crop belongs to, and how many seasons a family should stay away. A process that answers it from general knowledge produces a plan that reads as sound gardening and rests on nothing the garden told it: a remembered family for a species, a remembered interval, a remembered history.

The issue that asked for this, nolte/kamerplanter-goose#47, assumed a crop and family graph in the catalog. The measured surface holds much less. `get_species_info` carries `family_key`, `nutrient_demand_level` and `green_manure_suitable`. No tool reads a family, no family carries a name or a rank, and no relationship between families exists. The value sets of `nutrient_demand_level` are not recorded beyond the two examples `heavy_feeder` and `medium_feeder`. The only species-to-species relation, `compatible_companions[]`, is about planting side by side, not one after another. Nothing records a bed, a container or a bed's history. So this spec reuses the one graph edge that exists, species to `family_key`, and takes everything else from the caller or reports it unknown.

This spec specifies two steps. Collecting the rotation history reads each crop's family, demand class and green-manure suitability, and the garden's current and archived plants per location with their inspections. Planning the rotation turns that history, the caller's beds, the bed history, the interval and the constraints into one family group per bed and season, with a verdict for every crop considered and every conflict named. Both are read-only. A rotation plan is a document; recording it is a separate step, and the measured catalog has no tool that could do it (section G).

Everything about the tool surface below is quoted from [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) and from [the species baseline process](../species-baseline-verification/en.md), whose measurements were taken against the reference instance on 2026-08-07 and 2026-08-16. **Nothing here was re-measured when this spec was written**: the `kamerplanter` MCP server was unreachable in the session that drafted it (`INVALID_CONFIG`). A tool or field name is quoted from those specs; whether it still exists, and what a response carries beyond what they record, is unestablished until a `tools/list` and a read-only call against a reachable instance say so.

Boundaries: [the garden decision policy](../garden-decision-policy/en.md) owns the weight a claim carries, the recommendation shape and the garden context; this spec applies them and does not restate them. [The plant planning spec](../plant-planning-and-planting-calendar/en.md) owns the planting runs, and its runs stay `rotation: unknown`, because a run is assigned no bed and a rotation verdict exists only per bed. Bed layout, area, spacing, companion placement and succession are nolte/kamerplanter-goose#46, which reads this spec's output. The `-apply` half of nolte/kamerplanter-goose#47 is tracked in the blocked follow-up split out of #47. The audit that decides which artifact owns what is nolte/kamerplanter-goose#39 and nothing here pre-empts it. [The recipe project pattern](../../goose/recipe-project-pattern/en.md) owns recipe mechanics and [the server spec](../../mcp/kamerplanter-mcp-server/en.md) owns transport, authentication and tenancy.

Readers: authors of garden skills and recipes in this repository, the author of bed layout who consumes the rotation plan, and anyone reviewing a rotation before acting on it.

## Goals

- Every verdict names the rule that produced it, the fields it came from, their source and the evidence level it rests on
- A family, a demand class, an interval or a bed history that has no source is reported unknown with the missing input, never recalled
- A conflict is never hidden: a rule the plan breaks, including one broken by the caller's own pin, is listed with the evidence on both sides
- The plan is a function of its input blocks, so two runs over the same blocks give the same plan facts
- Read-only planning and recording are separate, and a plan can be reviewed before anything is recorded
- Bed layout can read the plan without re-deriving anything

## Non-Goals

- Recording a rotation, assigning a future crop to a bed, or creating a planting run. The measured catalog has no tool for it (section G)
- Bed layout, area and capacity, spacing, companion placement and succession — nolte/kamerplanter-goose#46
- Planting dates: those are [the planting calendar](../plant-planning-and-planting-calendar/en.md)
- Choosing crops: that is [crop selection](../site-analysis-and-crop-selection/en.md)
- A family, a rotation interval, a demand order or a soil effect from general knowledge. A value comes from a recorded field or from the caller, or it is unknown
- Researching a family during a run. The three-source rule of [the species baseline process](../species-baseline-verification/en.md) runs outside a recipe, and garden recipes fetch no URL

## Requirements

### A. Inputs

| Input | Source | Not established |
|-------|--------|-----------------|
| Candidate crops | The caller: entries `species_key` or `species_key:cultivar_key`, separated by commas | — |
| Planned seasons | The caller: consecutive years, separated by commas | — |
| Beds | The caller: entries `name` or `name:area_or_volume`, separated by commas | No source in the measured catalog |
| Bed history | The caller: entries `bed:season:species_key[:cultivar_key]` or `bed:season:none`, separated by commas; and the catalog, section C | Whether a catalog location is a bed |
| Rotation interval | The caller only: `rotation_years`, a whole number | No source; no number is built in |
| Demand order | The caller only: `demand_sequence`, values separated by commas | The value set of `nutrient_demand_level` |
| Constraints | The caller only: entries separated by semicolons, `pin=bed:season:species_key[:cultivar_key]`, `exclude=bed:species_key[:cultivar_key]`, or free text | — |
| The garden's planting runs | `list_planting_runs` | Their shape and parameters |

- **MUST** split every list at its separator and each entry at its colons, and **MUST NOT** pass the joined text on as a name; a bed name is the text before the first colon of a `beds` entry
- **MUST** stop and name the problem when the seasons are not consecutive whole years, and **MUST NOT** fill a gap
- **MUST** mark beds, bed history, the interval, the demand order and the constraints as source `caller`, and **MUST** report each as not supplied when the caller left it empty
- **MUST** treat as the plan's beds the union of the `beds` entries, the beds named in the bed history and the beds named in a pin, and **MUST** report that there is nothing to place when that union is empty
- **MUST** list every entry that cannot be parsed, and every free-text constraint, verbatim as `not evaluated`, and **MUST NOT** interpret free text as a rule
- **SHOULD** list the garden's planting runs as context only, since their shape is not recorded, and **MUST NOT** treat a partial or failed read of them as proof that there are none

### B. Family, demand class and green manure

| Field | Tool | Level | Not established |
|-------|------|-------|-----------------|
| `family_key` | `get_species_info` | 4 | Whether every species carries it; no family read tool, name or rank exists |
| `nutrient_demand_level` | `get_species_info`, `get_cultivar` | 4 | Its value set: only `heavy_feeder` and `medium_feeder` are recorded |
| `green_manure_suitable` | `get_species_info`, `get_cultivar` | 4 | Which species carry it |

- **MUST** read `get_species_info` once per distinct species among the candidates, the pins and the bed history, and **MUST** read `get_cultivar` only for a cultivar an entry names
- **MUST** use a cultivar's value when the cultivar carries the field and the species value otherwise, and **MUST** record which, per field
- **MUST** report an absent field as absent, meaning not populated for that species, and **MUST NOT** read an absent `family_key` as "belongs to no family"
- **MUST NOT** take a family from recall, from a scientific name or from a genus, and **MUST NOT** research one during a run; a crop without a recorded `family_key` has family `unknown`
- **MUST NOT** read `compatible_companions[]` as a rotation relationship
- **MUST** compare `nutrient_demand_level` with the demand order as text, as recorded, and **MUST NOT** build in a heavy, medium, light, green-manure convention
- **MUST** use `green_manure_suitable: true` only to let a crop match the value `green_manure` in the caller's demand order, and **MUST** report every other soil effect, among them nitrogen fixation and the persistence of soil-borne disease, as `not modeled`

### C. Bed history

| Source | What it gives | Not established |
|--------|---------------|-----------------|
| The caller's `bed_history` | Bed, season, crop or `none` | — |
| `list_plants` with `include_archived: true` | Per plant: `species_key`, `location_key`, `planted_on`, current and archived plants | Whether an archived plant keeps `location_key` and `planted_on`, which field marks it archived, and whether an end date exists |
| `get_plant_inspections` | The IPM history of one plant | The fields beyond pressure level, symptoms and structured findings |

- **MUST** take the caller's bed history as the primary source, and **MUST** attach a catalog plant to a bed only when its `location_key` equals the bed name exactly; every other location is listed as `unmapped location history`, context only
- **MUST** read `list_plants` with `include_archived: true`, paged and capped as the `garden-context` skill pages and caps it, and **MUST** report a partial or failed read as such and **MUST NOT** treat it as "no history"
- **MUST** take the year of `planted_on` as a catalog plant's season, and **MUST** report a plant without `planted_on` as history with season `unknown`
- **MUST** count a bed's history as established only when the caller supplied at least one entry for it, `none` included, or when a complete catalog read mapped at least one plant to it; an established history is taken as complete, so a season it does not name holds no crop, and the plan **MUST** say that this is an assumption resting on the caller
- **MUST** treat a history entry in a planned season as occupying that bed and season, and **MUST** count it as history for the later seasons
- **MUST** read `get_plant_inspections` only for plants at a location mapped to a bed, and **MUST** report a recorded inspection as a `caution` for that bed at level 3 with the missing input `host range: not recorded`; neither `get_pest` nor `get_disease` records a host range, so a pressure **MUST NOT** become a conflict
- **MUST NOT** reuse the judgement of a living plant's pest pressure for a future crop

### D. Rules and verdicts

Every crop considered for a bed and season gets exactly one verdict, the first that applies in this order:

| Verdict | When |
|---------|------|
| `unknown` (family) | The crop's family is `unknown` |
| `conflict` | With `rotation_years` N: a crop of the same family stands in the same bed in a season 1 to N−1 seasons earlier |
| `repeat — interval unknown` | Without `rotation_years`: a crop of the same family stands in the same bed in any earlier season |
| `unknown` (history) | A crop of unknown family stands in the comparison window, the bed holds a history entry whose season is `unknown`, or the window reaches before the first planned season of a bed whose history is not established |
| `caution` | None of the above, and the bed has a recorded inspection |
| `clear` | None of the above |

The comparison window is the seasons 1 to N−1 seasons earlier with an interval, and every earlier season without one. It holds the bed history and the plan's own placements in earlier planned seasons.

- **MUST** give every verdict its rule, the fields on both sides with their sources and levels, and the missing data per [the garden decision policy](../garden-decision-policy/en.md); a verdict resting on a caller-supplied fact **MUST** say so
- **MUST** read N as the smallest distance in seasons at which a family may stand in a bed again, and **MUST NOT** supply a value when the caller gave none
- **MUST NOT** report `conflict` or `clear` for a same-family repeat when no interval was supplied
- **MUST NOT** report `clear` for a crop of unknown family or for a window the history does not cover
- **MUST** treat demand order as a preference, `met`, `unmet`, `unknown` or `not evaluated`, judged against the demand class of the crop in the same bed one season earlier, and **MUST NOT** let it produce a conflict
- **MUST** honour a pin by placing its crop, and **MUST** report a pin that breaks a rule, lands on an occupied bed and season, or contradicts an exclusion or another pin, as a conflict, and **MUST NOT** move it
- **MUST** honour an exclusion by not considering that crop for that bed in any season

### E. The plan and its consumers

The planner walks the seasons in order and, within a season, the beds by name as text. Pins are placed first. For every other bed and season it considers each family group, the candidate crops that share a `family_key`, with every crop of unknown family as a group of its own, and drops the crops excluded from that bed.

- **MUST** select, per bed and season, at most one family group whose verdict is `clear`, `caution` or `unknown`, and **MUST** report the bed and season as `open`, with every group and its verdict, when none qualifies
- **MUST** rank the qualifying groups by verdict (`clear`, then `caution`, then `unknown`), then by how many beds already hold the group in that season (fewer first), then by demand preference (`met`, then `unknown` or `not evaluated`, then `unmet`), then known families before unknown ones, then by group key as text
- **MUST NOT** place runs, area or spacing; a placement names a family group and its crops, and bed layout places them
- **MUST** give every placement a rationale that states the ranking values and names every group not chosen with its verdict
- **MUST** list every candidate crop never placed under `NOT PLACED`, with the reason per bed and season: its verdict, its exclusion, or the group that outranked it
- **MUST** key every crop as `species_key/cultivar_key`, with `none` for no cultivar, which is the prefix of a [plant planning](../plant-planning-and-planting-calendar/en.md) run identifier, so a plan and a planting plan join on it

The plan document has six blocks, in this order and under these names: `ROTATION HEADER` (the garden, given or discovered, the inputs, the interval and demand order or `not supplied`, the not-evaluated entries), `BED HISTORY`, `ROTATION PLAN`, `CONFLICTS` (every placed crop that breaks a rule and every contradiction a pin causes; since selection never places a `conflict` or a `repeat — interval unknown`, only a pin produces an entry, and a crop considered for a slot and not placed there keeps its verdict in that slot and under `NOT PLACED`), `NOT PLACED` and `APPLY CONTRACT`. The level of a verdict is `caller` when it rests on any caller-supplied item, and otherwise the weakest level among its items.

| Consumer | Reads |
|----------|-------|
| Bed layout (nolte/kamerplanter-goose#46) | per bed and season: the bed, the season, the selected family group or `open` or `occupied`, the crops as `species_key/cultivar_key` with their verdicts, the conflicts |
| A person reviewing a [plant planning](../plant-planning-and-planting-calendar/en.md) plan | per crop: the beds and seasons it is placed in, joined to the planting runs on the `species_key/cultivar_key` prefix |

- **MUST** return the six blocks in this order with these names, and **MUST NOT** return a field that was not read, listing an unread field as absent with its reason

### F. Determinism

- **MUST** make the plan a function of the supplied input blocks and the policy, so that two runs over the same blocks give the same plan facts: the placements, the verdicts, the conflicts, the not-placed reasons and the evidence levels
- **MUST NOT** let the order of the input or the current date decide a plan fact; retrieval times are reported beside the facts and are not compared
- **MUST** state that byte-identical prose outside the plan facts is not claimed, and that the property is checked on a fixed fixture of input blocks and not on a live garden

### G. Separation and the apply contract

- **MUST** keep rotation planning read-only: the planning skills and recipes call no state-changing tool
- **MUST** include in every plan an `APPLY CONTRACT` block that states, per placement, what a later `-apply` recipe would have to record (the bed, the season, the family group and its crops), and **MUST** state that the measured catalog has no tool that records a bed assignment, a rotation, a planting run or a plan: the write tools it records are `add_plant_diary_entry`, `confirm_care_task`, `archive_plant`, `set_plant_location`, `claim_diary_analysis`, `submit_diary_analysis`, `transition_plant_phase`, `assign_species_phase_sequence`, `assign_nutrient_plan`, `record_feeding_event` and `create_inspection`, and the setup tool `create_site`, and none of them does; `set_plant_location` moves a plant that exists, and a rotation plans crops that are not plants yet
- **MUST** name the blocked follow-up split out of #47 as the place where the `-apply` recipe is tracked, and **MUST NOT** ship a recipe with the `-apply` suffix that does not write what its description says
- **MUST** leave recording a plan to a separate recipe that takes an approved plan, after a person has reviewed it

## Acceptance Criteria

- [ ] Every verdict names its rule, its fields with their sources and levels, and the missing data; a verdict resting on a caller fact says so
- [ ] A crop without a recorded `family_key` is `unknown` everywhere, and no family comes from recall or research
- [ ] Without `rotation_years`, a same-family repeat is `repeat — interval unknown`, never `conflict` and never `clear`
- [ ] A bed whose history is not established gives `unknown` wherever the comparison window reaches before the plan, never `clear`
- [ ] A catalog plant is attached to a bed only on exact `location_key` equality, and a partial or failed history read is reported, not read as no history
- [ ] A recorded inspection gives `caution`, never `conflict`
- [ ] Demand order is a preference and never produces a conflict; no demand convention is built in
- [ ] A pin is always placed, and a pin that breaks a rule is listed under `CONFLICTS`
- [ ] Every placement has a rationale naming the groups not chosen, and every crop never placed is listed with its reasons
- [ ] Every crop is keyed `species_key/cultivar_key`
- [ ] The plan has the six blocks in order, and the apply contract states that the measured catalog has no tool that records a rotation
- [ ] Two runs over the same input blocks give the same plan facts on a fixed fixture, and the plan says what is not claimed
- [ ] The rotation skills and recipes call no state-changing tool
- [ ] Every claim about the tool surface cites a spec in this repository; a claim not re-measured says so
- [ ] The German and the English file have the same headings in the same order, the same number of requirement bullets and the same number of acceptance checkboxes

## Source

- [The Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) — the tool catalog with no family read tool, `get_plant_inspections` measured empty on a plant never inspected, `get_pest` measured without host-range fields, the write and setup tools, and tenancy
- [The species baseline process](../species-baseline-verification/en.md) — `family_key`, `nutrient_demand_level`, `green_manure_suitable` and `compatible_companions[]` observed present on two species on 2026-08-07, a missing key meaning not populated, and the three-source rule
- [The nutrient imbalance process](../nutrient-imbalance-detection/en.md) — `heavy_feeder` and `medium_feeder` as the recorded examples of `nutrient_demand_level`
- [The garden decision policy](../garden-decision-policy/en.md) — evidence levels, the recommendation output, and the garden context with beds and containers as having no source
- [The plant planning spec](../plant-planning-and-planting-calendar/en.md) — the run identifier whose prefix this plan joins on, and the rotation note it leaves unknown
- `recipes/plant-master-data-check.yaml` — `list_plants` measured with `matched: 9` against `total_in_tenant: 11`, the only evidence that archived plants exist
- [The recipe project pattern](../../goose/recipe-project-pattern/en.md)
- Issue nolte/kamerplanter-goose#47 — the rotation factors and the five criteria are taken from its body; nolte/kamerplanter-goose#46, #59 and #39 — the consumer, the precedent for a blocked apply half, and the audit

## Open Questions

- **Whether every species carries `family_key`, and the value set of `nutrient_demand_level`.** Both were observed on two species, and which of the two carried which field is not recorded. A plan full of `unknown` is the honest result until `get_species_info` on ten or more vegetable species says otherwise.
- **What an archived plant carries.** Whether `list_plants` with `include_archived: true` keeps `location_key` and `planted_on`, and whether an end date exists. Until it is measured, the caller's history is primary.
- **Crops that stand longer than one season.** The catalog season is the year of `planted_on`, so a perennial or a crop spanning two years counts in its planting year only. No `cycle_type` field exists to correct it.
- **Built-in family intervals.** None are built in. Researched intervals would need three independent sources each, at authoring time and not in a run, and would be an amendment to this spec.
- **The shape of `list_planting_runs`.** Planting runs stay context until their shape is recorded.
- **Whether a live instance has a tool that records a rotation or a bed assignment.** The measured catalog has none, the server spec says to treat any tool count as a floor, and nobody has run `tools/list` against a reachable instance. The `-apply` recipe waits on it, tracked as the blocked follow-up split out of #47.
- **How determinism is measured.** This spec defines the plan facts and requires them to be the same over the same input blocks. It is checked on a fixed fixture written out as text, repeated runs compared; that shows the property for that fixture and not for a live garden, and the number of runs needed to call it stable is not settled here.
- **Where the audit, nolte/kamerplanter-goose#39, places rotation relative to planting and bed layout.** Whether collection and planning stay two skills is the audit's decision.
