---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter-goose"
issue: "75"
classification: "bug"
secondary-classes: ["spec-change"]
route: "direct"
status: draft
created: "2026-11-05"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter-goose
- **Issue**: #75 — Guard read-only recipes that reach Home Assistant: actuation by category and the unclassified intents
- **URL**: https://github.com/nolte/kamerplanter-goose/issues/75
- **Labels**: none
- **Linked items**: refs #49, PR #67 (merged, source of the follow-up). No open PR references #75 (`gh pr list --state all --search "75 in:body"` → `[]`).
- **Prior art checked**: `project/requirements/` does not exist; no open PR; `tests/validate_recipes.py` has no HA check.
- **Trust**: issue author `nolte` is the repository owner; no comments. Trusted.

## Classification

- **Primary class**: bug
- **Secondary class(es)**: spec-change (records the new literal marker in `spec/goose/recipe-project-pattern/`)
- **Rationale**: two MUSTs of `spec/mcp/home-assistant-mcp-server/en.md:94,96` are not enforced, and nine recipes currently violate the marker convention they would be checked under.
- **Asserted cause verified**: confirmed, and wider than the issue states.
  - `grep -n "Hass\|actuat\|TimeTillErnte\|home_assistant" tests/validate_recipes.py` → no output, rc=1.
  - `TimeTillErnte` / `time_till` are named in prose outside every `Forbidden by name:` block in **9** recipes, not 1: `connectivity-check.yaml:53-55`, `weather-impact-check.yaml:82-83`, `garden-review.yaml:114`, `growth-stage-check.yaml:117`, `harvest-plan.yaml:135`, `harvest-readiness-check.yaml:131`, `pest-ipm-plan.yaml:101`, `plant-health-assessment.yaml:111`, `season-review.yaml:124`.
  - The same holds in two skills loaded by read-only recipes: `.claude/skills/harvest-planning/SKILL.md:148`, `.claude/skills/weather-impact-analysis/SKILL.md:112`.
  - All 31 recipes name Home Assistant; `extensions.yaml:29-37` loads `home_assistant` into every run. The issue's predicate ("names HA") therefore equals the spec's ("every non-`-apply` recipe", `en.md:94,109`): 27 recipes.
  - Only `connectivity-check.yaml:50` carries a literal category marker (`Forbidden on Home Assistant:`); 23 carry the prose form "Call NO Home Assistant tool. Specifically, do not turn …"; `plant-master-data-check`, `provider-plugin-check`, `provider-surface-check` carry a blanket ban without categories.

## Requirements gate

No requirement artefact under `project/requirements/`. **Operator override** (2026-11-05): the issue's acceptance criteria plus the four answers below stand as the requirements.

Operator decisions (2026-11-05):

1. Scope: every recipe without the `-apply` suffix.
2. Marker: literal `Forbidden on Home Assistant:`; the paragraph it opens must contain `on or off`, `value`, `script`, `scene`, `automation`.
3. Blanket-ban recipes get the marker too; no exemption.
4. Requirements gate: override.

## Scope

- **In scope**: self-test cases, the guard in `tests/validate_recipes.py`, conforming all 27 non-`-apply` recipes, moving `TimeTillErnte` / `time_till` into `Forbidden by name:` in the two skills, recording the marker in `spec/goose/recipe-project-pattern/` (en+de) and pointing `spec/mcp/home-assistant-mcp-server/` (en+de) at it, updating the guard list in `CLAUDE.md`.
- **Out of scope**: classifying what `TimeTillErnte` / `time_till` actually do (open question in the HA spec, operator-owned); `-apply` recipes (spec rule is for read-only recipes; all four already say "Call NO Home Assistant tool at all"); the `worktree:add` failure in nolte/taskfiles (see Risks).

## Route

- **Decision**: direct
- **Rationale**: one outcome (the two HA MUSTs become machine-checked), one PR strand, no roadmap item.

## Work packages

### P1 — Self-test cases first

