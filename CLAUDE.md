# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A catalog of [Goose](https://github.com/block/goose) recipes that wire the Kamerplanter and Home Assistant MCP servers into repeatable plant-care runs. There is no application code and no runtime build — the shipped artifact is the YAML under `recipes/`, plus the project skills the recipes load and the specs that record measured Goose behaviour. The only Python here is `tests/validate_recipes.py`, which enforces the house pattern.

Everything here is verified against **Goose 1.45.0 with `GOOSE_PROVIDER=claude-code`**. Statements about Goose behaviour in `spec/` are measurements, not readings of the docs; the two differ in several places.

## Commands

```sh
direnv allow                                    # endpoints, pass-backed credentials, Task's remote-include flags
task setup                                      # project-local venv, install sets, git hooks
task worktree:add -- feat/<slug>                # parallel working copy off origin/develop

task check                                      # the quality gate CI runs: test + lint + docs
task test                                       # recipe contract only (tests/validate_recipes.py)
task docs                                       # mkdocs build --strict, same command as CI

goose recipe list -v                            # what is discoverable
goose recipe validate recipes/<name>.yaml       # schema only; task test covers the house pattern
goose run --recipe <name> --explain             # parameters + extensions without a model call

goose run --recipe connectivity-check --params tenant=my-garden
goose run --no-session --max-turns 25 -q --recipe diary-photo-analysis-apply \
  --params entry_key=<key> --params run_id=<id>
goose run --recipe domain-review --params persona=casual-owner \
  --params target=recipes/nutrient-imbalance-check.yaml

scripts/analyse-queue.sh [max_entries] [tenant] # queue, one Goose process per entry
```

Run `connectivity-check` first against any new environment; it names a bad URL, a revoked key, or a disabled MCP server before a real recipe misreports it. `provider-surface-check` and `provider-plugin-check` re-measure the agent's tool surface when a Goose or provider version changes.

