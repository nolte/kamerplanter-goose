---
title: Provider surface check
audience: [maintainer, recipe-author]
content_mode: how-to
track: developer-docs
last_updated: 2026-08-16
---

# Provider surface check

A recipe here declares what it must not call, and that declaration is worth exactly as much as your knowledge of what the agent can call in the first place. Under `claude-code` the running agent holds `Bash`, `Write`, `Edit`, `WebFetch`, and `Agent` no matter what a recipe says — **a read-only recipe is prompt discipline, not a boundary**. `provider-surface-check` inventories the tool surface a run actually holds, so that sentence stays a measurement rather than a memory.

Run it after a Goose upgrade, after a provider change, or before trusting a claim in `spec/goose/` that was measured against an older version.

The run calls **nothing at all** — not one MCP tool, not the shell, not a file read. Calling anything would change what the inventory measures.

## Run it

```sh
goose run --recipe provider-surface-check
```

It takes no parameters. It loads no project skill either, so it runs from any working directory.

To separate what Goose contributed from what the provider brought along, run it twice:

```sh
goose run --recipe provider-surface-check                        # with GOOSE_ADDITIONAL_CONFIG_FILES set
env -u GOOSE_ADDITIONAL_CONFIG_FILES goose run --recipe provider-surface-check
```

The difference between the two inventories is exactly what the shared `extensions.yaml` added. Whatever appears in **both** came from the provider.

## Read the outcome

The report has four sections and nothing else:

| Section | Contents |
|---------|----------|
| 1. MCP tools | every `mcp__<server>__<tool>` name, grouped by server, with a count per server |
| 2. Execution and file access | yes/no plus the exact tool name for shell execution, file reading, file writing, and URL fetching |
| 3. Agent and orchestration tools | anything that spawns subagents, schedules work, runs workflows, manages tasks, or loads skills |
| 4. Everything else | the remaining tool names |

| Closing line | Means |
|--------------|-------|
| `SURFACE: <n> MCP servers, <m> non-MCP tools` | `<n>` counted from section 1, `<m>` across sections 2 to 4 |

## What the numbers do and do not tell you

The non-MCP count is not stable between runs, and a smaller number does not mean a smaller surface. Some tools are deferred behind `ToolSearch` and need a schema fetch before they can be called — deferred is not absent, and `Bash` and `Write` have been in the directly-callable set either way.

Two results are worth knowing before you read your own inventory:

- **The provider replaces the whole Goose tool set, not part of it.** No Goose platform extension has appeared in an inventory — no `developer`, `todo`, `analyze`, or `summon` — even with all four enabled in `~/.config/goose/config.yaml`. Only MCP extensions survive, as `mcp__*`.
- **Anything Goose offers as a platform tool must be assumed missing here until measured present.** That includes `load_skill`; `goose skills list` reports discovery, not runtime availability.

For whether the plugin and project layers behind `Skill` and `Agent` are populated, use its companion, [provider plugin check](provider-plugin-check.md).

## Sources

- [`recipes/provider-surface-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/provider-surface-check.yaml) — the four sections and the counting rule
- [`spec/goose/recipe-project-pattern/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/goose/recipe-project-pattern/en.md) — the recorded inventories with their measurement dates and Goose version
