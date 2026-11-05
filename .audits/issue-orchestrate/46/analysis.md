---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter-goose"
issue: "46"
classification: "feature-request"
secondary-classes: ["spec-change", "docs"]
route: "direct"
status: approved
created: "2026-11-05"
---

# Issue Orchestration — Pre-analysis

<!-- Run-scoped artifact: committed on feat/bed-layout-succession, removed with a
     fix-forward `git rm` before the PR merges, per spec/project/issue-orchestration/
     §Pre-analysis artifact lifecycle. -->

## Issue metadata

- **Repository**: nolte/kamerplanter-goose
- **Issue**: #46 — [P1] Add bed layout, companion planting, and succession planning
- **URL**: https://github.com/nolte/kamerplanter-goose/issues/46
- **Labels**: enhancement, claude-code, skills
- **Author / trust**: nolte (repository owner, trusted); 0 comments
- **Linked items**: "Depends on issues #3 and #4". Both are closed and unrelated (#3 "nutrient-imbalance-check can never reach tier 1 or 2…", #4 "analyse-queue.sh reports success on a failed queue read…", `gh issue view 3/4`), so the reference is stale and does not block. The real upstream dependencies are #42 (plant planning, merged as PR #60) and #47 (crop rotation, open PR #70, branch `feat/crop-rotation-planning`). Related: #59 and #68 (blocked `-apply` precedents), #55 (skill obedience guard, open PR #69), #39 (ownership audit), #43 (care planning, a sibling consumer of the plan).
- **Prior art checked**: there is no `project/` directory (no requirements, features or roadmap). `gh pr list` shows #70 (#47, the base of this branch), #69 (#55) and #67 (growth stage/weather, unrelated but touches the same indexes). `gh issue list --search "bed layout OR succession OR companion"` finds only #46, #42 and #39. In-repo, bed layout appears only as a placeholder: plant-planning assigns `location: unassigned` and names a succession only within one candidate (`.claude/skills/plant-planning/SKILL.md:39-42`), and crop-rotation-planning "never place[s] runs, area or spacing" (`spec/process/crop-rotation-planning/en.md:136`). Nothing resolves the issue already.
- **Working copy**: /home/nolte/repos/.worktrees/kamerplanter-goose/bed-layout, branch `feat/bed-layout-succession`, **stacked** on `feat/crop-rotation-planning` @ `f24cc8a` (merge-base with `develop` is `b6e5a55`).

## Decisions

- **D1 Requirements gate: operator override.** There is no `project/requirements/`. The issue body is the grounded input, as for #42 and #47.
- **D2 Nothing measured live.** The `kamerplanter` MCP server is unreachable in this session (`INVALID_CONFIG`). Every claim about tool output rests on `spec/mcp/kamerplanter-mcp-server/en.md` and `spec/process/species-baseline-verification/en.md` (measured 2026-08-07 and 2026-08-16) and is **not re-measured**. The spec, skills, recipes and guides MUST say so.
- **D3 Autonomous run.** Open questions are resolved with a recommended default, marked "resolved by default, operator may overturn".
- **D4 No `bed-layout-plan-apply` in this PR.** I re-checked the measured write catalog (`spec/mcp/kamerplanter-mcp-server/en.md:128-148`, eleven `mcp.write` tools plus `create_site`). It has no tool that creates a bed, records a bed assignment or a layout, or creates a planting run:
  - `set_plant_location` moves a plant that **already exists**, while a layout places crops that are not plants yet (the same reasoning as `crop-rotation-planning/en.md:159`).
  - `create_site` creates a site root (apartment, garden, balcony, …), not a bed with an area, and is `mcp.setup`.
  - `add_plant_diary_entry` annotates an existing plant.

  So this PR builds only the read-only `bed-layout-plan` and `succession-plan`, each with an `APPLY CONTRACT` block. `bed-layout-plan-apply` is split into a blocked follow-up (draft in P12). This is the same blocker as #59 and #68. Established: `kamerplanter-mcp-server/en.md:128-148`.
- **D5 The #55 convention applies (PR #69, `21bd577`).**
  - Only content under a level-2 `## Gotchas` or `## Source` heading is explanation.
  - Elsewhere, a state-changing tool name outside a `Forbidden by name:` / `Permitted by name:` block is a call.
  - A skill-name token in a SKILL.md's instruction text counts as loading that skill, transitively.

  New skills must comply, verified by a trial merge with the #55 branch. Baseline established: a trial merge of `f24cc8a` with `fix/skill-instruction-separation` (which contains `21bd577`) in a scratchpad clone ran `tests/validate_recipes.py` → "OK — 21 recipe(s) match the house pattern" and `--self-test` → all cases hold. The only skill with a `Permitted by name:` block is `diary-analysis-claim` (`grep -l "Permitted by name:"` on the #55 worktree), and no planning-chain skill names it.

## Classification

- **Primary class**: feature-request
- **Secondary class(es)**: spec-change, docs
- **Rationale**: The issue adds a new process (spec, three skills, two recipes, guides). Existing specs change only in their cross-references.
- **Asserted cause verified**: The issue asserts no cause. Its implicit assumptions that spacing, light, access, irrigation and incompatible companions are catalog data are **mostly refuted**; see H1 to H3.

## Hypotheses checked

| # | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| H1 | Beds, containers, dimensions, light/shade, access and irrigation have no measured source and come from the caller | **Confirmed; the line reference is corrected.** Beds and containers have no source (`spec/process/garden-decision-policy/en.md:84`; `:49` and `:90` are the weather rows). Light and exposure, area and volume, and water are "No source measured" (`spec/process/site-analysis-and-crop-selection/en.md:44,45,48`), and `garden-context` reports beds as `no source` (`.claude/skills/garden-context/SKILL.md:53`). No field for access occurs anywhere in `spec/` (grep "access" finds nothing relevant). No read tool exists for a site's own attributes (`garden-decision-policy/en.md:48`) | established (file:line, grep) |
| H2 | Species and cultivar records carry no spacing or density field | **Partially refuted.** `seed_profile.sowing_density_per_m2` is an observed field (`species-baseline-verification/en.md:55`), measured on `Allium porrum` only (`kamerplanter-mcp-server/en.md:161`). Whether it counts seeds or plants per m², and whether a cultivar carries it, is unrecorded. No in-row, between-row, plant-spacing or plant-count field is named anywhere (grep `spacing\|row_dist\|plant_dist` finds no species field). Consequence: a capacity is validated only against numbers the caller supplies. `sowing_density_per_m2` is context, never a plant capacity, and spacing from general knowledge (level 8) is forbidden | established (file:line). Unestablished: the unit semantics and coverage of `sowing_density_per_m2`. Settling observation: `get_species_info` on ten or more vegetable species on a reachable instance |
| H3 | Companions: `compatible_companions[]` exists; check for an antagonist field | **Confirmed.** `compatible_companions[]` carries a `score` (`species-baseline-verification/en.md:56`; `.claude/skills/crop-selection/SKILL.md:52`). No incompatible or antagonist field exists, and a pair that is not listed is `unknown`, never incompatible (`site-analysis-and-crop-selection/en.md:75,83`). The value range and direction of `score` are unrecorded (the only matches for "score" are those lines). Incompatibility therefore comes only from the caller (`avoid=` pairs) | established (file:line, grep). Unestablished: the semantics of `score` |
| H4 | Succession reads planting-calendar windows and consumes the #47 rotation plan instead of re-deriving rotation | **Confirmed.** The plan's runs copy the calendar windows with their rule, fields, source and level (`.claude/skills/plant-planning/SKILL.md:37`, `plant-planning-and-planting-calendar/en.md:79,86-89`). The rotation plan exposes, per bed and season, the selected group or `open` or `occupied`, the crops keyed `species_key/cultivar_key` with their verdicts, and the conflicts for bed layout (`crop-rotation-planning/en.md:139,143-145`). The join is on the run-id prefix | established (file:line) |
| H5 | One or two specs and skills | **Decided: one spec, three skills.** One spec because the precedent is one spec for two steps (`plant-planning-and-planting-calendar`) and because layout capacity is evaluated over time, which includes the successions. Three skills: the two named in the issue (`succession-planning`, `bed-layout-planning`) stay tool-free so their determinism can be measured without the server (as in #60 and #47), and the catalog reads (companions with score, `sowing_density_per_m2`) move into a reading skill `companion-spacing-collect` | design decision; precedent established at `.claude/skills/planting-calendar/SKILL.md` and `plant-planning/SKILL.md`, and `rotation-history-collect` and `crop-rotation-planning` |

## Scope

- **In scope**:
  - Process spec `spec/process/bed-layout-and-succession-planning/{en,de}.md`.
  - Reading skill `companion-spacing-collect`, and tool-free skills `succession-planning` and `bed-layout-planning`.
  - Read-only recipes `recipes/succession-plan.yaml` and `recipes/bed-layout-plan.yaml`, each with an `APPLY CONTRACT` block.
  - Guides (en, de) for both recipes.
  - Bookkeeping: CLAUDE.md, mkdocs nav with DE translations, guide and reference indexes, `spec/README.md`.
  - Cross-reference updates in the plant-planning and crop-rotation specs.
  - Verification: `task check`, recipe audit, a determinism fixture, and the #55 trial merge.
  - Issue acceptance criteria and where they are covered:
    - "Layout proposals are explainable": every placement carries a rationale with rule, ranking values, inputs, sources and levels, and every crop left out has a reason (P1 §D, P4).
    - "Companion planting is treated as a constraint/input, not an absolute guarantee": the catalog companion list is a ranking input (level 4) and the caller's `avoid=` pairs are hard constraints. An unlisted pair is `unknown`, and the plan states that a companion pairing is not a guarantee (P1 §B and §D, P2, P4).
    - "Capacity and spacing are validated": capacity is checked per bed and month against the caller's area, spacing and quantity. Without them the result is `not validated` with the missing input, never a level-8 number (P1 §D, P4).
    - "Apply operations are separated from proposals": the `APPLY CONTRACT` blocks and the blocked follow-up (P12, D4).
    - "Succession proposals reference planting-calendar data": every succession names its run identifiers and copies their windows with rule, field and level (P1 §C, P3).
- **Out of scope**:
  - `recipes/bed-layout-plan-apply.yaml`: blocked follow-up (P12).
  - Geometric layout (rows, coordinates, drawings). The layout allocates area per bed, not positions.
  - Light, access and irrigation as placement rules: no species field records a crop's need (`site-analysis-and-crop-selection/en.md:77`, `species-baseline-verification/en.md:62`).
  - Changing the behaviour or MUSTs of `plant-planning` or `crop-rotation-planning`.
  - Any new validator rule.
  - Live measurement (D2).
  - Ownership and renaming questions (#39).
  - Multi-season layout.

## Route

- **Decision**: direct
- **Rationale**: One coherent outcome (reviewable succession and layout proposals), one PR strand on `feat/bed-layout-succession`, and no roadmap item (the repository has none), matching #42/#60 and #47/#70. The `-apply` half is split into its own blocked issue instead of being left unplanned.
- **Pipeline hand-off**: n/a

## Design defaults (resolved by default, operator may overturn)

1. **One spec, three skills** (H5): `companion-spacing-collect` reads; `succession-planning` and `bed-layout-planning` call no tool.
2. **One season per run.** The caller supplies `season`, a single year, which is passed to the rotation step as its one season. Windows are months. A run whose harvest end month falls before its first occupancy month, so that it wraps the year, gets occupancy `unknown — spans the season boundary`. No year is inferred.
3. **Beds** are the caller's entries `name:<n>m2` (a bed, by area) or `name:<n>l` (a container, by volume). `m²` is accepted as `m2`. Any other text gives capacity `unknown`, with the text copied verbatim. A bare `name` is a bed with unknown capacity. The format is compatible with the `beds` parameter of `garden-plan` and `crop-rotation-plan`.
4. **Bed attributes** come from the caller only, `bed_attributes`: semicolon-separated `bed:light=<text>`, `bed:access=<text>`, `bed:irrigation=<text>`. They are reported per bed and in each placement's rationale, and **form no rule** because no species field records a crop's light, access or water need. A caller who wants a rule uses `exclude=bed:species_key[:cultivar_key]`.
5. **Spacing** comes from the caller only, `spacing`: comma-separated `species_key[:cultivar_key]=<n>/m2` (plants per m², for beds) or `=<n>l` (litres per plant, for containers), with the cultivar entry before the species entry. **Quantities** come from the caller only, `quantities`: `species_key[:cultivar_key]=<plants>`. Area needed = plants ÷ density, or volume needed = plants × litres. When either is missing, the placement is `capacity not validated` and names the missing input. `sowing_density_per_m2` (level 4, unit semantics unrecorded) is shown as context only. Spacing from general knowledge is never used.
6. **Capacity** is validated per bed and per month. Each month, the sum of the area (or volume) of every run that occupies that bed in that month must not exceed the bed's capacity. Occupancy runs from the first sowing month (`direct_sow`) or the first transplant month (`indoor_then_transplant`) to the last harvest month; an unknown bound makes occupancy `unknown`, and the capacity for that month is then `not validated`. Result per bed and month: `within`, `over by <x>` (a conflict), or `not validated — <missing input>`.
7. **Companions.**
   - `compatible_companions[]` with `score` (level 4, read by `companion-spacing-collect`, the cultivar's list before the species list) is a ranking input only.
   - A numeric score counts toward the companion sum. A non-numeric score counts 0 and is listed as `score not comparable`. An unlisted pair is `unknown`.
   - The caller's `avoid=species_key[:cultivar_key]+species_key[:cultivar_key]` (semicolon-separated in `constraints`) is a hard constraint: two avoided crops never occupy the same bed in overlapping months.
   - The plan states verbatim that a companion pairing is a planning input from the catalog, not a guarantee of any outcome.
8. **Rotation is consumed, never re-derived.** In bed B for season S, only the crops listed in the rotation slot B/S, inside its selected family group or its pin, are admissible, and they keep the verdict the rotation plan gave them, copied with its level. A slot that is `open` or `occupied` admits nothing. A crop outside the slot is `not placed — outside rotation plan`. Rotation conflicts for season S are copied into `CONFLICTS`.
9. **Succession types.**
   - *(a) Sequential*: two runs whose crops are both admissible in the same rotation slot, where the earlier run's last harvest month comes before the later run's first occupancy month. This extends plant-planning's same-candidate rule to pairs of candidates in one slot. The within-candidate `precedes`/`follows` notes from plant-planning are carried over verbatim.
   - *(b) Staggered*: repeated sowings of one run inside its known sowing window, only with the caller's `stagger_weeks` (a whole number). The proposal lists the sowing dates as week offsets within the window's months, each citing the window's rule, field and level. Without `stagger_weeks` it says `staggering possible within <months> — interval not supplied`.
   - No succession is proposed from general knowledge, and months that cannot be compared give no succession.
10. **Placement procedure (deterministic).**
    - Beds are processed by name as text and runs by run identifier as text.
    - Hard admissibility comes first: the rotation slot, `exclude`, `avoid` against occupants in overlapping months, and the method chosen.
    - Rotation pins are placed first, in the pinned bed, even when capacity is exceeded, and the overrun is listed under `CONFLICTS` (a pin is never moved, as in `crop-rotation-planning/en.md:127`).
    - The other runs go to the first admissible bed, ranked by: validated capacity fits, ahead of capacity not validated; then the higher companion sum with occupants in overlapping months; then bed name.
    - A run that fits nowhere is `not placed — capacity`, with the shortfall.
    - Successions from the succession block are placed as chains in the same bed.
    - Neither the input order nor the current date decides a placement.
11. **Alternative methods.** When plant-planning offers the same species, cultivar and period under both methods (no `planting_method` given; `.claude/skills/plant-planning/SKILL.md`, Gotchas), the layout places neither and lists `method not chosen — set planting_method`. Different growing periods are separate plantings and are both considered.
12. **Output blocks.**
    - `succession-planning`: `SUCCESSION HEADER`, `SUCCESSIONS`, `NOT SUCCEEDED`, `APPLY CONTRACT`.
    - `bed-layout-planning`: `LAYOUT HEADER`, `BED LAYOUT` (per bed: capacity, attributes, placements with area and rationale), `CAPACITY` (per bed and month), `CONFLICTS`, `NOT PLACED`, `APPLY CONTRACT`.
    - Every placement and succession carries its rationale, confidence, uncertainty and missing data per `decision-policy`, and a level of `caller` whenever any element comes from the caller.
13. **#55 compliance.**
    - The planners' APPLY CONTRACT template refers to "the twelve write and setup tools listed under Gotchas" and lists them only under `## Gotchas`, as `crop-rotation-planning/SKILL.md` does, so no new `SKILL_LINE_ALLOWANCES` entry is needed.
    - `companion-spacing-collect` names all twelve in a `Forbidden by name:` block in its hard rules.
    - No new skill names `diary-analysis-claim`, or any other permitting skill, in its instruction text.
14. **No new validator check.** The existing checks cover the new artefacts: recipe completeness, `env_keys`, prompt, the skill completeness check, and the #55 obedience and permitting-load checks after the merge.
15. **The stale "Depends on #3 and #4"** is treated as not blocking and mentioned in the PR.

## Work packages

### P1 — Process spec for bed layout and succession planning

- **Problem statement**: The layout and succession steps need one authoritative spec that states inputs, sources, rules, output blocks, determinism and the apply contract, without restating policy or rotation.
- **Acceptance criteria**:
  - `spec/process/bed-layout-and-succession-planning/en.md` and `de.md` exist, `Status: draft`, `Portfolio-Scope: local`, with the sections of the sibling specs (Context, Goals, Non-Goals, Requirements A–G, Acceptance Criteria, Source, Open Questions).
  - §A, inputs table: planting runs (plant-planning), rotation plan (crop-rotation-planning), beds, bed attributes, spacing, quantities, `stagger_weeks`, `avoid` and `exclude` constraints, season (all source `caller`), `compatible_companions[]` with score and `sowing_density_per_m2` (level 4). Each has a "Not established" column.
  - §B covers the reading of companions and density. §C covers succession (defaults 8, 9). §D covers layout and capacity (defaults 3–7, 10, 11). §E covers the output blocks and consumers (default 12). §F covers determinism. §G covers the apply contract, naming the twelve tools and the follow-up issue.
  - The Context states "Nothing here was re-measured … `INVALID_CONFIG`".
  - The en and de files have the same headings in the same order, the same number of requirement bullets and the same number of acceptance checkboxes.
  - Every tool claim cites `spec/mcp/kamerplanter-mcp-server/en.md` or `spec/process/species-baseline-verification/en.md`.
- **Touched files / artifacts**: `spec/process/bed-layout-and-succession-planning/en.md`, `spec/process/bed-layout-and-succession-planning/de.md`
- **Specialist**: `nolte-shared:spec` (resolved at runtime: `/home/nolte/repos/github/claude-shared/skills/spec/SKILL.md`, "Creates, translates, indexes … multilingual specifications stored under the project's spec/ folder")
- **Depends on**: none (the follow-up issue number from P12 replaces the placeholder `#<NEW>` before the PR)

### P2 — Reading skill `companion-spacing-collect`

- **Problem statement**: The layout needs each crop's companion list with score, and the seed density as context, read once per distinct species from the catalog, so the planner can stay tool-free.
- **Acceptance criteria**:
  - `.claude/skills/companion-spacing-collect/SKILL.md` calls only `mcp__kamerplanter__get_species_info`, with `include_cultivars` when a cultivar is named, once per distinct species.
  - It reports per crop (`species_key/cultivar_key`): `compatible_companions[]` with `score` as recorded, `seed_profile.sowing_density_per_m2` as context, and the origin of each attribute (cultivar or species). An absent field is `absent — not populated`.
  - It never infers incompatibility and never supplies spacing.
  - Its hard rules contain a `Forbidden by name:` block with all twelve state-changing tools, and no other state-changing name appears in its instruction text.
  - It names no permitting skill.
  - `tests/validate_recipes.py` passes on this branch and on a trial merge with the #55 branch.
- **Touched files / artifacts**: `.claude/skills/companion-spacing-collect/SKILL.md`
- **Specialist**: no matching specialised agent — generalist remediation. No claude-shared skill or agent matches a Goose garden skill, and `nolte-claude-dev:skill-management` scaffolds under a plugin root, not this repository's `.claude/skills/` (as found for PR #60 and #47).
- **Depends on**: P1

### P3 — Tool-free skill `succession-planning`

- **Problem statement**: Sequential and staggered planting opportunities must be identified from the plan's calendar windows and the rotation slots, without inventing dates or breaking rotation.
- **Acceptance criteria**:
  - The skill calls no tool. Its inputs are the plant-planning block, the rotation-plan block, and the caller's `season` and `stagger_weeks`.
  - It produces the sequential and staggered successions of default 9. Every succession names both run identifiers and copies each window used, with its rule, fields, source and level, and carries over plant-planning's within-candidate notes.
  - Admissibility follows default 8. Each rejected opportunity goes to `NOT SUCCEEDED` with one reason.
  - Its blocks follow default 12. The APPLY CONTRACT refers to the Gotchas list (default 13).
  - It names no state-changing tool in its instruction text and passes the #55 trial merge.
- **Touched files / artifacts**: `.claude/skills/succession-planning/SKILL.md`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P1

### P4 — Tool-free skill `bed-layout-planning`

- **Problem statement**: Runs and successions must be allocated to the caller's beds with validated capacity, honouring rotation, constraints and companions, and every decision must be explainable.
- **Acceptance criteria**:
  - The skill calls no tool. Its inputs are the plant-planning, rotation-plan, succession and companion-spacing blocks and the caller's inputs.
  - It implements defaults 3–8, 10 and 11: per bed and month a capacity of `within`, `over by <x>` or `not validated — <missing>`. A placement exists only in a rotation-admissible slot. Pins are never moved. `avoid` is enforced, and an unlisted companion pair is `unknown`. The blocks follow default 12.
  - Every placement has a rationale stating the ranking values, the beds not chosen and why, the bed attributes as context, and the companion statement "input, not a guarantee". Every run that is not placed has one reason.
  - The skill passes the #55 trial merge.
- **Touched files / artifacts**: `.claude/skills/bed-layout-planning/SKILL.md`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P1, P3 (it consumes the succession block format)

### P5 — Read-only recipe `succession-plan`

- **Problem statement**: A person needs a headless run that proposes successions for one garden and season.
- **Acceptance criteria**:
  - `recipes/succession-plan.yaml` has no `extensions:` block. Its `description` says "Read-only", names the working directory, and says the measured catalog has no tool to apply the result.
  - Parameters: `tenant`, `crops` (required), `season` (required), `beds`, `bed_history`, `rotation_years`, `demand_sequence`, `constraints`, `harvest_window`, `planting_method`, `stagger_weeks`, plus the site parameters of `garden-plan`.
  - The prompt loads, in order, `garden-context`, `site-analysis`, `crop-selection`, `decision-policy`, `planting-calendar`, `plant-planning`, `rotation-history-collect`, `crop-rotation-planning` and `succession-planning`. Each load is reported as a step result.
  - The prompt carries `Forbidden by name:` with all twelve `mcp__kamerplanter__*` tools and a Home Assistant prohibition.
  - The run closes with a fixed table and the lines `SUCCESSION: <s> successions, <u> unknown — <slug>` and `APPLY: no write tool measured (nolte/kamerplanter-goose#<NEW>)`.
  - `goose recipe validate` passes, and so does `tests/validate_recipes.py`, including the #55 permitting-load check.
- **Touched files / artifacts**: `recipes/succession-plan.yaml`
- **Specialist**: no matching specialised agent — generalist remediation. `nolte-goose:recipe-implement` needs a plan from `nolte-goose:recipe-plan`, which needs a recipe requirement artifact, and none exists under D1. The independent check is `nolte-goose:recipe-audit` in P11.
- **Depends on**: P3

### P6 — Read-only recipe `bed-layout-plan`

- **Problem statement**: A person needs a headless run that proposes a bed layout for one garden and season and states what applying it would take.
- **Acceptance criteria**:
  - It has the same shape as P5, with the additional parameters `bed_attributes`, `spacing` and `quantities`.
  - The prompt additionally loads `companion-spacing-collect` and `bed-layout-planning`, eleven skills in all.
  - The final table has one row per bed and placement. The run closes with the lines `LAYOUT: <p> placements, <o> over capacity, <n> not validated — <slug>` and `APPLY: no write tool measured (nolte/kamerplanter-goose#<NEW>)`.
  - The `description` names `bed-layout-plan-apply` as tracked in the follow-up issue.
  - `goose recipe validate` and `tests/validate_recipes.py` pass.
  - `goose run --recipe bed-layout-plan --explain` lists the parameters without a model call.
- **Touched files / artifacts**: `recipes/bed-layout-plan.yaml`
- **Specialist**: no matching specialised agent — generalist remediation (see P5)
- **Depends on**: P2, P3, P4

### P7 — Cross-references in the dependent specs

- **Problem statement**: The plant-planning and crop-rotation specs refer to #46 as future work and must point at the new spec.
- **Acceptance criteria**:
  - `spec/process/plant-planning-and-planting-calendar/{en,de}.md`: the Boundaries (line 14), the Non-Goals (line 30) and the consumer table (line 89) link to the new spec. The Open Question at line 146 is answered: the layout carries the rotation verdict per placement and the plan's runs stay `rotation: unknown`.
  - `spec/process/crop-rotation-planning/{en,de}.md`: the Boundaries (line 16), the Non-Goals (line 32) and the consumer row (line 145) link to the new spec.
  - No MUST of either spec changes. en and de stay structurally equal.
- **Touched files / artifacts**: `spec/process/plant-planning-and-planting-calendar/en.md`, `spec/process/plant-planning-and-planting-calendar/de.md`, `spec/process/crop-rotation-planning/en.md`, `spec/process/crop-rotation-planning/de.md`
- **Specialist**: `nolte-shared:spec`
- **Depends on**: P1

### P8 — Guides

- **Problem statement**: Plant owners and recipe authors need how-to pages for both recipes, in both languages.
- **Acceptance criteria**:
  - `docs/{en,de}/guides/succession-plan.md` and `docs/{en,de}/guides/bed-layout-plan.md` exist, with frontmatter like `crop-rotation-plan.md` (`audience: [plant-owner, recipe-author]`, `content_mode: how-to`, `track: user-docs`).
  - Each page carries:
    - a "Not yet run against a live instance" note;
    - a working-directory warning;
    - a run example and a parameter table;
    - how to supply the beds, spacing, quantities and `avoid`;
    - what "not validated" means;
    - that companions are an input, not a guarantee;
    - what the plan does not do (apply, geometry, light, access and irrigation rules).
  - Both languages have the same sections, and `mkdocs build --strict` passes.
- **Touched files / artifacts**: `docs/en/guides/succession-plan.md`, `docs/de/guides/succession-plan.md`, `docs/en/guides/bed-layout-plan.md`, `docs/de/guides/bed-layout-plan.md`
- **Specialist**: `nolte-shared:audience-doc-author` (resolved at runtime: `/home/nolte/repos/github/claude-shared/agents/audience-doc-author.md`, drafts MkDocs pages against an existing `audience-identify` artifact; `AUDIENCES.md` is one)
- **Depends on**: P5, P6

### P9 — Bookkeeping

- **Problem statement**: The new skills, recipes and guides must be discoverable in the repository's indexes and nav.
- **Acceptance criteria**:
  - The CLAUDE.md garden-procedure list names all three skills, with `succession-planning` and `bed-layout-planning` among the tool-free exceptions.
  - `mkdocs.yml` has two Guides nav entries and their DE translations ("Succession plan: Folgesaatplan", "Bed layout plan: Beetplan").
  - `docs/{en,de}/guides/index.md` list both guides. `docs/{en,de}/references/index.md` list both recipes (writes: no) and the three skills.
  - `spec/README.md` is regenerated with the `spec` skill, not hand-edited.
  - `mkdocs build --strict` passes.
- **Touched files / artifacts**: `CLAUDE.md`, `mkdocs.yml`, `docs/en/guides/index.md`, `docs/de/guides/index.md`, `docs/en/references/index.md`, `docs/de/references/index.md`, `spec/README.md`
- **Specialist**: no matching specialised agent — generalist remediation; `nolte-shared:spec` for the `spec/README.md` index
- **Depends on**: P2, P3, P4, P5, P6, P8

### P10 — Determinism measurement of both planners

- **Problem statement**: The spec claims identical plan facts over identical blocks. This must be shown on a fixed fixture, as in PR #60 and #47.
- **Acceptance criteria**:
  - A fixed text fixture with invented keys:
    - three beds: one in `m2` with spacing and quantity, one with no area, one container in `l`;
    - a rotation plan with one pinned slot whose pin exceeds capacity and one `open` slot;
    - a crop offered under two methods, and a crop with two growing periods;
    - one `avoid` pair, a non-numeric companion score, one `stagger_weeks` variant and one variant without it.
  - Ten headless runs of each planner give identical plan facts: placements, areas, capacity per month, conflicts, not-placed reasons, successions and levels.
  - Ambiguities found are fixed in P3 or P4, and a final series of ten is identical.
  - The PR body states that this is a fixture result and not a live garden.
- **Touched files / artifacts**: none in the repository (fixture in the scratchpad, results in the PR body)
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P3, P4

### P11 — Quality gate, recipe audit, #55 trial merge

- **Problem statement**: The change must pass the CI gate, an independent recipe audit and the #55 guard before the PR.
- **Acceptance criteria**:
  - `task check` passes: the validator with `--self-test`, lint and `mkdocs build --strict`.
  - A trial merge of the branch head with `fix/skill-instruction-separation` (containing `21bd577`), in a throwaway clone, passes `tests/validate_recipes.py` and `--self-test`.
  - `nolte-goose:recipe-audit` runs on `succession-plan` and `bed-layout-plan`. Findings are fixed or recorded in the PR body, and the recipes are not changed after the audited runs.
  - The turn count of one `bed-layout-plan --explain` and dry review is recorded, because the recipe loads eleven skills.
  - SHOULD: one `domain-review` with `persona=outdoor-gardener` on `recipes/bed-layout-plan.yaml`.
- **Touched files / artifacts**: none (fixes land in the files of the owning package)
- **Specialist**: `nolte-goose:recipe-audit` (resolved at runtime: `~/.claude/plugins/cache/nolte-goose/nolte-goose/f91f3df26194/skills/recipe-audit`), with a generalist for the gate run and the trial merge
- **Depends on**: P5, P6, P7, P8, P9, P10

### P12 — Draft the blocked follow-up issue for `bed-layout-plan-apply`

- **Problem statement**: The issue asks for `bed-layout-plan-apply.yaml`, and no write tool exists for it (D4). It must be tracked, not dropped.
- **Acceptance criteria**:
  - The operator or orchestrator files the draft below (a GitHub write), or alternatively appends its scope to #68 and records that choice.
  - The resulting number replaces `#<NEW>` in P1, P3, P4, P5 and P6 before the PR opens.
  - The PR says "Closes #46" with the split stated and "Refs #<NEW>".
- **Touched files / artifacts**: none
- **Specialist**: no matching specialised agent — operator (issue creation)
- **Depends on**: P1

**Draft — title:** `Add the -apply recipe for bed layouts (blocked: no write tool for bed assignments or planting runs)`

**Draft — body:**

> ## Goal
>
> Add `recipes/bed-layout-plan-apply.yaml`, which takes an approved `bed-layout-plan` and records it in Kamerplanter: the beds, the placements of planting runs per bed, and the planned successions.
>
> ## Why it is blocked
>
> The measured Kamerplanter MCP catalog (`spec/mcp/kamerplanter-mcp-server/en.md`, 56 tools as of 2026-08-16, not re-measured since) records eleven `mcp.write` tools (`add_plant_diary_entry`, `confirm_care_task`, `archive_plant`, `set_plant_location`, `claim_diary_analysis`, `submit_diary_analysis`, `transition_plant_phase`, `assign_species_phase_sequence`, `assign_nutrient_plan`, `record_feeding_event`, `create_inspection`) and one `mcp.setup` tool (`create_site`). None of them creates a bed, records a bed assignment or a layout, or creates a planting run. `set_plant_location` moves a plant that already exists, while a layout places crops that are not plants yet. `create_site` creates a site root, not a bed with an area. This is the same blocker as #59 (garden and season plans) and #68 (crop rotation plans).
>
> ## Unblocks when
>
> A `tools/list` against a reachable instance shows a tool that creates a planting run or records a bed assignment, and the server spec records it.
>
> ## Acceptance criteria
>
> - [ ] The recipe takes an approved plan, not a fresh one, and applies only what the plan's `APPLY CONTRACT` lists
> - [ ] Its `description` opens with `WRITES to …`; its prompt carries `Permitted by name:` and `Forbidden by name:` blocks covering all state-changing tools
> - [ ] Every write is first called with `dry_run: true` and carries an `idempotency_key`
> - [ ] `mcp_permissions` from `list_tenants` is checked before any write
>
> ## Related
>
> - #46 (the read-only half), #59, #68, #55

## Dependency ordering

```
P1 ─► P2 ─────────────┐
P1 ─► P3 ─► P4 ───────┼─► P6 ─┐
       P3 ─► P5 ──────────────┼─► P8 ─► P9 ─► P11
P1 ─► P7 ──────────────────────────────────► P11
P3, P4 ─► P10 ─────────────────────────────► P11
P1 ─► P12 (operator; the number is needed before P1/P4/P5/P6 are final)
```

Dispatch order: P1 → {P2, P3, P7, P12} → P4 (after P3) and P5 (after P3) → P6 (after P2, P4) and P10 (after P3, P4) → P8 → P9 → P11.

## Risks

- **The base branch is unmerged (PR #70, #47).** P6 and P7 consume and edit #47's blocks and spec. A review fix on #70 forces a rebase here. Mitigation: freeze on `f24cc8a`, rebase after #70 merges, and re-run P11.
- **#55 is unmerged (PR #69).** The branch must pass both today's validator and the #55 guard. Mitigation: the P11 trial merge; follow the Gotchas pattern of default 13, and add no `SKILL_LINE_ALLOWANCES` entry.
- **Merge conflicts in shared indexes.** PR #67 and #69 touch `CLAUDE.md`, `mkdocs.yml` and the reference indexes. Mitigation: do P9 last and rebase before the PR.
- **Context and turn budget.** `bed-layout-plan` loads eleven skills in one context. Mitigation: measure in P11. If it is too heavy, fall back to running the rotation step only when `bed_history`, `rotation_years` or `constraints` are supplied. This is an operator decision; until then it is recorded, not built.
- **Mostly-unknown output.** With no caller spacing or quantities, every capacity is `not validated`. That is the honest result; the guides must say how to supply them.
- **Unrecorded meaning of `score` and `sowing_density_per_m2`.** Mitigation: rank by `score` only where it is numeric, and use density only as context (defaults 5, 7).
- **Security**: no credential or write path is touched, so no `security-review` is required. The recipes inherit the shared `extensions.yaml`.

## Open questions

All are resolved by default for this autonomous run; the operator may overturn them.

1. **One spec or two.** → One spec, three skills (H5). *Resolved by default, operator may overturn.*
2. **Spacing source.** → Caller only. `sowing_density_per_m2` is context; no level-8 spacing (default 5). *Resolved by default, operator may overturn.*
3. **Light, access and irrigation as rules.** → Reported only; `exclude=` is the rule mechanism (default 4). *Resolved by default, operator may overturn.*
4. **Companion semantics.** → A ranking input; `avoid=` is the only incompatibility (default 7). *Resolved by default, operator may overturn.*
5. **Succession across families in one bed and season.** → Not proposed; only crops admissible in the rotation slot (default 8). *Resolved by default, operator may overturn.*
6. **Alternative methods.** → Not placed until `planting_method` is set (default 11). *Resolved by default, operator may overturn.*
7. **Multi-season layout.** → Out of scope; one season per run (default 2). *Resolved by default, operator may overturn.*
8. **A separate follow-up issue or an extension of #68.** → A separate issue (P12 draft). *Resolved by default, operator may overturn.*
9. **Stale "Depends on #3 and #4".** → Not blocking; mentioned in the PR. *Resolved by default, operator may overturn.*

## Approval

- Pre-analysis approved 2026-11-05 under the operator's delegation ("arbeite die autonom ab"); route `direct`; defaults 1–15 and open questions 1–9 accepted as resolved by default.
- Base fast-forwarded to feat/crop-rotation-planning @c7752ac (PR #70), which removed the #47 artifact. #55 is PR #69 at 21bd577.
- P12: creating the follow-up issue was denied by the auto-mode classifier; the draft is at the orchestrator's scratchpad (issue-46-apply.md) for the operator. Until it exists, every `#<NEW>` reads "the blocked follow-up split out of #46" without a number.
- P10 cost bound: three runs per planner (not ten), on one fixture; record any divergence and fix ambiguities, without a second series.

## Dispatch log

<!-- Appended during operation 5. -->

- 2026-11-05 P1 done (generalist following `nolte-shared:spec`): `spec/process/bed-layout-and-succession-planning/{en,de}.md`, sections A–G; en/de 15 headings, 40 requirement bullets, 15 checkboxes each. §D refined during P4: two passes (pins first), and `not placed — no admissible bed` beside `not placed — capacity`.
- 2026-11-05 P2 done: `.claude/skills/companion-spacing-collect/SKILL.md`, `get_species_info` only, `Forbidden by name:` with all twelve.
- 2026-11-05 P3 done: `.claude/skills/succession-planning/SKILL.md`; refinement: the pinned crop of a slot is read from the caller's `pin=` entries, because the rotation block does not name it per slot.
- 2026-11-05 P4 done: `.claude/skills/bed-layout-planning/SKILL.md`; refinements: runs ordered by occupancy start month, then run identifier (so a sequential predecessor is always placed first); ranking key 1 is "bed holds the sequential predecessor"; the layout's beds are the `beds` entries plus every bed the rotation has a slot for (added after P10, not re-measured).
- 2026-11-05 P5/P6 done: `recipes/succession-plan.yaml` (9 skills), `recipes/bed-layout-plan.yaml` (11 skills); `goose recipe validate` and `--explain` pass. Deviation: the site-analysis free-text constraints are `site_constraints`, because `constraints` carries pin/exclude/avoid.
- 2026-11-05 P7 done: plant-planning and crop-rotation specs (en, de) link the new spec in Boundaries, Non-Goals and the consumer table; the plant-planning Open Question on rotation notes is answered. No MUST changed.
- 2026-11-05 P8/P9 done: four guides; CLAUDE.md, mkdocs nav (+DE), guide and reference indexes, `spec/README.md` regenerated (operation 4). The crop-rotation guides now link the two new guides instead of #46.
- 2026-11-05 P10 done: fixture in the scratchpad `p10-46/`, three headless runs per planner (`goose run --no-session -q`, provider claude-code, no extensions). Succession: 3/3 identical plan facts in both variants (stagger 2 / none), equal to the hand derivation. Layout: 3/3 identical plan facts, equal to the hand derivation; the fixture's own `COUNT n` was undefined and read as "not placed" in all three runs (fixture ambiguity; the recipe defines n). Observed: `goose run -q` moves long code blocks into `/tmp/goose-*.txt` (`... (N more lines → …)`), so a report can be truncated on stdout.
- 2026-11-05 P11 partial: validator (+`--self-test`), `mkdocs build --strict`, `pre-commit run --all-files` pass; trial merge with `21bd577` passes the validator including 23 skill-obedience and 12 permitting-load cases. Recipe audit not run (excluded by the orchestrator).
- 2026-11-05 P12 open: no follow-up issue number; every reference reads "the blocked follow-up split out of nolte/kamerplanter-goose#46".
- 2026-11-05 Review fixes (recipe-audit ×2 clean; independent review items 1–9): occupancy spans the season boundary also when a sowing or transplant month is higher than the highest harvest month, and staggered dates lie only inside a known occupancy; the layout's beds are the `beds` entries plus every rotation slot bed (capacity `unknown`, source `rotation plan`), now in spec §A/§D; method-not-chosen takes precedence over a pin (`pinned crop: method not chosen — set planting_method` under CONFLICTS); the pin clause admits before the selection and wins over `occupied`; `not placed — outside rotation plan` verbatim; `successor of` lists every predecessor, latest harvest end first; the score-direction sentence is a MUST and in the rationale template; guides explain `constraints` vs `site_constraints` and per-block staggering. P10 layout series 2 (fixture extended by a rotation-only bed and a sow-after-harvest run): 3/3 identical plan facts, equal to the hand derivation (p=8, o=5, n=28), except the excess format `1.00 m2` vs `1 m2` in two runs; the number format is now stated in the skill, not re-measured.