The `worktree:*` and `mkdocs:*` targets come from [nolte/taskfiles](https://github.com/nolte/taskfiles) as remote includes, so **every** `task` invocation here needs `TASK_X_REMOTE_TASKFILES=1` and `TASK_TRUSTED_HOSTS=raw.githubusercontent.com` — both set by `.envrc`. Without them Task fails at parse time with `not trusted by user`, which reads like a network problem and is not one. CI never calls `task`; it runs the same commands directly, so the quality gate does not depend on fetching a floating branch.

`docs:serve` delegates to `mkdocs:start`, which runs from the shared `~/.venvs/docs` — the module hardcodes that path and a consumer cannot override it. `docs` stays local because it is the CI command and must resolve the exact pins in `docs/requirements.txt` from the project-local `.venv`.

`tests/validate_recipes.py` is where the constraints below are enforced. It checks what the schema cannot see — a recipe-local `extensions:` block, a missing `prompt`, an `${VAR}` absent from `env_keys`, a write-capable recipe without the `-apply` suffix, a named skill with no directory, an agent in the directory this provider cannot see — and runs without a provider call. Adding a house rule means adding a check there, not only a paragraph to the spec.

Every recipe that loads a project skill **must be started with this checkout as the working directory** — skill discovery is relative to the Goose process's cwd, and a run from elsewhere loses the skill silently and still produces a plausible answer.

## Architecture

Three layers, each declared once:

- `extensions.yaml` — every MCP server for the whole repository (`kamerplanter`, `home_assistant`, `github`), loaded via `GOOSE_ADDITIONAL_CONFIG_FILES`.
- `recipes/*.yaml` — flat, one recipe per file, no `extensions:` block of its own. A recipe is orchestration: parameters, hard constraints, numbered steps, and a fixed report format.
- `.claude/skills/*/SKILL.md` — the reusable procedures the recipes call by name. Domain knowledge and measured server behaviour live here, so several recipes share one procedure. Two classes:
  - **Garden procedures**, which read the MCP servers: `diary-analysis-claim`, `plant-context-collect`, `plant-photo-read`, `nutrient-imbalance-assess`, `pest-pressure-assess`, `species-baseline-verify`, `plant-lifecycle-resolve`.
  - **Review lenses**, which read this checkout and never touch a garden: `agronomy-review`, `indoor-grower-review`, `casual-owner-review`, `outdoor-gardener-review`. One persona per run; they are meant to disagree, and averaging their verdicts destroys the result.
- `.claude/agents/` — measurement probes only, never working artefacts. Skills compose in the caller's context; an agent answers from a fresh one, which is the wrong shape for everything here. The probes exist so the statements about agent reachability in `spec/goose/` stay measurements.

`spec/` mirrors that split and is the authority for it: `spec/goose/` is the mechanics layer (how a recipe project is built), `spec/mcp/` is what each backend offers, `spec/process/` is what a recipe does with them. A rule stated in one layer is not restated in another. Canonical language is `en`; `de.md` is a translation kept in sync, and `spec/README.md` is generated — regenerate it with the `spec` skill rather than editing it.

`recipes/diary-analysis-queue-apply.yaml` and `scripts/analyse-queue.sh` are two shapes of the same queue run: the recipe loops inside one context, the script starts a fresh `goose run` per entry for genuine isolation. Neither uses Goose's `sub_recipes:` — see below.

## Constraints that are not visible from a recipe file

These are the failure modes `spec/goose/recipe-project-pattern/en.md` exists to record. Read it in full before changing recipe or extension structure.

- **A recipe's `extensions:` block replaces the shared set, it does not extend it.** Declare one entry and `extensions.yaml` is ignored entirely for that run. Shapes differ too: a map with `enabled: true` per entry in the shared file, a list in a recipe.
- **`${VAR}` is expanded only when `VAR` is listed in that extension's `env_keys`.** Omit it and the literal `${VAR}` goes over the wire, and the server answers `401` as though the credential were wrong. An extension whose `env_keys` variable is *unset* disappears with no warning at all.
- **Constraints belong in `prompt`, not only in `instructions`.** A recipe with only `instructions` fails a headless run with `no text provided for prompt`, and constraints stated only there have been observed to be ignored.
- **Name the forbidden tools individually** (`mcp__kamerplanter__confirm_care_task`, …) rather than describing a category — the prohibition must not depend on the model's classification.
- **A read-only recipe is prompt discipline, not a boundary.** Under `claude-code` the agent holds `Bash`, `Write`, `Edit`, `WebFetch`, and `Agent` regardless of what the recipe declares.
- **Goose's own skill layer is unreachable under this provider.** Never call `load_skill`; `goose skills list` reports discovery, not runtime availability. A skill carrying `disable-model-invocation: true` is invisible to every recipe run.
- **A project agent is dispatchable from `.claude/agents/` and nowhere else.** Measured: the registry a run sees is Claude Code's built-ins plus that directory. `.agents/agents/` — the location Goose's own documentation recommends for new project agents — is **not** in it, and a plugin agent type is not either. Both fail with a plain `not found` against a list that looks complete.
- **`sub_recipes:` and `--sub-recipe` do not work under this provider** and fail without a clean error — a run will name a plausible sub-recipe tool that does not exist. Verify any claimed invocation by an observable side effect.
- **Discovery is flat.** No subdirectories under `recipes/`; encode grouping in the filename.

## Conventions

- A recipe that calls any state-changing tool carries an `-apply` filename suffix, opens its `description` with `WRITES to …`, and states the effect there.
- Credentials never appear in a tracked file; they come from the environment via `.envrc` and `pass`.
- A recipe that loads a project skill names the required working directory in its `description`.
- Recipes close with a fixed PASS/FAIL or status table and a machine-readable final line (`SUBMITTED: completed`, `NOT CLAIMED: <reason>`), so a run's outcome is greppable.
- An absent tool is reported as an explicit step result naming the tool, never silently substituted.
- Communication with the user is German; recipes, skills, specs, and commit messages stay English.
