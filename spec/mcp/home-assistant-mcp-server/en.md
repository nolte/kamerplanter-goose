# Home Assistant MCP Server

Status: draft
Portfolio-Scope: local

## Context

Recipes in this repository read sensor state and — where a recipe declares it — actuate devices through the MCP Server integration built into Home Assistant. It is the second of the two backends these recipes combine, and it behaves fundamentally differently from the first.

The Kamerplanter MCP server has a **fixed, enumerable** tool catalog: a recipe author can name every tool ahead of time. Home Assistant does not. Its tool list is **assembled at runtime** from every installed integration that registers an LLM tools platform, sorted by domain, and scoped by which entities the operator has exposed to Assist (`homeassistant/components/llm/__init__.py`, `async_get_tools`). Two Home Assistant instances running the same version legitimately offer different tools. A platform that raises during collection is logged and skipped, so the catalog can also shrink silently between runs.

This is the load-bearing consequence for recipes here: **a recipe must not hard-code a Home Assistant tool name and assume it exists.** What can be specified is the discovery mechanism, the authentication contract, the shape of what comes back, and the rules a recipe follows given that uncertainty.

The catalog section below is a **measurement of the reference instance**, taken 2026-08-04, not a contract. It is recorded because it shows what the mechanism actually produces — including two tools that exist only on that instance.

Readers: authors of recipes in this repository, and operators wiring a Home Assistant instance up to them.

## Goals

- A recipe author knows which properties of this server are guaranteed and which are instance-specific
- A recipe degrades to a diagnosable report when an expected tool is absent, instead of inventing an answer
- Actuation is a declared, reviewable property of a recipe, never an emergent one
- The measured tool surface of the reference instance is on record, so drift becomes visible

## Non-Goals

- Specifying which entities an operator should expose to Assist — that is instance policy
- Documenting the Home Assistant REST or WebSocket API, or the `kamerplanter-ha` custom integration's entities
- Prescribing custom intents; the reference instance's own intents are recorded, not mandated
- OAuth client registration flows — recipes here use a long-lived access token

## Interface

### Transport and endpoint

The server is exposed at `/api/mcp` over the **Streamable HTTP** transport. Measured against the reference instance: `initialize` negotiates protocol revision `2024-11-05`, answers `content-type: application/json`, and issues **no `Mcp-Session-Id` header** — subsequent calls succeed without echoing a session.

`serverInfo` reports `{"name": "home-assistant", "version": "1.26.0"}`. Declared capabilities: `prompts`, `resources`, and `tools`, each with `listChanged: false`; `resources.subscribe: false`.

### Authentication

Two mechanisms are supported: OAuth via Home Assistant's IndieAuth (no pre-registered client ID) and a **long-lived access token** from the user's profile security settings. Recipes here use the token, sent as `Authorization: Bearer <token>`.

### How the tool catalog is assembled

1. The integration is configured against one LLM API; the default and backwards-compatible value is the built-in **Assist** API (`llm.LLM_API_ASSIST`).
2. `async_get_tools` iterates every integration that registered an LLM tools platform, **sorted by domain** so tool order does not depend on load order, and concatenates their tools.
3. An integration platform that raises is logged and skipped — its tools vanish from the catalog without an error reaching the client.
4. Each tool is converted to an MCP tool whose `inputSchema` is built as `{"type": "object", "properties": ...}`.

**Consequence — the schema carries no `required` list.** Verified live against the reference instance: across all 25 tools the only `inputSchema` keys present are `properties` and `type`. A client cannot tell which arguments are mandatory from the schema alone.

### Resources and prompts

Where the selected API exposes `GetLiveContext`, the server also publishes a read-only resource. Measured: one resource, `assist_context_snapshot` at `homeassistant://assist/context-snapshot`, mime type `text/plain`, described as matching the `GetLiveContext` tool output. `prompts/list` returns one prompt named after the API — measured: `Assist`.

## Tool Catalog (measured, reference instance, 2026-08-04)

25 tools. **This is a snapshot, not a contract.** Grouping by effect is this spec's classification, derived from tool names and descriptions.

### Read-only

| Tool | Notes |
|------|-------|
| `GetLiveContext` | Current state of devices, sensors, entities, areas. Filters: `name`, `domain` (single or list), `area` |
| `GetDateTime` | Current date and time; no arguments |
| `todo_get_items` | Queries a to-do list. `todo_list` is an enum of the instance's lists; `status` filters `needs_action` / `completed` / `all`, default `needs_action` |

The `todo_list` enum on the reference instance contains **`Kamerplanter Tasks`**, `Shopping List`, `Sourdough`, and `gardening`. The first is surfaced by the `kamerplanter-ha` integration, which means plant tasks are reachable through *both* backends. Recipes must decide deliberately which one is authoritative.

### Actuating

`HassTurnOn`, `HassTurnOff`, `HassSetPosition`, `HassStopMoving`, `HassCancelAllTimers`, `HassListAddItem`, `HassListCompleteItem`, `HassListRemoveItem`, `HassClimateSetTemperature`, `HassBroadcast`, `HassLightSet`, `HassMediaUnpause`, `HassMediaPause`, `HassMediaNext`, `HassMediaPrevious`, `HassSetVolume`, `HassSetVolumeRelative`, `HassMediaPlayerMute`, `HassMediaPlayerUnmute`, `HassMediaSearchAndPlay`.