- **Problem statement**: the guard needs pinned shapes before it exists, as the issue's first AC requires and as the file's own convention (`WRITE_GUARD_CASES` comment) demands.
- **Acceptance criteria**: new cases in `RECIPE_CASES` (and a dedicated case table if the helper is separate) covering: marker absent → finding; marker present but a category missing → finding; full marker → no finding; `TimeTillErnte` outside `Forbidden by name:` → finding; both inside → no finding; one of the two absent from the block → finding; an `-apply` filename → no HA finding. Committed before P2; `python3 tests/validate_recipes.py --self-test` fails on this commit (cases without the check) — output recorded.
- **Touched files**: `tests/validate_recipes.py`
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: none

### P2 — The guard

- **Problem statement**: `check_recipe` must enforce, for every recipe whose stem does not end in `-apply`: the literal marker with the five category terms inside `prompt`, and both intent names inside a `Forbidden by name:` block and nowhere outside one. `check_skills` must refuse either intent name in a skill's instruction text outside a policy block.
- **Acceptance criteria**: self-test green; `task test` fails each of the nine recipes above on `develop`'s content (measured, output recorded) before P3.
- **Touched files**: `tests/validate_recipes.py`
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: P1

### P3 — Conform recipes and skills

- **Problem statement**: 27 recipes and 2 skills must pass the guard without changing what they do.
- **Acceptance criteria**: `task test` green; diff per recipe is limited to the HA constraint lines and the `Forbidden by name:` block; `goose recipe validate` passes where `goose` is on PATH; `weather-impact-check.yaml` keeps `GetLiveContext` as its only permitted HA call.
- **Touched files**: `recipes/*.yaml` (27, non-`-apply`), `.claude/skills/harvest-planning/SKILL.md`, `.claude/skills/weather-impact-analysis/SKILL.md`
- **Specialist**: `nolte-engineering:fullstack-developer` (`nolte-goose:recipe-implement` checked and rejected: it writes a recipe from a ready `project/recipes/<slug>/plan.md`, not a cross-recipe constraint edit)
- **Depends on**: P2

### P4 — Spec and orientation

- **Problem statement**: the marker is a new house convention; the spec layer must state it once and the guard list must name it.
- **Acceptance criteria**: `spec/goose/recipe-project-pattern/en.md` gains the `Forbidden on Home Assistant:` MUST and an acceptance-criteria line; `de.md` in sync; `spec/mcp/home-assistant-mcp-server/en.md:94,109` refers to the marker instead of restating it; `de.md` in sync; `CLAUDE.md` guard list names the HA check; `task docs` green.
- **Touched files**: `spec/goose/recipe-project-pattern/{en,de}.md`, `spec/mcp/home-assistant-mcp-server/{en,de}.md`, `CLAUDE.md`
- **Specialist**: `nolte-shared:spec` (skill)
- **Depends on**: P2 (the spec states what the guard checks)

## Dependency ordering

P1 → P2 → P3 ; P2 → P4. P3 and P4 are independent of each other.

## Class sweep (defect-class-guards)

- **G1**: the guard itself is the deliverable.
- **G3**: it enumerates the class (every non-`-apply` recipe, every skill instruction section), not the nine sites.
- **G6**: selector = recipe stem without `-apply`, which is exactly the spec's property; skills are included because they compose into the recipe's context.
- **G7**: asserts only the two HA MUSTs; no other wording is checked.

## Risks

- **Category terms are keywords, not structure.** A paragraph could contain the five words and still not forbid anything. Mitigation: the literal marker carries the meaning; the words only prove the categories are named. Recorded as a known limit in the spec.
- **27-file prompt edit.** Mitigation: diff reviewed by a context that didn't produce it; per-recipe diff limited to the HA lines.
- **No security-sensitive path** (no credential, auth or network code touched).
- **Tooling (out of scope):** `task worktree:add` from `nolte/taskfiles@develop` exits 1 silently for any non-`exp` branch: `for p in …; do [ … ] && ok=1; done` under `set -e` aborts in Task's shell interpreter when the last iteration is false. Reproduced with a three-line Taskfile in the scratchpad (`exit status 1`, `reached` never printed). This worktree was created by hand with the same path and base (`git worktree add -b fix/75-ha-actuation-guard ~/repos/.worktrees/kamerplanter-goose/ha-actuation-guard origin/develop`). Offered to the operator as an upstream issue.

## Open questions

- none blocking.

## Dispatch log

<!-- filled per package -->

## Member results

<!-- not a group member -->
