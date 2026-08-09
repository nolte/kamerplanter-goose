# Audiences — kamerplanter-goose

<!--
Produced via the `audience-identify` skill, following
spec/project/audience-identification/.
Do not add audiences without first declaring the bounded context below.
-->

## Bounded context

**kamerplanter-goose** is a catalog of shareable Goose recipes that wire Kamerplanter and Home Assistant into repeatable plant-care runs, together with everything that makes them runnable.

- **Inside the boundary:** the recipes (`recipes/`), the shared MCP extension definitions (`extensions.yaml`), the project skills (`.claude/skills/`), the queue runner (`scripts/`), the specifications (`spec/`), and the documentation site (`docs/`).
- **Explicitly outside:** the Kamerplanter backend and its MCP server, the Home Assistant instance and its MCP integration, Goose itself, the `kamerplanter-ha` integration, and provider or model selection. The repository declares which MCP servers a recipe needs and nothing about where those servers run.

Recipes are meant to be consumed by operators other than the maintainer today, not eventually — that decision is what makes "Plant owners running Goose" a primary audience rather than an aspiration.

## Audiences

Each entry: label, stable ID, relationship category, interaction surface,
expectation, documentation `track` (`user-docs` or `developer-docs` per
spec/project/docs-audience-tracks/), open questions, `confirmed` or `assumed`,
criticality (primary / secondary / peripheral).

The ID is what downstream artifacts reference — page frontmatter under
`docs/<lang>/`, issue templates, release notes. A label may be reworded; an ID
is renamed only with its consumers.

### Direct consumers

- **Plant owners running Goose** — _id_: `plant-owner` · _category_: direct-consumer · _surface_: `goose run --recipe <name>`, recipe parameters, the PASS/FAIL report each run prints ·
  _expects_: recipes that run against their own garden without editing a file, and a named reason when a run refuses · _track_: `user-docs` ·
  _status_: `confirmed` · _criticality_: primary
  - Open questions: the validating source is not recorded here — note who was consulted, so `spec-drift-audit` can retire the tag if it turns out to rest on inference. Recipe names and parameters are still declared unstable in the README; that contradicts a primary consumer audience and is resolved by the first tagged release.

- **Recipe authors** — _id_: `recipe-author` · _category_: direct-consumer · _surface_: `recipes/*.yaml` as the house pattern, `spec/goose/recipe-project-pattern/`, `.claude/skills/`, `goose recipe validate` ·
  _expects_: one shared shape for plant-care agents — naming, parameters, extension configuration, read-versus-write boundary — plus the measured Goose failure modes up front rather than one debugging session at a time · _track_: `developer-docs` ·
  _status_: `assumed` · _criticality_: primary
  - Open questions: whether authors outside this repository consume the pattern by copying it or by forking; the former needs the spec published, the latter needs the repo installable.

### Operators

- **Self-hosters running Kamerplanter and Home Assistant** — _id_: `self-hoster` · _category_: operator · _surface_: `.envrc`, `extensions.yaml`, the environment variables every recipe consumes, `connectivity-check` ·
  _expects_: one documented set of environment variables that a recipe added next month needs no new wiring for, and a diagnostic that distinguishes an unset credential from an unreachable server · _track_: `developer-docs` ·
  _status_: `confirmed` · _criticality_: primary
  - Open questions: none.

- **Unattended queue operator** — _id_: `queue-operator` · _category_: operator · _surface_: `scripts/analyse-queue.sh` under cron or a timer, its exit code and summary lines ·
  _expects_: that a claimed diary entry is never left under a dangling lease, that one entry's failure cannot reach the next, and that the outcome is greppable without reading the transcript · _track_: `developer-docs` ·
  _status_: `assumed` · _criticality_: secondary
  - Open questions: no alerting path exists for a run that fails repeatedly; whether that belongs here or in the caller's scheduler is undecided.

### Contributors / maintainers

- **Maintainer** — _id_: `maintainer` · _category_: contributor · _surface_: `spec/`, `CLAUDE.md`, the git history, the recipe and skill sources ·
  _expects_: that measured Goose behaviour is recorded with its measurement date and version, so a Goose upgrade is re-verifiable rather than re-discovered · _track_: `developer-docs` ·
  _status_: `confirmed` · _criticality_: primary
  - Open questions: none.

- **External contributors** — _id_: `external-contributor` · _category_: contributor · _surface_: pull requests, `spec/goose/recipe-project-pattern/` as the review standard ·
  _expects_: a stated contribution path and a licence that permits reuse · _track_: `developer-docs` ·
  _status_: `assumed` · _criticality_: peripheral
  - Open questions: none known today. The MIT licence and the first release are the precondition for this audience existing at all.

### Governing parties

- `none` — private project with no compliance body, architecture review board, or legal approver. Recorded as considered, not omitted.
  - See the cross-cutting open questions below: the absence of a governing party does not remove the photo-processing and credential-handling constraints, it only means nobody external enforces them.

### Indirect audiences

- **Other members of the same Kamerplanter garden** — _id_: `garden-member` · _category_: indirect · _surface_: none in this repository; they read the AI analyses that the `-apply` recipes write into shared diary entries ·
  _expects_: that a submitted analysis is legible, states its evidence, and refuses rather than invents when a photo cannot answer the question · _track_: `user-docs` ·
  _status_: `assumed` · _criticality_: peripheral
  - Open questions: the garden has one member today; a second member is a revisit trigger, and this entry moves from peripheral to secondary when that happens.

## Open questions (cross-cutting)

- The `-apply` recipes send plant photos to a language model provider and the runs hold Kamerplanter and Home Assistant credentials. No governing party enforces a constraint on either, so the constraint is carried by recipe prompts and `.envrc` discipline alone. Whether that warrants a written data-handling note is undecided.
- The README declares recipe names and parameters unstable while naming outside plant owners as a target. Those two statements cannot both hold once the first release ships.
- No audience has been asked what a failing run should do beyond printing a table; alerting and retry expectations are unmapped for every entry.

## Revisit triggers

- The first tagged release and the MIT licence landing — external contributors and outside plant owners become reachable audiences at that point
- A second member joining the Kamerplanter garden
- A recipe that actuates a Home Assistant device rather than only reading it — that adds a physical-effect surface no current audience entry covers
- A new MCP backend beyond Kamerplanter, Home Assistant, and GitHub
- A Goose or provider version bump that changes the measured tool surface recorded in `spec/goose/recipe-project-pattern/`
