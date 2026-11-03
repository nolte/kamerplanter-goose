---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter-goose
issue: "43"
classification: feature-request
secondary-classes: []
route: direct
status: draft
created: "2026-11-03"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter-goose
- **Issue**: #43 — [P0] Add care planning and daily garden check workflows
- **URL**: https://github.com/nolte/kamerplanter-goose/issues/43
- **Labels**: enhancement, claude-code, skills
- **Linked items**: none. `gh issue view 43 --json closedByPullRequestsReferences` → 0 PRs; 0 comments; no milestone. Handed over by `issue-backlog-partition` run 2026-11-02 (`.audits/issue-backlog-partition/2026-11-02.md`); the record was re-checked against the live issue, not re-derived.
- **Prior art checked**: no `care-planning` or `daily-garden-check` in `.claude/skills/`, `recipes/`, `spec/` on `develop` (a77c1a5). Patterns to follow: `garden-context` (gathering), `decision-policy` (evidence), `plant-planning` + `recipes/garden-plan.yaml` + `spec/process/plant-planning-and-planting-calendar/` (tool-free composition skill, read-only recipe, spec shape), merged in #57, #58, #60. The body's "Depends on issues #2 and #4" uses a retired numbering (#2 is a merged migration PR, #4 a closed bug); mapped by skill name to `garden-context` and `decision-policy`, both on `develop`.

## Classification

- **Primary class**: feature-request
- **Secondary class(es)**: none
- **Rationale**: adds one new capability (a care-planning layer and a daily orchestration recipe) to the catalogue; nothing is broken.
- **Asserted cause verified**: none asserted.

## Scope

