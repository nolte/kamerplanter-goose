# Watering and Fertilisation Decisions

Status: draft
Portfolio-Scope: local

## Context

Two questions come up for every plant that is tended through this repository: should it be watered now, and should it be fed. Each has a tempting wrong answer. Watering because a reminder is due, or because an interval has elapsed, puts water on a plant whose present state nobody read. Feeding because a plant looks pale treats an undersupply that may be unavailability, an oversupply or a pH problem. This spec fixes what each decision may rest on, the closed set of answers it may give, what it must refuse, and what an `-apply` recipe for it may and may not write.

A decision here is a proposal to a person. It changes nothing, and it is made from blocks that other skills already collected.

Everything about the tool surface is quoted from [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md), measured against the reference instance on 2026-08-16 and not re-measured for this spec: the Kamerplanter MCP server was unreachable (`INVALID_CONFIG`) when this spec was written. Four facts the requirements rest on were read from the working copy rather than measured: the server spec lists twelve state-changing tools and none of them waters, doses or actuates (its "Write tools" and "Setup tool" tables); no spec, guide, skill or recipe records the value set of `reminder_type` (a search of `spec/`, `docs/`, `.claude/` and `recipes/` finds the field name and no value); the phase definition carries a `watering_interval_days` field ([the species baseline spec](../species-baseline-verification/en.md), its table of `list_phase_definitions`, and `.claude/skills/plant-context-collect/SKILL.md` §4); and no plant-to-entity mapping for Home Assistant sensors is recorded ([the nutrient spec](../nutrient-imbalance-detection/en.md), Open Questions).

Boundaries: [the garden decision policy](../garden-decision-policy/en.md) owns the evidence levels, the six rules and the shape of a recommendation, and names the question "a watering interval" as one that the owning process decides; this spec is that process for watering and fertilising, and states no level of its own. [The nutrient imbalance detection spec](../nutrient-imbalance-detection/en.md) owns the direction of a nutrient problem, the evidence ladder and the rule that tier 2 needs recorded dose amounts; the fertilisation decision consumes its report and does not re-derive it. [The care planning spec](../care-planning-and-daily-check/en.md) owns the plug-in shape of a finding and the daily check that runs these decisions. [The recipe project pattern](../../goose/recipe-project-pattern/en.md) owns how a recipe is built, including forbidden-by-name.

Readers: authors of garden skills and recipes in this repository, the people who run the decisions and read their results, and anyone reviewing an `-apply` recipe before it writes.

## Goals

- A watering result says what it rests on about the plant's present state, and says plainly when there is nothing
- A fertilisation result says which of insufficient nutrition, an environmental cause and an uncertain diagnosis it rests on, and "do not feed" is an ordinary answer
- No concentration, dose, mixing order or measurement appears that no tool returned
- A due reminder is never a reason to water
- An `-apply` recipe records what a person did and cannot be mistaken for something that waters or feeds

## Non-Goals

