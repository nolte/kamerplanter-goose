---
title: Weather impact check
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Weather impact check

A frost forecast is a fact about the garden, not about the plant. `weather-impact-check` says what the weather you supply means for up to five plants: per factor, whether the plant is **exposed**, whether the data show **no exposure**, or whether there is **no source** for that factor at all. Each exposure names the threshold it was judged against and whether care, health or harvest timing is likely to be affected. It never reports the weather as a symptom of the plant.

The run **only reads**. It turns nothing on or off, protects or moves no plant, records nothing, and has no apply recipe.

!!! note "Not yet run against a live instance"
    The recipe and the skill were written while the Kamerplanter MCP server was unreachable. Tool names come from the [Kamerplanter server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/en.md), measured on 2026-08-16, and the [Home Assistant server spec](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/home-assistant-mcp-server/en.md), measured on 2026-08-04. Whether your Home Assistant exposes a weather entity has never been measured. Treat the first real run as the measurement.

## Where the weather comes from

- **From you.** The Kamerplanter server has no weather or forecast tool, so the `weather` parameter is the main source. It is taken as written and marked as coming from you.
- **From Home Assistant, if it offers `GetLiveContext`.** The run reads it once, for the `weather` domain only, and labels the reading `home_assistant (unmeasured)`. It reads no other entity and no sensor: nothing in the record maps a sensor to a plant. If you and Home Assistant disagree, both values are shown side by side and nothing is averaged.

## Expect "no source"

With no `weather` and no weather entity in Home Assistant, **every factor is `no source`**, and the report says what it cannot conclude: whether the plants are or will be exposed to frost, heat, rain, wind or a humidity extreme. That is the honest result, not a failure of the run. A factor your weather text does not mention is `no source` too.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `plant-context-collect`, `decision-policy` and `weather-impact-analysis` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. Started elsewhere, the skills are lost silently and the run still produces a plausible answer.
- Run [`connectivity-check`](connectivity-check.md) first against a new environment.

## Run it

```sh
goose run --recipe weather-impact-check \
  --params tenant=my-garden \
  --params plants="42,43" \
  --params weather="clear tonight, down to -2 °C, light wind; mild from Thursday" \
  --params placement="42 outdoors in the bed, 43 on the windowsill"
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `tenant` | no | the run discovers the garden slug from `list_tenants` |
| `plants` | no | no plant is assessed; only the weather factors are rated |
| `weather` | no | weather comes only from Home Assistant, if it offers a weather entity; otherwise every factor is `no source` |
| `placement` | no | every impact is stated as conditional ("if the plant stands outdoors"): the record has no field for where a plant stands |

**At most five plants are assessed**, in the order you give them; every further key is reported as not checked.

## What it reports

| Factor | Exposure when the data name |
|--------|-----------------------------|
| temperature extremes | a minimum or maximum that reaches a threshold, frost, or a heat spell |
| rainfall | rain, heavy rain, hail or a dry spell |
| wind | strong wind, gusts or a storm |
| humidity | a relative humidity beyond a recorded or labelled threshold, fog, prolonged wetness or very dry air; "18 °C, 55 % RH" alone is no exposure |
| heat and cold events | a heatwave, a frost night or a cold snap |
| forecast changes | a change between now and the forecast |

- **A threshold has a source or it is not used.** The species' frost sensitivity or hardiness zones, or the phase's stress tolerance, read as recorded; general knowledge only when labelled as such. Without one, the impact is `not assessed`.
- **Weather is not a symptom.** Symptoms come only from a photo reading, a diary entry or a recorded inspection, and they are listed in a block of their own. A symptom and an exposure are linked at most as "consistent with", which is a suspicion, not a diagnosis.
- **Vapour pressure deficit** is computed only from a temperature and a humidity from the same time and place, with the formula stated, and reported without judgement: no target is recorded for it.
- **A recommendation needs a threshold from the record and a plant you place outdoors or in a sheltered spot.** You cannot set a threshold yourself. Everything else is an observation.

## Read the outcome

| Closing line | Means |
|--------------|-------|
| `WEATHER: <e> exposures, <s> no source — <slug>` | the number of factors rated exposure and no source, over the assessed plants |
| `WEATHER: not assessed — <slug>` | every step failed |

Each plant's block also carries a hand-off for plant health: the exposures, and separately the symptoms, so a later health check can read the two without mixing them.

## Sources

- [`recipes/weather-impact-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/weather-impact-check.yaml) — the parameters, the Home Assistant guard and the report format
- [`.claude/skills/weather-impact-analysis/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/weather-impact-analysis/SKILL.md) — the factor table, the threshold rule and the separation of exposure and symptom
- [`spec/process/growth-stage-and-weather-impact/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/growth-stage-and-weather-impact/en.md) — the process this recipe implements
