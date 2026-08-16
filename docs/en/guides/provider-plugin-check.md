---
title: Provider plugin check
audience: [maintainer, recipe-author]
content_mode: how-to
track: developer-docs
last_updated: 2026-08-16
---

# Provider plugin check

Its companion, [provider surface check](provider-surface-check.md), asks which tools exist. This one asks the narrower question: when a run holds `Skill` and `Agent`, is the registry behind them actually populated — and which discovery layer is answering, Goose's or the provider's? The two disagree about where a file belongs, and following the wrong one puts a skill or an agent where the run cannot see it, with no error to show for it.

Run it after a Goose upgrade, after a provider change, or after installing a plugin whose skills you intend a recipe to use.

The run is read-only: it writes no file and calls no MCP tool. The two agents it dispatches are probes that reply with a single word and audit nothing.

## Before you start

**Start the run from this repository checkout.** Steps 5 to 7 dispatch probe agents defined in `.claude/agents/` and `.agents/agents/` in this tree. Started elsewhere the recipe reports both as unreachable — which is a wrong measurement, not a failed run, and looks identical to the real result for one of the two.

## Run it

```sh
goose run --recipe provider-plugin-check
```

It takes no parameters.

## What it probes

| # | Probe | Question |
|---|-------|----------|
| 1 | Skill registry | which skill names are listable, and does any carry a plugin prefix |
| 2 | Load a plugin skill | does `Skill(frontend-design:frontend-design)` actually load |
| 3 | Agent type registry | which agent types are listable |
| 4 | Dispatch a plugin agent | does `nolte-shared:project-structure-reviewer` dispatch |
| 5 | Project-agent registry | is `probe-agent-reachable` from `.claude/agents/` among the types |
| 6 | Dispatch it | does that project-local agent answer |
| 7 | Dispatch its twin | does the identical agent in `.agents/agents/` answer |

Steps 5 and 6 are separate on purpose: a registry that does not advertise a type and a registry that rejects it are different results, so step 6 attempts the call even when step 5 did not list the name.

## Read the outcome

One row per probe, with a Result of exactly `AVAILABLE`, `UNAVAILABLE`, or `ERROR` and one line of evidence — the observed names, the returned text, or the verbatim error. Then four closing lines:

```
PLUGIN SKILLS: <available or unavailable>
PLUGIN AGENTS: <available or unavailable>
PROJECT AGENTS (.claude/agents): <available or unavailable>
PROJECT AGENTS (.agents/agents): <available or unavailable>
```

## What was measured here

Against Goose 1.45.0 with `GOOSE_PROVIDER=claude-code`, the last recorded run:

| Capability | Result | Evidence |
|------------|--------|----------|
| Load a plugin skill | works | `Skill(frontend-design:frontend-design)` loaded from the plugin cache |
| Dispatch a plugin agent | fails | `Agent type '…' not found.` against a list of the provider's built-ins |
| Dispatch an agent from `.claude/agents/` | works | the probe returned `reachable` |
| Dispatch the twin from `.agents/agents/` | fails | `Agent type 'probe-agents-dir' not found.` in the same run |

Three results in one run settle which layer is answering: the registry lists Claude Code's own built-ins, the dispatch goes through the provider's `Agent` tool, and only `.claude/` is read. **This is the provider's agent layer, not Goose's** — the exact counterpart of what happens to skills, where the provider's `.claude/skills/` reader survives and Goose's `load_skill` does not.

The trap is that Goose's own documentation names `.agents/agents/` as the place for new project agents, and that is the one directory this provider cannot see. If your own run reproduces the table above, nothing changed. If it does not, the statements in `spec/goose/recipe-project-pattern/` are the ones to update — that is what the recipe exists for.

## Sources

- [`recipes/provider-plugin-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/provider-plugin-check.yaml) — the seven probes and why two probe agents exist
- [`spec/goose/recipe-project-pattern/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/goose/recipe-project-pattern/en.md) — the measurements with their dates, and the directory table they produced