- Plant health and pest management (nolte/kamerplanter-goose#48), growth stage and weather (#49)
- Actuating anything: no irrigation, no dosing pump, no Home Assistant device. A decision is a proposal to a person
- Changing the nutrient process: its direction, its ladder and its tier rule stay where they are
- Computing a watering or feeding schedule
- Measuring the tool surface live. Claims about it cite the server spec and say they are not re-measured

## Requirements

### A. Inputs

- **MUST** take the plant context block from `plant-context-collect`, the read report and measurements from `diary-measurements-read` and the garden context block from `garden-context` as given, and **MUST NOT** call a tool to fetch what one of them already holds
- **MUST** accept only the facts the server has no source for as caller-supplied, marked `caller`: weather and forecast, the container or bed, irrigation constraints, user constraints, the EC of the water source, and the tank and dosing state
- **MUST** report each absent input as absent with its reason, `no source` or `not collected`, and **MUST NOT** fill it
- **MUST NOT** use a Home Assistant sensor as evidence about a plant, because no mapping from a sensor to a plant is recorded

### B. The watering decision

- **MUST** return exactly one of `water now`, `wait` and `insufficient evidence`
- **MUST** return `water now` only with evidence about the plant's present state, and **MUST** name that evidence in the result: a recent measurement in a diary entry of this plant counts as level 1
- **MUST** read the care log's confirmed reminders and their intervals as level 3, and the phase definition's `watering_interval_days` and the species and phase requirements as level 4 priors that **MUST NOT** decide alone
- **MUST NOT** return `water now` because a reminder is due, because an interval or a schedule has elapsed, or because the plant is expected to be dry (rule 2 of the decision policy)
- **MUST** return `insufficient evidence` when nothing is known about the plant's present state, and **MUST** name the observation that would supply it
- **MUST NOT** fabricate a missing measurement, and **MUST NOT** read soil moisture from a `measurements` key whose meaning or unit is ambiguous
- **MUST** give every result its evidence, confidence, uncertainty and missing data, as the decision policy requires

### C. The fertilisation decision

- **MUST** return exactly one of `feed`, `do not feed` and `insufficient evidence`
- **MUST** take the nutrient report as given, and **MUST NOT** re-derive, re-rank or override its direction or its tier rule
- **MUST** return `feed` only when the nutrient process has established undersupply as a direction and no environmental cause is named
- **MUST** return `do not feed` when the direction is oversupply or unavailability at adequate supply, or when an environmental cause is named (rule 5 of the decision policy), and **MUST** treat it as an ordinary result
- **MUST** return `insufficient evidence` when the nutrient process leaves the direction undetermined or at a suspicion
- **MUST** say which of insufficient nutrition, an environmental cause and an uncertain diagnosis the result rests on
- **MUST** take recent fertilisation from the care log as confirmed reminders, which carry no amount, and **MUST NOT** state an amount the record does not hold
- **MUST** prefer the conservative result when the evidence is incomplete

### D. Safety

- **MUST NOT** state a concentration, a dose or a mixing order except as the result of `calculate_mixing_protocol`, which works on EC-net, and **MUST** state the base-water assumption when it is called
- **MUST** report the dose as unknown when that result is absent
- **MUST NOT** invent a concentration or a measurement

### E. Separation and the apply contract

- **MUST** keep the decision skills and the read-only recipes free of any state-changing tool and any Home Assistant tool
- **MUST** have an `-apply` recipe take a decision a person approved and the action the person carried out, write a record of that action and nothing else, and refuse when either is missing
- **MUST** have `watering-decision-apply` call only `confirm_care_task`, with the `plant_key` and the `reminder_type` the caller supplies, and **MUST NOT** guess the `reminder_type`
- **MUST** have `fertilization-decision-apply` call only `record_feeding_event`, with the `plant_key`, `volume_applied_liters` and only the other values the person supplied, and **MUST** read the names of the optional inputs from the tool's own schema at run time and invent none
- **MUST** call the tool with `dry_run` true first and report the planned effect, and then call it with an `idempotency_key`
- **MUST** name exactly its one tool as permitted by name and every other state-changing tool as forbidden by name, and **MUST NOT** call a Home Assistant tool
- **MUST NOT** claim that a plant was watered or fed, **MUST** state that the effect is a record, and **MUST** state that whether any read tool returns recorded feeding events is not measured (nolte/kamerplanter-goose#54)

### F. The plug-in shape

- **MUST** return, besides the decision, findings in the shape the care planning spec defines in its section C
- **MUST** give `water now` and `feed` as recommendations, and `wait`, `do not feed` and `insufficient evidence` as observations
- **MUST** leave the consequence of a finding absent unless an input states one

### G. Determinism

- **MUST** make the decision a function of the supplied blocks, so that two runs over the same blocks give the same decision, evidence levels and missing-data list
- **MUST NOT** read the current date inside the decision facts; retrieval times are reported beside the facts and are not compared
- **MUST** state that byte-identical prose outside the decision facts is not claimed, and that the property is checked on a fixed fixture of input blocks written out as text

### H. What does not exist

- **MUST NOT** assume a tool that waters, doses or actuates: none is measured

## Acceptance Criteria

- [ ] A watering result is one of `water now`, `wait` and `insufficient evidence`, and a fertilisation result is one of `feed`, `do not feed` and `insufficient evidence`
- [ ] `water now` names evidence about the plant's present state, and no result rests on a due reminder, an elapsed interval or a schedule alone
- [ ] A phase's `watering_interval_days`, the species data and the phase requirements are read as priors and decide nothing alone
- [ ] A missing measurement is reported missing, and no soil moisture is read from an ambiguous `measurements` key
- [ ] Every result carries evidence, confidence, uncertainty and missing data
- [ ] The fertilisation decision takes the nutrient report as given and does not re-derive its direction or its tier rule
- [ ] `feed` appears only with an established undersupply and no named environmental cause, and `do not feed` is returned for oversupply, unavailability and a named environmental cause
- [ ] The result says which of insufficient nutrition, an environmental cause and an uncertain diagnosis it rests on
- [ ] No concentration, dose or mixing order appears except from `calculate_mixing_protocol`, with the base-water assumption stated, and an absent result gives an unknown dose
- [ ] No Home Assistant sensor is used as evidence, and no input without a source is filled
- [ ] The decision skills and the read-only recipes call no state-changing tool and no Home Assistant tool
- [ ] Each `-apply` recipe takes an approved decision and the action carried out, refuses without them, writes only its one tool's record and names every other state-changing tool as forbidden
- [ ] `watering-decision-apply` never guesses a `reminder_type`, and `fertilization-decision-apply` passes no input the person did not supply
- [ ] Each `-apply` recipe calls `dry_run` first, reports the planned effect, then calls with an `idempotency_key`
- [ ] No `-apply` recipe claims that a plant was watered or fed, and each states that the effect is a record and that the read-back of feeding events is not measured
- [ ] Each decision returns findings in the care planning plug-in shape, with `water now` and `feed` as recommendations and the other results as observations
- [ ] Two runs over the same input blocks give the same decision facts on a fixed fixture, and the result says what is not claimed
- [ ] Every claim about the tool surface cites a spec in this repository, and a claim not re-measured says so
- [ ] The German and the English file have the same headings in the same order, the same number of requirement bullets and the same number of acceptance checkboxes

## Source

- [The garden decision policy](../garden-decision-policy/en.md) — the evidence levels, the six rules, the recommendation output and the garden context block
- [The nutrient imbalance detection spec](../nutrient-imbalance-detection/en.md) — the direction, the ladder, the tier 2 rule (dose amounts needed; merged in nolte/kamerplanter-goose#64) and the open question on sensors
- [The care planning and daily check spec](../care-planning-and-daily-check/en.md) — the plug-in shape and the daily check
- [The species baseline verification spec](../species-baseline-verification/en.md) — the phase definition fields, including `watering_interval_days`
- [The Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) — the tool catalog, the write tools, `dry_run` and `idempotency_key`, measured 2026-08-16
- [The recipe project pattern](../../goose/recipe-project-pattern/en.md) — how a recipe is built here, including forbidden-by-name
- Issues nolte/kamerplanter-goose#44 and #45 — the scope and the acceptance criteria are taken from their bodies; #54 — the read-back of feeding events; #59 — the apply half that was split from planning for the same reason

## Open Questions

- **The value set of `reminder_type` and which value is watering.** No file here records it, so the caller supplies it. A read-only call to the care log of a reachable instance would show the values in use.
- **The input names of the optional fields of `record_feeding_event`.** The server spec records them only as amount, EC and pH before and after, and runoff. The recipe reads them from the tool's own schema at run time.
- **Whether feeding events are read back (nolte/kamerplanter-goose#54).** It decides whether a record written by `fertilization-decision-apply` ever reaches tier 2 of the nutrient ladder.
- **The source of weather and forecast.** There is none in the measured catalog; until there is, only the caller can supply them.
- **Which `measurements` key carries soil moisture.** The field has no fixed key set, and the nutrient spec's normalisation applies; no key is established here.
- **What `watering_interval_days` counts and whether the species carries a water demand.** The phase definition carries the field; this spec does not establish what it counts, and no species water-demand field is recorded. It is read as a level 4 prior and decides nothing alone.
