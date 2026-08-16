---
title: Nutrient imbalance check
audience: [plant-owner]
content_mode: how-to
track: user-docs
last_updated: 2026-08-16
---

# Nutrient imbalance check

A plant looks off and the question is whether to feed it. That question has three possible answers, and two of them make feeding the wrong move: the plant may be undersupplied, oversupplied, or unable to take up nutrients it already has. `nutrient-imbalance-check` decides which — for one plant — and proposes a correction only when the evidence establishes the direction.

Yellowing leaves do not settle it. The recipe therefore ranks what it found before it says anything, and refuses when the ranking is too weak.

This run **only reads** your garden. `calculate_mixing_protocol` is the one exception it is allowed to call, because it calculates a mix and persists nothing.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `plant-context-collect` and `nutrient-imbalance-assess` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. A run started elsewhere loses the skill silently and still produces a plausible answer.
- **You need the plant's `plant_key`** — the numeric key, not the readable `instance_id`. [plant-master-data-check](plant-master-data-check.md) prints both side by side.

## Run it

```sh
goose run --recipe nutrient-imbalance-check \
  --params plant_key=11441519 \
  --params tenant=my-garden
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `plant_key` | yes | — |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |

## How it decides

The run collects the plant's context, then reads its diary for a measured value, then ranks everything it holds on one ladder. A lower tier corroborates or contradicts a higher one; it never overrides it.

| Tier | Evidence | Weight |
|:----:|----------|--------|
| 1 | A measured value with a recognisable unit — EC, pH, a runoff reading — from a diary entry | Decides the direction on its own when recent enough |
| 2 | Phase `target_ec_ms` and `npk_ratio` against confirmed feeding frequency and substrate baseline | Decides the direction when tier 1 is absent, at reduced confidence |
| 3 | Care-log pattern alone — feeding frequent, rare, or snoozed; repotting overdue | Supports a direction, never establishes one |
| 4 | Visible symptoms | Localise which nutrient and how far advanced, never the direction |
| 5 | Species `nutrient_demand_level` and phase expectation | Sets the prior only |

**At tier 3 or below the run proposes no dosage.** It names the measurement that would resolve the direction instead. That refusal is the deliverable, not a failed run.

Tier 1 is why the recipe reads the diary itself: it lists the plant's entries, opens up to the eight most recent, and stops at the first `measurements` value carrying an unambiguous unit and a date inside the current phase. Values it cannot pin down are discarded and reported as discarded — a bare `ec: 1.8` may be millisiemens or microsiemens, from the tank or from the runoff, and guessing turns tier 1 evidence into a confident wrong answer.

## Read the outcome

The report opens with a field table — direction, evidence tier, the assigned plan phase and its `target_ec_ms`, the substrate, and what the diary read produced — then gives the reasoning in at most five sentences, each discarded measurement with why, the recommended actions, and how long a correction needs before it shows.

| Closing line | Means |
|--------------|-------|
| `DIRECTION: undersupply (tier <n>)` | the plant is short of what it is being asked to grow with |
| `DIRECTION: oversupply (tier <n>)` | more feeding makes it worse |
| `DIRECTION: unavailable-at-adequate-supply (tier <n>)` | the nutrients are there and the plant cannot reach them — pH, root damage, or the substrate |
| `DIRECTION: undetermined (tier <n>)` | followed by a second line naming the single measurement that would settle it |

## When it says nothing useful

`undetermined` at tier 3 is the ordinary outcome for a plant whose diary holds no measurement, and it is honest rather than lazy. There is currently no tool that records a feeding event with its amount, EC, and pH — so for a garden where reminders get confirmed but quantities never get logged, tier 2 collapses to tier 3 and the answer is a request to measure.

Record one EC or pH reading in a diary entry and re-run: the same plant then answers at tier 1.

## Sources

- [`recipes/nutrient-imbalance-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/nutrient-imbalance-check.yaml) — the parameters, the diary read, and the report format
- [`.claude/skills/nutrient-imbalance-assess/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/nutrient-imbalance-assess/SKILL.md) — the evidence ladder and the refusal rule
- [`spec/process/nutrient-imbalance-detection/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/nutrient-imbalance-detection/en.md) — the process this recipe implements
