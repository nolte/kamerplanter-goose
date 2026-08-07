# Plant Health Image Analysis

Status: draft
Portfolio-Scope: local

## Context

Kamerplanter collects diary entries, and a diary entry may carry photos. The backend marks the ones that want a machine analysis and holds them in a queue; measured on the reference instance, two entries were waiting. The MCP server exposes the whole cycle — list the queue, claim an entry under a lease, fetch its photos, write the result back — and one field in the submit tool is named `recipe_version`. The server is built expecting an agent like the ones in this repository to do the analysing.

What the server does not supply is the analysis itself, and that is harder than looking at a photograph. A yellowing lower leaf is senescence on a determinate tomato in fruit, nitrogen deficiency on a heavy feeder in vegetative growth, and overwatering on a succulent in winter rest. The photo is identical in all three. **The image is evidence; the plant instance is what the evidence is read against.** An analysis that skips the instance produces text that sounds botanical and means nothing.

This spec describes that process: which context is gathered, in what order, how the species shifts the reading, how uncertainty is expressed, and how a claim is always released. It is the process layer. The recipe mechanics — where extensions are declared, what the provider adds — are specified in [the Goose recipe project pattern](../../goose/recipe-project-pattern/en.md); what the server offers is specified in [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md). Neither is restated here.

Everything marked *measured* was read from the reference instance on 2026-08-05 through the live MCP endpoint and through headless Goose runs.

Readers: authors of the analysis recipe in this repository, and anyone judging whether a submitted analysis was justified by what it was given.

## Goals

- A finding is bound to one plant instance, its species, and its current phase — never to a generic plant photograph
- Species differences enter the analysis from backend master data, so the spec does not carry botanical knowledge that drifts against the catalog
- Every claim a run opens is closed by the same run, including when the analysis fails
- Uncertainty is quantified and named rather than rounded up into a diagnosis
- A photo that cannot answer the question yields a named gap, not an invented finding
- A reviewer can reconstruct from the submitted result which photo and which context field produced each finding

## Non-Goals

- Image capture, upload, and rendition generation — the backend owns these; the process consumes what `get_diary_entry_photos` returns
- Identifying the species from the image; the species is a fact of the instance, and a photo that contradicts it is a finding, not a re-identification
- Triggering treatments, confirming care tasks, or any state change beyond writing the analysis result back to its own entry
- Kamerplanter's in-app AI assistant, which is a separate surface with its own context
- Recipe mechanics and the MCP server's transport, auth, and tenancy rules — specified elsewhere and referenced, not repeated
- Prescribing prompt wording; this spec fixes the invariants a prompt must preserve

## Measured baseline

The catalog has grown well past what the MCP server spec records. Measured on 2026-08-05, `tools/list` returned **42 tools**, not the 12 documented there as the complete surface. The analysis cycle depends on five of the newer ones, so the process is available today:

| Tool | Required arguments | Notes (measured) |
|------|--------------------|------------------|
| `list_pending_diary_analyses` | — | `limit` default 20, max 100; `include_stale` default `true` also returns entries whose lease expired |
| `claim_diary_analysis` | `entry_key`, `worker_id` | `lease_seconds` default 900, max 3600; lease plus compare-and-set |
| `get_diary_entry` | `entry_key` | Full plant context inline, **without** image data |
| `get_diary_entry_photos` | `entry_key` | Photos as MCP image content blocks (WebP); `size` is 512 or 1280, anything else is a validation error |
| `submit_diary_analysis` | `entry_key`, `lease_token`, `status` | `status` is `completed` or `failed`; ends the claim |

**Image content blocks reach the model and are legible.** Measured end to end: a headless run called `get_diary_entry_photos` at `size: 512` and described what was depicted. The process is not blocked on a transport limitation.

That same measurement is the sharpest available reminder of why refusal matters. The photo in the queue depicted a plastic clamp and a remote control — no plant at all. The "the image does not answer the question" case is not a hypothetical to be handled for completeness; it was the first real entry encountered.

`get_diary_entry` already returns the instance context inline — `plant_key`, `species_key`, `species_name`, `cultivar_name`, `current_phase`, `phase_started_at`, `planted_on`, `location_name` — alongside the entry's own `text`, `tags`, `measurements`, and `photo_refs`. One call establishes what the photo is a photo *of*.

## The process

One run handles exactly one diary entry. The stages are ordered so that everything cheap and refusable happens before the claim, and nothing after the claim can end without releasing it.

