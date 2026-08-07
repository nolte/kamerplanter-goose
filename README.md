# kamerplanter-goose

[![ci](https://github.com/nolte/kamerplanter-goose/actions/workflows/ci.yml/badge.svg)](https://github.com/nolte/kamerplanter-goose/actions/workflows/ci.yml)
[![Goose](https://img.shields.io/badge/Goose-1.45%2B-black.svg)](https://github.com/block/goose)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
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

# keep the credentials out of your shell history — for example via pass
export KAMERPLANTER_API_KEY=$(pass path/to/kamerplanter/token-mcp)
export HA_MCP_TOKEN=$(pass path/to/homeassistant/token-mcp)

# the shared MCP extension definitions every recipe here relies on
export GOOSE_ADDITIONAL_CONFIG_FILES="$PWD/extensions.yaml"
```

With [direnv](https://direnv.net/), put those lines in a `.envrc` and they load per directory.


### Use the recipes

Clone the repository. The recipes here declare no MCP servers of their own — those live in `extensions.yaml`, so a checkout is what makes them runnable:

```sh
git clone https://github.com/nolte/kamerplanter-goose.git
cd kamerplanter-goose

export GOOSE_RECIPE_PATH="$PWD/recipes"
export GOOSE_ADDITIONAL_CONFIG_FILES="$PWD/extensions.yaml"

goose recipe list -v
goose run --recipe connectivity-check --params tenant=my-garden
```

Start with `connectivity-check`. It is the walking skeleton of this repository: a read-only probe that calls both MCP servers and prints a PASS/FAIL table per step, so a broken URL, a revoked key, or a disabled MCP server is named before any real recipe runs.

`GOOSE_RECIPE_PATH` takes several directories separated by `:`, so a private recipe folder can sit next to this one.

### Consume the recipes from GitHub

Goose can also pull recipes straight from this repository by name:

```sh
export GOOSE_RECIPE_GITHUB_REPO="nolte/kamerplanter-goose"
goose run --recipe connectivity-check
```

This fetches the recipe but **not** `extensions.yaml`, and a recipe without extensions has no MCP servers to talk to. Point `GOOSE_ADDITIONAL_CONFIG_FILES` at a copy of that file — from a checkout, or your own equivalent — or the run starts with no tools.

### Inspect before you run

Every recipe declares its parameters. Read them, and the extensions it will connect to, without spending a model call:

```sh
goose run --recipe connectivity-check --explain
```

### Write a recipe

A recipe is a single YAML file under `recipes/`. The house pattern declares **no** `extensions:` block — the MCP servers come from `extensions.yaml` — an explicit read-only instruction, and one parameter per garden:

```yaml
version: "1.0.0"
title: "Daily Plant Check"
description: "Reconcile due care tasks with live sensor readings"

parameters:
  - key: tenant
    input_type: string
    requirement: required
    description: "Kamerplanter garden slug the run applies to"

instructions: |
  Read-only run. Never actuate a device and never write to Kamerplanter.

prompt: |
  For garden {{ tenant }}, list the care tasks due today, cross-check each one
  against the matching Home Assistant sensor, and report which are truly needed.
```

To add a server, edit `extensions.yaml` rather than the recipe. Note the shape differs: there `extensions` is a map keyed by name with `enabled: true` per entry, while inside a recipe it would be a list.

Validate it before committing:

```sh
goose recipe validate recipes/connectivity-check.yaml
```

#### Notes

- **A recipe's own `extensions:` block replaces the shared ones, it does not extend them.** Declare one entry in a recipe and `extensions.yaml` is ignored entirely for that run — including the servers you did not redeclare. Goose applies the shared set only to recipes that declare none. Measured against Goose 1.45.0.
- **`${VAR}` without `env_keys` is silently not expanded.** Goose substitutes an environment variable in an extension entry only when the variable is listed in that entry's `env_keys`. Omit it and the literal string `${KAMERPLANTER_API_KEY}` goes over the wire as the header value — the recipe validates, starts, and fails with a `401` that looks like a bad key. Verified against Goose 1.45.0 by capturing what it actually sent.
- **`prompt` is not optional in practice.** A recipe with only `instructions` loads fine but fails a headless run with `no text provided for prompt`. Constraints that must hold belong in `prompt`, not only in `instructions`.
- **Recipe discovery is flat.** Goose lists `*.yaml` directly under each configured directory; nested folders are not walked. Keep `recipes/` flat and encode grouping in the filename.
- **The Kamerplanter API key carries your full permissions.** It grants exactly the gardens its account is an active member of. Issue a separate key for Goose so it can be revoked on its own.
- **A recipe that writes says so.** Recipes that confirm care tasks or actuate devices are named with a `-apply` suffix and state the effect in their `description`.

## Structure

```
recipes/                       one Goose recipe per file, flat — the shipped artifact
  connectivity-check.yaml      read-only probe for both MCP servers
  nutrient-imbalance-check.yaml  read-only nutrient diagnosis for one plant
  pest-pressure-check.yaml     read-only: is a pest suspicion biologically tenable
  species-baseline-check.yaml  read-only: is the species record plausible, what is its cycle
  domain-review.yaml           read-only: reviews a recipe or spec as one grower persona
  diary-photo-analysis-apply.yaml  WRITES: analyses one queued diary entry
  diary-analysis-queue-apply.yaml  WRITES: works through the queue, entry by entry
extensions.yaml                the MCP servers, declared once for every recipe
.claude/skills/                project-local skills the recipes load by name
.claude/agents/                measurement probes only — see spec/goose/
scripts/analyse-queue.sh       the queue loop as one Goose process per entry
tests/validate_recipes.py      the house pattern as an executable check
spec/goose/                    how a recipe project is built
spec/mcp/                      what each MCP backend offers, EN canonical + DE
spec/process/                  what a recipe does with them
docs/                          the MkDocs site, one tree per language
AUDIENCES.md                   who this repository is for, per audience
.envrc                         direnv: endpoints, pass-backed credentials, config path
```

## Related repositories

- [nolte/kamerplanter](https://github.com/nolte/kamerplanter) — the plant lifecycle management system; its MCP server is the primary data source for these recipes
- [nolte/kamerplanter-ha](https://github.com/nolte/kamerplanter-ha) — Home Assistant custom integration for Kamerplanter; the entity-level counterpart to the agent-level automation here
- [nolte/home-assistant-config](https://github.com/nolte/home-assistant-config) — the Home Assistant instance these recipes are developed against

## Status

Early stage. Nine recipes ship: three diagnostics (`connectivity-check`, `provider-surface-check`, `provider-plugin-check`), four read-only plant-care recipes (`nutrient-imbalance-check`, `pest-pressure-check`, `species-baseline-check`, `domain-review`), and two that write (`diary-photo-analysis-apply`, `diary-analysis-queue-apply`). Everything but the diagnostics loads project-local skills from `.claude/skills/`, so they must run with this checkout as the working directory — skill discovery is relative to the Goose process's cwd, and a recipe started elsewhere loses the skill without an error.

No release exists yet, and recipe names and parameters will change without notice until the first tagged release. CI validates every recipe against the house pattern (`tests/validate_recipes.py`) and builds the documentation on each pull request. Recipe syntax, the `env_keys` behaviour above, and the skill-loading path are verified against Goose 1.45.0 with the `claude-code` provider.

## License

[MIT](LICENSE). Copyright © 2026 nolte.
