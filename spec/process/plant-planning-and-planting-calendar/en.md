# Plant Planning and Planting Calendar

Status: draft
Portfolio-Scope: local

## Context

Choosing a crop is not yet a plan. A plan says when each chosen crop is sown, when it is transplanted, when it is expected to be harvested, and where it goes, and every one of those answers is a date. Dates are where a process that works from general knowledge does the most harm while sounding the most certain: "sow tomatoes in March" is wrong for most gardens and reads as right. The Kamerplanter catalog holds some of what a date needs — a sowing calendar with the garden's frost dates, and species fields for sowing months, harvest months and growing periods — and does not hold the rest: it names no field for beds or containers, for a target harvest window, or for rotation.

This spec specifies two steps. The planting calendar turns each chosen crop into the windows in which it can be sown, transplanted and harvested at this garden, and says for every window which rule and which field produced it. The plan turns the calendar into planting-run proposals a person can review, with a stable identity for each run, a rationale and a confidence for each date, and a list of what was not planned and why. Both are read-only. A plan is a document; applying it is a separate step, and the measured catalog has no tool that could do it (section F).

Everything about the tool surface below is quoted from [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) and from [the species baseline process](../species-baseline-verification/en.md), whose measurements were taken against the reference instance on 2026-08-07. **Nothing here was re-measured when this spec was written**: the `kamerplanter` MCP server was unreachable in the session that drafted it (`INVALID_CONFIG`). A tool or field name is quoted from those specs; whether it still exists, and what a response carries beyond what they record, is unestablished until a `tools/list` and a read-only call against a reachable instance say so.

Boundaries: [the site analysis and crop selection spec](../site-analysis-and-crop-selection/en.md) owns the candidate record and the site profile this spec reads; [the garden decision policy](../garden-decision-policy/en.md) owns the weight a claim carries, the recommendation shape and the garden context. This spec applies them and does not restate them. Bed layout is nolte/kamerplanter-goose#46, care planning is nolte/kamerplanter-goose#43 and crop rotation is nolte/kamerplanter-goose#47; the first two read this spec's output and the third is not built. The `-apply` recipes for garden and season plans are nolte/kamerplanter-goose#59. The audit that decides which artifact owns what is nolte/kamerplanter-goose#39 and nothing here pre-empts it. [The recipe project pattern](../../goose/recipe-project-pattern/en.md) owns recipe mechanics and [the server spec](../../mcp/kamerplanter-mcp-server/en.md) owns transport, authentication and tenancy.

Readers: authors of garden skills and recipes in this repository, the authors of bed layout and care planning who consume the plan, and anyone reviewing a plan before acting on it.

## Goals

- Every date in a plan names the rule that produced it, the fields it came from and the evidence level it rests on
- A date that cannot be computed from recorded fields is reported unknown with the missing input, never estimated
- A planting run has an identity that depends on what it is, not on the order it was listed in, so a plan can be compared with the next one
- Read-only planning and applying are separate, and a plan can be reviewed before anything is applied
- The plan can be read by care planning and by bed layout without re-deriving anything

## Non-Goals

- Applying a plan: creating planting runs, tasks or plants. The measured catalog has no tool for it (section F)
- Choosing crops: that is [crop selection](../site-analysis-and-crop-selection/en.md)
- Assigning plants to beds, laying beds out, or planning rotation — nolte/kamerplanter-goose#46 and #47
- Care schedules for the planted crop — nolte/kamerplanter-goose#43
- Supplying facts the catalog does not hold. Where there is no source, the caller supplies the value or it stays unknown
- Typical sowing dates, durations or offsets from general knowledge. A date comes from a recorded field or it is unknown

## Requirements

### A. Inputs

| Input | Source | Not established |
|-------|--------|-----------------|
| Candidate records | [crop selection](../site-analysis-and-crop-selection/en.md), sections E and F | — |
| Site profile, including the garden's frost dates | [site analysis](../site-analysis-and-crop-selection/en.md), section A | The format of the frost dates: only that `get_sowing_calendar` with a `query` returned them is recorded |
| The garden's existing planting runs | `list_planting_runs` | Its parameters and its pagination are not recorded |
| Beds and containers | The caller only: entries `name:area_or_volume` separated by commas | No source in the measured catalog |
| Target harvest window | The caller only, in the caller's words | No source |
| Planting method preference | The caller only: `direct_sow` or `indoor_then_transplant` | No source |

- **MUST** take the candidate records as given and **MUST NOT** recompute or overrule a verdict
- **MUST** mark beds and containers, the harvest window and the method preference as source `caller`, and **MUST** report each as unknown when the caller did not supply it
- **MUST** split the beds string at the commas and at the first colon of each entry and **MUST NOT** pass the joined text on as a name
- **MUST NOT** assign a run to a bed the caller did not name
- **SHOULD** list the garden's existing planting runs as context, and **MUST NOT** treat a partial or failed read of them as proof that there are none

### B. The planting calendar

A window is a start and an end for one step of one planting method of one growing period of one candidate. A candidate with several `growing_periods[]` has several sets of windows.