### Stage 0 — Preconditions

Resolve the garden and read `mcp_permissions` from `list_tenants`. The cycle needs `mcp.write` for `claim_diary_analysis` and `submit_diary_analysis`. A key holding only `mcp.read` must stop here and say so — claiming an entry it cannot submit would park that entry under a lease for up to an hour.

### Stage 1 — Selection

Either take the `entry_key` given as a recipe parameter, or call `list_pending_diary_analyses` and take the oldest entry by `requested_at`. The listing carries `photo_count`; an entry with `photo_count: 0` is not a candidate for image analysis and is reported as skipped rather than claimed.

### Stage 2 — Claim

Call `claim_diary_analysis` with a `worker_id` that identifies this recipe and run, and a `lease_seconds` chosen to exceed the expected run, not the maximum. Keep the returned `lease_token`; without it the result cannot be submitted. From this point every exit path runs through stage 6.

### Stage 3 — Instance context

Call `get_diary_entry` for the entry, then gather what the reading needs:

- `get_species_info` for the `species_key` — the species baseline
- `list_phase_definitions` to resolve `current_phase` into its definition, which carries `stress_tolerance`, `watering_interval_days`, and `typical_duration_days`
- `get_cultivar` when `cultivar_key` is set — traits and `days_to_maturity` narrow the species expectation
- `get_plant_care_log` — when the plant was last watered or fed, which decides whether a drought or deficiency reading is plausible
- `get_plant_inspections` — the IPM history; a pest already recorded on this plant raises the prior for the same pest, and a plant with no inspections has no such prior

The entry's own `text`, `tags`, and `measurements` are part of the context and are read as a claim by the observer, not as ground truth. Where the text and the image disagree, both are reported.

### Stage 4 — Images

Fetch the photos with `get_diary_entry_photos`. Prefer `size: 1280` when the question is a fine-grained one — leaf undersides, chlorosis patterns, insect bodies — and `512` when it is about habit or overall vigour. Record which `photo_ids` actually informed the analysis; at most five may be reported.

### Stage 5 — Reading

Describe what is visible before interpreting it, and keep the two separable in the result. Then read each observation against the expectation the instance sets, per the tables below. A finding is the *gap* between the two, not the observation alone.

Every finding carries a `confidence` between 0.0 and 1.0 and a `rationale` naming the evidence: which photo, which visible feature, and which context field made it a finding rather than normality. At most ten findings, at most ten recommended actions.

### Stage 6 — Submit

Always. On success, `status: "completed"` with a `summary` of one to three sentences (2000 characters maximum), the findings, the recommended actions, the analysed photo ids, the model, and the `recipe_version`. When the analysis cannot be made — no legible photo, no plant depicted, missing context, a tool that failed — `status: "failed"` with `error` naming the cause. A failed submit is a correct outcome; an abandoned lease is not.

## What the species changes

The species baseline comes from `get_species_info`. Each field shifts what counts as normal, so the same visible feature yields a different finding on a different species. The spec names the mapping; it does not name the plants.

| Field (measured) | Shifts the reading of |
|------------------|-----------------------|
| `plant_category` | Which pest and disease spectrum is plausible at all, and what light and humidity the plant is presumed to stand in — an indoor plant and an outdoor vegetable share almost no failure modes |
| `growth_habit` | Whether trailing, creeping, or sprawling growth is the plant doing its job or a symptom of etiolation; on a `groundcover` it is the former |
| `root_type` | How fast drought stress appears and how it looks; a fibrous root system wilts on a different clock than a taproot |
| `nutrient_demand_level` | Whether a deficiency reading is plausible under the recorded feeding history; a `heavy_feeder` and a lean-soil species make opposite priors from the same pale leaf |
| `frost_sensitivity`, `hardiness_zones` | Whether cold damage is admissible as an explanation at the entry's date and the plant's location |
| `bloom_months`, `harvest_months` | Whether flowers or fruit in the photo are on schedule, early, or absent when they were due — against `created_at`, not against today |
| `allows_harvest`, `harvest_pattern` | Whether ripeness is a question worth asking, and whether a partially picked plant is expected to look picked |
| `base_temp_gdd` | How much growth to expect since `planted_on`, which is what makes "stunted" a claim rather than an impression |
| `cultivars[].traits`, `cultivars[].days_to_maturity` | The species expectation narrowed to the variety, when `cultivar_key` is set |
| `toxicity` | Never the health reading — but it belongs in a recommended action that would have someone handle or eat the plant |

