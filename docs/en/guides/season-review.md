---
title: Season review
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Season review

`season-review` closes the cycle that [`garden-plan`](garden-plan.md) opens. It looks back over one season of a garden, **archived plants included, so the failures are not hidden**, and ends in a next-cycle block whose lines are the parameters of the next season's plan. It gives the same blocks as [`garden-review`](garden-review.md) — history records, cultivar performance, lessons and the domain status — over a season you name.

The run **only reads**. It writes the review nowhere — no file, no diary entry — has no apply recipe and calls no Home Assistant tool.

!!! note "Not yet run against a live instance"
    The recipe and the skill were written while the Kamerplanter MCP server was unreachable. Listing archived plants uses `include_archived`, which other recipes here use but the [server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md) does not record. Treat the first real run as the measurement.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `garden-context`, `plant-context-collect`, `diary-measurements-read`, `growth-stage-assessment`, `decision-policy` and `garden-review` from `.claude/skills/`. Started elsewhere, the skills are lost silently.
- **Run it once without `plants` first.** It then lists the season's plants, archived ones marked, so you can pick up to five to review.

## Run it

```sh
goose run --recipe season-review \
  --params season=2026 \
  --params tenant=my-garden \
  --params plants=42,43,51 \
  --params yields="42:1.2 kg,43:14 fruit" \
  --params notes="51: bolted in the June heat; a wet, cool spring"
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `season` | yes | — a year (`2026`) or a span (`2026-03-01..2026-10-31`); anything else stops the run |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `plants` | no | no plant is reviewed; the season's plants are listed so you can name them |
| `yields` | no | every yield is absent; the record has no yield field |
| `notes` | no | nothing from you about plants or the season |
| `weather` | no | the season's weather is absent; it is context only either way |
| `as_of` | no | the growth stage is judged against the newest diary entry read |

Each plant's diary is read for at most eight entries; the history record says whether that covers the season or where it stops.

## Hand the result to the next plan

The `NEXT CYCLE` block is shown verbatim. Its `crops`, `goals`, `constraints` and `harvest_window` lines have the formats `garden-plan` and `crop-selection` take, so the next season starts from them:

```text
NEXT CYCLE
  crops:            solanum_lycopersicum:san_marzano, allium_porrum
    solanum_lycopersicum:san_marzano: reconsider — notes (caller): blossom end rot in July
    allium_porrum: keep — yield 1.2 kg (caller, level 3)
  goals:            fewer losses to blossom end rot
  constraints:      wet June; slugs
  harvest_window:   August to October
  location history (location, not bed):
    bed-north:2026:solanum_lycopersicum:san_marzano
```

```sh
goose run --recipe garden-plan \
  --params tenant=my-garden \
  --params crops="solanum_lycopersicum:san_marzano,allium_porrum" \
  --params goals="fewer losses to blossom end rot" \
  --params constraints="wet June; slugs" \
  --params harvest_window="August to October"
```

A crop marked `reconsider` stays in the list: whether to drop it is your decision, and [`crop-selection`](crop-selection.md) checks the alternatives. The location history lines name locations, not beds: the record has no bed source.

## Read the outcome

| Closing line | Means |
|--------------|-------|
| `SEASON REVIEW: <season> — <n> reviewed, <m> not reviewed — <slug>` | `<n>` plants have a history record; `<m>` were named beyond the limit or could not be read |
| `SEASON REVIEW: not reviewed (invalid season) — <season>` | the season is neither a year nor a valid span |

## Sources

- [`recipes/season-review.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/season-review.yaml) — the parameters, the archived-plant listing and the report format
- [`.claude/skills/garden-review/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/garden-review/SKILL.md) — the history record, the lessons and the next-cycle block
- [`spec/process/garden-and-season-review/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/garden-and-season-review/en.md) — the process this recipe implements
