---
title: Planting calendar
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-10-14
---

# Planting calendar

When a crop can go in depends on this garden's frost dates and on what the species record says about its sowing and harvest months. `planting-calendar` computes, for each crop you name and each of its growing periods, the windows in which it can be sown, sown indoors, transplanted and harvested, and says for every window which rule and which field gave it. It proposes no planting; for that, see the [garden plan](garden-plan.md).

A window that no recorded field supports is **unknown**, with the missing input. The run never fills it with a typical date.

This run **only reads**. It changes no record.

!!! note "Not yet run against a live instance"
    The recipe and its four skills were written while the Kamerplanter MCP server was unreachable. Tool names and species fields come from the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md) and the [species baseline spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/en.md), measured on 2026-08-07 on two species. Treat the first real run as the measurement.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `garden-context`, `site-analysis`, `planting-calendar` and `decision-policy` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.

## Run it

```sh
goose run --recipe planting-calendar \
  --params tenant=my-garden \
  --params crops="allium-porrum" \
  --params harvest_window="summer"
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `crops` | yes | — |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `harvest_window` | no | the harvest preference is reported unknown; it never drops a crop |

`crops` is a comma-separated list; each entry is a species key, or a species key and a cultivar key joined by a colon (`species_key:cultivar_key`).

## What it computes

| Window | Fed by | What it does not cover |
|--------|--------|------------------------|
| Sowing (direct) | the sowing months of the growing period; the garden's frost dates for a frost-sensitive crop | what `frost_sensitivity` values mean, and the frost-date format, are not recorded: the frost bound is applied only where both read unambiguously |
| Indoor sowing | the weeks before the last frost the species records, and the last frost date | the frost-date format |
| Transplanting | the last frost date, for a frost-sensitive crop | how long a seedling needs: no field says, so only the start is given |
| Harvest | the harvest months of the growing period | the months on the species record as a whole are the union across periods, so a period is chosen first |
| Maturity | the cultivar's days to maturity | what it counts from, sowing or transplanting, is not recorded: it is shown as a value and no harvest date is computed from it |

A species with several growing periods has several sets of windows, each named by the months it carries. Cultivar values are used before species values, and the report says which.

## Read the outcome

The report is a table with one row per crop and period (sowing, indoor sowing, transplanting, harvest, harvest preference, confidence), followed by the rule, fields, source, retrieval time and evidence level behind each known window, the crops that were not computed, and any tool error reported verbatim.

| Closing line | Means |
|--------------|-------|
| `CALENDAR: <k> windows known, <u> unknown — <slug>` | how many windows the record could support |
| `UNKNOWN WINDOWS: <windows>` | each unknown window with the input that would settle it |

A crop with no window is not a failed run. It is a statement about what the species record and the sowing calendar hold.

## Sources

- [`recipes/planting-calendar.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/planting-calendar.yaml) — the parameters and the report format
- [`.claude/skills/planting-calendar/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/planting-calendar/SKILL.md) — the windows, the rules and what each field does not cover
- [`.claude/skills/site-analysis/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/site-analysis/SKILL.md) — the frost dates and the site profile
- [`spec/process/plant-planning-and-planting-calendar/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/plant-planning-and-planting-calendar/en.md) — the process this recipe implements
