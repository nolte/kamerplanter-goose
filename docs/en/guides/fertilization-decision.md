---
title: Fertilization decision
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-03
---

# Fertilization decision

A plant looks pale and the first thought is to feed it. That is the move that makes an oversupplied or uptake-blocked plant worse. `fertilization-decision` takes the [nutrient check](nutrient-imbalance-check.md) for one plant and answers the question a person has: **feed, do not feed, or not enough evidence to say.** It says what the answer rests on, how sure it is, and what would change it.

It decides nothing about the nutrient direction. That comes from the nutrient check, and this recipe reuses it as it is. "Do not feed" is an ordinary result, not a failure.

Two recipes belong together and stay separate:

- **`fertilization-decision`** only reads. It feeds nothing and records nothing.
- **`fertilization-decision-apply`** **writes**: it records one feeding that you carried out. It does not feed, dose or measure anything.

!!! note "Not yet run against a live instance"
    The recipes and the skill were written while the Kamerplanter MCP server was unreachable. Tool names come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md), measured on 2026-08-16. Treat the first real run as the measurement.

## Before you start

- **Start the run from this repository checkout.** The decision recipe loads the project skills `plant-context-collect`, `diary-measurements-read`, `nutrient-imbalance-assess`, `decision-policy` and `fertilization-decision` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.
- **You need the plant's `plant_key`**, the numeric key. [plant-master-data-check](plant-master-data-check.md) prints it next to the readable `instance_id`.

## Decide

```sh
goose run --recipe fertilization-decision \
  --params plant_key=42 \
  --params tenant=my-garden \
  --params water_source_ec="0.3 mS/cm"
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `plant_key` | yes | — |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `water_source_ec` | no | no base-water value is passed: a dose, if one is given at all, is stated for an unknown base water |
| `tank_state` | no | the tank and dosing state is unknown; the server has no field for it |

## What it decides

| The nutrient check says | Decision | Rests on |
|-------------------------|----------|----------|
| undersupply, established as a direction, and no environmental cause named | `feed` | insufficient nutrition |
| oversupply | `do not feed` | insufficient nutrition is ruled out |
| unavailability at adequate supply, or an environmental cause named | `do not feed` | an environmental cause: correct that first |
| direction undetermined, or a suspicion | `insufficient evidence` | an uncertain diagnosis |

- **When the evidence is thin, it prefers the cautious answer.** A plant with no nutrient plan, no diary measurement and only confirmed feeding reminders ends at `insufficient evidence`. The reminders say that a feeding happened, not how much, and the nutrient check treats a frequency without amounts as weak evidence.
- **A dose appears only when the mixing protocol returned one**, and then with the assumption it made about your base water. Without that result the dose is `unknown`; the recipe never gives a concentration, a mixing order or an amount from general knowledge.
- **No sensor is used as evidence.** The record holds no mapping from a Home Assistant sensor to a plant.

## Record a feeding

Once you have fed the plant, you can have the feeding written down:

```sh
goose run --recipe fertilization-decision-apply \
  --params plant_key=42 \
  --params decision=feed \
  --params volume_applied_liters=2 \
  --params ec_before=1.4 \
  --params run_id=2026-11-03-a
```

| Parameter | Required | Meaning |
|-----------|:--------:|---------|
| `plant_key` | yes | the plant that was fed |
| `decision` | yes | the decision you approved; only `feed` is accepted |
| `volume_applied_liters` | yes | the volume you applied, in litres, as a number |
| `ec_before`, `ph_before`, `ec_after`, `ph_after`, `runoff` | no | only what you measured; empty ones are not passed |
| `run_id` | yes | makes a retry traceable and keeps it from writing twice |
| `tenant` | no | the garden slug; needed when your key covers several gardens |

- **It refuses without an approved `feed` decision, without an amount, or with an amount that is not a plain number**, and says which. A value with a unit such as ml is refused, never converted. The amount is the feeding you carried out: it is recorded as you give it, and the run cannot check it. It does not write a record that contradicts the decision.
- **It calls a dry run first**, reports what would be written, and only then writes, with an idempotency key built from the plant and the `run_id`. A dry run that succeeds does not prove that the write will; the result of the real call is reported as returned.
- **What is written is a record.** The run fed nothing, and it does not claim that anything was fed. **It is not measured whether any read tool returns recorded feeding events** ([#54](https://github.com/nolte/kamerplanter-goose/issues/54)), so a recorded feeding may not reach the nutrient check at all.
- The only state-changing tool it calls is the one that records a feeding. It reads the garden list first, and it calls no Home Assistant tool.

## Read the outcome

| Closing line | Means |
|--------------|-------|
| `FERTILIZATION: <decision> — <plant_key>` | the decision recipe's result |
| `FERTILIZATION: not decided — <plant_key>` | a step failed and no decision could be reached |
| `RECORDED: feeding event for <plant_key>` | the record was written |
| `NOT RECORDED: <reason>` | nothing was written, and why |

The decision report carries the decision, what it rests on, the nutrient direction and tier, the dose or `unknown`, the evidence, the confidence, what would change it, and what is missing. The diary read line says how many entries were listed, opened and found without measurements.

## Sources

- [`recipes/fertilization-decision.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/fertilization-decision.yaml) and [`recipes/fertilization-decision-apply.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/fertilization-decision-apply.yaml) — the parameters and the report formats
- [`.claude/skills/fertilization-decision/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/fertilization-decision/SKILL.md) — the decision table and the dose rule
- [`spec/process/watering-and-fertilization-decisions/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/watering-and-fertilization-decisions/en.md) — the process these recipes implement
