# Growth Stage and Weather Impact

Status: draft
Portfolio-Scope: local

## Context

Two questions sit under almost every other judgement about a plant: is it where its record says it is in its development, and what is the weather doing to it. Each has a tempting wrong answer. A growth stage read off the recorded phase alone repeats whatever was entered weeks ago, and a stage computed from accumulated warmth alone places a plant from a number nobody checked against the plant. A weather reading turned into a plant symptom ("the frost damaged the leaves") reports as observed what was only an exposure. This spec fixes what a growth-stage assessment and a weather-impact assessment may rest on, the closed set of answers each may give, how the three derived quantities (growing degree days, vapour pressure deficit, photoperiod) are computed and what they may not decide, and how a weather exposure is kept apart from a plant symptom.

An assessment here is a statement to a person. It changes nothing, and it is made from blocks that other skills already collected, plus at most two phase reads and one optional Home Assistant read named below.

Everything about the tool surface is quoted from [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md), measured against the reference instance on 2026-08-16, and from [the Home Assistant MCP server spec](../../mcp/home-assistant-mcp-server/en.md), measured on 2026-08-04; neither was re-measured for this spec: the Kamerplanter MCP server was unreachable (`INVALID_CONFIG`) when this spec was written. Six facts the requirements rest on were read from the working copy rather than measured: the server spec's 44 read tools include no weather or forecast tool (its "Read tools" section); `get_plant_phase_status` can answer `phase_state: unresolved`, which reads as a normal result and is not (its signature table), and `plant-context-collect` does not call it (`.claude/skills/plant-context-collect/SKILL.md` §2 and §4); no spec records the response fields of `get_plant_phase_history` (a search of `spec/` finds the tool's name in catalog and table rows only); the species record carries `base_temp_gdd`, measured 5.0 for leek and 15.0 for the peace lily, and the cultivar carries `days_to_maturity` in days ([the species baseline spec](../species-baseline-verification/en.md)); no spec records a photoperiod-sensitivity field or a GDD target for a stage or for maturity (a search of `spec/` for "photoperiod" and "GDD" finds neither); and whether Home Assistant exposes any weather entity is unmeasured ([the garden decision policy](../garden-decision-policy/en.md), level 6).

Boundaries: [the garden decision policy](../garden-decision-policy/en.md) owns the evidence levels, the six rules and the shape of a recommendation; weather is its level 6, and it ranks sources, not derivations, so a derivation here carries no level. This spec states no level of its own. [The care planning spec](../care-planning-and-daily-check/en.md) owns the plug-in shape of a finding and the daily check that runs these assessments. [The species baseline spec](../species-baseline-verification/en.md) owns the plausibility of the species record these assessments read, including the warning about a tropical species with a temperate base temperature. `plant-context-collect` owns the plant context block, and `plant-lifecycle-resolve` the lifecycle windows; neither is changed here. [The recipe project pattern](../../goose/recipe-project-pattern/en.md) owns how a recipe is built, including forbidden-by-name, and the Home Assistant server spec owns the rules for its tools.

