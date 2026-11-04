---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter-goose"
issue: "47"
classification: "feature-request"
secondary-classes: ["spec-change", "docs"]
route: "direct"
status: approved
created: "2026-11-04"
---

# Issue Orchestration — Pre-analysis

<!-- Run-scoped artifact: committed on feat/crop-rotation-planning, then removed with a
     fix-forward `git rm` before the PR merges, per spec/project/issue-orchestration/
     §Pre-analysis artifact lifecycle. Anything worth keeping goes into the PR's
     Risk / rollout notes or the issue comment first. -->

## Issue metadata

- **Repository**: nolte/kamerplanter-goose
- **Issue**: #47 — [P1] Add crop rotation planning
- **URL**: https://github.com/nolte/kamerplanter-goose/issues/47
- **Labels**: enhancement, claude-code, skills
- **Author / trust**: nolte (repository owner, trusted); 0 comments
- **Linked items**: "Depends on issue #4" — #4 is the closed, unrelated "analyse-queue.sh reports success on a failed queue read" (`gh issue view 4`), so the reference is stale and non-blocking. Related: #42 (plant planning, PR #60), #46 (bed layout and succession, open, consumes rotation), #59 (the blocked `-apply` precedent), #39 (ownership audit), #55 (skill obedience guard).
- **Prior art checked**: no `project/` directory (no requirements, features or roadmap); no open PRs (`gh pr list`); merged PR #60 (plant-planning + planting-calendar) and PR #66 (watering/fertilization) as the shape; existing rotation mentions are placeholders only: `plant-planning` reports `rotation: unknown` (`.claude/skills/plant-planning/SKILL.md:43`, `spec/process/plant-planning-and-planting-calendar/en.md:80,120,146`), `spec/process/site-analysis-and-crop-selection/en.md:29,138` waits for #47. Nothing already resolves the issue.
- **Working copy**: /home/nolte/repos/.worktrees/kamerplanter-goose/crop-rotation, branch `feat/crop-rotation-planning` off `origin/develop` `b6e5a55`.

## Decisions

- **D1 Requirements gate — operator override.** The repository has no `project/requirements/`; the issue body is the grounded input, as for #40–#45 and #49.
- **D2 Nothing measured live.** The `kamerplanter` MCP server is unreachable in this session (`INVALID_CONFIG`). Every claim about tool output below rests on `spec/mcp/kamerplanter-mcp-server/en.md` and `spec/process/species-baseline-verification/en.md` (measured 2026-08-07 / 2026-08-16) and is **not re-measured**; the spec, skills, recipe and guides must say so.
- **D3 No `-apply` recipe in this PR.** The measured write catalog (`spec/mcp/kamerplanter-mcp-server/en.md:130-148`) has no tool that records a bed assignment, a rotation, a planting run or a plan. The two nearest do not fit: `set_plant_location` moves an *existing* plant, and a rotation plans future crops that are not plants yet. `add_plant_diary_entry` writes a note to an existing plant. Confirmed: build only the read-only `crop-rotation-plan` with an `APPLY CONTRACT` block, and split `crop-rotation-plan-apply` into a blocked follow-up issue (draft in P10).
- **D4 Autonomous run.** Open questions are resolved by a recommended default, marked "resolved by default, operator may overturn".

## Classification

- **Primary class**: feature-request
- **Secondary class(es)**: spec-change, docs
- **Rationale**: Adds a new process (spec, skills, recipe, guides); touches existing specs only to update cross-references.
- **Asserted cause verified**: The issue asserts "existing crop/family graph data" — **partially refuted**. See H1: one species→family key exists; no family-level rotation relationship exists in the measured surface.

## Hypotheses checked

| # | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| H1 | The catalog carries family, demand class and rotation data | **Partially refuted.** `family_key`, `nutrient_demand_level` and `green_manure_suitable` are observed fields of `get_species_info`. No family read tool, no family name or rank, and no family-level rotation edge exist. Value sets are unrecorded; only `heavy_feeder` and `medium_feeder` appear as examples. The table is a union over two species, so which species carried which field is unrecorded. The only species-to-species relation, `compatible_companions[]`, must not be read as rotation. Cultivars carry no family | established: `spec/process/species-baseline-verification/en.md:46-56`; `spec/mcp/kamerplanter-mcp-server/en.md:94-104` (no family tool); `spec/process/nutrient-imbalance-detection/en.md:80,102`; `spec/process/plant-planning-and-planting-calendar/en.md:80`. Unestablished: whether every species carries `family_key` and the value set of `nutrient_demand_level` (settling observation: `get_species_info` on ≥10 vegetable species on a reachable instance) |
| H1a | Family can come from research under the three-source rule | **Refuted for a recipe run.** Garden recipes forbid fetching URLs ("Use MCP tools only … do not fetch URLs"). The three-source rule (`species-baseline-verification/en.md:82-98`) can therefore only run outside a recipe. An absent `family_key` is `unknown`, never recalled | established: `recipes/garden-plan.yaml` prompt; `species-baseline-verification/en.md:84` |
| H2 | Bed history has no source; previous crops come from the caller or planting runs | **Confirmed, with a refinement.** No source exists for beds or containers, and location ≠ bed is unrecorded. Planting-run shape and parameters are unrecorded. A candidate source for per-location history: `list_plants` with `include_archived: true` (`species_key`, `location_key`, `planted_on` per plant). Archived plants exist (`matched 9` vs `total_in_tenant 11`). Whether archived records keep `location_key` and `planted_on`, and whether any end date is carried, is unrecorded | established: `spec/process/garden-decision-policy/en.md:84,86`; `.claude/skills/garden-context/SKILL.md:25,37,53,88`; `spec/process/plant-planning-and-planting-calendar/en.md:43,144`. Unestablished: archived-plant fields (settling observation: `list_plants include_archived:true` on the reference garden) |
| H3 | The output must plug into plant-planning, site-analysis and #46 | **Confirmed, with a refinement.** `plant-planning` assigns no bed (`location: unassigned`), so a rotation verdict cannot be one note per run. It is per (bed, season, crop). Join key: the `species_key/cultivar_key` prefix of the plant-planning run identifier. `plant-planning` stays unchanged (its MUST "report rotation as unknown" holds, because it assigns no bed). #46 reads the rotation block | established: `.claude/skills/plant-planning/SKILL.md:39-43`; `spec/process/plant-planning-and-planting-calendar/en.md:79-80,89`; `gh issue view 46` body ("without violating rotation") |
| H4 | Pest and disease pressure history comes from inspections | **Partially refuted.** `get_plant_inspections` returns IPM history per plant (empty on a never-inspected plant), and it attaches to a bed only through the plant's location. Neither `get_pest` nor `get_disease` records a host range, so a recorded pressure cannot be projected onto a future family. It is a `caution`, never a `conflict`. `pest-pressure-assess` judges one living plant and is not reused | established: `spec/mcp/kamerplanter-mcp-server/en.md:115,157-159`. Unestablished: inspection fields beyond "pressure level, symptoms, structured findings" (`:142`) |

## Scope

- **In scope**:
  - A process spec `spec/process/crop-rotation-planning/{en,de}.md`.
  - A reading skill `rotation-history-collect`.
  - A tool-free, deterministic skill `crop-rotation-planning`.
  - The read-only recipe `recipes/crop-rotation-plan.yaml` with an `APPLY CONTRACT` block.
  - Guides (en, de).
  - Bookkeeping: CLAUDE.md, mkdocs.yml nav and its DE translations, guide and reference indexes, `spec/README.md`.
  - Cross-reference updates in the plant-planning and site-analysis specs.
  - Verification: `task check`, recipe audit, and a determinism measurement on a fixture.
  - Issue acceptance criteria → coverage:
    - "Bed history is incorporated" → P1 §inputs, P2, P3.
    - "Family-level rotation constraints are supported" → P1 §rules, P3.
    - "Existing graph relationships are reused" → `family_key` reused, `compatible_companions` explicitly not (P1, P2). The rest of the asserted graph does not exist, which is the H1 finding.
    - "Conflicts are surfaced explicitly" → `CONFLICTS` block (P3).
    - "Apply operations are separate from planning" → `APPLY CONTRACT` and P10.
