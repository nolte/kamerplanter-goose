# Plant Health and IPM Planning

Status: draft
Portfolio-Scope: local

## Context

A plant that looks wrong invites a single answer: "it is a nitrogen deficiency", "it is spider mites", "the frost got it". Each domain in this repository already answers one narrower question well, and each refuses to answer it when the evidence is thin: [the nutrient process](../nutrient-imbalance-detection/en.md) leaves a direction undetermined below its threshold, [the pest process](../pest-pressure-assessment/en.md) calls a surviving candidate *not contradicted* rather than *identified*, and [the weather assessment](../growth-stage-and-weather-impact/en.md) keeps an exposure apart from a symptom. What none of them does is put the candidate explanations for one plant next to each other, say which survive, and say what would tell the survivors apart. A layer that does this badly undoes the care the domains took: it averages a suspicion and a supported finding into a confident "diagnosis", or it counts the same nutrient finding twice. And once a pest or disease candidate survives, nothing yet orders what to do about it, from looking more closely to a targeted treatment, with the treatment's safety interval and prerequisites stated.

This spec fixes two things. A **plant health assessment** combines what the existing skills already returned for one plant into a differential: a fixed set of candidate classes, each with one status, and one overall result, never a diagnosis. An **IPM plan** takes a pest or disease candidate as the pest process left it and orders the interventions in four stages, reaching a targeted treatment only at the pest process's own threshold and only with its safety constraints and prerequisites attached.

An assessment or a plan here is a statement to a person. It changes nothing. The health assessment makes no read of its own; the IPM plan makes at most the catalogue reads named in section D.