Readers: authors of garden skills and recipes in this repository, the authors of the plant health (nolte/kamerplanter-goose#48) and harvest (#50) domains that will read these results, and the people who run the assessments and read them before acting.

## Goals

- A growth-stage result says whether the recorded stage matches what is known about the plant, with its evidence and confidence, and says plainly when nothing is known
- Growing degree days, vapour pressure deficit and photoperiod are used when their inputs exist, and reported absent with the reason when they do not
- A weather effect is an exposure or an expected risk, never a symptom of the plant, and a symptom is never read off the weather
- Uncertainty is explicit: what each result does not know, and what would change it
- The results plug into the care plan and hand named fields to the plant health and harvest domains

## Non-Goals

- Plant health and pest management (nolte/kamerplanter-goose#48) and harvest planning (#50), beyond the hand-off fields named in section F
- Changing the recorded phase: no `-apply` recipe. A questionable stage names the mutation a later apply step would call and calls nothing
- A weather backend, a mapping from a Home Assistant sensor to a plant, or a table of GDD targets per stage: none has a source
- Re-ranking the decision policy's levels, including for questions where weather decides (Open Questions)
- Measuring the tool surface live. Claims about it cite the server specs and say they are not re-measured

## Requirements

### A. Inputs

- **MUST** take the plant context block from `plant-context-collect` as given and **MUST NOT** call a tool to fetch what it already holds; **MAY** take the read report and measurements from `diary-measurements-read`, the findings of `plant-photo-read`, the lifecycle report of `plant-lifecycle-resolve` and the garden context block from `garden-context` as given
- **MUST** accept as caller-supplied, marked `caller`, only facts the server has no source for: weather and forecast, a daily temperature series, the latitude, an indoor light schedule, where the plant stands (outdoors, sheltered, indoors), the person's own observation of the plant, and the assessment date
- **MUST** take the assessment date from the caller or, without one, from the recorded date of the newest observation used, and **MUST NOT** read the current date
- **MUST** report each absent input as absent with its reason, `no source` or `not collected`, and **MUST NOT** fill it

### B. The growth stage

- **MUST** call `get_plant_phase_status` for the plant and **MUST** report `phase_state: unresolved` as an absent recorded stage, never as a normal one
- **MAY** call `get_plant_phase_history` for the plant, and **MUST** report its response as returned, assuming no field name
- **MUST** return exactly one of `recorded stage consistent`, `recorded stage questionable` and `insufficient evidence`
- **MUST** carry a `direction` of `ahead`, `behind` or `unclear` on `recorded stage questionable`, and no direction on the other two
- **MUST** rest `recorded stage consistent` and `recorded stage questionable` on an observation of the plant's present development at level 1 to 3, or on a photo reading corroborated by a timing expectation, and **MUST** name that observation
- **MUST** read the phase's `typical_duration_days`, the species month windows, the cultivar's `days_to_maturity` and the lifecycle windows as level 4 timing expectations that **MUST NOT** decide alone, and a photo reading as a reading with no level that **MUST NOT** decide alone
- **MUST** return `insufficient evidence` when the recorded stage is absent, when no observation of the present development exists, or when only priors, derivations or an uncorroborated photo reading speak to it, and **MUST** name the observation that would supply it
- **MUST** name `transition_plant_phase` as the mutation a later apply step would call for a questionable stage, with a target phase only where the evidence names one, and **MUST NOT** call it
- **MUST** give every result its evidence, confidence, uncertainty and missing data, as the decision policy requires

### C. Derivations

- **MUST** compute growing degree days only from a caller-supplied daily minimum and maximum series with its unit and the species' `base_temp_gdd`, state the method and the span the series covers, and report them absent with the reason when either input is missing
- **MUST NOT** compute growing degree days from a single reading, a Home Assistant snapshot or a forecast, and **MUST NOT** place a stage from accumulated growing degree days alone, since no GDD target for a stage or for maturity is recorded
- **MUST** compute vapour pressure deficit only from a temperature and a relative humidity taken at the same time and place, state the formula, refuse a `measurements` key whose meaning or unit is ambiguous, and report the value without judging it against a target none of the sources records
- **MUST** compute photoperiod outdoors only from a caller-supplied latitude and the assessment date, and indoors only from the caller's light schedule, and **MUST** report the species' response to day length as `no source`
- **MUST** give each derivation `no level`, and **MUST** state that `search_glossary` supplies definitions, not evidence

### D. Weather impact

- **MUST** take weather and forecast from the caller, marked `caller`, and **MAY**, where the recipe permits it, read a weather entity through Home Assistant's `GetLiveContext` if that tool is present, reported as `home_assistant (unmeasured)`
- **MUST** report each of temperature extremes, rainfall, wind, humidity, heat and cold events, and forecast changes as exactly one of `exposure`, `no exposure in the supplied data` and `no source`
- **MUST** report every factor as `no source` when neither source supplied data, and **MUST** say what the assessment cannot conclude
- **MUST** report a disagreement between the caller and Home Assistant as a contradiction with both sources side by side, and **MUST NOT** average them
- **MUST** read weather as level 6, and **MUST** state the threshold an exposure is judged against with its source and level, or say that no threshold is recorded and the impact is not assessed
- **MUST** name, for each exposure, the area it is likely to affect (care, health or harvest timing) and **MUST** make it conditional on where the plant stands when the caller did not say
- **MUST NOT** use a Home Assistant entity of any other domain, or any sensor, as evidence about a plant

### E. Separation of exposure and symptom

- **MUST** state a weather effect as an exposure or an expected risk, and **MUST NOT** state it as a symptom of the plant or as evidence about the plant's present state
- **MUST** take a symptom only from `plant-photo-read`, a diary entry or a recorded inspection, and **MUST** report symptoms in a block of their own
- **MUST** link a symptom to an exposure only as "consistent with", which is a suspicion under rule 1 of the decision policy and never a diagnosis

### F. Plug-in shape and hand-off

- **MUST** return, besides the result, findings in the shape the care planning spec defines in its section C
- **MUST** give `recorded stage questionable` and an exposure judged against a recorded threshold for a plant the caller places outdoors or sheltered as recommendations, and every other result as an observation
- **MUST** leave the consequence of a finding absent unless an input states one
- **MUST** return a hand-off block for harvest planning holding the recorded and estimated stage, the result and its direction, the days in the phase against `typical_duration_days`, the days since `planted_on` against the cultivar's `days_to_maturity`, the accumulated growing degree days with their inputs, and the photoperiod, each absent with its reason where it is
- **MUST** return a hand-off block for plant health holding the exposures and, separately, the symptoms with any "consistent with" link

### G. Determinism

- **MUST** make each result a function of the supplied blocks, the reads named in section B and the snapshot named in section D, so that two runs over the same input give the same result, direction, factor statuses, evidence levels and missing-data list
- **MUST NOT** read the current date inside the facts; retrieval times are reported beside the facts and are not compared
- **MUST** state that byte-identical prose outside the facts is not claimed, and that the property is checked on a fixed fixture of input blocks written out as text

### H. Separation and forbidden tools

- **MUST** keep both skills and both recipes free of every state-changing tool, and **MUST** name all twelve that the Kamerplanter server spec lists, individually, in each recipe's prompt as forbidden
- **MUST** forbid Home Assistant actuation by category in the weather recipe's prompt (turning a device on or off, setting a value, running a script, scene or automation), and **MUST NOT** call `TimeTillErnte` or `time_till`, whose effect is unclassified
- **MUST NOT** call a Home Assistant tool from the growth-stage skill or recipe, or from the daily check
- **MUST NOT** ship an `-apply` sibling of either recipe

## Acceptance Criteria

- [ ] A growth-stage result is one of `recorded stage consistent`, `recorded stage questionable` and `insufficient evidence`, and a questionable one carries a direction of `ahead`, `behind` or `unclear`
- [ ] Every growth-stage result carries evidence and confidence, and a consistent or questionable one names the observation of the present development it rests on
- [ ] An unresolved phase is reported as an absent recorded stage, and the phase history is reported as returned
- [ ] No stage is placed from accumulated growing degree days, a timing expectation or an uncorroborated photo reading alone
- [ ] Growing degree days, vapour pressure deficit and photoperiod are computed when their inputs are supplied, carry `no level`, and are reported absent with the reason otherwise
- [ ] Each weather factor is one of `exposure`, `no exposure in the supplied data` and `no source`, and with no source every factor is `no source` and the result says what cannot be concluded
- [ ] A Home Assistant weather reading is labelled `home_assistant (unmeasured)`, and a disagreement with the caller is reported side by side, not averaged
- [ ] Weather effects appear as exposures in a block separate from plant symptoms, and a link between them reads "consistent with"
- [ ] Every result states its uncertainty and its missing data
- [ ] Each result returns findings in the care planning plug-in shape, plus the named hand-off blocks for plant health and harvest planning
- [ ] A questionable stage names `transition_plant_phase` as a mutation, and nothing calls it
- [ ] Two runs over the same input give the same facts on a fixed fixture, and the result says what is not claimed
- [ ] Neither skill nor recipe calls a state-changing tool, each recipe's prompt forbids all twelve by name, the weather recipe forbids actuation by category and `TimeTillErnte` and `time_till`, and the growth-stage recipe calls no Home Assistant tool
- [ ] Every claim about the tool surface cites a spec in this repository, and a claim not re-measured says so
- [ ] The German and the English file have the same headings in the same order, the same number of requirement bullets and the same number of acceptance checkboxes

## Source

- [The garden decision policy](../garden-decision-policy/en.md) — the evidence levels, weather as level 6, the six rules, derivations carrying no level, and the open question on a global ranking
- [The care planning and daily check spec](../care-planning-and-daily-check/en.md) — the plug-in shape and the daily check
- [The species baseline verification spec](../species-baseline-verification/en.md) — `base_temp_gdd`, `days_to_maturity`, the phase definition fields and the three-source rule
- [The plant health image analysis spec](../plant-health-image-analysis/en.md) — the open question on GDD without a temperature history
- [The watering and fertilisation decisions spec](../watering-and-fertilization-decisions/en.md) — weather as a caller-supplied input, and no Home Assistant sensor as evidence about a plant
- [The Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) — the tool catalog, `get_plant_phase_status`, `get_plant_phase_history` and the state-changing tools, measured 2026-08-16
- [The Home Assistant MCP server spec](../../mcp/home-assistant-mcp-server/en.md) — `GetLiveContext`, the actuation rule and the unclassified `TimeTillErnte` and `time_till`, measured 2026-08-04
- [The recipe project pattern](../../goose/recipe-project-pattern/en.md) — how a recipe is built here, including forbidden-by-name
- Issue nolte/kamerplanter-goose#49 — the scope and the five acceptance criteria are taken from its body; #48 and #50 — the domains that read the hand-off blocks

## Open Questions

- **The source of weather and forecast.** The measured Kamerplanter catalog has none; until it does, the caller supplies them, and Home Assistant is a second, unmeasured source.
- **Whether Home Assistant exposes a weather entity, and its shape.** Unmeasured. A `GetLiveContext` call filtered to `domain: weather` against the reference instance would settle it; until then a reading is reported as returned.
- **A GDD target for a stage or for maturity.** No field records one, and the cultivar's maturity counts days. Until one exists, accumulated growing degree days are context and place no stage.
- **The unit of `base_temp_gdd`.** The measured values, 5.0 and 15.0, fit degrees Celsius; no spec records the unit. The assessment reads it as Celsius and says so.
- **A photoperiod-sensitivity field.** None is recorded on the two species probed. A `get_species_info` call on a short-day crop would show whether one exists.
- **The response fields of `get_plant_phase_history`.** Not recorded; one read call on a reachable instance would settle them, and until then the history is reported as returned.
- **Whether the ranking is global or per question for frost and heat.** The decision policy places species data above weather, and a frost is a question where weather decides; this spec does not re-rank and carries the question to [the decision policy](../garden-decision-policy/en.md).
- **Where a person's own observation of the plant sits.** It is read here as a confirmed observation, level 3, marked `caller`; whether a statement in a recipe parameter carries the weight of a recorded inspection is open, as the decision policy's open question on photo readings is.
- **The value set of `frost_sensitivity` and the shape of `stress_tolerance`.** Both fields are recorded as present and their values are not, so a threshold read from them is stated as read and its meaning is not assumed.
