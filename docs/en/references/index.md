---
title: References
audience: [recipe-author, self-hoster, maintainer]
content_mode: meta
track: developer-docs
last_updated: 2026-08-16
---

# References

Reference material: the shipped recipes with their parameters, the shared MCP extension definitions, the project skills, and the environment variables every run consumes.

## Recipes

A recipe that loads project skills must be started with this repository checkout as the working directory, because skill discovery is relative to the Goose process's working directory. The three diagnostics and `plant-master-data-check` load none, so they run from anywhere — which is what lets them be used over `GOOSE_RECIPE_GITHUB_REPO`.

Each recipe has a guide of its own, linked from its name.

| Recipe | Writes | Purpose |
|--------|:------:|---------|
| [`connectivity-check`](../guides/connectivity-check.md) | no | Probes both MCP servers read-only and prints PASS/FAIL per step |
| [`provider-surface-check`](../guides/provider-surface-check.md) | no | Inventories the tools the agent actually holds under the current provider |
| [`provider-plugin-check`](../guides/provider-plugin-check.md) | no | Whether plugin skills, plugin agents, and project agents are reachable from a run |
| [`nutrient-imbalance-check`](../guides/nutrient-imbalance-check.md) | no | Undersupply, oversupply, or unavailability at adequate supply, for one plant |
| [`pest-pressure-check`](../guides/pest-pressure-check.md) | no | Whether a pest or disease suspicion is biologically tenable |
| [`species-baseline-check`](../guides/species-baseline-check.md) | no | Whether a species record is plausible, and what its lifecycle is |
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

**Review lenses** — read this checkout, never a garden. One per run; they are meant to disagree:

| Skill | Reviews as |
|-------|------------|
| `agronomy-review` | A plant scientist, for biological correctness |
| `indoor-grower-review` | A tent operator, for daily practicality |
| `casual-owner-review` | Someone with three houseplants and no patience |
| `outdoor-gardener-review` | An allotment gardener, across seasons and 120 plants |

## Agents

`.claude/agents/` holds measurement probes only, never working artefacts. A project agent is dispatchable from that directory and nowhere else — not from `.agents/agents/`, which Goose's own documentation recommends, and not from a plugin. See the [recipe project pattern spec](https://github.com/nolte/kamerplanter-goose/blob/main/spec/goose/recipe-project-pattern/en.md).
