---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter-goose"
issue: "50"
classification: "feature-request"
secondary-classes: ["spec-change", "docs"]
route: "direct"
status: approved
created: "2026-11-05"
---

# Issue Orchestration — Pre-analysis

<!-- Run-scoped artifact: committed on feat/harvest-garden-review, then removed with a
     fix-forward `git rm` before the PR merges, per spec/project/issue-orchestration/
     §Pre-analysis artifact lifecycle. `.audits/` is gitignored here (.gitignore:13),
     so the commit needs `git add -f`, as on #49. -->

## Issue metadata

- **Repository**: nolte/kamerplanter-goose
- **Issue**: #50 — [P2] Add harvest planning and garden review workflows
- **URL**: https://github.com/nolte/kamerplanter-goose/issues/50
- **Labels**: enhancement, claude-code, skills
- **Author**: nolte (repository owner, trusted); 0 comments
- **Linked items**: the declared dependencies #4 (CLOSED, "analyse-queue.sh reports success on a failed queue read…"), #10 (MERGED, "give develop the branch protection its CI assumes") and #11 (CLOSED, "The Probot Settings app has never applied .github/settings.yml") are satisfied and, judging by their titles, unrelated to this feature (`gh issue view 4|10|11`). Effective dependencies: #49 (growth stage and weather, open PR #67 on `feat/growth-stage-weather-impact`, which this branch is stacked on @4a516ce); #42 and #43 (plant planning and care planning, merged as PR #60 and #65). In-flight siblings that this work must not depend on: #47 (crop rotation, branch `feat/crop-rotation-planning` @6af928d), #48 (plant health, branch `feat/plant-health-ipm`, which carries no commits of its own yet) and #55 (skill separation, commit 7ce172e).
- **Prior art checked**: no `project/` directory (no roadmap, features or requirement artifacts); `gh pr list` shows only #67; `.claude/skills/` and `recipes/` hold no harvest or review skill or recipe. Partial coverage, composed rather than duplicated: `plant-context-collect` (`allows_harvest`, `harvest_pattern`, `harvest_months`, cultivar `days_to_maturity`, care log, inspections), `plant-lifecycle-resolve` (harvest windows), `growth-stage-assessment` (`HAND-OFF: HARVEST PLANNING` block, `.claude/skills/growth-stage-assessment/SKILL.md:106-111`), `weather-impact-analysis` (exposures with impact area "harvest timing"), `pest-pressure-assess` (Karenz rule, `SKILL.md:79,95`), `garden-context`, `decision-policy`, `diary-measurements-read`, `plant-photo-read`.

## Decisions already made by the operator (recorded, not reopened)

- **D1 Requirements gate**: explicit operator override. No `project/requirements/` exists; the requirements are the issue's scope list and four acceptance criteria plus D2–D6.
- **D2 No live measurement**: the `kamerplanter` MCP server is unreachable in this session (`INVALID_CONFIG`). Every claim about tool output cites a spec in this repository and is marked "not re-measured".
- **D3 Autonomous**: open questions are resolved with recommended defaults, each marked "resolved by default, operator may overturn" (section "Planning decisions taken here").
- **D4 Read-only only**: the issue proposes no `-apply` recipe, and upstream lists the harvest write tools as specified but unimplemented (`spec/mcp/kamerplanter-mcp-server/en.md:28`). All four recipes are read-only, and each prompt carries a `Forbidden by name:` block naming all twelve state-changing tools (`spec/mcp/kamerplanter-mcp-server/en.md:177`).
- **D5 Skill convention from #55 (7ce172e)**: only content under a level-2 `## Gotchas` or `## Source` heading counts as explanation. Anywhere else, a state-changing tool name outside a `Forbidden by name:`/`Permitted by name:` block counts as a call. Both new skills must satisfy this, verified by overlaying 7ce172e (P12).
- **D6 #48 is not available here**: `garden-review` treats plant-health input as `not available (nolte/kamerplanter-goose#48)`, taking health evidence only from the recorded inspections and from existing `pest-pressure-assess` / `nutrient-imbalance-assess` results the caller supplies, exactly as `care-planning` handles unbuilt domains (`spec/process/care-planning-and-daily-check/en.md:54`).

## Planning decisions taken here (resolved by default, operator may overturn)

