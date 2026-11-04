---
title: Plant health assessment
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Plant health assessment

A plant that looks wrong invites one confident answer. `plant-health-assessment` gives you the honest version for one plant: **the candidate explanations side by side, which of them survive, and what would tell the survivors apart.** It runs the checks that already exist — nutrients, pests and diseases, growth stage, weather — and combines what they return with your own observation, an optional photo, the diary's measurements and the plant's care history. It never calls the result a diagnosis.

The run **only reads**. It treats nothing, records nothing and has no apply recipe. It calls no Home Assistant tool: weather comes only from what you supply.

!!! note "Not yet run against a live instance"
    The recipe and the skill were written while the Kamerplanter MCP server was unreachable. Tool names come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md), measured on 2026-08-07 and 2026-08-16. Treat the first real run as the measurement.

## Expect "suspicion only"

Seven candidate classes are considered: `nutrient`, `pest`, `disease`, `water`, `environment`, `development` and `abiotic handling/site`. A candidate is **supported** only when the check that owns it returned its own positive result and something else that is not the symptom itself backs it up. One yellow leaf, one photo or one "the weather was consistent with it" is a **suspicion**, never more. And no check is overruled: a pest the pest check left *not contradicted* stays *not contradicted* here.

So most runs end at `suspicion only` or `competing explanations`. **That is the useful result, not a weak one**: the report names, for each pair of surviving candidates, the one observation that would separate them — often "look at the leaf undersides" or "take one substrate moisture reading". Without your observation, a photo or a recorded inspection there is no symptom to assess, and the answer is `insufficient evidence`.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `plant-context-collect`, `diary-measurements-read`, `plant-photo-read`, `nutrient-imbalance-assess`, `pest-pressure-assess`, `growth-stage-assessment`, `weather-impact-analysis`, `decision-policy` and `plant-health-assessment` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.
- **You need the plant's `plant_key`**, the numeric key. [plant-master-data-check](plant-master-data-check.md) prints it next to the readable `instance_id`.
- Run [`connectivity-check`](connectivity-check.md) first against a new environment.

## Run it

```sh
goose run --recipe plant-health-assessment \
  --params plant_key=42 \
  --params tenant=my-garden \
  --params observations="lower leaves yellow between the veins, fine webbing under the leaves" \
  --params as_of=2026-06-12
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `plant_key` | yes | — |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `observations` | no | nothing from you about what the plant looks like |
| `entry_key` | no | no photo is read |
| `weather` | no | every weather factor is `no source`; the `environment` candidate is not assessable |
| `placement` | no | every weather exposure is conditional on where the plant stands |
| `as_of` | no | the date of the newest diary entry read is used; with none, or with `observations` and no `as_of`, no timing is computed |

## What it decides

| Overall result | Means |
|----------------|-------|
| `leading explanation` | exactly one candidate is supported; any suspicions are listed beside it |
| `competing explanations` | two or more candidates are supported, and the report says what would separate them |
| `suspicion only` | nothing is supported, but at least one candidate is a suspicion |
| `no abnormality reported` | the sources that were read report nothing abnormal |
| `insufficient evidence` | there was no symptom source at all, or no check could say anything |

- **Weather is an exposure, not a symptom.** Exposures are listed in a block of their own, and a symptom is linked to one only as "consistent with". The `environment` candidate is therefore a suspicion at most.
- **The health item is an observation.** In the [daily garden check](daily-garden-check.md) it sits beside the other checks' items and cites them; it never repeats their recommendations, so nothing is counted twice.
- **A pest or disease suspicion goes on to the IPM plan.** The report hands the candidate, as the pest check left it, to the [pest IPM plan](pest-ipm-plan.md), which says what to do about it and in which order.

## Read the outcome

| Closing line | Means |
|--------------|-------|
| `HEALTH: leading explanation — <plant_key>` | one candidate is supported by its own check and a second piece of evidence |
| `HEALTH: competing explanations — <plant_key>` | several are; make the discriminating observation before acting |
| `HEALTH: suspicion only — <plant_key>` | the usual result; the report names what would settle it |
| `HEALTH: no abnormality reported — <plant_key>` | nothing that was read looks wrong |
| `HEALTH: insufficient evidence — <plant_key>` | nothing says what the plant looks like now; give `observations` or a photo |
| `HEALTH: not assessed — <plant_key>` | a step failed and no differential could be reached |

## Sources

- [`recipes/plant-health-assessment.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/plant-health-assessment.yaml) — the parameters and the report format
- [`.claude/skills/plant-health-assessment/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/plant-health-assessment/SKILL.md) — the candidate classes, the statuses and the overall results
- [`spec/process/plant-health-and-ipm-planning/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/plant-health-and-ipm-planning/en.md) — the process this recipe implements
