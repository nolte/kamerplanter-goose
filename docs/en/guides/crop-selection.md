---
title: Crop selection
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-10-13
---

# Crop selection

Whether a crop suits a site depends on facts about the site, and the facts people reach for first — light, room, water — are the ones the Kamerplanter catalog does not hold. `crop-selection` builds a profile of what is known about your garden's site, judges candidate species and cultivars against it, and returns for each candidate a verdict, the reasons, and the constraints it failed. What it does not know, it says it does not know.

A candidate is never called suitable on a parameter nobody supplied. An unknown site parameter or an absent species field leaves the constraint **undetermined**: not met, and not failed.

This run **only reads**. It plans no planting and changes no record.

!!! note "Not yet run against a live instance"
    The recipe and its four skills were written while the Kamerplanter MCP server was unreachable. Tool names and species fields come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md) and the [species baseline spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/en.md), measured on 2026-08-07 on two species. Treat the first real run as the measurement.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `garden-context`, `site-analysis`, `crop-selection` and `decision-policy` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.

## Run it

```sh
goose run --recipe crop-selection \
  --params tenant=my-garden \
  --params crops="allium-porrum" \
  --params light="south-facing, about six hours of sun" \
  --params hardiness_zone=7b
```

| Parameter | Effect when omitted |
|-----------|---------------------|
| `tenant` | the run discovers the garden slug from `list_tenants`; a key that covers several gardens needs it set |
| `crops` | the sowing calendar cannot be narrowed by a species of yours, so the frost dates come from a plant of the garden, or are unknown; a bounded sample of the species catalog is judged, and the report says it is a sample |
| `goals` | no goal is judged; none is reported met |
| `harvest_window` | timing is reported unknown |
| `light`, `area_or_volume`, `water`, `constraints` | the matching site parameter is reported unknown: the server has no field for them |
| `hardiness_zone` | the hardiness-zone check is undetermined: no tool says which zone a garden is in |

Your own words for light, area and water are taken as written and marked as coming from you. The run does not turn "sunny" into hours or a bed into square metres.

## What the site profile holds

Seven parameters, each `known` or `unknown`.

| Parameter | Where it comes from |
|-----------|---------------------|
| Light and exposure | only you |
| Area and container volume | only you |
| Soil and substrate | the substrates the garden's plants reference; a bed's own substrate is not known |
| Climate and season | the sowing calendar's frost dates, narrowed by a species name; the zone only from you |
| Water availability | only you |
| Environmental constraints | only you, as free text |
| Existing observations and measurements | collected per plant, so not collected at garden level |

## What a candidate is judged on

| Kind | What | If it cannot be judged |
|------|------|------------------------|
| **Hard constraint** | frost sensitivity against the garden's frost dates; hardiness zone against your zone | undetermined |
| **Preference** | timing against your harvest window; days to maturity against the frost-free span; companion fit; your goals | unknown |

A failed hard constraint rejects the candidate and is listed with its values and source. A preference only ranks and never rejects. Where a cultivar carries a value, it is used instead of the species value, and the report says which one it used.

Light, shade tolerance, waterlogging tolerance and soil pH are **not** checked: the species fields for them were absent on both species probed, so no constraint can be formed. Whether other species carry them is not established.

## Read the outcome

The report opens with the site profile table, states whether the candidates came from you or are a sample, then gives one row per candidate with its verdict, failed hard constraints, undetermined constraints and confidence, followed by the reasons and the preferences.

| Verdict | Means |
|---------|-------|
| `eligible` | every hard constraint that could be formed is met, and none is undetermined |
| `rejected` | at least one hard constraint failed |
| `undetermined` | something a hard constraint needs is unknown |

| Closing line | Means |
|--------------|-------|
| `CROP SELECTION: <e> eligible, <r> rejected, <u> undetermined — <slug>` | the verdict counts |
| `UNKNOWN SITE PARAMETERS: <parameters>` | what to supply to turn undetermined into a decision |

A long list of undetermined candidates is not a failed run. It is the honest result when the garden's site facts were not supplied.

## Sources

- [`recipes/crop-selection.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/crop-selection.yaml) — the parameters and the report format
- [`.claude/skills/site-analysis/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/site-analysis/SKILL.md) — the site profile
- [`.claude/skills/crop-selection/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/crop-selection/SKILL.md) — the constraints and the verdict
- [`spec/process/site-analysis-and-crop-selection/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/site-analysis-and-crop-selection/en.md) — the process this recipe implements
