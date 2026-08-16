---
title: Species baseline check
audience: [plant-owner, maintainer]
content_mode: how-to
track: user-docs
last_updated: 2026-08-16
---

# Species baseline check

Every judgement about a plant stands on its species record: germination temperature, sowing depth, hardiness, the timing windows. If one of those values is wrong, everything reasoned on top of it is wrong too, and nothing in a later run will notice. `species-baseline-check` reads one species record, checks it for agronomic plausibility, resolves its lifecycle where the record does not state it, and proposes a correction only when three independent sources agree.

Finding many doubtful values and proposing no correction is the expected outcome, not a weak one.

This run **only reads**. It changes no record — a correction it proposes is directed at [nolte/kamerplanter](https://github.com/nolte/kamerplanter) for a human to act on.

## Before you start

- **Start the run from this repository checkout.** The recipe loads the project skills `species-baseline-verify` and `plant-lifecycle-resolve` from `.claude/skills/`, and skill discovery is relative to the Goose process's working directory. A run started elsewhere loses the skill silently and still produces a plausible answer.
- **The run researches on the web.** It is the one recipe here that reads sources outside your two servers, because a value has to be checked against something. Nothing it asserts may come from the model's memory.

## Run it

```sh
goose run --recipe species-baseline-check \
  --params species_key=allium-porrum \
  --params tenant=my-garden
```

| Parameter | Required | Effect when omitted |
|-----------|:--------:|---------------------|
| `species_key` | yes | — |
| `tenant` | no | the run discovers the garden slug from `list_tenants` |

`tenant` is not decoration here: the sowing calendar's frost dates are per garden, and timing checks are anchored to your own last frost, Eisheilige, and first frost rather than to a rule of thumb.

## What it checks

The species record returns only its populated fields, so an absent key means "not populated for this species" — never "does not apply". The run therefore lists which fields are present and which are absent **before** checking anything, and keeps checks that could not run separate from checks that ran and passed. Collapsing the two would turn a gap into a false assurance.

Then it resolves the lifecycle, stopping at the first step that settles it: the instance's own assignment, then growing periods and month fields, then the overwintering profile, then research under the three-source rule. Botanical and cultivated cycle are stated separately where they differ — a leek is biennial and grown as an annual, and only one of those answers a harvest question.

## What licenses a correction

| Confidence | Basis | Licenses |
|------------|-------|----------|
| **Established** | Three or more independent sources agree | A proposed correction, with its sources |
| **Probable** | Two agree, or three with minor divergence | A finding. The recorded value stands |
| **Uncertain** | Sources conflict, or only one was found | A finding naming the conflict. The value stands |
| **Unverifiable** | No usable source | A named gap. The value stands |

Independent means not quoting one another: three pages repeating one nursery's catalogue text are one source. University extension services, RHS and ISTA rank highest; seed houses count for timing specifically; forums support but never carry a claim. Wikipedia, AI-generated text, and unattributed blog posts are never sufficient alone.

## Read the outcome

The report opens with a field table — species, fields present, fields absent, cycle, frost anchors, findings by severity — then lists each finding with its confidence and sources, the checks that could not run, and any proposed correction with its three sources.

| Closing line | Means |
|--------------|-------|
| `BASELINE: plausible` | nothing in the record contradicts what the sources say |
| `BASELINE: findings:<n>` | followed by a second line naming the single most consequential finding |

A finding is not a defect in this repository. It is a statement about the species record in Kamerplanter, and the report is written so it can be filed there as-is.

## Sources

- [`recipes/species-baseline-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/species-baseline-check.yaml) — the parameters and the report format
- [`.claude/skills/species-baseline-verify/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/species-baseline-verify/SKILL.md) — the plausibility checks, the source ranking, and the three-source rule
- [`.claude/skills/plant-lifecycle-resolve/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/plant-lifecycle-resolve/SKILL.md) — the resolution order and the two cycles
- [`spec/process/species-baseline-verification/en.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/en.md) — the process this recipe implements
