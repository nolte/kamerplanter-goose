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
- A recipe that reuses a project's skills states what it needs from the environment, rather than failing silently when it is missing
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

The count is not stable: a repeat inventory on 2026-08-05 returned **32** non-MCP tools from the same provider, of which only ten (`Agent`, `Bash`, `Edit`, `Read`, `ReportFindings`, `ScheduleWakeup`, `Skill`, `ToolSearch`, `Workflow`, `Write`) were directly callable — the rest were deferred behind `ToolSearch` and needed a schema fetch first. Deferred is not absent: `Bash` and `Write` are in the directly-callable set either way, so the boundary above does not move.

**What the provider replaces is the whole Goose tool set, not part of it.** In that same inventory not one Goose platform extension appeared — no `developer`, `todo`, `analyze`, or `summon` tool — although all four are `enabled: true` in `~/.config/goose/config.yaml`. Only MCP extensions survive the substitution, as `mcp__*`. Anything Goose offers as a platform tool must therefore be assumed missing under this provider until measured present.

### Plugin availability

Under the `claude-code` provider, measured:

| Capability | Result | Evidence |
|------------|--------|----------|
| Load a plugin **skill** | works | `Skill(frontend-design:frontend-design)` loaded from the plugin cache |
| Dispatch a plugin **agent** | fails | `Agent type '…' not found. Available agents: claude, Explore, general-purpose, Plan, statusline-setup` |

Only skills from plugins that are installed and enabled are visible; skills reachable in an interactive Claude Code session by another mechanism are not.

### Agents from a project checkout

A plugin agent being unreachable says nothing about an agent defined in the checkout itself. Goose documents an agent layer of its own — Markdown files with `name`, `description`, and `model` frontmatter, discovered under `.agents/agents/`, `.goose/agents/`, and `.claude/agents/` in the project plus their `~` counterparts, and invoked conversationally by `@name` or by asking Goose to delegate. It names `.agents/agents/` as the location new project agents should use.

Measured 2026-08-07 with two probe agents whose only job is to answer with one word, identical but for their directory:

| Capability | Result | Evidence |
|------------|--------|----------|
| List a project-local **agent** type | works | `probe-agent-reachable` appeared in the registry beside the five built-ins, carrying its own `description` and `(Tools: Read)` |
| Dispatch it from `.claude/agents/` | works | `Agent(subagent_type: probe-agent-reachable)` returned `reachable` |
| Dispatch the twin from `.agents/agents/` | fails | `Agent type 'probe-agents-dir' not found. Available agents: claude, Explore, general-purpose, Plan, probe-agent-reachable, statusline-setup` |
| Dispatch a plugin agent, same run | fails | `Agent type 'nolte-shared:project-structure-reviewer' not found.` — same available list |

Three results in one run settle which layer is answering. The registry lists Claude Code's own built-ins (`Explore`, `Plan`, `general-purpose`), the dispatch goes through the provider's `Agent` tool with a `subagent_type`, and only the `.claude/` directory is read. **This is the provider's agent layer, not Goose's** — the exact counterpart of what happens to skills, where the provider's `.claude/skills/` reader survives and Goose's `load_skill` does not.

The consequence is a trap, because the two layers disagree about where a file belongs:

| Directory | Goose's documentation | Reachable from a recipe run here |
|-----------|-----------------------|-----------------------------------|
| `.claude/agents/` | supported, legacy | yes |
| `.agents/agents/` | recommended for new project agents | **no** |
| `~/.claude/plugins/*/agents/` | not Goose's mechanism | no |

Following Goose's own recommendation puts a project agent where this provider cannot see it, and the failure is a plain "not found" against a list that looks complete. Whether Goose's `@name` invocation works under a native provider is untested here; only `claude-code` is configured, so "absent under this provider" and "absent everywhere" stay indistinguishable, exactly as with `load_skill`.

Discovery is cwd-relative in the same way project skills are, and carries the same failure mode: a run started from another directory loses the agent without an error. Unlike a skill, an agent has no `disable-model-invocation` equivalent, so there is no way to hide one from a non-interactive run.

