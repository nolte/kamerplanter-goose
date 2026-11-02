# Group pre-analysis: 2026-11-02-tier2-evidence

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch, and it must
> never be hidden behind a `.gitignore` entry.

## Scope of this analysis

**Research question:** What may tier 2 of the nutrient-imbalance evidence ladder rely on, which of the four places that state it contradict each other today, and which of those can be corrected without the live measurement #54 needs?

**The group's single logical change, in one sentence:** Settle what tier 2 of the nutrient-imbalance evidence ladder may rely on (confirmed feeding frequency without dose amounts, and whether recorded feeding events can be read back), then align the spec, the `nutrient-imbalance-assess` skill and both guide pages to that answer.

**Out of scope:** #55 (skill instruction/explanation convention and write-guard); any change to `recipes/nutrient-imbalance-check.yaml` (its only tier-2-adjacent text is the forbidden-tool list, `recipes/nutrient-imbalance-check.yaml:52`); reporting a missing read-back tool upstream (belongs to #54's "not readable" branch, not to this PR).

**Tier:** 2 — several files across spec, skill and docs, one repository, no published contract crossed. Spec en+de are translations of one source, not a second contract.

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #53 | spec-change | shared touch surface | `spec/process/nutrient-imbalance-detection/en.md:163` (Open Question), `.claude/skills/nutrient-imbalance-assess/SKILL.md:83`, `docs/en/guides/nutrient-imbalance-check.md:64` — all three re-read live 2026-11-02 |
| #54 | spec-change (measurement) | shared touch surface | `spec/mcp/kamerplanter-mcp-server/en.md:141` (the write), `docs/{en,de}/guides/nutrient-imbalance-check.md:69` and `SKILL.md:83` (the claims that depend on the answer) |

**Dependency ordering:** #54 (measure) before #53 (decide) is the natural order, but #53 does not need #54: its question is whether `get_plant_care_log` frequency is enough, and `get_plant_care_log` is already read by the skill. **#54 is blocked**: this session's `kamerplanter` MCP reports `INVALID_CONFIG`, and in the shell used here `KAMERPLANTER_URL`/`KAMERPLANTER_API_KEY` are not exported (`env | grep -ci kamerplanter` → 2, both unrelated `PWD`/`OLDPWD`; `.envrc:14-15` sets them, direnv not loaded). No measurement was attempted.

**Shared touch surface:** `spec/process/nutrient-imbalance-detection/{en,de}.md`, `.claude/skills/nutrient-imbalance-assess/SKILL.md`, `docs/{en,de}/guides/nutrient-imbalance-check.md`.

## Mode decision

**Mode:** A — single strand.

**Reason:** #54 is the member likeliest to need removal (external dependency), which is Mode B's criterion — but its tracked changes are not separable from #53's. Both edit the same skill line (`SKILL.md:83`) and the same guide paragraph. A sub-branch for #54 would conflict with #53 on every file. Instead of Mode B, the plan **defers #54 out of the bundle** (see Open questions 1): the bundle carries #53 and a hedged wording that does not assert #54's unmeasured answer, and `Refs #54` rather than a closing keyword.

## Structural finding

**Cluster shape:** symptom cluster.

**Root cause or defect class:** One claim — "tier 2 needs dose amounts" — is stated in four places, and its source is a skill decision that outran its spec. Three findings, each measured:

1. **The spec's own text points the other way.** The ladder defines tier 2 as plan target against *confirmed feeding frequency* and substrate baseline (`en.md:77`), and "Deciding the direction" defines oversupply as measured EC above target **or "a supply frequency exceeding the plan in a medium that buffers little"** (`en.md`, Oversupply paragraph). Frequency alone is already a spec-sanctioned oversupply signal. The Open Question at `en.md:163` is therefore narrower than the skill treats it: what is unknown is *strength* (dose per feeding), not *whether tier 2 exists*.
2. **The skill resolved the Open Question by refusing.** `SKILL.md:83`: "tier 2 collapses to tier 3 and the honest output is a refusal plus a request to measure". `grep -rn "collapses to tier 3" .claude spec docs` finds `SKILL.md:83` and, in prose, `en.md:163`; the guide carries it as "tier 2 has nothing to stand on" (`docs/en/guides/nutrient-imbalance-check.md:64`).
3. **The guides contradict themselves.** `docs/en/guides/nutrient-imbalance-check.md:64` says tier 2 has nothing to stand on without logged quantities; `:69` (and DE `:69`) says a garden recording fertigations "gives tier 2 the feeding frequency it needs". The second is exactly #54's unmeasured claim, asserted in a user-facing page. `SKILL.md:83` says the opposite of `:69` in the same pair.