- **In scope**: skill `care-planning`; recipe `daily-garden-check` (read-only); spec `spec/process/care-planning-and-daily-check/{en,de}.md`; guide `daily-garden-check` en + de; nav, guides index, references index, `CLAUDE.md` garden-procedures bullet, regenerated `spec/README.md`.
- **Out of scope**: the domain skills the layer plugs into (`watering-decision` #44, `fertilization-decision` #45, `plant-health-assessment`/`pest-ipm-planning` #48, `growth-stage-assessment`/`weather-impact-analysis` #49): each is its own issue. Any `-apply` recipe: the daily check only recommends, "no mutation occurs without explicit apply steps" is met by shipping none. Live measurement against a Kamerplanter server (unreachable, `INVALID_CONFIG`): the guide says it was not run live, as `garden-plan` does.

## Route

- **Decision**: direct
- **Rationale**: one coherent outcome (the care layer and its entry recipe), one PR strand, no new roadmap item. Confirmed by the operator at gate 1 (2026-11-03). **Requirements gate:** no requirement artefact exists (`project/requirements/` absent); the operator recorded an explicit override at gate 1 (the issue body states goal, scope and acceptance criteria), as for #40–#42.

## Design decisions (operator-confirmed unless marked)

1. **Skill shape.** `care-planning` makes no tool call; it is a function of the blocks it is handed (garden-context block, optional per-plant domain findings), like `plant-planning`. Determinism and refusal rules are testable on a fixed fixture.
2. **Three kinds of output, never blurred.** Every item is an *observation* (what was read), a *recommendation* (a proposal to a person, with evidence, confidence, uncertainty, missing data per `decision-policy`), or a *mutation* (a named state-changing tool that a later apply step would call; this layer never calls and never schedules one).
3. **Plug-in contract.** A domain plugs in by returning findings in one shape: domain, subject (plant key or garden), kind (observation or recommendation), what it says, evidence entries with level and source, confidence, what would change it, missing data. Plug-ins that exist today: `nutrient-imbalance-assess`, `pest-pressure-assess`. Plug-ins named in other issues are reported as not available, naming the skill, never substituted (house convention). The contract is deliberately minimal; the future domain skills may extend it (Open question 1).
4. **Prioritisation.** Items are ordered by urgency, then confidence, then key. Urgency is derived only from recorded fields (a due task past its own recorded interval, a finding that states advancing harm), never from general knowledge. An item without evidence for a present state is not generated; it appears under "no action, evidence insufficient" with the missing observation (this is the rule `decision-policy` already states for watering reminders).
5. **Daily check.** Operator decision: parameter `plants` (comma-separated plant keys, default empty). Empty: garden level only (due tasks, planting runs from `garden-context`). Given: nutrient and pest checks for those keys, at most 5, the rest reported as not checked. Unavailable domains reported as explicit step results.

## Work packages

### P1 — Spec, English

- **Problem statement**: the layer has no governing document; the rules in design decisions 1–5 must exist in `spec/` before the skill or recipe cite them.
- **Acceptance criteria**: `spec/process/care-planning-and-daily-check/en.md` exists with Context, Goals, Non-Goals, Requirements (inputs; observation/recommendation/mutation; plug-in contract; prioritisation; insufficient evidence; daily-check orchestration; determinism; separation), Acceptance Criteria, Source, Open Questions; follows the heading shape of `plant-planning-and-planting-calendar/en.md`; `grep -c "MUST" ` non-zero; no rule restated that `decision-policy` or `garden-decision-policy` already owns (cites them).
- **Touched files / artifacts**: `spec/process/care-planning-and-daily-check/en.md`
- **Specialist**: `nolte-shared:spec` (skill) — resolved by runtime lookup at dispatch
- **Depends on**: none

### P2 — Spec, German

- **Problem statement**: `de.md` is the kept-in-sync translation.
- **Acceptance criteria**: `de.md` has the same section structure and the same number of MUST/MUST NOT lines as `en.md`; checked by comparing `grep -c "MUSS"` with the English count.
- **Touched files / artifacts**: `spec/process/care-planning-and-daily-check/de.md`
- **Specialist**: `nolte-shared:spec`
- **Depends on**: P1

### P3 — Skill `care-planning`

- **Problem statement**: the reusable procedure that turns a garden block and domain findings into a prioritised, evidence-backed action list.
- **Acceptance criteria**: `.claude/skills/care-planning/SKILL.md` with frontmatter (`name`, `description` ≤ the length of its siblings, no `disable-model-invocation`), Input / Procedure / Hard rules / Source sections; makes no tool call and does not contain the string `mcp__kamerplanter__` (so the skill completeness check does not select it) — OR, if it names a tool, names all twelve; cites `spec/process/care-planning-and-daily-check/en.md`; `python tests/validate_recipes.py` → OK.
- **Touched files / artifacts**: `.claude/skills/care-planning/SKILL.md`
- **Specialist**: no matching specialised agent for project-local garden skills found yet; candidates from the lookup: `nolte-goose:recipe-implement` (recipes), `nolte-claude-dev:skill-management` (plugin skills). Resolved at dispatch; fallback: generalist with `plant-planning` as the pattern.
- **Depends on**: P1

### P4 — Recipe `daily-garden-check`

- **Problem statement**: the orchestration entry point; consumes `garden-context`, then per named plant `nutrient-imbalance-assess` and `pest-pressure-assess`, then `decision-policy` and `care-planning`.
- **Acceptance criteria**: `recipes/daily-garden-check.yaml` has `description` naming "Read-only", the required working directory, parameters `tenant` and `plants`; prompt states "Forbidden by name:" with all twelve state-changing tools and no Home Assistant call; numbered steps; fixed report with a PASS/FAIL-style status table and a machine-readable last line; the `plants` cap of 5 stated; absent domains listed as step results. `python tests/validate_recipes.py` → all recipes match the house pattern; `goose recipe validate recipes/daily-garden-check.yaml` → valid (if `goose` is installed; otherwise recorded as not run).
- **Touched files / artifacts**: `recipes/daily-garden-check.yaml`
- **Specialist**: `nolte-goose:recipe-implement` (skill); verification with `nolte-goose:recipe-audit`
- **Depends on**: P3

### P5 — Guide and navigation

- **Problem statement**: users and recipe authors need a page; the nav and both indexes must list it.
- **Acceptance criteria**: `docs/{en,de}/guides/daily-garden-check.md` with the frontmatter the sibling guides carry, a "Not yet run against a live instance" note, and parity between languages; `mkdocs.yml` nav entry; rows in `docs/{en,de}/guides/index.md` and `docs/{en,de}/references/index.md`; `mkdocs build --strict` rc=0.
- **Touched files / artifacts**: `docs/{en,de}/guides/daily-garden-check.md`, `mkdocs.yml`, `docs/{en,de}/guides/index.md`, `docs/{en,de}/references/index.md`
- **Specialist**: `nolte-shared:audience-doc-author` (agent) — needs an audience artifact first; none is committed in this repo, so the fallback is the generalist with `garden-plan.md` as the pattern, recorded as such
- **Depends on**: P4

### P6 — Catalogue bookkeeping

- **Problem statement**: `CLAUDE.md` lists the garden procedures by name; `spec/README.md` is generated.
- **Acceptance criteria**: `CLAUDE.md` garden-procedures bullet names `care-planning` with the tool-free exception, and the recipe count claim, if any, still matches `ls recipes | wc -l`; `spec/README.md` regenerated with the `spec` skill (not hand-edited) and carries one new `process` row; `task test`-equivalent green.
- **Touched files / artifacts**: `CLAUDE.md`, `spec/README.md`
- **Specialist**: `nolte-shared:spec` (index regeneration); `CLAUDE.md` edit by the generalist
- **Depends on**: P1, P2

### P7 — Verification (not a dispatch)

- **Acceptance criteria**: `python tests/validate_recipes.py` rc=0 with output; `mkdocs build --strict` rc=0; `nolte-goose:recipe-audit` run on `recipes/daily-garden-check.yaml` with its verdict recorded; independent code review run **from the worktree** with `git diff --stat origin/develop...HEAD` captured first; corpus grep for the new names to catch the places that list recipes or skills.

## Dependency ordering

P1 → P2 ; P1 → P3 → P4 → P5 ; (P1, P2) → P6 ; P7 last. P2 and P3 may run in parallel after P1.

## Risks

- **Plug-in contract guesses the future.** #44, #45, #48, #49 will plug in; a contract that is too narrow forces a spec change then. Mitigation: keep the contract minimal, list it as Open question 1, and have the spec state it as extendable by those issues, not frozen.
- **Not measured live.** The `kamerplanter` MCP server is unreachable (`INVALID_CONFIG`); the recipe's step sequence rests on tool names from `spec/mcp/kamerplanter-mcp-server/en.md`. Mitigation: the guide's "Not yet run against a live instance" note, as in `garden-plan.md`.
- **Merge collisions.** `CLAUDE.md`, `mkdocs.yml`, the two indexes and `spec/README.md` are touched by every feature PR (#57, #58, #60). Mitigation: merge serially, rebase before merge; this is the first feature single, so no sibling is open.
- **Skill completeness check.** `tests/validate_recipes.py` selects skills on the string `mcp__kamerplanter__`; a skill that mentions one tool must name all twelve. Mitigation: `care-planning` makes no tool call and avoids the string; P3's check is the validator run.
- **Prompt cost of per-plant checks.** Capped at five plants by the recipe; stated in the spec so the cap is a requirement, not an implementation detail.
- **Review agents move the primary checkout.** Observed in #64: `code-review` left the primary checkout detached at `FETCH_HEAD`. Mitigation: run reviews from the worktree and check `git status -sb` in the primary checkout afterwards.

## Open questions

1. Whether the plug-in contract needs an explicit `urgency_basis` field from the domain skills or whether urgency stays derived inside `care-planning`. Decided provisionally: derived inside, from recorded fields only; revisit when #44 lands.
2. Whether the spec directory should be named for both parts (`care-planning-and-daily-check`) or only the layer (`care-planning`). Provisionally both, matching `plant-planning-and-planting-calendar`.

## Dispatch log

2026-11-03 P1+P2 dispatched to nolte-shared:spec — `spec/process/care-planning-and-daily-check/{en,de}.md` written; en/de parity: 16 headings each at identical levels, 31 requirement bullets each, 17 acceptance checkboxes each, all relative links resolve. `spec/README.md` not regenerated (P6).
  - **Hypothesis refuted in part (recorded, first-class result):** (1) the existing plug-ins `nutrient-imbalance-assess` (`SKILL.md:64-67`) and `pest-pressure-assess` (`SKILL.md:83-88`) do NOT return findings in the contract shape; spec section C therefore requires the layer to map their reports into findings with levels from decision-policy's "How the existing ladders relate" table, assigning no level where the table gives none (nutrient tier 2, image symptoms). (2) "urgency from a due task past its own recorded interval" cannot be specified: no spec/docs/recipes file records the response fields of `get_due_care_tasks` (grep finds the tool name only); urgency is instead derived from an optional `consequence` field the domain itself states (`now`/`soon`), a due task is `routine` at most, an observation is `watch`. This adds one optional field (`consequence`) to the contract and one Open Question (due-task fields).
2026-11-03 P3 care-planning skill written (generalist: lookup found no specialist for a project-local garden skill; `recipe-implement` needs `project/recipes/<slug>/plan.md` in state ready, absent here). `python tests/validate_recipes.py` rc=0, skill contains no `mcp__kamerplanter__` string.
2026-11-03 **Deviation (structural, operator-decided):** writing P4 showed that the tier 1 diary read (`list_diary_entries`, at most eight `get_diary_entry`, no type filter) lives as ~25 lines in step 2 of `recipes/nutrient-imbalance-check.yaml`, not in `nutrient-imbalance-assess` (whose own text says "Somebody has to fetch those entries, and this skill does not", `SKILL.md:40`). The daily check needs it per plant, and spec F forbids duplicating domain logic in a recipe; recipes cannot call recipes (`sub_recipes` fails under this provider, CLAUDE.md). Operator chose to extract it. New package **P3b**: skill `diary-measurements-read` (moved unchanged in substance; names all twelve forbidden tools as the completeness check requires); `recipes/nutrient-imbalance-check.yaml` step 2 now loads it ("Three skills"); `nutrient-imbalance-assess/SKILL.md:40` points at it. Existing recipe behaviour unchanged by intent, re-audit required (P7).
2026-11-03 P4 `recipes/daily-garden-check.yaml` written (generalist, same reason). Checks: `python tests/validate_recipes.py` → "OK — 16 recipe(s) match the house pattern", "OK — 9 completeness cases hold"; `goose recipe validate` on both changed recipes → "✓ recipe file is valid"; `goose run --recipe recipes/daily-garden-check.yaml --explain` lists parameters `tenant` and `plants`.
2026-11-03 P5 guides `docs/{en,de}/guides/daily-garden-check.md`, nav entry + nav translation in `mkdocs.yml`, rows in `docs/{en,de}/guides/index.md` and `docs/{en,de}/references/index.md` (recipe row, plus skill rows for `care-planning` and `diary-measurements-read`). `mkdocs build --strict` rc=0, both language pages built. Corpus grep after the nutrient recipe change found two stale statements that the nutrient guides list only two loaded skills; fixed in `docs/{en,de}/guides/nutrient-imbalance-check.md`.
2026-11-03 P6 `CLAUDE.md` garden-procedures bullet names `diary-measurements-read` and `care-planning` (tool-free exception extended); `spec/README.md` one new `process` row, inserted alphabetically following operation 4 of the `spec` skill (Last updated from `git log -1 --format=%cs` of the canonical file: 2026-11-03).
