---
name: plant-photo-read
description: "Reads Kamerplanter diary photos against a plant's established context and turns them into findings, gaps, or a refusal, each with a confidence and an evidence-naming rationale. Use when a recipe must interpret plant photos, judge whether a visible symptom is a departure from normal, or decide whether an image can answer a question at all. Separates describing from interpreting and refuses to invent a diagnosis the image does not support."
---

# Read plant photos into findings

Turns pixels into claims that a reviewer can check. The plant's context — species baseline, phase, care and pest history — must already be established; this skill consumes it rather than gathering it.

Photos come from `mcp__kamerplanter__get_diary_entry_photos` on the `kamerplanter` MCP server, which returns MCP image content blocks.

## The core move

**A finding is the gap between what is visible and what this plant should look like.** An observation on its own is not a finding, because most of what a photo shows is a plant being normal. Describe first, interpret second, and keep the two separable in the output — a reader must be able to disagree with the interpretation while still trusting the description.

## Procedure

### 1. Fetch at the right resolution

Call `mcp__kamerplanter__get_diary_entry_photos` with the `entry_key`. Pick `size` deliberately:

- `1280` when the question turns on fine detail — leaf undersides, chlorosis patterns, insect bodies, lesion margins
- `512` when it turns on habit, posture, or overall vigour

Only 512 and 1280 are accepted; anything else fails validation. Fetch all photos of the entry unless the caller names specific `photo_ids`.

### 2. Describe

For each photo, state what is visible in plain terms: which plant parts are in frame, their colour and posture, the condition of leaf margins and new growth, what the substrate surface looks like, and anything present that is not the plant.

Do not name a cause at this stage. "Lower leaves yellow between the veins, newest growth green" is a description. "Nitrogen deficiency" is not.

### 3. Compare against the expectation

Read each observation against the context. The species and phase decide what normal is: senescing lower leaves are routine on a plant in fruit, and alarming on a seedling. Growth that trails is the job of a groundcover and a symptom on an upright species.

### 4. Walk the nine axes

Read `references/inspection-checklist.md` before classifying anything — always, not only when something looks unusual. It lists the nine axes an inspection must cover (image fitness, distribution pattern, habit, leaf colour and its location, leaf shape, necrosis, signs, flowers and fruit, substrate surface), what each one records, and the backend symptom slugs to report against.

Every axis is acquitted explicitly as `absent`, `present`, or `not-assessable`. Coverage is the point: a run that reports three findings and leaves six axes unmentioned is indistinguishable from a run that never looked.

### 5. Classify each observation

Three outcomes, and they must not collapse into one another:

| Outcome | When | Result |
|---------|------|--------|
| **Finding** | Visible and a departure from normal for this species and phase | Reported with `confidence` and `rationale` |
| **Gap** | The question is legitimate but the image cannot answer it | Reported as a gap, naming what would resolve it |
| **Refusal** | The image does not show this plant, or shows no plant at all | The whole analysis fails; say so |

A gap is never a low-confidence finding. "The leaf undersides are not visible, so mite pressure could not be assessed" is honest; a 0.2-confidence mite finding from the same photo is not.

### 6. Write the rationale

Every finding names three things: **which photo**, **which visible feature**, and **which context field** turned that feature into a departure. A rationale that only restates the observation has not explained why it is a finding.

`confidence` describes how unambiguous the visible evidence is — not how fluent the sentence is, and not how confident the phrasing sounds.

## Hard rules

- Never state the direction of a suspected nutrient problem — undersupply versus oversupply — from the image. The two are visually indistinguishable, and their corrections are opposite. Hand that determination to the nutrient assessment path.
- Never re-identify the species from the image. Where the photo appears to show a different plant than the recorded species, that mismatch is the finding, at whatever confidence the image supports.
- Never analyse a photo whose entry has not been claimed, when the run is part of a claim cycle.
- Never treat the entry's own `text`, `tags`, or `measurements` as ground truth. They are the observer's claim. Where text and image disagree, report both.
- Never report more than 10 findings or cite more than 5 photo ids; the submit path rejects more. When the nine axes yield more than ten findings, merge the least specific ones rather than dropping an axis silently.
- Never leave an axis unmentioned. `not-assessable` is a valid, useful answer; silence is not.
- Judge timing against the entry's `created_at`. A photo analysed three weeks late is evidence about the plant three weeks ago.

## Gotchas

- Image content blocks do reach the model and are legible — verified at `size: 512` against this server. A failure to see an image is a real failure, not an expected limitation to work around.
- Queued entries genuinely contain photos with no plant in them. The first entry encountered on the reference instance depicted a clamp and a remote control. Refusal is a routine path, not an edge case.
- `mcp__kamerplanter__get_diary_entry_photos` delivers WebP renditions, not originals. Fine detail beyond the 1280 edge size is simply unavailable; treat that as a gap rather than straining the interpretation.
- An empty pest history means no *recorded* pests, not no pests. It lowers the prior for a recurrence; it does not raise it for a clean plant.
- Photos of the same entry may show different plant parts rather than the same subject twice. Reconcile them before concluding, and cite each id that actually contributed.

## Source

Derived from `spec/process/plant-health-image-analysis/` §"Stage 5 — Reading" and §"Confidence and refusal", measured against the reference instance on 2026-08-05.