`compatible_companions` describes planting decisions, not plant health, and does not enter a finding.

Two rules keep this honest. A species field that is absent or null **narrows** the analysis — the corresponding question is not asked and the gap is named — rather than being replaced by a general assumption about plants. And the species is never inferred from the image: where the photo appears to show a different plant than `species_name`, that mismatch is itself the finding, at whatever confidence the image supports.

## What the instance changes

Species data alone would give the same answer for every strawberry in the world. The instance is what makes the analysis about this plant:

| Source | Shifts the reading of |
|--------|-----------------------|
| `current_phase` plus its definition | What the plant should be doing now; `stress_tolerance` also sets how much a given symptom matters in this phase |
| `phase_started_at` against `typical_duration_days` | Whether the plant is overdue to leave its phase, which reframes "not flowering yet" as either normal or a finding |
| `planted_on` | The plant's age, and with `base_temp_gdd` the growth expected by now |
| `watering_interval_days` from the phase, against `get_plant_care_log` | Whether the plant is plausibly under- or over-watered at the time the photo was taken |
| `get_plant_inspections` | Prior pest and disease pressure on this individual — a recurrence and a first occurrence are different findings |
| The entry's `measurements` and `tags` | Values the observer recorded, to be reconciled with the image rather than trusted over it |
| `location_name` | Where it stands, which bounds the exposure explanations available |

All timing is judged against the entry's `created_at`, never against the time of the run. A photo analysed three weeks after it was taken is evidence about the plant three weeks ago.

## Confidence and refusal

A finding's `confidence` is about the evidence, not about the model's fluency. Three cases must not be collapsed:

- **A finding** — the image shows something, and the instance context makes it a departure from normal. Confidence reflects how unambiguous the visible feature is.
- **A gap** — the question is legitimate but the image cannot answer it (the leaf undersides are not visible, the photo is out of focus, the crop excludes the soil). Reported as a gap with what would resolve it, never as a low-confidence finding.
- **A refusal** — the image does not depict the plant, or depicts no plant at all. `status: "failed"` with an `error` saying so.

A run that finds nothing wrong submits `completed` with an empty findings list and a summary saying the plant appears normal for its species and phase. Healthy is a result.

## Requirements

- **MUST** read `mcp_permissions` from `list_tenants` and confirm `mcp.write` before claiming, since a claim that cannot be submitted parks the entry under a lease for up to an hour
- **MUST** claim an entry with `claim_diary_analysis` before reading its photos, and **MUST** carry the returned `lease_token` to the submit call
- **MUST** call `submit_diary_analysis` on every path that claimed an entry, with `status: "failed"` and a populated `error` when the analysis could not be made
- **MUST** set `lease_seconds` from the expected run duration rather than the 3600 maximum, so a crashed run frees the entry sooner
- **MUST** pass a `worker_id` that identifies the recipe and the run, and populate `recipe_version` and `model` on submit, so a result can be traced to what produced it
- **MUST** resolve the plant instance, its species, and its current phase before interpreting any image, and **MUST NOT** submit a finding that was not read against that context
- **MUST** derive species-dependent expectations from the fields returned by `get_species_info`, `get_cultivar`, and `list_phase_definitions`, and **MUST NOT** encode per-species botanical rules in the recipe prompt, which would duplicate the catalog and drift against it
- **MUST** judge all timing against the entry's `created_at`, never against the time of the run
- **MUST** give every finding a `rationale` naming the photo and the visible feature it rests on, and the context field that made it a departure from normal
- **MUST** report a mismatch between the depicted plant and `species_name` as a finding, and **MUST NOT** re-identify the species from the image or silently analyse the plant it appears to show
- **MUST NOT** call any state-changing tool other than `claim_diary_analysis` and `submit_diary_analysis` for the entry it claimed; naming the forbidden ones in the `prompt` is required by the recipe project pattern
- **MUST NOT** turn an unanswerable question into a low-confidence finding; a gap is reported as a gap
- **MUST** carry the `-apply` filename suffix and state the write effect in its `description`, since the process writes
- **SHOULD** handle exactly one entry per run, so a failure is attributable and the lease stays short
- **SHOULD** skip an entry whose `photo_count` is 0 with a named reason instead of claiming it
- **SHOULD** pass `dry_run: true` on the submit call when the run is a rehearsal, and an `idempotency_key` derived from the entry and run so a retry does not double-write
- **SHOULD** request `size: 1280` when the finding turns on fine detail and `512` when it turns on habit or vigour, and record which photo ids informed the result
- **SHOULD** narrow the analysis when a species field is absent, naming the question it could not ask, rather than substituting a general assumption
- **SHOULD** submit `completed` with an empty findings list when the plant appears normal, rather than manufacturing a marginal finding
- **MAY** read `get_plant_nutrient_plan`, `get_pest`, `get_disease`, or `get_treatment` to substantiate a specific finding, and **MAY** cite a treatment's safety interval (`Karenz`) in a recommended action when the plant `allows_harvest`
- **MUST NOT** state the direction of a suspected nutrient problem — undersupply versus oversupply — from the image, since the two are visually indistinguishable; that determination belongs to [nutrient imbalance detection](../nutrient-imbalance-detection/en.md) and **SHOULD** be handed to it rather than guessed
- **MAY** consult `list_pending_diary_analyses` with `include_stale: true` to pick up an entry whose previous lease expired

