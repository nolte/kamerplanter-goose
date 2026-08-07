# Grower Persona Review

Status: draft
Portfolio-Scope: local

## Context

A recipe in this repository tells someone what to do with a living plant. The report it prints is the product — not the tool calls behind it, not the YAML. Two things can be wrong with that product, and neither is caught by anything currently in the repository:

- **The advice is agronomically wrong.** `tests/validate_recipes.py` checks the house pattern; `goose recipe validate` checks the schema; the process specs constrain the reasoning. None of them notices that a recommendation is biologically unsound, that a proposed EC target is out of range for the crop, or that a treatment is being suggested inside a harvest interval.
- **The advice is agronomically fine and useless to its reader.** A report that opens with "tier 2 evidence indicates a conductivity deviation of 0.4 mS/cm against the phase target" is correct and will be closed unread by someone with three houseplants. A report that never mentions runoff EC is useless to someone running a tent. The same run cannot satisfy both, and pretending otherwise is how software ends up serving neither.

This spec establishes a review that reads a recipe, a process spec, or a run's actual output **as a specific grower**, and reports what that grower would do with it. Four personas, deliberately far apart, inherited from the reviewer cluster in `nolte/kamerplanter` where they were applied to requirement documents. Here they are applied to recipes and to the reports recipes produce.

**These are not the audiences in `AUDIENCES.md`.** That file describes who consumes *this repository* — `plant-owner`, `recipe-author`, `self-hoster`, and the rest — and its IDs are referenced by documentation frontmatter and issue templates. The personas here are the growing situations a recipe's advice lands in. One `plant-owner` may be any of the four, and the four disagree with each other about the same report. The two axes are orthogonal; a review under this spec must not renumber, extend, or cite `AUDIENCES.md` IDs as though they were personas.

Readers: recipe authors in this repository, and anyone deciding whether a recipe is ready to be run against a real garden.

## Goals

- A recipe's advice is judged for agronomic soundness by someone qualified to see the error, and for usability by the people who will actually receive it
- Each persona's verdict is separable, because a report that is excellent for one and unusable for another is a real result, not a contradiction to be averaged away
- A finding names the consequence for that persona — abandoned app, wasted release, dead plant — rather than a style preference
- No agronomic correction enters a review on the strength of the reviewer's recall
- The review target may be a recipe, a process spec, or a run's real output, since a recipe can be well-specified and still print something unusable

## Non-Goals

- Reviewing recipe mechanics — extension blocks, `env_keys`, `-apply` suffixes, working-directory declarations. `tests/validate_recipes.py` and [the recipe project pattern](../../goose/recipe-project-pattern/en.md) own that, and duplicating it here would put one rule in two layers
- Judging an individual plant's condition; the personas review the process, not a garden
- Correcting the pest, species or nutrient catalogs — findings about data go to [pest pressure assessment](../pest-pressure-assessment/en.md) and [species baseline verification](../species-baseline-verification/en.md), and corrections to `nolte/kamerplanter`
- Editing prose for its own sake; a readability finding must name the persona it blocks
- Replacing the audience artefact in `AUDIENCES.md` or the documentation tracks derived from it
- Producing a consensus verdict across personas

## The personas

Each is a review lens with a fixed profile, a fixed vocabulary boundary, and a fixed reason it would walk away. The profile is what makes the finding predictable rather than a matter of the reviewer's mood, and it is quoted from the source cluster rather than reinvented.

### `agronomy` — the plant scientist

Twenty years of practice, weighted toward indoor growing, houseplants, hydroponics and controlled-environment agriculture, with outdoor phenology as a comparison base. Reads for **biological correctness**: plant physiology under artificial conditions, light (PPFD, DLI, spectrum, photoperiod), climate control (VPD, CO₂, DIF, air movement), integrated pest management, taxonomy and nomenclature.

Asks: is this claim true, is this recommendation safe, does this reasoning chain hold, and is a species-specific value being asserted that nobody verified?

This lens carries the strictest evidence rule in the spec and is the only one licensed to make agronomic corrections.

### `indoor-grower` — the tent operator

