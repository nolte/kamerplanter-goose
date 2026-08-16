---
title: Domain review
audience: [recipe-author, maintainer]
content_mode: how-to
track: developer-docs
last_updated: 2026-08-16
---

# Domain review

A recipe can be technically correct and still be useless to the person it is written for — too much jargon for someone with three houseplants, too little rigour for a plant scientist, blind to what 120 outdoor plants across a season actually cost. `domain-review` reads one recipe, spec, or captured run output as exactly one grower persona and reports what that grower would do with it.

One persona per run, deliberately. Three passes and one fail is the useful result; averaging the four into a score destroys it.

This run touches no garden and calls no Kamerplanter or Home Assistant tool. It does **write**, though: its report goes to `.audits/grower-persona-review/` in your checkout, which is why the recipe says so in its description and still carries no `-apply` suffix — that suffix is about a garden, not the filesystem.

## Before you start

- **Start the run from this repository checkout.** The recipe loads a persona skill from `.claude/skills/` and reads the review target from this tree; both are resolved relative to the Goose process's working directory.
- `.audits/` is gitignored. The report is a working artefact, not something to commit.

## Run it

```sh
goose run --recipe domain-review \
  --params persona=casual-owner \
  --params target=recipes/nutrient-imbalance-check.yaml
```

| Parameter | Required | Value |
|-----------|:--------:|-------|
| `persona` | yes | one of `agronomy`, `indoor-grower`, `casual-owner`, `outdoor-gardener` |
| `target` | yes | a repository-relative path — a recipe under `recipes/`, a spec under `spec/`, or a captured run output |

An unknown persona is not resolved to the closest match. The run stops with `REVIEW: fail — unknown persona "<value>"` and nothing else.

## The four lenses

| Persona | Reviews as | Asks |
|---------|-----------|------|
| `agronomy` | A plant scientist | Is the claim biologically correct, and is the advice safe |
| `indoor-grower` | A tent operator | Does this survive daily use, run after run |
| `casual-owner` | Someone with three houseplants and no patience | Do I know what to do now, and would I still use this in two days |
| `outdoor-gardener` | An allotment gardener | Does this hold across seasons and 120 plants |

They are meant to disagree. A `fail` is a statement about one lens, not a verdict on the target.

## Read the outcome

Each lens ranks every finding by consequence, using the same five ranks, and names that consequence. A finding that names only a preference is not a finding.

| Rank | Meaning |
|------|---------|
| **Blocker** | The reader loses a plant, or abandons the target |
| **Frustrating** | It works and costs something every single time |
| **Overwhelming** | Correct and pitched past its reader |
| **Solved well** | Named so nobody removes it later |
| **Wish** | Would help; its absence is not a defect |

The written report lands at `.audits/grower-persona-review/<target>-<persona>.md`. Its **open research points** section is mandatory and may be empty, but may never be absent: any factual claim about a plant needs three independent sources, and one that does not have them goes there instead of into the findings. A persona's own reaction needs no sources — "I would not know what that word means" *is* the evidence.

The run itself prints a short field table (persona, target, whether the skill loaded, the report path, blocker count, open-research-point count), the single most severe blocker in one sentence, and one closing line:

| Closing line | Means |
|--------------|-------|
| `REVIEW: pass` | no blocker for this lens |
| `REVIEW: fail — <blocker>` | one lens would stop here, and why |
| `REVIEW: fail — target not found: <path>` | the path does not exist; nothing was reviewed |

If the persona skill does not load, the run stops and says so rather than reviewing anyway. A review written from the recipe prompt alone would read plausibly and carry none of the persona — which is the one failure that would not look like one.

## Sources

- [`recipes/domain-review.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/domain-review.yaml) — the parameters, the persona mapping, and the write boundary
- [`spec/process/grower-persona-review/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/grower-persona-review/en.md) — why the personas stay separate and what a review owes the reader