This repository ships skills rather than agents regardless, because a skill runs in the caller's context and composes with the others rather than answering from a fresh one. The two probes exist to keep the statements above measurements rather than assumptions, and are the only agents here.

### Skills from a project checkout

Goose has a skill layer of its own — a `skills` platform extension, a `goose skills list` command, and a `load_skill` tool documented as "Load a skill's full content into your context so you can follow its instructions". It discovers skills under `.claude/skills/`, `.agents/skills/`, and `.goose/skills/` in the current project, plus `~/.agents/skills/`, `~/.agents/plugins/*/skills/`, and `builtin://skills/`.

**Under the `claude-code` provider that layer is unreachable.** `goose skills list` run from a project checkout listed all 18 of its skills correctly, but a run started in that same directory reported `load_skill` absent — consistent with the whole-tool-set substitution above. `goose skills list` is a statement about discovery, not about runtime availability.

What works instead is the provider's own equivalent, which reads the same `.claude/skills/` directory relative to the **working directory of the Goose process**. Measured end to end: a recipe resolved from `GOOSE_RECIPE_PATH` in one repository, run with the cwd set to a second repository, loaded that second repository's project skill and received the recipe's `{{ parameter }}` as the skill's `$ARGUMENTS`.

One frontmatter key decides whether a project skill exists at all for a recipe run:

| Skill frontmatter | Visible to a recipe run |
|-------------------|-------------------------|
| no `disable-model-invocation` key | yes |
| `disable-model-invocation: true` | no |

Measured with two otherwise identical probe skills in one directory: the run listed the first and not the second. The key means "only a human may invoke this, by slash command" — and a recipe run has no human. Goose's own `skills list` ignores the key and shows such skills anyway, so the two views disagree, and the optimistic one is the one that does not run the recipe.

The working directory is the only lever. Measured, neither `GOOSE_SEARCH_PATHS` nor `GOOSE_WORKING_DIR` changed what was discovered; the recipe schema has no `skills:` key and `goose run` no corresponding flag. A symlink at `.claude/skills` pointing into another checkout **is** followed, which relocates discovery without relocating the process — but a skill that reads its own repository's files needs that repository as cwd regardless.

### Sub-recipes

The recipe schema accepts a `sub_recipes:` list — entries carrying `name`, `path`, `values`, and `sequential_when_repeated` — and `goose run` accepts a repeatable `--sub-recipe` flag. Both are the natural way to build a queue runner that calls a single-entry recipe once per item.

**Neither works under the `claude-code` provider.** Measured 2026-08-05 with a child recipe whose only job was to `touch` a marker file: with a `sub_recipes:` block, and again with `--sub-recipe`, the run reported no sub-recipe tool and **no marker file was created**. The mechanism is registered as a Goose tool, so it disappears in the same tool-set substitution that removes `load_skill`.

The failure mode is worth naming because it is not a clean error. Asked whether a sub-recipe tool exists, a run once answered `subrecipe__echo_child` — a plausible name constructed from the recipe's own `name:` field, with no such tool present. A model's claim that it invoked a sub-recipe is not evidence that anything ran; only an observable side effect is.

A loop over N items therefore has two shapes here: iterate inside one recipe over shared skills, accepting one context for the whole batch, or start one Goose process per item from a shell script, which keeps per-item isolation at the cost of a process start.