- **PD1 Two governing specs, not one.** `spec/process/harvest-readiness-and-planning/{en,de}.md` covers a per-plant judgement plus a cross-plant sequence. `spec/process/garden-and-season-review/{en,de}.md` covers a retrospective aggregation plus the reuse contract. Rationale: the two halves share no rule beyond what the decision policy already owns; one spec would mix a forward decision with a retrospective one. The harvest spec is the review spec's input, not the reverse.
- **PD2 One skill per spec, with two scopes each.** `harvest-planning` has scope `readiness` (one plant) and scope `plan` (several plants), following the issue's file list. `garden-review` has scope `garden` (up to the assessment date) and scope `season` (a bounded span). This mirrors `plant-planning` serving both `garden-plan` and `season-plan`. It confirms H4.
- **PD3 The readiness result is a closed set, decided only by an observation.** The result is exactly one of `ready`, `approaching`, `not ready`, `not harvestable` (species `allows_harvest: false`) and `insufficient evidence`. `ready`, `approaching` and `not ready` must rest on an observed maturity indicator at level 1–3: the person's own observation marked `caller`, a diary entry, an inspection, or a photo reading corroborated by a timing expectation. Timing priors are level 4 (the selected `growing_periods[]` entry's `harvest_months`, the growth-stage hand-off's `days_to_maturity` position, and the stage result and direction). The `get_harvest_readiness` response is reported as returned with no level. None of these may decide alone. This copies the #49 growth-stage pattern (`spec/process/growth-stage-and-weather-impact/en.md`, §B).
- **PD4 `days_to_maturity` is a position, never a date.** The hand-off's "days since `planted_on`: n of `days_to_maturity` m" is carried as a level 4 prior. The skill must say that neither what `days_to_maturity` counts from nor what `planted_on` denotes (sowing or transplanting) is recorded. It must not compute a harvest date from it, per `spec/process/plant-planning-and-planting-calendar/en.md:69`. The harvest window comes from `harvest_months` of the selected period only.
- **PD5 `get_harvest_readiness` is called and reported as returned.** Arguments and response fields are unrecorded. The skill calls it with the plant and the garden only, reports the response verbatim, assumes no field name, assigns no level, and on `validation.error` reports the error verbatim and continues. This is the same pattern as `get_plant_phase_history` in #49 and `list_diary_entries` in `diary-measurements-read`.
- **PD6 Intended use, weather, and the pre-harvest safety interval (Karenz).**
  - **Intended use** comes from the caller in the caller's words, marked `caller`. A use-specific indicator (for example for storage or seed saving) is stated only from the caller or as level 8 labelled "not from the record", and never decides alone.
  - **Weather** comes only from a caller `weather` parameter, through `weather-impact-analysis` with no Home Assistant read. Only exposures whose impact is "harvest timing" feed readiness, as a risk and never as a maturity indicator.
  - **The pre-harvest safety interval (Karenz)** applies when the caller supplies `treatments` as `treatment_key:YYYY-MM-DD`. The skill reads `get_treatment` → `safety_interval_days` (`spec/mcp/kamerplanter-mcp-server/en.md:114`) and reports a harvest gate `blocked until <date>` on top of the result. Without that input the gate is `unknown (no treatment date supplied)`. The catalog records no treatment-application history.
- **PD7 Harvest plan.** It plans for at most five named plants, the cap used by the daily check (`care-planning-and-daily-check/en.md:74`); the rest are listed as not planned. With `plants` empty it reports the garden's crops and planting runs (from `garden-context`) as context only and computes no window, naming the parameter.
  - **Sequencing** is a total order: window start month, then readiness (`ready` < `approaching` < `not ready` < `insufficient evidence`), then plant key.
  - **Workload** is counted as plants per month of window start and of `ready`/`approaching`. Hours or effort come only from a caller `capacity` value. "Over capacity" is stated only when capacity is given in the same unit as the counts.
  - **Storage and use constraints** are "not modeled in the measured catalog" (a search of `spec/` and `.claude/skills/` for "storage" finds no field), so they come from a caller `storage` text, marked `caller`, or are reported absent.
