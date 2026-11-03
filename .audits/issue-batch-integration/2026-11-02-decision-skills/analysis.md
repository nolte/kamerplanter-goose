# Group pre-analysis: 2026-11-02-decision-skills

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch, and it must
> never be hidden behind a `.gitignore` entry.

## Scope of this analysis

**Research question:** What does it take to add the watering and fertilisation decisions as consumers of `garden-context` and `decision-policy`, which parts of the measured tool catalogue can an `-apply` recipe honestly use, and what must change elsewhere once the two skills exist?

**The group's single logical change, in one sentence:** Add the watering-decision and fertilization-decision skills, each with a read-only recipe and an `-apply` recipe, as consumers of `garden-context` and `decision-policy`, and plug both into the care plan and the daily garden check.

**Out of scope:** the other domains that plug into the care plan (#48, #49); a Home Assistant actuation path (every recipe here forbids Home Assistant tools, `CLAUDE.md`); live measurement (the `kamerplanter` MCP server is unreachable, `INVALID_CONFIG`); re-deriving or overriding the nutrient tier rule from #64 (`fertilization-decision` consumes it); a tool that waters or doses (the catalogue has none).

**Tier:** 2 — one repository, many files across spec, skills, recipes and docs, no published contract crossed.

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #44 | feature-request | thematic coupling | re-read live 2026-11-03: OPEN, author `nolte`, 0 comments, 0 linked PRs; body "Reuses `garden-context` and `decision-policy`"; skill `watering-decision`, recipes `watering-decision.yaml`, `watering-decision-apply.yaml` |
| #45 | feature-request | thematic coupling | OPEN, author `nolte`, 0 comments, 0 linked PRs; same skill + read-only recipe + `-apply` recipe shape; body names `nutrient-imbalance-check` as the diagnostic to reuse, does **not** name `decision-policy`; skill `fertilization-decision`, recipes `fertilization-decision.yaml`, `fertilization-decision-apply.yaml` |

**Dependency ordering:** the two members are independent of each other; both depend on `garden-context`, `decision-policy`, `plant-context-collect` (all on `develop`). Order of work: group spec first, then #45, then #44 (see "Packages"), then integration. Predecessors #43 (PR #65, `22ed342`) and tier2-evidence (PR #64, `a77c1a5`) are merged.

**Shared touch surface:** the catalogue files every feature PR here changes: `CLAUDE.md`, `mkdocs.yml`, `docs/{en,de}/guides/index.md`, `docs/{en,de}/references/index.md`, `spec/README.md` (linked PRs #57, #58, #60, #65 touched them). Not an edge, a serialisation point inside one strand.

## Mode decision

**Mode:** A — single strand.

**Reason:** the criterion for Mode B is a member likely to need removal (uncertain acceptance, external dependency). The only candidate is the `-apply` half of #44, because the catalogue offers no watering tool; that uncertainty is resolved at this gate (Open questions 1 and 2), not left to implementation, and a removed `-apply` recipe is a separate package, not a separate strand. The members share the catalogue files, so sub-branches would conflict on every rebase.

## Structural finding

**Cluster shape:** neither — none found. The provisional kind from the partition ("class": two instances of one pattern) is **overturned**: a class cluster is several issues of one *defect* class, and these are two features. There is no shared root cause either (symptom cluster). Consequence: no group requirement artifact; the requirements gate is per member, and the operator override requested below covers both.

**Root cause or defect class:** none. What the two share is a shape: evidence-based decision skill, read-only recipe, separate `-apply` recipe, `decision-policy` output (evidence, confidence, uncertainty, missing data).

**Process finding:** none new. Related, already known: the same gap that made #42 split its apply half (#59): the issue bodies name `-apply` recipes without checking which write tool the catalogue has.

**Preventive change:** before a decision skill gets an `-apply` recipe, the plan names the write tool and its measured contract; if none exists, the apply half is a referenced issue, not a promise.

**Recurrence fed to the portfolio loop:** second occurrence of "issue asks for an apply recipe the catalogue cannot support" in this repository (#42 → #59, now #44/#45). Counted, not filed.

## Measured facts the plan rests on

- **Write tools** (`spec/mcp/kamerplanter-mcp-server/en.md:127-148`): `confirm_care_task` (`plant_key`, `reminder_type`) "Confirm a care reminder for a plant"; `add_plant_diary_entry` (`plant_key`, `text`); `record_feeding_event` (`plant_key`, `volume_applied_liters`) "Record a fertigation: amount, EC/pH before and after, runoff"; `assign_nutrient_plan` (`plant_key`, `plan_key`). Twelve state-changing tools in total; none waters, doses or actuates.
- **`dry_run` / `idempotency_key`:** every state-changing tool exposes both (`en.md:150`); `dry_run` defaults to false, an identical `idempotency_key` replays for 24 hours (`en.md:167`); the server spec says SHOULD call with `dry_run: true` first and SHOULD pass an `idempotency_key` (`en.md:182-183`). Caveat measured 2026-08-16: `dry_run` succeeded where the real `assign_nutrient_plan` failed with `INTERNAL_ERROR` (`en.md:228`), so a dry run is not evidence that the write works.
- **`reminder_type` values:** not recorded anywhere (`grep -rn reminder_type spec docs .claude recipes` finds the field name in the server spec, the nutrient spec and `plant-context-collect/SKILL.md:54`, no value set). A `watering-decision-apply` that calls `confirm_care_task` cannot name the watering reminder type from the record; the caller would have to supply it.
- **Read-back of feeding events:** not measured (#54, open); the nutrient skill says so (`SKILL.md:83`). A fertilisation `-apply` that writes `record_feeding_event` therefore writes a record this repository cannot yet show is read by anything.
- **Inputs a watering decision could use:** the garden-context block marks weather, beds/containers, current measurements and goals absent (`garden-context/SKILL.md` §7: `no source` / `not collected`); soil moisture is known only if a diary entry carries it (`diary-measurements-read`); recent irrigation only through confirmed reminders in the care log (`plant-context-collect` reads `confirmed_at` per `reminder_type`); Home Assistant moisture sensors have no plant-to-entity mapping (`nutrient-imbalance-detection` Open Questions). Expect most runs to end "insufficient evidence"; that is the honest result, not a failure.
- **Nutrient rule to reuse, not re-derive:** tier 2 needs recorded dose amounts; frequency without amounts is tier 3 (PR #64; `spec/process/nutrient-imbalance-detection/en.md:77`).
- **Plug-in contract:** `spec/process/care-planning-and-daily-check/en.md` §C requires the layer to map the reports of "the two domains that exist" and to report each domain named in the Non-Goals as not available "until that skill exists"; `recipes/daily-garden-check.yaml` step 4 hard-codes watering and fertilisation as `not available (… #44 / #45)`. Once the two skills exist, leaving that is a contradiction.

## Plan approval

**Authorised by:** `2026-11-02-decision-skills/plan-approval`, covering the members, mode, and order above. Revoked for undispatched members by any structural regression until re-approved.

**Approved:** 2026-11-02 plan gate, answered 2026-11-03 by the operator on the four open questions, all as recommended. Decisions: (1) `-apply` means record what the person carried out, never actuate; (2) `watering-decision-apply` uses `confirm_care_task`, `reminder_type` supplied by the caller, never guessed; (3) plug-in integration (G1) is in this bundle; (4) requirements gate overridden for both members, mode A (single strand), cluster shape "neither". Membership and order as written above.

**Group requirement artifact (class cluster only):** not applicable — cluster shape is "neither" (see Structural finding); the requirements gate is an explicit operator override for both members, requested at this gate (Open question 4), as for #40–#43.

## Packages

Group-level packages (G), then the member packages (W for #44, F for #45). Member packages are what `issue-orchestrate` receives; a member's run may split a package but may not leave its row of the matrix.

- **G0 — spec** `spec/process/watering-and-fertilization-decisions/{en,de}.md`, one spec for both decisions, specialist `nolte-shared:spec`. Decision outputs (watering: water now / wait / insufficient evidence; fertilisation: feed / do not feed / insufficient evidence), inputs and which have a source, the conservative rules from #45's Safety list, and the apply contract. Before any member work.
- **F1 — skill `fertilization-decision`**; **F2 — recipe `fertilization-decision.yaml`** (read-only; loads `plant-context-collect`, `diary-measurements-read`, `nutrient-imbalance-assess`, `decision-policy`, the new skill; reuses the nutrient report, never re-derives its tier); **F3 — recipe `fertilization-decision-apply.yaml`** (records a fertigation the person carried out via `record_feeding_event`, with amounts the person supplies; `dry_run` first, `idempotency_key`, `Permitted by name` / `Forbidden by name`; never invents a concentration); **F4 — guide en/de.**
- **W1 — skill `watering-decision`**; **W2 — recipe `watering-decision.yaml`**; **W3 — recipe `watering-decision-apply.yaml`** (shape depends on Open questions 1 and 2); **W4 — guide en/de.**
- **G1 — plug-in integration:** `care-planning` spec §C and Non-Goals (the domains that exist are now four), `.claude/skills/care-planning/SKILL.md` mapping, `recipes/daily-garden-check.yaml` steps 3–4 and report, `docs/{en,de}/guides/daily-garden-check.md`; the 5-plant cap stays and now bounds four domains per plant.
- **G2 — catalogue:** `CLAUDE.md` bullet, `mkdocs.yml` nav + German labels, both guide indexes, both reference indexes, `spec/README.md` (via the `spec` skill).
- **G3 — verification:** `python tests/validate_recipes.py`, `mkdocs build --strict`, `goose recipe validate` on each new recipe, `nolte-goose:recipe-audit` on every new recipe at its final head, an independent read-only review from the worktree, a corpus grep for `#44`, `#45`, `watering-decision`, `fertilization-decision`, "not available".

**Dependency ordering:** G0 → F1 → F2 → F3 → F4 ; G0 → W1 → W2 → W3 → W4 ; (F4, W4) → G1 → G2 → G3. F-chain before W-chain because #45's apply is the clearer one and its decision shape informs W1.

## Completeness matrix

Columns derived from the repository (`ls`: `.claude/skills`, `recipes`, `spec`, `docs`, `tests/validate_recipes.py`, a generated `spec/README.md`, `mkdocs.yml`). No config/workflow column: no `.github/` file changes.

| Member | Skill | Recipe | Spec | Docs | Tests | Generated index / catalogue |
|---|---|---|---|---|---|---|
| #44 | `.claude/skills/watering-decision/SKILL.md`, tool-free over blocks; check: `python tests/validate_recipes.py` | `recipes/watering-decision.yaml` read-only; `recipes/watering-decision-apply.yaml` per Open questions 1–2; check: `goose recipe validate` + `recipe-audit` on each | covered by G0 | `docs/{en,de}/guides/watering-decision.md` (+ `-apply` guide if shipped); check: `mkdocs build --strict` | not applicable — no new test file; the existing validator covers recipes and skills; check: `python tests/validate_recipes.py` | rows in both indexes, nav, `CLAUDE.md` (G2) |
| #45 | `.claude/skills/fertilization-decision/SKILL.md`; check as above | `recipes/fertilization-decision.yaml`; `recipes/fertilization-decision-apply.yaml` (Permitted: `record_feeding_event`); check: `goose recipe validate` + `recipe-audit` | covered by G0 | `docs/{en,de}/guides/fertilization-decision.md` (+ apply guide); check: `mkdocs build --strict` | not applicable — as above | as above |
| group (G) | `care-planning` mapping (G1) | `daily-garden-check.yaml` flips two domains to checked (G1) | `care-planning-and-daily-check/{en,de}.md` §C and Non-Goals (G1); new spec G0 | `daily-garden-check.md` en/de (G1) | `python tests/validate_recipes.py`; `mkdocs build --strict` | `spec/README.md` regenerated via `spec` skill; `CLAUDE.md` |

## Risks

- **No tool waters or doses.** An `-apply` recipe that appears to do so would invent a capability. Mitigation: apply = record what the person did, stated in the description (`WRITES to Kamerplanter: …`), the spec and the guide; Open question 1.
- **`reminder_type` for watering is unmeasured.** `confirm_care_task` cannot be wired without a guessed value. Mitigation: the caller supplies it, or the watering apply uses `add_plant_diary_entry`, or it is split out; Open question 2.
- **Feeding events may not be readable (#54).** A fertigation recorded by `fertilization-decision-apply` may never reach tier 2. Mitigation: the guide and the apply recipe say so; no promise of effect.
- **Safety:** dosing numbers. `fertilization-decision` must not invent a concentration or mixing order; it calls `calculate_mixing_protocol` (read-only, permitted, EC-net: states the base-water assumption, `nutrient-imbalance-assess/SKILL.md` Gotchas) or reports the dose as unknown.
- **Per-plant cost.** The daily check now runs four domains per plant, at most five plants. Mitigation: the cap stays; stated in the spec.
- **Not measured live.** Both guides carry the "Not yet run against a live instance" note.
- **Merge collisions** on the catalogue files; serial by construction in one strand.
- **Review tooling:** the built-in `code-review` moves the primary checkout (seen in #64); reviews run as read-only agents in the worktree.

## Open questions for the operator

1. **What `-apply` means.** Reading A (recommended): record what the person carried out, never actuate; `fertilization-decision-apply` writes `record_feeding_event` from amounts the person supplies. Reading B: also actuate via Home Assistant, contradicting the rule in every recipe here and `spec/process/nutrient-imbalance-detection` (a correction is a proposal for a human). Reading C: ship no `-apply` recipes now, file a follow-up like #59.
2. **Watering `-apply` tool**, if Reading A: (a) `confirm_care_task` with a `reminder_type` the caller supplies, because no value set is recorded; (b) `add_plant_diary_entry`, a note that the person watered; (c) split the watering apply out into a referenced issue and ship only the read-only watering recipe in this bundle.
3. **Plug-in integration in this bundle (G1).** Recommended yes: the care-planning spec says a domain is "not available until that skill exists", so leaving the daily check unchanged contradicts the spec. Alternative: a follow-up issue, with the contradiction recorded.
4. **Requirements gate.** Operator override for both members (the bodies state goal, scope, inputs, acceptance criteria, safety), recorded here, as for #40–#43.

## Member results

Filled during implementation. Each entry records the dispatched specialist and the **actual output** of every declared check, never an assertion that it passed.

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| | | | |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| | | |

## Requirement coverage

Not applicable — no group requirement artifact (cluster shape "neither").

## Findings

| Finding | Source | Outcome | Reproduction | Issue |
|---|---|---|---|---|
| | | | | |

## Dispatch log

2026-11-03 G0 dispatched to `nolte-shared:spec` — `spec/process/watering-and-fertilization-decisions/{en,de}.md` written. Parity measured: 16 headings each at identical levels, 36 requirement bullets each, 19 acceptance checkboxes each, every relative link resolves. `spec/README.md` not regenerated (G2). One citation in `de.md` corrected after the check: the German server spec's section is "Schreibtools", not "Schreib-Tools" (`spec/mcp/kamerplanter-mcp-server/de.md:128`).
  - **Hypothesis refined (recorded as a result):** the brief had no source for a watering prior. The phase definition carries `watering_interval_days` (`spec/process/species-baseline-verification/en.md` table of `list_phase_definitions`; `.claude/skills/plant-context-collect/SKILL.md` §4). Spec section B reads it as a level 4 prior that decides nothing alone; what it counts and whether the species carries a water demand stay an Open Question. `spec/process/garden-decision-policy/en.md:30` already names "a watering interval" as a question the owning process decides, which this spec now is.
  - Duplicate check: no existing spec covers either decision; hits in nutrient, care-planning, decision-policy, MCP and species-baseline specs are references.
2026-11-03 #45 dispatched to `issue-orchestrate` (group delegation, `authorised_by: 2026-11-02-decision-skills/plan-approval`, resolved: artifact present in the worktree, lists #45, carries the approval) — F1–F4 written by the generalist: no matching specialised agent (`recipe-implement` needs a ready `project/recipes/<slug>/plan.md`, absent here). Files: `.claude/skills/fertilization-decision/SKILL.md`, `recipes/fertilization-decision.yaml`, `recipes/fertilization-decision-apply.yaml`, `docs/{en,de}/guides/fertilization-decision.md`.
  - Checks (actual output): `python tests/validate_recipes.py` → "OK — 27 write-guard cases hold." "OK — 9 completeness cases hold." "OK — 7 skill completeness cases hold." "OK — 8 recipe-level cases hold." "OK — 18 recipe(s) match the house pattern." rc=0; `goose recipe validate` on both recipes → "✓ recipe file is valid"; `goose run --recipe … --explain` lists 4 parameters (decision) and 10 (apply); `mkdocs build --strict` rc=0 (the new guide is not in the nav until G2: INFO only).
  - `recipe-audit` (baseline 2026-08-02, process 1.1.0): `fertilization-decision.yaml` exit 0, 0 findings, DIGEST subject=ccdfe5ec…288138; `fertilization-decision-apply.yaml` first version exit 0, 0 findings, DIGEST subject=4bbfa12a…5e7f (re-run after the fixes below, see next entry).
  - Independent read-only review (fresh context, told not to check out or fetch; diff stat captured first, 8 files): no contradiction with spec C/D/E; five items, each reproduced from the text and fixed: (1) the oversupply row's "rests on" value was not one of the three enumerated values → the skill now emits `insufficient nutrition ruled out (oversupply)` and spec C, its goal and its acceptance criterion now say "or that insufficient nutrition is ruled out" (en and de, parity re-measured: 36 bullets, 19 checkboxes, 16 headings each); (2) the `mcp.write` refusal and the tool-error stop had no `NOT RECORDED:` wording → added; (3) "action carried out" was only implied → step 1 and the guide now say the volume is the action carried out, recorded as given, not checkable; (4) "is not in litres" had no unit to check on a bare number → now "not a plain positive number; a value with a unit such as ml is refused, never converted"; (5) the apply description gave a working-directory reason although the recipe loads no skill → sentence removed.
  - **Addition beyond the spec text (local adaptation, recorded):** `fertilization-decision-apply` also refuses a decision that is not exactly `feed`, so it never writes a record that contradicts the decision; the spec says "approved decision plus action, refuse when either is missing" and is silent on a contradicting decision.
