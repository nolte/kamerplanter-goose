# Kamerplanter MCP Server

Status: draft
Portfolio-Scope: local

## Context

Recipes in this repository reach plant data through the MCP server that ships inside the Kamerplanter backend. That server is not a generic REST mirror: it exposes a curated, semantically high-level tool palette where one tool encapsulates a whole use case and returns compact JSON, instead of the model chaining several REST calls.

Two properties make it worth specifying rather than discovering per recipe. First, the tool catalog is **fixed and enumerable** — measured live, the server offers exactly the 12 tools the upstream documentation lists, so a recipe author can know the full surface ahead of time. This is the sharp contrast to [Home Assistant](../home-assistant-mcp-server/en.md), whose catalog is assembled at runtime and differs per instance. Second, the server is **multi-tenant with a per-garden permission model**, so the same key may write in one garden and be refused the identical action in another. A recipe that ignores this produces errors that look like bugs but are correct refusals.

Everything below marked *measured* was read from the reference instance on 2026-08-04 via `initialize`, `tools/list`, and a read-only `list_tenants` call. The upstream documentation marks the server **partially available**: the 12 tools are what is implemented; roughly 30 are specified in total.

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

## Tool Catalog (measured, 12 tools, 2026-08-04)

The live catalog matches the documented one exactly. Unlike Home Assistant, **every `inputSchema` carries a full JSON Schema** — measured keys include `required`, `properties`, `$defs`, `additionalProperties`, and `title` — so a client can tell mandatory arguments from optional ones without being told.

### Read tools (`mcp.read`)

| Tool | Required | Takes `tenant` | Purpose |
|------|----------|:--------------:|---------|
| `list_tenants` | — | no | Gardens the key covers, with role and `mcp_permissions` |
| `list_species` | — | no | Plant species catalog (`limit`, `offset`) |
| `get_species_info` | `species_key` | no | Master data for a species, incl. companion-planting hints |
| `list_planting_runs` | — | yes | Planting runs (`status`, `limit`, `offset`) |
| `list_tasks` | — | yes | Tasks (`status`, `limit`, `offset`) |
| `get_due_care_tasks` | — | yes | Due and overdue care reminders (`urgency`) |
| `get_harvest_readiness` | — | yes | Harvest-readiness overview (`limit`) |
| `get_mcp_activity` | — | no | The account's own MCP call history (`limit`) |

Three read tools take no `tenant`: `list_tenants` and `get_mcp_activity` are account-scoped, and `list_species` / `get_species_info` serve the shared species catalog.

### Write tools (`mcp.write`)

| Tool | Required | Purpose |
|------|----------|---------|
| `confirm_care_task` | `plant_key`, `reminder_type` | Confirm a care reminder for a plant |
| `archive_plant` | `plant_key` | Mark a plant disposed / given away / died — never a hard delete |
| `set_plant_location` | `plant_key` | Move a plant to another site, location, or slot |

### Setup tool (`mcp.setup`)

| Tool | Required | Purpose |
|------|----------|---------|
| `create_site` | `name` | Create a site root (apartment, garden, balcony, greenhouse, windowsill, grow tent) |

Measured: all four state-changing tools expose `tenant`, `dry_run`, and `idempotency_key`.

### Response envelope

Measured, a `tools/call` result carries `isError`, an MCP-standard `content` array with the summary as `type: "text"`, and a **`structuredContent`** object holding the three documented fields: `summary` (one-sentence recap), `data` (the structured result), `links` (pointers into the UI or REST API). The documented envelope is therefore nested under `structuredContent`, not at the top level.

`dry_run` (default `false`) returns the planned effect without persisting. `idempotency_key` makes an identical key from the same account, tenant, and tool replay the original result for 24 hours, marked `"idempotent_replay": true`.

Every call is audited with a SHA-256 hash of the arguments — never plaintext, never the key. Audit entries are removed after 90 days.

## Requirements

- **MUST** reach the server through a `streamable_http` extension pointing at `${KAMERPLANTER_URL}/api/v1/mcp`, declared either in the recipe's own `extensions:` block or in the repository's shared `extensions.yaml`
- **MUST** list `KAMERPLANTER_URL` and `KAMERPLANTER_API_KEY` in that extension's `env_keys`, wherever it is declared; without it Goose sends the literal `${...}` string as the header value
- **MUST** pass the credential as the `X-API-Key` header, never as a URL parameter and never inline in a recipe or config file
- **MUST** resolve the garden explicitly: either accept a `tenant` recipe parameter or call `list_tenants` first; a recipe **MUST NOT** assume the key covers exactly one garden
- **MUST** name every forbidden write tool in the recipe's `prompt` when the recipe is read-only — `instructions` alone is not enforced on a headless run; the four to name are `confirm_care_task`, `archive_plant`, `set_plant_location`, `create_site`
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
- [ ] A read-only recipe names all four state-changing tools as forbidden inside `prompt`
- [ ] Every recipe calling a write tool has an `-apply` filename and says so in `description`
- [ ] A recipe run against a key covering two gardens either takes `tenant` as a parameter or calls `list_tenants` before any tenant-scoped tool
- [ ] No recipe derives permission from a role name rather than from `mcp_permissions`
- [ ] No recipe references a tool outside the catalog above
- [ ] No recipe issues `prompts/list` or `resources/list` against this server

## Open Questions

- The role `lead` is measured on the reference instance but appears in no upstream role table. Whether it is a rename of `admin`, a distinct fourth role, or instance-local configuration is unresolved — hence the rule to read `mcp_permissions` rather than the role.
- Whether the `Mcp-Session-Id` must be echoed on every call or only within a session window; the reference probe echoed it throughout and was not tested without it.
- Whether `get_mcp_activity` is useful as a self-audit step at the end of an `-apply` recipe, or whether it only adds noise.
- The upstream catalog is documented as growing to roughly 30 tools. This spec has no mechanism yet for detecting that the live server offers tools this document does not list; today they match exactly.

## Source

- Live measurement of the reference instance, 2026-08-04: `initialize` (protocol `2025-06-18`, `Mcp-Session-Id`, `tools`-only capabilities), `tools/list` (12 tools with full JSON Schema), `tools/call list_tenants` (role `lead`, `mcp_permissions`, `structuredContent` envelope), `GET /mcp` → `405`, unauthenticated `POST` → `401`
- `nolte/kamerplanter` — `docs/en/api/mcp-server.md` (transport, authentication, tenancy, documented permission classes, tool purposes, audit trail), read 2026-08-04
- Goose `env_keys` behaviour measured against Goose 1.45.0 by capturing the requests it issues; see `README.md` §Notes
