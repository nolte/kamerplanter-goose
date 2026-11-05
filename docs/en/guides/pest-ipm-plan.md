---
title: Pest IPM plan
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Pest IPM plan

Once a pest or a disease is suspected, the tempting step is a spray. `pest-ipm-plan` orders what could be done for one plant the way integrated pest management does: **first confirm and monitor, then correct the environment, then cultural and mechanical controls, and a targeted treatment only when it is justified.** It first runs the same assessment as the [pest pressure check](pest-pressure-check.md) on the suspicion, and plans only for the candidate that check names, exactly as it left it.

The run **only reads**. It treats nothing, releases nothing and records nothing, not even an inspection; it has no apply recipe. A monitoring step names the inspection a later apply step would record, and nothing calls it. It calls no Home Assistant tool.

!!! note "Not yet run against a live instance"
    The recipe and the skill were written while the Kamerplanter MCP server was unreachable. Tool names come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md), measured on 2026-08-07 and 2026-08-16. Treat the first real run as the measurement.

## Expect "treatment not justified"

A treatment is reached only at the pest check's own threshold: a recorded inspection naming the organism, or a photo showing it together with catalogue data that do not contradict it. This recipe reads no photo, so here the threshold is met only by a recorded inspection; for photo evidence, run the [plant health assessment](plant-health-assessment.md) with `entry_key`. A described symptom alone does not reach it. **Below the threshold the plan stops after the cultural and mechanical stage** and names the monitoring method that would raise the evidence — a sticky trap, checking the leaf undersides yourself with a hand lens, an inspection of the affected part. That is the ordinary result, and the monitoring step is the useful part.

Monitoring methods, and a pest's preference for dry or humid air, are **not recorded** in the pest catalogue; the plan labels them as general knowledge. A disease is better served: its record names the environmental triggers, and the environmental correction quotes them. **An environmental side that was not assessed blocks every treatment**: correct the environment before treating the plant. This recipe runs no health assessment, so for a pest the environmental side is always not assessed here, and a pest treatment is never recommendable from this recipe alone; the report says what would assess it.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `plant-context-collect`, `pest-pressure-assess`, `growth-stage-assessment`, `decision-policy` and `pest-ipm-planning` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.
- **You need the plant's `plant_key`**, the numeric key. [plant-master-data-check](plant-master-data-check.md) prints it next to the readable `instance_id`.
- **For a plant you will harvest, give `harvest_date` and `as_of`.** Without a time to harvest, no treatment on it can be recommended (see below).
- Run [`connectivity-check`](connectivity-check.md) first against a new environment.

## Run it

```sh
goose run --recipe pest-ipm-plan \
  --params plant_key=42 \
  --params tenant=my-garden \
  --params suspicion="fine webbing and stippling on the leaf undersides" \
  --params placement="greenhouse" \
  --params harvest_date=2026-07-20 \
  --params as_of=2026-06-12
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `plant_key` | yes | — |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `suspicion` | no | the plan works from the plant's recorded inspection history alone |
| `placement` | no | enclosed or open is stated as inferred; introducing beneficials and conserving them are different advice |
| `harvest_date` | no | the time to harvest comes from the cultivar's days to maturity, or is not established |
| `as_of` | no | no time to harvest can be computed |

## Safety interval and harvest date

Every treatment in the plan carries a fixed block:

- **Prerequisites**: the identification meets the threshold, with its tier; the earlier stages are done or unavailable, with the reason; whether the plant may be harvested, and the time left until the harvest; and the product label and local plant-protection rules, which are **not in the record**: always listed as "confirm before applying", and yours to check. They do not decide whether a treatment is recommendable; the other prerequisites do.
- **Safety constraints**, quoted from the record exactly as it holds them, never scaled or converted: the safety interval in days, the protective equipment, the dosage per litre, the application method and the active ingredient.
- **Exclusions**: a treatment whose safety interval is longer than the time left until the harvest is **excluded**. On a plant that may be harvested, a treatment is **not recommendable** when the time to harvest is not known, or when the record carries no safety interval for it, because its interval cannot be checked. A missing interval is never read as zero. Two treatments sharing an active ingredient are never offered as alternatives.

The time to harvest is your `harvest_date` minus `as_of`, or, without a harvest date, the cultivar's days to maturity minus the days since planting. That fallback assumes one harvest at maturity and ignores an early or continuous harvest — baby leaf, herbs, cut-and-come-again — so give `harvest_date` for those. It is never taken from the server's harvest-readiness tool, whose answer is not recorded anywhere here.

Biological measures come before chemical ones, and a beneficial is checked against what it actually preys on. That a broad-spectrum product wipes out a beneficial release is general knowledge the record does not carry; the plan states it as such.

## Read the outcome

| Closing line | Means |
|--------------|-------|
| `IPM: <n> steps, treatment justified — <plant_key>` | at least one treatment meets the threshold and every prerequisite holds; read its safety block before acting |
| `IPM: <n> steps, treatment not justified — <plant_key>` | the usual result: the candidate is below the threshold, or every treatment is excluded or cannot be checked |
| `IPM: <n> steps, treatment not applicable — <plant_key>` | the pest check names no pest or disease candidate |
| `IPM: not planned — <plant_key>` | a step failed and no plan could be reached |

## Sources

- [`recipes/pest-ipm-plan.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/pest-ipm-plan.yaml) — the parameters and the report format
- [`.claude/skills/pest-ipm-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/pest-ipm-planning/SKILL.md) — the four stages, the threshold and the treatment block
- [`spec/process/plant-health-and-ipm-planning/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/plant-health-and-ipm-planning/en.md) — the process this recipe implements
