---
name: plant-health-assessment
description: "Combines what the existing checks already returned for one plant — the person's observations, photo readings, the growth stage, diary measurements, watering and fertilisation history, species and cultivar data, the nutrient and pest reports and the weather exposures — into a differential: seven candidate classes (nutrient, pest, disease, water, environment, development, abiotic handling/site), each supported, suspicion, contradicted or not assessable, and one overall result (leading explanation, competing explanations, suspicion only, no abnormality reported, insufficient evidence) with evidence, confidence, uncertainty, missing data and the observation that would tell surviving candidates apart. Use when a recipe must say what may be wrong with a plant and what would settle it, or when the daily check needs the plant health domain. Never diagnoses, never upgrades a domain's own result, never reads a weather exposure as a symptom, and calls no tool: the result is a function of the blocks it is given."
---

# Assess a plant's health as a differential

Puts the candidate explanations for one plant next to each other and says which survive. It decides no single question itself: the nutrient direction is `nutrient-imbalance-assess`'s, pest and disease tenability is `pest-pressure-assess`'s, the stage is `growth-stage-assessment`'s, the exposures are `weather-impact-analysis`'s, and the weight of a claim is `decision-policy`'s. Their verdicts stand as they returned them; this skill re-runs no ladder, no falsification test and no refusal threshold, and never raises a result above what its owner gave.

It makes no tool call: everything it needs is in the blocks it is handed, which is what lets two runs over the same blocks give the same differential. It writes nothing. The result is a statement to a person, never a diagnosis, and never an instruction to a device or a write.

## Input

Each as returned by its skill; each absent one is reported `not collected` (the skill did not run) or `no source` (nothing in the record could supply it), with the reason.

- **The plant context block** from `plant-context-collect`: species and cultivar data, the resolved phase and its definition, the care log (the most recent confirmation per reminder type, snoozed entries), the inspections, the gaps list.
- **The read report and measurements** from `diary-measurements-read`.
- **Photo findings** from `plant-photo-read`, only when the caller named a diary entry with photos.
- **The growth-stage result and its hand-offs** from `growth-stage-assessment`.
- **The plant-health hand-off** from `weather-impact-analysis`: the exposures and, separately, the symptoms with any "consistent with" link.
- **The nutrient report** from `nutrient-imbalance-assess` and **the pest report** from `pest-pressure-assess`.
- **The watering and fertilisation findings** from `watering-decision` and `fertilization-decision`, optional.
- **Caller facts**, optional, marked `caller`: the person's own observation of the plant, where it stands, the assessment date. Never read the current date.

Without the plant context block, stop and say that `plant-context-collect` must run first.

## Procedure

### 1. Inventory the inputs

List every input above as present, `not collected` or `no source`, with the reason. A domain that did not run is absent, not negative: never read its silence as "nothing wrong".

### 2. Collect the symptoms and the exposures, apart

- **Symptoms**: what the person observed (`caller`, level 3), recorded inspections (level 3), diary entries and their measurements (level 1, or 2 when no longer current), and `plant-photo-read` findings (no level: a reading that may corroborate or contradict, never decide alone). Name the **presenting symptom**: the one the question is about, or the most specific one when there are several.
- **Exposures**: only those of the weather hand-off, at level 6, in a block of their own. An exposure is never a symptom, and no symptom is read off the weather. A link between them is only ever "consistent with".

When no symptom source was available at all (no observation, no photo, no diary entry, no inspection), say so: the overall result can then only be `insufficient evidence`.

### 3. Rate each candidate class

Every class gets exactly one status:

| Status | When |
|--------|------|
| `supported` | the owning domain returned its own positive result **and** at least one further evidence item that is not the presenting symptom supports it, with no higher-level contradiction |
| `suspicion` | it rests on a single symptom, a photo reading, priors, or a "consistent with" link only |
| `contradicted` | the owning domain's own negative result, or a named item at a higher level, contradicts it |
| `not assessable` | the owning domain did not run or returned nothing, with the reason |

Where each class takes its status from:

| Class | Owning source | Its own positive result | Its own negative result |
|-------|---------------|-------------------------|-------------------------|
| `nutrient` | the nutrient report, and the fertilisation finding | a direction the report establishes, with the tier it names | the report rules an imbalance out |
| `pest` | the pest report, pest candidate | status `identified` | status `rejected`, or no pest candidate tenable |
| `disease` | the pest report, disease candidate | status `identified` | status `rejected`, or no disease candidate tenable |
| `water` | the watering finding, the care log's watering confirmations, moisture measurements | decision `water now` (a measured dry state) | decision `wait` on a measured state within the target |
| `environment` | the weather hand-off | none: a "consistent with" link is a suspicion at most | every factor `no exposure in the supplied data` |
| `development` | the growth-stage result, read against the phase definition and the species months | a stage at level 1 to 3 in which the presenting change is expected (for example senescing lower leaves in fruit) | a stage at level 1 to 3 in which the change is not expected |
| `abiotic handling/site` | the caller's observation, the care log (a repeatedly snoozed repotting) | none: no process owns it, so a suspicion at most | none |

**Never upgrade a domain's result.** A pest or disease candidate the pest process left `not contradicted` is a `suspicion` here and keeps the words `not contradicted`; a nutrient direction it left undetermined stays undetermined and is a `suspicion` at most. Carry the tier and the tests not run exactly as the report gave them. A candidate resting on one symptom is a suspicion, as rule 1 of `decision-policy` requires.

