# Garden and Season Review

Status: draft
Portfolio-Scope: local

## Context

A season ends with a question that faces backwards and is asked for the sake of the next one: what worked, what did not, and what should change. It has three tempting wrong answers. A review written from memory of the season reports what the reviewer expected rather than what was recorded. A review that links care to outcome ("the plant failed because it was fed late") states a cause no record can carry. A review that sees only the plants still alive hides the ones that failed. This spec fixes how a retrospective of a garden, up to an assessment date or over a bounded season, is assembled from recorded history and caller statements, what may be said about cultivar performance and care outcomes, and the shape in which the review hands its result to the next planning cycle.

A review here is a statement to a person. It changes nothing and persists nothing: no file is written and no diary entry is added. It is assembled by a tool-free skill from blocks that other skills already collected; the only additional read is the listing of archived plants in season scope, named below.

Everything about the tool surface is quoted from [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md), measured against the reference instance on 2026-08-16 and not re-measured for this spec: the Kamerplanter MCP server was unreachable (`INVALID_CONFIG`) when this spec was written. Five facts the requirements rest on were read from the working copy rather than measured: historical observations come from `get_plant_inspections`, `list_diary_entries` and `get_plant_care_log` ([the garden decision policy](../garden-decision-policy/en.md), its garden context table); `list_plants` accepts `include_archived`, as used by `recipes/plant-master-data-check.yaml` and `.claude/skills/garden-context/SKILL.md`, but the parameter is not recorded in the server spec; `diary-measurements-read` opens at most eight entries per plant (`.claude/skills/diary-measurements-read/SKILL.md`), and the `list_diary_entries` signature is unmeasured, so a season's diary is not known to be fully readable; no field for yield or harvest amount is recorded (a search of `spec/mcp` for "yield" finds none); and the planning recipes take `crops`, `goals`, `harvest_window` and `constraints` as caller strings (`recipes/garden-plan.yaml`, `recipes/crop-selection.yaml`).

