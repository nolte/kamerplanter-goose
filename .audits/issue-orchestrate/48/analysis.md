---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter-goose"
issue: "48"
classification: "feature-request"
secondary-classes: ["spec-change", "docs"]
route: "direct"
status: approved
created: "2026-11-05"
---

# Issue Orchestration — Pre-analysis

<!-- Run-scoped artifact: committed on feat/plant-health-ipm with `git add -f` (`.audits/` is
     gitignored, .gitignore:13), then removed with a fix-forward `git rm` before the PR merges, per
     spec/project/issue-orchestration/ §Pre-analysis artifact lifecycle. The branch is stacked on
     feat/growth-stage-weather-impact @4a516ce and inherits .audits/issue-orchestrate/49/analysis.md;
     that file belongs to the #49 run and is not touched by this run (Risk R2). -->

## Issue metadata

- **Repository**: nolte/kamerplanter-goose
- **Issue**: #48 — [P1] Add plant health assessment and IPM planning
- **URL**: https://github.com/nolte/kamerplanter-goose/issues/48
- **Labels**: enhancement, claude-code, skills
- **Author**: nolte (repository owner, trusted); 0 comments (`gh issue view 48 --json ...`)
- **Linked items**: declared dependencies #2 (MERGED, plant-domain knowledge migration) and #5 (CLOSED, unrelated by title); both satisfied (`gh issue view 2|5`). Upstream inputs from #49 (unmerged branch feat/growth-stage-weather-impact @4a516ce, no PR open yet): `growth-stage-assessment`, `weather-impact-analysis`, their spec, and the plug-in of both into care planning. Concurrent convention from #55 (OPEN; commit 7ce172e on fix/skill-instruction-separation). Sibling consumer #50 (OPEN, harvest) is not touched. Precedents: PR #65 (#43), PR #66 (#44, #45), the #49 branch.
- **Prior art checked**: no `project/` directory (`ls project` fails), so no roadmap, feature or requirement artifact; `gh pr list` → `[]`; `.claude/skills/` and `recipes/` hold no health-assessment or IPM-planning skill or recipe. Partial coverage, composed rather than duplicated: `nutrient-imbalance-assess`, `pest-pressure-assess` (identification, falsification tests, beneficial check, safety interval, rotation), `plant-photo-read`, `plant-context-collect` (care log, inspections), `diary-measurements-read`, `growth-stage-assessment`, `weather-impact-analysis`, `decision-policy`, `care-planning`.

## Decisions already made by the operator (recorded, not reopened)