Everything about the tool surface is quoted from [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md), measured against the reference instance on 2026-08-07 and 2026-08-16, and not re-measured for this spec: the Kamerplanter MCP server was unreachable (`INVALID_CONFIG`) when this spec was written. Five facts the requirements rest on were read from the working copy rather than measured: `get_pest` carries nested `treatments[]` with `treatment_key`, `name`, `treatment_type`, `active_ingredient`, `application_method`, `safety_interval_days`, `dosage_per_liter` and `protective_equipment[]`, and `beneficials[]` with `preys_on[]`, recorded on one pest ([the pest process](../pest-pressure-assessment/en.md), "The catalogue, and where it stops"); `get_disease` carries `environmental_triggers[]` and `get_pest` carries no humidity, host-range or monitoring field (same section); no spec records the value set of `treatment_type` (a search of `spec/` and `.claude/` for `treatment_type` finds only field-name rows); no spec records the response fields of `get_harvest_readiness`, nor those of `get_plant_inspections` on an inspected plant (the server spec names the first only in its catalog table, and the pest process lists the second as an open question); and `create_inspection` is in the measured write catalog, while no tool that records a treatment is (the server spec's write table), although the server spec's Non-Goals still list IPM write tools as unimplemented (Open Questions).

Boundaries: [the garden decision policy](../garden-decision-policy/en.md) owns the evidence levels, the six rules (rule 1, never diagnose from a single symptom; rule 5, correct an environmental cause before treating the plant) and the shape of a recommendation; this spec states no level of its own. [The pest process](../pest-pressure-assessment/en.md) owns identification, its evidence ladder, the falsification tests, the treatment threshold and the checks on beneficials, safety interval and rotation; this spec cites them and restates none. [The nutrient process](../nutrient-imbalance-detection/en.md) owns the nutrient direction. [The plant health image analysis spec](../plant-health-image-analysis/en.md) owns the photo queue and its claim-and-submit cycle, a write cycle; this spec owns only the read-only synthesis and takes photo findings as given. [The growth stage and weather impact spec](../growth-stage-and-weather-impact/en.md) owns the growth stage, the exposures and their hand-off to plant health. [The care planning spec](../care-planning-and-daily-check/en.md) owns the plug-in shape of a finding and the daily check that runs these assessments. [The recipe project pattern](../../goose/recipe-project-pattern/en.md) owns how a recipe is built, including forbidden-by-name, and why the composition happens in a recipe rather than through sub-recipes.

Readers: authors of garden skills and recipes in this repository, and the people who read a health assessment or an IPM plan before acting on a plant.

## Goals

- Several evidence sources are combined into one picture of a plant's health, and each candidate explanation says what it rests on
- Competing explanations are kept side by side when the evidence does not separate them, with the observation that would separate them
- Confidence and uncertainty are explicit for every candidate and for the result as a whole
- The existing diagnostic skills are reused, and no domain's verdict is re-run, upgraded or counted twice
- An IPM plan prefers confirmation, then environmental correction, then cultural and mechanical controls, and reaches a targeted treatment only when the pest process's threshold is met
- Every treatment in a plan carries its safety constraints and prerequisites, quoted from the record, and is excluded when they cannot be checked

## Non-Goals

- Recording anything: no `-apply` recipe, no inspection record, no treatment record. A step that a later apply step would record names the mutation and calls nothing
- Identifying a pest or disease, judging a nutrient direction, reading a photo, assessing the growth stage or the weather: those belong to their own processes, which this layer composes
- Harvest planning (nolte/kamerplanter-goose#50), beyond the time to harvest the safety check needs
- A treatment contraindication table, a host-range table, a monitoring-method table or a mapping from `treatment_type` to a stage: none has a source in the record
- Correcting the stale Non-Goal of the server spec that lists IPM write tools as unimplemented (Open Questions)
- Measuring the tool surface live. Claims about it cite the server spec and say they are not re-measured

## Requirements

### A. Inputs

- **MUST** take, for the health assessment, the plant context block from `plant-context-collect` (which already holds the care log, the inspections, the species and cultivar data and the phase), the read report and measurements of `diary-measurements-read`, the result and hand-offs of `growth-stage-assessment`, the plant-health hand-off of `weather-impact-analysis`, and the reports of `nutrient-imbalance-assess` and `pest-pressure-assess`, each as returned
- **MAY** take, for the health assessment, the findings of `plant-photo-read` when the caller names a diary entry with photos, and the findings of `watering-decision` and `fertilization-decision`, each as returned
- **MUST** make no tool call from the health assessment skill: everything it uses is in the blocks it is handed
- **MUST** take, for the IPM plan, the `pest-pressure-assess` report as returned, and **MAY** take the health assessment's IPM hand-off and the harvest hand-off of `growth-stage-assessment`
- **MUST** accept as caller-supplied, marked `caller`, only facts the server has no source for: the person's own observation of the plant, the suspicion to test, the weather, where the plant stands (enclosed or open, outdoors, sheltered or indoors), the planned harvest date and the assessment date, and **MUST NOT** read the current date
- **MUST** report each absent input as absent with its reason, `not collected` or `no source`, and **MUST NOT** fill it

### B. The differential

- **MUST** consider exactly these candidate classes: `nutrient`, `pest`, `disease`, `water`, `environment`, `development` and `abiotic handling/site`
- **MUST** give each candidate exactly one status: `supported`, `suspicion`, `contradicted` or `not assessable`
- **MUST** give `supported` only when the owning domain returned its own positive result and at least one further evidence item that is not the presenting symptom supports it, with no contradiction at a higher level
- **MUST** give `suspicion` to a candidate resting on a single symptom, a photo reading, priors, or a "consistent with" link only, `contradicted` to a candidate that the owning domain's own negative result for a candidate it tested (for a pest or disease, the pest process's `rejected`; an empty inspection history is never one) or a named item at a higher level contradicts, and `not assessable` to a candidate whose domain did not run, returned nothing or tested no candidate of that class, with the reason
- **MUST** return exactly one overall result: `leading explanation`, `competing explanations`, `suspicion only`, `no abnormality reported` or `insufficient evidence`, determined in a fixed order that leaves no case open, so that an abnormality reported with no candidate `supported` or `suspicion` is `insufficient evidence`
- **MUST NOT** upgrade a domain's result: a pest candidate the pest process left `not contradicted` stays `not contradicted`, a nutrient direction it left undetermined stays undetermined, and the health layer re-runs no ladder, falsification test or refusal threshold of another process
- **MUST NOT** call any result a diagnosis, and **MUST** label a candidate resting on one symptom a suspicion, as rule 1 of the decision policy requires

### C. Confidence and uncertainty

- **MUST** give every candidate its evidence entries (level, source, retrieved-at), its confidence from the highest decision-policy level that supports it, its uncertainty and its missing data, and **MUST** say that no level applies when none does
- **MUST** name, for each pair of surviving candidates, the observation that would discriminate between them
- **MUST** read the levels of the domain reports from the decision policy's table "How the existing ladders relate", and **MUST NOT** assign a level where that table gives none
- **MUST** carry a domain's own contradiction or refusal into the result as that domain stated it, and **MUST NOT** resolve a disagreement between two domains in favour of the more fluent one

### D. IPM stages

- **MUST** order an IPM plan in exactly these four stages, in this order: confirmation and monitoring; environmental correction; cultural and mechanical controls; targeted treatment
- **MUST NOT** identify a candidate or re-run the pest process's falsification tests, and **MUST** plan only for a candidate the pest report names, with the status and tier the report gave
- **MUST** limit the plan's own reads to `get_pest` and `get_disease` for the candidate keys the pest report names, `get_treatment` for a treatment key those records name, and `search_glossary` for a term, and **MUST** quote `treatments[]`, `beneficials[]` and `environmental_triggers[]` as returned
- **MUST** reach the targeted-treatment stage only when the pest process's treatment threshold is met, and below it **MUST** stop after the cultural and mechanical stage and name the monitoring method that would raise the evidence, labelled as general knowledge not in the record
- **MUST** cite `environmental_triggers` for an environmental correction against a disease, and **MUST** label one against a pest as general knowledge not in the record, since the pest record carries no humidity ecology
- **MUST** order the targeted-treatment stage biological before chemical, place a beneficial release there and the conservation of natural enemies in an open setting in the cultural stage, and check each beneficial against `preys_on` as the pest process requires
- **MUST** report a `treatment_type` value it cannot place in a stage as "stage not determinable from the record", since the value set is not recorded, and **MUST NOT** guess the stage
- **MUST** return "no pest or disease candidate" as a valid empty plan when the pest report names none

### E. Treatment prerequisites and safety constraints

- **MUST** give every measure in the targeted-treatment stage a prerequisites block: the identification meets the pest threshold, with the tier named; each earlier stage is done or unavailable, with the reason, where an environmental correction that was not assessed is neither and blocks the measure until what would assess it is supplied; and the harvest situation, `allows_harvest` and the time to harvest
- **MUST** take the time to harvest only from the caller's planned harvest date or from the growth-stage harvest hand-off (days since `planted_on` against `days_to_maturity`), **MUST** name as uncertainty that this fallback ignores an early or continuous harvest (baby leaf, herbs), and **MUST NOT** take it from `get_harvest_readiness`, whose response fields are not recorded
- **MUST** give every such measure a safety-constraints block quoting `safety_interval_days`, `protective_equipment[]`, `dosage_per_liter`, `application_method` and `active_ingredient` verbatim from the record, and **MUST NOT** scale, convert or invent any of them
- **MUST** exclude a measure whose `safety_interval_days` exceeds the time remaining to harvest, and **MUST** report a measure as "not recommendable: interval cannot be checked" when `allows_harvest` is true and either the time to harvest is not established or `safety_interval_days` is not recorded (null or absent)
- **MUST NOT** offer two measures sharing an `active_ingredient` as alternatives, and **MUST** say that the rotation claim cannot be made where `active_ingredient` is `null`
- **MUST** state, as not recorded, the conflict between a beneficial release and a broad-spectrum measure, and the product label and local plant-protection rules as a prerequisite outside the record, always listed for the person to confirm before applying and never by itself deciding whether a measure is recommendable
- **MUST** take the enclosed or open setting from the caller, or state it as inferred, as the pest process requires

### F. Separation of exposure and symptom

- **MUST** take weather into the health assessment only through the plant-health hand-off of the weather assessment, and **MUST** keep the exposures in a block of their own, apart from the symptoms
- **MUST** link a symptom to an exposure only as "consistent with", which keeps the `environment` candidate a suspicion, as [the growth stage and weather impact spec](../growth-stage-and-weather-impact/en.md) section E requires

### G. Plug-in shape and kinds

- **MUST** return, besides the result, findings in the shape the care planning spec defines in its section C
- **MUST** return the health assessment as observations only, one finding per plant holding the differential, which cites the other domains' findings by domain and restates none of their recommendations
- **MUST** return a hand-off block for the IPM plan holding the `environment` and `water` candidates and the pest or disease candidate as the pest report returned it
- **MUST** give a monitoring step for an existing candidate the kind recommendation, an environmental or cultural step the kind recommendation only when the candidate is at least `not contradicted` in the pest report and observation otherwise, and a targeted treatment the kind recommendation only when the threshold is met, every earlier stage is done or unavailable, and the harvest situation allows it; the label and local rules are listed for confirmation and decide nothing
- **MUST** leave the consequence of a finding absent unless an input states one
- **MUST** name the inspection-recording tool, `create_inspection`, as the mutation a later apply step would call for a monitoring step, and `no tool measured` for a treatment, and **MUST NOT** call either

### H. Determinism

- **MUST** make each result a function of the supplied blocks and the reads named in section D, so that two runs over the same input give the same candidate statuses, overall result, stages, exclusions, evidence levels and missing-data list
- **MUST NOT** read the current date inside the facts; retrieval times are reported beside the facts and are not compared
- **MUST** state that byte-identical prose outside the facts is not claimed, and that the property is checked on a fixed fixture of input blocks written out as text

### I. Separation and forbidden tools

- **MUST** keep both skills and both recipes free of every state-changing tool, and **MUST** name all twelve that the Kamerplanter server spec lists, individually, in each recipe's prompt as forbidden
- **MUST NOT** call a Home Assistant tool from either skill or recipe, and **MUST** forbid in each recipe's prompt actuation by category (turning a device on or off, setting a value, running a script, scene or automation) and `TimeTillErnte` and `time_till`, whose effect is unclassified
- **MUST** compose the sub-skills in the recipe, by name, and **MUST NOT** rely on `sub_recipes:` or `--sub-recipe`, which do not work under the `claude-code` provider
- **MUST NOT** ship an `-apply` sibling of either recipe

## Acceptance Criteria

- [ ] A health assessment combines the context, measurements, growth stage, weather exposures and the nutrient and pest reports, and names each absent input with its reason
- [ ] Each candidate class carries exactly one of `supported`, `suspicion`, `contradicted` and `not assessable`, and the result is exactly one of the five overall results
- [ ] Two surviving candidates are reported side by side as `competing explanations`, with the observation that would discriminate between them
- [ ] No result is called a diagnosis, and no candidate resting on one symptom is more than a suspicion
- [ ] Every candidate states its evidence, confidence, uncertainty and missing data
- [ ] No domain's result is upgraded, re-run or restated: the health finding is an observation that cites the domains by name
- [ ] Weather enters only as exposures, kept apart from symptoms and linked only as "consistent with"
- [ ] An IPM plan has the four stages in order, and reaches a targeted treatment only at the pest process's threshold
- [ ] Below the threshold the plan names a monitoring method, labelled as not recorded
- [ ] Every targeted treatment carries its prerequisites and its safety constraints quoted verbatim, and is excluded or not recommendable when its interval exceeds or cannot be checked against the time to harvest, including when the interval is not recorded
- [ ] No two measures sharing an active ingredient are offered as alternatives, and an unplaceable `treatment_type` is reported as such
- [ ] Both skills return findings in the care planning plug-in shape, and a monitoring step names `create_inspection` as a mutation that nothing calls
- [ ] Two runs over the same input give the same facts on a fixed fixture, and the result says what is not claimed
- [ ] Neither skill nor recipe calls a state-changing tool or a Home Assistant tool, and each recipe's prompt forbids all twelve state-changing tools by name, actuation by category, and `TimeTillErnte` and `time_till`
- [ ] Every claim about the tool surface cites a spec in this repository, and a claim not re-measured says so
- [ ] The German and the English file have the same headings in the same order, the same number of requirement bullets and the same number of acceptance checkboxes

## Source

- [The garden decision policy](../garden-decision-policy/en.md) — the evidence levels, the six rules, the recommendation output and the table "How the existing ladders relate"
- [The pest pressure assessment spec](../pest-pressure-assessment/en.md) — the evidence ladder, the treatment threshold, the falsification tests, the beneficial, safety-interval and rotation checks, and the measured pest and disease records
- [The nutrient imbalance detection spec](../nutrient-imbalance-detection/en.md) — the nutrient direction and its refusal threshold
- [The plant health image analysis spec](../plant-health-image-analysis/en.md) — the photo reading and its write cycle, which this spec does not own
- [The growth stage and weather impact spec](../growth-stage-and-weather-impact/en.md) — the growth stage, its harvest hand-off, and the exposures handed to plant health
- [The care planning and daily check spec](../care-planning-and-daily-check/en.md) — the plug-in shape and the daily check
- [The Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) — the tool catalog, `get_pest`, `get_disease`, `get_treatment`, `create_inspection` and the state-changing tools, measured 2026-08-07 and 2026-08-16
- [The recipe project pattern](../../goose/recipe-project-pattern/en.md) — how a recipe is built here, forbidden-by-name, and why sub-recipes are not used
- Issue nolte/kamerplanter-goose#48 — the scope, the IPM order and the five acceptance criteria are taken from its body

## Open Questions

- **The value set of `treatment_type`.** Not recorded. Until a `get_pest` call over several pests shows it, a value is placed in a stage only where its meaning is plain, and otherwise reported as "stage not determinable from the record".
- **The fields of `get_plant_inspections` on an inspected plant.** Measured only on an empty history. A populated response would settle whether a pressure level can enter the differential as more than a named organism.
- **A source for contraindications between treatments.** None is recorded; the conflict between a release and a broad-spectrum measure stays general knowledge until the backend, the glossary or a cited source carries it.
- **Legal and label constraints.** Product registration, label conditions and local plant-protection rules are not in the record. A plan states them as a prerequisite outside it; whether a source for them belongs here is open.
- **Whether the health result may ever be a recommendation.** It is an observation here, so that the care plan counts no domain's recommendation twice. A recommendation proper to the combination, such as "look at the leaf undersides", is carried by the discriminating observation instead; whether that should become a recommendation is open.
- **The stale Non-Goal of the server spec.** Its Non-Goals list IPM write tools as specified but unimplemented, while its own write table records `create_inspection` as measured. A follow-up should correct it; this spec does not.
- **Whether the "uniform damage across plants" cue of the photo checklist is available per plant.** It points to an abiotic cause, but a single-plant assessment sees one plant. The first live run over several plants would show whether it can enter the `abiotic handling/site` candidate.
