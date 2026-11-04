---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter-goose"
issue: "49"
classification: "feature-request"
secondary-classes: ["spec-change", "docs"]
route: "direct"
status: approved
created: "2026-11-04"
---

# Issue Orchestration — Pre-analysis

<!-- Run-scoped artifact: committed on feat/growth-stage-weather-impact, then removed with a
     fix-forward `git rm` before the PR merges, per spec/project/issue-orchestration/
     §Pre-analysis artifact lifecycle. See Risks R1: `.audits/` is gitignored in this repo. -->

## Issue metadata

- **Repository**: nolte/kamerplanter-goose
- **Issue**: #49 — [P1] Add growth stage assessment and weather impact analysis
- **URL**: https://github.com/nolte/kamerplanter-goose/issues/49
- **Labels**: enhancement, claude-code, skills
- **Author**: nolte (repository owner, trusted); 0 comments
- **Linked items**: declared dependencies #2 (MERGED, plant-domain knowledge migration) and #5 (CLOSED, "The task setup guard hides dependency bumps locally until CI fails" — unrelated to this feature by title; both are satisfied, neither blocks). Downstream consumers: #48 (plant health, takes "weather impact" as input), #50 (harvest, needs growth stage and GDD). Comparable precedents: PR #65 (issue #43) and PR #66 (issues #44, #45).
- **Prior art checked**: no `project/` directory (no roadmap, no features, no requirement artifacts); no open PRs (`gh pr list` returned `[]`); `.claude/skills/` holds no growth-stage or weather skill; `recipes/` holds no growth-stage or weather recipe. Partial coverage exists and is composed, not duplicated: `plant-context-collect` (phase, `phase_started_at`, `planted_on`, `typical_duration_days`, `base_temp_gdd`, cultivar `days_to_maturity`), `plant-lifecycle-resolve` (cycle and windows anchored to frost dates), `diary-measurements-read`, `plant-photo-read`, `garden-context` (weather `no source`), `decision-policy` (level 6 = weather), `care-planning` (plug-in contract).

## Decisions already made by the operator (recorded, not reopened)

- **D1 Requirements gate**: explicit operator override. This repository has no `project/requirements/`; the requirements are the issue's five acceptance criteria and scope list plus D2 to D4. Same override as #40 to #45.
- **D2 Weather source**: weather and forecast come as a caller-supplied recipe parameter, marked `caller`. The skill MAY additionally read a Home Assistant weather entity through the `home_assistant` server's `GetLiveContext`, and MUST report that as an unmeasured source. With neither, weather is reported explicitly as `no source`, and the analysis says what it cannot conclude.
- **D3 Read-only**: both new recipes are read-only (no `-apply` sibling). Each prompt carries a `Forbidden by name:` block naming all twelve state-changing Kamerplanter tools (`spec/mcp/kamerplanter-mcp-server/en.md:177`).
- **D4 No live measurement**: the `kamerplanter` MCP server is unreachable in this session (`INVALID_CONFIG`). Every claim about tool output rests on the recorded measurements in `spec/` and MUST be marked as not re-measured.

## Planning decisions taken here (operator may overturn at the approval gate)

