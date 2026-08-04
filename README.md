# kamerplanter-goose

[![Goose](https://img.shields.io/badge/Goose-1.45%2B-black.svg)](https://github.com/block/goose)
[![Status](https://img.shields.io/badge/status-early%20stage-orange.svg)](#status)

Shareable [Goose](https://github.com/block/goose) recipes for anyone running [Kamerplanter](https://github.com/nolte/kamerplanter) and [Home Assistant](https://www.home-assistant.io/). Each one wires those [Model Context Protocol](https://modelcontextprotocol.io/) servers into a repeatable plant-care run you invoke by name.

## Purpose

Plant care data lives in more than one system. Kamerplanter knows the plants, growth phases, nutrient plans, and due care tasks. Home Assistant knows the soil moisture, temperature, and the pump on the balcony. Both speak MCP, but connecting them into a useful agent means writing the same prompt, the same extension block, and the same guardrails over and over.

This repository publishes that glue once, as versioned Goose recipes:

- **For plant owners who already run Goose:** a catalog of ready recipes — "what needs watering today", "reconcile the nutrient plan with tank readings" — invoked by name, parameterized by garden.
- **For self-hosters running Kamerplanter and Home Assistant:** one documented set of environment variables that every recipe here consumes, so a recipe added next month needs no new wiring.
- **For recipe authors:** a shared shape for plant-care agents — naming, parameters, extension configuration, and read-only versus write boundaries — instead of per-recipe improvisation.

The recipes stay portable: they declare the MCP servers they need and nothing about where those servers run.

## Usage

### Prerequisites

- Goose 1.45.0 or later, with a configured provider
- A Kamerplanter backend with `MCP_SERVER_ENABLED=true` and an API key (`kp_...`)
- A Home Assistant instance with the [MCP Server integration](https://www.home-assistant.io/integrations/mcp_server/) and a long-lived access token

Recipes read their endpoints and credentials from the environment, so no secret is ever written into a recipe file:

```sh
export KAMERPLANTER_URL="http://localhost:3000"
export HA_URL="https://ha.example.com"

# keep the two credentials out of your shell history — for example via pass
export KAMERPLANTER_API_KEY=$(pass network/kamerplanter/api/token-mcp)
export HA_MCP_TOKEN=$(pass network/homeassistant/api/token-mcp)
```

With [direnv](https://direnv.net/), put those four lines in a `.envrc` and they load per directory.


### Use the recipes

Point Goose at this repository as a recipe source, then invoke recipes by name:

```sh
export GOOSE_RECIPE_GITHUB_REPO="nolte/kamerplanter-goose"

goose recipe list -v
goose run --recipe connectivity-check
```

Prefer a local checkout — for offline use, or to run a modified copy:

```sh
git clone https://github.com/nolte/kamerplanter-goose.git
export GOOSE_RECIPE_PATH="$PWD/kamerplanter-goose/recipes"

goose run --recipe connectivity-check --params tenant=my-garden
```

Start with `connectivity-check`. It is the walking skeleton of this repository: a read-only probe that calls both MCP servers and prints a PASS/FAIL table per step, so a broken URL, a revoked key, or a disabled MCP server is named before any real recipe runs.

`GOOSE_RECIPE_PATH` takes several directories separated by `:`, so a private recipe folder can sit next to this one.

### Inspect before you run

Every recipe declares its parameters. Read them, and the extensions it will connect to, without spending a model call:

```sh
goose run --recipe connectivity-check --explain
```

### Write a recipe

A recipe is a single YAML file under `recipes/`. The shape below is the house pattern — environment-substituted endpoints, an explicit read-only instruction, and one parameter per garden:

```yaml
version: "1.0.0"
title: "Daily Plant Check"
description: "Reconcile due care tasks with live sensor readings"

parameters:
  - key: tenant
    input_type: string
    requirement: required
    description: "Kamerplanter garden slug the run applies to"

extensions:
  - type: streamable_http
    name: kamerplanter
    uri: "${KAMERPLANTER_URL}/api/v1/mcp"
    env_keys: ["KAMERPLANTER_URL", "KAMERPLANTER_API_KEY"]
    headers:
      X-API-Key: "${KAMERPLANTER_API_KEY}"
    timeout: 300
  - type: streamable_http
    name: home_assistant
    uri: "${HA_URL}/api/mcp"
    env_keys: ["HA_URL", "HA_MCP_TOKEN"]
    headers:
      Authorization: "Bearer ${HA_MCP_TOKEN}"
    timeout: 300

instructions: |
  Read-only run. Never actuate a device and never write to Kamerplanter.

prompt: |
  For garden {{ tenant }}, list the care tasks due today, cross-check each one
  against the matching Home Assistant sensor, and report which are truly needed.
```

Validate it before committing:

```sh
goose recipe validate recipes/connectivity-check.yaml
```

#### Notes

- **`${VAR}` without `env_keys` is silently not expanded.** Goose substitutes an environment variable in an extension block only when the variable is listed in that extension's `env_keys`. Omit it and the literal string `${KAMERPLANTER_API_KEY}` goes over the wire as the header value — the recipe validates, starts, and fails with a `401` that looks like a bad key. Verified against Goose 1.45.0 by capturing what it actually sent.
- **`prompt` is not optional in practice.** A recipe with only `instructions` loads fine but fails a headless run with `no text provided for prompt`. Constraints that must hold belong in `prompt`, not only in `instructions`.
- **Recipe discovery is flat.** Goose lists `*.yaml` directly under each configured directory; nested folders are not walked. Keep `recipes/` flat and encode grouping in the filename.
- **The Kamerplanter API key carries your full permissions.** It grants exactly the gardens its account is an active member of. Issue a separate key for Goose so it can be revoked on its own.
- **A recipe that writes says so.** Recipes that confirm care tasks or actuate devices are named with a `-apply` suffix and state the effect in their `description`.

## Structure

```
recipes/                       one Goose recipe per file, flat — the shipped artifact
  connectivity-check.yaml      read-only probe for both MCP servers
.envrc                         direnv: endpoints plus pass-backed credentials for local runs
```

## Related repositories

- [nolte/kamerplanter](https://github.com/nolte/kamerplanter) — the plant lifecycle management system; its MCP server is the primary data source for these recipes
- [nolte/kamerplanter-ha](https://github.com/nolte/kamerplanter-ha) — Home Assistant custom integration for Kamerplanter; the entity-level counterpart to the agent-level automation here
- [nolte/home-assistant-config](https://github.com/nolte/home-assistant-config) — the Home Assistant instance these recipes are developed against

## Status

Early stage. One recipe ships — `connectivity-check`, the walking skeleton — and it is the only one; the catalog described under Purpose is still ahead. No CI workflow and no release exist yet, and recipe names and parameters will change without notice until the first tagged release. Recipe syntax and the `env_keys` behaviour above are verified against Goose 1.45.0.

## License

Not yet licensed. A `LICENSE` file lands with the first release; until then, no usage rights are granted.
