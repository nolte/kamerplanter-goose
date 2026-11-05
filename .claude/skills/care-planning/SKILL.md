---
name: care-planning
description: "Puts the results a garden's domain checks already returned next to each other and orders them for a person: every item is an observation, a recommendation or a named mutation, each recommendation carries evidence, confidence, uncertainty and missing data, items are ordered by urgency then confidence, and a state with no evidence yields no action and says what would supply it. Use when a daily or periodic garden check must say what to look at first, or when a domain such as nutrients or pests must plug into one list. Never derives urgency from a due reminder or general knowledge, never substitutes a domain that is not available, and calls no tool: the plan is a function of the blocks it is given."
---

# Plan the care

Turns what the domain checks returned into one ordered list a person can act on, or into an honest "nothing to do". It makes no tool call: everything it needs is in the blocks it is handed, which is what lets two runs over the same blocks give the same plan. It writes nothing and decides nothing about a plant. The garden's facts are `garden-context`, the weight of a claim is `decision-policy`, and the judgement of one question stays with the domain that owns it (`nutrient-imbalance-assess`, `pest-pressure-assess`).

## Input

- **The garden context block** from `garden-context`: the due tasks, the planting runs, and the list of absent fields.
- **Domain reports**, one per plant per domain that ran: the reports of `nutrient-imbalance-assess` and `pest-pressure-assess`, as they returned them, and the findings of `watering-decision`, `fertilization-decision`, `growth-stage-assessment`, `weather-impact-analysis`, `plant-health-assessment` and `pest-ipm-planning`, which already have the shape of step 1.
- **Domain statuses**, from the caller, one per domain: `checked`, `not available` (with the skill that would provide it) or `not checked` (with why).
- **The plan document** from `plant-planning`, optional. Read per run: the run identifier, the species and cultivar key, the method, the windows and the confidence.

Without the garden context block, stop and say that `garden-context` must run first. A plan that was not supplied is absent, which is not the same as having no planting runs.

## Procedure

### 1. Make findings

Map each domain report into a finding with exactly these fields: the domain, the subject (a plant key or the garden), the kind (observation or recommendation), the statement, the evidence entries (level, source, retrieved-at), the confidence, what would change it, the missing data, and the consequence only if the domain stated one. Add no field the domain did not return.

- **Levels** come from the table "How the existing ladders relate" in `decision-policy`. Where it gives none, write `no level`: the nutrient tier 2 (a plan target against reconstructed supply, which needs recorded dose amounts) and symptoms read from an image.
- **A report that leaves the direction undetermined**, names a suspicion, or stays below its process's refusal threshold is an **observation**. Only a result that proposes an action is a **recommendation**.
- **The watering and fertilisation decisions, the growth-stage assessment and the weather-impact analysis** return findings in this shape themselves: take them as they return them, and map nothing. Their recommendations carry no stated consequence today unless an input states one, so they rank `routine`. A questionable growth stage names the phase-transition tool as its mutation, and a weather exposure names none (`no tool measured`); carry both into step 3 as named. A weather exposure is never a symptom of the plant: keep it apart from the symptoms the other domains report. Without a stated placement a weather exposure is conditional and arrives as an observation; never raise it to a recommendation.
- **The plant health assessment** returns one finding per plant, and it is always an **observation**: the differential, citing the other domains' findings by domain. Carry it as an observation and never raise it; never count a domain's finding a second time through it, and take no recommendation from it. **The IPM plan** returns one finding per step: a monitoring step names the inspection-recording tool as its mutation, and a treatment names none (`no tool measured`); carry both into step 3 as named. A treatment the plan excluded, or left not recommendable, arrives as an observation; never raise it.
- **Pest report and IPM plan for the same plant**: when the IPM plan ran for a plant, map the `pest-pressure-assess` report of that plant into an **observation only** (the candidate, the tier, the tests run and not run), and take every measure, monitoring and treatment alike, only from the IPM findings. Never make a recommendation from the pest report then, so no measure is counted twice. When the IPM plan did not run for a plant, map the pest report as the bullets above say.
- A domain that returned nothing is absent, with the reason. Never fill it from general knowledge and never take another domain's result in its place.