- **PD1 One governing spec for both skills**: `spec/process/growth-stage-and-weather-impact/{en,de}.md`, the same shape as `watering-and-fertilization-decisions` (one spec for two coupled decisions). Rationale: both share the environment inputs (temperature, humidity, light), the derivation rule and the separation of exposure from symptom; two specs would restate those rules, and CLAUDE.md says a rule stated in one layer is not restated in another.
- **PD2 growth-stage-assessment reconciles; it does not re-read**: the skill's added value is reconciling the recorded phase against observations (diary measurements, photo findings), plant age since `planted_on`, phase duration and cultivar or species expectations. It consumes the `plant-context-collect` block (and optionally the `plant-lifecycle-resolve` report) as given. Its only own tool reads are `get_plant_phase_status` (to catch `phase_state: unresolved`, which `plant-context-collect` does not call) and `get_plant_phase_history` (whose response fields are unrecorded, so it reports them verbatim and assumes no key). Rationale: `garden-context/SKILL.md:89` explicitly leaves the `unresolved` check to "a caller that narrows to a plant", and editing `plant-context-collect` would change the context of every existing recipe that loads it.
- **PD3 GDD, VPD and photoperiod are derivations, computed only from supplied inputs, with no evidence level**:
  - GDD: computed only from a caller-supplied daily temperature series (min/max per day, unit stated) since `planted_on`, against the species record's `base_temp_gdd`. Absent series or absent `base_temp_gdd` → GDD absent with the reason. A Home Assistant snapshot is a single point and is not a series, so it never yields GDD. No measured field holds a GDD-to-stage or GDD-to-maturity target (cultivar `days_to_maturity` counts days), so accumulated GDD is reported as context and MUST NOT place a stage on its own.
  - VPD: computed only from a temperature and a relative humidity taken at the same time and place (caller, or the HA weather entity for outdoor air). A diary `measurements` key whose meaning or unit is ambiguous is refused, as in the watering spec. `search_glossary` supplies the definition only (vocabulary, not evidence).
  - Photoperiod: outdoors computed from a caller-supplied latitude and the assessment date (no site-attribute source exists); indoors only the caller-supplied light schedule. No measured species field states photoperiod sensitivity, so "the species responds to day length" is `no source` unless researched under the three-source rule.
  - Rationale: `spec/process/garden-decision-policy/en.md` ranks sources, not derivations ("Where derived evidence sits", Open Questions), and gives such a derivation no level; `care-planning` already writes `no level` where the policy gives none. This keeps the decision-policy table untouched (the policy owns levels; this spec states none of its own).
- **PD4 Weather effects are exposures, never symptoms**: a weather finding states an exposure or an expected risk to the plant (frost below the species' tolerance, heat above the phase's stress tolerance, heavy rain, wind, humidity band, a forecast change) as an observation or a proposal to a person. A plant symptom comes only from `plant-photo-read`, a diary entry or an inspection, and is reported in a separate block. The two may be linked only as "consistent with", which under decision-policy rule 1 is a suspicion, never a diagnosis. This is the issue's acceptance criterion 2.
- **PD5 Output fits the care-planning plug-in contract**: both skills return findings in `care-planning` §C shape (domain, subject, kind, statement, evidence entries, confidence, what would change it, missing data, optional stated consequence), so `care-planning` takes them as returned, like the watering and fertilisation findings. A named mutation for a phase discrepancy is `transition_plant_phase`, named and never called. An additional, documented hand-off block names the fields #48 (weather exposures, separated from symptoms) and #50 (estimated stage, accumulated GDD with its inputs, cultivar `days_to_maturity` position) can read; neither consumer is built here.
- **PD6 Daily check integration is in scope**: `spec/process/care-planning-and-daily-check/en.md` §C requires each Non-Goal domain to be reported as `not available` "until that skill exists". Shipping the skills without updating the care plan and the daily check would leave those texts false. PR #66 did the same for watering and fertilisation. The daily check takes weather only from a new caller parameter, never from Home Assistant, because §H of that spec forbids any Home Assistant tool call from the daily check.
- **PD7 Home Assistant guard in the weather recipe**: the weather recipe's prompt forbids actuation by category (HA spec requirement), names `GetLiveContext` conditionally ("if present"), and forbids `TimeTillErnte` and `time_till` while their effect is unclassified (`spec/mcp/home-assistant-mcp-server/en.md`, Requirements). The growth-stage recipe calls no Home Assistant tool at all; the `TimeTillErnte` intent ("time till harvest") is the most tempting wrong substitute in this domain.

## Classification

- **Primary class**: feature-request
- **Secondary class(es)**: spec-change, docs
- **Rationale**: two new skills and two new recipes with a new governing process spec; existing specs and guides are amended to plug them in.
- **Asserted cause verified**: none asserted (feature, no defect claim).