**Process finding:** A skill is allowed to resolve a spec Open Question with no trace in the spec; nothing flags that an Open Question text and a skill sentence are the same sentence. The same shape as #55's gap (no separation between instruction and explanation). Not filed separately here; see Open questions 3.

**Preventive change:** A spec Open Question that a skill answers must be closed in the spec in the same change (spec first, skill and guides follow — the order #53 already prescribes). No guard proposed in this group; a mechanical check would be a #55-class convention question.

**Recurrence fed to the portfolio loop:** first occurrence in this repository (#34's fifth item produced #53; no second instance found by `grep -rn "Open Question" .claude/skills`, not run to exhaustion — recorded as unverified).

## Plan approval

**Authorised by:** `2026-11-02-tier2-evidence/plan-approval`, covering the members, mode, and order above. Revoked for undispatched members by any structural regression until re-approved.

**Approved:** 2026-11-02 by operator. Decisions: (1) #53 rule **B** — tier 2 can establish undersupply from confirmed frequency; oversupply stays tier 3 unless dose amounts exist; (2) #54 leaves the closing set: bundle closes #53, `Refs #54`, #54 stays open for its own run once the server is reachable; (3) process finding is carried in #55's thread, no new issue.

**Group requirement artifact (class cluster only):** not applicable — symptom cluster, per-member elicitation. #53's requirement is the issue's own "Decision needed"; it is an operator decision, taken at this gate (Open question 2).

## Completeness matrix

Columns derived from the repository: skill, spec, docs, tests, generated index. No source-code, config or workflow column (`git ls-files` shows no Python source touching tier text; `recipes/nutrient-imbalance-check.yaml` carries no tier wording).

| Member | Spec (en, then de) | Skill | Docs (en, de) | Tests | Generated index |
|---|---|---|---|---|---|
| #53 | `spec/process/nutrient-imbalance-detection/en.md:163`: close the Open Question per decision; mirror in `de.md:163`; check: `grep -rn "collapses to tier 3\|zusammenf" spec/process/nutrient-imbalance-detection` returns only the intended text | `SKILL.md:83`: drop "collapses to tier 3" as stated fact, state the decided rule; check: `grep -n "collapses to tier 3" .claude/skills/nutrient-imbalance-assess/SKILL.md` returns nothing | `docs/en/guides/nutrient-imbalance-check.md:64,69` and `docs/de/…:64,69`: align both paragraphs to the decision, remove the `:64`/`:69` contradiction; check: `task docs` (mkdocs build --strict) | not applicable — no test asserts tier-2 wording; check: `task test` still green | not applicable — no spec title/summary change; check: `task test` |
| #54 | **deferred** — conditional on measurement: "readable" → name the tool in `spec/process/nutrient-imbalance-detection/`; "not readable" → drop the hedge in `spec/mcp/kamerplanter-mcp-server/en.md`; check: live `tools/list` + read-only `tools/call` of `get_plant_care_log` and `get_plant_diagnostics` | **deferred** — `SKILL.md:83` wording follows the result | **deferred** — `:69` in both guides follows the result; until then it is reworded to not assert the unmeasured claim (done under #53) | not applicable | not applicable — `spec/README.md` lists topics, not tool names; check: `task test` |

## Risks

- #53 needs an operator decision, not an edit: choosing "tier 2 survives on frequency" raises how often the check proposes a direction; choosing "collapses" confirms the status quo. Wrong in the first direction = a dosage direction proposed with reduced confidence on thin evidence.
- Reworded `:69` hides, rather than resolves, #54's question; the bundle must say so in its PR body (`Refs #54`, open).
- DE spec/guides drift if the en edit lands without the de mirror — the matrix names both; `task docs` does not check translation parity.
- Three places currently disagree (finding 3); an incomplete alignment leaves one of them live.

## Open questions for the operator

1. **#54 inside the bundle?** Reading A (as approved in the partition): proceed with #53, #54 waits. Concretely: the bundle PR closes #53 only, `Refs #54`; #54 stays open and becomes its own later run once the server is reachable (fix with `direnv allow` in a shell that exports the `.envrc` variables, then `goose run --recipe connectivity-check`). Confirm that dropping #54 from the closing set is acceptable, or say if you want to measure first.
2. **The #53 decision.** Evidence for each reading:
   - **A — tier 2 survives on frequency:** the spec already counts "supply frequency exceeding the plan in a medium that buffers little" as oversupply (finding 1). Rule: tier 2 needs a nutrient plan, a known substrate and a confirmed cadence; amounts are not required; confidence stays reduced, and the result states that strength per feeding is unknown. The Open Question narrows to "how much confidence", the skill's `:83` refusal and the guide's `:64` sentence are replaced.
   - **B — oversupply needs amounts, undersupply does not:** frequency below plan indicates undersupply, but frequency alone cannot show *over*supply when concentration is unknown (a weak mix fed often is not oversupply). Rule: tier 2 can establish undersupply from frequency; for oversupply it stays tier 3 unless amounts exist. This keeps the skill's refusal, but only for one branch.
   - **C — keep the status quo (tier 2 collapses):** contradicts the ladder table at `en.md:77`, which the spec would then have to rewrite.
   Recommendation: **A or B, not C**; I lean to B because the spec's oversupply clause is conditional on "a medium that buffers little", and frequency says nothing about concentration. This is your decision.
3. **Process finding:** file the "skill answers a spec Open Question without closing it in the spec" shape as an issue, or fold it into #55's thread?

## Member results

Filled during implementation.

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #53 | no matching specialist — generalist (prose edits to spec/skill/docs; no skill/agent in the registry owns spec text for this repository) | `python tests/validate_recipes.py` (the command behind `task test`) | `OK — 7 skill completeness cases hold.` / `OK — 8 recipe-level cases hold.` / `OK — 15 recipe(s) match the house pattern.` rc=0 |
| #53 | same | `mkdocs build --strict` (the command behind `task docs`) | rc=0, `Documentation built in 2.21 seconds`; Material's 2.0 banner printed, no strict warning |
| #53 | same | `grep -rn "collapses to tier 3" .claude spec docs` | no output, rc=1 |
| #54 | deferred | — | not run: bundle closes #53 only, `Refs #54` |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| #53 | local adaptation | `task worktree:add` exited 1 with no message; the same steps run directly (`git worktree add -b docs/2026-11-02-tier2-evidence …/tier2-evidence origin/develop`) succeeded, so the plan stub `.resume/<slug>/plan.md` was not seeded — this artifact is the plan. Upstream tracking to `origin/develop` was unset. |
| #53 | local adaptation | `task test` / `task docs` in the worktree stopped at "Taskfile … not trusted by user" (the remote-include trust env is not loaded there), so the commands behind them were run directly with the primary checkout's `.venv`. |
| #53 | local adaptation | The matrix put the `:64`/`:69` guide rewording in the same cells as the decision; the DE spec/guide mirrors were edited in the same commit. No structural regression: admission, mode and order held. |

## Requirement coverage

Not applicable — no group requirement artifact.

## Findings

| Finding | Source | Outcome | Reproduction | Issue |
|---|---|---|---|---|
| `SKILL.md:59` still let frequency alone establish oversupply | independent review (fresh context) | fixed directly | `sed -n 59p` showed the old row, reproduced | — |
| `SKILL.md:19` tier-2 row lacked the undersupply/oversupply qualifier | independent review | fixed directly | `sed -n 19p` reproduced | — |
| `spec/process/garden-decision-policy/{en,de}.md:145` pointed at the deleted Open Question | independent review | fixed directly (surface widened by these two files) | `sed -n 145p` reproduced; `grep "open question about tier 2"` now empty | — |
| guide `:69` concluded "does not feed this check" from an unmeasured fact | independent review | fixed directly: "may not … by itself" / "womöglich" | `sed -n 69p` reproduced | — |
