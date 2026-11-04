# Harvest Readiness and Planning

Status: draft
Portfolio-Scope: local

## Context

"Is it ready?" is the question a grower asks most often near the end of a crop, and it has two tempting wrong answers. One reads the answer off the calendar: the species harvests in August, it is August, so the plant is ready. The other reads it off the plant's age: the cultivar matures in 75 days, 75 days have passed, so it is ready. Neither looks at the plant, and the second rests on a count whose starting point nobody recorded. A harvest plan across several plants adds three more temptations: a yield nobody measured, a storage limit nobody recorded, and a workload estimate nobody supplied. This spec fixes what a harvest-readiness judgement may rest on, the closed set of answers it may give, how a pre-harvest safety interval (Karenz) gates it, and how a harvest plan sequences plants and counts work without a source for yield, storage or effort.

A judgement here is a statement to a person. It changes nothing: nothing is harvested, recorded or scheduled. It is made from blocks that other skills already collected, plus at most two reads per plant named below.

Everything about the tool surface is quoted from [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md), measured against the reference instance on 2026-08-16, and from [the Home Assistant MCP server spec](../../mcp/home-assistant-mcp-server/en.md), measured on 2026-08-04; neither was re-measured for this spec: the Kamerplanter MCP server was unreachable (`INVALID_CONFIG`) when this spec was written. Six facts the requirements rest on were read from the working copy rather than measured: `get_harvest_readiness` is a read tool in the catalog (the server spec's "Care and tasks" row), it was called read-only on 2026-08-16, and its arguments and response fields are recorded nowhere (a search of `spec/`, `.claude/`, `recipes/` and `tests/` finds the name only in the catalog row and that Source line); `get_treatment` carries `safety_interval_days`, the pre-harvest Karenz (its signature table); the harvest write tools are specified upstream but unimplemented, and none is among the twelve state-changing tools (its Non-Goals and Requirements); no field for yield, harvest amount, storage or shelf life is recorded (a search of `spec/mcp` for "yield" and of `spec/` and `.claude/skills/` for "storage" finds none); no record of when a treatment was applied is described (the care log is described by `reminder_type` and `confirmed_at` only, [the nutrient imbalance detection spec](../nutrient-imbalance-detection/en.md)); and `TimeTillErnte` and `time_till` on the reference Home Assistant instance are unclassified custom intents.

Boundaries: [the garden decision policy](../garden-decision-policy/en.md) owns the evidence levels, the six rules and the shape of a recommendation; this spec states no level of its own. [The growth stage and weather impact spec](../growth-stage-and-weather-impact/en.md) owns the growth-stage result, the hand-off block for harvest planning (its section F) and the weather exposures; this spec consumes them as returned and does not restate their rules. [The plant planning and planting calendar spec](../plant-planning-and-planting-calendar/en.md) owns the harvest window rule and the prohibition on a harvest date from `days_to_maturity`. [The pest pressure assessment spec](../pest-pressure-assessment/en.md) owns which treatment a pest calls for; this spec reads only the safety interval of a treatment the caller says was applied. [The care planning spec](../care-planning-and-daily-check/en.md) owns the plug-in shape of a finding. [The recipe project pattern](../../goose/recipe-project-pattern/en.md) owns how a recipe is built, including forbidden-by-name.

Readers: authors of garden skills and recipes in this repository, the author of the garden and season review (its spec reads the results defined here), and the people who run a harvest check and read it before they pick.

## Goals

- A readiness result says whether a plant is ready, approaching, not ready, not harvestable or not known, with its evidence and confidence, and says plainly when nothing about the plant itself is known
- The calendar and the plant's age are used as expectations, never as the answer, and no harvest date is computed from a count whose starting point is unrecorded
- A pre-harvest safety interval blocks a harvest when the caller says a treatment was applied, and says it cannot be checked when the caller did not
- A harvest plan orders plants deterministically and counts the work it can count, without inventing a yield, a storage limit or an effort estimate
- Uncertainty is explicit: what each result does not know, and what would change it

## Non-Goals

- Recording a harvest, a yield or a treatment: no `-apply` recipe. Upstream lists the harvest write tools as specified but unimplemented, and none is in the measured catalog
- Recommending a treatment, or judging pest or disease pressure; that is [the pest pressure assessment](../pest-pressure-assessment/en.md), and plant health is nolte/kamerplanter-goose#48
- Judging the growth stage or the weather; that is [the growth stage and weather impact spec](../growth-stage-and-weather-impact/en.md)
- Integrating harvest readiness into the daily garden check
- A table of maturity indicators per species, a storage model or a yield model: none has a source
- Measuring the tool surface live. Claims about it cite the server specs and say they are not re-measured

## Requirements

### A. Inputs

- **MUST** take the plant context block from `plant-context-collect` as given and **MUST NOT** call a tool to fetch what it already holds; **MAY** take the read report and measurements from `diary-measurements-read`, the findings of `plant-photo-read`, the growth-stage assessment with its hand-off block for harvest planning, the weather findings and the garden context block from `garden-context` as given
- **MUST** accept as caller-supplied, marked `caller`, only facts the server has no source for: the person's own observation of the plant, the intended use, the weather and forecast, the applied treatments as `treatment_key:YYYY-MM-DD`, the storage conditions, the available harvest capacity and the assessment date
- **MUST** take the assessment date from the caller or, without one, as the growth-stage assessment fixed it, and **MUST NOT** read the current date
- **MUST** report each absent input as absent with its reason, `no source` or `not collected`, and **MUST NOT** fill it

### B. The readiness result

- **MUST** return exactly one of `ready`, `approaching`, `not ready`, `not harvestable` and `insufficient evidence`
- **MUST** return `not harvestable` when the species record carries `allows_harvest: false`, and **MUST** then judge nothing further about maturity
- **MUST** rest `ready`, `approaching` and `not ready` on an observed maturity indicator at level 1 to 3 (a diary measurement, a recorded inspection, or the person's own observation marked `caller`), or on a photo reading corroborated by a timing expectation, and **MUST** name that indicator
- **MUST** read the month window of the selected `growing_periods[]` entry's `harvest_months`, the position against `days_to_maturity`, and the growth-stage result and direction as level 4 priors that **MUST NOT** decide alone, and a photo reading as a reading with no level that **MUST NOT** decide alone
- **MUST** return `insufficient evidence` when `allows_harvest` is absent, when no maturity indicator exists, or when only priors or an uncorroborated photo reading speak to maturity, and **MUST** name the observation that would supply it
- **MUST** state a use-specific indicator (for example for storage or for seed saving) only from the caller or as general knowledge labelled level 8 and not from the record, and **MUST NOT** let it decide alone
- **MUST** give every result its evidence, confidence, uncertainty and missing data, as the decision policy requires

### C. Timing priors

- **MUST** take the harvest window only from the `harvest_months` of the `growing_periods[]` entry that applies, saying which, and **MUST NOT** use the top-level months when periods exist
- **MUST** carry the days since `planted_on` against the cultivar's `days_to_maturity` as a position, **MUST** state that neither what `days_to_maturity` counts from nor what `planted_on` denotes is recorded, and **MUST NOT** compute a harvest date from it
- **MUST** take the growth-stage position from the hand-off block as returned, and **MUST** report it absent with its reason when the growth-stage assessment did not run

### D. Reads

- **MAY** call `get_harvest_readiness` once per plant with the plant and the garden only, **MUST** report its response as returned, assuming no field name and assigning no level, and **MUST** report a `validation.error` verbatim and continue without it
- **MUST** call `get_treatment` for each treatment the caller supplied, and only for those, and **MUST** read only its `safety_interval_days`

### E. Weather and the safety interval

- **MUST** take weather only from the caller, through the weather-impact assessment with no Home Assistant read, and **MUST** feed only exposures whose impact is harvest timing into readiness, as a risk and never as a maturity indicator
- **MUST** report a harvest gate on top of the result: `blocked until <date>` when an applied treatment's date plus its `safety_interval_days` lies after the assessment date, `clear` when every supplied treatment's interval has passed, and `unknown (no treatment date supplied)` without treatment input
- **MUST NOT** infer from the care log, the inspections or the diary that a treatment was or was not applied

### F. The harvest plan

- **MUST** plan for at most five named plants, in the order given, and **MUST** list the rest as not planned with the reason
- **MUST**, with no plants named, report the garden's crops and planting runs from the garden context as context only, compute no window and no readiness, and name the parameter that would supply the plants
- **MUST** order the planned plants by window start month, a plant whose window is unknown after every known one, then by readiness (`ready`, `approaching`, `not ready`, `insufficient evidence`, `not harvestable`), then by plant key, so that the order is a total order on content
- **MUST** count workload as plants per month of window start and plants `ready` or `approaching`, **MUST** state hours or effort only from a caller-supplied capacity, and **MUST** state "over capacity" only when that capacity is given in the same unit as the counts
- **MUST** report storage and use constraints as `not modeled in the measured catalog` unless the caller supplied them, and then mark them `caller`
- **MUST** carry each plant's harvest gate into the plan, and **MUST NOT** order a blocked plant as harvestable before its gate date

### G. Plug-in shape

- **MUST** return, besides the result or the plan, findings in the shape the care planning spec defines in its section C
- **MUST** give `ready` and `approaching` resting on a level 1 to 3 indicator as recommendations, and every other result as an observation
- **MUST** leave the consequence of a finding absent unless an input states one, and **MUST** name the mutation as `no tool measured`, since the catalog holds no harvest write tool

### H. Determinism

- **MUST** make each result and the plan order a function of the supplied blocks and the reads named in section D, so that two runs over the same input give the same results, gates, order, evidence levels and missing-data list
- **MUST NOT** read the current date inside the facts; retrieval times are reported beside the facts and are not compared
- **MUST** state that byte-identical prose outside the facts is not claimed, and that the property is checked on a fixed fixture of input blocks written out as text

### I. Separation and forbidden tools

- **MUST** keep the skill and both recipes free of every state-changing tool, and **MUST** name all twelve that the Kamerplanter server spec lists, individually, in each recipe's prompt as forbidden
- **MUST NOT** call a Home Assistant tool from the skill or either recipe, and **MUST** name `TimeTillErnte` and `time_till` as forbidden in each recipe's prompt, since they are the most tempting wrong substitute and their effect is unclassified
- **MUST NOT** ship an `-apply` sibling of either recipe

## Acceptance Criteria

- [ ] A readiness result is one of `ready`, `approaching`, `not ready`, `not harvestable` and `insufficient evidence`
- [ ] A `ready`, `approaching` or `not ready` result names the level 1 to 3 maturity indicator, or the corroborated photo reading, it rests on
- [ ] No result rests on the harvest months, the position against `days_to_maturity`, the growth stage or a photo reading alone
- [ ] No harvest date is computed from `days_to_maturity`, and the harvest window comes from the selected growing period's `harvest_months`
- [ ] The `get_harvest_readiness` response is reported as returned, with no level and no assumed field, and an error from it does not stop the run
- [ ] Weather enters only from the caller, only as a harvest-timing risk, and no Home Assistant tool is called
- [ ] The harvest gate is `blocked until <date>`, `clear` or `unknown (no treatment date supplied)`, and rests only on `get_treatment` and caller-supplied dates
- [ ] A harvest plan covers at most five plants, names the rest as not planned, and with no plants reports garden context only
- [ ] The plan order is window start, then readiness, then plant key, and does not change when the order of the input changes
- [ ] Workload is counts only unless the caller supplied capacity, and storage is `not modeled in the measured catalog` unless the caller supplied it
- [ ] Every result states its evidence, confidence, uncertainty and missing data, and returns findings in the care planning plug-in shape
- [ ] Two runs over the same input give the same facts on a fixed fixture, and the result says what is not claimed
- [ ] Neither the skill nor a recipe calls a state-changing tool, each recipe's prompt forbids all twelve by name plus `TimeTillErnte` and `time_till`, and no `-apply` sibling ships
- [ ] Every claim about the tool surface cites a spec in this repository, and a claim not re-measured says so
- [ ] The German and the English file have the same headings in the same order, the same number of requirement bullets and the same number of acceptance checkboxes

## Source

- [The garden decision policy](../garden-decision-policy/en.md) — the evidence levels, the six rules and the recommendation output
- [The growth stage and weather impact spec](../growth-stage-and-weather-impact/en.md) — section F, the hand-off block for harvest planning, and the weather exposures with impact area harvest timing
- [The plant planning and planting calendar spec](../plant-planning-and-planting-calendar/en.md) — the harvest window from `harvest_months[]` of the chosen growing period, and no harvest date from `days_to_maturity`
- [The pest pressure assessment spec](../pest-pressure-assessment/en.md) — the safety interval as the pre-harvest Karenz
- [The care planning and daily check spec](../care-planning-and-daily-check/en.md) — the plug-in shape of a finding and the cap of five plants
- [The nutrient imbalance detection spec](../nutrient-imbalance-detection/en.md) — the care log fields
- [The Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) — `get_harvest_readiness`, `get_treatment` with `safety_interval_days`, the unimplemented harvest writes and the twelve state-changing tools, measured 2026-08-16
- [The Home Assistant MCP server spec](../../mcp/home-assistant-mcp-server/en.md) — the unclassified `TimeTillErnte` and `time_till`, measured 2026-08-04
- [The recipe project pattern](../../goose/recipe-project-pattern/en.md) — how a recipe is built here, including forbidden-by-name
- Issue nolte/kamerplanter-goose#50 — the scope and acceptance criteria are taken from its body

## Open Questions

- **The arguments and response fields of `get_harvest_readiness`.** Called once on 2026-08-16 and recorded nowhere. One read call on a reachable instance would settle them; until then the call passes only the plant and the garden and the response is reported as returned.
- **What `days_to_maturity` counts from.** Sowing or transplanting is not recorded, nor whether `planted_on` denotes either. Until it is, the maturity comparison is a position, never a date.
- **A source for treatment application dates.** No described field records when a treatment was applied; whether a care-log `reminder_type` can name a treatment is unrecorded. Until one exists, the caller supplies the date.
- **A source for yield, storage and effort.** None is recorded. Until one is, workload is counts and storage is caller text.
- **Where a person's own observation of maturity sits.** It is read here as a confirmed observation, level 3, marked `caller`, carrying the open question the growth stage spec already records.
- **Whether `TimeTillErnte` or `time_till` answers a harvest question.** Unclassified; the operator would have to classify them before any recipe reads them.
- **Whether five plants is the right cap.** Taken from the daily check, not measured.