## Established and unestablished claims

| # | Claim | Status | Evidence or settling observation |
|---|-------|--------|----------------------------------|
| C1 | The measured Kamerplanter catalog has no weather or forecast tool | established (recorded, not re-measured) | `spec/mcp/kamerplanter-mcp-server/en.md:96-110` (44 read tools, none weather); `spec/process/garden-decision-policy/en.md:49,90`; `.claude/skills/garden-context/SKILL.md:54` |
| C2 | Weather is treated as caller-supplied elsewhere | established | `spec/process/watering-and-fertilization-decisions/en.md:39,133`; `recipes/watering-decision.yaml:20-26` (`weather` parameter) |
| C3 | Whether Home Assistant exposes any weather entity is unmeasured | established as unmeasured | `spec/process/garden-decision-policy/en.md:49`; settle with a `GetLiveContext` call filtered to `domain: weather` against the reference instance |
| C4 | No GDD, VPD or photoperiod value exists in the catalog; only `search_glossary` defines VPD | established (recorded) | `spec/mcp/kamerplanter-mcp-server/en.md:118`; `grep -rn -i "vpd\|gdd\|photoperiod" spec/mcp` finds nothing else |
| C5 | Refines the hypothesis: a GDD input does exist: species `base_temp_gdd` | established (recorded, measured 5.0 leek, 15.0 peace lily) | `spec/process/species-baseline-verification/en.md:53,126`; `.claude/skills/plant-context-collect/SKILL.md:39` |
| C6 | No GDD target for a stage or maturity is recorded; cultivar maturity is in days | established (recorded) | `spec/process/plant-health-image-analysis/en.md:110`, `spec/process/nutrient-imbalance-detection/en.md:108` |
| C7 | The GDD-without-temperature-history question is already open upstream | established | `spec/process/plant-health-image-analysis/en.md:189` |
| C8 | No species field records photoperiod sensitivity | established (recorded, two species probed) | `spec/process/species-baseline-verification/en.md:55,62`; settle with `get_species_info` on a short-day crop |
| C9 | `get_plant_phase_status` can answer `phase_state: unresolved`, which reads as normal and is not | established (recorded) | `spec/mcp/kamerplanter-mcp-server/en.md:119`; `spec/process/garden-decision-policy/en.md:47,87` |
| C10 | `plant-context-collect` does not call `get_plant_phase_status`; `garden-context` defers the check to a per-plant caller | established | `.claude/skills/plant-context-collect/SKILL.md` §2, §4; `.claude/skills/garden-context/SKILL.md:89` |
| C11 | Response fields of `get_plant_phase_history` and `get_harvest_readiness` are not recorded | established (absence) | `grep -rn` over `spec/` finds only catalog/table rows; settle with one read call each on a reachable instance |
| C12 | Two specs name #49 as a future plug-in domain; care planning reports it `not available` only "until that skill exists" | established | `spec/process/care-planning-and-daily-check/en.md:16,28` and §C last bullet; `spec/process/watering-and-fertilization-decisions/en.md:28`; `.claude/skills/care-planning/SKILL.md:14`; `recipes/daily-garden-check.yaml:4,110-111`; `docs/en/guides/daily-garden-check.md:47` |
| C13 | The daily check must not call a Home Assistant tool | established | `spec/process/care-planning-and-daily-check/en.md` §H |
| C14 | Read-only recipes must forbid HA actuation by category in `prompt` and must not call `TimeTillErnte`/`time_till`; neither rule is machine-checked | established | `spec/mcp/home-assistant-mcp-server/en.md` Requirements; `grep -n "Hass\|actuat\|TimeTillErnte" tests/validate_recipes.py` finds nothing |
| C15 | A skill that mentions `mcp__kamerplanter__` must name all twelve state-changing tools (machine-checked) | established | `tests/validate_recipes.py:279-298,620-653` |
| C16 | No Home Assistant sensor may be used as evidence about a plant | established | `spec/process/watering-and-fertilization-decisions/en.md` §A, fourth bullet |
| C17 | Decision-policy level 6 is "Weather"; derivations carry no level | established | `.claude/skills/decision-policy/SKILL.md:29,33`; `spec/process/garden-decision-policy/en.md` Open Questions |
| C18 | The ranking may be wrong where weather decides (frost, heat spike) | established as open upstream | `spec/process/garden-decision-policy/en.md` Open Questions "Whether the ranking is global or per question" |
| C19 | `recipe-implement` cannot be used: needs `project/recipes/<slug>/plan.md` in state ready, absent | established | nolte-goose `skills/recipe-implement/SKILL.md` description; `ls project` → no such directory |
| C20 | An audience artifact exists | established | `AUDIENCES.md`; guides carry `audience:` frontmatter (`docs/en/guides/watering-decision.md:1-7`) |
| C21 | `.audits/` is gitignored in this repository | established | `git check-ignore -v .audits/issue-orchestrate/49/analysis.md` → `.gitignore:13:/.audits/` |
| C22 | Any statement about live tool output (field names, `phase_state` value set, HA entity shape) holds for this run | unestablished | `kamerplanter` `INVALID_CONFIG`; settle by the first real run of each recipe |

