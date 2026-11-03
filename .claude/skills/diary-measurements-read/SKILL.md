---
name: diary-measurements-read
description: "Reads the recorded measurements of one Kamerplanter plant from its diary — lists the entries without a type filter, opens the most recent ones, and returns the measurements objects with a read report of how many entries were listed, opened and carried no measurements. Use when a nutrient assessment needs tier 1 evidence (an EC, pH or runoff value) and nothing else in the run fetches it, or when a recipe must know whether the diary was read. Passes only the plant and the garden, never guesses a limit, a date filter or a sort parameter, and reports a rejected call or a paged result verbatim."
---

# Read a plant's recorded measurements

Fetches the diary measurements a later question rests on, and reports how much of the diary was read, so that an empty result can be told from a diary nobody read. It judges nothing: what a value means is `nutrient-imbalance-assess`. Without this step a nutrient assessment never rises above tier 3 and always refuses, even for a plant whose diary holds a perfectly good reading.

Every tool below is on the `kamerplanter` MCP server and is addressed as `mcp__kamerplanter__<tool>`. All of them are read-only.

## Input

- **plant_key**: the plant instance whose diary to read.
- **tenant**: the garden's slug, or the garden `plant-context-collect` or `garden-context` already resolved. Never rely on a default membership.

## Procedure

### 1. List the entries

Call `mcp__kamerplanter__list_diary_entries` for the plant and the garden. Pass the plant and the garden and nothing else.

Do **not** filter by entry type. `measurements` is an open field carried by any entry regardless of its type, so an EC or pH value recorded against an observation or a note is exactly the reading this step exists to find, and a type filter would hide it.

Do **not** guess a limit, a date filter or a sort parameter. This procedure was written without a measured signature for this tool, and a rejected argument ends the step in a `validation.error`, which drops the caller back to the tier 3 refusal this step is meant to remove. If the tool rejects the call or its result is paged, report the error or the paging field verbatim as a step result and continue with what came back; that report is how the signature gets measured.

### 2. Open the most recent entries

Read the entries newest first. For at most the eight most recent, call `mcp__kamerplanter__get_diary_entry` with the entry key and read the `measurements` object. Stop early once a value carries an unambiguous unit and a date inside the current phase: one such reading settles tier 1, and the remaining calls would spend turns a headless run does not have.

### 3. Report

Return, as its own line: how many entries were listed, how many were opened, and how many carried no `measurements`. That line is what tells the caller the diary was read. Then the measurements found, each with its entry key and date, exactly as recorded, with no normalisation: `measurements` has no declared schema, and ambiguous values are discarded by the assessment that reads them, not here.

An empty result after a real read is ordinary. It puts the assessment at tier 3 or below, which is a legitimate outcome and not a failed run. Report a tool error verbatim and say that the diary was not read.

## Hard rules

- Never filter the list by entry type, and never guess a limit, a date filter or a sort parameter.
- Never open more than eight entries.
- Never interpret, convert or discard a measurement; report it as recorded.
- Never report an empty list as "read" unless the listing call succeeded.
- Call no state-changing tool. Forbidden by name: `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__set_plant_location`, `mcp__kamerplanter__create_site`, `mcp__kamerplanter__add_plant_diary_entry`, `mcp__kamerplanter__claim_diary_analysis`, `mcp__kamerplanter__submit_diary_analysis`, `mcp__kamerplanter__transition_plant_phase`, `mcp__kamerplanter__assign_species_phase_sequence`, `mcp__kamerplanter__assign_nutrient_plan`, `mcp__kamerplanter__record_feeding_event`, `mcp__kamerplanter__create_inspection`.
- Call no Home Assistant tool.

## Gotchas

- The signature of `mcp__kamerplanter__list_diary_entries` was not measured when this procedure was written, which is why it passes only the plant and the garden.
- This skill itself was not run against a live instance; tool names come from `spec/mcp/kamerplanter-mcp-server/en.md`.

## Source

Governed by `spec/process/nutrient-imbalance-detection/en.md`, the requirement to read the plant's recent diary entries before assessing. The procedure was moved here, unchanged in substance, from step 2 of `recipes/nutrient-imbalance-check.yaml` so that `daily-garden-check` and the nutrient check load one copy.
