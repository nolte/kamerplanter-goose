# kamerplanter-goose

[![ci](https://github.com/nolte/kamerplanter-goose/actions/workflows/ci.yml/badge.svg)](https://github.com/nolte/kamerplanter-goose/actions/workflows/ci.yml)
[![Goose](https://img.shields.io/badge/Goose-1.45%2B-black.svg)](https://github.com/block/goose)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-early%20stage-orange.svg)](#status)

Ask questions about your plants and get answers grounded in what you actually recorded about them — not in generic advice from the internet. Ready-made [Goose](https://github.com/block/goose) recipes you run by name.

## Purpose

What a plant needs is written down in two places.

[Kamerplanter](https://github.com/nolte/kamerplanter) knows the plants: which species, how old, when it was last fed, what the plan for its current growth phase says. [Home Assistant](https://www.home-assistant.io/) knows what the sensors see: soil moisture, temperature, the pump on the balcony.

Answering something as ordinary as *does this one need water today* means reading both, and knowing what normal looks like for that particular plant at that particular stage. Do it by hand and you are the one holding it all together. Do it with an AI assistant and you write the same setup and the same warnings over and over.

This repository writes that down once, so a run is a name and a garden rather than a prompt you compose again each time.

What you get depends on who you are:

- **You keep plants and already use Goose.** A catalog of ready recipes. Ask what is wrong with a plant, whether it is over- or underfed, or whether a pest suspicion holds up — one command each.
- **You host Kamerplanter and Home Assistant yourself.** One documented set of settings that every recipe here uses. A recipe added next month needs no new wiring from you.
- **You want to write your own recipes.** A worked-out shape to copy: how to name things, how to pass in a garden, and where the boundary between reading and writing runs.

Where your systems live is written down once, in `extensions.yaml`, and never inside a recipe — so the same recipe works against your setup as readily as against anyone else's.

## Usage

### What you need

- [Goose](https://github.com/block/goose) 1.45 or later, with an AI provider configured
- A Kamerplanter garden with its MCP server switched on (`MCP_SERVER_ENABLED=true`) and an API key
- A Home Assistant instance with the [MCP Server integration](https://www.home-assistant.io/integrations/mcp_server/) and a long-lived access token

### Getting started

Clone the repository and tell Goose where your systems live. Your key and token are looked up when the shell starts, never typed in as text — so they stay out of your shell history and out of every file here:

```sh
git clone https://github.com/nolte/kamerplanter-goose.git
cd kamerplanter-goose

# no trailing slash — the addresses get `/api/...` appended, and a double
# slash comes back as a server error rather than as the typo it is
export KAMERPLANTER_URL="https://kamerplanter.example.com"
export HA_URL="https://ha.example.com"

# fetched from a password manager, so the value itself is never written down
export KAMERPLANTER_API_KEY=$(pass path/to/kamerplanter/token-mcp)
export HA_MCP_TOKEN=$(pass path/to/homeassistant/token-mcp)

export GOOSE_RECIPE_PATH="$PWD/recipes"
export GOOSE_ADDITIONAL_CONFIG_FILES="$PWD/extensions.yaml"
```

`extensions.yaml` also lists a third system, GitHub. No recipe here uses it yet; it is kept for work on the knowledge documents this repository draws on. Leave `GITHUB_MCP_PAT` unset and it is quietly skipped, which is the right setting for everyone not doing that work. Set it — as the maintainer's `.envrc` does, from `gh auth token` — and your GitHub token is sent to a Copilot endpoint. Worth knowing before you copy that line.

**Do not run `direnv allow` on the `.envrc` that ships here.** It is checked into git and filled with the maintainer's own addresses and password-manager paths. On your machine those lookups fail, both systems drop out **without any warning**, and the run reports that no systems are configured at all — which looks like a Goose problem and is not one. Put your own lines in, keeping the two `TASK_*` variables the file already sets, or the `task` commands below stop before they start.

Then check that your systems answer:

```sh
goose run --recipe connectivity-check --params tenant=my-garden
```

Run this one first, always. It only reads, and it prints one line per step — so a mistyped address or an expired key is named as exactly that, instead of surfacing later as a recipe that seems to think your plants are fine.

**Run recipes from inside the folder you cloned.** Most of them load their know-how from files in this repository, and Goose looks for those relative to wherever you started it. Start somewhere else and the recipe still answers — just without that knowledge, and without telling you.

### What the recipes can do

Most recipes need more than a garden name — a plant, a species, a discriminator for the run. Ask before you run; it costs nothing:

```sh
goose recipe list -v                       # everything available, with its options
goose run --recipe <name> --explain        # what this one needs, before it costs anything
```

| Recipe | Changes anything? | What it answers |
|---|---|---|
| `connectivity-check` | no | Can I reach both systems, and is my key still good? |
| `nutrient-imbalance-check` | no | Is this plant underfed, overfed, or unable to take up what it already has? |
| `pest-pressure-check` | no | Does this pest or disease suspicion actually hold up? |
| `species-baseline-check` | no | Is what we know about this species plausible in the first place? |
| `domain-review` | writes a report file | How does a recipe read to an experienced grower? |
| `diary-photo-analysis-apply` | **yes** | Looks at the photos in one diary entry and writes back what it found |
| `diary-analysis-queue-apply` | **yes** | The same, for every entry waiting in the queue |

Recipes ending in `-apply` change something in Kamerplanter, and say so in their description. `domain-review` is the one exception to the naming: it touches no garden, but it does write its report into `.audits/` in your checkout. Everything else only reads. Two more, `provider-surface-check` and `provider-plugin-check`, exist to check what an AI assistant can actually do here — useful after an upgrade, uninteresting otherwise.

### Using the recipes without cloning

Goose can fetch recipes from this repository by name:

```sh
export GOOSE_RECIPE_GITHUB_REPO="nolte/kamerplanter-goose"
goose run --recipe connectivity-check
```

That gets you the recipe but **not** `extensions.yaml`, and a recipe with no systems attached has nothing to talk to. Point `GOOSE_ADDITIONAL_CONFIG_FILES` at a copy of that file — from a clone, or your own equivalent — or the run starts with no access to anything. The same goes for the recipes that load know-how from `.claude/skills/`: those need the clone.

If you write that file yourself, list every `${VARIABLE}` you use under that entry's `env_keys`. Leave one out and Goose sends the text `${YOUR_KEY}` as the key itself; the server answers with a plain authentication error, and it reads exactly like a wrong key rather than a missing line.

### About your API key

A Kamerplanter key carries everything its account may do, in every garden that account belongs to. Make a separate one for Goose, so you can withdraw it on its own if you ever need to.

### Writing your own recipe

A recipe is one YAML file in `recipes/`: a title, the options it takes, and the task in plain words. A recipe that only reads has to say so — and has to name the tools it must not call, one by one, because "don't change anything" is left to the assistant's judgement while a named tool is not:

```yaml
version: "1.0.0"
title: "Daily Plant Check"
description: "Compare today's care tasks against what the sensors report"

parameters:
  - key: tenant
    input_type: string
    requirement: required
    description: "Which garden this applies to"

instructions: |
  You report on plant care. You never act on a plant.

prompt: |
  For garden {{ tenant }}, list the care tasks due today, check each one
  against the matching Home Assistant sensor, and report which are really needed.

  Read-only run. Forbidden by name: `mcp__kamerplanter__confirm_care_task`,
  `mcp__kamerplanter__add_plant_diary_entry`,
  `mcp__kamerplanter__set_plant_location`.
```

Check it before committing:

```sh
goose recipe validate recipes/my-recipe.yaml   # is the file well-formed
task test                                      # does it follow the conventions used here
```

`task` reads its own settings from `.envrc`, so run it with direnv active — without that it stops before any target runs, with an error that looks like a network problem and is not one.

Goose behaves in a few ways that are not obvious and cost a debugging session each — a setting that fails silently rather than loudly, a rule that is ignored where you would expect it to hold. They are all written up, with how each one was measured, in [the recipe project pattern](spec/goose/recipe-project-pattern/en.md). Read it before adding a recipe.

## Structure

```
recipes/            one recipe per file — what this repository ships
extensions.yaml     where your systems live, written down once for every recipe
.claude/skills/     the know-how recipes draw on: how to read a photo,
                    how to judge a feeding question, how to check a pest
scripts/            a queue runner that handles one diary entry per run
tests/              the recipe conventions, as a check that can fail
spec/               how it all works, in English and German
docs/               the documentation site
AUDIENCES.md        who this is for
```

## Related repositories

- [nolte/kamerplanter](https://github.com/nolte/kamerplanter) — the plant management system these recipes read from
- [nolte/kamerplanter-ha](https://github.com/nolte/kamerplanter-ha) — brings Kamerplanter into Home Assistant as ordinary entities, if you would rather build dashboards than ask questions
- [nolte/home-assistant-config](https://github.com/nolte/home-assistant-config) — the Home Assistant setup these recipes are developed against

## Status

Early stage, and honest about it. Nine recipes work and are used against a real garden, but there is no released version yet, so names and options can change without warning. Every change is checked automatically before it lands.

Everything here was tried against Goose 1.45.0 with the `claude-code` provider. Another provider may behave differently in ways that are hard to spot — the recipes would still run and still answer.

## License

[MIT](LICENSE). Copyright © 2026 nolte.
