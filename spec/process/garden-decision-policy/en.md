# Garden Decision Policy

Status: draft
Portfolio-Scope: local

## Context

Every garden skill in this repository ends by telling a person what to do with a living plant, and each of them decides what to believe on its own. The nutrient process ranks five tiers of evidence, the pest process ranks five different ones, and the skills that read a photo or a care log carry the rest in prose. That works while each skill answers one question. It stops working when a recommendation has to combine questions — watering against a nutrient reading against a pest suspicion — because the tiers of one process cannot be compared to the tiers of another, and nothing says what wins when they disagree.

This spec states one policy for that: how evidence is ranked, which rules a recommendation may never break, what a recommendation must expose, and what a normalised view of a garden has to say about the fields it could not fill. It specifies the rules; the skills `decision-policy` and `garden-context` apply them, and the recipe `garden-context-check` reports what the second one found.

The policy exists because of three failure shapes that were each observed in a neighbouring spec. A symptom read from a photo is taken as the cause. A due reminder is taken as a need. A missing measurement is replaced by a plausible one. Each is cheap to commit and expensive to notice, because the output still reads as an answer.

Everything about the tool surface below comes from [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md), last measured against the reference instance on 2026-08-16. **Nothing in this spec was re-measured against a live instance when it was written**: the `kamerplanter` MCP server was unreachable in the session that drafted it (`INVALID_CONFIG`). Tool names are therefore quoted from that spec; whether a name still exists, and what its response carries, is unestablished until a `tools/list` and a read-only call against a reachable instance say so.

Boundaries: [the nutrient imbalance process](../nutrient-imbalance-detection/en.md) and [the pest pressure process](../pest-pressure-assessment/en.md) own their own evidence ladders and the decisions made with them. This spec does not change either; it relates them to a common ranking and lists where they disagree. The audit that decides which artifact owns what, and whether any of them is renamed, merged or retired, is a separate piece of work tracked as nolte/kamerplanter-goose#39, and nothing here pre-empts it. [The recipe project pattern](../../goose/recipe-project-pattern/en.md) owns recipe mechanics and [the server spec](../../mcp/kamerplanter-mcp-server/en.md) owns transport, authentication and tenancy.

Readers: authors of garden skills and recipes in this repository, and anyone reviewing a recommendation one of them produced before acting on it.

## Goals

- Every recommendation names what it rests on, and the reader can tell a measured value from a catalogue default from general knowledge
- Evidence of a lower rank corroborates or contradicts evidence of a higher rank and never overrides it
- A missing input is reported as missing; the recommendation degrades in a stated way instead of filling the gap
- Confidence and uncertainty are part of the output, not a tone of voice
- A normalised garden context says which fields it holds and which it could not fill, with the reason

## Non-Goals

- Deciding any specific question — direction of a nutrient problem, tenability of a pest, a watering interval. Those are the processes that own them
- Applying a recommendation, confirming a task, or changing a record
- Renaming, merging, splitting or retiring any existing skill, recipe or spec — that is the audit tracked as nolte/kamerplanter-goose#39
- Specifying any tool the server catalog does not name. Where a field has no source in the measured catalog, this spec says so
- Replacing a laboratory analysis, a horticultural reference, or a person's judgement

## Requirements

### A. The evidence hierarchy

Evidence is ranked in eight levels, highest first. The rank travels with each claim into the output.

| Level | Evidence | Source in the measured catalog | Not established |
|-------|----------|-------------------------------|-----------------|
| 1 | A current measurement: a value with a recognisable unit, recorded for this plant, recent enough for the question | Diary entries carrying `measurements`: `list_diary_entries`, `get_diary_entry` | What "recent enough" means per question (see Open Questions). The `measurements` object has no fixed key set, so the key is normalised or refused, never assumed |
| 2 | A historical measurement of this plant, too old to describe now but still describing the plant | The same diary entries; `get_plant_diagnostics` | The fields `get_plant_diagnostics` returns are not enumerated in the server spec |
| 3 | A confirmed observation: something a person or a recorded process established about this plant | `get_plant_inspections` (IPM history), `get_plant_care_log` (`confirmed_at`, `interval_at_time_days`), diary entries of observation type | Whether a diary entry was confirmed by a person is not a field the server spec names |
| 4 | Kamerplanter species and cultivar data, the cultivar before the species | `get_cultivar`, `list_cultivars`, `get_species_info`, `get_species_lifecycle`, `get_species_phase_sequence`, `list_phase_definitions`, `get_plant_phase_status`, `get_plant_nutrient_plan` | `get_plant_phase_status` can answer `phase_state: unresolved`, which reads as a normal result and is not |
| 5 | Site data: what is known about where the plant stands | A plant's `site_key` and `location_key` from `list_plants` / `get_plant`; `list_plants_at_location`; `list_substrates`; `list_hardiness_zones` | **No read tool for a site's own attributes is named in the measured catalog.** The keys identify a site; what the site is like is not measured |
| 6 | Weather | **No source measured.** The server catalog names no weather tool; the Home Assistant server publishes entity state through `GetLiveContext`, and whether any weather entity is exposed is unmeasured | Everything |
| 7 | A documented expert source: a cited reference, not the model's recollection | `search_plant_knowledge` is declared; measured on 2026-08-16 it answered `service.unavailable` because the knowledge base is an optional component not deployed on the reference instance. `search_glossary` returns the project's own definitions of terms, which is vocabulary, not evidence | Whether any instance deploys the knowledge base |
| 8 | General knowledge of the model that is not in any record | None, by definition | Always labelled as not from the record |