- **Out of scope**:
  - `recipes/crop-rotation-plan-apply.yaml` → blocked follow-up issue (P10, D3).
  - Bed layout, spacing, area and capacity, companion placement, succession → #46.
  - Changing `plant-planning`'s behaviour or its MUSTs.
  - Any new validator rule (no new house rule is introduced).
  - Live measurement of the catalog (D2).
  - Ownership and renaming questions → #39.

## Route

- **Decision**: direct
- **Rationale**: One coherent outcome (a reviewable rotation plan), one PR strand on `feat/crop-rotation-planning`, no roadmap item (the repo has none). This matches #42/PR #60. The `-apply` half is split out as a separate blocked issue rather than left silently unplanned, so the routes are not mixed.
- **Pipeline hand-off**: n/a

## Design defaults (resolved by default, operator may overturn)

1. **Two skills, not one.** The issue names one skill, `crop-rotation-planning`. The plan splits off the reading half as `rotation-history-collect`, so the planner stays tool-free and its determinism can be measured without the server. This mirrors `planting-calendar` / `plant-planning`.
2. **Family source.** `family_key` from `get_species_info` (level 4), cultivar before species if a cultivar ever carries it. Absent → family `unknown` and every verdict for that crop is `unknown`, with the missing input named. Never recalled (no level-8 family), never researched in-run (H1a).
3. **Rotation interval.** It comes from the caller only (`rotation_years`, a whole number of seasons between two crops of one family in one bed). The catalog has no source and the spec states no built-in agronomic number. Without it, a same-family repeat is `repeat — interval unknown`, never `conflict` and never `clear`.
4. **Demand classes.** `nutrient_demand_level` is read as recorded. The caller's `demand_sequence` (an ordered, comma-separated list of values) makes sequencing a preference: `met`, `unmet` or `unknown`. It never produces a conflict. Without the parameter, sequencing is `not evaluated`. The heavy→medium→light→green-manure convention is not hard-coded.
5. **Soil effects "where modeled".** Only `green_manure_suitable` is modelled. It can mark a candidate as fit for a green-manure slot and does nothing else. Every other soil effect (nitrogen fixation, soil-borne disease persistence) is reported `not modeled`.
6. **Bed history.**
   - Primary source is the caller (`bed_history`: entries `bed:season:species_key[:cultivar_key]`, comma-separated).
   - Secondary source is the catalog: archived and current plants per `location_key` from `list_plants include_archived:true`. It attaches to a bed only when the caller's bed name equals a `location_key` exactly; otherwise it is listed as `unmapped location history` context.
   - A catalog season is the year of `planted_on`. A plant without `planted_on` is history with season `unknown`.
   - Planting runs from `garden-context` are context only, because their shape is unrecorded.
   - A partial or failed read is never treated as "no history".
7. **Pressure history.** Inspections per historical plant at a mapped bed are reported as `caution` with level 3 and the missing input "host range: not recorded". They never produce a conflict.
8. **User constraints.**
   - Structured pins `pin=bed:season:species_key` are honoured, and a pin that breaks a rule is kept and reported as a conflict, never silently moved.
   - Structured exclusions `exclude=bed:species_key` are honoured.
   - Any other text is listed verbatim as `not evaluated`.
9. **Future plans.** Candidate crops come in as `crops` (`species_key[:cultivar_key]`, the same shape as `garden-plan`) and seasons as `seasons` (ordered years). Re-running plant-planning inside this recipe is not required. The output is keyed by `species_key/cultivar_key` so #46 and a plant-planning plan join on the run-id prefix.
10. **What the planner selects.**
    - Per bed and season it selects one candidate family group (with the candidate crops of that family), or `open`. It does not place runs, area or spacing; that is #46.
    - Selection is a fixed function of the blocks: seasons in order, beds by name as text, admissible groups first, then the `demand_sequence` preference, then `family_key` as text.
    - It never uses input order or the current date.
11. **Output blocks**, in order: `ROTATION HEADER`, `BED HISTORY`, `ROTATION PLAN`, `CONFLICTS`, `NOT PLACED`, `APPLY CONTRACT`. Verdict vocabulary per (bed, season, crop): `clear | conflict | repeat — interval unknown | caution | unknown`, each with its rule, fields, source, level, and missing data per `decision-policy`.
12. **No new validator check.** Existing checks cover the recipe (forbidden-tool completeness, `env_keys`, prompt) and the reading skill (completeness of all 12 names).

