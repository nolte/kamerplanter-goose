# Photo inspection checklist

Nine axes a photo analysis walks so that coverage is reproducible instead of incidental. Every axis is **acquitted explicitly** — `present`, `absent`, or `not-assessable` — so a reader can tell "looked and found nothing" from "never looked".

This file collects observations. It does **not** assign causes: that mapping lives in the Kamerplanter knowledge base (`spec/knowledge/rag/diagnostik/`) and in the `mcp__kamerplanter__get_pest` / `get_disease` catalogues, which stay authoritative. Duplicating their rules here would drift against them.

Where an observation matches a term from the backend's controlled symptom vocabulary, report that slug verbatim — it keeps the output joinable with the catalogue.

## Contents

- [How to acquit an axis](#how-to-acquit-an-axis)
- [A1 — Image fitness (gate)](#a1--image-fitness-gate)
- [A2 — Distribution pattern](#a2--distribution-pattern)
- [A3 — Habit and turgor](#a3--habit-and-turgor)
- [A4 — Leaf colour and its location](#a4--leaf-colour-and-its-location)
- [A5 — Leaf shape and texture](#a5--leaf-shape-and-texture)
- [A6 — Necrosis, lesions, feeding damage](#a6--necrosis-lesions-feeding-damage)
- [A7 — Signs: organisms and deposits](#a7--signs-organisms-and-deposits)
- [A8 — Flowers and fruit](#a8--flowers-and-fruit)
- [A9 — Substrate surface and plant base](#a9--substrate-surface-and-plant-base)
- [Never inferred from an image](#never-inferred-from-an-image)
- [Output shape](#output-shape)

## How to acquit an axis

| Verdict | Meaning |
|---------|---------|
| `absent` | The axis was assessable in this photo and showed nothing abnormal for this species and phase |
| `present` | Something visible departs from the expectation — becomes a finding with confidence and rationale |
| `not-assessable` | The photo cannot answer this axis (out of frame, out of focus, wrong angle, resolution too low) — becomes a gap, never a low-confidence finding |

`not-assessable` is a normal outcome, not a failure. A top-down shot cannot show leaf undersides; saying so is more useful than guessing.

## A1 — Image fitness (gate)

Runs first and can end the analysis.

- Does the photo depict a plant at all?
- Does it plausibly depict the recorded species? A mismatch is a **finding**, never a re-identification.
- Is it sharp enough, and is the subject large enough in frame, to judge anything?
- How many distinct plants are in frame? This number governs A2 and limits every later attribution.

Fails here → the whole analysis is a refusal (`status: failed`), not a set of weak findings.

## A2 — Distribution pattern

The strongest single discriminator available in a photo, and the one most often skipped.

- Are several plants visible, and are they **all** affected or only some?
- Are affected and unaffected plants of the **same species** side by side under the same light and watering?
- Is the pattern uniform across the frame, or localised to individuals, one side, or one height?

Reading, per extension diagnostics: damage spread uniformly across plants — including plants of different species — points toward an **abiotic** cause (site, water, temperature, handling). Damage confined to some individuals of one species while unrelated neighbours stay healthy points toward a **biotic** cause, because pathogens and pests have limited host ranges.

State this as an orientation, not a verdict; a single photo shows one moment and cannot establish spread over time.

## A3 — Habit and turgor

- Overall posture: upright, drooping, collapsed
- Turgor: firm or limp — and limp *despite* visibly moist substrate is its own signal (`wilting_despite_moisture`, distinct from `leaves_wilting`)
- Internode length and proportion: drawn-out, pale, weak-stemmed growth (`leggy_stretching`)
- Size against what `planted_on` and the phase would predict (`stunted_growth`)

Judge habit against `growth_habit` from the species record. Trailing growth on a groundcover is the plant working correctly.

## A4 — Leaf colour and its location

Colour alone is nearly meaningless; colour **plus location** is the key diagnostic axis. Always report where on the plant, not just what.

- Uniform yellowing on **older / lower** leaves (`leaves_yellowing_lower`)
- Uniform yellowing or pallor on **younger / upper** leaves (`leaves_yellowing_upper`)
- Chlorosis **between the veins** with veins staying darker (`interveinal_chlorosis`) — and again: older or younger leaves?
- Purple or reddish stems and petioles (`purple_stems`)
- Mottled light/dark patchwork rather than a gradient (`mosaic_pattern`)

Why location carries the weight: mobile nutrients (N, P, K, Mg, Mo) are withdrawn from old leaves toward new growth, so their deficiency symptoms appear on **older** tissue first. Immobile nutrients (Ca, Fe, Mn, Zn, Cu, B, S) cannot be relocated, so their symptoms appear on **new** growth first. The knowledge base turns that split into a specific nutrient; this axis only has to record the split correctly.

Do **not** name a nutrient here, and do **not** state whether supply is too low or too high — see the exclusions below.

## A5 — Leaf shape and texture

- Deformation, asymmetry, crinkling, brittleness (`leaf_deformation`)
- Curling upward (`leaves_curling_up`) or downward (`leaves_curling_down`) — the direction is diagnostic and cheap to record
- Surface gloss, dullness, or unusual thickness
- Growing-tip condition: intact, deformed, or dead

## A6 — Necrosis, lesions, feeding damage

- Dead tissue at **tips** (`leaf_burn_tips`) versus along **margins** (`leaf_edges_browning`) — different axes, do not merge
- Discrete spots, their colour, whether they carry a halo or a defined border (`leaf_spots`)
- Holes and chewed margins (`leaf_holes`), and whether edges are ragged or clean-cut
- Soft, dark, or collapsed stem tissue (`stem_rot`); seedlings toppling at the base (`damping_off`)
- Whether necrosis follows the leaf margin, the veins, or neither

## A7 — Signs: organisms and deposits

"Signs" are the organism or its products — as opposed to the plant's reaction. Their presence is far more decisive than any symptom, so this axis is worth its own pass at the highest resolution available.

- Insects visible on the plant (`visible_aphids`, `small_flying_insects`)
- Moving specks, typically on undersides (`tiny_moving_dots`); fine silk (`webbing_on_leaves`)
- Silvery or bronzed stippling with black frass specks (`silvery_leaf_speckling`)
- Sticky shine or droplets, often with sooty mould following (`sticky_honeydew`)
- White floury coating on the upper surface (`white_powdery_coating`); greyish fuzzy growth on the underside (`downy_mildew`); grey-brown fuzzy rot (`grey_mould`); raised orange-brown pustules (`rust_pustules`)
- Scale bumps, waxy woolly masses, egg clusters

Leaf undersides carry most early pest evidence and are usually invisible in a top-down shot. When they are not in frame, this axis is `not-assessable` — say so, and name it as the photo that would resolve it.

## A8 — Flowers and fruit

Only meaningful against the phase and the season; skip cleanly when the plant is not expected to carry either.

- Flowers absent when the phase and `bloom_months` predict them (`no_flowering`)
- Buds or flowers dropping (`flower_drop`)
- Fruit failing to develop or ripen (`buds_not_ripening`)
- Ripeness against `harvest_months` and `harvest_pattern`
- Mixed-sex or malformed flowers where the species does not expect them (`hermaphrodite_flowers`)

Late-phase yellowing of lower leaves while flowers and fruit stay sound is **senescence**, not deficiency. Record it as normal.

## A9 — Substrate surface and plant base

Often the only root-zone evidence a photo carries.

- Salt crust, white deposits, or efflorescence on the surface or pot rim
- Algae or persistent sheen suggesting chronic wetness (`overwatering_signs`)
- Fungus gnats around the surface (`small_flying_insects` at substrate level)
- Standing water, compaction, or substrate pulled away from the pot wall
- Mulch, roots at the surface, container size against the plant

## Never inferred from an image

Six conclusions this checklist never supports, however suggestive the picture:

1. **The direction of a nutrient problem.** Deficiency and oversupply share their symptoms and have opposite corrections. Hand this to the nutrient assessment path, which needs an EC or pH reading.
2. **A specific nutrient.** Record the location-plus-pattern split (A4); let the knowledge base name the element.
3. **The species.** It is a fact of the instance. A contradicting photo is a finding.
4. **pH, EC, or salt load.** Not visible. A surface crust is a hint, not a measurement.
5. **Root condition.** Not visible. Wilting despite moist substrate is a *reason to inspect* roots, not a root diagnosis.
6. **Progression over time.** One photo is one moment. Spread and speed need a second observation.

## Vocabulary coverage

The nine axes cite 33 of the backend's controlled symptom slugs. Three are deliberately not collected here:

| Slug | Why not |
|------|---------|
| `heat_stress_symptoms` | A cause label, not an observation. A photo shows curled margins or wilting; naming the cause is the knowledge base's job, and temperature is not visible |
| `cold_stress_symptoms` | Same reason |
| `slow_seed_germination` | Needs two observations over time, which one photo cannot supply |

If the backend catalogue grows, this table is where the gap should be recorded rather than left implicit.

## Output shape

Report all nine axes, in order, before any interpretation:

```
A1 image fitness       absent | present | not-assessable   — one line of evidence
A2 distribution        ...
...
A9 substrate & base    ...
```

Then, for each `present` axis, one finding carrying: the photo id, the visible feature, the context field that made it a departure, a confidence between 0.0 and 1.0, and — where one applies — the backend symptom slug.

Then, for each `not-assessable` axis, the gap and the photograph that would close it.

Nine acquitted axes with three findings and two gaps is a complete result. Three findings with six axes silently unmentioned is not.
