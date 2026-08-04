# Goose Recipe Project Pattern

Status: draft
Portfolio-Scope: local

## Context

A repository that ships reusable Goose recipes hits the same set of obstacles regardless of what the recipes do. Extension blocks get copied into every file. A credential silently fails to expand and the run reports a server outage. A constraint placed in the wrong key is ignored on a headless run. The agent turns out to hold tools nobody declared.

None of that is discoverable by reading a recipe. Each rule below was measured against **Goose 1.45.0** with the `claude-code` provider — by capturing the requests Goose actually issues, and by probing the running agent's tool surface — because the observable behaviour and the documented behaviour differ in several places.

This spec is the mechanics layer for this repository. The per-backend specs under `spec/mcp/` describe *what a server offers*; this one describes *how a Goose project is built around them*, so the same rule is not restated per backend.

Readers: anyone adding a recipe here, and anyone starting a comparable Goose repository who wants the failure modes up front rather than one debugging session at a time.

## Goals

- An MCP server is declared once per repository, not once per recipe
- A misconfigured credential produces a message naming the credential, not a false report about the server
- The read/write boundary of a recipe is visible from its filename and enforced where Goose actually enforces things
- The tools an agent really holds are knowable before a recipe is trusted with them
- A new recipe costs a prompt, not a setup

## Non-Goals

- Recipe prompt engineering or output-format design
- Which MCP backends to use and what their tools mean — that is `spec/mcp/`
- Goose provider selection, model choice, or cost management
- Packaging recipes for consumers outside this repository's own distribution

## Measured behaviour

### Extension declaration and precedence

Extensions may be declared in a recipe's `extensions:` block or in a shared file loaded through `GOOSE_ADDITIONAL_CONFIG_FILES`. **The two do not merge.** Measured: with a shared extension and a recipe-local one both configured, only the recipe-local one connected; the shared entry produced no request at all.

A recipe therefore either declares every extension it needs, or declares none and inherits the shared set. There is no "shared plus one more".

The two locations use different shapes for the same data:

| Location | Shape |
|----------|-------|
| Shared config file | `extensions:` is a **map** keyed by name, each entry needs `enabled: true` |
| Recipe | `extensions:` is a **list**, no `enabled` key |

### Environment variable expansion

`${VAR}` inside an extension is expanded **only** when `VAR` is listed in that extension's `env_keys`. Measured against a capture server:

| Declaration | What Goose sent |
|-------------|-----------------|
| `${SECRET}`, no `env_keys` | `${SECRET}` — the literal string |
| `${SECRET}` with `env_keys: ["SECRET"]` | the value |
| `{{ param }}` as a recipe parameter | the value |

The failure is silent and misleading: the recipe validates, the extension connects, and the server answers `401` as though the credential were wrong.

**An extension whose `env_keys` variable is unset is skipped entirely** — no `Failed to start extension` warning, the tools are simply absent. Observed when `pass` could not decrypt: two extensions vanished while a third, whose variable was set, loaded normally. The agent diagnosed it as "no MCP servers configured", which was wrong.

`--render-recipe` does not settle this: it prints `${VAR}` unexpanded either way.

### Recipe discovery and distribution

- `GOOSE_RECIPE_PATH` accepts several directories separated by `:`
- Discovery is **flat** — `*.yaml` directly under each directory; nested folders are not walked
- `GOOSE_RECIPE_GITHUB_REPO` takes `owner/repo` and fetches recipes by name
- It fetches **recipes only**. A shared extensions file is not part of that transfer, so a recipe consumed this way arrives with no servers unless the consumer supplies the config separately

### Where constraints are enforced

A recipe declaring `instructions` but no `prompt` loads and validates, then fails a headless run with `no text provided for prompt`. Constraints stated only in `instructions` have been observed to be ignored. Anything that must hold belongs in `prompt`.

### Provider surface

The provider is not necessarily a bare model endpoint. Measured with `GOOSE_PROVIDER=claude-code`, a recipe declaring no extensions and loading no shared config still reported **29 non-MCP tools**, including `Bash`, `Read`, `Write`, `Edit`, `WebFetch`, `WebSearch`, `Agent`, `Workflow`, `Skill`, and the `Task*` / `Cron*` families.

A "read-only" recipe under such a provider holds shell access, file-write access, and the ability to spawn subagents. Its read-only property is **prompt discipline, not a technical boundary**. MCP tools from Goose extensions appear as `mcp__<server>__<tool>`.

### Plugin availability

Under the `claude-code` provider, measured:

