---
title: Growth stage check
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Growth stage check

The record says a plant is in a phase because someone entered it, often weeks ago. `growth-stage-check` asks whether that still matches the plant, for one plant: **the recorded stage is consistent, it is questionable, or there is not enough evidence to say.** A questionable stage also says which way it points: the plant looks **ahead** of its record, **behind** it, or the evidence is **unclear**. Every answer says what it rests on, how sure it is, what would change it and what is missing.

The run **only reads**. It changes no phase, writes no diary entry and has no apply recipe. When the stage looks questionable, the report names the phase transition a person might record, and nothing calls it. It calls no Home Assistant tool.

!!! note "Not yet run against a live instance"
    The recipe and the skill were written while the Kamerplanter MCP server was unreachable. Tool names come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md), measured on 2026-08-16. Treat the first real run as the measurement.

## Expect "insufficient evidence"

Age, time in the phase, the cultivar's days to maturity and the species' bloom and harvest months say what is **expected**. They are not a look at the plant, and on their own they place no stage. Something has to say where the plant is now: your own observation (`observations`), a diary measurement that clearly describes development, or a photo reading backed by one of those expectations. Without any of them the honest answer is `insufficient evidence`. **That is the ordinary result, not a failure of the run.** The report says which observation would settle it, usually one sentence from you about what you see.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `plant-context-collect`, `diary-measurements-read`, `plant-photo-read`, `decision-policy` and `growth-stage-assessment` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.
- **You need the plant's `plant_key`**, the numeric key. [plant-master-data-check](plant-master-data-check.md) prints it next to the readable `instance_id`.
- Run [`connectivity-check`](connectivity-check.md) first against a new environment.

## Run it

```sh
goose run --recipe growth-stage-check \
  --params plant_key=42 \
  --params tenant=my-garden \
  --params observations="first flower buds open" \
  --params as_of=2026-06-12
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `plant_key` | yes | — |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `observations` | no | nothing from you about the plant's present development |
| `entry_key` | no | no photo is read |
| `temperatures` | no | no growing degree days: the server has no temperature history |
| `latitude` | no | no outdoor day length: the server has no field for it |
| `light` | no | no indoor light schedule |
| `as_of` | no | the date of the newest diary entry read is used; with none, no timing is computed |

## What it decides

| What is known | Result |
|---------------|--------|
| the phase is unresolved or absent | `insufficient evidence` |
| your observation, an inspection or a clear measurement that matches the recorded phase | `recorded stage consistent` |
| one of those that contradicts the recorded phase | `recorded stage questionable` |
| a photo reading, matching or contradicting, backed by a timing expectation | consistent or questionable |
| only expectations, growing degree days or an unbacked photo | `insufficient evidence` |

- **An unresolved phase is not a normal phase.** The phase status can answer `unresolved`, which reads like a result and is not; the report says the recorded stage is absent.
- **Growing degree days are context.** They are computed only from a daily series you supply and the species' base temperature, with the method and the span stated. No growing-degree-day target for a stage or for maturity is recorded, so they never place a stage on their own.
- **Day length is computed, the plant's response to it is not known.** Outdoors from your latitude, indoors from your light schedule. No species field records sensitivity to day length, so the report says `no source` for it.
- **Give `as_of` with `observations`.** Your observation carries no date, so with `observations` and no `as_of` the run computes no time-based comparison at all (days in the phase, days since planting, month windows, growing degree days, day length) and says why. A photo entry's date counts only when the run read that diary entry and it belongs to the plant.
- **The phase history is reported as it comes back.** Its fields are not recorded anywhere here, so nothing is assumed about them.

## Read the outcome

| Closing line | Means |
|--------------|-------|
| `GROWTH STAGE: recorded stage consistent — <plant_key>` | an observation of the plant matches its recorded phase |
| `GROWTH STAGE: recorded stage questionable (<direction>) — <plant_key>` | an observation contradicts it; check the plant and decide whether to record another phase |
| `GROWTH STAGE: insufficient evidence — <plant_key>` | nothing says where the plant is now; the report names what would |
| `GROWTH STAGE: not assessed — <plant_key>` | a step failed and no assessment could be reached |

The report also carries a hand-off block for harvest planning: the recorded and the estimated stage, the days in the phase against its typical duration, the days since planting against the cultivar's days to maturity, the growing degree days with their inputs, and the day length, each marked absent with its reason where it is.

## Sources

- [`recipes/growth-stage-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/growth-stage-check.yaml) — the parameters and the report format
- [`.claude/skills/growth-stage-assessment/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/growth-stage-assessment/SKILL.md) — the decision table, the derivations and the hand-off block
- [`spec/process/growth-stage-and-weather-impact/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/growth-stage-and-weather-impact/en.md) — the process this recipe implements