### 4. Decide the overall result

In this order, the first that applies:

| Overall result | When |
|----------------|------|
| `insufficient evidence` | no symptom source was available, or every class is `not assessable` |
| `no abnormality reported` | the symptom sources that were read report no abnormality, and no class is `supported` or `suspicion` |
| `leading explanation` | exactly one class is `supported` |
| `competing explanations` | two or more classes are `supported` |
| `suspicion only` | no class is `supported`, and at least one is `suspicion` |

The **surviving candidates** are those `supported` or `suspicion`. A `leading explanation` still lists every surviving suspicion beside it. No result is ever called a diagnosis, and none is worded as certain.

### 5. Name what would discriminate

For each pair of surviving candidates, name the one observation that would tell them apart, stated as something a person can do or record: "the leaf undersides at 1280, for mites against a nutrient pattern"; "a substrate moisture reading, for drought against root damage"; "whether new growth is affected, for a mobile against an immobile nutrient". When the observation is general knowledge rather than a recorded method, label it level 8, not from the record.

### 6. Weigh it

Apply `decision-policy` to every candidate and to the overall result: evidence (level, source, retrieved-at, one entry each), confidence from the highest level that supports it, uncertainty (what would change it), and missing data (each input it did not have, with the observation that would supply it). Read the levels of the domain reports from the table "How the existing ladders relate"; where it gives none, write `no level`. When two domains disagree, report both with their levels; never resolve it in favour of the more fluent one, and never average.

### 7. Report

Return, in this order:

```
PLANT HEALTH ASSESSMENT
  plant:           <plant key>
  assessed as of:  <date> (caller | newest observation) | none
  inputs:          <each input: present | not collected (<reason>) | no source (<reason>)>
  presenting symptom: <symptom, source, level> | none reported | no symptom source
SYMPTOMS
  <symptom, source, level>, one per line | none
EXPOSURES (NOT SYMPTOMS)
  <factor and impact, as the weather hand-off gave it> | none | not collected
  link: <symptom> consistent with <exposure> | none
CANDIDATES
  <class>: supported | suspicion | contradicted | not assessable
    rests on:    <the owning domain's result, as it returned it, with its tier or decision> | <reason not assessable>
    evidence:    <level, source, retrieved-at, one entry each>
    confidence:  <the level it rests on, or: no level applies>
    against it:  <the item that contradicts it, with its level> | none
RESULT
  overall:     leading explanation | competing explanations | suspicion only | no abnormality reported | insufficient evidence
  surviving:   <the supported and suspicion classes> | none
  discriminate: <candidate A vs candidate B: the observation that would tell them apart>, one per pair | none
  uncertainty: <what would change the result>
  missing:     <each input it did not have, with the observation that would supply it>
HAND-OFF: IPM PLANNING
  pest or disease candidate: <as the pest report returned it: candidate, key, status, tier, tests not run> | none named
  environment: <status, with the exposures it rests on>
  water:       <status, with what it rests on>
FINDING
  domain: plant health | subject: <plant key> | kind: observation
  statement:   <the overall result and the surviving candidates, citing each owning domain by name>
  evidence / confidence / what would change it / missing data, as above
  consequence: <only if an input states one, otherwise absent>
```

The finding is always an **observation**. It cites the nutrient, pest, watering, fertilisation, growth-stage and weather findings by domain and restates none of their recommendations, so a care plan that carries both counts nothing twice. It names no mutation. Return no field that was not read. The facts two runs over the same blocks must agree on are the candidate statuses, the overall result, the surviving set, the discriminating observations, the evidence levels and the missing-data list; retrieval times and prose may differ, and byte-identical prose is not claimed.

## Hard rules

- Call no tool. Everything is in the blocks.
- Never call a result a diagnosis, and never raise a candidate resting on one symptom above a suspicion.
- Never upgrade, re-run or restate a domain's result: `not contradicted` stays `not contradicted`, an undetermined direction stays undetermined.
- Never read a weather exposure as a symptom, and never link the two more strongly than "consistent with".
- Never read a domain that did not run as a negative result, and never fill an absent input.
- Never return the health finding as a recommendation, and never word it as an instruction to a device or a write.
- Never read the current date into the facts.

## Gotchas

- Most plants end at `suspicion only` or `insufficient evidence`: the pest process rarely reaches `identified` without a recorded inspection, and the nutrient direction stays undetermined at tier 3 and below. That is the honest result, not a failure; the discriminating observation is the useful part.
- A plant tended only through reminders has no symptom source at all. A due task is a request from the schedule, not an observation of the plant, and adds nothing here.
- The photo checklist's cue "uniform damage across plants points to an abiotic cause" needs several plants; a single-plant assessment cannot use it, and whether the daily check can is unmeasured.
- The health finding is an observation on purpose: the recommendations belong to the owning domains and to the IPM plan, and a second copy here would be counted twice in the care plan.
- This skill itself was not run against a live instance; it has no tool calls to get wrong, and its input blocks inherit that status.

## Source

Governed by `spec/process/plant-health-and-ipm-planning/en.md` §A, §B, §C, §F, §G and §H.
