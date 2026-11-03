---
title: Watering decision
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-03
---

# Watering decision

A reminder says the plant is due. It does not say the plant is dry. `watering-decision` answers the question a person has, for one plant: **water now, wait, or not enough evidence to say.** It says what the answer rests on, how sure it is, and what would change it. It never waters because a reminder is due, because an interval has elapsed, or because the plant is expected to be dry.

Two recipes belong together and stay separate:

- **`watering-decision`** only reads. It waters nothing and records nothing.
- **`watering-decision-apply`** **writes**: it confirms one care reminder because you say you acted on it. It does not water anything and cannot check that you did.

!!! note "Not yet run against a live instance"
    The recipes and the skill were written while the Kamerplanter MCP server was unreachable. Tool names come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md), measured on 2026-08-16. Treat the first real run as the measurement.

## Expect "not enough evidence"

The measured catalog has one source of a plant's present state: a moisture value you recorded in a diary entry of that plant. A plant tended only through reminders has none, and then the honest answer is `insufficient evidence`. **That is the ordinary result, not a failure of the run.** The result says which observation is missing, usually one moisture reading recorded in a diary entry, and which target it would be compared with.

## Before you start

- **Start the run from this repository checkout.** The decision recipe loads the project skills `plant-context-collect`, `diary-measurements-read`, `decision-policy` and `watering-decision` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.
- **You need the plant's `plant_key`**, the numeric key. [plant-master-data-check](plant-master-data-check.md) prints it next to the readable `instance_id`.

## Decide

```sh
goose run --recipe watering-decision \
  --params plant_key=42 \
  --params tenant=my-garden \
  --params constraints="keep the substrate moisture between 30 and 50 %"
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `plant_key` | yes | — |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `weather` | no | weather and forecast are unknown; the server has no source for them |
| `container` | no | the container or bed is unknown; the server has no field for it |
| `constraints` | no | no moisture target is stated, so a reading has nothing to be compared with (the measured record carries none) |

## What it decides

| What is known about the present state | Decision |
|---------------------------------------|----------|
| a recent, unambiguous moisture reading of this plant on the dry side of a stated target | `water now` |
| a recent, unambiguous reading within the target, or on the wet side | `wait` |
| a reading with no target, an ambiguous key or unit, or one too old | `insufficient evidence` |
| no reading at all | `insufficient evidence` |

- **A phase's watering interval, the species data and the phase requirements are priors.** They say what is normal and decide nothing alone; the report lists them as priors.
- **Weather you supply may change how sure the answer is, never the answer alone.**
- **No sensor is used as evidence.** The record holds no mapping from a Home Assistant sensor to a plant, and a moisture value from an ambiguous diary key is discarded, not guessed at.

## Confirm a reminder

Once you have watered, you can have the reminder confirmed:

```sh
goose run --recipe watering-decision-apply \
  --params plant_key=42 \
  --params decision="water now" \
  --params reminder_type=<the type as your care log records it> \
  --params run_id=2026-11-03-a
```

| Parameter | Required | Meaning |
|-----------|:--------:|---------|
| `plant_key` | yes | the plant whose reminder you acted on |
| `decision` | yes | the decision you approved; only `water now` is accepted |
| `reminder_type` | yes | the type of the reminder to confirm, exactly as your care log records it for a confirmed reminder |
| `run_id` | yes | makes a retry traceable and keeps it from writing twice |
| `tenant` | no | the garden slug; needed when your key covers several gardens |

- **You name the reminder type.** No list of reminder types is recorded in this repository, so the run never guesses or defaults one.
- **It refuses without an approved `water now` decision or without a reminder type**, and says which. It does not write a confirmation that contradicts the decision. The reminder type is recorded as you give it, and the run cannot check it.
- **It calls a dry run first**, reports what would be written, and only then writes, with an idempotency key built from the plant and the `run_id`. A dry run that succeeds does not prove that the write will; the result of the real call is reported as returned.
- **What is written is a record: the confirmation of a care reminder.** The run watered nothing and did not check that the plant was watered.
- It calls no tool other than the one that confirms a care reminder, and no Home Assistant tool.

## Read the outcome

| Closing line | Means |
|--------------|-------|
| `WATERING: <decision> — <plant_key>` | the decision recipe's result |
| `CONFIRMED: care task for <plant_key>` | the confirmation was written |
| `NOT CONFIRMED: <reason>` | nothing was written, and why |
| `WATERING: not decided — <plant_key>` | a step failed and no decision could be reached |

The decision report carries the decision, the present state it rests on or `unknown`, the evidence, the priors, the confidence, what would change it, and what is missing. The diary read line says how many entries were listed, opened and found without measurements.

## Sources

- [`recipes/watering-decision.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/watering-decision.yaml) and [`recipes/watering-decision-apply.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/watering-decision-apply.yaml) — the parameters and the report formats
- [`.claude/skills/watering-decision/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/watering-decision/SKILL.md) — the decision table and the evidence rules
- [`spec/process/watering-and-fertilization-decisions/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/watering-and-fertilization-decisions/en.md) — the process these recipes implement
