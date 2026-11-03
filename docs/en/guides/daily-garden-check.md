---
title: Daily garden check
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-03
---

# Daily garden check

A garden holds many small questions at once: what is due, what looks wrong, what needs nothing. `daily-garden-check` is the daily look. It reads one Kamerplanter garden, runs the nutrient and pest checks for the plants you name, and puts everything into one list ordered by what deserves attention first. Each item says whether it is an observation or a recommendation, what it rests on, how sure it is, and what would change it. What has no action because the evidence is missing is listed too, with the observation that would supply it.

This run **only reads**. It changes no record, schedules nothing, and has no apply recipe. "Nothing to do" is a legitimate result, and the check does not pad the list to look useful.

!!! note "Not yet run against a live instance"
    The recipe and its skills were written while the Kamerplanter MCP server was unreachable. Tool names come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md), measured on 2026-08-16. Treat the first real run as the measurement.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `garden-context`, `plant-context-collect`, `diary-measurements-read`, `nutrient-imbalance-assess`, `pest-pressure-assess`, `decision-policy` and `care-planning` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.
- Run [`connectivity-check`](connectivity-check.md) first against a new environment.

## Run it

```sh
goose run --recipe daily-garden-check \
  --params tenant=my-garden \
  --params plants="plant-1,plant-2"
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `plants` | no | the garden level only: due tasks and planting runs. The nutrient and pest checks are not run |

`plants` is a comma-separated list of plant instance keys. **At most five are checked**, in the order you give them; every further key is reported as not checked. The limit keeps the number of per-plant calls bounded: the check never reads every plant of a garden.

## What it looks at

| Domain | Status |
|--------|--------|
| nutrient | checked for the plants you name |
| pest | checked for the plants you name |
| watering | **not available** (`watering-decision`, [#44](https://github.com/nolte/kamerplanter-goose/issues/44)) |
| fertilisation | **not available** (`fertilization-decision`, [#45](https://github.com/nolte/kamerplanter-goose/issues/45)) |
| plant health and pest management | **not available** (`plant-health-assessment`, `pest-ipm-planning`, [#48](https://github.com/nolte/kamerplanter-goose/issues/48)) |
| growth stage and weather | **not available** (`growth-stage-assessment`, `weather-impact-analysis`, [#49](https://github.com/nolte/kamerplanter-goose/issues/49)) |

A domain that is not available is named in the report and never replaced by another. When one of those skills exists, it plugs in here without a change to the care plan's rules.

## What the list means

- **An observation** is what a tool or a document said, with its source and time. **A recommendation** is a proposal to you, with evidence, confidence, uncertainty and missing data. A **mutation** is only ever named: the check says which state-changing tool a later apply step would call, and calls nothing.
- **Order.** Items are ordered by urgency (`now`, `soon`, `routine`, `watch`), then by confidence, then by plant and domain. Urgency comes only from what a domain itself said about the consequence of doing nothing. A due care task is `routine` at most.
- **A due task is not a reason to act.** It is a request from the schedule, not a measurement of the plant, and the check never recommends watering or feeding because a reminder is due.
- **A suspicion is an observation.** When the nutrient or pest check leaves a direction or a candidate undetermined, that is what you get, not a recommendation.
- **No evidence, no action.** A state the record says nothing about appears under *no action, evidence insufficient*, with the observation that would settle it.

## Read the outcome

The report is the care plan in five blocks: the header, the items, the named mutations, the entries with no action, and the status of every domain. Then, per plant, one line saying how many diary entries were listed, opened and found without measurements; that line is what tells you the diary was read at all.

| Closing line | Means |
|--------------|-------|
| `APPLY: none — this check reports and applies nothing` | nothing here can be applied |
| `CARE: <a> actions, <n> no action — <slug>` (always the last line) | how many recommendations were made and how many entries have no action |

A report with no actions and a long list of entries without action is the honest result when the garden's inputs are thin.

## How far "deterministic" goes

The care plan facts are a function of the blocks the skills were given: the item identifiers, kinds, urgencies, the order, the confidence levels, the named mutations and the entries with no action. Two runs over the same blocks give the same facts; the wording around them can differ. This is specified, not yet checked on a fixed fixture.

## Sources

- [`recipes/daily-garden-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/daily-garden-check.yaml) — the parameters and the report format
- [`.claude/skills/care-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/care-planning/SKILL.md) — the items, the urgency rules and the order
- [`.claude/skills/diary-measurements-read/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/diary-measurements-read/SKILL.md) — the diary read behind the nutrient check
- [`spec/process/care-planning-and-daily-check/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/care-planning-and-daily-check/en.md) — the process this recipe implements
