---
name: fertilization-decision
description: "Turns the nutrient assessment of one plant into a fertilisation decision for a person: feed, do not feed, or insufficient evidence, with the basis it rests on (insufficient nutrition, an environmental cause, or an uncertain diagnosis), evidence, confidence, uncertainty and missing data. Use when a recipe must say whether to feed a plant, or when the daily check needs the fertilisation domain. Takes the nutrient report as given and never re-derives its direction or its tier rule, returns a dose only from the mixing protocol result and otherwise says the dose is unknown, treats do not feed as an ordinary result, and calls no tool: the decision is a function of the blocks it is given."
---

# Decide whether to feed

Turns what the nutrient process already established into a decision a person can act on. It makes no tool call: everything it needs is in the blocks it is handed, which is what lets two runs over the same blocks give the same decision. It writes nothing and does not diagnose. The direction of a nutrient problem is `nutrient-imbalance-assess`, the weight of a claim is `decision-policy`, and gathering the plant's facts is `plant-context-collect` and `diary-measurements-read`. A decision here is a proposal to a person, never an instruction to a device.

## Input

- **The nutrient report** from `nutrient-imbalance-assess` for this plant: the direction, the evidence tier that established it, what it assumed about the base water, any proposed correction, and the dose it took from `calculate_mixing_protocol` if it called it. Without it, stop and say that `nutrient-imbalance-assess` must run first.
- **The plant context block** from `plant-context-collect` (species, phase, the care log summary with the most recent confirmed reminder per type and the snoozed entries, inspections, the gaps list) and **the diary read report** from `diary-measurements-read`.
- **The garden context block** from `garden-context`, optional.
- **Caller facts**, each optional, taken as written and marked `caller`: the EC of the water source, the tank and dosing state. The server has no source for them; absent ones are absent, never filled.

## Procedure

### 1. Read the direction, do not make it

Take the direction and the tier from the nutrient report exactly as it states them. Never re-derive the direction, never re-rank a tier, never override the nutrient process's refusal. Its rule that tier 2 needs recorded dose amounts, and that a feeding frequency without amounts is tier 3, is its own: a care log of confirmed reminders carries no amount, so a frequency here is not a dose.

### 2. Decide

| The nutrient report says | Decision | Rests on |
|--------------------------|----------|----------|
| undersupply, established as a direction, and no environmental cause named | `feed` | insufficient nutrition |
| oversupply | `do not feed` | insufficient nutrition ruled out (oversupply) |
| unavailability at adequate supply, or any environmental cause named (a pH outside the range, an EC that impedes uptake, exhausted substrate shown by repeated snoozed repotting, antagonism) | `do not feed` | an environmental cause: correct it before treating the plant |
| direction undetermined, a suspicion, or the highest tier is 3 or below | `insufficient evidence` | an uncertain diagnosis |

`do not feed` is an ordinary and often correct result. When the evidence is incomplete, prefer the conservative row: `do not feed` or `insufficient evidence` over `feed`. Say which of insufficient nutrition, an environmental cause and an uncertain diagnosis the result rests on.

### 3. The dose

A concentration, a dose or a mixing order appears only as the result of `calculate_mixing_protocol` that the nutrient report carries. It works on EC-net, so state the base-water assumption it used and whether the caller supplied the water source EC. Without that result, the dose is `unknown`: give no number and no order from general knowledge. Never invent a concentration or a measurement. For recent fertilisation, read the care log's confirmed reminders; they carry no amount, so never state one the record does not hold.

### 4. Weigh it

Apply `decision-policy` to the decision: evidence (level, source, retrieved-at, with the nutrient tier mapped through its table "How the existing ladders relate", `no level` where it gives none), confidence from the highest level that supports it, uncertainty (what would change the decision), and missing data (each input it did not have, with the observation that would supply it).

### 5. Report

Return, in this order:

```
FERTILIZATION DECISION
  plant:       <plant key>
  decision:    feed | do not feed | insufficient evidence
  rests on:    insufficient nutrition | insufficient nutrition ruled out (oversupply) | an environmental cause | an uncertain diagnosis
  nutrient:    <direction> (tier <n>), as the nutrient report stated it
  dose:        <the mixing protocol result, with its base-water assumption> | unknown
  evidence:    <level, source, retrieved-at, one entry each>
  confidence:  <the level it rests on, or: no level applies>
  uncertainty: <what would change the decision>
  missing:     <each input it did not have, with the observation that would supply it>
FINDING
  domain: fertilization | subject: <plant key> | kind: recommendation (feed) or observation (do not feed, insufficient evidence)
  statement / evidence / confidence / what would change it / missing data, as above
  consequence: <only if an input states one, otherwise absent>
```

Return no field that was not read. Facts that two runs over the same blocks must agree on are the decision, what it rests on, the evidence levels and the missing-data list; retrieval times and prose may differ.

## Hard rules

- Never call a tool. Everything is in the blocks.
- Never re-derive, re-rank or override the direction or the tier rule of `nutrient-imbalance-assess`.
- Never return `feed` without an established undersupply and without every named environmental cause being absent.
- Never state a concentration, a dose or a mixing order that `calculate_mixing_protocol` did not return, and never state an amount the care log does not hold.
- Never fill an absent input, never invent a measurement, and never use a Home Assistant sensor as evidence.
- Never read the current date into the decision facts.

## Gotchas

- A plant with a nutrient plan of `null`, no diary measurement and a frequency-only care log ends at `insufficient evidence`. That is the ordinary result, not a failure of the run.
- `calculate_mixing_protocol` subtracts the base water EC: an omitted `base_water_ec` overstates the dose. Say which assumption the dose used.
- The decision proposes; the record of a feeding a person carried out is `fertilization-decision-apply`, a different recipe, and nothing here feeds a plant.
- This skill itself was not run against a live instance; it has no tool calls to get wrong, and its input blocks inherit that status.

## Source

Governed by `spec/process/watering-and-fertilization-decisions/en.md` §A, §C, §D, §F and §G.
