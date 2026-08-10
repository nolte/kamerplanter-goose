# Kamerplanter MCP Server

Status: draft
Portfolio-Scope: local

## Context

Recipes in this repository reach plant data through the MCP server that ships inside the Kamerplanter backend. That server is not a generic REST mirror: it exposes a curated, semantically high-level tool palette where one tool encapsulates a whole use case and returns compact JSON, instead of the model chaining several REST calls.

Two properties make it worth specifying rather than discovering per recipe. First, the tool catalog is **enumerable and fully schema'd** — every tool declares a complete JSON Schema, so a recipe author can know the whole surface ahead of time by asking once. This is the sharp contrast to [Home Assistant](../home-assistant-mcp-server/en.md), whose catalog is assembled at runtime and differs per instance. Enumerable is not the same as fixed: the catalog grew from 12 tools to 43 between two measurements three days apart, so the surface is knowable per instance and per date rather than once and for all. Second, the server is **multi-tenant with a per-garden permission model**, so the same key may write in one garden and be refused the identical action in another. A recipe that ignores this produces errors that look like bugs but are correct refusals.

Everything below marked *measured* was read from the reference instance via `initialize`, `tools/list`, and read-only `tools/call` invocations — the transport, authentication and tenancy sections on 2026-08-04, the tool catalog and its field shapes on 2026-08-07. The upstream documentation marked the server **partially available** at the first measurement, with 12 of roughly 30 specified tools implemented; the second measurement found 43, so the implementation has overtaken that reading and the documentation is no longer the authority on scope.

Recipe mechanics — where an extension may be declared, how `env_keys` expansion behaves, what the provider adds to the agent — are specified once in [the Goose recipe project pattern](../../goose/recipe-project-pattern/en.md) and are not restated here.

Readers: authors of recipes in this repository, and anyone reviewing a recipe's declared extension block and prompt for correctness.

## Goals

- A recipe author can name the exact tool for a task without inspecting a live server
- The tenant argument, the permission class, and the write/read boundary of every tool are visible before a recipe runs
- Recipes fail with a diagnosable message when the server is disabled, the key is invalid, or the role is insufficient — never with a silent wrong answer
- Write access is a deliberate, declared property of a recipe, not an accident of prompt wording

## Non-Goals

- Documenting the Kamerplanter REST API, the in-app AI assistant, or the knowledge service — the MCP server is a separate, machine-to-machine surface
- Specifying tools that upstream lists as specified-but-unimplemented (setup macros, bulk plant creation, IPM and harvest write tools, the knowledge-base bridge)
- Deployment, scaling, or Helm concerns — the server currently runs in-process with the backend
- Prescribing prompt wording; only the invariants a prompt must preserve

## Interface

### Transport and endpoints

The server implements the **Streamable HTTP** transport under `/api/v1/mcp/`. Measured: `initialize` negotiates protocol revision `2025-06-18`, answers `content-type: application/json`, and **issues an `Mcp-Session-Id`** that subsequent calls echo. `serverInfo` reports `{"name": "kamerplanter-mcp", "version": "1.0"}`.

Declared capabilities, measured: **`tools` only**, with `listChanged: false`. The server advertises no `prompts` and no `resources` — a recipe that expects either gets nothing.

| Method | Path | Purpose | Measured |
|--------|------|---------|----------|
| `POST` | `/mcp` | The MCP endpoint — JSON-RPC 2.0: `initialize`, `tools/list`, `tools/call`, `ping` | ✓ |
| `GET` | `/mcp` | `405` — the server sends no server-initiated messages | ✓ `405` |
| `DELETE` | `/mcp` | Terminates the session named in `Mcp-Session-Id` | not probed |
| `GET` | `/mcp/tools` | REST-friendly tool listing | not probed |
| `POST` | `/mcp/tools/{tool_name}` | REST-friendly tool call, JSON body as arguments | not probed |
| `POST` | `/mcp/rpc` | Retained alias of `POST /mcp` (deprecated) | not probed |