Boundaries: [the garden decision policy](../garden-decision-policy/en.md) owns the evidence levels, the six rules and the shape of a recommendation; this spec states no level of its own. [The harvest readiness and planning spec](../harvest-readiness-and-planning/en.md) owns every harvest result this review consumes, and [the growth stage and weather impact spec](../growth-stage-and-weather-impact/en.md) every growth-stage result and weather exposure; neither is restated. [The nutrient](../nutrient-imbalance-detection/en.md) and [pest](../pest-pressure-assessment/en.md) processes own their results; a review consumes them only when the caller supplies them. [The plant health and IPM planning spec](../plant-health-and-ipm-planning/en.md) owns the plant health finding; a review consumes it only when the caller supplies it and never runs it. [The plant planning and planting calendar spec](../plant-planning-and-planting-calendar/en.md) and [the site analysis and crop selection spec](../site-analysis-and-crop-selection/en.md) own the parameters the next-cycle block is shaped for; they are not amended. Crop rotation (nolte/kamerplanter-goose#47) is not a dependency. [The recipe project pattern](../../goose/recipe-project-pattern/en.md) owns how a recipe is built, including forbidden-by-name.

Readers: authors of garden skills and recipes in this repository, and the people who review a garden or a season and then plan the next one.

## Goals

- A review says per plant what was recorded, what was supplied by the person and what is absent, with the source of each
- Cultivar performance is stated side by side on recorded fields, never as a score or an average across units
- A care outcome is linked to care only as "consistent with", never as a cause
- The plants that failed or were archived are part of a season review, and the limits of what was read are stated
- The review ends in a block the next planning run can take as its parameters, without anything being written

## Non-Goals

- Persisting a review, as a file or as a diary entry: no `-apply` recipe
- Assessing the present state of a plant: the review runs no nutrient, pest, watering, fertilisation or health assessment of its own
- Assessing plant health or planning pest management (the plant health and IPM planning spec), beyond the recorded inspections and caller-supplied results
- Crop rotation (nolte/kamerplanter-goose#47); the location history lines are string-compatible where location names equal bed names, and are not a contract
- Integrating the review into the daily garden check, or amending the planning specs
- Measuring the tool surface live. Claims about it cite the server spec and say they are not re-measured

## Requirements

### A. Inputs

- **MUST** take the garden context block from `garden-context`, the plant context blocks from `plant-context-collect` (care log and inspections included) and the diary read reports from `diary-measurements-read` as given, and **MAY** take growth-stage hand-off blocks and caller-supplied nutrient or pest results as given; the review recipes **MUST NOT** run the harvest planning themselves
- **MUST** accept as caller-supplied, marked `caller`, only facts the server has no source for: yields as `plant_key:amount unit`, harvest results as `plant_key:<readiness result>[:YYYY-MM-DD]` (typically copied from the final lines of harvest readiness checks), notes on a plant or the season, the season's weather and the assessment date, and **MUST** fill a plant's harvest result only from such a harvest result, otherwise absent
- **MUST** read a caller yield as level 3, a confirmed observation, carrying the open question on the weight of a caller statement, and **MUST NOT** read a diary `measurements` key as yield
- **MUST** report each absent input as absent with its reason, `no source` or `not collected`, and **MUST NOT** fill it

### B. Scopes and span

- **MUST** offer two scopes: `garden`, the garden up to the assessment date, and `season`, a bounded span
- **MUST** take the span in season scope as a year `YYYY`, read as `YYYY-01-01..YYYY-12-31`, or as `YYYY-MM-DD..YYYY-MM-DD` with the start not after the end, and **MUST** stop the run and name the problem when the span is absent or invalid
- **MUST**, in season scope, list the garden's plants with `include_archived: true`, report the listing as `complete`, `partial: <reason>` or `failed: <error verbatim>`, mark each plant `archived` or `live` as the listing returns it, and **MUST** report every archived plant of the listing, also when plants were named
- **MUST** review at most five named plants, the first five by plant key as text, and **MUST** list the rest as not reviewed with the reason; with no plants named, **MUST** review the garden level only and name the parameter that would supply the plants
- **MUST** state, per plant, the oldest and newest diary entry opened against the span, and **MUST** say when the span is not covered, without paging further

### C. The history record

- **MUST** return one record per reviewed plant, ordered by plant key, with fixed fields: plant key, species key, cultivar key, location name, `planted_on`, recorded phase, archived, care confirmations per reminder type, snoozes, inspections, diary coverage, growth stage, harvest result, yield and notes
- **MUST** give each field its source, level and retrieval time when present, and its reason when absent

### D. Cultivar performance

- **MUST** group the reviewed plants by `species_key:cultivar_key`, and **MUST** state the fields of each group side by side
- **MUST NOT** compute a score, a rank or an average across units, and **MUST** compare two cultivars only on the same field in the same unit

### E. Care outcomes and lessons

- **MUST** take watering and fertilisation outcomes only from the care log's confirmations and snoozes, and **MUST** link care to a result only as "consistent with", never as a cause
- **MUST** take pest, nutrient and plant health history only from the recorded inspections and caller-supplied results, **MUST** consume a supplied plant health finding as the observation it is, and **MUST** report plant health as `not supplied` when none was given
- **MUST** give every lesson exactly one kind: an observation with its source, or a recommendation for the next cycle with the four blocks of the decision policy, and **MUST** number the lessons by plant key, then field, then kind, never by statement text
- **MUST** rest a recommendation on at least one item at level 1 to 3 or a caller statement, and **MUST NOT** rest it on general knowledge alone

### F. The next-cycle block

- **MUST** return `crops` in the format the planning recipes take (`species_key[:cultivar_key]`, comma-separated), each crop marked `keep`, `reconsider` or `no evidence` with the evidence it rests on: `reconsider` when a level 1 to 3 item or a caller statement records a problem, taking precedence over `keep`; `keep` only when the caller reports a success (a yield the caller marks as a success, or a note) and no problem is recorded; `no evidence` otherwise, including for a yield figure alone
- **MUST** return `goals` as free text drawn only from the lessons and the caller's notes, `constraints` as free text carrying only recorded or caller-stated site and environmental observations and never a lesson, and `harvest_window` in the caller's month words, drawn only from harvest results and caller statements, each absent with the reason when nothing supplies it; `;` and `:` are reserved separators in the caller's parameters, and free text containing them is reported verbatim and unparsed
- **MUST** return location history lines `location_name:season:species_key[:cultivar_key]`, labelled "location, not bed"
- **MUST NOT** write the block anywhere; it is handed over as text

### G. Determinism

- **MUST** make the review a function of the supplied blocks and, in season scope, the listing named in section B, so that two runs over the same input give the same records, groups, lessons, kinds, next-cycle strings and missing-data list
- **MUST NOT** read the current date inside the facts; retrieval times are reported beside the facts and are not compared
- **MUST** state that byte-identical prose outside the facts is not claimed, and that the property is checked on a fixed fixture of input blocks written out as text

### H. Separation and forbidden tools

- **MUST** keep the skill tool-free, working only on the blocks it is handed
- **MUST** keep the skill and both recipes free of every state-changing tool, and **MUST** name all twelve that the Kamerplanter server spec lists, individually, in each recipe's prompt as forbidden
- **MUST NOT** call a Home Assistant tool, and **MUST NOT** ship an `-apply` sibling of either recipe

## Acceptance Criteria

- [ ] A review is in scope `garden` or `season`, and an absent or invalid season span stops the run with the problem named
- [ ] A season review lists archived plants, also when plants are named, reports the listing as complete, partial or failed, and marks each plant archived or live
- [ ] At most five plants are reviewed, selected by plant key as text, the rest are named as not reviewed, and with no plants only the garden level is reviewed
- [ ] Each reviewed plant has one history record with the fixed fields, ordered by plant key, each present with its source or absent with its reason
- [ ] Diary coverage is stated against the span, and a span the diary read does not cover is named
- [ ] Yield comes only from the caller, at level 3, and no diary key is read as yield
- [ ] Cultivar performance is side by side, with no score, rank or average, and two cultivars are compared only on the same field in the same unit
- [ ] No care outcome is stated as caused by care; a link reads "consistent with"
- [ ] A supplied plant health finding is consumed as an observation and never re-run; without one, plant health is reported as `not supplied`, and no present-state assessment is run by the review
- [ ] Every lesson is an observation or a recommendation with evidence, confidence, uncertainty and missing data
- [ ] The next-cycle block carries `crops`, `goals`, `constraints` and `harvest_window` in the planning recipes' formats, `reconsider` takes precedence over `keep`, `keep` needs a caller-reported success, `constraints` carries no lesson, and location history lines are labelled "location, not bed"
- [ ] Nothing is written: no file, no diary entry
- [ ] Two runs over the same input give the same facts on a fixed fixture, and the result says what is not claimed
- [ ] The skill calls no tool, neither recipe calls a state-changing or Home Assistant tool, each recipe's prompt forbids all twelve by name, and no `-apply` sibling ships
- [ ] Every claim about the tool surface cites a spec in this repository, and a claim not re-measured says so
- [ ] The German and the English file have the same headings in the same order, the same number of requirement bullets and the same number of acceptance checkboxes

## Source

- [The garden decision policy](../garden-decision-policy/en.md) — the evidence levels, the six rules, the recommendation output, and the historical observation sources
- [The harvest readiness and planning spec](../harvest-readiness-and-planning/en.md) — the harvest results a review consumes
- [The growth stage and weather impact spec](../growth-stage-and-weather-impact/en.md) — the growth-stage hand-off and the weather exposures
- [The care planning and daily check spec](../care-planning-and-daily-check/en.md) — the not-available handling of unbuilt domains and the cap of five plants
- [The plant planning and planting calendar spec](../plant-planning-and-planting-calendar/en.md) and [the site analysis and crop selection spec](../site-analysis-and-crop-selection/en.md) — the planning parameters the next-cycle block is shaped for
- [The Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) — the tool catalog and the twelve state-changing tools, measured 2026-08-16
- [The recipe project pattern](../../goose/recipe-project-pattern/en.md) — how a recipe is built here, including forbidden-by-name
- Issue nolte/kamerplanter-goose#50 — the scope and acceptance criteria are taken from its body; #47 and #48 — the domains this review does not depend on

## Open Questions

- **Whether `list_plants` accepts `include_archived`, and what an archived plant carries.** Used by two files here and not recorded in the server spec; whether an archive date is returned is unrecorded. One read call on a reachable instance would settle both.
- **How much of a season's diary is readable.** At most eight entries are opened per plant and the listing signature is unmeasured; until it is, coverage is stated rather than assumed.
- **A source for yield.** None is recorded; until one is, yield is a caller statement at level 3.
- **Where a person's statement sits.** Read as level 3, marked `caller`, carrying the open question the growth stage spec records.
- **Whether a review should be persisted.** A diary-entry `-apply` sibling would be a follow-up once the policy on writes changes.
- **Whether location history becomes bed history.** Only if the crop rotation work (nolte/kamerplanter-goose#47) defines a contract; until then the lines are labelled "location, not bed".
- **Whether five plants is the right cap for a season.** Taken from the daily check, not measured against a garden's size.