Ten years in a 120×120×200 cm tent, 480 W LED, inline extraction with carbon filter, coco-perlite fertigation, photoperiod and autoflowering genetics, mother plants and cuttings. Trains with topping, LST, SCROG, lollipopping. Runs a trichome scope, logs temperature and humidity through dry and cure, and measures success in grams per square metre.

Asks: can I map my whole cycle in this, does it help me get more and better, is this practical or only theoretically nice, and would I use it every day?

Finds the gap between a workflow that is *covered* and one that is *usable at 11 pm with wet hands*.

### `casual-owner` — the reluctant houseplant keeper

Thirty-two, office job, three houseplants, one of them unidentified. Botanical knowledge near zero. Two plants died last year. Motivation minimal, patience shorter: more than three taps is an annoyance, and any hurdle is a reason to stop. Does not read Latin. **"EC", "VPD" and "PPFD" are foreign words that actively repel.** Wants a push notification saying "water your monstera" and nothing else.

Asks: what do I actually do now, why do I have to fill this in, can you say that in plain language, and would I delete this after two days?

This lens produces the findings nobody else can produce, because everyone else already knows the vocabulary. Its verdict is a proxy for whether the software survives first contact with an ordinary person.

### `outdoor-gardener` — the allotment planner

Forty-five, fifteen years' practice, a 400 m² home garden plus an 80 m² plot in a community garden, Central Europe (USDA 7b–8a). Around 120 plants at once, 40 of them perennial. Systematic four-year rotation, companion planting, February propagation on the windowsill and in a polytunnel, own compost and nettle brew, rainwater from an IBC. Overwinters container plants, lifts dahlias, mulches beds. Moderate technical affinity; has tried three garden apps and none did everything.

Asks: what goes where and when, what gets harvested when, what has to come indoors before first frost, can I keep four years of rotation straight, and who is watering the shared plot this week?

Finds everything that assumes a single plant in a pot indoors — and the seasonal and multi-year horizons that an indoor-only design never has to think about.

## Evidence discipline

Inherited unchanged from the source cluster, because the failure it prevents is the one a persona review is most prone to: an authoritative-sounding species-specific number that nobody checked.

**Never invent, estimate, or infer a domain fact from context.** This binds all four lenses, not only `agronomy`. It applies to species-specific values (PPFD, temperature, pH, EC, VPD), taxonomy, toxicity and safety claims, pest-to-host assignments, nutrient requirements and dosages, and yield or growth-rate figures.

Any agronomic claim offered as a correction must be derivable from **three independent, checkable sources**: peer-reviewed literature; official institutions (JKI, BfN, EPPO, FAO, USDA, RHS, ASPCA); recognised reference works; standardised databases (GBIF, POWO, CABI, Tropicos); or manufacturer data sheets for product-specific values. **Not accepted:** blogs, forums, social media, wikis without a scientific reference, or the reviewer's own expertise offered without a citation.

A claim that cannot be supported becomes an open research point, not a softer assertion. Every review carries a section listing them — the section may be empty, but it may never be absent:

| No. | Claim | Sources available | Missing | Recommended research |
|-----|-------|-------------------|---------|----------------------|

The rule does not apply to persona reactions. "I would not know what this word means" needs no citation; it is the finding.

## Findings and severity

Ranked by what the persona does next, not by how wrong the text is:

| Rank | Meaning |
|------|---------|
| **Blocker** | This persona stops. The plant is harmed, the advice is unsafe, or the app is deleted |
| **Frustrating** | It works and it costs the persona something every time |
| **Overwhelming** | Correct and pitched past this persona; usable by a specialist, a wall for this one |
| **Solved well** | Named explicitly, so a later change does not quietly remove it |
| **Wish** | Would help, absence is not a defect |

Every finding names the target and location, the persona consequence, and — for `agronomy` — its sources or its open-research-point number. A finding that names only a preference is not a finding.

## Output

One report per persona per target. Reports are written under `.audits/grower-persona-review/`, never into `spec/`: a review is an observation at a point in time, and `spec/` holds what is intended to be true.

Each report closes with a fixed table and a machine-readable final line, matching the convention every recipe here follows:

```
REVIEW: pass
REVIEW: fail — <the single most severe blocker>
```

`fail` means this persona would stop. It is a statement about one lens, not a verdict on the recipe — three passes and one fail is a normal and informative result, and averaging it into a score destroys the only thing the review produces.

