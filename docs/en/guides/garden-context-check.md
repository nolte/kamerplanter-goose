---
title: Garden context check
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-10-13
---

# Garden context check

Before anything advises on a garden, it should know what the garden holds and what it does not. `garden-context-check` collects the context of one Kamerplanter garden and reports it field by field: what was read and from which tool, and what is **absent**, with the reason. It recommends nothing.

The point is the absent column. A field the server has no source for comes back absent rather than filled with a typical value, so a later step cannot mistake a guess for a record.

This run **only reads**. It changes no record.

!!! note "Not yet run against a live instance"
    The recipe and its skill were written while the Kamerplanter MCP server was unreachable. Tool names and response fields come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md) and an earlier measurement, not from a run of this recipe. Treat the first real run as the measurement.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skill `garden-context` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skill is lost silently and the run still produces a plausible answer.

## Run it

```sh
goose run --recipe garden-context-check \
  --params tenant=my-garden
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `tenant` | no | the run discovers the garden slug from `list_tenants`; a key that covers several gardens needs it set |
| `goals` | no | the "user goals and constraints" field is reported absent: the server has no source for it, so it appears only when you supply it |

## What it collects

Eleven fields, each reported `present` or `absent`.

| Field | Where it comes from |
|-------|---------------------|
| Site and location | the site and location keys on each plant; the site's own attributes have no read tool in the measured catalog |
| Crops and cultivars | the plants' species, then the species record once per distinct species, and the cultivar where a plant has one |
| Planting runs | the planting-runs list |
| Growth stage | the phase key on each plant |
| Soil and substrate | the substrate each plant references, matched against the substrate list |
| Watering and fertilisation state | the care tasks that are due, and only those: an empty list is not evidence of recent care, because the care log is read per plant |
| Beds and containers | **no source measured** |
| Weather | **no source measured** |
| Current measurements | `not collected`: per-plant evidence, read for the plants you name, not at garden level |
| Historical observations | `not collected`: the same, from inspections, diary and care log |
| User goals and constraints | only from you |

A due care task is carried as a request from the schedule, not as a measurement of the plant. The run counts plants by `matched`, not by `total_in_tenant`, which includes archived plants.

## Read the outcome

The report is a table of the eleven fields with their status, retrieval time, and source or reason, followed by the plant count, the species list, whether the garden slug was given or discovered, and any tool error reported verbatim.

| Closing line | Means |
|--------------|-------|
| `GARDEN CONTEXT: <n> of 11 present — <tenant>` | how much of the context the server could supply |
| `ABSENT: <fields>` | the fields to narrow any later analysis around, each marked `no source` (the measured catalog offers none) or `not collected` (a source exists but is read per plant) |

A low count is not a failure of the run. It is a statement about what the garden and the server hold, and the later step should narrow its question to match.

## Sources

- [`recipes/garden-context-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/garden-context-check.yaml) — the parameters and the report format
- [`.claude/skills/garden-context/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/garden-context/SKILL.md) — the collection steps and what is absent by construction
- [`spec/process/garden-decision-policy/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/garden-decision-policy/en.md) — the context contract, §D
