# Care Planning and the Daily Garden Check

Status: draft
Portfolio-Scope: local

## Context

A garden holds many small questions at once: which plants are due something, which look wrong, which need nothing. Each domain in this repository answers one of them for one plant: [the nutrient process](../nutrient-imbalance-detection/en.md) says which direction a nutrient imbalance runs, [the pest process](../pest-pressure-assessment/en.md) says whether a pest candidate survives its tests. Nothing yet puts those answers next to each other, says which one a person should look at first, and says plainly when there is nothing to do. This spec specifies that layer, care planning, and the recipe that runs it every day, the daily garden check.

The layer decides nothing about a plant. It reads what the garden context and the domain processes already returned, keeps observation, recommendation and mutation apart, orders the recommendations, and refuses to produce an action where the evidence about the present state is missing. A person reads the result; nothing is applied.

Everything about the tool surface is quoted from [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md), measured against the reference instance on 2026-08-16 and not re-measured for this spec: the Kamerplanter MCP server was unreachable (`INVALID_CONFIG`) when this spec was written. The shapes of the existing domain reports were read from `.claude/skills/nutrient-imbalance-assess/SKILL.md` (§5 Report) and `.claude/skills/pest-pressure-assess/SKILL.md` (§5 Report); neither returns a structured finding today, which is why section C maps them. The watering and fertilisation decisions return findings in this shape themselves ([their spec](../watering-and-fertilization-decisions/en.md), section F), and so do the growth-stage and weather assessments ([their spec](../growth-stage-and-weather-impact/en.md), section F) and the plant health assessment and the IPM plan ([their spec](../plant-health-and-ipm-planning/en.md), section G). No spec in this repository records the response fields of `get_due_care_tasks` (a search of `spec/`, `docs/` and `recipes/` finds the tool's name and no field), which is why section D computes no overdue interval.

Boundaries: [the garden decision policy](../garden-decision-policy/en.md) owns the evidence levels, the six rules and the shape of a recommendation, and the garden context block; this spec applies them and states no level of its own. [The plant planning spec](../plant-planning-and-planting-calendar/en.md) owns the plan this layer may read (its consumer table names care planning). [The nutrient](../nutrient-imbalance-detection/en.md) and [pest](../pest-pressure-assessment/en.md) processes keep their own ladders and refusal thresholds; this layer does not re-rank them.

Readers: authors of garden skills and recipes in this repository, the authors of the watering, fertilisation, health and weather domains that will plug into this layer, and anyone reading a daily check before acting on it.

## Goals

- A reader gets one ordered list of what to look at, each item saying what it rests on, how sure it is and what would change it
- An observation, a recommendation and a mutation are never confused: the reader can tell what was read, what is proposed and what would change state
- A state with no evidence about it yields no action, and the result says what observation would supply it
- A domain plugs in by returning findings in one shape, and a domain that does not exist yet is reported as not available, never replaced
- The daily check duplicates no domain logic and calls no state-changing tool

## Non-Goals

- The domains themselves. Watering and fertilisation are specified in [the watering and fertilisation decisions spec](../watering-and-fertilization-decisions/en.md), growth stage and weather in [the growth stage and weather impact spec](../growth-stage-and-weather-impact/en.md), plant health and pest management in [the plant health and IPM planning spec](../plant-health-and-ipm-planning/en.md)
- Applying anything: no `-apply` recipe, no apply contract. The issue asks for none, and "no mutation occurs without explicit apply steps" is met by shipping none
- Measuring the tool surface live. Claims about it cite the server spec and say they are not re-measured
- Computing an overdue interval for a care task. The response shape of `get_due_care_tasks` is not recorded (section D)
- Checking every plant of a garden each day (section F)

## Requirements

### A. Inputs

- **MUST** take the garden context block from `garden-context` as given, and **MUST** report a field the block marks absent as absent, never fill it
- **MAY** take the plan document of `plant-planning`, of which it reads, per run, the run identifier, the species key, the cultivar key, the method, the windows and the confidence (the consumer table of the plan spec), and **MUST** treat a plan that was not supplied as absent, not as "no planting runs"
- **MUST** take the domain findings as given (section C), **MUST** report a domain that returned nothing as absent with the reason, and **MUST NOT** substitute general knowledge for one

### B. Observation, recommendation, mutation

- **MUST** give every item exactly one kind: an observation (what a tool or document said, with its source and retrieval time), a recommendation (a proposal to a person) or a mutation (the next requirement)
- **MUST** give every recommendation the four blocks of the decision policy (evidence, confidence, uncertainty, missing data), and **MUST NOT** return a recommendation without them
- **MUST** name a mutation only as the state-changing tool a later apply step would call, with the item that justifies it, and **MUST NOT** call it, schedule it, or phrase a recommendation as an instruction to a device or a write

### C. The plug-in contract

- **MUST** define a finding as: the domain, the subject (a plant key or the garden), the kind (observation or recommendation), the statement, the evidence entries (level, source, retrieved-at), the confidence, what would change it, the missing data, and, optionally, the consequence (what happens if nothing is done, in the domain's own words)
- **MUST NOT** add to a finding a field the domain did not return, and **MUST** leave the consequence absent unless the domain stated one
- **MUST** map the reports of the two domains that do not return this shape, `nutrient-imbalance-assess` and `pest-pressure-assess`, into findings, **MUST** take the findings of the watering and fertilisation decisions, of the growth-stage and weather assessments and of the plant health assessment and the IPM plan as they return them, **MUST** read the evidence levels of the mapped reports from the table "How the existing ladders relate" in the decision policy, and **MUST NOT** assign a level where that table gives none (the nutrient tier 2 and symptoms read from an image)
- **MUST** carry the plant health assessment's finding as the observation it is, which cites the other domains' findings by domain, **MUST**, for a plant the IPM plan ran for, carry the `pest-pressure-assess` result as an observation only (the candidate, the tier, the tests) and take every measure, monitoring and treatment alike, only from the IPM findings, and **MUST NOT** count a domain's finding a second time through either; for a plant the IPM plan did not run for, the pest report is mapped as above
- **MUST** treat a nutrient or pest result that its owning process leaves with an undetermined direction, as a suspicion or below its refusal threshold, as an observation and not as a recommendation
- **MUST** report each domain named in the Non-Goals as not available, naming the skill that would provide it, until that skill exists, and **MUST NOT** substitute another domain's result

### D. Prioritisation

- **MUST** order the action items by urgency (`now`, `soon`, `routine`, `watch`), then by confidence, higher evidence level first, then by subject key, then by domain, so that the order is a total order on content
- **MUST** derive urgency only from stated fields: `now` when the finding's consequence states harm that is present or advancing, `soon` when it states harm that follows if nothing is done, `routine` for a recommendation with no stated consequence and for a due care task, and `watch` for an observation
- **MUST NOT** derive urgency from general knowledge, from how long a reminder has been due, or from a due task alone beyond `routine`
- **MUST** derive confidence from the highest decision-policy level that supports the item, never from how sure its statement reads, and **MUST** say that no level applies when none does

### E. Insufficient evidence

- **MUST NOT** generate an action for the present state of a plant or the garden without evidence about that state, and **MUST** list it under "no action, evidence insufficient" with the observation that would supply it
- **MUST** carry a due care task as a request from the schedule and not as a measurement, and **MUST NOT** recommend an action solely because it is due
- **MUST** allow "no action" as the result of the whole run, and **MUST NOT** pad a plan to look useful

### F. The daily check

- **MUST** be an orchestration entry point that runs the garden context, then each domain that is available, then the decision policy and the care layer, and **MUST NOT** duplicate a domain's logic in the recipe
- **MUST** take a `plants` parameter, comma-separated plant keys, empty by default: empty runs the garden level only (due tasks and planting runs from the garden context), and given runs the nutrient, pest, watering, fertilisation, growth-stage, weather, plant health and IPM checks for those plants
- **MUST** take a `weather` parameter, the caller's weather and forecast, empty by default, hand it to the weather assessment marked `caller`, and **MUST NOT** read weather from any other source (section H)
- **MUST** check at most five plants and report the rest as not checked with the reason, and **MUST NOT** call a per-plant tool for every plant of the garden
- **MUST** list each domain with a status of checked, not available (naming the skill) or not checked (naming why), and **MUST NOT** leave a domain out
- **MUST** report a tool error verbatim and continue with the rest
- **MUST** close with a fixed report and a machine-readable final line stating the number of actions, the number of items with no action, and the garden slug

### G. Determinism

- **MUST** make the care plan facts a function of the supplied blocks and findings, so that two runs over the same input give the same facts in the same order
- **MUST NOT** read the current date inside the care plan facts; retrieval times are reported beside the facts and are not compared
- **MUST** state that byte-identical prose outside the care plan facts is not claimed, and that the property is checked on a fixed fixture of input blocks written out as text

### H. Separation

- **MUST NOT** call a state-changing tool from the skill or the recipe, and **MUST** name every state-changing tool the server spec lists, individually, in the recipe's prompt as forbidden
- **MUST NOT** call a Home Assistant tool
- **MUST NOT** ship an `-apply` sibling of the recipe and **MUST NOT** invent an apply contract
- **MUST** keep the skill tool-free: it works only on the blocks and findings it is handed

## Acceptance Criteria

- [ ] Every item of a care plan has exactly one kind, and no mutation is called, scheduled or phrased as an instruction
- [ ] Every recommendation carries evidence, confidence, uncertainty and missing data, and none is returned without them
- [ ] A finding has the fields of section C and no field the domain did not return; the consequence is absent unless the domain stated one
- [ ] The nutrient and pest reports are mapped into findings with levels taken from the decision policy's table, and no level is assigned where the table gives none, and the watering and fertilisation decisions, the growth-stage and weather assessments and the plant health assessment and IPM plan are taken as the findings they return
- [ ] A suspicion or an undetermined direction is an observation, not a recommendation
- [ ] The plant health finding is an observation, and where the IPM plan ran the pest result is an observation whose measures come only from the IPM findings, so no domain's finding is counted twice
- [ ] Each domain named in the Non-Goals is reported as not available with the skill that would provide it, and none is replaced by another
- [ ] The order is urgency, then confidence, then subject key, then domain, and does not change when the order of the input changes
- [ ] Urgency comes only from a stated consequence, a due task or an observation, and never from general knowledge or the age of a reminder
- [ ] A state with no evidence about it yields no action and appears under "no action, evidence insufficient" with the observation that would supply it
- [ ] A due care task is carried as a request from the schedule, and no action rests on its being due alone
- [ ] The daily check with no `plants` runs the garden level only, with a plant list checks at most five and names the rest as not checked
- [ ] The daily check lists every domain with its status and closes with the machine-readable final line
- [ ] The daily check takes weather only from its `weather` parameter
- [ ] Two runs over the same input blocks give the same care plan facts on a fixed fixture, and the result says what is not claimed
- [ ] Neither the skill nor the recipe calls a state-changing tool or a Home Assistant tool, and the recipe's prompt forbids every state-changing tool by name
- [ ] No `-apply` recipe and no apply contract ships with this change
- [ ] Every claim about the tool surface cites a spec in this repository, and a claim not re-measured says so
- [ ] The German and the English file have the same headings in the same order, the same number of requirement bullets and the same number of acceptance checkboxes

## Source

- [The garden decision policy](../garden-decision-policy/en.md) — the evidence levels, the six rules, the recommendation output, the garden context block, and the table "How the existing ladders relate"
- [The plant planning and planting calendar spec](../plant-planning-and-planting-calendar/en.md) — the plan document and its consumer table, where care planning is named
- [The nutrient imbalance detection spec](../nutrient-imbalance-detection/en.md) — the nutrient ladder, its refusal threshold, and the tier 2 rule (dose amounts needed; merged in nolte/kamerplanter-goose#64)
- [The pest pressure assessment spec](../pest-pressure-assessment/en.md) — the pest ladder and its falsification tests
- [The Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) — the tool catalog and the state-changing tools, measured 2026-08-16
- [The recipe project pattern](../../goose/recipe-project-pattern/en.md) — how a recipe is built here, including the forbidden-by-name rule
- [The watering and fertilisation decisions spec](../watering-and-fertilization-decisions/en.md) — the two domains that return findings in this shape
- [The growth stage and weather impact spec](../growth-stage-and-weather-impact/en.md) — the growth-stage and weather assessments, which return findings in this shape
- [The plant health and IPM planning spec](../plant-health-and-ipm-planning/en.md) — the plant health assessment and the IPM plan, which return findings in this shape
- Issue nolte/kamerplanter-goose#43 — the scope and the five acceptance criteria are taken from its body; #44, #45, #48 and #49 — the domains that plug in; #39 — the audit
- The audit for nolte/kamerplanter-goose#39 (2026-11-06) kept care planning as one skill, `care-planning`, an aggregator over the plant-care results that reads no garden; the garden context stays with `garden-context`

## Open Questions

- **Whether the domain skills need an explicit urgency field in the plug-in contract.** Urgency is derived here from the stated consequence. The watering and fertilisation decisions leave the consequence absent unless an input states one, and no input does today, so their recommendations rank `routine`; whether a consequence can be stated for them in one shape is open until a domain does.
- **How the nutrient tier 2 rule shows up as confidence in a care item.** Tier 2 needs recorded dose amounts and carries no decision-policy level (section C), so a care item resting on it says that no level applies. Whether that is the right place for it is open.
- **The response fields of `get_due_care_tasks`.** No spec here records whether a task carries a due date or an interval, so no overdue computation is specified and a due task is `routine` at most. A measurement against a reachable instance would settle it.
- **Whether five plants is the right cap.** The number is chosen to bound the per-plant calls, not measured against a garden's size or the server's limits.