### Instance-specific, effect unclassified

| Tool | Measured surface |
|------|------------------|
| `TimeTillErnte` | Description is the generic `Execute Home Assistant TimeTillErnte intent`; arguments are the standard entity filters `name`, `area`, `floor`, `domain`, `device_class` |
| `time_till` | Description is `Aliases: ['Ernte', 'ernten', 'time_till']`; no arguments |

Both are custom intents of the reference instance and appear on no stock Home Assistant. Their generic descriptions give a model little to work with, and this spec cannot state whether either has side effects. Until the operator classifies them, recipes treat them as unclassified.

## Requirements

- **MUST** reach the server through a `streamable_http` extension pointing at `${HA_URL}/api/mcp`, declared either in the recipe's own `extensions:` block or in the repository's shared `extensions.yaml`
- **MUST NOT** declare an `extensions:` block of its own when it relies on the shared `extensions.yaml`; a recipe-local block **replaces** the shared set instead of extending it, silently dropping every server the recipe does not redeclare
- **MUST** list `HA_URL` and `HA_MCP_TOKEN` in that extension's `env_keys`, wherever it is declared; without it Goose sends the literal `${...}` string as the header value
- **MUST** pass the credential as `Authorization: Bearer <token>`, never inline in a recipe or config file
- **MUST** discover the available tools at runtime and **MUST NOT** assume any named Home Assistant tool exists; every tool reference in a `prompt` is conditional ("prefer X if present, otherwise …")
- **MUST** report an absent expected tool as an explicit step result, never silently substitute a different tool or answer from memory
- **MUST** state required arguments in the `prompt` when calling a tool whose mandatory arguments matter — the server's `inputSchema` omits `required`, so the model cannot infer them
- **MUST** forbid actuation in the `prompt` — not only in `instructions` — for any recipe that is not an `-apply` recipe, and **MUST** name the categories it forbids (turning devices on or off, setting values, running scripts, scenes, or automations)
- **MUST** name the authoritative source in its prompt when a recipe touches plant tasks, since the `Kamerplanter Tasks` to-do list mirrors data that Kamerplanter's own MCP server also serves
- **MUST NOT** call `TimeTillErnte` or `time_till` from a read-only recipe while their effect is unclassified
- **SHOULD** prefer `GetLiveContext` for state reads, since it is the documented state-query entry point and backs the published resource
- **SHOULD** treat a shrinking tool list as an instance-side failure worth reporting: an integration platform that raises is skipped silently upstream
- **MAY** read the `homeassistant://assist/context-snapshot` resource instead of calling `GetLiveContext` when a recipe wants the whole snapshot rather than a filtered view
- **MAY** rely on OAuth instead of a long-lived token when a future client supports it

## Acceptance Criteria

- [ ] The extension is declared exactly once — in the recipe or in `extensions.yaml` — naming `streamable_http`, the `/api/mcp` path, and both env keys
- [ ] No recipe relying on the shared `extensions.yaml` declares an `extensions:` block of its own
- [ ] `goose recipe validate` passes on the recipe
- [ ] No recipe prompt asserts unconditionally that a specific Home Assistant tool exists
- [ ] A run against an instance lacking an expected tool produces a step marked as skipped or failed, naming the tool
- [ ] A run with an invalid token reports an authentication failure distinct from an empty tool list
- [ ] Every non-`-apply` recipe forbids the actuating tool categories inside `prompt`
- [ ] No read-only recipe calls `TimeTillErnte` or `time_till`
- [ ] A recipe reading plant tasks names whether Kamerplanter or the `Kamerplanter Tasks` list is authoritative

## Open Questions

- What `TimeTillErnte` and `time_till` actually do, and whether either has side effects. Until the operator answers, both stay unclassified and off-limits to read-only recipes.
- Whether the `Kamerplanter Tasks` to-do list is a read-only projection of Kamerplanter or independently writable from Home Assistant. This decides whether a recipe may ever complete a task there.
- Whether the absence of an `Mcp-Session-Id` header is stable behaviour or an artifact of this version; the transport permits sessions and a future release may issue one.
- Whether recipes should assert a minimum expected tool set at startup and abort, or degrade per step. This spec currently requires degrade-per-step.

## Source

- Live measurement of the reference instance, 2026-08-04: `initialize`, `tools/list` (25 tools), `resources/list`, `prompts/list`. Endpoint and credential from the repository's `.envrc`
- `home-assistant/core` — `homeassistant/components/mcp_server/server.py` (server name, tool formatting, `GetLiveContext` resource) and `homeassistant/components/llm/__init__.py` (`async_get_tools`: platform iteration, domain sort, skip-on-exception), read 2026-08-04
- Home Assistant documentation — [MCP Server integration](https://www.home-assistant.io/integrations/mcp_server/) (endpoint, transport, OAuth and long-lived token authentication)
- Goose `env_keys` behaviour measured against Goose 1.45.0; see `README.md` §Notes