| Window | Method | Fields that feed it | What they do not cover |
|--------|--------|---------------------|------------------------|
| Sowing | Direct sowing | `direct_sow_months[]` of the chosen growing period; the garden's frost dates for a frost-sensitive crop | What `frost_sensitivity` values mean and the frost-date format are unrecorded, so the frost bound is applied only where both read unambiguously |
| Indoor sowing | Indoor sowing, then transplanting | `sowing_indoor_weeks_before_last_frost`; the garden's last frost date | The frost-date format |
| Transplanting | Indoor sowing, then transplanting | The garden's frost dates for a frost-sensitive crop | The same, and how long a seedling needs before transplanting: no field says |
| Harvest | Both | `harvest_months[]` of the chosen growing period | The top-level months are the union across periods, so a period must be chosen first |
| Harvest, from maturity | Both | The cultivar's `days_to_maturity` | What it counts from, sowing or transplanting, is not recorded |

- **MUST** choose the entry of `growing_periods[]` that applies, **MUST** say which, and **MUST NOT** use the top-level months when periods exist
- **MUST** compute a window only from fields whose meaning is recorded, and **MUST** report a window whose field is absent, unreadable or unrecorded in meaning as `unknown` with the missing input
- **MUST NOT** use a typical date, a typical duration or an offset from general knowledge to fill or bound a window
- **MUST NOT** compute a harvest date from `days_to_maturity` while its starting point is unrecorded, and **MUST** use `harvest_months[]` for the harvest window and report the maturity comparison as `unknown`
- **MUST** use the cultivar's value when the cultivar carries the attribute and the species value otherwise, and **MUST** record which, per attribute used
- **MUST** give each window the rule applied, its fields, its source (a tool or `caller`), its retrieval time and its evidence level per [the garden decision policy](../garden-decision-policy/en.md)
- **MUST** compare a window with the caller's target harvest window as a preference, met, unmet or unknown, and **MUST NOT** drop a candidate on it

### C. The plan

- **MUST** produce a planting run only for a candidate whose verdict is `eligible` and who has a method with a known sowing window: a known direct sowing window, or for indoor sowing a known indoor sowing date
- **MUST** list every other candidate under not planned, with one reason: `rejected` and the failed hard constraint, `undetermined` and the input that is missing, or `window unknown` and the missing input
- **MUST** give each run an identifier built from the species key, the cultivar key or none, the planting method and the growing period, the period identified by the months it carries and not by its position, and **MUST NOT** build it from the order of the input or from the time
- **MUST** give each run its method, its windows with their rules, a location that is a bed the caller named or `unassigned`, a succession note, a rotation note, and for each date a rationale, a confidence derived from the highest evidence level that supports it, an uncertainty statement and a missing-data list, per [the garden decision policy](../garden-decision-policy/en.md)
- **MUST** report rotation as unknown, and **MUST NOT** read `compatible_companions[]` as a rotation constraint
- **MUST** name a succession opportunity only where the calendar's own dates make two windows follow each other, **MUST** name it on both runs of the pair (`precedes <run identifier>` on the earlier, `follows <run identifier>` on the later), and **MUST NOT** invent one
- **MUST NOT** state a confidence for a date that rests on a caller-supplied fact without saying so

The plan document has four blocks, in this order and under these names: `PLAN HEADER` (the garden, given or discovered, and the input blocks it was made from), `PLANTING RUNS`, `NOT PLANNED` and `APPLY CONTRACT`.