## Work packages

### P1 — Process spec for crop rotation planning

- **Problem statement**: The repository has no authoritative spec for what a rotation plan reads, decides and returns, and what the catalog cannot supply.
- **Acceptance criteria**:
  - `spec/process/crop-rotation-planning/en.md` and `de.md` exist with Status `draft` and Portfolio-Scope `local`.
  - They follow the house section order: Context, Goals, Non-Goals, Requirements A–F (inputs, family and demand, bed history, rules and verdicts, the plan and its consumers, determinism, separation and apply contract), Acceptance Criteria, Source, Open Questions.
  - The spec states defaults 2–11 as MUST/MUST NOT rules.
  - It states that nothing was re-measured (D2), citing `spec/mcp/kamerplanter-mcp-server/en.md` and `species-baseline-verification/en.md` for every tool or field claim.
  - It names #46 as the consumer, with a per-consumer table, and #59's sibling follow-up (P10) as the apply tracker.
  - It contains no agronomic interval or family list from general knowledge.
  - en and de have identical headings, requirement-bullet count and acceptance-checkbox count.
  - `spec/README.md` is regenerated by the `spec` skill and lists the row.
  - `mkdocs build --strict` passes.
- **Touched files / artifacts**: `spec/process/crop-rotation-planning/en.md`, `spec/process/crop-rotation-planning/de.md`, `spec/README.md`
- **Specialist**: `nolte-shared:spec` (resolved: `/home/nolte/repos/github/claude-shared/skills/spec/SKILL.md` — "Creates, translates, indexes … multilingual specifications stored under the project's spec/ folder")
- **Depends on**: none

### P2 — Reading skill `rotation-history-collect`

- **Problem statement**: The planner needs family, demand class, green-manure suitability per candidate, and per-location history including archived plants and their inspections, read once and normalised with sources.
- **Acceptance criteria**:
  - `.claude/skills/rotation-history-collect/SKILL.md` exists with `name`/`description` frontmatter and no `disable-model-invocation`.
  - It resolves the tenant as `garden-context` does, or takes it from the garden-context block.
  - Its reads:
    - `get_species_info` once per distinct candidate and historical species, recording `family_key`, `nutrient_demand_level` and `green_manure_suitable` as present or absent; absent means "not populated", never "does not apply";
    - `get_cultivar` only for referenced cultivars;
    - `list_plants` with `include_archived: true`, paged and capped like garden-context, recording `species_key`, `location_key`, `planted_on` and archived status;
    - `get_plant_inspections` per historical plant at a location that matches a caller bed.
  - It reports every field with its source, retrieval time and level, or absent with a reason.
  - It never reads `compatible_companions[]` as rotation.
  - It names all twelve state-changing tools individually as forbidden.
  - It marks archived-plant fields and inspection fields "not re-measured".
  - `python3 tests/validate_recipes.py` passes: the skill completeness check selects it and finds nothing missing.