- **PD8 No Home Assistant in the harvest recipes.** Neither harvest recipe calls a Home Assistant tool. Both name `TimeTillErnte` and `time_till` in the prompt as forbidden: they are the most tempting wrong substitute ("Ernte"), and their effect is unclassified (`spec/mcp/home-assistant-mcp-server/en.md:81-82,96`). The review recipes call no Home Assistant tool either.
- **PD9 The review is tool-free over collected blocks.** The `garden-review` skill calls no tool (like `care-planning`). Its inputs are the garden context, up to five plant context blocks (care log and inspections included), the diary read reports, optional growth-stage hand-offs, optional harvest-planning results, and the caller's `yields`, `notes` and `weather`.
  - The review runs **no** current-state domain assessment. Pest and nutrient history comes from the inspections and from caller-supplied results; plant health (#48) is `not available`.
  - Watering and fertilisation outcomes are the care log's confirmations and snoozes. A link between care and result may be stated only as "consistent with" (decision-policy rule 1), never as a cause.
  - **Yield** comes from the caller as `plant_key:amount unit` entries, marked `caller` at level 3, with the open question #49 already carries on the weight of a caller statement. A diary `measurements` key is never read as yield, because the key set is unrecorded. This confirms H3.
  - **Cultivar performance** is grouped by `species_key:cultivar_key`, with fields side by side. There is no score and no average across units, and two cultivars are compared only on the same field in the same unit.
- **PD10 Season scope.** `season-review` requires `season` (a year `YYYY` or `YYYY-MM-DD..YYYY-MM-DD`).
  - The recipe additionally lists archived plants with `mcp__kamerplanter__list_plants` and `include_archived: true`. That parameter is used by `garden-context/SKILL.md:25` and by the #47 branch, but it is not recorded in `spec/mcp` (unestablished, not re-measured). A season review that only sees live plants hides the failures.
  - Diary coverage is what `diary-measurements-read` returns (at most eight entries, `SKILL.md:40`). The review states the newest and oldest opened date against the span, and says when the span is not covered. It does not page further.
- **PD11 Reuse is a structured output, not a write (H2).** Both scopes return a `HISTORY RECORD` block (one fixed-field record per plant, ordered by plant key, each field present with source, level and retrieval time, or absent with its reason) and a `NEXT CYCLE` block. The `NEXT CYCLE` block holds:
  - `crops` (`species_key[:cultivar_key]`, comma-separated: the `crop-selection`/`garden-plan` format, `recipes/garden-plan.yaml:15-21`), each marked keep / reconsider with its evidence;
  - `goals` and `constraints` as free text (`recipes/garden-plan.yaml:23-29,62-67`);
  - an observed `harvest_window` in the caller's month words;
  - location history lines `location_name:season:species_key[:cultivar_key]`, labelled "location, not bed". Where location names equal bed names, these are string-compatible with the in-flight #47 `bed history` format, but they are not a contract.

  No file is written, no diary entry is added (D4), and no consumer spec is amended, which avoids conflicts with #47, whose branch edits the site-analysis and plant-planning specs.
- **PD12 No daily-check integration.** `care-planning` reports only the domains named in its Non-Goals as not available, and harvest and review are not among them (`spec/process/care-planning-and-daily-check/en.md:54`), so no text there becomes false. Plugging harvest readiness into the daily check is out of scope.

## Classification

- **Primary class**: feature-request
- **Secondary class(es)**: spec-change, docs
- **Rationale**: two new skills and four new recipes under two new governing process specs, plus guides and index bookkeeping.
- **Asserted cause verified**: none asserted (feature, no defect claim).

## Established and unestablished claims

| # | Claim | Status | Evidence or settling observation |
|---|-------|--------|----------------------------------|
| C1 | `get_harvest_readiness` is a read tool in the catalog | established (recorded, not re-measured) | `spec/mcp/kamerplanter-mcp-server/en.md:101` |
| C2 | `get_harvest_readiness` was called read-only on 2026-08-16, and its arguments and response fields are recorded nowhere | established (absence by search) | `en.md:228`; `grep -rn get_harvest_readiness spec .claude recipes tests` finds only `en.md:101,228` |
| C3 | Harvest write tools are specified upstream but unimplemented, and none is in the twelve | established | `en.md:28`, `en.md:177`; `tests/validate_recipes.py` `STATE_CHANGING_TOOLS` |
| C4 | No harvest date may come from `days_to_maturity`; the harvest window is `harvest_months` of the selected period | established | `spec/process/plant-planning-and-planting-calendar/en.md:63-64,69` |
| C5 | #49 hands harvest planning: stage, result, direction, days in phase, `days_to_maturity` position, GDD with inputs, photoperiod | established (on this stacked branch, unmerged) | `.claude/skills/growth-stage-assessment/SKILL.md:106-111`; `spec/process/growth-stage-and-weather-impact/en.md` §F |
| C6 | No yield or harvest-amount field is recorded in the MCP specs | established (absence by search) | `grep -rni "yield" spec/mcp` → only false positives in `home-assistant-mcp-server/de.md` |
| C7 | No storage or shelf-life field is recorded | established (absence by search) | `grep -rni storage spec .claude/skills` finds no field |
| C8 | `get_treatment` carries `safety_interval_days` | established (recorded, not re-measured) | `en.md:114`; `pest-pressure-assess/SKILL.md:79,95` |
| C9 | No record of treatment application dates exists | unestablished | The care log records `reminder_type`/`confirmed_at` (`nutrient-imbalance-detection/en.md:52`); whether a treatment is a reminder type is unrecorded. Default PD6: caller supplies the date |
| C10 | `list_plants` accepts `include_archived` | established in skill usage, unestablished in the server spec | `.claude/skills/garden-context/SKILL.md:25`; absent from `spec/mcp` |
| C11 | Historical observations come from `get_plant_inspections`, `list_diary_entries`, `get_plant_care_log` | established | `spec/process/garden-decision-policy/en.md:89` |
| C12 | The planning recipes take `crops`, `goals`, `harvest_window`, `constraints` as caller strings | established | `recipes/garden-plan.yaml:15-38,62-67`; `recipes/crop-selection.yaml:20-41,65` |
| C13 | `TimeTillErnte`/`time_till` are unclassified and must not be called from a read-only recipe | established (measured 2026-08-04, not re-measured) | `spec/mcp/home-assistant-mcp-server/en.md:81-82,96,115` |
| C14 | This branch passes the #55 validator | established | Scratch overlay of 7ce172e's skills, `recipe-project-pattern/en.md` and `tests/validate_recipes.py` onto `git archive HEAD`, then `.venv/bin/python -I tests/validate_recipes.py` → "OK — 14 skill obedience cases hold … OK — 22 recipe(s) match the house pattern" |
| C15 | #55 and this branch overlap only in `CLAUDE.md`, in separate hunks | established | `git diff --name-only b6e5a55 7ce172e` vs `b6e5a55 HEAD`; hunks at CLAUDE.md lines 41/79 vs 52 |
| C16 | A season's diary is fully readable | unestablished | `diary-measurements-read` opens at most eight entries (`SKILL.md:40`), and the `list_diary_entries` signature is unmeasured; PD10 reports coverage instead |
| C17 | The #48 plant-health skill name | unestablished | `feat/plant-health-ipm` carries no commits of its own (`git diff --name-only develop...feat/plant-health-ipm` = the #49 files); name the issue, not a skill |

## Scope

- **In scope**: both specs (en/de); both skills; the four read-only recipes `harvest-readiness-check`, `harvest-plan`, `garden-review` and `season-review`; four guides in en/de; the guide and reference indexes; the `mkdocs.yml` nav; the skill lists in CLAUDE.md; `spec/README.md` regenerated; verification under the #55 convention.
- **Out of scope**:
  - every `-apply` recipe and apply contract (D4; upstream harvest writes are unimplemented);
  - persisting a review, whether to a file or as a diary entry;
  - plant health (#48, D6) and crop rotation (#47; no dependency, format compatibility only);
  - daily-check integration (PD12);
  - amending the site-analysis or plant-planning specs, or `garden-context`;
  - new validator checks (no new house rule; `STATE_CHANGING_TOOLS` unchanged);
  - live measurement (D2).

## Route

- **Decision**: direct (one PR strand on `feat/harvest-garden-review`, stacked on #49 / PR #67).
- **Rationale**: one goal outcome ("complete the lifecycle"), no roadmap item (no `project/`).
  - A split into two feature branches would by definition make the issue unbounded and force the pipeline route (`spec/project/issue-orchestration/en.md:315-319`).
  - Implementing only one half directly would be a forbidden partial implementation (`:320-322`).
  - Acceptance criterion 4 ("the lifecycle closes from planning through review") is only verifiable with both halves present.
  - The halves share CLAUDE.md, `mkdocs.yml`, both indexes and `spec/README.md`.
  - Expected size is about 32 files, about 1.3–1.5× PR #66 (25 files, +1470) and #49 (24 files, +1528): large but in the precedent's range.
  - Inside the strand, the harvest half (P1, P3–P5) lands before the review half (P2, P6–P8), so commits are reviewable in halves.
- **Split alternative (not recommended)**: only via an operator-created second issue.
  - **A, harvest**: P1, P3, P4, P5 plus its share of P9–P12, stacked on #49, "Closes" the narrowed #50.
  - **B, review**: P2, P6, P7, P8 plus its share of P9–P12, stacked on A, "Closes" the new issue.
  - Each half is bounded (one spec, one skill, two recipes). The cost is two passes over the bookkeeping files and an acceptance criterion 4 that #50 alone cannot meet.
- **Pipeline hand-off**: not applicable.

## Work packages

### P1 — Governing spec: harvest readiness and planning

- **Problem statement**: no spec fixes what a harvest-readiness judgement may rest on, its closed result set, or how a harvest plan sequences and counts work without a yield, storage or workload source.
- **Acceptance criteria**:
  - `spec/process/harvest-readiness-and-planning/en.md` and `de.md` exist with Status/Portfolio-Scope headers.
  - The spec encodes PD3–PD8.
  - The result set is closed (`ready | approaching | not ready | not harvestable | insufficient evidence`), and every result carries evidence, confidence, uncertainty and missing data per the decision policy.
  - Only a level 1–3 maturity observation decides.
  - `days_to_maturity` is a position, never a date (citing `plant-planning-and-planting-calendar/en.md:69`).
  - `get_harvest_readiness` is reported as returned, with no level and no assumed field.
  - Weather comes only from the caller; the pre-harvest safety interval (Karenz) gate goes through `get_treatment`.
  - Sequencing is a total order; workload is counts only, unless the caller supplies capacity; storage is "not modeled" unless the caller supplies it.
  - The spec names the five-plant cap, determinism on a fixed fixture, all twelve tools forbidden by name, and `TimeTillErnte`/`time_till` forbidden; no `-apply` sibling.
  - It cites the growth-stage spec §F as the input owner, not restating it.
  - Every tool-surface claim cites a spec and says "not re-measured".
  - en/de have the same headings, requirement-bullet counts and checkbox counts.
- **Touched files / artifacts**: `spec/process/harvest-readiness-and-planning/en.md`, `spec/process/harvest-readiness-and-planning/de.md`
- **Specialist**: `nolte-shared:spec` (create and translate); optional read-only check `nolte-shared:spec-readiness-reviewer`
- **Depends on**: none

### P2 — Governing spec: garden and season review

- **Problem statement**: no spec fixes how a retrospective is assembled from recorded history, what may be said about cultivar performance and care outcomes, or the shape in which a review feeds the next planning cycle.
- **Acceptance criteria**:
  - `spec/process/garden-and-season-review/{en,de}.md` exist and encode PD9–PD11 and D6.
  - The two scopes are `garden` and `season`, with the season span syntax and stop-on-invalid behaviour.
  - Fixed blocks: `REVIEW HEADER`, `HISTORY RECORD` (per plant, fixed fields, ordered by plant key), `CULTIVAR PERFORMANCE`, `LESSONS` (each a recommendation with four policy blocks, or an observation), `NEXT CYCLE` (strings in the exact formats of `recipes/garden-plan.yaml` `crops`/`goals`/`constraints`/`harvest_window`, plus location history lines labelled "location, not bed") and `DOMAIN STATUS` (plant health `not available (nolte/kamerplanter-goose#48)`).
  - Yield comes only from the caller, and a diary key is never read as yield.
  - There is no causal care→outcome claim, only "consistent with".
  - Diary coverage is stated against the span, and archived plants are read in season scope.
  - Five-plant cap, determinism, read-only, the skill is tool-free.
  - The spec cites the harvest spec (P1) for any harvest result it consumes, and states that #47 is not a dependency.
  - en/de parity as in P1.
- **Touched files / artifacts**: `spec/process/garden-and-season-review/en.md`, `spec/process/garden-and-season-review/de.md`
- **Specialist**: `nolte-shared:spec`; optional `nolte-shared:spec-readiness-reviewer`
- **Depends on**: P1

### P3 — Skill: harvest-planning

- **Problem statement**: the procedure that turns the plant context, the growth-stage hand-off, maturity observations, weather exposures and caller facts into a readiness result (scope `readiness`) or a sequenced plan over up to five plants (scope `plan`).
- **Acceptance criteria**:
  - `.claude/skills/harvest-planning/SKILL.md` exists, with frontmatter `name`/`description` and no `disable-model-invocation`.
  - Its own reads are only `get_harvest_readiness` (per plant, reported as returned) and `get_treatment` (when treatments are supplied).
  - It returns the readiness block, the plan block and findings in the `care-planning` §C shape.
  - A `Forbidden by name:` block lists all twelve tools, and the skill calls no Home Assistant tool.
  - Any state-changing name outside a policy block sits only under `## Gotchas`/`## Source` (D5).
  - Hard rules: no date from `days_to_maturity`; no result from a prior alone; no assumed `get_harvest_readiness` field.
  - `task test` passes, and the #55 overlay validator passes.
- **Touched files / artifacts**: `.claude/skills/harvest-planning/SKILL.md`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P1

### P4 — Recipe: harvest-readiness-check (read-only)

- **Problem statement**: an entry point for one plant's harvest readiness.
- **Acceptance criteria**:
  - `recipes/harvest-readiness-check.yaml` has parameters `plant_key` (required), `tenant`, `observations`, `entry_key`, `intended_use`, `weather`, `temperatures`, `treatments` and `as_of`.
  - Steps: `plant-context-collect` → `diary-measurements-read` → optional `plant-photo-read` → `growth-stage-assessment` → `weather-impact-analysis` (caller weather only, no Home Assistant read) → `decision-policy` → `harvest-planning` (readiness scope).
  - The `description` opens "Read-only:" and names the required working directory.
  - The prompt carries a `Forbidden by name:` block with the twelve tools plus `TimeTillErnte` and `time_till`.
  - A fixed step table, then the final line `HARVEST READINESS: <result> — <plant_key>` (or `not assessed`).
  - `goose recipe validate` and `task test` pass.
- **Touched files / artifacts**: `recipes/harvest-readiness-check.yaml`
- **Specialist**: no matching specialised agent — generalist remediation (`nolte-goose:recipe-implement` needs a `project/recipes/<slug>/plan.md` that does not exist)
- **Depends on**: P3

### P5 — Recipe: harvest-plan (read-only)

- **Problem statement**: an entry point for windows, sequencing, workload and storage constraints across up to five plants.
- **Acceptance criteria**:
  - `recipes/harvest-plan.yaml` has parameters `tenant`, `plants` (at most five, the rest not planned), `intended_use`, `storage`, `capacity`, `weather`, `treatments` and `as_of`.
  - Empty `plants` gives garden-level context only, with no window, and says which parameter would supply them.
  - It composes `garden-context`, then per plant the P4 chain, then `harvest-planning` (plan scope).
  - Policy block as in P4.
  - Final line `HARVEST PLAN: <n> planned, <m> not planned — <tenant>`.
  - `task test` passes.
- **Touched files / artifacts**: `recipes/harvest-plan.yaml`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P3

### P6 — Skill: garden-review

- **Problem statement**: a tool-free procedure assembling the history record, cultivar performance, lessons and the next-cycle block for scope `garden` or `season`.
- **Acceptance criteria**:
  - `.claude/skills/garden-review/SKILL.md` exists, works only on handed blocks, and returns the P2 blocks in order.
  - A missing input is absent with its reason, never filled.
  - Plant health is reported `not available (nolte/kamerplanter-goose#48)`.
  - `NEXT CYCLE` strings parse as the `garden-plan` parameter formats.
  - A `Forbidden by name:` block lists all twelve tools (the skill completeness check, if it references the server); no Home Assistant call; the D5 placement rule holds.
  - `task test` and the #55 overlay pass.
- **Touched files / artifacts**: `.claude/skills/garden-review/SKILL.md`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P2, P3 (the harvest-result shape it may consume)

### P7 — Recipe: garden-review (read-only)

- **Problem statement**: an entry point for an in-season review of a garden up to the assessment date.
- **Acceptance criteria**:
  - `recipes/garden-review.yaml` has parameters `tenant`, `plants` (at most five), `yields`, `notes`, `weather` and `as_of`.
  - Steps: `garden-context` → per plant `plant-context-collect`, `diary-measurements-read` and optionally `growth-stage-assessment` → `decision-policy` → `garden-review` (garden scope).
  - Policy block with the twelve tools; no Home Assistant tool.
  - Final line `GARDEN REVIEW: <n> reviewed, <m> not reviewed — <tenant>`.
  - `task test` passes.
- **Touched files / artifacts**: `recipes/garden-review.yaml`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P6

### P8 — Recipe: season-review (read-only)

- **Problem statement**: an entry point that closes the lifecycle, a season retrospective that feeds the next plan.
- **Acceptance criteria**:
  - `recipes/season-review.yaml` takes P7's parameters plus `season` (required). An invalid span stops the run and names the problem.
  - It adds a step listing plants with `include_archived: true`, reported `complete`, `partial: <reason>` or `failed: <error verbatim>`.
  - It hands off to `garden-review` in season scope.
  - The report shows the `NEXT CYCLE` block verbatim with a one-line pointer to `garden-plan`/`crop-selection`.
  - Final line `SEASON REVIEW: <season> — <n> reviewed, <m> not reviewed — <tenant>`.
  - `task test` passes.
- **Touched files / artifacts**: `recipes/season-review.yaml`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P6

### P9 — Guides for the four recipes

- **Problem statement**: plant owners need how-to guides, and the guide and reference indexes must list the new recipes and skills.
- **Acceptance criteria**:
  - Four pages per language, with frontmatter `title`, `audience`, `content_mode: how-to`, `track: user-docs` and `last_updated`, matching `docs/en/guides/growth-stage-check.md`.
  - The season-review guide shows the hand-over from the `NEXT CYCLE` block into `garden-plan` (acceptance criterion 4).
  - Rows are added to both indexes.
  - `mkdocs build --strict` passes after P10.
- **Touched files / artifacts**: `docs/{en,de}/guides/{harvest-readiness-check,harvest-plan,garden-review,season-review}.md`, `docs/{en,de}/guides/index.md`, `docs/{en,de}/references/index.md`
- **Specialist**: `nolte-shared:audience-doc-author` (`AUDIENCES.md` exists); generalist if the operator keeps the #65/#66 precedent
- **Depends on**: P4, P5, P7, P8

### P10 — Bookkeeping: CLAUDE.md and nav

- **Problem statement**: the architecture section and the docs nav must name the new skills and pages.
- **Acceptance criteria**:
  - CLAUDE.md line 52 lists `harvest-planning` and `garden-review` among the garden procedures, and `garden-review` among the tool-free exceptions.
  - `mkdocs.yml` nav carries the four pages.
  - `task docs` passes.
  - The CLAUDE.md edit touches only the line 52 hunk (C15).
- **Touched files / artifacts**: `CLAUDE.md`, `mkdocs.yml`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P9

### P11 — Regenerate the spec index

- **Problem statement**: `spec/README.md` is generated and must list both new specs.
- **Acceptance criteria**: `spec/README.md` is regenerated by the `spec` skill (not hand-edited) and lists both specs.
- **Touched files / artifacts**: `spec/README.md`
- **Specialist**: `nolte-shared:spec` (index mode)
- **Depends on**: P1, P2

### P12 — Verification

- **Problem statement**: the change must pass the repository gates and the #55 convention before the PR opens.
- **Acceptance criteria**:
  - `task check` is green (test, lint, docs).
  - `goose run --recipe <each new> --explain` lists the parameters without a model call.
  - The #55 overlay (the method of C14, rerun on the final tree) reports every case OK; alternatively a trial `git merge --no-commit 7ce172e` in a throwaway worktree is clean apart from the known CLAUDE.md hunks, and its validator passes.
  - `nolte-goose:recipe-audit` passes for the four recipes.
  - Optional: `domain-review` with persona `outdoor-gardener` on `recipes/season-review.yaml` (it reads only the checkout).
  - Gaps are recorded in the PR's Risk / rollout notes.
- **Touched files / artifacts**: none (reports only; any `domain-review` report goes into the gitignored `.audits/`)
- **Specialist**: `nolte-goose:recipe-audit`; `task check` run by the orchestrator
- **Depends on**: P1–P11

## Dependency ordering

P1 → P3 → {P4, P5}
P1 → P2 → P6 (also needs P3) → {P7, P8}
{P1, P2} → P11
{P4, P5, P7, P8} → P9 → P10
{all} → P12

Commit order inside the one strand: harvest half (P1, P3, P4, P5), then review half (P2, P6, P7, P8), then P9–P12.

## Risks

- **R1 `.audits/` is gitignored.** The artifact needs `git add -f`, plus a fix-forward `git rm` before merge. Mitigation: the same handling as #49.
- **R2 Stacked on unmerged #49 (PR #67).** A #49 review change to the hand-off block breaks P3. Mitigation: P3 consumes the block by its field names as they stand at `growth-stage-assessment/SKILL.md:106-111`; rebase after #67 merges and re-run P12.
- **R3 `get_harvest_readiness` signature unknown (C2).** Passing only plant and garden may be rejected. Mitigation: PD5 reports the error verbatim and continues; readiness never depends on this tool. Record in Gotchas: "treat the first live run as the measurement".
- **R4 Concurrent branches #47, #48 and #55 touch CLAUDE.md line 52, `mkdocs.yml` and both indexes.** Mitigation: the conflicts are mechanical list merges; whichever lands second rebases. With #55 there is no overlapping hunk (C15).
- **R5 Review coverage.** At most eight diary entries per plant may not cover a season (C16), and five plants may not cover a garden. Mitigation: both limits are stated in the output with what was not covered.
- **R6 Overclaiming from caller data.** Yield and observations are caller statements at level 3. Mitigation: they are marked `caller` everywhere, carried over the open question from #49, and never averaged across units.
- **R7 Tempting Home Assistant substitute.** `TimeTillErnte` ("time till harvest") looks like the answer. Mitigation: forbidden by name in all harvest prompts (PD8).
- **R8 PR size (~32 files).** Mitigation: commits split by half, as in the route section.
- **Security**: no security-sensitive path is touched (no credentials, no write path, no extension change), so `code-security-reviewer` is not required.

## Open questions

All resolved by default per D3. Each says "resolved by default, operator may overturn".

- **Q1 One PR strand or a split?** One strand, direct (Route). Resolved by default, operator may overturn by opening a second issue for the review half.
- **Q2 One or two harvest skills?** One, `harvest-planning`, with two scopes (PD2, as the issue proposes). Resolved by default, operator may overturn.
- **Q3 How does harvest readiness reconcile `days_to_maturity` with the growth stage?** As a level 4 position prior, never a date (PD4). Resolved by default, operator may overturn.
- **Q4 Where do yield, storage, workload and treatment dates come from?** From the caller only (PD6, PD7, PD9). Resolved by default, operator may overturn.
- **Q5 Should a review be persisted?** No; it is a structured output block only (PD11). A diary-entry `-apply` sibling would be a follow-up issue once D4 changes. Resolved by default, operator may overturn.
- **Q6 Should the harvest check join the daily check?** No (PD12). Resolved by default, operator may overturn.
- **Q7 What is the per-run plant cap?** Five, as in the daily check (PD7, PD9). Resolved by default, operator may overturn.
- **Q8 Should season scope read archived plants?** Yes, through `include_archived: true`, recorded as unestablished in the server spec (PD10, C10). Resolved by default, operator may overturn.

## Approval

- Pre-analysis approved 2026-11-05 under the operator's delegation ("arbeite die autonom ab"); one PR strand, route `direct`; PD1–PD12 and Q1–Q8 accepted as resolved by default.
- Base fast-forwarded to feat/growth-stage-weather-impact @f88ac8e (PR #67). #55 is PR #69 at 21bd577 (guard final 4a64a00): P12 uses a trial merge with 21bd577 instead of the overlay.
- D6 interplay: #48 is implemented concurrently on feat/plant-health-ipm. This branch keeps plant health `not available (nolte/kamerplanter-goose#48)`; whichever of #48/#50 merges second updates `garden-review` to consume the health finding.

## Dispatch log

<!-- Appended during operation 5; one line per package once its specialist reports. -->
- 2026-11-05 P1 — done (generalist, spec format followed; `nolte-shared:spec` loaded for the index rule): `spec/process/harvest-readiness-and-planning/{en,de}.md`, 9 requirement sections, 15 checkboxes, en/de heading/bullet/checkbox counts equal. Refinement: `not harvestable` sorts last in the plan order, and a plant with an unknown window sorts after every known one (PD7 named neither). Commit fb270de.
- 2026-11-05 P3 — done (generalist): `.claude/skills/harvest-planning/SKILL.md`; reads only `get_harvest_readiness` and `get_treatment`; no state-changing name outside its `Forbidden by name:` block; `TimeTillErnte` explanation under `## Gotchas`. Commit fb270de.
- 2026-11-05 P4 — done (generalist): `recipes/harvest-readiness-check.yaml`; the weather step runs only when `weather` is given (SKIP otherwise). Final line carries the gate: `HARVEST READINESS: <result> (gate: <gate>) — <plant_key>`. Commit fb270de.
- 2026-11-05 P5 — done (generalist): `recipes/harvest-plan.yaml`; adds an `observations` parameter (`plant_key: words`, semicolon-separated) beyond the planned list, since without it every plant would be `insufficient evidence`; `treatments` takes `plant_key:treatment_key:YYYY-MM-DD`. Commit fb270de.
- 2026-11-05 P2 — done (generalist): `spec/process/garden-and-season-review/{en,de}.md`, 8 requirement sections, 16 checkboxes, parity equal. Refinements: crops are marked `keep | reconsider | no evidence` (PD11 named two values); C10 evidence widened — `include_archived` is also used by `recipes/plant-master-data-check.yaml`.
- 2026-11-05 P6 — done (generalist): `.claude/skills/garden-review/SKILL.md`, tool-free, carries the twelve under `Forbidden by name:` (it therefore references the server and passes the completeness check).
- 2026-11-05 P7 — done (generalist): `recipes/garden-review.yaml`; growth-stage step runs per plant with no caller facts beyond `as_of`.
- 2026-11-05 P8 — done (generalist): `recipes/season-review.yaml`; the season is validated in step 1 before any read; with `plants` empty it lists the season's plants (archived marked) and reviews none.
- 2026-11-05 P9 — done (generalist, #65/#66 precedent kept): four guides per language, both indexes; the season-review guide shows the NEXT CYCLE → `garden-plan` hand-over.
- 2026-11-05 P10 — done: CLAUDE.md garden-procedures hunk only (both skills, `garden-review` among the tool-free exceptions); `mkdocs.yml` nav and `nav_translations`.
- 2026-11-05 P11 — done: `spec/README.md` regenerated per `nolte-shared:spec` operation 4 (dates from `git log -1 --format=%cs`).
- 2026-11-05 P12 — gate green: validator self-test and run, `mkdocs build --strict`, `goose recipe validate` and `--explain` for the four recipes, `pre-commit run --all-files`, trial merge with 21bd577 and its validator. `recipe-audit` not run (per instruction); `domain-review` not run.
- 2026-11-05 review fix (independent review of f88ac8e..1d3f3f9; recipe-audit ×4 clean): 13 findings applied in one commit — Karenz aggregate `blocked` > `unknown` > `clear` with an unreadable interval never `clear`; undated observation → month-window position and gate `not computed (observation undated)`; accumulated GDD as a `no level` prior with `GDD target for maturity: no source`; `harvest_results` caller parameter on both review recipes (no harvest-planning chaining); lessons numbered by plant key, field, kind; `reconsider` over `keep`, `keep` needs a caller-reported success; archived plants always listed in season scope; five-plant cap by plant key as text; window start by calendar month stated; unreadable plants `not planned (<error>)` counted in `<m>`; `get_harvest_readiness` called when present, absence reported; photo+prior confidence wording; guide example and `constraints`/separator rules. Specs en/de parity rechecked.