## Requirements

- **MUST** review as exactly one persona per run, and **MUST NOT** blend personas or average their verdicts
- **MUST NOT** assert a species-specific value, taxonomic assignment, toxicity claim, pest-host assignment, dosage, or yield figure without three independent citable sources
- **MUST** carry an open-research-points section in every report, empty if nothing is outstanding, and **MUST NOT** omit it
- **MUST** state a persona consequence for every finding, and **MUST NOT** report a bare style preference as a finding
- **MUST** write reports under `.audits/grower-persona-review/` and **MUST NOT** write into `spec/`, `recipes/`, or `.claude/`
- **MUST** close with the fixed table and one `REVIEW:` line
- **MUST NOT** call any Kamerplanter or Home Assistant tool; the review reads files in this checkout
- **MUST NOT** restate recipe-mechanics rules owned by [the recipe project pattern](../../goose/recipe-project-pattern/en.md), and **SHOULD** route a mechanics defect to `tests/validate_recipes.py` as a proposed check instead
- **MUST NOT** treat `AUDIENCES.md` IDs as personas, and **SHOULD** name the relationship explicitly when a finding touches both axes
- **SHOULD** accept a run's real output as a review target, since a recipe can be well-specified and still print something its reader cannot use
- **SHOULD** name what is solved well, so a later change does not silently remove it
- **SHOULD** route a data-quality finding to [pest pressure assessment](../pest-pressure-assessment/en.md) or [species baseline verification](../species-baseline-verification/en.md) rather than resolving it here
- **MAY** quote the persona's own voice where it makes a finding concrete, provided the finding stands without the quote

## Acceptance Criteria

- [ ] Every report identifies exactly one persona
- [ ] Every report contains an open-research-points section
- [ ] No agronomic correction appears without three sources or an open-research-point number
- [ ] Every finding names a persona consequence
- [ ] Every report ends with exactly one `REVIEW:` line
- [ ] No report is written outside `.audits/`
- [ ] No review run calls an MCP tool
- [ ] No finding restates a rule owned by the recipe project pattern
- [ ] No report cites an `AUDIENCES.md` ID as a persona
- [ ] Findings appear under the severity ranks defined here, in that order

## Open Questions

- Whether four personas is the right cut. The source cluster carried more — a smart-home lens and a frontend-design lens among them — and both have plausible targets here. Adding them is cheap; deciding they are missing is what this question tracks.
- Whether a run's output should be reviewed automatically after every recipe change, or on request. Automatic review needs a stored reference output per recipe, which the repository does not have.
- How a persona review interacts with the documentation tracks derived from `AUDIENCES.md`. A `casual-owner` blocker on a report is probably also a `user-docs` finding, and there is no convention for saying so once.
- Whether the `agronomy` lens should be allowed to read the MCP catalogs, which would let it check a recommendation against the actual pest and species records rather than against the recipe text alone. It would also make the review dependent on a live environment, which the others are not.
- Whether a `fail` from one persona should block anything, or remain purely informational. Nothing consumes the final line today.

## Source

- Persona profiles, evidence rule, and severity structure inherited from `nolte/kamerplanter`, `.claude/agents/`: `agrobiology-requirements-reviewer.md` (the three-source rule, the accepted and rejected source types, the open-research-points section, the CEA and physiology background), `cannabis-indoor-grower-reviewer.md`, `casual-houseplant-user-reviewer.md`, and `outdoor-garden-planner-reviewer.md` (the profiles, thought patterns, and the go/no-go statement). Those agents review that repository's requirement documents and write into its `spec/analysis/`; this spec governs the same lenses applied to this repository's recipes and reports, writing into `.audits/`.
- Audience distinction: `AUDIENCES.md` in this repository, and `spec/project/audience-identification/` in `nolte/nolte-shared` for what that artefact is for
- Recipe mechanics: [the Goose recipe project pattern](../../goose/recipe-project-pattern/en.md)
- Domain processes a review may route findings to: [pest pressure assessment](../pest-pressure-assessment/en.md), [species baseline verification](../species-baseline-verification/en.md), [nutrient imbalance detection](../nutrient-imbalance-detection/en.md), [plant health image analysis](../plant-health-image-analysis/en.md)