`goose plugin install <git-url>` installs a git repository carrying `plugin.json` (or `.goose-plugin/plugin.json`, or `.plugin/plugin.json`) plus `skills/`, `agents/`, and `.mcp.json` into `~/.agents/plugins/`, which lifts discovery out of the cwd on the Goose side. It does not help here: the tool that would load those skills is the one the provider removed.

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
- **MUST** carry an `-apply` filename suffix and state the effect in `description` when a recipe calls a tool that changes a backend's state — the `mcp.write` and `mcp.setup` classes. The suffix is a statement about somebody's garden, not about the filesystem: a recipe that only writes a report into the gitignored `.audits/` tree **MUST NOT** take the suffix, and **MUST** say what it writes in its `description` instead, since `-apply` would otherwise read as a warning about data nobody can lose
- **MUST** keep `recipes/` flat; grouping **MUST** be encoded in filenames, because discovery does not walk subdirectories
- **MUST** state in the repository's README that consuming recipes over `GOOSE_RECIPE_GITHUB_REPO` requires supplying the extension config separately
- **MUST NOT** treat a read-only prompt as a security boundary under a provider that supplies execution tools; a recipe handling untrusted input **MUST** run under a provider without them, or under `--no-profile`
- **MUST** state the required working directory in the `description` of a recipe that loads a project skill, since skill discovery is relative to the Goose process's cwd and a recipe run from elsewhere loses the skill without an error
- **MUST NOT** call `load_skill`, or otherwise rely on Goose's own skill layer, under a provider that substitutes the Goose tool set; a name shown by `goose skills list` **MUST NOT** be treated as evidence that the skill is loadable at runtime
- **MUST NOT** rely on `sub_recipes:` or `--sub-recipe` under such a provider, and **MUST** verify any claimed sub-recipe invocation by an observable side effect rather than by the run's own report, since a run will name a plausible sub-recipe tool that does not exist
- **MUST NOT** carry `disable-model-invocation: true` in a project skill that a recipe is meant to load, since the key makes the skill invisible to every non-interactive run
- **MUST** place a project agent under `.claude/agents/` rather than the `.agents/agents/` that Goose's own documentation recommends, since only the former is in the registry a run under this provider sees
- **MUST** name the required working directory in the `description` of a recipe that dispatches a project-local agent, for the same reason it does for a skill: `.claude/agents/` resolves against the Goose process's cwd, and no frontmatter key exists to make an agent selectively invisible when it does not
- **MUST NOT** dispatch a plugin-provided agent type from a recipe; only the built-in types and those defined in the working directory's `.claude/agents/` are in the registry a run sees
- **SHOULD** ship a connectivity recipe that exercises every declared server read-only and reports per-server PASS/FAIL, and **SHOULD** run it before trusting any other recipe against a new environment
- **SHOULD** ship a provider-surface recipe that inventories the agent's tools, so the execution surface is a measurement rather than an assumption
- **SHOULD** report an absent tool as an explicit step result naming the tool, never as a silent substitution
- **SHOULD** have a recipe that loads a skill report the load as a named step result, since a skill that fails to load leaves a run that still produces a plausible answer from the prompt alone
- **SHOULD** verify skill availability by measurement in the target environment before a recipe depends on it, the same way the provider's tool surface is measured rather than assumed
- **SHOULD** distinguish an unset credential from an unreachable server when reporting a failure, since an extension with an unset `env_keys` variable disappears without a warning
- **MAY** declare extensions inside a single recipe when it is meant to be consumed standalone, accepting that it then forgoes the shared set entirely

## Acceptance Criteria

- [ ] Every MCP server appears exactly once across the repository
- [ ] No recipe that relies on `extensions.yaml` declares an `extensions:` block
- [ ] Every `${VAR}` used in an extension is listed in that extension's `env_keys`
- [ ] No tracked file contains a literal credential
- [ ] Every prohibition a recipe depends on appears in its `prompt`
- [ ] Every recipe calling an `mcp.write` or `mcp.setup` tool has an `-apply` filename
- [ ] Every recipe that writes anything at all says so in its `description`, whether or not it carries the suffix
- [ ] `recipes/` contains no subdirectories
- [ ] The README states the extension-config requirement for GitHub-sourced recipes
- [ ] A connectivity recipe exists and passes against the current environment
- [ ] A provider-surface recipe exists and its latest result is recorded
- [ ] No recipe calls `load_skill`
- [ ] No recipe declares `sub_recipes:` or is launched with `--sub-recipe` while the provider substitutes the Goose tool set
- [ ] Every recipe that loads a project skill names the required working directory in its `description`
- [ ] No skill loaded by a recipe carries `disable-model-invocation: true`
- [ ] No recipe dispatches a plugin-provided agent type
- [ ] Every project agent lives under `.claude/agents/`, not `.agents/agents/`
- [ ] `goose recipe validate` passes for every file in `recipes/`

