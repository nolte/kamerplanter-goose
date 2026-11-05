---
name: pest-ipm-planning
description: "Turns a pest or disease candidate, as the pest pressure assessment left it, into an integrated pest management plan for one plant in four ordered stages — confirmation and monitoring, environmental correction, cultural and mechanical controls, targeted treatment — reaching a treatment only at the pest process's own threshold and giving every treatment its prerequisites and its safety constraints quoted verbatim from the record (safety interval against the time to harvest, protective equipment, dosage, application method, active ingredient). Use when a recipe must say what to do about a pest or disease suspicion and in which order, or when the daily check needs the pest management domain. Never identifies a candidate or re-runs the falsification tests, labels monitoring methods and pest humidity ecology as not recorded, excludes a treatment whose interval cannot be checked, and records nothing: a monitoring step names the inspection write a later apply step would make and calls nothing."
---

# Plan integrated pest management

Answers "what should be done, in which order" for a candidate the pest process already judged. It never answers "what is it": identification, the evidence ladder, the falsification tests, the treatment threshold and the checks on beneficials, safety interval and rotation belong to `pest-pressure-assess`, and the candidate arrives with the status and tier that skill gave it. The environmental side comes from `plant-health-assessment` when the caller has its hand-off, the harvest timing from `growth-stage-assessment`, the weight of a claim from `decision-policy`.

It writes nothing. A plan is a proposal to a person; recording an inspection or a treatment is a separate, later apply step that this skill names and never calls.

Every tool below is on the `kamerplanter` MCP server, addressed as `mcp__kamerplanter__<tool>`, and read-only. Tool behaviour is quoted from `spec/mcp/kamerplanter-mcp-server/en.md` and `spec/process/pest-pressure-assessment/en.md`, measured 2026-08-07 and 2026-08-16 and not re-measured for this skill.

## Input

- **The pest report** from `pest-pressure-assess`, as it returned it: the pest or disease candidate with its catalogue key, its status, the tier, the tests run and not run, the beneficial check, the treatments it named with their safety intervals, and the observation that would settle it.
- **The plant context block** from `plant-context-collect`: `allows_harvest`, `planted_on`, the cultivar's `days_to_maturity`, the inspections, the gaps list.
- **The IPM hand-off** from `plant-health-assessment`, optional: the `environment` and `water` candidates with what they rest on.
- **The harvest hand-off** from `growth-stage-assessment`, optional: the days since `planted_on` against `days_to_maturity`, and its assessment date.
- **Caller facts**, each optional, marked `caller`: the setting (enclosed: greenhouse, tent, indoors; or open: outdoors), the planned harvest date, the assessment date. Never read the current date.

Without the pest report, stop and say that `pest-pressure-assess` must run first. A report that names no pest or disease candidate gives the valid empty plan "no pest or disease candidate".

## Procedure

### 1. Take the candidate as given

The status is one of the four values this skill reads from the pest report, and nothing else; the pest skill's own wording stays authoritative:

| Status read | Means here | Order |
|-------------|------------|-------|
| `identified` | the report established the organism | highest |
| `not contradicted` | the candidate survived every test the record could support, which is weaker than identified | second |
| `undetermined` | the report could not decide, for lack of evidence | third |
| `rejected` | a test the report ran ruled the candidate out | lowest |

"At least `not contradicted`" below means `identified` or `not contradicted`. A report wording that maps to none of the four is reported verbatim and treated as `undetermined`.

Plan only for a candidate the pest report names, with its status and tier unchanged. Never identify, never resolve a candidate from memory, never re-run a falsification test, and never write *identified* where the report says *not contradicted*. A `rejected` candidate gets no plan, only the line saying it was rejected and by which test.

**The treatment threshold** is the pest process's own: tier 1, or tier 4 plus an uncontradicted tier 2. Say whether it is met, with the tier.

### 2. Read the record, only for the keys named

- For a pest candidate, call `mcp__kamerplanter__get_pest` with its `pest_key`; for a disease, `mcp__kamerplanter__get_disease` with its `disease_key`. Skip the call when the pest report already quotes the full record, and say so.
- Call `mcp__kamerplanter__get_treatment` for a `treatment_key` those records name, when the nested `treatments[]` entry lacks a field the safety block needs.
- Call `mcp__kamerplanter__search_glossary` for a term the plan uses in a domain-specific sense (for example Karenz); a definition is not evidence.

Quote `treatments[]`, `beneficials[]` and `environmental_triggers[]` as returned. Read no other key and call no other tool. Report a tool error verbatim and continue with what remains; report an absent tool by name.

### 3. Order the stages

Exactly four, in this order. Each step names its stage, what it rests on and its level.