- **D1 Requirements gate**: explicit operator override. There is no `project/requirements/`; the requirements are the issue's scope list, the five acceptance criteria, and D2 to D5. Same override as #40 to #45 and #49.
- **D2 No live measurement**: the `kamerplanter` MCP server is unreachable in this session (`INVALID_CONFIG`). Every claim about tool output rests on the measurements recorded in `spec/` and MUST be marked "not re-measured".
- **D3 Autonomous run**: open questions are resolved with a recommended default, marked "resolved by default, operator may overturn".
- **D4 Read-only only**: the issue asks for no `-apply` recipe. IPM write-back (`create_inspection`, or any treatment record) is out of scope. Refinement (see C9): `spec/mcp/kamerplanter-mcp-server/en.md:28` lists "IPM and harvest write tools" as specified-but-unimplemented, but the same spec records `create_inspection` as measured and implemented (`:84`, `:142`). No treatment-application write tool appears in the measured catalog (`:132-148`).
- **D5 Skill instruction/explanation convention (#55, 7ce172e)**: in a SKILL.md only content under a level-2 `## Gotchas` or `## Source` heading counts as explanation. Anywhere else, a state-changing tool name outside a `Forbidden by name:` or `Permitted by name:` block counts as a call. The new and edited skills must pass this: output templates carry no literal state-changing tool name, and explanations that name one go under `## Gotchas`. This is verified by a trial merge with 7ce172e (P11).

## Planning decisions taken here (resolved by default, operator may overturn)

- **PD1 One governing spec for both skills**: `spec/process/plant-health-and-ipm-planning/{en,de}.md`, the same shape as `growth-stage-and-weather-impact` and `watering-and-fertilization-decisions`. Rationale: IPM step 2 (environmental correction) consumes the health differential's environmental candidates, and both share the evidence intake. Two specs would restate it. Boundaries named in Context: `plant-health-image-analysis` owns the photo queue and submit cycle (a write cycle, `diary-photo-analysis-apply`). This spec owns the read-only synthesis. `pest-pressure-assessment` owns identification, its threshold and its treatment checks, and the new spec cites them without restating them. `garden-decision-policy` owns levels and rules.
- **PD2 plant-health-assessment composes; it reads nothing itself**: it is a tool-free skill, like `care-planning`. It takes, as returned:
  - the `plant-context-collect` block, which already holds the care log (watering and other confirmations), the inspections, the species and cultivar data and the phase;
  - `diary-measurements-read`;
  - `plant-photo-read` findings (only when the caller names a diary entry with photos);
  - the result and hand-off of `growth-stage-assessment`;
  - the `HAND-OFF: PLANT HEALTH` block of `weather-impact-analysis`;
  - the reports of `nutrient-imbalance-assess` and `pest-pressure-assess`;
  - optionally the findings of `watering-decision` and `fertilization-decision`.

  It never re-runs another skill's ladder, falsification test or refusal threshold. Where a process owns a question, its verdict stands (decision-policy step 5, `.claude/skills/decision-policy/SKILL.md:60-62`). The recipe, not the skill, orchestrates the sub-skills, because `sub_recipes:` does not work under this provider (`spec/goose/recipe-project-pattern/en.md:147`). This is AC4 ("existing diagnostic skills are reused").
- **PD3 A differential, never a diagnosis** (AC1, AC2, AC3):
  - The candidate classes are fixed: `nutrient`, `pest`, `disease`, `water`, `environment` (weather exposure), `development` (stage-normal change such as senescence), `abiotic handling/site`.
  - Each candidate carries exactly one status: `supported`, `suspicion`, `contradicted` or `not assessable`.
    - `supported`: the owning domain's own positive result plus at least one independent evidence item that is not the presenting symptom, with no higher-level contradiction.
    - `suspicion`: rests on a single symptom, a photo reading, priors, or a "consistent with" link only.
    - `contradicted`: a named item at a higher level contradicts it.
    - `not assessable`: the domain did not run or returned nothing, with the reason.
  - The overall result is exactly one of `leading explanation`, `competing explanations`, `suspicion only`, `no abnormality reported` and `insufficient evidence`.
  - Every result carries evidence entries (level, source, retrieved-at), confidence from the highest supporting decision-policy level, uncertainty, missing data, and, per pair of surviving candidates, the discriminating observation.
  - The health layer MUST NOT upgrade a domain's result: a pest `not contradicted` stays `not contradicted`, and an undetermined nutrient direction stays undetermined.
  - The word "diagnosis" is not used for any result.
- **PD4 Weather arrives only as #49 exposures**: weather enters only through the `weather-impact-analysis` hand-off. Exposures stay in their own block, and a symptom–exposure link reads only "consistent with" (a suspicion under decision-policy rule 1). The health recipe passes a caller `weather` parameter to `weather-impact-analysis`, and **Home Assistant reads are not permitted** in either new recipe. Rationale: this keeps the HA surface at zero, so the non-machine-checked HA bans (C17) need not be relied on, and matches the daily check §H.
- **PD5 pest-ipm-planning orders interventions, it does not identify**: it consumes the `pest-pressure-assess` report (candidate, tier, tests run and not run, beneficial check, treatment checks) and, when the caller has it, the health differential's `environment` and `water` candidates. Its own reads are limited to `get_pest` and `get_disease` (for the candidate keys the pest report names, to read `treatments[]`, `beneficials[]` and `environmental_triggers[]` verbatim), `get_treatment` and `search_glossary`. It orders steps in the issue's four stages:
  1. confirmation/monitoring;
  2. environmental correction;
  3. cultural/mechanical controls;
  4. targeted treatment, ordered internally biological before chemical (`pest-pressure-assessment/en.md:124`).

  Rules for the stages:
  - Stage 4 is reached only when the pest process's own threshold is met (tier 1, or tier 4 plus an uncontradicted tier 2, `:81`); below it the plan stops after stage 3 and names the monitoring method.
  - Monitoring methods and pest humidity ecology are tier 5 and labelled "not recorded" (`:59`, `:146`). An environmental correction for a disease cites `environmental_triggers` (tier 2, `:61`).
  - A `treatment_type` value that cannot be placed in a stage is reported as "stage not determinable from the record", because its value set is unrecorded (C11).
- **PD6 Safety constraints and prerequisites per treatment** (AC5): every stage-4 measure carries a fixed block:
  - **Prerequisites**:
    - (a) the identification meets the pest threshold (tier named);
    - (b) each earlier stage is done or unavailable, with the reason;
    - (c) the harvest situation: `allows_harvest`, and the time to harvest from a caller `harvest_date` or the growth-stage harvest hand-off (days since `planted_on` against `days_to_maturity`), never from `get_harvest_readiness` (fields unrecorded, C12).
  - **Safety constraints**, quoted verbatim from the record and never scaled, converted or invented: `safety_interval_days`, `protective_equipment[]`, `dosage_per_liter`, `application_method`, `active_ingredient`.
  - **Exclusions**:
    - The measure is excluded when the interval exceeds the remaining time (`:126`, `:149`).
    - When `allows_harvest` is true and the time to harvest is not established, the measure is "not recommendable: interval cannot be checked" and stays an observation.
    - Two measures sharing an `active_ingredient` are never offered as alternatives. A `null` ingredient means the rotation claim cannot be made (`:128`).
  - **Tier-5 / level-8 notes**:
    - The beneficial-versus-broad-spectrum conflict is stated as such, because contraindications are not recorded (`:130`).
    - Product label and local plant-protection rules are not in the record and are stated as a prerequisite outside it.
    - The enclosed-or-open setting is taken from the caller's `placement`, or stated as inferred.
- **PD7 Plug-in shape and kinds**: both skills return findings in care-planning §C shape.
  - **plant-health-assessment returns observations only**, one finding per plant (the differential). It cites the owning domains' findings by domain and never restates their recommendations, so the care plan counts nothing twice.
  - **pest-ipm-planning**:
    - A monitoring step for an existing candidate (from a symptom, a photo reading or an inspection) is a recommendation (urgency `routine`, no consequence unless an input states one).
    - Environmental and cultural steps are recommendations only when the candidate is at least `not contradicted` per the pest report. Otherwise they are observations.
    - A stage-4 treatment is a recommendation only when justified and every prerequisite holds.
    - No candidate means no IPM item ("no pest or disease candidate").
  - **Named mutations**, named and never called:
    - a monitoring step: the inspection-recording tool (`create_inspection`);
    - a treatment: `no tool measured`;
    - both are written in templates only as a placeholder pointing at `## Gotchas` (D5).
- **PD8 Daily check integration is in scope**: care-planning §C requires each Non-Goal domain to be reported `not available` "until that skill exists" (`care-planning-and-daily-check/en.md:54`). Shipping the skills without updating the care plan and the daily check would leave `:28`, `care-planning/SKILL.md:14`, `daily-garden-check.yaml:4,130-131,153` and both daily-check guides false. #49 and PR #66 did the same.
  - In the daily check, `plant-health-assessment` runs per checked plant after the weather step, on blocks already collected, with no new call. `pest-ipm-planning` runs after it, and its reads stay inside the five-plant cap.
  - Weather stays caller-only and no Home Assistant tool is called (§H).
  - The final line format is unchanged.
- **PD9 D5 conformity**: every new or edited SKILL.md that references `mcp__kamerplanter__` names all twelve state-changing tools in one `Forbidden by name:` block (C15). No state-changing name appears in instruction text outside that block. Output templates use placeholders, and the sentences naming `create_inspection` as the mutation go under `## Gotchas`.
- **PD10 Recipe names as the issue proposes**: `recipes/plant-health-assessment.yaml` and `recipes/pest-ipm-plan.yaml`, although sibling read-only recipes end in `-check`. The issue author is the trusted owner, and no validator rule requires `-check`.

## Classification

- **Primary class**: feature-request
- **Secondary class(es)**: spec-change, docs
- **Rationale**: two new skills and two new read-only recipes with a new governing process spec. The care-planning spec, the daily check and their guides are amended to plug them in.
- **Asserted cause verified**: none asserted (feature, no defect claim).

## Established and unestablished claims

| # | Claim | Status | Evidence or settling observation |
|---|-------|--------|----------------------------------|
| C1 | "Never diagnose from a single symptom" is already decision-policy rule 1, and "correct an environmental cause before treating" is rule 5 | established | `.claude/skills/decision-policy/SKILL.md:49,53` |
| C2 | Reuse must be by skill, not by recipe: `sub_recipes:`/`--sub-recipe` do not work under claude-code | established | `spec/goose/recipe-project-pattern/en.md:145-149`; CLAUDE.md "Constraints" |
| C3 | The pest record has no host range, humidity ecology or monitoring fields; contraindications between treatments are not recorded | established (recorded 2026-08-07, not re-measured) | `spec/process/pest-pressure-assessment/en.md:59,130`; `spec/mcp/kamerplanter-mcp-server/en.md:160` |
| C4 | A treatment is proposable only on pest tier 1, or tier 4 plus an uncontradicted tier 2 | established | `spec/process/pest-pressure-assessment/en.md:81`; `.claude/skills/pest-pressure-assess/SKILL.md:24` |
| C5 | The existing IPM ordering is cultural/physical → biological → chemical; an opening chemical must state why earlier tiers are unavailable | established | `pest-pressure-assessment/en.md:124,154` |
| C6 | `safety_interval_days` is checked against the harvest situation when `allows_harvest`; an exceeding interval excludes the measure | established | `pest-pressure-assessment/en.md:126,149`; `spec/mcp/kamerplanter-mcp-server/en.md:114` |
| C7 | Nested `treatments[]` carries `treatment_key`, `name`, `treatment_type`, `active_ingredient`, `application_method`, `safety_interval_days`, `dosage_per_liter`, `protective_equipment[]` | established (recorded on one pest, not re-measured) | `pest-pressure-assessment/en.md:56` |
| C8 | `get_disease` carries `environmental_triggers[]`, so disease environmental correction is tier 2 while pest correction is tier 5 | established (recorded, not re-measured) | `pest-pressure-assessment/en.md:61,114` |
| C9 | `create_inspection` exists in the measured catalog although `:28` lists IPM write tools as unimplemented; no treatment-application write tool exists | established (recorded 2026-08-16, not re-measured) | `spec/mcp/kamerplanter-mcp-server/en.md:28,84,142`; write tables `:132-148` |
| C10 | The care-planning spec and its consumers still list #48 as the one unbuilt domain | established | `spec/process/care-planning-and-daily-check/en.md:28,54`; `.claude/skills/care-planning/SKILL.md:14`; `recipes/daily-garden-check.yaml:4,130-131,153`; `docs/{en,de}/guides/daily-garden-check.md:50` |
| C11 | The value set of `treatment_type` is not recorded | established (absence) | `grep -rn treatment_type spec .claude` finds only field-name rows (`pest-pressure-assessment/en.md:56,124`, `pest-pressure-assess/SKILL.md:77`) |
| C12 | The response fields of `get_harvest_readiness`, and of `get_plant_inspections` on an inspected plant, are not recorded | established (absence) | `spec/mcp/kamerplanter-mcp-server/en.md:101` (name only); `pest-pressure-assessment/en.md:178` |
| C13 | Weather reaches health as the #49 hand-off: exposures, and separately symptoms with "consistent with" links | established (on the unmerged #49 branch) | `spec/process/growth-stage-and-weather-impact/en.md:77,85`; `.claude/skills/weather-impact-analysis/SKILL.md:95` |
| C14 | Growth-stage harvest hand-off gives days since `planted_on` against `days_to_maturity`, usable as time-to-harvest input | established (on #49 branch) | `.claude/skills/growth-stage-assessment/SKILL.md:106-111`; `growth-stage-and-weather-impact/en.md:84` |
| C15 | A skill that mentions `mcp__kamerplanter__` must name all twelve state-changing tools (machine-checked) | established | `tests/validate_recipes.py:42-55` (`STATE_CHANGING_TOOLS`), `skill_missing_tools` |
| C16 | The D5 guard passes on the #49 tree once 7ce172e's own four skill repairs are present; the only file both branches change is `CLAUDE.md` | established (simulated, not a real merge) | 7ce172e's `tests/validate_recipes.py` run over `git archive 4a516ce` in the scratchpad: 4 FAILs (pest-pressure-assess, plant-lifecycle-resolve, plant-photo-read, species-baseline-verify), all files 7ce172e repairs; with those four overlaid, "OK — 22 recipe(s)". `comm -12` of both `--name-only` diffs → `CLAUDE.md` |
| C17 | HA actuation bans and `TimeTillErnte`/`time_till` are not machine-checked | established | #49 artifact C14; `grep -n "TimeTillErnte" tests/validate_recipes.py` finds nothing |
| C18 | Baseline gate on 4a516ce is green | established | `python3 tests/validate_recipes.py` → "OK — 22 recipe(s) match the house pattern" |
| C19 | `recipe-implement` is unusable: needs `project/recipes/<slug>/plan.md` in state ready | established | `/home/nolte/repos/github/claude-goose/skills/recipe-implement/SKILL.md` description; `ls project` fails |
| C20 | `.audits/` is gitignored | established | `git check-ignore -v .audits/issue-orchestrate/48/analysis.md` → `.gitignore:13:/.audits/` |
| C21 | The surviving-candidate set a real plant yields, and whether the photo-checklist "uniform damage across plants → abiotic" cue is available per plant | unestablished | `.claude/skills/plant-photo-read/references/inspection-checklist.md:53` names the cue; settle with the first live run |
| C22 | Any statement about live tool output (field names, `treatment_type` values, a populated inspection) holds for this run | unestablished | `kamerplanter` `INVALID_CONFIG`; settle by the first real run of each recipe |

## Scope

- **In scope**:
  - New spec `spec/process/plant-health-and-ipm-planning/{en,de}.md`.
  - Skills `.claude/skills/plant-health-assessment/SKILL.md` and `.claude/skills/pest-ipm-planning/SKILL.md`.
  - Read-only recipes `recipes/plant-health-assessment.yaml` and `recipes/pest-ipm-plan.yaml`.
  - Plug-in integration: care-planning spec en/de, `care-planning` skill, `recipes/daily-garden-check.yaml` and its guides.
  - Guides `docs/{en,de}/guides/{plant-health-assessment,pest-ipm-plan}.md`.
  - Bookkeeping: `CLAUDE.md`, `mkdocs.yml`, `docs/{en,de}/guides/index.md`, `docs/{en,de}/references/index.md`, `spec/README.md` (regenerated).
- **Out of scope**:
  - Any `-apply` recipe, `create_inspection` call or treatment record (D4).
  - Edits to `pest-pressure-assess`, `nutrient-imbalance-assess`, `plant-photo-read`, `plant-context-collect`, the #49 skills, `decision-policy` or its level table.
  - Correcting the stale `spec/mcp/kamerplanter-mcp-server/en.md:28` Non-Goal (follow-up, Q7).
  - A treatment contraindication table, host-range data or a `treatment_type` stage map (no source).
  - A new validator rule.
  - The #55 change itself.
  - Harvest planning (#50).
  - Live measurement (D2).

## Route

- **Decision**: direct
- **Rationale**: one goal outcome and one PR strand on feat/plant-health-ipm. No `project/roadmap.md` exists to create or retarget an item. Shape and size match #49 and PR #66.
- **Pipeline hand-off**: n/a

## Work packages

### P1 — Governing spec: plant health assessment and IPM planning

- **Problem statement**: no spec fixes what a combined health assessment may rest on, how a differential is formed without diagnosing, how the IPM stages are ordered and gated, or what a treatment must carry.
- **Acceptance criteria**:
  - `en.md` has Status `draft`, Portfolio-Scope `local`, and sections Context, Goals, Non-Goals and Requirements. The Requirements sections are: A Inputs, B The differential, C Confidence and uncertainty, D IPM stages, E Treatment prerequisites and safety constraints, F Separation of exposure and symptom (by reference to #49 §E), G Plug-in shape and kinds, H Determinism, I Separation and forbidden tools. Then Acceptance Criteria, Source and Open Questions follow.
  - The requirements encode D2 to D5 and PD1 to PD9. They cite `pest-pressure-assessment` for the threshold, safety interval, rotation and beneficial rules without restating them, and cite `garden-decision-policy` for the levels and rule 1/5. Every tool-surface claim cites `spec/mcp/*` and says "not re-measured", and the Context names `INVALID_CONFIG`.
  - Each of the issue's five acceptance criteria maps to at least one requirement and one checkbox.
  - The closed result sets of PD3 and the four stages of PD5 are stated verbatim.
  - The spec states no evidence level of its own.
  - `de.md` has identical heading order and equal requirement-bullet and checkbox counts.
  - The Open Questions include: the `treatment_type` value set; populated `get_plant_inspections` fields; a contraindication source; legal/label constraints outside the record; whether the health result may ever be a recommendation; the stale `:28` Non-Goal.
- **Touched files / artifacts**: `spec/process/plant-health-and-ipm-planning/en.md`, `spec/process/plant-health-and-ipm-planning/de.md`
- **Specialist**: `nolte-shared:spec`; optional read-only check `nolte-shared:spec-readiness-reviewer`
- **Depends on**: none

### P2 — Plug plant health and IPM into the care-planning spec

- **Problem statement**: the care-planning spec lists #48 as the last unbuilt Non-Goal domain (C10).
- **Acceptance criteria**:
  - `spec/process/care-planning-and-daily-check/{en,de}.md` Non-Goals point to the new spec instead of listing #48 as unbuilt.
  - §C names both skills as domains returning findings in the plug-in shape, and states that the health differential is observation-only and cites, never duplicates, other domains' findings.
  - The "not available until that skill exists" rule stays general.
  - §F adds both checks to the per-plant list. §H is unchanged.
  - Source cites the new spec and the Context sentence on returned shapes includes the two.
  - en/de heading order and counts are identical.
  - `watering-and-fertilization-decisions/en.md:28` and `growth-stage-and-weather-impact/en.md:28` are left as is: they are those specs' own Non-Goals and remain true.
- **Touched files / artifacts**: `spec/process/care-planning-and-daily-check/en.md`, `spec/process/care-planning-and-daily-check/de.md`
- **Specialist**: `nolte-shared:spec`
- **Depends on**: P1

### P3 — Skill: plant-health-assessment

- **Problem statement**: no procedure combines observations, photos, growth stage, measurements, watering and fertilisation history, species data, the nutrient and pest reports and weather exposures into one differential with explicit uncertainty.
- **Acceptance criteria**:
  - Frontmatter `name` and `description`, no `disable-model-invocation`.
  - Inputs exactly as PD2; each absent input is reported `not collected` or `no source` with the reason.
  - Tool-free: names no read tool as its own call.
  - Applies PD3: the candidate classes, the four statuses and the five overall results. Never upgrades a domain result, and "diagnosis" is never used for a result.
  - Exposures and symptoms stay in separate blocks, linked only as "consistent with".
  - Evidence, confidence from the highest supporting level, uncertainty, missing data, and the discriminating observation per surviving pair.
  - One observation finding per plant in care-planning §C shape, citing other domains by name.
  - A hand-off block for `pest-ipm-planning` carries the `environment` and `water` candidates and the pest/disease candidate as the pest report returned it.
  - `## Gotchas` and `## Source` present.
  - Passes `task test`, and passes the 7ce172e guard in the P11 trial merge.
- **Touched files / artifacts**: `.claude/skills/plant-health-assessment/SKILL.md`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P1

### P4 — Skill: pest-ipm-planning

- **Problem statement**: a surviving pest or disease candidate is never turned into an ordered intervention plan with gated treatment and stated prerequisites.
- **Acceptance criteria**:
  - Frontmatter `name` and `description`.
  - Consumes the `pest-pressure-assess` report and, optionally, the P3 hand-off and the #49 growth-stage harvest hand-off. Never re-runs identification or the falsification tests.
  - Its own reads are only `get_pest`, `get_disease`, `get_treatment` and `search_glossary`, for keys the pest report names.
  - Four stages in issue order. Stage 4 only at the pest threshold (C4), internally biological before chemical. Below the threshold the plan names the monitoring method, labelled tier 5 "not recorded".
  - Environmental correction cites `environmental_triggers` for a disease and is labelled tier 5 for a pest.
  - Every stage-4 measure carries the PD6 prerequisites, safety-constraint and exclusion block, with values quoted verbatim, never scaled.
  - Unmappable `treatment_type` is reported as such.
  - Kinds per PD7; the mutation is named via placeholder, with `create_inspection` and `no tool measured` stated under `## Gotchas`.
  - One `Forbidden by name:` block with all twelve tools (C15), and no state-changing name elsewhere in instruction text.
  - Findings in care-planning §C shape; "no pest or disease candidate" is a valid empty result.
  - Passes `task test`, and passes the 7ce172e guard in P11.
- **Touched files / artifacts**: `.claude/skills/pest-ipm-planning/SKILL.md`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P1

### P5 — Recipe: plant-health-assessment (read-only)

- **Problem statement**: a person cannot ask for one evidence-combined health picture of a plant.
- **Acceptance criteria**:
  - No `extensions:` block. `description` opens `Read-only:`, names the working directory, and states that weather is caller-only and that no Home Assistant tool is called.
  - Parameters (proposed): `plant_key` (required), `tenant`, `observations`, `entry_key` (photos), `weather`, `placement`, `as_of`.
  - `prompt` has `Forbidden by name:` with all twelve tools, and bans every Home Assistant tool, actuation by category and `TimeTillErnte`/`time_till`.
  - Steps load, in order: `plant-context-collect`, `diary-measurements-read`, `plant-photo-read` (only with `entry_key`), `nutrient-imbalance-assess`, `pest-pressure-assess`, `growth-stage-assessment`, `weather-impact-analysis` (no HA read), `plant-health-assessment`, `decision-policy`.
  - A fixed report and a machine-readable final line (proposed `HEALTH: <overall result> — <plant_key>`). An absent tool is an explicit step result.
  - `goose recipe validate` valid, `goose run --recipe plant-health-assessment --explain` lists the parameters, `task test` passes.
- **Touched files / artifacts**: `recipes/plant-health-assessment.yaml`
- **Specialist**: no matching specialised agent — generalist remediation (`nolte-goose:recipe-implement` needs an absent `project/recipes/<slug>/plan.md`, C19)
- **Depends on**: P3

### P6 — Recipe: pest-ipm-plan (read-only)

- **Problem statement**: a person cannot ask for an IPM-ordered plan for a pest or disease suspicion with treatment safety stated.
- **Acceptance criteria**:
  - No `extensions:` block. `description` opens `Read-only:`, names the working directory, and states that nothing is applied or recorded.
  - Parameters (proposed): `plant_key` (required), `tenant`, `suspicion`, `placement` (enclosed or open), `harvest_date`, `as_of`.
  - `prompt` has `Forbidden by name:` with all twelve tools (with `create_inspection` among them), and bans every Home Assistant tool.
  - Steps load: `plant-context-collect`, `pest-pressure-assess`, `growth-stage-assessment` (harvest timing only), `pest-ipm-planning`, `decision-policy`.
  - A fixed report with stages 1 to 4 and a per-treatment safety block, plus a final line (proposed `IPM: <n> steps, treatment <justified|not justified|not applicable> — <plant_key>`).
  - `goose recipe validate` valid, `--explain` lists the parameters, `task test` passes.
- **Touched files / artifacts**: `recipes/pest-ipm-plan.yaml`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P4

### P7 — Integrate into care planning and the daily garden check

- **Problem statement**: the care plan and the daily check report plant health and pest management as `not available` (C10), which is false once P3 and P4 exist.
- **Acceptance criteria**:
  - `care-planning/SKILL.md` Input lists both domains, taken as returned. Step 1 states that the health finding is an observation and cites, never duplicates. The "domain not yet built" sentence is removed.
  - `daily-garden-check.yaml`:
    - adds both skills to the loaded-skill list;
    - adds items 9 (`plant-health-assessment`, on blocks already collected, no new call) and 10 (`pest-ipm-planning`, no `harvest_date`, no placement) per checked plant;
    - Step 4 gives the domain statuses `checked` / `not checked`;
    - the `description` no longer says the domain is unbuilt, and the domain list in the Step 7 report names the new domains;
    - no HA tool is called or named as callable, and the final line format is unchanged.
  - `task test` passes and `goose recipe validate` is valid.
  - The skill passes the 7ce172e guard (no literal state-changing name in instruction text).
- **Touched files / artifacts**: `.claude/skills/care-planning/SKILL.md`, `recipes/daily-garden-check.yaml`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P2, P3, P4

### P8 — Guides for both recipes and the daily-check update

- **Problem statement**: no guide exists for the new recipes, and the daily-check guide calls the domain not available.
- **Acceptance criteria**:
  - `docs/{en,de}/guides/plant-health-assessment.md` and `pest-ipm-plan.md` carry house frontmatter (`title`, `audience`, `content_mode: how-to`, `track`, `last_updated`).
  - Each has: a "not yet run against a live instance" note; the working-directory warning; a parameter table; a section on reading `competing explanations` / `suspicion only` and why treatment is usually `not justified`; and, in the IPM guide, the safety-interval and harvest-date prerequisite.
  - `daily-garden-check.md` en/de domain table row (line 50) is updated.
  - `task docs` passes.
- **Touched files / artifacts**: `docs/en/guides/plant-health-assessment.md`, `docs/de/guides/plant-health-assessment.md`, `docs/en/guides/pest-ipm-plan.md`, `docs/de/guides/pest-ipm-plan.md`, `docs/en/guides/daily-garden-check.md`, `docs/de/guides/daily-garden-check.md`
- **Specialist**: no matching specialised agent — generalist remediation (#49 Q4 precedent); `nolte-shared:audience-doc-author` available if the operator prefers (AUDIENCES.md exists)
- **Depends on**: P5, P6, P7

### P9 — Bookkeeping: CLAUDE.md, nav, indexes

- **Problem statement**: the new skills and recipes are not listed in the repository map, the nav or the reference indexes.
- **Acceptance criteria**:
  - `CLAUDE.md`: the garden-procedures bullet (line 52) lists both skills, and `plant-health-assessment` is added to the tool-free exceptions. The merge with #55's `CLAUDE.md` change is resolved by hand (C16).
  - `mkdocs.yml` has nav entries with German labels next to the #49 entries (around lines 166-167).
  - `docs/{en,de}/guides/index.md` and `docs/{en,de}/references/index.md` list both recipes (writes: no) and both skills.
  - `task docs` passes.
- **Touched files / artifacts**: `CLAUDE.md`, `mkdocs.yml`, `docs/en/guides/index.md`, `docs/de/guides/index.md`, `docs/en/references/index.md`, `docs/de/references/index.md`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P5, P6

### P10 — Regenerate spec/README.md

- **Problem statement**: `spec/README.md` is generated and does not list the new spec.
- **Acceptance criteria**: regenerated, not hand-edited. It lists `process/plant-health-and-ipm-planning` with its en/de titles, `draft` and `local`, and the care-planning row reflects P2.
- **Touched files / artifacts**: `spec/README.md`
- **Specialist**: `nolte-shared:spec` (index mode)
- **Depends on**: P1, P2

### P11 — Verification

- **Problem statement**: the bundle must pass the house gate, the recipe audit and the #55 convention before the PR.
- **Acceptance criteria**:
  - `task check` and `pre-commit run --all-files` are green.
  - `nolte-goose:recipe-audit` on `plant-health-assessment.yaml`, `pest-ipm-plan.yaml` and `daily-garden-check.yaml` at the final head exits 0 with 0 findings, digests recorded.
  - Trial merge with 7ce172e in a throwaway worktree (`git merge --no-commit --no-ff 7ce172e`, `CLAUDE.md` conflict resolved): `python3 tests/validate_recipes.py` reports 0 problems, including "skill obedience" for both new skills and the edited `care-planning`. The worktree is then discarded.
  - `grep` confirms no state-changing tool name in either new skill outside `Forbidden by name:` and `## Gotchas`.
  - An independent fresh-context read-only review finds no spec/skill/recipe contradiction, specifically no health result worded as a diagnosis and no treatment without its PD6 block. Findings are fixed or recorded.
  - The PR Testing section states that nothing ran live (`INVALID_CONFIG`).
- **Touched files / artifacts**: none (fixes route back to the owning package)
- **Specialist**: `nolte-goose:recipe-audit`; `task check` and the trial merge by the orchestrator
- **Depends on**: P5, P6, P7, P8, P9, P10

## Dependency ordering

P1 → {P2, P3, P4} (parallel) → {P5 after P3, P6 after P4, P10 after P1+P2} → P7 (after P2, P3, P4) → P9 (after P5, P6) → P8 (after P5, P6, P7) → P11 (after P5–P10).

## Risks

- **R1** `.audits/` is gitignored (C20). Mitigation: `git add -f`, then a fix-forward `git rm` before merge, as in #49 and PR #66.
- **R2** Stacked on the unmerged #49 branch, which carries its own `.audits/issue-orchestrate/49/analysis.md`. Mitigation: open the PR only after #49 merges, rebase onto `develop`, and never touch the #49 artifact (Q6).
- **R3** The #55 convention lands concurrently, and the guard is not on this branch. Mitigation: the P11 trial merge and the PD9 template rule. `CLAUDE.md` is the only overlapping file (C16).
- **R4** The health differential reads as a diagnosis, or double-counts nutrient and pest findings in the care plan. Mitigation: PD3 vocabulary, observation-only health findings that cite rather than restate (PD7), and the P11 review check.
- **R5** A treatment recommended with an unknowable safety interval. Mitigation: PD6 exclusion when time to harvest is unknown and `allows_harvest` is true, and values quoted verbatim.
- **R6** Tier-5 IPM content (monitoring methods, pest humidity ecology, contraindications) presented as recorded. Mitigation: the mandatory "not recorded" label, mirroring `pest-pressure-assess` hard rules.
- **R7** Nothing measured live (D2). Mitigation: "not re-measured" markers, and the guides say the first real run is the measurement.
- **R8** Daily check grows by two per-plant steps. Mitigation: health is tool-free, IPM reads only keys the pest report names, and the five-plant cap stays.
- **R9** Scope creep into #50 or into IPM write-back. Mitigation: harvest only as an input to the safety check; `create_inspection` only named.
- No security-sensitive path; `code-security-reviewer` not required.

## Open questions

All resolved by default under D3; the operator may overturn any.

- **Q1** Should the health result ever be a recommendation? → **Resolved by default**: no. Observation only (PD7); recommendations stay with the owning domains and IPM.
- **Q2** Should HA weather be readable in the health recipe? → **Resolved by default**: no (PD4). Caller `weather` only.
- **Q3** How is time to harvest sourced for the safety check? → **Resolved by default**: from the caller's `harvest_date`, else the growth-stage hand-off; never `get_harvest_readiness` (C12). If it is unknown and `allows_harvest` is true, the treatment is not recommendable.
- **Q4** Where do beneficials sit in the four stages? → **Resolved by default**: a release is stage 4 (biological, before chemical); conservation in an open setting is stage 3 (cultural).
- **Q5** Recipe names `plant-health-assessment` / `pest-ipm-plan` versus the `-check` convention? → **Resolved by default**: keep the issue's names (PD10).
- **Q6** PR base while #49 is unmerged? → **Resolved by default**: wait for the #49 merge, rebase, target `develop`. If the PR must open earlier, base it on feat/growth-stage-weather-impact.
- **Q7** Stale `spec/mcp/kamerplanter-mcp-server/en.md:28` (C9)? → **Resolved by default**: out of scope. Follow-up issue proposed; creating it is a GitHub write, pending the operator.
- **Q8** Spec slug? → **Resolved by default**: `plant-health-and-ipm-planning`.

## Approval

- Pre-analysis approved 2026-11-05 under the operator's delegation ("arbeite die autonom ab"); route `direct`; PD1–PD10 and Q1–Q8 accepted as resolved by default.
- Base updated: fast-forwarded to feat/growth-stage-weather-impact @f88ac8e (PR #67), which already removed the #49 artifact; R2 reduces to "rebase onto develop after #67 merges".
- #55 is now PR #69 at 21bd577 (guard final at 4a64a00); the P11 trial merge uses 21bd577.
- Q7 follow-up issue: GitHub issue creation is partly denied by the auto-mode classifier in this session; the draft goes to the operator.

## Dispatch log

<!-- Appended during operation 5; one line per package once its specialist reports.
     <YYYY-MM-DD> P<k> dispatched to <subagent_type> — <result one-liner> -->
- 2026-11-05 P1 done (generalist, `nolte-shared:spec` loaded and followed; autonomous, no interactive gates) — `spec/process/plant-health-and-ipm-planning/{en,de}.md`, §A–§I; en/de 17 headings, 54 requirement bullets, 16 checkboxes each. Refinement: `contradicted` also covers the owning domain's own negative result (pest `rejected`, no exposure in the supplied data), not only a higher-level item; without it a domain that ran and ruled a class out had no status.
- 2026-11-05 P2 done — care-planning spec en/de: Non-Goals point to the new spec, §C takes health/IPM findings as returned plus one bullet (health finding is an observation, no double count), §F plants bullet, one AC checkbox, Source row; en/de 38 bullets / 19 checkboxes each. §H unchanged.
- 2026-11-05 P3 done — `.claude/skills/plant-health-assessment/SKILL.md`, tool-free, no `mcp__kamerplanter__` reference (so no policy block needed, C15 not triggered).
- 2026-11-05 P4 done — `.claude/skills/pest-ipm-planning/SKILL.md`; one `Forbidden by name:` block with all twelve; `create_inspection` named only there and under `## Gotchas`; template uses a placeholder.
- 2026-11-05 P5 done — `recipes/plant-health-assessment.yaml`; `decision-policy` loaded before the health skill (step 8), matching the #49 recipes, rather than last as the plan listed.
- 2026-11-05 P6 done — `recipes/pest-ipm-plan.yaml`; `growth-stage-assessment` runs only when `harvest_date` is empty.
- 2026-11-05 P7 done — care-planning skill (inputs, step 1 bullet, "not yet built" sentence removed), daily check items 9 and 10, statuses `checked`/`not checked`, description and Step 7 domain list; final line unchanged.
- 2026-11-05 P8 done — guides en/de for both recipes, daily-check guide row and paragraph en/de.
- 2026-11-05 P9 done — CLAUDE.md garden-procedures bullet and tool-free exceptions, mkdocs nav + de labels, guide and reference indexes en/de.
- 2026-11-05 P10 done — `spec/README.md` row added in sort order, date 2026-11-05 = commit date (`git log -1 --format=%cs`); care-planning row already 2026-11-05.
- 2026-11-05 P11 partial — validator (incl. `--self-test`) OK, 24 recipes; `mkdocs build --strict` OK; `goose recipe validate` OK for plant-health-assessment, pest-ipm-plan, daily-garden-check; `--explain` lists all parameters; `pre-commit run --all-files` OK; grep finds no state-changing name in instruction text of the two new skills or care-planning. Trial merge with 21bd577 in a throwaway worktree: CLAUDE.md auto-merged without conflict, validator "OK — 24 recipe(s)", self-test OK incl. 12 permitting-load cases; merge aborted, worktree removed. `recipe-audit` and the independent review not run (orchestrator). No live run: `kamerplanter` `INVALID_CONFIG`.