## Open Questions

- Whether the provider's tool surface can be constrained per recipe rather than per run; `--no-profile` is documented as dropping default extensions, but its effect on provider-supplied tools was not measured.
- How several files are separated in `GOOSE_ADDITIONAL_CONFIG_FILES`, and whether `~/.config/goose/config.yaml` behaves identically to an additional file. Untested — the user's global config was deliberately left untouched.
- Whether MCP servers configured in the provider's own settings are exposed to the Goose agent. The probe returned none, but the provider's servers were failing at the time, so "not forwarded" and "forwarded but broken" are indistinguishable from the result.
- Whether a skill installed as a plugin becomes visible to Goose immediately or only after a session restart.
- Whether `load_skill` appears under a native model provider such as `anthropic` or `openai`, which would make Goose's own skill layer — and with it `~/.agents/plugins/` and `goose plugin install` — usable. Untested: only `claude-code` is configured here, so "absent under this provider" and "absent everywhere" are not distinguishable from the measurement.
- Whether Goose's own agent layer — `@name` invocation and the `.agents/agents/` directory it documents — works under a native model provider. Untested for the same reason `load_skill` is: only `claude-code` is configured, and under it the provider's agent layer answers instead. If it does, an agent would have two incompatible homes depending on the provider, which is worse than the current single one.
- Whether distributing skills as a provider-side plugin is a steadier route than the cwd, given that the cwd is also what a skill's own file paths resolve against. Not measured; the two concerns pull in opposite directions and no recipe here yet depends on a skill.
- Whether the deferred-tool split observed on 2026-08-05 varies by provider version or by session, and whether a tool can move between the deferred and directly-callable sets while a run is in progress.

## Source

- Measured against Goose 1.45.0 with `GOOSE_PROVIDER=claude-code`, 2026-08-04: extension precedence and `env_keys` expansion captured with a local HTTP server logging inbound headers; recipe discovery probed with `goose recipe list`; tool surface and plugin availability probed with `recipes/provider-surface-check.yaml` and `recipes/provider-plugin-check.yaml`
- Measured against Goose 1.45.0 with `GOOSE_PROVIDER=claude-code`, 2026-08-05: skill discovery probed with `goose skills list` from several working directories and with a symlinked skills directory; `load_skill` availability, the tool inventory, and the `disable-model-invocation` effect probed with headless `goose run --no-session` runs, the last against two purpose-built probe skills differing only in that key; parameter-to-`$ARGUMENTS` passing probed with a throwaway recipe on `GOOSE_RECIPE_PATH` run from a different repository's checkout; discovery paths and the plugin manifest layout read from the binary's embedded strings; sub-recipe availability probed with a child recipe whose only effect was creating a marker file, run once via a `sub_recipes:` block and once via `--sub-recipe`
- Measured against Goose 1.45.0 with `GOOSE_PROVIDER=claude-code`, 2026-08-07: project-local agent discovery and dispatch probed with `recipes/provider-plugin-check.yaml` extended by three steps, against two purpose-built probe agents identical but for their directory — `.claude/agents/probe-agent-reachable.md` and `.agents/agents/probe-agents-dir.md`; the plugin-agent dispatch in the same run supplied the third contrasting result
- Goose documentation, *Custom Agents* (`https://goose-docs.ai/docs/guides/context-engineering/custom-agents/`), read 2026-08-07, for the documented discovery directories, the `name` / `description` / `model` frontmatter, and the recommendation to use `.agents/agents/` — the recommendation the measurement above contradicts under this provider
- `goose run --help`, `goose recipe --help`, `goose skills --help`, `goose plugin install --help` (Goose 1.45.0) for discovery and extension flags
- Per-backend contracts: `spec/mcp/kamerplanter-mcp-server/en.md`, `spec/mcp/home-assistant-mcp-server/en.md`
