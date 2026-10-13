---
name: decision-policy
description: "Applies one evidence policy to a garden recommendation before it is returned: ranks every claim on an eight-level hierarchy from current measurement down to general knowledge, checks six core rules, and shapes the result as evidence, confidence, uncertainty and missing data. Use when a skill or recipe is about to tell someone what to do with a plant and must say what the advice rests on, when two kinds of evidence disagree, or when an input the advice needs is absent. Refuses to diagnose from one symptom, to recommend watering because a reminder is due, and to fill a missing measurement."
---

# Apply the garden decision policy

Decides what a recommendation may rest on and what it must show. It reads no garden and writes nothing: the caller hands it the evidence it already holds, and it returns the recommendation in a fixed shape with the gaps named. Gathering the evidence is `garden-context` (a garden) and `plant-context-collect` (one plant); judging a specific question stays with the process that owns it.

## Input

The caller supplies, for the question being decided:

- **The question**, stated so that the answer is a proposal to a person.
- **Evidence items**, each with what it says, where it came from (a tool or a document, or the caller), and when it was retrieved.
- **The owning process**, if one exists for this question (nutrient direction, pest tenability), because its own ladder and its own refusal threshold stay authoritative for that question.

## The hierarchy

Rank every claim by what it rests on, highest first. A lower level corroborates or contradicts a higher one and never overrides it.

| Level | Evidence |
|-------|----------|
| 1 | A current measurement: a value with a recognisable unit, for this plant, recent enough for the question |
| 2 | A historical measurement of this plant, too old to describe now |
| 3 | A confirmed observation: an inspection, or a care-log confirmation |
| 4 | Kamerplanter species and cultivar data, the cultivar before the species |
| 5 | Site data: where the plant stands |
| 6 | Weather |
| 7 | A documented expert source, cited rather than recalled |
| 8 | The model's general knowledge, always labelled as not from the record |

Levels 5 to 7 often have no source in the measured catalog. Weather has none, and a site is known by its keys but not by its attributes. An absent level is reported absent with the reason, not treated as supplied by a lower one.

## Procedure

### 1. Inventory the evidence

List every item the caller holds with its source and retrieval time. An item without a source is level 8.

### 2. Assign each claim one level

A claim that rests on two items takes the level of the weaker. A model reading of a photo has no level in this hierarchy yet; report it as a reading and hold it below every recorded level, and name that placement as an open question in the result.

### 3. Check the six rules

Stop and change the recommendation, not the evidence, when one is broken:

1. **Never diagnose from a single symptom.** Cite a further piece of evidence that is not that symptom, or label the result a suspicion.
2. **Never recommend watering solely because a reminder is due.** Name the evidence about the plant's present state that supports it, or say there is none.
3. **Prefer a measured value over general knowledge** about the same quantity, and say when a measurement is declined as stale.
4. **Prefer cultivar data over species defaults** for the same attribute, and name which was used.
5. **Correct an environmental cause before treating the plant**, where one is among the candidates; name it, or say why it is not proposed.
6. **Never invent a measurement.** A value that is not in the record is missing.

### 4. Resolve disagreement

When two items disagree, report the contradiction with both levels. The higher level stands; the lower one is listed as contradicting it. Do not average them, and do not resolve in favour of the more fluent source.

### 5. Respect the owning process

If a process owns the question, use its ladder for the decision and its refusal threshold for whether to propose an action; use the hierarchy here only to compare evidence across processes. This policy sets no action threshold of its own.

### 6. Report

Return, with every recommendation:

- **Evidence**: one entry per claim: level, source, retrieved-at.
- **Confidence**: stated, and derived from the highest level that supports the recommendation, not from how sure the text sounds.
- **Uncertainty**: what would change the recommendation.
- **Missing data**: each input the recommendation would have used and did not have, with the observation that would supply it.

The recommendation is a proposal to a person, never an instruction to a device or a write.

## How the existing ladders relate

The nutrient and pest processes keep their own ladders for their own decisions. Read across, by reading rather than by running a case through both:

| In the process | Reads as |
|----------------|----------|
| A measured value in a diary entry (nutrient tier 1) | Level 1, or level 2 when no longer current |
| A recorded inspection naming the organism (pest tier 1) | Level 3 |
| Care-log pattern (nutrient tier 3) | Level 3 |
| Catalogue fields, species demand and phase expectation (pest tier 2, nutrient tier 5) | Level 4 |
| Visible symptoms read from an image (tier 4 in both) | No level yet |
| Plan target against reconstructed supply (nutrient tier 2) | No level: derived |
| General knowledge of the taxon (pest tier 5) | Level 8 |

The two cases with no level are open questions in the spec, and nothing here re-ranks either process.

## Hard rules

- **Never** read a garden or call any tool from this skill; it works only on the evidence it is given.
- **Never** let a lower level override a higher one.
- **Never** report a level as supplied when the catalog names no source for it.
- **Never** return a recommendation without its evidence, confidence, uncertainty and missing-data blocks.
- **Never** edit or re-rank the ladder of a process that owns the question.
- Report an absent input as an explicit result naming it. Never substitute another.

Governed by `spec/process/garden-decision-policy/en.md`.