| Capability | Result | Evidence |
|------------|--------|----------|
| Load a plugin **skill** | works | `Skill(frontend-design:frontend-design)` loaded from the plugin cache |
| Dispatch a plugin **agent** | fails | `Agent type '…' not found. Available agents: claude, Explore, general-purpose, Plan, statusline-setup` |

Only skills from plugins that are installed and enabled are visible; skills reachable in an interactive Claude Code session by another mechanism are not.

## Project layout

```
recipes/                       one recipe per file, flat — the shipped artifact
extensions.yaml                every MCP server, declared once
spec/                          this layer plus one spec per backend
.envrc                         endpoints, credential lookups, config path
```

## Requirements

- **MUST** declare each MCP server exactly once for the repository — in `extensions.yaml` — and recipes relying on it **MUST NOT** carry an `extensions:` block of their own, since a recipe-local block replaces the shared set rather than extending it
- **MUST** list every `${VAR}` an extension references in that extension's `env_keys`, wherever the extension is declared
- **MUST** resolve credentials from the environment; a literal credential **MUST NOT** appear in a recipe, in `extensions.yaml`, or in any tracked file
- **MUST** place every constraint that has to hold in the recipe's `prompt`; `instructions` **MAY** carry framing and tone but **MUST NOT** be the only place a prohibition appears
- **MUST** name the specific tools a read-only recipe may not call, rather than describing the category alone, so the prohibition does not depend on the model's classification
- **MUST** carry an `-apply` filename suffix and state the effect in `description` when a recipe calls any state-changing tool
- **MUST** keep `recipes/` flat; grouping **MUST** be encoded in filenames, because discovery does not walk subdirectories
- **MUST** state in the repository's README that consuming recipes over `GOOSE_RECIPE_GITHUB_REPO` requires supplying the extension config separately
- **MUST NOT** treat a read-only prompt as a security boundary under a provider that supplies execution tools; a recipe handling untrusted input **MUST** run under a provider without them, or under `--no-profile`
- **SHOULD** ship a connectivity recipe that exercises every declared server read-only and reports per-server PASS/FAIL, and **SHOULD** run it before trusting any other recipe against a new environment
- **SHOULD** ship a provider-surface recipe that inventories the agent's tools, so the execution surface is a measurement rather than an assumption
- **SHOULD** report an absent tool as an explicit step result naming the tool, never as a silent substitution
- **SHOULD** distinguish an unset credential from an unreachable server when reporting a failure, since an extension with an unset `env_keys` variable disappears without a warning
- **MAY** declare extensions inside a single recipe when it is meant to be consumed standalone, accepting that it then forgoes the shared set entirely

## Acceptance Criteria

- [ ] Every MCP server appears exactly once across the repository
- [ ] No recipe that relies on `extensions.yaml` declares an `extensions:` block
- [ ] Every `${VAR}` used in an extension is listed in that extension's `env_keys`
- [ ] No tracked file contains a literal credential
- [ ] Every prohibition a recipe depends on appears in its `prompt`
- [ ] Every recipe calling a state-changing tool has an `-apply` filename
- [ ] `recipes/` contains no subdirectories
- [ ] The README states the extension-config requirement for GitHub-sourced recipes
- [ ] A connectivity recipe exists and passes against the current environment
- [ ] A provider-surface recipe exists and its latest result is recorded
- [ ] `goose recipe validate` passes for every file in `recipes/`

## Open Questions

- Whether the provider's tool surface can be constrained per recipe rather than per run; `--no-profile` is documented as dropping default extensions, but its effect on provider-supplied tools was not measured.
- How several files are separated in `GOOSE_ADDITIONAL_CONFIG_FILES`, and whether `~/.config/goose/config.yaml` behaves identically to an additional file. Untested — the user's global config was deliberately left untouched.
- Whether MCP servers configured in the provider's own settings are exposed to the Goose agent. The probe returned none, but the provider's servers were failing at the time, so "not forwarded" and "forwarded but broken" are indistinguishable from the result.
- Whether a skill installed as a plugin becomes visible to Goose immediately or only after a session restart.

## Source

- Measured against Goose 1.45.0 with `GOOSE_PROVIDER=claude-code`, 2026-08-04: extension precedence and `env_keys` expansion captured with a local HTTP server logging inbound headers; recipe discovery probed with `goose recipe list`; tool surface and plugin availability probed with `recipes/provider-surface-check.yaml` and `recipes/provider-plugin-check.yaml`
- `goose run --help`, `goose recipe --help` (Goose 1.45.0) for discovery and extension flags
- Per-backend contracts: `spec/mcp/kamerplanter-mcp-server/en.md`, `spec/mcp/home-assistant-mcp-server/en.md`