### 2. Carry the due tasks

A due care task from the garden context is a request from the schedule, not a measurement. Carry it as an observation with the urgency `routine`. Derive no recommendation from it: a task being due is not evidence about the plant's present state.

### 3. Name the mutations

A recommendation that a later apply step would carry out names the state-changing tool it would call and the item that justifies it. If the measured catalog has no such tool, say `no tool measured`. This skill never calls one, never schedules one, and never words a recommendation as an instruction to a device or a write.

### 4. Set urgency

From stated fields only:

| Urgency | When |
|---------|------|
| `now` | the finding's consequence states harm that is present or advancing |
| `soon` | the consequence states harm that follows if nothing is done |
| `routine` | a recommendation with no stated consequence, and a due care task |
| `watch` | an observation |

Never derive urgency from general knowledge, from how long a reminder has been due, or from a due task beyond `routine`.

### 5. Order

Order the items by urgency (`now`, `soon`, `routine`, `watch`), then by confidence (higher evidence level first, `no level` last), then by subject key, then by domain, as text. The order of the input has no effect. Confidence comes from the highest `decision-policy` level that supports the item; when none applies, say that no level applies.

### 6. List what has no action

For each plant or garden state that has no evidence about its present state, make no action. List it under `NO ACTION, EVIDENCE INSUFFICIENT` with the observation that would supply it. List every domain that is not available or not checked there too. An empty plan, with every plant and domain accounted for, is a valid result.

### 7. Report

Return these blocks, in this order and under these names:

```
CARE PLAN HEADER
  garden:     <tenant> (given | discovered)
  made from:  <the blocks received: garden context, domain reports, statuses, plan>
  absent:     <the blocks or fields that were not supplied, each with its reason>
  not claimed: byte-identical prose outside the plan facts
ITEMS
  ITEM <subject>/<domain>/<kind>/<n>
    kind:        observation | recommendation
    urgency:     now | soon | routine | watch
    statement:   <what was read, or what is proposed to a person>
    evidence:    <level, source, retrieved-at, one entry each>
    confidence:  <the level it rests on, or: no level applies>
    uncertainty: <what would change it>
    missing:     <each input it did not have, with the observation that would supply it>
MUTATIONS (NAMED, NEVER CALLED)
  <item id>: <the state-changing tool a later apply step would call | no tool measured>
NO ACTION, EVIDENCE INSUFFICIENT
  <subject or domain>: <why, and the observation that would supply the evidence>
DOMAINS
  <domain>: checked | not available (<skill>) | not checked (<why>)
```

The `<n>` in an item id numbers the items of one subject, domain and kind in the order of their statement text, never in the order of the input. Return no field that was not read. Facts that two runs over the same blocks must agree on are the item ids, kinds, urgencies, the order, the confidence levels, the named mutations and the no-action entries; retrieval times and prose may differ.

## Hard rules

- Never call a tool. Everything is in the blocks.
- Never derive an action from a due task alone, and never derive urgency from general knowledge or the age of a reminder.
- Never return a recommendation without its evidence, confidence, uncertainty and missing data.
- Never assign an evidence level where `decision-policy` gives none; write `no level`.
- Never substitute one domain's result for another, and never fill an absent domain.
- Never present a mutation as done or as scheduled: it is named, with the tool, and nothing more.
- Never read the current date into the plan facts, and never pad a plan to look useful.

## Gotchas

- A garden where every domain reports a suspicion or nothing gives a plan of `watch` items and a long no-action list. That is the honest result when evidence is thin, not a failure.
- The existing domain reports are prose with a tier, not structured findings. This skill does the mapping; if a domain's wording leaves the kind unclear, treat it as an observation and say why.
- The response fields of the due-task read are not recorded in any spec here, so no overdue computation is made; a due task is `routine` at most.
- This skill itself was not run against a live instance; it has no tool calls to get wrong, and its input blocks inherit that status.

## Source

Governed by `spec/process/care-planning-and-daily-check/en.md` §A to §H.