- **MUST** assign every claim in a recommendation to exactly one level and carry the level with the claim into the output
- **MUST NOT** let evidence of a lower level override evidence of a higher level; lower evidence corroborates or contradicts, and a contradiction is reported as such, not resolved silently in favour of the lower
- **MUST** label level 8 evidence as not from the record wherever it appears
- **MUST** prefer, within level 4, cultivar data over species data for the same attribute
- **MUST NOT** treat a level for which the measured catalog names no source as available; the field is reported absent with the reason "no source measured"

### B. Core rules

- **MUST NOT** diagnose from a single symptom. A diagnosis cites at least one further piece of evidence that is not that symptom, or is labelled a suspicion
- **MUST NOT** recommend watering solely because a reminder is due. A due task is a request from the schedule; the recommendation additionally names the evidence about the plant's current state that supports it, or says there is none
- **MUST** prefer a measured value over general knowledge about the same quantity, and say so when it declines a measurement because it is stale
- **MUST** prefer cultivar-specific data over species defaults when both are present for the same attribute, and name which one it used
- **MUST**, where an environmental cause is among the candidates, name it and propose its correction before a treatment of the plant, and say why when it does not
- **MUST NOT** invent a measurement. A value that is not in the record is reported missing, together with the observation that would supply it

### C. The recommendation output

- **MUST** return, with every recommendation, an evidence list in which each entry carries its level, its source (tool or document), and when it was retrieved
- **MUST** return a confidence for the recommendation, and **MUST** derive it from the highest level that supports it rather than from the fluency of the text
- **MUST** return an uncertainty statement naming what would change the recommendation
- **MUST** return a missing-data list, naming each input the recommendation would have used and did not have
- **MUST**, where the process that owns the question proposes no action below a stated evidence tier, follow that process; this spec sets no threshold of its own
- **MUST NOT** express a recommendation as an instruction to a device or a write; a recommendation is a proposal to a person

### D. The garden context

A garden context is a normalised view of one garden. It is a value passed between steps, not a store.

| Field | Source in the measured catalog | Not established |
|-------|-------------------------------|-----------------|
| Site and location | `site_key`, `location_key` from `list_plants` / `get_plant`; `list_plants_at_location` | Attributes of the site itself: no read tool named |
| Beds and containers | No source measured | Whether a location is a bed or a container is not a field the server spec names |
| Crops and cultivars | `list_plants` (`species_key`), `get_species_info`, `list_cultivars`, `get_cultivar` | — |
| Planting runs | `list_planting_runs` | Pagination behaviour is not measured |
| Growth stage | `current_phase_key` from `list_plants`; `get_plant_phase_status`, `get_plant_phase_history` | An `unresolved` phase state is an absent stage, not a normal one |
| Current measurements | Diary entries (`list_diary_entries`, `get_diary_entry`) | The key set of `measurements` |
| Historical observations | `get_plant_inspections`, `list_diary_entries`, `get_plant_care_log` | — |
| Weather | No source measured | Everything |
| Soil and substrate | `substrate_key` from `list_plants`; `list_substrates` | — |
| Watering and fertilisation state | `get_plant_care_log`, `get_due_care_tasks`, `list_tasks`, `get_plant_nutrient_plan` | Dose amounts: the care log records a confirmation, not a quantity |
| User goals and constraints | No source measured; may be supplied by the caller | Whether any instance stores goals |

- **MUST** report every field of the context as `present` or `absent`, and **MUST** give each `present` field its source tool and retrieval time
- **MUST** give each `absent` field the reason: "no source measured", the typed refusal the server answered, or the empty result, and **MUST NOT** fill it with a default
- **MUST** resolve the garden explicitly before collecting anything, through `list_tenants` or a `tenant` input, per [the server spec](../../mcp/kamerplanter-mcp-server/en.md), and **MUST NOT** assume a key covers exactly one garden
- **MUST NOT** call any state-changing tool while collecting a context; the collection is read-only
- **SHOULD** report the list of absent fields as its own block, separate from the data, so a downstream step cannot read past it
- **MAY** accept a field from the caller — user goals, for example — and **MUST** then mark its source as the caller, not as a tool

### E. Relationship to the existing ladders

The ladders in [the nutrient process](../nutrient-imbalance-detection/en.md) and [the pest process](../pest-pressure-assessment/en.md) rank evidence for one question each. They remain authoritative for that question.

