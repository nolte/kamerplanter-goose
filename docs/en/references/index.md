---
title: References
audience: [recipe-author, self-hoster, maintainer]
content_mode: meta
track: developer-docs
last_updated: 2026-11-06
---

# References

Reference material: the shipped recipes with their parameters, the shared MCP extension definitions, the project skills, and the environment variables every run consumes.

## Recipes

A recipe that loads project skills must be started with this repository checkout as the working directory, because skill discovery is relative to the Goose process's working directory. `connectivity-check`, `provider-surface-check`, and `plant-master-data-check` load none and run from anywhere — which is what lets them be used over `GOOSE_RECIPE_GITHUB_REPO`.

`provider-plugin-check` loads no skill either and still needs this checkout: its last three probes dispatch agents defined in this tree. Started elsewhere it reports them as unreachable, which is a wrong measurement rather than a failed run — and indistinguishable from the genuine result for one of the two directories it compares.

Each recipe has a guide of its own, linked from its name.

| Recipe | Writes | Purpose |
|--------|:------:|---------|
| [`connectivity-check`](../guides/connectivity-check.md) | no | Probes both MCP servers read-only and prints PASS/FAIL per step |
| [`provider-surface-check`](../guides/provider-surface-check.md) | no | Inventories the tools the agent actually holds under the current provider |
| [`provider-plugin-check`](../guides/provider-plugin-check.md) | no | Whether plugin skills, plugin agents, and project agents are reachable from a run |
| [`nutrient-imbalance-check`](../guides/nutrient-imbalance-check.md) | no | Undersupply, oversupply, or unavailability at adequate supply, for one plant |
| [`pest-pressure-check`](../guides/pest-pressure-check.md) | no | Whether a pest or disease suspicion is biologically tenable |
| [`daily-garden-check`](../guides/daily-garden-check.md) | no | What deserves attention in a garden today, ordered by urgency; applies nothing |
| [`watering-decision`](../guides/watering-decision.md) | no | Water now, wait, or not enough evidence, for one plant; waters nothing |
| [`watering-decision-apply`](../guides/watering-decision.md) | **yes** | Confirms one care reminder a person says they acted on |
| [`fertilization-decision`](../guides/fertilization-decision.md) | no | Feed, do not feed, or not enough evidence, for one plant; feeds nothing |
| [`fertilization-decision-apply`](../guides/fertilization-decision.md) | **yes** | Records one feeding a person carried out |
| [`growth-stage-check`](../guides/growth-stage-check.md) | no | Recorded stage consistent, questionable (ahead, behind, unclear), or not enough evidence, for one plant; changes no phase |
| [`weather-impact-check`](../guides/weather-impact-check.md) | no | Per weather factor an exposure, none, or no source, for up to five plants; actuates nothing |
| [`plant-health-assessment`](../guides/plant-health-assessment.md) | no | A differential for one plant: leading or competing explanations, suspicion only, nothing abnormal, or not enough evidence; never a diagnosis |
| [`pest-ipm-plan`](../guides/pest-ipm-plan.md) | no | Four IPM stages for a pest or disease suspicion, a treatment only at the threshold and with its safety block; treats and records nothing |
| [`harvest-readiness-check`](../guides/harvest-readiness-check.md) | no | Ready, approaching, not ready, not harvestable or not enough evidence, for one plant, with its safety-interval gate; harvests nothing |
| [`harvest-plan`](../guides/harvest-plan.md) | no | The harvests of up to five plants in one order, with windows and workload counts; schedules nothing |
| [`garden-review`](../guides/garden-review.md) | no | A garden's history so far, plant by plant, with lessons and a next-cycle block; writes nothing |
| [`garden-review` `season=…`](../guides/season-review.md) | no | A season's history, archived plants included, handed to the next plan; writes nothing |
| [`species-baseline-check`](../guides/species-baseline-check.md) | no | Whether a species record is plausible, and what its lifecycle is |
| [`garden-context-check`](../guides/garden-context-check.md) | no | Which parts of a garden's context are known and which are absent |
| [`crop-selection`](../guides/crop-selection.md) | no | Which candidate crops a site supports, and which constraints it fails |
| [`planting-calendar`](../guides/planting-calendar.md) | no | When each chosen crop can be sown, transplanted and harvested at a garden |
| [`garden-plan`](../guides/garden-plan.md) | no | Planting-run proposals for chosen crops, for review; applies nothing |
| [`garden-plan` `view=months`](../guides/season-plan.md) | no | The plan laid on twelve months, with its successions |
| [`crop-rotation-plan`](../guides/crop-rotation-plan.md) | no | One plant family per bed and season, with verdicts and conflicts; records nothing |
| [`succession-plan`](../guides/succession-plan.md) | no | Sequential and staggered successions per bed for one season; records nothing |
| [`bed-layout-plan`](../guides/bed-layout-plan.md) | no | Runs per bed with capacity per month, conflicts and runs not placed; records nothing |
| [`plant-master-data-check`](../guides/plant-master-data-check.md) | no | Which plants lack the master data a later analysis would need |
| [`domain-review`](../guides/domain-review.md) | to `.audits/` only | Reviews a recipe or spec as one grower persona |
| [`diary-photo-analysis-apply`](../guides/diary-analysis-queue.md) | **yes** | Analyses one queued diary entry and submits the result |
| [`diary-analysis-queue-apply`](../guides/diary-analysis-queue.md) | **yes** | Works through the analysis queue, entry by entry |