| Consumer | Reads, per run |
|----------|----------------|
| Care planning (nolte/kamerplanter-goose#43) | the run identifier, the species key, the cultivar key, the method, the sowing, transplant and harvest windows, the confidence |
| Bed layout (nolte/kamerplanter-goose#46) | the run identifier, the location, the area or volume as the caller supplied it, the succession note, the rotation note |

- **MUST** return the four blocks in this order with these names, and **MUST NOT** return a field that was not read, listing an unread field as absent with its reason

### D. The season view

- **MUST** build the season view from the runs of the plan only, grouped by the months of their windows, and **MUST NOT** add a date that is not in the plan
- **MUST** list the succession opportunities the plan names and no others, and **MUST** state that a season view over a plan with unknown windows is incomplete, naming them

### E. Determinism

- **MUST** make the plan a function of the supplied input blocks and the policy, so that two runs over the same blocks give the same plan facts: the run identifiers, the methods, the windows, the locations, whether a succession is named, the rotation notes, the not-planned reasons and the confidence levels
- **MUST** order the runs by content (species key, cultivar key, method, period), and **MUST NOT** order them by the order of the input
- **MUST NOT** read the current date inside the plan facts; retrieval times are reported beside the facts and are not compared
- **MUST** state that byte-identical prose outside the plan facts is not claimed, and that the property is checked on a fixed fixture of input blocks and not on a live garden

### F. Separation and the apply contract

- **MUST** keep planning read-only: the planning skills and recipes call no state-changing tool
- **MUST** include in every plan an `APPLY CONTRACT` block that states, per run, what a later `-apply` recipe would have to create (a planting run with its species, cultivar, method, windows and location), and **MUST** state that the measured catalog has no tool that creates a planting run, a sowing or planting task, or a plan: the write tools it records are `add_plant_diary_entry`, `confirm_care_task`, `archive_plant`, `set_plant_location`, `claim_diary_analysis`, `submit_diary_analysis`, `transition_plant_phase`, `assign_species_phase_sequence`, `assign_nutrient_plan`, `record_feeding_event` and `create_inspection`, and the setup tool `create_site`, and none of them does
- **MUST** name nolte/kamerplanter-goose#59 as the place where the `-apply` recipes are tracked, and **MUST NOT** ship a recipe with the `-apply` suffix that does not write what its description says
- **MUST** leave applying a plan to a separate recipe that takes an approved plan, after a person has reviewed it

## Acceptance Criteria

- [ ] Every window in a plan names its rule, its fields, its source, its retrieval time and its evidence level, and a window that cannot be computed is unknown with the missing input
- [ ] No window is built from a typical date, duration or offset, and no harvest date from `days_to_maturity`
- [ ] The growing period used is named for every candidate that has periods
- [ ] Only `eligible` candidates with a known sowing window or indoor sowing date have a run; every other candidate is listed with one reason
- [ ] A run identifier does not change when the order of the input changes
- [ ] A run is assigned to a bed only when the caller named it; otherwise it is `unassigned`
- [ ] Rotation is unknown in every run and `compatible_companions[]` is not used as a rotation constraint
- [ ] A succession is named only where two windows follow each other by the calendar's dates
- [ ] The plan has the four blocks in order, and the apply contract states that the measured catalog has no tool that creates a planting run
- [ ] Two runs over the same input blocks give the same plan facts on a fixed fixture, and the plan says what is not claimed
- [ ] The planning skills and recipes call no state-changing tool
- [ ] Every claim about the tool surface cites a spec in this repository; a claim not re-measured says so
- [ ] The German and the English file have the same headings in the same order, the same number of requirement bullets and the same number of acceptance checkboxes

## Source

- [The Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md) — the tool catalog, the write tools, the refusal of an unnarrowed `get_sowing_calendar`, and tenancy
- [The species baseline process](../species-baseline-verification/en.md) — the species and cultivar fields observed present (`direct_sow_months[]`, `harvest_months[]`, `sowing_indoor_weeks_before_last_frost`, `growing_periods[]`, `frost_sensitivity`, `compatible_companions[]`, `days_to_maturity`) and `get_sowing_calendar` with a `query` returning frost dates, measured against the reference instance on 2026-08-07
- [The species baseline check guide](../../../docs/en/guides/species-baseline-check.md) — says the sowing calendar's frost dates are per garden and name the last frost, the Eisheilige and the first frost as anchors; the format is not given there
- [The site analysis and crop selection spec](../site-analysis-and-crop-selection/en.md) — the candidate record, the site profile and the output this spec reads
- [The garden decision policy](../garden-decision-policy/en.md) — evidence levels, the recommendation output and the garden context
- [The recipe project pattern](../../goose/recipe-project-pattern/en.md)
- Issue nolte/kamerplanter-goose#42 — the planning factors and the five criteria are taken from its body; nolte/kamerplanter-goose#43, #46, #47, #59 and #39 — the consumers, rotation, the apply half and the audit

## Open Questions

- **The format of the sowing calendar's frost dates.** Only that frost dates come back is recorded, and a guide in this repository speaks of the last frost, the Eisheilige and the first frost as anchors. Whether they are single dates, ranges or week numbers is not recorded. Until it is, a window bounded by them is computed only where the response reads unambiguously.
- **What `days_to_maturity` counts from.** Sowing and transplanting give different harvest dates. Open because no spec records the starting point; until it does, harvest comes from `harvest_months[]`.
- **The value set of `frost_sensitivity`.** The field is recorded as present, its values are not. A frost bound on a window needs to know which values mean "tender".
- **How a growing period is identified.** The entries of `growing_periods[]` are recorded as carrying their own months; whether they carry a name or a key is not. This spec identifies a period by its months so that a run identifier does not depend on position, which is a choice made without that fact.
- **The parameters of `list_planting_runs`.** Whether it can be filtered or paged is not recorded, and neither is how a run it returns is shaped; the plan lists existing runs as context only.
- **Whether a live instance has a tool that creates planting runs.** The measured catalog has none, the server spec says to treat any tool count as a floor, and nobody has run `tools/list` against a reachable instance. The `-apply` recipes wait on it, tracked as nolte/kamerplanter-goose#59.
- **How rotation constraints will arrive.** Until nolte/kamerplanter-goose#47 exists, rotation is unknown in every run.
- **How determinism is measured.** This spec defines the plan facts and requires them to be the same over the same input blocks. It is checked on a fixed fixture of input blocks written out as text, repeated runs compared; that shows the property for that fixture and not for a live garden, and the number of runs needed to call it stable is not settled here.
- **Where the audit, nolte/kamerplanter-goose#39, places planning relative to the garden context and site analysis.** Whether the calendar and the plan stay two artifacts is the audit's decision.