## Scope

- **In scope**: new spec `spec/process/growth-stage-and-weather-impact/{en,de}.md`; skills `.claude/skills/growth-stage-assessment/SKILL.md`, `.claude/skills/weather-impact-analysis/SKILL.md`; read-only recipes `recipes/growth-stage-check.yaml`, `recipes/weather-impact-check.yaml`; plug-in integration (care-planning spec en/de, care-planning skill, `recipes/daily-garden-check.yaml`, its guides); guides `docs/{en,de}/guides/{growth-stage-check,weather-impact-check}.md`; bookkeeping in `CLAUDE.md`, `mkdocs.yml`, `docs/{en,de}/guides/index.md`, `docs/{en,de}/references/index.md`, `spec/README.md` (regenerated).
- **Out of scope**: any `-apply` recipe, phase-transition write or HA actuation (D3); plant health/IPM (#48) and harvest planning (#50) beyond the named hand-off fields; a weather backend, sensor-to-plant mapping or GDD target table (no source; open questions); edits to `plant-context-collect`, `plant-lifecycle-resolve`, `decision-policy` or the decision-policy level table; a new validator rule (Q3); live measurement (D4).

## Route

- **Decision**: direct
- **Rationale**: one goal outcome, one PR strand on `feat/growth-stage-weather-impact`, no `project/roadmap.md` exists to create or retarget an item; same shape and size as PR #66.
- **Pipeline hand-off**: n/a

## Work packages

### P1 — Governing spec: growth stage and weather impact

- **Problem statement**: no spec fixes what a growth-stage estimate and a weather-impact assessment may rest on, how GDD, VPD and photoperiod are derived, or how weather exposure is kept apart from plant symptoms.
- **Acceptance criteria**:
  - `en.md` exists with Status `draft`, Portfolio-Scope `local`, sections Context, Goals, Non-Goals, Requirements (A Inputs, B Growth stage, C Derivations GDD/VPD/photoperiod, D Weather impact, E Separation of exposure from symptom, F Plug-in shape and hand-off to #48/#50, G Determinism, H Separation and forbidden tools), Acceptance Criteria, Source, Open Questions.
  - Requirements encode D2–D4 and PD2–PD7; every tool-surface claim cites `spec/mcp/*` and says "not re-measured"; Context names `INVALID_CONFIG`.
  - Each of the issue's five acceptance criteria maps to at least one requirement and one checkbox.
  - Growth stage returns a closed result set (proposed: `recorded stage consistent`, `recorded stage questionable`, `insufficient evidence`; `phase unresolved` reported as an absent stage). Weather returns per factor (temperature extremes, rainfall, wind, humidity, heat/cold events, forecast changes) one of `exposure`, `no exposure in the supplied data`, `no source`.
  - States no evidence level of its own; derivations carry `no level`.
  - `de.md` translation with identical heading order and equal requirement-bullet and checkbox counts.
  - Open Questions include: weather source, HA weather entity shape, GDD target, photoperiod sensitivity field, `get_plant_phase_history` fields, global-vs-per-question ranking for frost/heat.
- **Touched files / artifacts**: `spec/process/growth-stage-and-weather-impact/en.md`, `spec/process/growth-stage-and-weather-impact/de.md`
- **Specialist**: `nolte-shared:spec`; optional read-only check `nolte-shared:spec-readiness-reviewer`
- **Depends on**: none

### P2 — Plug growth stage and weather into the care-planning spec

- **Problem statement**: the care-planning spec lists growth stage and weather as unbuilt Non-Goal domains to report `not available` until the skill exists (C12).
- **Acceptance criteria**: `spec/process/care-planning-and-daily-check/{en,de}.md` Non-Goals no longer list #49 as unbuilt; §C names the two skills as domains returning findings in the plug-in shape; §F adds them to the per-plant checks and adds a caller `weather` parameter; §H unchanged; Source cites the new spec; en/de heading order and counts identical. `watering-and-fertilization-decisions:28` left as is unless dedup finds a stale pointer.
- **Touched files / artifacts**: `spec/process/care-planning-and-daily-check/en.md`, `spec/process/care-planning-and-daily-check/de.md`
- **Specialist**: `nolte-shared:spec`
- **Depends on**: P1

### P3 — Skill: weather-impact-analysis

- **Problem statement**: no procedure turns caller-supplied weather (and an optional HA weather entity) into exposures for a plant, kept apart from symptoms and honest about missing sources.
- **Acceptance criteria**: frontmatter `name` + `description`, no `disable-model-invocation`; inputs caller weather/forecast (`caller`), optional `GetLiveContext` named conditionally and reported as `home_assistant (unmeasured)`, the `plant-context-collect` block; neither source → every factor `no source` plus what cannot be concluded; caller-vs-HA disagreement reported as contradiction, not averaged; weather never evidence about the plant's present state nor a symptom, symptom block separate, linked only as "consistent with"; findings in care-planning §C shape, level 6 for weather, `no level` for VPD; forbids HA actuation by category and `TimeTillErnte`/`time_till`; names all twelve tools if it mentions `mcp__kamerplanter__`; `task test` passes.
- **Touched files / artifacts**: `.claude/skills/weather-impact-analysis/SKILL.md`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P1

### P4 — Skill: growth-stage-assessment

- **Problem statement**: the recorded phase is read in three skills but never reconciled against what the plant shows, its age, its phase duration and its cultivar expectation; GDD and photoperiod are never used.
- **Acceptance criteria**: frontmatter `name` + `description`; consumes `plant-context-collect` (and optionally `plant-lifecycle-resolve`, `diary-measurements-read`, `plant-photo-read`) as given; own reads only `get_plant_phase_status` and `get_plant_phase_history`; `unresolved` reported as absent stage; history fields reported as returned; closed result set from P1 with evidence, confidence from highest supporting level, uncertainty, missing data; GDD only from caller series + `base_temp_gdd`, never placing a stage alone; photoperiod only from caller latitude/light schedule; both `no level`; a questionable phase names `transition_plant_phase` as a mutation, never called; names all twelve tools; output fits care-planning §C plus #50 hand-off fields; `task test` passes.
- **Touched files / artifacts**: `.claude/skills/growth-stage-assessment/SKILL.md`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P1

### P5 — Recipe: weather-impact-check (read-only)

- **Problem statement**: a person cannot ask what the current weather and forecast mean for named plants.
- **Acceptance criteria**: no `extensions:` block; `description` opens `Read-only:`, names the working directory, states caller weather and optional unmeasured HA source; parameters (proposed) `tenant`, `weather`, `plants` (≤5, rest not checked); `prompt` has `Forbidden by name:` with all twelve tools, bans HA actuation by category, bans `TimeTillErnte`/`time_till`, references `GetLiveContext` conditionally; loads `plant-context-collect`, `weather-impact-analysis`, `decision-policy`; fixed status table and machine-readable final line; `goose recipe validate` valid, `--explain` lists parameters, `task test` passes.
- **Touched files / artifacts**: `recipes/weather-impact-check.yaml`
- **Specialist**: no matching specialised agent — generalist remediation (`nolte-goose:recipe-implement` needs an absent `project/recipes/<slug>/plan.md`)
- **Depends on**: P3

### P6 — Recipe: growth-stage-check (read-only)

- **Problem statement**: a person cannot ask whether a plant's recorded stage matches what is known about it.
- **Acceptance criteria**: no `extensions:` block; `description` opens `Read-only:`, names the working directory; parameters (proposed) `plant_key` (required), `tenant`, `temperatures`, `light`, `observations`; `prompt` has `Forbidden by name:` with all twelve tools and calls no HA tool; loads `plant-context-collect`, `diary-measurements-read`, `plant-photo-read` (only with photos), optionally `plant-lifecycle-resolve`, then `growth-stage-assessment`, `decision-policy`; fixed table and final line; `goose recipe validate` valid, `--explain` lists parameters, `task test` passes.
- **Touched files / artifacts**: `recipes/growth-stage-check.yaml`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P4

### P7 — Integrate into care planning and the daily garden check

- **Problem statement**: the care plan and daily check report growth stage and weather as `not available` (C12), false once P3/P4 exist.
- **Acceptance criteria**: `care-planning/SKILL.md` takes both domains' findings as returned and names only #48 as unbuilt; `daily-garden-check.yaml` gains optional `weather` (caller), runs both skills per checked plant on blocks already collected plus the two phase reads, status `checked`, `description` updated, no HA tool called or named as callable, final line format unchanged; `task test` passes, `goose recipe validate` valid.
- **Touched files / artifacts**: `.claude/skills/care-planning/SKILL.md`, `recipes/daily-garden-check.yaml`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P2, P3, P4

### P8 — Guides for the two recipes and the daily check update

- **Problem statement**: no guide exists for the new recipes, and the daily-check guide calls the domains not available.
- **Acceptance criteria**: `docs/{en,de}/guides/growth-stage-check.md` and `weather-impact-check.md` with house frontmatter (`title`, `audience`, `content_mode: how-to`, `track`, `last_updated`), a "not yet run against a live instance" note, the working-directory warning, a parameter table, an "expect `no source` / `insufficient evidence`" section; `daily-garden-check.md` en/de domain table updated and `weather` parameter documented; `task docs` passes.
- **Touched files / artifacts**: `docs/en/guides/growth-stage-check.md`, `docs/de/guides/growth-stage-check.md`, `docs/en/guides/weather-impact-check.md`, `docs/de/guides/weather-impact-check.md`, `docs/en/guides/daily-garden-check.md`, `docs/de/guides/daily-garden-check.md`
- **Specialist**: `nolte-shared:audience-doc-author` (AUDIENCES.md exists); generalist if the operator keeps the #65/#66 precedent
- **Depends on**: P5, P6, P7

### P9 — Bookkeeping: CLAUDE.md, nav, indexes

- **Problem statement**: the new skills and recipes are not listed in the repository map, nav or reference indexes.
- **Acceptance criteria**: `CLAUDE.md` garden-procedures bullet lists both skills (both read tools, so not tool-free exceptions); `mkdocs.yml` nav with German labels; `docs/{en,de}/guides/index.md` and `docs/{en,de}/references/index.md` list both recipes (writes: no) and both skills; `task docs` passes.
- **Touched files / artifacts**: `CLAUDE.md`, `mkdocs.yml`, `docs/en/guides/index.md`, `docs/de/guides/index.md`, `docs/en/references/index.md`, `docs/de/references/index.md`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P8

### P10 — Regenerate the spec index

- **Problem statement**: `spec/README.md` is generated and does not list the new spec.
- **Acceptance criteria**: regenerated (not hand-edited), lists `process/growth-stage-and-weather-impact` with en/de titles, `draft`, `local`; care-planning row date reflects P2.
- **Touched files / artifacts**: `spec/README.md`
- **Specialist**: `nolte-shared:spec` (index mode)
- **Depends on**: P1, P2

### P11 — Verification

- **Problem statement**: the bundle must pass the house gate and the recipe audit before the PR.
- **Acceptance criteria**: `task check` and `pre-commit run --all-files` green; `nolte-goose:recipe-audit` on `weather-impact-check.yaml`, `growth-stage-check.yaml`, `daily-garden-check.yaml` at the final head, exit 0, 0 findings, digests recorded; an independent fresh-context read-only review finds no spec/skill/recipe contradiction (findings fixed or recorded); PR Testing states no live run (`INVALID_CONFIG`).
- **Touched files / artifacts**: none (fixes route back to the owning package)
- **Specialist**: `nolte-goose:recipe-audit`; `task check` by the orchestrator
- **Depends on**: P5, P6, P7, P8, P9, P10

## Dependency ordering

P1 → {P2, P3, P4} (parallel) → {P5 after P3, P6 after P4, P10 after P1+P2} → P7 (after P2, P3, P4) → P8 (after P5, P6, P7) → P9 → P11 (after P5–P10).

## Risks

- **R1** `.audits/` is gitignored (`.gitignore:13`) while §Pre-analysis artifact lifecycle requires it committed and not hidden. Mitigation: `git add -f`, fix-forward `git rm` before merge, as PR #66 did; `.gitignore` change out of scope.
- **R2** Nothing measured live (D4). Mitigation: mark not re-measured, report history fields verbatim, guides say the first real run is the measurement.
- **R3** Plausible GDD with nothing behind it. Mitigation: caller series + `base_temp_gdd` only, no GDD-only stage, `no level`; `species-baseline-verify` warns of fictitious GDD for a tropical species with a temperate base.
- **R4** Decision-policy ranks species data (4) above weather (6), yet weather decides for frost (C18). Mitigation: no re-ranking; weather exposure is a level-6 observation; conflict carried as open question pointing at the decision-policy spec.
- **R5** HA surface: `GetLiveContext` may be absent or expose no weather entity; `TimeTillErnte`/`time_till` unclassified; HA bans not machine-checked. Mitigation: conditional references, explicit `no source` step result, category and named bans, recipe-audit in P11.
- **R6** Weather leaking into plant evidence (C16). Mitigation: P1 §E and P3 keep weather site-level exposure; P11 review checks it.
- **R7** Daily check grows by two per-plant reads for up to five plants. Mitigation: cap stays; weather adds no Kamerplanter call there.
- **R8** Scope creep into #48/#50. Mitigation: hand-off limited to a named field list.
- No security-sensitive path; `code-security-reviewer` not required.

## Open questions

- **Q1** HA read in the weather recipe default-on when `GetLiveContext` is present, or opt-in by parameter?
- **Q2** Is `recorded stage consistent | recorded stage questionable | insufficient evidence` acceptable, or should "ahead"/"behind" be distinct for #50?
- **Q3** Add a validator check for HA actuation bans and `TimeTillErnte`/`time_till` (C14), or follow-up issue?
- **Q4** P8 via `nolte-shared:audience-doc-author` or generalist?
- **Q5** Confirm the spec slug `growth-stage-and-weather-impact`.

## Open-question resolutions (operator delegated: "arbeite die autonom ab", 2026-11-04)

- **Q1** default-on: the weather recipe reads `GetLiveContext` when the tool is present (per D2, "MAY additionally read"), always labelled `home_assistant (unmeasured)`; caller data wins on disagreement only by being reported side by side as a contradiction, never averaged.
- **Q2** keep the three-value closed set, and add a `direction` field on `recorded stage questionable` with `ahead | behind | unclear`, so #50 can read it without a fourth result.
- **Q3** out of scope; follow-up issue for a validator check on HA actuation bans and `TimeTillErnte`/`time_till`. Creating it is a GitHub write, pending operator (auto-mode denies `gh` writes in this session).
- **Q4** generalist, following the #65/#66 precedent; one implementation agent carries P1–P10 in DAG order.
- **Q5** slug `growth-stage-and-weather-impact` confirmed.

## Approval

- Pre-analysis approved 2026-11-04 under the operator's delegation; route `direct` confirmed.

## Dispatch log

<!-- Appended during operation 5; one line per package once its specialist reports. -->
- 2026-11-05 P1 done (generalist; spec authored by hand, `nolte-shared:spec` used for P10 only) — `spec/process/growth-stage-and-weather-impact/{en,de}.md`, 40 requirement bullets and 15 checkboxes in both, identical heading structure. Refinements: caller `placement` input added (no site-attribute source, `garden-decision-policy` level 5) and a sourced-threshold rule for exposures (`frost_sensitivity`/`stress_tolerance` value sets unrecorded); caller observation read as level 3, carried as an open question.
- 2026-11-05 P2 done — care-planning spec en/de: Non-Goals list only #48 as unbuilt, §C takes growth-stage and weather findings as returned, §F adds the two checks and a `weather` parameter (+1 requirement bullet, +1 checkbox each language), Source cites the new spec; §H unchanged.
- 2026-11-05 P3 done — `.claude/skills/weather-impact-analysis/SKILL.md`; HA read only with caller permission or a reading handed over; names all twelve tools; validator green.
- 2026-11-05 P4 done — `.claude/skills/growth-stage-assessment/SKILL.md`; own reads `get_plant_phase_status`, `get_plant_phase_history`; assessment date is an input (caller or newest observation), never today; `direction` per Q2; names all twelve tools.
- 2026-11-05 P5 done — `recipes/weather-impact-check.yaml`; params `tenant`, `plants`, `weather`, `placement` (added, see P1); `GetLiveContext` conditional, once, `domain: weather` (Q1 default-on); actuation banned by category, `TimeTillErnte`/`time_till` by name; final line `WEATHER: <e> exposures, <s> no source — <slug>`.
- 2026-11-05 P6 done — `recipes/growth-stage-check.yaml`; params `plant_key`, `tenant`, `observations`, `entry_key`, `temperatures`, `latitude`, `light`, `as_of`. `plant-lifecycle-resolve` deliberately not loaded: its step 4 researches via URL fetch, which the recipe forbids; the skill still accepts its report when a caller has one.
- 2026-11-05 P7 done — care-planning skill names only #48 as unbuilt; daily check gains `weather`, runs both skills per plant (items 7, 8), HA read not permitted, domains split into `growth stage` and `weather`, final line unchanged.
- 2026-11-05 P8 done (generalist, per Q4) — guides en/de for both recipes; daily-check guides en/de updated (domain table, `weather` parameter).
- 2026-11-05 P9 done — CLAUDE.md, mkdocs.yml (nav + German labels), guides and references indexes en/de.
- 2026-11-05 P10 done — `spec/README.md` regenerated per `nolte-shared:spec` operation 4 after the commit, dates from `git log -1 --format=%cs`.
- 2026-11-05 P11 partial — validator, `mkdocs build --strict`, `goose recipe validate` (3 recipes), `pre-commit run --all-files` green; `nolte-goose:recipe-audit` and the independent fresh-context review not run by this implementation agent (orchestrator's step). No live run: `kamerplanter` `INVALID_CONFIG`.
- 2026-11-05 P11 review fixes — five review findings on 5d3c622 fixed: humidity is an exposure only beyond a sourced threshold or a named extreme; the caller is no threshold source (level 4 record or labelled level 8 only); an own observation without `as_of` computes no time-based comparison; the photo entry date is taken only from a diary entry read for this plant; without `placement` every weather exposure in the daily check stays a conditional observation. Gate re-run green.
