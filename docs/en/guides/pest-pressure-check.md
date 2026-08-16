---
title: Pest pressure check
audience: [plant-owner]
content_mode: how-to
track: user-docs
last_updated: 2026-08-16
---

# Pest pressure check

You suspect something is eating a plant, and you want to know whether that suspicion survives contact with the record before you spray anything. `pest-pressure-check` tests one suspicion against what the garden actually holds — the plant's context, its inspection history, and the pest or disease catalogue — and names a control measure only when the identification supports one.

"Not contradicted" is a common and legitimate result. It is weaker than "identified", and the recipe is written to keep the two apart.

This run **only reads** your garden. It never records an inspection, confirms a task, or actuates anything.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `plant-context-collect` and `pest-pressure-assess` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. A run started elsewhere loses the skill silently and still produces a plausible answer.
- **You need the plant's `plant_key`** — the numeric key, not the readable `instance_id`. [plant-master-data-check](plant-master-data-check.md) prints both.

## Run it

```sh
goose run --recipe pest-pressure-check \
  --params plant_key=11441519 \
  --params suspicion="sticky leaves, small white flies on the underside" \
  --params tenant=my-garden
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `plant_key` | yes | — |
| `suspicion` | no | the run works from the plant's recorded inspection history alone |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |

`suspicion` takes either a symptom you observed or an organism you suspect. Describing what you saw is usually the better input: naming the organism invites the run to confirm it, describing the symptom lets it rule candidates out.

## How it decides

Every claim is ranked by what it rests on, and a lower tier never overrides a higher one.

| Tier | Evidence | Weight |
|:----:|----------|--------|
| 1 | A recorded inspection naming the organism, with pressure level and findings | Establishes presence on its own |
| 2 | Catalogue fields — `pest_type`, `lifecycle_days`, `optimal_temp_*`, `damage_symptoms`, or a disease's `environmental_triggers` | Confirms or falsifies a candidate; never establishes presence |
| 3 | Situation fit — species category, phase, season, care history, enclosure | Narrows the candidate set, never selects from it |
| 4 | Visible symptoms from a photo | Localise and stage. Establish presence only for an organism visible as itself, never for one inferred from its damage |
| 5 | General knowledge of the taxon that is not in the record | Reasoning aid only, and always labelled "not recorded" |

**A treatment is proposed only on tier 1, or on tier 4 plus an uncontradicted tier 2.** Below that the deliverable is the observation that would resolve it — usually a named monitoring method, not another photo.

The pest catalogue is thinner than the disease catalogue, and the recipe says so rather than filling the gap. `get_pest` carries no host plants, no humidity ecology, no monitoring hints and no affected plant parts, so any argument resting on those runs at tier 5. `get_disease` carries `environmental_triggers`, `incubation_period_days`, and `pathogen_type`, so the same moisture argument runs at tier 2 for a disease. The report states which of the two it is in.

## Read the outcome

The report opens with a field table — candidate, status, evidence tier, inspection count, and the tests the record could not support — then gives the reasoning in at most five sentences, each rejected candidate with the test that rejected it, and the recommended measures in IPM order with their safety intervals checked against the plant's harvest situation.

| Closing line | Means |
|--------------|-------|
| `PEST: identified — <candidate> (tier <n>)` | presence is established, and a measure may follow |
| `PEST: not contradicted — <candidate> (tier <n>)` | the candidate survived every test that could run, which is not the same as being present |
| `PEST: rejected — <candidate> (tier <n>)` | a test ruled the candidate out |
| `PEST: undetermined — none (tier <n>)` | nothing tenable; a second line names the single observation that would settle it |

Anything short of `identified` closes with that second line. Two measures sharing an active ingredient are never offered as alternatives, because that selects for resistance — and where the record carries no active ingredient at all, the report says the rotation claim cannot be made.

A defect the run finds in the catalogue itself is reported as such, directed at [nolte/kamerplanter](https://github.com/nolte/kamerplanter) rather than silently worked around.

## Sources

- [`recipes/pest-pressure-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/pest-pressure-check.yaml) — the parameters and the report format
- [`.claude/skills/pest-pressure-assess/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/pest-pressure-assess/SKILL.md) — the evidence ladder, the falsification tests, and what the record does not carry
- [`spec/process/pest-pressure-assessment/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/pest-pressure-assessment/en.md) — the process this recipe implements