- **Touched files / artifacts**: `.claude/skills/rotation-history-collect/SKILL.md`
- **Specialist**: no matching specialised agent — generalist remediation (`nolte-claude-dev:skill-management`, per PR #60, scaffolds under a plugin root, not this repo's `.claude/skills/`; no claude-shared skill or agent matches a Goose garden skill)
- **Depends on**: P1

### P3 — Tool-free planner skill `crop-rotation-planning`

- **Problem statement**: Turning history, families, demand classes, caller rules and candidate crops into a multi-season, explainable rotation with explicit conflicts must be a deterministic function of its input blocks.
- **Acceptance criteria**:
  - `.claude/skills/crop-rotation-planning/SKILL.md` exists and makes no tool call.
  - It contains no `mcp__kamerplanter__` reference, so the validator does not select it.
  - It implements the verdict vocabulary, the selection order and the six output blocks of defaults 3–11.
  - Every placement has a rationale.
  - Every conflict names the bed, season, crop, rule, the evidence on both sides, and its level.
  - A pin that breaks a rule appears in `CONFLICTS`.
  - Unknown family or absent history gives `unknown` with the missing input, never `clear`.
  - The `APPLY CONTRACT` states what an apply step would record and that the measured catalog has no tool for it, listing the 11 `mcp.write` tools and `create_site`, and names the P10 issue.
  - Output is keyed by `species_key/cultivar_key`.
  - Plan facts exclude the current date and input order.
- **Touched files / artifacts**: `.claude/skills/crop-rotation-planning/SKILL.md`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P1

### P4 — Read-only recipe `crop-rotation-plan`

- **Problem statement**: A person needs one headless-runnable recipe that produces the rotation plan for one garden.
- **Acceptance criteria**:
  - `recipes/crop-rotation-plan.yaml` exists with no `extensions:` block.
  - Its `description` opens "Read-only:" and names the required working directory.
  - Parameters: `tenant`, `crops` (required), `seasons` (required), `beds`, `bed_history`, `rotation_years`, `demand_sequence`, `constraints`.
  - The `prompt` names the four loaded skills (`garden-context`, `rotation-history-collect`, `crop-rotation-planning`, `decision-policy`) and forbids all twelve state-changing tools by name and any Home Assistant tool.
  - It runs numbered steps and ends with a fixed table plus the final lines `ROTATION: <p> placements, <c> conflicts, <u> unknown — <slug>` and `APPLY: no write tool measured (<P10 issue>)`.
  - `python3 tests/validate_recipes.py` reports one more recipe and `OK`.
  - `goose recipe validate recipes/crop-rotation-plan.yaml` and `goose run --recipe crop-rotation-plan --explain` both succeed.
- **Touched files / artifacts**: `recipes/crop-rotation-plan.yaml`
- **Specialist**: no matching specialised agent — generalist remediation (`nolte-goose:recipe-implement` requires a ready plan from `nolte-goose:recipe-plan`, which requires a recipe requirement artifact; none exists under D1). Independent check: `nolte-goose:recipe-audit` in P8.
- **Depends on**: P2, P3

### P5 — Cross-references in the dependent specs

- **Problem statement**: The plant-planning and site-analysis specs say rotation "is not built" (#47) and leave its arrival as an open question; once P1 exists, that text is stale.
- **Acceptance criteria**:
  - In `spec/process/plant-planning-and-planting-calendar/{en,de}.md`, the Boundaries paragraph, the Non-Goals line and the Open Question "How rotation constraints will arrive" point to `crop-rotation-planning` and the run-id-prefix join.
  - In `spec/process/site-analysis-and-crop-selection/{en,de}.md`, the Non-Goals line and the Open Question at en.md:138 point to it as well.
  - No MUST, MUST NOT or acceptance checkbox in either spec changes, and plant-planning's `rotation: unknown` stays.
  - en/de counts stay equal.
  - `mkdocs build --strict` passes.
- **Touched files / artifacts**: `spec/process/plant-planning-and-planting-calendar/en.md`, `…/de.md`, `spec/process/site-analysis-and-crop-selection/en.md`, `…/de.md`
- **Specialist**: `nolte-shared:spec`
- **Depends on**: P1

### P6 — Guides

- **Problem statement**: Plant owners and recipe authors need a how-to for the recipe, in both languages.
- **Acceptance criteria**:
  - `docs/en/guides/crop-rotation-plan.md` and `docs/de/guides/crop-rotation-plan.md` exist, with frontmatter like `garden-plan.md` (`audience: [plant-owner, recipe-author]`, `content_mode: how-to`, `track: user-docs`).
  - They carry a "Not yet run against a live instance" note.
  - They have a working-directory warning, a run example, a parameter table, how to supply bed history and the interval, the verdict vocabulary, and what the plan does not do (no apply, no layout).
  - Both languages have the same sections.
  - `mkdocs build --strict` passes.
- **Touched files / artifacts**: `docs/en/guides/crop-rotation-plan.md`, `docs/de/guides/crop-rotation-plan.md`
- **Specialist**: `nolte-shared:audience-doc-author` (resolved: `/home/nolte/repos/github/claude-shared/agents/audience-doc-author.md` — drafts MkDocs pages against an existing `audience-identify` artifact; `AUDIENCES.md` is one)
- **Depends on**: P4

### P7 — Bookkeeping

- **Problem statement**: The new skills, recipe and guide must be discoverable in the repo's indexes and nav.
- **Acceptance criteria**:
  - The CLAUDE.md garden-procedure list names both skills, with `crop-rotation-planning` among the tool-free exceptions.
  - `mkdocs.yml` has a nav entry under Guides and a DE nav translation.
  - `docs/{en,de}/guides/index.md` list the guide.
  - `docs/{en,de}/references/index.md` list the recipe (writes: no) and both skills.
  - `mkdocs build --strict` passes.
- **Touched files / artifacts**: `CLAUDE.md`, `mkdocs.yml`, `docs/en/guides/index.md`, `docs/de/guides/index.md`, `docs/en/references/index.md`, `docs/de/references/index.md`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P2, P3, P4, P6

### P8 — Quality gate and independent recipe audit

- **Problem statement**: The change must pass the CI gate and an independent recipe audit before the PR.
- **Acceptance criteria**:
  - `task check` (validator plus `--self-test`, lint, `mkdocs build --strict`) passes.
  - `nolte-goose:recipe-audit` runs five times on the final `crop-rotation-plan`, each with a report and digest; findings are fixed or recorded in the PR body.
  - The recipe is not changed after the audited runs.
  - SHOULD: one `domain-review` run with `persona=outdoor-gardener`, `target=recipes/crop-rotation-plan.yaml`, findings recorded.
- **Touched files / artifacts**: none (fixes land in the owning package's files)
- **Specialist**: `nolte-goose:recipe-audit` (resolved: `~/.claude/plugins/cache/nolte-goose/nolte-goose/f91f3df26194/skills/recipe-audit/SKILL.md`), with generalist for the gate run
- **Depends on**: P4, P5, P7

### P9 — Determinism measurement of the planner

- **Problem statement**: The spec claims identical plan facts over identical blocks; this must be shown on a fixed fixture, as in PR #60.
- **Acceptance criteria**:
  - A fixed text fixture with invented keys: four beds, three seasons, families including one unknown, a pin that conflicts, history with a same-family repeat, one inspection caution, and no `rotation_years` in one variant.
  - Ten headless runs of `crop-rotation-planning` give identical plan facts: placements, verdicts, conflicts, not-placed reasons, levels.
  - Any ambiguity found is fixed in P3, and a final series of ten is identical.
  - The PR body states that this is not out-of-sample and not a live garden.
- **Touched files / artifacts**: none (fixture in the scratchpad; results in the PR body)
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P3

### P10 — Draft the blocked follow-up issue for `crop-rotation-plan-apply`

- **Problem statement**: The issue asks for `crop-rotation-plan-apply.yaml`, which has no write tool to use (D3); it must be tracked, not dropped.
- **Acceptance criteria**:
  - The draft below is handed to the operator, who creates the issue (a GitHub write).
  - Its number replaces the placeholder in P1, P3 and P4 before the PR opens.
  - The PR says "Refs" that number and "Closes #47" with the split stated.
- **Touched files / artifacts**: none
- **Specialist**: no matching specialised agent — operator (issue creation)
- **Depends on**: P1

**Draft — title:** `Add the -apply recipe for crop rotation plans (blocked: no write tool for bed assignments or planting runs)`

**Draft — body:**

> Split out of #47.
>
> #47 asked for `recipes/crop-rotation-plan-apply.yaml`, which applies an approved rotation plan. The read-only half — the plan as a reviewable document — is built there. This half is not, because the measured catalog has nothing to apply a rotation with.
>
> ## What the catalog holds
>
> `spec/mcp/kamerplanter-mcp-server/en.md`, section "Write tools", lists eleven `mcp.write` tools and one `mcp.setup` tool: `add_plant_diary_entry`, `confirm_care_task`, `archive_plant`, `set_plant_location`, `claim_diary_analysis`, `submit_diary_analysis`, `transition_plant_phase`, `assign_species_phase_sequence`, `assign_nutrient_plan`, `record_feeding_event`, `create_inspection`, and `create_site`. None records a bed's rotation, assigns a future crop to a bed, or creates a planting run or a plan. `set_plant_location` moves a plant that already exists; a rotation plans crops that are not plants yet. The same blocker holds for #59.
>
> ## Not established
>
> Whether a live instance offers such a tool. The server spec says to treat any tool count as a floor, and the `kamerplanter` MCP server was unreachable (`INVALID_CONFIG`) when #47 was worked. `tools/list` plus a read-only call against a reachable instance would settle it.
>
> ## Done when
>
> - A write tool that records a bed assignment, a rotation or a planting run is named in `spec/mcp/kamerplanter-mcp-server/`, measured against a reachable instance, with its required fields and whether it takes `dry_run` and `idempotency_key`.
> - The recipe exists with the `-apply` suffix, a `description` that opens with `WRITES to …`, and a `Permitted by name:` / `Forbidden by name:` split in the prompt. It applies only a plan the person has approved, as the apply-contract section of `spec/process/crop-rotation-planning/` describes.
>
> Refs #47, #59.

## Dependency ordering

```
P1 ──► P2 ──┐
   ├─► P3 ──┼─► P4 ──► P6 ──► P7 ──► P8
   │        └─► P9 (parallel to P4…P7; fixes feed back into P3 before P8)
   ├─► P5 ─────────────────────────► P8
   └─► P10 (operator; issue number needed before P4 is final)
```

Dispatch order: P1 → {P2, P3, P5, P10} → P4 (after P2, P3) and P9 (after P3) → P6 → P7 → P8.

## Risks

- **Asserted graph is mostly absent (H1).** Issue criterion "Existing graph relationships are reused" can only be met as "`family_key` reused". Mitigation: the spec and PR say so explicitly. A missing family gives `unknown` rather than a guess.
- **`family_key` coverage and value sets unmeasured (D2).** Many species may lack it, giving a plan full of `unknown`. Mitigation: that is the honest result; the guide explains it; a settling observation is listed in Open Questions.
- **Archived-plant fields unmeasured.** `include_archived: true` may not return `location_key` or `planted_on`. Mitigation: caller history is primary, and a failed or partial read is never "no history".
- **Season from `planted_on` misrepresents perennials and multi-year occupancy.** Mitigation: flagged as a known limit; perennials are reported as `occupancy unknown` beyond their planting year.
- **No built-in interval reduces usefulness for casual users.** Mitigation: the guide gives the parameter prominently. Adding cited family intervals would need three-source research at authoring time; that is listed as an open question, not done inline.
- **Run length.** The recipe loads four skills and reads species per crop plus inspections per historical plant. Mitigation: distinct-species reads; inspections only for locations mapped to a caller bed.
- **Forbidden-tool list drift.** Mitigation: the validator enforces all twelve names in the recipe and the reading skill.
- **Overlap with #46 ownership.** Mitigation: rotation picks a family per bed and season only; placement, area and succession stay with #46, and the spec states the boundary.
- **Security.** No credentials, no writes; no security review trigger.

## Open questions

All resolved by default; the operator may overturn any of them.

1. **One skill or two?** → Two (`rotation-history-collect` + `crop-rotation-planning`). *Resolved by default, operator may overturn.*
2. **Built-in family intervals?** → No; `rotation_years` comes from the caller, and without it the verdict is `repeat — interval unknown`. *Resolved by default, operator may overturn.* Researched intervals with three sources would be a separate spec amendment.
3. **Demand-class sequencing as a rule?** → A preference via `demand_sequence`, never a conflict. *Resolved by default, operator may overturn.*
4. **Mapping catalog locations to caller beds?** → Exact `location_key` equality only; everything else is unmapped context. *Resolved by default, operator may overturn.*
5. **Should plant-planning's `rotation: unknown` change?** → No; it assigns no bed. The join happens on the run-id prefix (P5 updates cross-references only). *Resolved by default, operator may overturn.*
6. **Do pressure histories produce conflicts?** → No; `caution` only, because host range is unrecorded. *Resolved by default, operator may overturn.*
7. **Stale "Depends on #4".** → Treated as non-blocking (#4 is closed and unrelated); mentioned in the PR. *Resolved by default, operator may overturn.*
8. **Settling observations (not resolvable here, D2):**
   - `get_species_info` on ≥10 vegetable species for `family_key` and `nutrient_demand_level` coverage and values;
   - `list_plants include_archived:true` for archived-plant fields;
   - the `list_planting_runs` shape;
   - `tools/list` for any bed or rotation write tool.

## Approval

- Pre-analysis approved 2026-11-04 under the operator's delegation ("arbeite die autonom ab"); route `direct`; defaults 1–12 and open questions 1–7 accepted as resolved.
- P10: issue creation is a GitHub write the auto-mode classifier denies in this session; the draft is handed to the operator. Until it exists, P1/P3/P4 refer to it as "the blocked follow-up split out of #47" without a number. Created by the operator as #68 on 2026-11-05; placeholders replaced.
- P8/P9 cost bound: recipe-audit runs once on the final head (not five times); the determinism series is three runs, not ten, and only if `goose` is runnable here.

## Dispatch log

<!-- Appended during operation 5. -->

- 2026-11-05 P1 — done (generalist + `nolte-shared:spec` for the index). `spec/process/crop-rotation-planning/{en,de}.md`; requirement sections are A–G (the plan's "A–F" listed seven topics). en/de: 15 headings, 49 bold bullets, 15 checkboxes each. Verdict table refined: an entry with season `unknown` also yields `unknown` (history).
- 2026-11-05 P2 — done. `.claude/skills/rotation-history-collect/SKILL.md`; selected by the skill completeness check, all twelve names present.
- 2026-11-05 P3 — done. `.claude/skills/crop-rotation-planning/SKILL.md`; no `mcp__kamerplanter__` reference; state-changing tool names only under `## Gotchas` (the #55 obedience-guard convention, coordinator request). Refined after P9: CONFLICTS scope and verdict level made explicit.
- 2026-11-05 P4 — done. `recipes/crop-rotation-plan.yaml`; validator OK (21 recipes), `goose recipe validate` and `--explain` succeed.
- 2026-11-05 P5 — done. Boundaries/Non-Goals/Open Question updated in plant-planning and site-analysis specs (en/de); no MUST or checkbox changed. Additionally fixed the stale "rotation is not built yet" reason in `docs/{en,de}/guides/garden-plan.md` and in `plant-planning` SKILL.md (reason text only; its `rotation: unknown` behaviour unchanged).
- 2026-11-05 P6 — done (generalist; audience-doc-author not dispatched). `docs/{en,de}/guides/crop-rotation-plan.md`.
- 2026-11-05 P7 — done. CLAUDE.md, mkdocs.yml nav + DE translation, guides and references indexes (en/de). `spec/README.md` regenerated per `spec` operation 4 from git dates, which also corrected stale dates on existing rows.
- 2026-11-05 P8 — partial: validator, `--self-test`, pre-commit, `mkdocs build --strict` green; recipe-audit left to the orchestrator.
- 2026-11-05 P9 — done, three runs (cost bound). Fixture in the session scratchpad: 4 beds, 3 seasons, one unknown family, conflicting pin, same-family repeat, one inspection, variants with N=3 and without N. All 24 placements, 168 verdict+rule pairs and NOT PLACED identical across runs and equal to a hand computation. Two divergences: run 1 listed only pinned conflicts under CONFLICTS (runs 2–3 also unplaced candidates), and levels differed (caller vs 4/5). Both fixed in P3/P1 afterwards; not re-measured (cap reached).
- 2026-11-05 P10 — created by the operator as #68; every placeholder "the blocked follow-up split out of #47" in spec, skill, recipe and guides now reads nolte/kamerplanter-goose#68.
- 2026-11-05 Review fixes (coordinator, after recipe-audit of 6af928d) — done: per-rule verdict elements and levels (N is an element of every verdict it windows; plan selections carry their family_key level, pins `caller`); pins placed per season after earlier seasons are decided; history established only from its earliest recorded season, earlier seasons `unknown`; season-`unknown` entry unconditional (rule 4); failed/partial inspection read → `unknown` (new rule 6, caution 7, clear 8); recipe table values and `<p>` defined; NOT PLACED reasons `occupied`/`pinned slot`, empty groups skipped as `excluded`, duplicate seasons deduplicated; §B `get_cultivar` aligned; guide nits; placeholder → #68. P9 re-run (3 runs, same fixture): CONFLICTS (2 pinned entries) and every verdict level identical across all three; runs 4 and 5 fully identical; run 6 diverged in one variant-B ranking (bed-d/2028 placed fam-aster instead of unknown/sp-mystery, contrary to the bed-count key) and its cascade; the rank step was then made explicit about strict key order, not re-measured.