1. **Confirmation and monitoring.** The observation that would raise the evidence tier, usually the one the pest report named: an inspection of the named plant part, a sticky trap, the person checking the leaf undersides with a hand lens. A monitoring method is general knowledge of the taxon, **labelled "not recorded"** (tier 5, level 8): the pest record carries no monitoring field. Recording what was found is an inspection a later apply step would write.
2. **Environmental correction.** Rule 5 of `decision-policy`: correct an environmental cause before treating the plant. For a **disease**, cite its `environmental_triggers` verbatim (tier 2, level 4) against the plant's situation and the health hand-off's `environment` and `water` candidates. For a **pest**, any humidity or temperature correction is general knowledge, **labelled "not recorded"**: the pest record has no humidity ecology. Without the health hand-off, or with one whose `environment` and `water` candidates are both `not assessable`, and for a disease also without `environmental_triggers` to set against the plant's situation, report stage 2 as `not assessed`, naming what would assess it. A `not assessed` stage 2 is neither done nor unavailable: it blocks every stage-4 measure (step 4).
3. **Cultural and mechanical controls.** Removing affected parts, isolating the plant, hosing off, barriers, traps, sanitation: general knowledge, labelled "not recorded", unless a recorded treatment's `treatment_type` plainly places it here. In an **open** setting, the conservation and encouragement of natural enemies belongs here.
4. **Targeted treatment.** Only when the threshold of step 1 is met. Below it, stop after stage 3 and say that a treatment is not justified, naming the monitoring method of stage 1 as what would change that. At the threshold, order the measures **biological before chemical**: a beneficial release (in an **enclosed** setting) and biological treatments first, chemical ones after, and say why the earlier stages are not enough before opening with a chemical. Check each beneficial against `preys_on`, as the pest process requires; one that does not list the candidate is a finding, not a measure.

A `treatment_type` whose stage is not plain from its value is reported as **"stage not determinable from the record"**, with the value as read: the value set is not recorded. Never guess its stage.

The setting comes from the caller. Without it, state it as inferred (site type, `frost_sensitivity`, `hardiness_zones`) and say that introduction and conservation are different recommendations.

### 4. Give every treatment its block

Every measure in stage 4 carries all three parts, in this shape:

- **Prerequisites**: (a) the identification meets the threshold, with the tier named; (b) each earlier stage done or unavailable, with the reason. **A stage 2 that was not assessed is neither**: it blocks the measure, which is then "not recommendable: environmental side not assessed", naming what would assess it (the health assessment's hand-off, or the plant's situation for a disease's `environmental_triggers`); (c) the harvest situation: `allows_harvest` as read, and the time to harvest, computed only from the caller's planned harvest date minus the assessment date, or from the growth-stage harvest hand-off (`days_to_maturity` minus the days since `planted_on`), each stated with its source. The `days_to_maturity` fallback assumes one harvest at maturity: name as uncertainty that it ignores an early or continuous harvest (baby leaf, herbs, cut-and-come-again), and that the caller's harvest date is the better source. Never from the harvest-readiness read, whose fields are not recorded. Without an assessment date there is no time to harvest. (d) The product label and the local plant-protection rules: always listed as "outside the record — confirm before applying". It is shown for the person to check and never decides whether the measure is recommendable; (a) to (c) decide that.
- **Safety constraints**, quoted verbatim from the record and never scaled, converted or invented: `safety_interval_days`, `protective_equipment[]`, `dosage_per_liter`, `application_method`, `active_ingredient`. A field the record does not carry is `not recorded`.
- **Exclusions**:
  - `safety_interval_days` greater than the time to harvest: **excluded**, and saying so is the result for that measure.
  - `allows_harvest` true and no time to harvest established: **"not recommendable: interval cannot be checked"**.
  - `allows_harvest` true and `safety_interval_days` not recorded (null or absent): **"not recommendable: interval cannot be checked"** as well. A missing interval is never read as zero.
  - `allows_harvest` false: the interval check does not apply; say so.
  - Two measures sharing an `active_ingredient` are never offered as alternatives; where `active_ingredient` is `null`, say that the rotation claim cannot be made.
  - A broad-spectrum measure beside a beneficial release: state the conflict as general knowledge, **not recorded** (contraindications are not in the record).

### 5. Give each step its kind

| Step | Kind |
|------|------|
| a monitoring step for a candidate the report names | recommendation, with no consequence unless an input states one |
| an environmental or cultural step, candidate at least `not contradicted` in the pest report | recommendation |
| an environmental or cultural step, candidate below that | observation |
| a treatment at the threshold, prerequisites (a) to (c) holding and no exclusion applying | recommendation |
| a treatment excluded, not recommendable, or below the threshold | observation, with the reason |

**The named mutation**: a monitoring step names the inspection-recording tool as the write a later apply step would make; a treatment names `no tool measured`, since the measured catalog has no tool that records a treatment. Both are named, never called.

### 6. Weigh it

Apply `decision-policy` to every recommendation: evidence (level, source, retrieved-at, one entry each), confidence from the highest level that supports it, uncertainty (what would change it), missing data (each input it did not have, with the observation that would supply it). Read pest tiers as levels from the table "How the existing ladders relate": tier 1 is level 3, tier 2 is level 4, tier 4 has no level, tier 5 is level 8.

### 7. Report

Return, in this order:

```
IPM PLAN
  plant:       <plant key>
  candidate:   <pest or disease, key, status and tier as the pest report gave them> | no pest or disease candidate
  threshold:   met (tier <n>) | not met (tier <n>) | not applicable
  setting:     enclosed | open (caller) | inferred: <from what> | not stated
  as of:       <date> (caller | growth-stage hand-off) | none
  time to harvest: <days, from planned harvest date | from days_to_maturity> | not established (<reason>) | not applicable (allows_harvest false)
STAGE 1 — CONFIRMATION AND MONITORING
  <step, what it rests on, level; a method labelled "not recorded">
STAGE 2 — ENVIRONMENTAL CORRECTION
  <step, environmental_triggers as read (disease) or "not recorded" (pest)> | not assessed (<reason>)
STAGE 3 — CULTURAL AND MECHANICAL CONTROLS
  <step, source, level>
STAGE 4 — TARGETED TREATMENT
  not justified: <why, and the monitoring step that would change it> | not applicable
  | TREATMENT <treatment_key> <name> (<treatment_type> | stage not determinable from the record)
      prerequisites: identification <tier>; earlier stages <done | unavailable: reason | stage 2 not assessed: blocks, <what would assess it>>; allows_harvest <value>; time to harvest <days, source, uncertainty | not established>; product label and local rules: outside the record — confirm before applying
      safety:        safety_interval_days <as read>; protective_equipment <as read>; dosage_per_liter <as read>; application_method <as read>; active_ingredient <as read | null: rotation claim cannot be made>
      status:        recommendable | excluded (<interval exceeds time to harvest>) | not recommendable: interval cannot be checked (<time to harvest not established | interval not recorded>) | not recommendable: environmental side not assessed
  beneficials: <each, preys_on checked: lists the candidate | does not (finding)>
  not recorded: <contraindications; the beneficial against broad-spectrum conflict, where it applies>
FINDINGS
  domain: pest management | subject: <plant key> | kind: recommendation or observation
  statement / evidence / confidence / what would change it / missing data
  mutation (named, never called): <the inspection-recording tool named under Gotchas> (monitoring) | no tool measured (treatment)
  consequence: <only if an input states one, otherwise absent>
TREATMENT: justified | not justified | not applicable
```

Give one finding per step. `TREATMENT: justified` when at least one stage-4 measure is recommendable; `not justified` when a candidate exists but the threshold is not met or every measure is excluded or not recommendable; `not applicable` when there is no candidate. Return no field that was not read. The facts two runs over the same input must agree on are the stages and their steps, the threshold, the kinds, the exclusions, the quoted safety values, the evidence levels and the missing-data list; retrieval times and prose may differ, and byte-identical prose is not claimed.

## Hard rules

- Never identify a candidate, re-run a falsification test, or write *identified* where the report says *not contradicted*.
- Never reach stage 4 below the pest process's threshold.
- Never state a monitoring method, a pest's humidity preference or a contraindication as recorded.
- Never scale, convert or invent a dosage, an interval or a protective measure; quote them.
- Never recommend a treatment whose interval exceeds, or cannot be checked against, the time to harvest, and never read a missing interval as zero.
- Never offer two measures sharing an `active_ingredient` as alternatives.
- Never read the current date into the facts.
- Call no Home Assistant tool.
- Call no tool that changes state. Forbidden by name: `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`, `mcp__kamerplanter__submit_diary_analysis`, `mcp__kamerplanter__transition_plant_phase`, `mcp__kamerplanter__assign_species_phase_sequence`, `mcp__kamerplanter__assign_nutrient_plan`, `mcp__kamerplanter__record_feeding_event`, `mcp__kamerplanter__create_inspection`.

## Gotchas

- The inspection-recording tool a monitoring finding names as its mutation is `mcp__kamerplanter__create_inspection`. The finding carries that name in its output; this skill never calls it, and it sits closest to this skill's subject, which is why it is forbidden by name above.
- No tool in the measured catalog records a treatment, so a treatment's mutation is `no tool measured`. The server spec's Non-Goals still list IPM write tools as unimplemented although its write table records the inspection write as measured; that line is stale.
- Most plans stop after stage 3: without a recorded inspection the pest process rarely reaches tier 1, and a photo alone is tier 4. `TREATMENT: not justified` is the ordinary result, and the monitoring step is the useful part.
- The `pest-ipm-plan` recipe runs no health assessment, so for a pest there is no hand-off and stage 2 stays `not assessed`: a pest treatment is then never recommendable from that recipe alone. That is deliberate (rule 5 of `decision-policy`). The daily check runs the health assessment first and hands it over, but without supplied weather or a watering measurement both candidates there are usually `not assessable`, with the same effect.
- The value set of `treatment_type` is not recorded, so "stage not determinable from the record" is expected for some values until a live run shows them.
- The harvest-readiness read exists in the catalog, but its response fields are not recorded; a time to harvest is never taken from it.
- This skill itself was not run against a live instance; treat the first real run as the measurement.

## Source

Governed by `spec/process/plant-health-and-ipm-planning/en.md` §A, §D, §E, §G, §H and §I.