| Existing tier | Nutrient process | Pest process | Hierarchy level |
|---------------|------------------|--------------|-----------------|
| Measured value from a diary entry | Tier 1 | — | 1, or 2 when no longer current |
| Recorded inspection naming the organism | — | Tier 1 | 3 |
| Plan target against reconstructed supply | Tier 2 | — | No level: derived from 3 and 4 (see Open Questions) |
| Catalogue fields | — | Tier 2 | 4 |
| Care-log pattern | Tier 3 | — | 3 |
| Situation fit: category, phase, season, care history, enclosure | — | Tier 3 | 4 and 5, with care history at 3 |
| Visible symptoms read from an image | Tier 4 | Tier 4 | No level (see Open Questions) |
| Species demand level and phase expectation | Tier 5 | — | 4 |
| General knowledge of the taxon, labelled as not from the record | — | Tier 5 | 8 |

- **MUST** keep a process's own ladder authoritative for the decisions that process owns, and **MUST NOT** re-rank its tiers using this hierarchy
- **MUST** use this hierarchy to compare evidence across processes, where two ladders would otherwise be compared by tier number
- **MUST** record, where this spec and a process ladder disagree, the disagreement as an Open Question and **MUST NOT** resolve it by editing the other spec

## Acceptance Criteria

- [ ] A skill applying this policy returns, for every recommendation, an evidence list with level, source and retrieval time, a confidence, an uncertainty statement and a missing-data list
- [ ] No recommendation in a checked run rests on a single symptom, on a due reminder alone, or on a measurement that is not in the record
- [ ] A run follows the threshold of the process that owns its question, and this spec's output adds none
- [ ] A garden context lists every field of section D as present or absent; each absent field names its reason; no absent field holds a default
- [ ] Beds and containers, weather and user goals are reported absent with "no source measured" unless a tool named in the server spec supplies them, or the caller does
- [ ] The collection step calls no state-changing tool and resolves the tenant before reading anything
- [ ] Neither existing ladder is changed by the work that implements this spec, and every disagreement between the two sets of rules is listed under Open Questions
- [ ] Every claim about the tool surface cites the server spec; a claim not re-measured says so
- [ ] The German and the English file have the same headings in the same order, the same number of requirement bullets and the same number of acceptance checkboxes

## Source

- [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) — tool catalog, caveats and tenancy, measured against the reference instance on 2026-08-16
- [the nutrient imbalance process](../nutrient-imbalance-detection/en.md) — §"The evidence ladder"
- [the pest pressure process](../pest-pressure-assessment/en.md) — §"The evidence ladder"
- [the recipe project pattern](../../goose/recipe-project-pattern/en.md)
- Issue nolte/kamerplanter-goose#40 — the eight levels and six rules are taken from its body; nolte/kamerplanter-goose#39 — the audit that owns ownership boundaries

## Open Questions

- **Where a photo reading sits.** Both existing ladders rank a symptom read from an image fourth; this hierarchy has no level for it. A reading confirmed by a person or a recorded inspection belongs at level 3, but an unconfirmed reading by a model is neither a confirmed observation nor general knowledge. Open because placing it either way changes what outranks it: at level 3 it would outrank species data, which both existing processes deny it. To be decided with the audit, nolte/kamerplanter-goose#39.
- **Where derived evidence sits.** The nutrient process's tier 2 combines a plan target, a confirmed frequency and a substrate baseline into a reconstructed supply. The hierarchy ranks sources, not derivations, and gives such a derivation no level. Open because the derivation is the nutrient process's own and ranking it here would re-rank its ladder. Whether the nutrient process's open question about tier 2 without dosage records changes this is not decided here.
- **Whether the ranking is global or per question.** The existing ladders order evidence for one question and let a species prior be the lowest tier; this hierarchy places species data above site data and weather. For a question where weather decides — a frost, a heat spike — a global order may be the wrong one. Open because no process in this repository has yet needed both orders at once.
- **Whether a common action threshold is needed.** The nutrient process proposes no dosage change when its best evidence is its tier 3 or lower, and the pest process proposes a treatment only when the identification rests on its tier 1, or on its tier 4 plus an uncontradicted tier 2; these are thresholds on two different ladders, and this spec sets none. Open because a threshold stated on the hierarchy would have to be reconciled with both, and the mapping in section E is by reading, not by running a case through both.
- **What "recent enough" means for level 1.** The nutrient process says "when recent enough" without a threshold; no process states one per quantity. Open because the threshold depends on how fast the quantity moves (a soil moisture reading and an EC reading do not age alike) and no measured source of that exists in the record.
- **Whether a live instance offers sources this spec marks "no source measured".** Nobody has run a `tools/list` against a reachable instance for bed, container, weather or goal tools; the server was unreachable when this spec was written. The fields stay absent until a measurement says otherwise, and finding a tool moves the field, not the contract.
- **Whether the knowledge base is deployable.** `search_plant_knowledge` is declared and was measured unavailable; level 7 has no working source on the measured instance. Open because it is an optional component and nothing in the record says whether the operator intends to deploy it.
- **Which artifact owns what.** `plant-context-collect` collects the context of one plant, and the context contract in section D collects the context of a garden; where one ends and the other begins, and whether the existing ladders move into a shared skill, is the audit's decision, nolte/kamerplanter-goose#39.