A stdio transport is specified upstream but not implemented; only Streamable HTTP is available.

### Authentication

The server accepts **API keys only** — never a JWT access token, never an interactive session. The key carries the `kp_` prefix and travels as `X-API-Key` or `Authorization: Bearer kp_...`. Measured: a request without a key answers `401`.

The server is **disabled by default**. Unless `MCP_SERVER_ENABLED=true`, every `/mcp/*` endpoint answers `404` — the interface effectively does not exist.

### Tenancy

A key grants exactly the gardens its account is an active member of. Which garden a call applies to is decided per call through the `tenant` argument (the garden's slug); with exactly one membership it may be omitted, with several it is required. The server resolves the **garden first**, then checks permissions — checked the other way round, a key would hold its strongest role everywhere.

A garden the key does not cover answers `not_found`, identical to a garden that does not exist, so the interface cannot be used to discover other users' gardens.

Measured: `list_tenants` returns each garden's `slug`, `name`, `role`, **and its resolved `mcp_permissions` array**. A recipe can therefore establish what it is allowed to do before attempting it, rather than discovering the boundary through a rejection.

### Permission classes

Every tool requires exactly one of three permissions, bound to the role the account holds **in the garden being addressed**:

| Tenant role | `mcp.read` | `mcp.write` | `mcp.setup` | Source |
|-------------|:----------:|:-----------:|:-----------:|--------|
| viewer | ✓ | ✗ | ✗ | documented |
| grower | ✓ | ✓ | ✗ | documented |
| admin | ✓ | ✓ | ✓ | documented |
| `lead` | ✓ | ✓ | ✓ | **measured, undocumented** |

The reference instance's account holds role `lead` with all three permissions. That role appears in no upstream role table. Recipes therefore **must not** infer permissions from the role name; the `mcp_permissions` array is the only reliable source.

A call lacking the permission is rejected with `permission.denied` and audited as `status: "denied"`.

## Tool Catalog (measured, 43 tools, 2026-08-07)

Unlike Home Assistant, **every `inputSchema` carries a full JSON Schema** — measured keys include `required`, `properties`, `$defs`, `additionalProperties`, and `title` — so a client can tell mandatory arguments from optional ones without being told.

The catalog grows between measurements. An inventory on 2026-08-04 returned 12 tools and matched the documentation of the day; a re-inventory on 2026-08-07 returned **43** — 31 more, of which 28 are read tools and three are writes (`add_plant_diary_entry`, `claim_diary_analysis`, `submit_diary_analysis`). **Treat any count here as a floor, not a contract**, and re-run `tools/list` before assuming a tool is absent.

### Read tools (`mcp.read`), 36 measured

Grouped by what a recipe reaches for, not by the server's own layering.

| Group | Tools |
|-------|-------|
| Account and tenancy | `list_tenants`, `get_mcp_activity` |
| Plants | `list_plants`, `get_plant`, `list_plants_at_location`, `list_planting_runs` |
| Species and varieties | `list_species`, `get_species_info`, `list_cultivars`, `get_cultivar` |
| Phases and lifecycle | `list_phase_definitions`, `get_sowing_calendar`, `list_overwintering_profiles`, `list_hardiness_zones` |
| Care and tasks | `list_tasks`, `get_due_care_tasks`, `get_plant_care_log`, `get_harvest_readiness` |
| Nutrition and medium | `get_plant_nutrient_plan`, `list_nutrient_plans`, `get_nutrient_plan`, `list_fertilizers`, `list_substrates`, `calculate_mixing_protocol` |
| Plant protection | `get_plant_inspections`, `list_pests`, `get_pest`, `list_diseases`, `get_disease`, `get_treatment` |
| Diary | `list_diary_entries`, `get_diary_entry`, `get_diary_entry_photos`, `list_pending_diary_analyses` |
| Onboarding and vocabulary | `list_starter_kits`, `search_glossary` |

Signatures worth naming, because a recipe gets them wrong otherwise:

| Tool | Required | Takes `tenant` | Note |
|------|----------|:--------------:|------|
| `get_species_info` | `species_key` | no | `include_cultivars` optional; serves the shared catalog |
| `get_pest` | `pest_key` | no | Returns nested `treatments[]` and `beneficials[]` in one call |
| `get_disease` | `disease_key` | no | Carries `environmental_triggers[]` and `incubation_period_days` |
| `get_treatment` | `treatment_key` | no | Carries `safety_interval_days` — the pre-harvest Karenz |
| `get_plant_inspections` | `plant_key` | yes | IPM history; measured empty on a plant never inspected |
| `get_sowing_calendar` | — | yes | **Refuses an unnarrowed call**: without `query` it answers `validation.error` naming the species count and the `limit` ceiling of 25 |
| `list_phase_definitions` | — | no | 29 definitions measured; the lifecycle engine's vocabulary |
| `search_glossary` | — | no | The project's own definitions of EC, VPD, Karenz |

`calculate_mixing_protocol` computes and persists nothing, which is why it sits among the read tools despite its name.

Fifteen read tools take no `tenant`: `list_tenants` and `get_mcp_activity` are account-scoped, and the species, cultivar, pest, disease, treatment, substrate, glossary, hardiness and phase-definition catalogs are shared across gardens. The split is per tool, read from each `inputSchema` rather than inferred from the group a tool sits in: `list_substrates` takes no `tenant` while `list_fertilizers` in the same group does. For the remaining tenant-scoped tools the argument follows the tenancy rule above — optional on a key with one membership, required on a key with several — so a recipe cannot infer from this section that omitting it is ever safe.

### Write tools (`mcp.write`)

| Tool | Required | Purpose |
|------|----------|---------|
| `add_plant_diary_entry` | `plant_key`, `text` | Record an observation, problem, or measurement |
| `confirm_care_task` | `plant_key`, `reminder_type` | Confirm a care reminder for a plant |
| `archive_plant` | `plant_key` | Mark a plant disposed / given away / died — never a hard delete |
| `set_plant_location` | `plant_key` | Move a plant to another site, location, or slot |
| `claim_diary_analysis` | `entry_key`, `worker_id` | Claim an entry for analysis under a lease |
| `submit_diary_analysis` | `entry_key`, `lease_token`, `status` | Write a result back and end the claim |

### Setup tool (`mcp.setup`)

| Tool | Required | Purpose |
|------|----------|---------|
| `create_site` | `name` | Create a site root (apartment, garden, balcony, greenhouse, windowsill, grow tent) |

Measured: every state-changing tool exposes `dry_run` and `idempotency_key`, and no read tool carries either — which is the cheapest way to tell the two classes apart in a `tools/list` response. `tenant` does **not** separate them: all seven state-changing tools take it — the six `mcp.write` tools and the one `mcp.setup` tool — and so do 21 of the 36 reads. Writes are tenant-scoped like everything else, so the tenancy rule above applies to them in full: on a key covering several gardens, omitting `tenant` on a write is an error, not a default.

### What the catalog does not carry

Two absences matter, because a process that assumes the field exists produces a confident answer with nothing behind it. Both measured 2026-08-07:

- **`get_pest` has no humidity, host-range, prevention, or monitoring fields.** Measured on `Tetranychus urticae`, the record is `pest_key`, `scientific_name`, `common_name`, `common_name_de`, `pest_type`, `damage_symptoms`, `lifecycle_days`, `optimal_temp_min`, `optimal_temp_max`, `description`, `detection_symptom_hint`, plus nested `treatments[]` and `beneficials[]`. There is no `optimal_humidity_min/max`, no `host_plants`, no `prevention_tips`, no `monitoring_hints`, no `affected_plant_parts`, no severity or detection-difficulty rating, and no GBIF key. `get_disease` **does** carry `environmental_triggers[]` (`low_humidity`, `high_humidity`, `poor_air_circulation`, …), so the moisture axis exists for diseases and not for pests.
- **`get_species_info` returns only the populated fields**, and the set differs per species. Measured, `Allium porrum` returned 23 fields including a full `seed_profile` (`germination_temp_min_c`/`max_c`, `sowing_depth_cm`, `days_to_germination`, `seed_viability_years`, `light_germination`, `pretreatment[]`, `thousand_seed_weight_g`, `sowing_density_per_m2`) and `growing_periods[]`; `Spathiphyllum wallisii` returned 18, with `plant_category` and no `seed_profile` at all. Neither carried `toxicity`, although the tool's own description advertises it. A missing key means "not populated for this species", never "does not apply".

### Response envelope

Measured, a `tools/call` result carries `isError`, an MCP-standard `content` array with the summary as `type: "text"`, and a **`structuredContent`** object holding the three documented fields: `summary` (one-sentence recap), `data` (the structured result), `links` (pointers into the UI or REST API). The documented envelope is therefore nested under `structuredContent`, not at the top level.

`dry_run` (default `false`) returns the planned effect without persisting. `idempotency_key` makes an identical key from the same account, tenant, and tool replay the original result for 24 hours, marked `"idempotent_replay": true`.

Every call is audited with a SHA-256 hash of the arguments — never plaintext, never the key. Audit entries are removed after 90 days.

## Requirements

- **MUST** reach the server through a `streamable_http` extension pointing at `${KAMERPLANTER_URL}/api/v1/mcp`, declared either in the recipe's own `extensions:` block or in the repository's shared `extensions.yaml`
- **MUST** list `KAMERPLANTER_URL` and `KAMERPLANTER_API_KEY` in that extension's `env_keys`, wherever it is declared; without it Goose sends the literal `${...}` string as the header value
- **MUST** pass the credential as the `X-API-Key` header, never as a URL parameter and never inline in a recipe or config file
- **MUST** resolve the garden explicitly: either accept a `tenant` recipe parameter or call `list_tenants` first; a recipe **MUST NOT** assume the key covers exactly one garden
- **MUST** name every forbidden state-changing tool individually in the recipe's `prompt` when the recipe is read-only — `instructions` alone is not enforced on a headless run. The catalog measurement raised that list from four to seven: `confirm_care_task`, `archive_plant`, `set_plant_location`, `create_site`, `add_plant_diary_entry`, `claim_diary_analysis`, `submit_diary_analysis` (six `mcp.write` plus the one `mcp.setup`). Naming a subset is the failure this rule exists to catch, and a category ("and anything else that writes") does not substitute for any of the seven: the prohibition must not depend on the model's classification. A write-capable `-apply` recipe is the exception the word *forbidden* already carries — the tools it exists to call are declared, not prohibited
- **MUST** carry the `-apply` suffix in its filename and state the effect in its `description` when a recipe calls any `mcp.write` or `mcp.setup` tool
- **MUST NOT** infer what it may do from a garden's role name; the `mcp_permissions` array from `list_tenants` is the only reliable source, and undocumented roles exist
- **MUST NOT** expect `prompts` or `resources` from this server; it advertises the `tools` capability only
- **SHOULD** read `mcp_permissions` from `list_tenants` before attempting a write, and report a missing permission as a precondition rather than provoking `permission.denied`
- **SHOULD** call a write tool with `dry_run: true` first when the recipe reports a planned action to a human before executing it
- **SHOULD** pass an `idempotency_key` on every write call so a retried run does not duplicate the action
- **SHOULD** treat `not_found` for a named garden as "not covered by this key" rather than "does not exist", and say so in the report
- **MUST NOT** interpret `404` on the endpoint as a wrong URL without also naming `MCP_SERVER_ENABLED` as the likely cause; a missing or invalid key answers `401`, which is a different fault
- **MUST NOT** call a tool that this spec's catalog does not list; unlisted tools are unimplemented upstream
- **MAY** use the REST-friendly `POST /mcp/tools/{tool_name}` form for diagnostics outside a recipe, but **MUST NOT** rely on it from inside one

## Acceptance Criteria

- [ ] The extension is declared exactly once — in the recipe or in `extensions.yaml` — naming `streamable_http`, the `/api/v1/mcp` path, and both env keys
- [ ] `goose recipe validate` passes on the recipe
- [ ] A run against a server with `MCP_SERVER_ENABLED` unset reports the opt-in variable, not a URL error
- [ ] A run with a missing or revoked key reports `401` as an authentication failure, distinct from a permission failure
- [ ] Every read-only recipe names all seven state-changing tools in its `prompt`, individually — never a subset, never a category standing in for a name
- [ ] A machine check enforces the criterion above; a rule stated only in prose has drifted from the recipes twice
- [ ] Every recipe calling a write tool has an `-apply` filename and says so in `description`
- [ ] A recipe run against a key covering two gardens either takes `tenant` as a parameter or calls `list_tenants` before any tenant-scoped tool
- [ ] No recipe derives permission from a role name rather than from `mcp_permissions`
- [ ] No recipe references a tool outside the catalog above
- [ ] No recipe issues `prompts/list` or `resources/list` against this server

## Open Questions

- Three shipped recipes do not satisfy the criterion above: `connectivity-check` names four of seven, and `provider-surface-check` and `provider-plugin-check` name none, relying on a blanket instead. The conforming prompts and the validator check that enforces them are on `refactor/recipe-validator-guard`; until that lands, the criterion is a statement of intent and not a measured property of this repository.

- The role `lead` is measured on the reference instance but appears in no upstream role table. Whether it is a rename of `admin`, a distinct fourth role, or instance-local configuration is unresolved — hence the rule to read `mcp_permissions` rather than the role.
- Whether the `Mcp-Session-Id` must be echoed on every call or only within a session window; the reference probe echoed it throughout and was not tested without it.
- Whether `get_mcp_activity` is useful as a self-audit step at the end of an `-apply` recipe, or whether it only adds noise.
- This spec has no mechanism for detecting that the live server offers tools it does not list. As of the 2026-08-07 re-inventory the two agree — all 43 are listed here — but nothing keeps them agreeing, and the drift that made this section wrong was caught by hand, three days after it opened. Separately, and unrelated to that gap: upstream still documents the catalog as growing toward roughly 30, which the implementation has passed.

## Source

- Live measurement of the reference instance, 2026-08-04: `initialize` (protocol `2025-06-18`, `Mcp-Session-Id`, `tools`-only capabilities), `tools/list` (12 tools with full JSON Schema), `tools/call list_tenants` (role `lead`, `mcp_permissions`, `structuredContent` envelope), `GET /mcp` → `405`, unauthenticated `POST` → `401`
- Per-tool `tenant`, `dry_run` and `idempotency_key` classification derived from the 2026-08-07 `tools/list` response by testing each tool's `inputSchema.properties` for those keys — not from the grouping in this document, and not from calling anything: no write tool was invoked, so the claim is about the declared schema and not about observed behaviour
- Live measurement of the reference instance, 2026-08-07: `tools/list` (43 tools), and read-only `tools/call` for `list_tenants`, `list_pests`, `get_pest` (`Tetranychus urticae`), `list_diseases`, `list_species`, `get_species_info` (`Allium porrum`, `Spathiphyllum wallisii`), `list_plants`, `get_plant_inspections`, `list_phase_definitions`, `list_overwintering_profiles`, and `get_sowing_calendar` (both unnarrowed, which was refused, and with `query`). No write tool was called.
- `nolte/kamerplanter` — `docs/en/api/mcp-server.md` (transport, authentication, tenancy, documented permission classes, tool purposes, audit trail), read 2026-08-04
- Goose `env_keys` behaviour measured against Goose 1.45.0 by capturing the requests it issues; see `README.md` §Notes