## Acceptance Criteria

- [ ] A run that claims an entry submits a result on every exit path, including tool failure and unusable images
- [ ] A run without `mcp.write` stops before claiming and names the missing permission
- [ ] Every submitted finding's `rationale` names a photo id, a visible feature, and a context field
- [ ] No submitted finding rests on species knowledge absent from the backend response
- [ ] An entry whose photo shows no plant is submitted as `failed` with an explanatory `error`, not as a finding
- [ ] A healthy plant yields `completed` with an empty findings list and a summary saying so
- [ ] Timing statements in a summary reference the entry's `created_at`, not the run date
- [ ] The recipe file carries an `-apply` suffix and names its write effect in `description`
- [ ] The recipe's `prompt` names every forbidden state-changing tool
- [ ] `lease_seconds` in the recipe is below the 3600 maximum and justified by the expected run duration
- [ ] Findings, recommended actions, and analysed photo ids stay within the server's limits of 10, 10, and 5

## Open Questions

- Whether the model's reading of a 512-pixel rendition is materially worse than of a 1280 one for the findings that matter here. Both sizes are available; only 512 has been exercised, and only against a photo containing no plant.
- Whether several photos of one entry should be analysed jointly in one pass or separately and then reconciled. The submit schema accepts up to five analysed photo ids without saying how they relate.
- Whether a re-analysis should read the previous result before overwriting it. The payload itself is now measured (2026-08-05): a `failed` submit leaves `analysis` at `null` and puts the error text verbatim into `analysis_error`, while a `completed` submit stores an object keyed `summary`, `findings`, `recommended_actions`, `analyzed_photo_ids`, `model`, `recipe_version`, plus two fields the server adds on its own — `analyzed_at` and a `disclaimer` naming the result as a language-model hypothesis. A recipe therefore **MUST NOT** author its own disclaimer text; the server owns that surface.
- Whether `confidence` values from an LLM are comparable across runs well enough to drive a threshold in the UI, or whether they are only ordinal within one analysis.
- How the process should treat an entry whose `text` asserts a diagnosis the image contradicts — currently "report both", which may be the wrong default if observers routinely self-diagnose.
- Whether the growth expectation from `base_temp_gdd` is computable at all without local temperature history, and whether Home Assistant sensor data should supply it. Not attempted; it would make the process depend on a second backend.

## Source

- Measured against the reference Kamerplanter instance on 2026-08-05 through `POST /api/v1/mcp`: `tools/list` returned 42 tools with full input schemas; `list_tenants`, `list_pending_diary_analyses`, `get_diary_entry`, `get_plant`, `get_plant_inspections`, `get_species_info`, and `list_phase_definitions` were called read-only for their payload shapes. No write tool was called.
- Image legibility measured with a headless `goose run --no-session` calling `get_diary_entry_photos` at `size: 512` on a queued entry, under Goose 1.45.0 with `GOOSE_PROVIDER=claude-code`
- Field semantics for `claim_diary_analysis` and `submit_diary_analysis` read from their live `inputSchema`, including the `DiaryFindingInput` definition and its deliberate deferral of length and range bounds to the domain model (`REQ-050 §5`)
- Recipe mechanics: [the Goose recipe project pattern](../../goose/recipe-project-pattern/en.md)
- Server contract: [the Kamerplanter MCP server spec](../../mcp/kamerplanter-mcp-server/en.md)
