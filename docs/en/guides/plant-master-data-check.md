---
title: Plant master data check
audience: [plant-owner, self-hoster]
content_mode: how-to
track: user-docs
last_updated: 2026-08-16
---

# Plant master data check

Every later analysis reads the same four fields, and a plant missing one of them cannot be judged at all. `plant-master-data-check` sweeps every living plant in a garden and reports which ones are incomplete — and, for each gap, what it prevents.

It audits record-keeping, not plants. Nothing it reports is a statement about a plant's health.

This run **only reads**, and it loads no project skill, so it runs from any working directory — including over `GOOSE_RECIPE_GITHUB_REPO` without a clone.

## Run it

```sh
goose run --recipe plant-master-data-check --params tenant=my-garden
```

| Parameter | Required | Default | Effect |
|-----------|:--------:|---------|--------|
| `tenant` | no | discovered from `list_tenants` | required only when your key covers several gardens |
| `include_archived` | no | `false` | `true` also inspects removed plants, whose records drive no decision |

If your key covers several gardens and you name none, the run stops without inspecting anything and says so: `NOT INSPECTED: several gardens available, none given`. Name the garden rather than letting the key pick one — a key with several memberships otherwise answers for the wrong garden while the report still carries the one you meant.

## The four fields it checks

| Field | Missing means |
|-------|---------------|
| `species_key` | Nothing can be judged. No baseline, no phase plan, no pest plausibility. |
| `location_key` | No sensor, climate, or site context can be attached to this plant. |
| `current_phase_key` | No watering interval, no stress tolerance, no "is it overdue" — every phase-dependent judgement is unavailable. |
| `planted_on` | Age is unknown, so nothing can be called early or late. |

Nothing else counts as a gap — not `plant_name`, `cultivar_key`, `site_key`, `substrate_key`, or `slot_key`. This repository has not established that those are required, and counting them would bury the four that are. Anything striking among them lands in the closing note instead.

## Read the outcome

The report lists one row per incomplete plant, ordered by how many fields are missing, with archived rows last. When nothing is missing it prints `No gaps.` instead of the table, followed by a closing note of at most three sentences and two counting lines.

| Column | What it carries |
|--------|-----------------|
| Plant | `instance_id` — the readable identifier, e.g. `DRACA-0616-OWL` |
| Key | `plant_key` — e.g. `11441519`, the value every follow-up recipe takes |
| Missing | the missing fields by name, or `archived` |
| Prevents | the shortest true statement of what is thereby unavailable |

| Closing line | Means |
|--------------|-------|
| `INSPECTED: <n> of <m>` | plants checked against the number the filter selected; on a complete sweep the two halves are equal |
| `INCOMPLETE: <n>` | living plants missing at least one of the four fields; archived plants are never counted here |

Both identifiers are in the table on purpose. `instance_id` is what you recognise; `plant_key` is what [nutrient-imbalance-check](nutrient-imbalance-check.md), [pest-pressure-check](pest-pressure-check.md), and every plant tool actually accept. Neither accepts the readable one.

## Cost

One `list_plants` response already carries every field this recipe checks, so a garden of 120 plants costs three paginated calls rather than 120 — the recipe explicitly forbids a per-plant `get_plant`.

## Sources

- [`recipes/plant-master-data-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/plant-master-data-check.yaml) — the four fields, the paging rule, and the report format
- [`spec/mcp/kamerplanter-mcp-server/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md) — what `list_plants` returns and which counters mean what
