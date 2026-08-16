---
title: Connectivity check
audience: [self-hoster, plant-owner]
content_mode: how-to
track: developer-docs
last_updated: 2026-08-16
---

# Connectivity check

Before any answer about a plant is worth believing, both MCP servers have to be reachable, authenticated, and actually answering tool calls. `connectivity-check` establishes that in four read-only steps and prints one line per step, so a mistyped address or an expired key is named as exactly that — instead of surfacing later as a recipe that seems to think your plants are fine.

Run it first against any new environment, and again after you change a URL, rotate a key, or upgrade either server.

This run **only reads**. It calls no tool that changes state, and it never prints a key or a token, not even partially.

## Before you start

- **The environment must carry the endpoints and credentials**: `KAMERPLANTER_URL`, `KAMERPLANTER_API_KEY`, `HA_URL`, `HA_MCP_TOKEN`, and `GOOSE_ADDITIONAL_CONFIG_FILES` pointing at an `extensions.yaml`. Write your own `.envrc` for this — the one checked in here holds the maintainer's addresses and password-manager paths, and on your machine those lookups fail silently.
- **This recipe loads no project skill**, so it runs from any working directory — including over `GOOSE_RECIPE_GITHUB_REPO` without a clone. It still needs `extensions.yaml`: a recipe with no servers attached has nothing to probe.

## Run it

```sh
goose run --recipe connectivity-check --params tenant=my-garden
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `tenant` | no | the check discovers the garden slug from `list_tenants` and probes the first one |

## What it probes

| # | Step | Server | Call |
|---|------|--------|------|
| 1 | Reachability | Kamerplanter | `list_tenants` — records the garden slugs and roles the key carries |
| 2 | Payload | Kamerplanter | `get_due_care_tasks` for the resolved garden, counted per urgency group |
| 3 | Reachability | Home Assistant | lists the tools your instance exposes, by name |
| 4 | Payload | Home Assistant | one read-only tool — `GetLiveContext`, else `GetDateTime` or `todo_get_items` |

Home Assistant's tool catalog is assembled per instance, so step 3 reports what your instance actually offers rather than checking against a fixed list. Step 4 then picks only from those three classified read-only tools; a tool that merely looks harmless is not called. Two are forbidden by name for exactly that reason: `TimeTillErnte` and `time_till` do not say in their description whether they act, so a read-only run leaves them alone.

A failing step does not end the run. Each one is recorded and the next still runs, so a single report tells you whether one server is down or both.

## Read the outcome

The run prints one row per step with a Result of exactly `PASS`, `FAIL`, or `SKIP`, and a Detail line carrying either the observed answer or the verbatim error. It closes with a single verdict line.

| Closing line | Means |
|--------------|-------|
| `VERDICT: PASS` | all four steps passed |
| `VERDICT: FAIL` | at least one step did not, followed by one sentence naming the server at fault and the most likely cause |

`SKIP` is not a pass. It means a step had nothing to work with: no garden came back from step 1, or step 3 exposed none of the three read-only tools.

## What a failure is telling you

| Observation | Cause |
|-------------|-------|
| `404` from Kamerplanter | its MCP server is not switched on — `MCP_SERVER_ENABLED=true` |
| `401` from Kamerplanter | the API key is invalid or revoked |
| `401` from Home Assistant | the long-lived access token is wrong |
| a server absent from the run entirely | the variable under that extension's `env_keys` is unset, and Goose drops the extension without a warning |
| `401` although the credential is correct | the variable is not listed under that extension's `env_keys`, so the literal `${KAMERPLANTER_API_KEY}` went over the wire and the server rejected it as a wrong key |

The last two are the expensive ones, because neither reads like a configuration problem. Both are properties of `extensions.yaml`, not of your server.

## Sources

- [`recipes/connectivity-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/connectivity-check.yaml) — the four steps, the forbidden tools, and the report format
- [`extensions.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/extensions.yaml) — the endpoints and `env_keys` every recipe here shares
- [`spec/goose/recipe-project-pattern/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/goose/recipe-project-pattern/en.md) — why an unset `env_keys` variable removes an extension silently
