---
name: watering-decision
description: "Turns what is known about one plant into a watering decision for a person: water now, wait, or insufficient evidence, with the evidence about the plant's present state it rests on, confidence, uncertainty and missing data. Use when a recipe must say whether to water a plant, or when the daily check needs the watering domain. Never returns water now because a reminder is due, an interval has elapsed or the plant is expected to be dry; reads the phase's watering interval and the species requirements as priors that decide nothing alone; ends at insufficient evidence when nothing is known about the plant's present state, which is the ordinary result; and calls no tool: the decision is a function of the blocks it is given."
---

# Decide whether to water

Turns the facts already collected into a decision a person can act on, or into an honest "not enough to say". It makes no tool call: everything it needs is in the blocks it is handed, which is what lets two runs over the same blocks give the same decision. It writes nothing. Gathering the plant's facts is `plant-context-collect` and `diary-measurements-read`, the weight of a claim is `decision-policy`. A decision here is a proposal to a person, never an instruction to a device.

## Input

- **The plant context block** from `plant-context-collect`: species, the resolved phase and its definition (which carries `watering_interval_days`), the care log summary (the most recent confirmed reminder per type, the snoozed entries), inspections, the gaps list.
- **The diary read report and measurements** from `diary-measurements-read`.
- **The garden context block** from `garden-context`, optional.
- **Caller facts**, each optional, taken as written and marked `caller`: weather and forecast, the container or bed, irrigation constraints, and user constraints (the moisture target the caller wants the plant kept to is one). The server has no source for them; absent ones are absent, never filled.

Without the plant context block, stop and say that `plant-context-collect` must run first.

## Procedure

### 1. Find what is known about the plant's present state

The measured catalog has one source for it: a measurement in a diary entry of this plant. Take a soil or substrate moisture value only from a `measurements` key whose meaning and unit are unambiguous, and discard an ambiguous one, saying that you did. A measurement recent enough for the question is level 1; an older one is level 2 and describes the past, not the present. "Recent enough" is not defined (the decision policy leaves it open, and the decision facts never read today's date): report the measurement's recorded date and the basis on which you judged it current, for example the caller saying the reading is from today. A reading you cannot judge is level 2.

Everything else is context, not present state:

- the care log's confirmed reminders and their intervals are level 3: they say what was done and when, not how dry the plant is now;
- the phase definition's `watering_interval_days`, the species data and the phase requirements are level 4 **priors**: they say what is normal and decide nothing alone;
- weather and forecast come only from the caller; they may change the confidence or the uncertainty, never the decision alone;
- a Home Assistant sensor is not evidence: no mapping from a sensor to a plant is recorded.

### 2. Decide

| What is known about the present state | Decision |
|---------------------------------------|----------|
| a recent, unambiguous moisture measurement of this plant on the dry side of a target the caller states | `water now` |
| a recent, unambiguous moisture measurement within that target, or on the wet side | `wait` |
| a measurement with no target to compare it with, an ambiguous key or unit, or one too old for the question | `insufficient evidence` |
| no measurement at all | `insufficient evidence` |

A target comes from the caller, as a user constraint: no field of the plant context block carries a moisture target in the measured record. **This skill adds that rule; the spec does not state it** (its Open Questions name it). Without a target, a measurement alone is a number with nothing to compare it to. That ends at `insufficient evidence`, and the result says which target is missing.

**Never** return `water now` because a reminder is due, because a schedule or the phase's interval has elapsed, or because the plant is expected to be dry: that is rule 2 of `decision-policy`, and none of them is a reading of the plant. `insufficient evidence` is the ordinary result of this skill, not a failure: say what would supply the missing evidence, for example one moisture reading recorded in a diary entry, and say that it is the person's observation that is missing.

### 3. Weigh it

Apply `decision-policy` to the decision: evidence (level, source, retrieved-at, one entry each), confidence from the highest level that supports it, uncertainty (what would change the decision), and missing data (each input it did not have, with the observation that would supply it). A missing measurement is reported missing, never fabricated.

### 4. Report

Return, in this order:

```
WATERING DECISION
  plant:       <plant key>
  decision:    water now | wait | insufficient evidence
  present state: <the measurement, its key, unit and date, and the target it was compared with> | unknown
  evidence:    <level, source, retrieved-at, one entry each>
  priors:      <watering_interval_days and the species and phase requirements, read as priors only> | absent
  confidence:  <the level it rests on, or: no level applies>
  uncertainty: <what would change the decision>
  missing:     <each input it did not have, with the observation that would supply it>
FINDING
  domain: watering | subject: <plant key> | kind: recommendation (water now) or observation (wait, insufficient evidence)
  statement / evidence / confidence / what would change it / missing data, as above
  consequence: <only if an input states one, otherwise absent>
```

Return no field that was not read. Facts that two runs over the same blocks must agree on are the decision, the evidence levels and the missing-data list; retrieval times and prose may differ.

## Hard rules

- Never call a tool. Everything is in the blocks.
- Never return `water now` without named evidence about the plant's present state, and never because a reminder is due, an interval has elapsed, a schedule says so or the plant is expected to be dry.
- Never let a prior (the phase interval, the species data, the phase requirements) or the weather decide alone.
- Never read soil moisture from a key whose meaning or unit is ambiguous, never fabricate a measurement, and never use a Home Assistant sensor as evidence.
- Never fill an absent input or invent a target.
- Never read the current date into the decision facts.

## Gotchas

- Most runs end at `insufficient evidence`: the record has no moisture source of its own, so a plant tended only through reminders has no present-state evidence at all.
- What `watering_interval_days` counts, and whether a species carries a water demand, is not established here. It is read as a level 4 prior and named as such.
- The decision proposes; confirming a care reminder after a person has watered is `watering-decision-apply`, a different recipe, and nothing here waters a plant.
- This skill itself was not run against a live instance; it has no tool calls to get wrong, and its input blocks inherit that status.

## Source

Governed by `spec/process/watering-and-fertilization-decisions/en.md` §A, §B, §F and §G.