## Project skills

Loaded by name from `.claude/skills/`. Discovery is relative to the Goose process's working directory.

**Garden procedures** — read the Kamerplanter MCP server:

| Skill | Answers |
|-------|---------|
| `plant-context-collect` | What is normal for this specific plant |
| `plant-photo-read` | What a diary photo shows, against that context |
| `nutrient-imbalance-assess` | Which direction a nutrient problem runs |
| `pest-pressure-assess` | Whether a pest suspicion survives its falsification tests |
| `species-baseline-verify` | Whether the species record can be trusted |
| `plant-lifecycle-resolve` | Annual, biennial or perennial, and the windows that follow |
| `diary-analysis-claim` | The claim-and-submit handshake for the analysis queue |
| `garden-context` | What is known about a garden, and what is absent |
| `decision-policy` | How far a recommendation may be trusted; reads no garden, works on the evidence it is given |
| `site-analysis` | What is known about a site, parameter by parameter, and what is not |
| `crop-selection` | Which candidate crops a site supports, with reasons and failed constraints |
| `planting-calendar` | The sowing, transplanting and harvest windows per crop and growing period, with the rule behind each |
| `plant-planning` | Planting-run proposals with identifiers, rationale and confidence; calls no tool |
| `rotation-history-collect` | Each crop's family, demand class and green-manure suitability, and the plants and inspections per location, archived included |
| `crop-rotation-planning` | One family per bed and season, with a verdict and its rule for every crop considered and every conflict named; calls no tool |
| `companion-spacing-collect` | Each crop's catalog companions with their scores, and its seed density as context only |
| `succession-planning` | Which runs can follow each other in one bed, and staggered sowings at the caller's interval; calls no tool |
| `bed-layout-planning` | Which run stands in which bed, its need, and the capacity per bed and month; calls no tool |
| `diary-measurements-read` | The recorded measurements of one plant's diary, with a report of how much was read |
| `care-planning` | The domain results put into one list ordered by urgency, with what has no action; calls no tool |
| `watering-decision` | Water now, wait, or insufficient evidence, from the plant's present state; calls no tool |
| `fertilization-decision` | Feed, do not feed, or insufficient evidence, from the nutrient assessment; calls no tool |
| `growth-stage-assessment` | Recorded stage consistent, questionable or insufficient evidence, from observations against timing expectations; reads the phase status and history |
| `weather-impact-analysis` | Weather exposures per factor, kept apart from symptoms; reads one Home Assistant weather entity only where permitted |
| `plant-health-assessment` | Candidate explanations per class, each supported, suspicion, contradicted or not assessable, and one overall result; calls no tool |
| `pest-ipm-planning` | Confirmation, environmental correction, cultural controls and targeted treatment in order, with prerequisites and safety constraints per treatment; reads the candidate's catalogue records |
| `harvest-planning` | Ready, approaching, not ready, not harvestable or insufficient evidence from an observed maturity indicator, a safety-interval gate, and a harvest order for up to five plants; reads the harvest readiness and treatment records |
| `garden-review` | History records, cultivar performance, lessons and a next-cycle block for a garden or a season; calls no tool |

**Review lenses** — read this checkout, never a garden. One per run; they are meant to disagree:

| Skill | Reviews as |
|-------|------------|
| `agronomy-review` | A plant scientist, for biological correctness |
| `indoor-grower-review` | A tent operator, for daily practicality |
| `casual-owner-review` | Someone with three houseplants and no patience |
| `outdoor-gardener-review` | An allotment gardener, across seasons and 120 plants |

## Agents

`.claude/agents/` holds measurement probes only, never working artefacts. A project agent is dispatchable from that directory and nowhere else — not from `.agents/agents/`, which Goose's own documentation recommends, and not from a plugin. See the [recipe project pattern spec](https://github.com/nolte/kamerplanter-goose/blob/main/spec/goose/recipe-project-pattern/en.md).
