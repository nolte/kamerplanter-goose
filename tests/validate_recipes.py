#!/usr/bin/env python3
"""Validate every recipe against the house pattern.

The rules checked here come from spec/goose/recipe-project-pattern/en.md. Each
one was measured against Goose 1.45.0 rather than read from the documentation,
and each fails silently at runtime: a recipe that breaks one of them still
validates, still starts, and still produces a plausible-looking answer.

`goose recipe validate` covers the schema. This covers what the schema cannot
see. It runs without a provider call and without network access; the optional
`goose` pass is skipped with a note when the binary is absent, so CI does not
depend on a Goose install.

Usage:  python3 tests/validate_recipes.py
Exit:   0 when every check passes, 1 on the first failure category found.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RECIPES_DIR = REPO_ROOT / "recipes"
EXTENSIONS_FILE = REPO_ROOT / "extensions.yaml"
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

TOOLS_SNAPSHOT = REPO_ROOT / "tests" / "kamerplanter-tools-list.json"

# The two inputSchema keys that mark a Kamerplanter MCP tool as state-changing.
# Measured: every write carries both and no read carries either (12/12 on
# 2026-08-16, 16/16 on 2026-11-05 and 2026-11-06), so a tool carrying only one
# of them breaks the classifier and is refused rather than guessed.
WRITE_MARKER_KEYS = frozenset({"dry_run", "idempotency_key"})


def classify_tools(tools: dict[str, list[str]]) -> tuple[set[str], list[str]]:
    """Return the state-changing tools of a tools/list snapshot, plus every
    tool whose inputSchema carries only one of the two marker keys."""
    writes = {name for name, keys in tools.items() if WRITE_MARKER_KEYS <= set(keys)}
    ambiguous = sorted(
        name for name, keys in tools.items() if len(WRITE_MARKER_KEYS & set(keys)) == 1
    )
    return writes, ambiguous


def load_state_changing_tools(path: Path = TOOLS_SNAPSHOT) -> set[str]:
    """The state-changing set, derived from the checked-in tools/list snapshot.

    Refresh the snapshot with scripts/snapshot-tools-list.sh whenever the
    server's surface changes. A new write tool then joins this set in the same
    change, and every policy block that does not name it fails, instead of the
    tool passing the guard silently as it did three times while this set was a
    hand-maintained list (#80, #85).
    """
    try:
        tools = json.loads(path.read_text())["tools"]
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f"{path.relative_to(REPO_ROOT)}: unreadable tools/list snapshot ({error})")
    writes, ambiguous = classify_tools(tools)
    if ambiguous:
        sys.exit(
            f"{path.relative_to(REPO_ROOT)}: {', '.join(ambiguous)} carry only one of "
            f"{sorted(WRITE_MARKER_KEYS)}; the write classifier no longer holds"
        )
    if not writes:
        sys.exit(f"{path.relative_to(REPO_ROOT)}: no state-changing tool found")
    return writes


# Kamerplanter MCP tools that change server state. A recipe naming any of these
# outside a policy block has to carry the -apply suffix.
STATE_CHANGING_TOOLS = load_state_changing_tools()

VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

# A recipe names the skills it loads in prose: "load the skill `plant-photo-read`".
# Both orders occur, so match either side of the word.
SKILL_REF_PATTERN = re.compile(
    r"skills?\s+`([a-z0-9][a-z0-9-]*)`|`([a-z0-9][a-z0-9-]*)`\s+skill"
)

AGENTS_DIR = REPO_ROOT / ".claude" / "agents"

# Goose's own documentation recommends `.agents/agents/` for project agents, and
# under the claude-code provider nothing there is reachable — measured 2026-08-07,
# see spec/goose/recipe-project-pattern/en.md §"Agents from a project checkout".
# The probe that established this has to live there to keep measuring it; nothing
# else may.
UNREACHABLE_AGENTS_DIR = REPO_ROOT / ".agents" / "agents"
UNREACHABLE_AGENTS_ALLOWED = {"probe-agents-dir"}


class Findings:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.notes: list[str] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def note(self, message: str) -> None:
        self.notes.append(message)


# A recipe declares its tool policy under two literal markers, each opening a
# block whose body is backticked tool names and punctuation. A name inside a
# block is policy; a name outside every block is a call.
#
# That convention replaces the prose analysis this file used to carry —
# sentence spans, list continuations, clause splitting, name-only-line
# detection. Twelve review rounds went into making that infer intent from
# English, and it misread in both directions throughout. Deciding it by
# convention is what makes it checkable at all.
POLICY_MARKERS = ("Forbidden by name:", "Permitted by name:")
# The markers a read-only recipe's policy is read at: `Permitted by name:` is
# not policy there, for the reason `calls_state_changing_tools` gives.
READ_ONLY_MARKERS = ("Forbidden by name:",)

BULLET_PREFIX_PATTERN = re.compile(r"^\s*[-*]\s")
# The bullet prefix with every space after the marker: its end is the column
# the bullet's text starts at.
BULLET_TEXT_PATTERN = re.compile(r"^\s*[-*]\s+")
BACKTICK_SPAN_PATTERN = re.compile(r"`[^`]*`")
TABLE_ROW_PATTERN = re.compile(r"^\s*\|")
# A fence at ANY indent, unlike CommonMark's three spaces: a prompt nests its
# examples inside list items, and reading too much as code is the safe
# direction for every caller of `code_spans`.
CODE_FENCE_PATTERN = re.compile(r"^[ \t]*(`{3,}|~{3,})")
BACKTICK_RUN_PATTERN = re.compile(r"`+")


def code_spans(text: str) -> list[tuple[int, int]]:
    """Character spans of `text` that are code: fenced blocks and inline spans.

    The one predicate every marker check asks "is this a mention?" with (#78,
    #84). A fence runs from its opening line to a closing line of the same
    character, at least as long, with nothing after it — or to the end of the
    text when none comes. Outside fences, an inline span opens at a run of
    backticks and closes at the next run of exactly the same length within
    the same paragraph (a blank line or a fence ends it), as in CommonMark; a
    run with no partner is literal text. So `Don`t` does not open a span, and
    a single backtick inside ``a ` b`` does not close one.

    Not modelled: backslash escapes, and a list item ending a paragraph. Both
    can only read more as code than CommonMark would, and a marker read as
    code fails a recipe — its names count as calls, its categories as
    missing — rather than passing one.
    """
    spans: list[tuple[int, int]] = []
    paragraph_start = None
    fence: tuple[str, int, int] | None = None
    offset = 0

    def close_paragraph(end: int) -> None:
        if paragraph_start is not None:
            spans.extend(inline_code_spans(text, paragraph_start, end))

    for line in text.split("\n"):
        line_end = offset + len(line)
        if fence is not None:
            char, length, start = fence
            stripped = line.strip()
            if (
                stripped
                and set(stripped) == {char}
                and len(stripped) >= length
            ):
                spans.append((start, line_end))
                fence = None
        elif opener := CODE_FENCE_PATTERN.match(line):
            close_paragraph(offset)
            paragraph_start = None
            run = opener.group(1)
            fence = (run[0], len(run), offset)
        elif not line.strip() or ATX_HEADING_PATTERN.match(line):
            # A heading ends the paragraph and is a block of its own, as in
            # CommonMark; a backtick before it must not pair with one after.
            close_paragraph(offset)
            paragraph_start = None
            if line.strip():
                spans.extend(inline_code_spans(text, offset, line_end))
        elif paragraph_start is None:
            paragraph_start = offset
        offset = line_end + 1
    if fence is not None:
        spans.append((fence[2], len(text)))
    else:
        close_paragraph(len(text))
    return sorted(spans)


def inline_code_spans(text: str, start: int, end: int) -> list[tuple[int, int]]:
    """Inline code spans of `text[start:end]`, paired by run length."""
    runs = list(BACKTICK_RUN_PATTERN.finditer(text, start, end))
    spans, index = [], 0
    while index < len(runs):
        length = len(runs[index].group())
        partner = next(
            (
                later
                for later in range(index + 1, len(runs))
                if len(runs[later].group()) == length
            ),
            None,
        )
        if partner is None:
            index += 1
            continue
        spans.append((runs[index].start(), runs[partner].end()))
        index = partner + 1
    return spans


def in_code(spans: list[tuple[int, int]], position: int) -> bool:
    """True when `position` falls inside one of `code_spans`' spans."""
    return any(start <= position < end for start, end in spans)


def tool_pattern(tool: str) -> re.Pattern:
    """Match a tool by its bare name or in its `mcp__<server>__` form.

    A plain `\\b<tool>\\b` does not match the prefixed form: the separator is
    `__` and `_` is a word character, so there is no boundary between
    `kamerplanter__` and `archive_plant`. That emptied the match set and left
    this guard inert against every recipe in this repository.
    """
    return re.compile(rf"(?<![A-Za-z0-9_])(?:mcp__[A-Za-z0-9_]+__)?{re.escape(tool)}\b")


def is_name_line(text: str) -> bool:
    """True when `text` carries backticked names and punctuation, nothing else."""
    rest = BULLET_PREFIX_PATTERN.sub("", text)
    rest = BACKTICK_SPAN_PATTERN.sub("", rest)
    return not re.search(r"[A-Za-z0-9]", rest)


def continues_block(text: str) -> bool:
    """A continuation line is a name line that actually carries a name.

    Without the second half a punctuation-only line — a Markdown rule `---`,
    an ellipsis, an empty bullet — held the block open and absorbed the name
    below it, because stripping the backtick spans from nothing also leaves
    nothing.
    """
    return is_name_line(text) and bool(BACKTICK_SPAN_PATTERN.search(text))


def policy_spans(
    prompt: str, marker: str, skip_code: bool = True
) -> list[tuple[int, int]]:
    """Character spans of every block introduced by `marker`.

    Spans, not strings: excision by `str.replace` is position-blind and left an
    outer block standing whenever another sat inside it.

    A marker inside code (`code_spans`) is a mention of the convention and
    opens nothing (#78): a quoted `Forbidden by name:` followed by a name on
    the next line used to excise that name as policy, hiding a real call.

    `skip_code=False` reads every marker as a block. That is the strict
    reading for a caller to whom a found block is the failure — a permitted
    write in `permitting_skill_loads` — where skipping code would be the
    unsafe direction.
    """
    spans = []
    code = code_spans(prompt) if skip_code else []
    for match in re.finditer(re.escape(marker), prompt):
        if in_code(code, match.start()):
            continue
        # A marker on the prompt's last line has no newline after it. Treating
        # that as "the block runs to the end" handed the whole remainder to
        # policy, prose and calls included.
        newline = prompt.find("\n", match.end())
        end = len(prompt) if newline == -1 else newline
        head = prompt[match.end():end]
        if not is_name_line(head):
            # Prose on the marker's own line. The policy reaches its last name
            # and no further — taking the whole line exempted everything after
            # it, so `Forbidden by name: \`a\`; call \`b\` instead.` read as if
            # nothing were called.
            # The contiguous run of names directly after the marker, and no
            # further. Taking the last name on the line instead would have
            # swallowed the call in `Forbidden by name: \`a\`; call \`b\`
            # instead.` — where the call IS the last name.
            stop, cursor = match.end(), match.end()
            for span in BACKTICK_SPAN_PATTERN.finditer(head):
                between = head[cursor - match.end():span.start()]
                # A full stop ends the run as surely as a word does. Measured:
                # `Forbidden by name: <names>. \`create_inspection\` is called
                # at step 4.` pulled that last name into the block, because the
                # gap between it and the previous one held punctuation only —
                # so a recipe that really called it read as complete AND as
                # calling nothing.
                #
                # This scan runs only where the marker line also carries prose.
                # A line of names alone never reaches it, so `\`a\`. \`b\`.` on
                # a bare name line still counts both — the full-stop rule is
                # not a general "a period-separated list ends at the first
                # name". Where the scan does run, for a guard "the sentence
                # ended" is the safe reading.
                if re.search(r"[A-Za-z0-9.]", between):
                    break
                cursor = match.end() + span.end()
                stop = cursor
            spans.append((match.start(), stop))
            continue
        # A marker line that already carries names continues onto continuation
        # lines only — a new bullet is a new element. A marker line with no
        # names of its own is the nested-bullet shape, where the bullets are
        # the list.
        nested = not BACKTICK_SPAN_PATTERN.search(head)
        line_start = prompt.rfind("\n", 0, match.start()) + 1
        marker_indent = len(prompt[line_start:]) - len(prompt[line_start:].lstrip())
        for line in prompt[end + 1:].split("\n"):
            if not line.strip() or not continues_block(line):
                break
            if TABLE_ROW_PATTERN.match(line):
                break
            bullet = BULLET_PREFIX_PATTERN.match(line)
            if bullet:
                # The two shapes differ, and not "whichever shape the marker
                # line used" — an earlier wording here claimed exactly that
                # and was the reverse of the code. Where the marker line
                # carries no names, the bullets below it ARE the list: a
                # deeper one continues it, a sibling or shallower one is the
                # next element. Where the marker line already carries names,
                # `not nested` short-circuits and any bullet ends the block,
                # the deeper one included.
                indent = len(line) - len(line.lstrip())
                if not nested or indent <= marker_indent:
                    break
            end += 1 + len(line)
        spans.append((match.start(), end))
    return spans


def outside_policy(prompt: str, markers: tuple[str, ...] = POLICY_MARKERS) -> str:
    """The prompt with every policy block cut out.

    Excision, not name-set subtraction: subtracting the names declared in a
    block from the names found in the whole prompt is empty by construction
    whenever a recipe declares them all.
    """
    spans = sorted(
        span for marker in markers for span in policy_spans(prompt, marker)
    )
    kept, cursor = [], 0
    for start, end in spans:
        if start >= cursor:
            kept.append(prompt[cursor:start])
            cursor = end
        else:
            cursor = max(cursor, end)
    kept.append(prompt[cursor:])
    return "\n".join(kept)


def calls_state_changing_tools(
    body: str,
    is_apply: bool = True,
    tools: Iterable[str] = STATE_CHANGING_TOOLS,
) -> list[str]:
    """`tools` named outside every policy block — i.e. called — sorted.

    `Permitted by name:` counts as policy only where the filename says the
    recipe writes. Excising it unconditionally let any recipe declare a write
    permitted and drop out of the guard: renaming
    `diary-photo-analysis-apply.yaml` to drop the suffix left a recipe that
    claims and submits diary analyses passing clean.

    `tools` defaults to the sixteen; the Home Assistant guard passes
    `HA_UNCLASSIFIED_INTENTS`. A read-only recipe is read at `is_apply=False`
    (the `Forbidden by name:` marker alone); a skill at the default, both
    markers. For the sixteen, whether a skill's `Permitted by name:` block is
    legitimate is the separate `check_permitting_skill_loads` question, for
    the sixteen and the Home Assistant intents alike (#84).
    """
    markers = POLICY_MARKERS if is_apply else READ_ONLY_MARKERS
    remainder = outside_policy(body, markers)
    return sorted(tool for tool in tools if tool_pattern(tool).search(remainder))


def policy_text(
    body: str, markers: tuple[str, ...] = POLICY_MARKERS, skip_code: bool = True
) -> str:
    """Everything INSIDE a policy block — the complement of `outside_policy`."""
    spans = sorted(
        span
        for marker in markers
        for span in policy_spans(body, marker, skip_code)
    )
    return "\n".join(body[start:end] for start, end in spans)


def missing_from_policy(
    body: str,
    markers: tuple[str, ...] = POLICY_MARKERS,
    tools: Iterable[str] = STATE_CHANGING_TOOLS,
) -> list[str]:
    """`tools` — the sixteen by default — minus what the artefact names INSIDE
    a policy block, sorted.

    The guard above answers the opposite question — which names sit OUTSIDE a
    block, i.e. are called — and cannot see a subset at all, because an absent
    name is outside nothing. Measured: stripping eight of the twelve out of a
    read-only recipe's `Forbidden by name:` block left the whole gate green.

    Completeness is a property of the union. The `-apply` recipes split the
    set into a permitted and a forbidden half — the diary pair as two plus
    fourteen — so demanding sixteen in the forbidden half alone would fail
    exactly the recipes that declare their writes correctly.

    A marker inside a fenced example or an inline code span declares nothing:
    `policy_spans` skips it, so a quoted template no longer makes a recipe
    look complete (#84; before it, this was an accepted false negative).
    """
    inside = policy_text(body, markers)
    return sorted(tool for tool in tools if not tool_pattern(tool).search(inside))


# Home Assistant's catalog is assembled per instance, so its actuating side
# cannot be forbidden by name the way the sixteen are. A read-only recipe
# forbids it by category behind a literal marker instead, and the marker's
# sentence has to name every category — the words prove the categories are
# named, the marker carries the meaning (#75).
HA_CATEGORY_MARKER = "Forbidden on Home Assistant:"

# Goose renders `prompt` as a template before the model sees it, and a
# conditional block is measured to work (`{% if view == "months" %}`, 2026-11-06,
# #87). Every check here reads the unrendered text, so a policy block inside a
# conditional is counted although a rendered run may drop it.
TEMPLATE_BLOCK_PATTERN = re.compile(r"\{%-?\s*(if|for|endif|endfor)\b")


def conditional_policy_markers(prompt: str) -> list[str]:
    """Policy markers that sit inside a `{% if %}` or `{% for %}` block."""
    depth_at: list[tuple[int, int]] = []
    depth = 0
    for match in TEMPLATE_BLOCK_PATTERN.finditer(prompt):
        depth += 1 if match.group(1) in ("if", "for") else -1
        depth_at.append((match.end(), depth))
    found = []
    for marker in (*POLICY_MARKERS, HA_CATEGORY_MARKER):
        for hit in re.finditer(re.escape(marker), prompt):
            inside = 0
            for end, level in depth_at:
                if end > hit.start():
                    break
                inside = level
            if inside > 0 and marker not in found:
                found.append(marker)
    return found
HA_CATEGORY_TERMS = ("on or off", "value", "script", "scene", "automation")

# Two intents on the reference instance whose effect is unclassified
# (spec/mcp/home-assistant-mcp-server/en.md). Until the operator classifies
# them, a read-only recipe forbids both by name and calls neither.
HA_UNCLASSIFIED_INTENTS = ("TimeTillErnte", "time_till")

# A list item's prefix — bullet or number — with every space after it, for
# the Home Assistant scope alone: its end is the column the item's text
# starts at. `policy_spans` keeps the narrower `BULLET_PREFIX_PATTERN`.
LIST_ITEM_PATTERN = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
# A sentence terminator: `.`, `!` or `?`, any closing brackets or quotes,
# then whitespace or the end of the text.
SENTENCE_END_PATTERN = re.compile(r"[.!?][)\]\"']*(?=\s|$)")


def ha_category_scopes(prompt: str) -> list[str]:
    """The scope each `Forbidden on Home Assistant:` marker opens.

    A scope runs from the marker to the end of the sentence the marker sits
    in: the first `.`, `!` or `?` — with any closing `)`, `]`, `"` or `'`
    after it — that is followed by whitespace or the end of the text. It is
    cut earlier at the first following line that is one of:

    - blank (whitespace-only);
    - a list item (`-`, `*`, `+`, `1.`, `1)`) indented at most as deep as the
      line carrying the marker;
    - a line that is not a list item, indented less than the marker line's
      text column.

    The sentence bound is what ends a scope in the common case, whatever the
    surrounding format: a plain line, a bullet, and a numbered item each end
    where their sentence does, so a next step that follows at the marker's
    own indent is not read as its continuation (pre-merge review R1, R2). The
    line cuts bound a scope that carries no terminator — categories listed as
    nested bullets without punctuation, say. The text column is where the
    marker line's prose starts: past the list prefix (`  - ` and `1. ` are
    columns 4 and 3) when the marker line is a list item, the line's own
    indent when it is not. A deeper list item continues the scope, and so
    does its own wrapped text. Text before the marker on its own line is not
    part of it.

    A period that ends no sentence still ends the scope when whitespace
    follows it: `e.g. a light` cuts at `e.g.`. That can only fail a recipe
    that names its categories after such a period, never pass one that
    omits them; a decimal (`0.5`) or a dotted name (`light.turn_on`) has no
    whitespace after its period and does not cut.

    A marker inside code — a fenced block or an inline span, as
    `code_spans` decides it — is a mention of the rule, not the rule, and
    opens nothing (#77, #84). Counting backticks on the marker's line instead
    read a fenced example as the rule, and an apostrophe typed as a backtick
    hid a real marker.

    Deliberately simpler than `policy_spans`: that one bounds a run of names,
    this one bounds prose, so a prose line continues it where it would end a
    name block.
    """
    scopes = []
    code = code_spans(prompt)
    for match in re.finditer(re.escape(HA_CATEGORY_MARKER), prompt):
        if in_code(code, match.start()):
            continue
        line_start = prompt.rfind("\n", 0, match.start()) + 1
        marker_line = prompt[line_start:]
        marker_indent = len(marker_line) - len(marker_line.lstrip())
        item = LIST_ITEM_PATTERN.match(marker_line)
        text_column = item.end() if item else marker_indent
        lines = prompt[match.end():].split("\n")
        kept = [lines[0]]
        for line in lines[1:]:
            if not line.strip():
                break
            indent = len(line) - len(line.lstrip())
            if LIST_ITEM_PATTERN.match(line):
                if indent <= marker_indent:
                    break
            elif indent < text_column:
                break
            kept.append(line)
        scope = "\n".join(kept)
        if sentence_end := SENTENCE_END_PATTERN.search(scope):
            scope = scope[:sentence_end.end()]
        scopes.append(scope)
    return scopes


def ha_category_term_pattern(term: str) -> re.Pattern:
    """Match a category as whole words, with an optional plural `s`.

    Read against text whose whitespace runs are already collapsed to one
    space, so the single space inside `on or off` stands for any wrap.
    """
    return re.compile(rf"\b{re.escape(term)}s?\b")


def ha_category_missing(prompt: str) -> list[str]:
    """`HA_CATEGORY_TERMS` absent from every marker scope, sorted.

    Case-insensitive whole-word match over the union of all marker scopes,
    with every whitespace run collapsed to one space first, so a category may
    wrap across a line and the categories may be split across two markers. A
    plural `s` counts (`values`, `scripts`); a longer word does not
    (`scenery`, `transcript`, `devalued`, `button or offset`). No marker means
    all five are missing.

    Known limit, accepted: the terms are keywords, not structure — a scope
    can name all five and forbid nothing, and the marker is what carries the
    prohibition. That can only pass a recipe that names the categories badly,
    never fail one that names them well.
    """
    text = " ".join(" ".join(ha_category_scopes(prompt)).split()).lower()
    return sorted(
        term
        for term in HA_CATEGORY_TERMS
        if not ha_category_term_pattern(term).search(text)
    )


SKILL_SERVER_REFERENCE = "mcp__kamerplanter__"


def skill_missing_tools(text: str) -> list[str]:
    """The sixteen minus what a skill names ANYWHERE, for a skill that reaches
    the Kamerplanter server at all.

    The selector is the reference to `mcp__kamerplanter__`, not "every skill":
    the four `*-review` lenses read this checkout and never a garden, and a
    forbidden list there would be noise. Measured on develop, the reference
    selects exactly the seven garden skills.

    This is a completeness check and nothing more: a name anywhere counts,
    inside a call or under `## Gotchas` alike. The call direction is the
    separate obedience guard below, `skill_unpermitted_calls` (#55).
    """
    if SKILL_SERVER_REFERENCE not in text:
        return []
    return sorted(
        tool for tool in STATE_CHANGING_TOOLS if not tool_pattern(tool).search(text)
    )


# The two level-2 headings whose content is explanation rather than
# instruction. A closed set and a literal match, so deciding a section is a
# lookup and never a reading of the sentence (#55).
EXPLANATION_HEADINGS = {"Gotchas", "Source"}

ATX_HEADING_PATTERN = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
FENCE_PATTERN = re.compile(r"^ {0,3}(`{3,}|~{3,})")
# A closing fence carries nothing after its run — an info string or prose
# after the backticks makes it content, not a closer.
FENCE_CLOSE_PATTERN = re.compile(r"^ {0,3}(`{3,}|~{3,})[ \t]*$")
# A setext underline. It can only END an explanation section: only the ATX
# forms `## Gotchas` and `## Source` open one.
SETEXT_UNDERLINE_PATTERN = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")

# Lines a skill must carry verbatim although they name state-changing tools,
# keyed by skill directory and the EXACT stripped line. A prefix match was
# tried and withdrawn: it held any new line that opened with the same words,
# a call appended to them included. The entry holds only when that line occurs
# exactly once, and is stale otherwise. Per line, never per skill: the rest of
# the skill stays guarded.
SKILL_LINE_ALLOWANCES = {
    (
        "plant-planning",
        "The measured catalog has no tool that creates a planting run, a sowing "
        "or planting task, or a plan. The write tools it records are "
        "add_plant_diary_entry, confirm_care_task, archive_plant, "
        "set_plant_location, claim_diary_analysis, submit_diary_analysis, "
        "transition_plant_phase, assign_species_phase_sequence, "
        "assign_nutrient_plan, record_feeding_event, create_inspection, "
        "clone_nutrient_plan, set_nutrient_plan_phase_targets, "
        "create_substrate_mix and set_plant_substrate, and the setup tool "
        "create_site; none does.",
    ): (
        "spec/process/plant-planning-and-planting-calendar/en.md §F requires "
        "every plan's APPLY CONTRACT to enumerate the sixteen write tools"
    ),
}


def normalise_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def skill_instruction_text(text: str) -> str:
    """The SKILL.md with every explanation line blanked, line count preserved.

    Explanation is exactly the content under a level-2 ATX heading reading
    `Gotchas` or `Source`, up to the next level-1 or level-2 heading — ATX or
    setext. Everything else is instruction, fail-closed: frontmatter, text
    before the first heading, any other heading, a `### Gotchas` nested
    elsewhere. A heading inside a fenced block or an HTML comment is not a
    heading, and no line of the frontmatter is one either — a YAML comment
    starts with `#` too. A setext underline ends a section and never opens
    one, and its title line is returned to instruction. Line endings are
    normalised to LF first.
    """
    lines = normalise_newlines(text).split("\n")
    frontmatter_end = -1
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                frontmatter_end = index
                break
    explanation, fence, comment, paragraph = False, None, False, False
    kept = []
    for index, line in enumerate(lines):
        if index > frontmatter_end:
            was_paragraph, paragraph = paragraph, False
            if fence is not None:
                closer = FENCE_CLOSE_PATTERN.match(line)
                if closer and closer.group(1)[0] == fence[0] and len(
                    closer.group(1)
                ) >= len(fence):
                    fence = None
            elif comment:
                if "-->" in line:
                    comment = False
            elif fence_match := FENCE_PATTERN.match(line):
                fence = fence_match.group(1)
            elif "<!--" in line and "-->" not in line[line.index("<!--") + 4:]:
                comment = True
            elif heading := ATX_HEADING_PATTERN.match(line):
                level = len(heading.group(1))
                if level <= 2:
                    explanation = level == 2 and (heading.group(2) or "") in EXPLANATION_HEADINGS
            elif was_paragraph and SETEXT_UNDERLINE_PATTERN.match(line):
                explanation = False
                kept[-1] = lines[index - 1]
            else:
                paragraph = bool(line.strip())
        kept.append("" if explanation else line)
    return "\n".join(kept)


def blank_spans(text: str, spans: list[tuple[int, int]]) -> str:
    """`text` with every span overwritten by spaces, newlines kept, so a line
    number found afterwards is still the line number in the file."""
    chars = list(text)
    for start, end in spans:
        for position in range(start, end):
            if chars[position] != "\n":
                chars[position] = " "
    return "".join(chars)


def skill_permitted_tools(text: str) -> set[str]:
    """State-changing names inside the skill's instruction-side
    `Permitted by name:` blocks — the only licence a skill has to call."""
    inside = policy_text(skill_instruction_text(text), ("Permitted by name:",))
    return {tool for tool in STATE_CHANGING_TOOLS if tool_pattern(tool).search(inside)}


def skill_unpermitted_calls(
    text: str,
    skill: str,
    allowances: dict[tuple[str, str], str] = SKILL_LINE_ALLOWANCES,
) -> list[tuple[int, str]]:
    """(line, tool) for each state-changing tool a skill's instruction calls
    without listing it in its own `Permitted by name:` block (#55).

    Predicate: in the instruction sections (see `skill_instruction_text`), with
    every `Forbidden by name:` and `Permitted by name:` block cut out exactly as
    for a recipe, any remaining state-changing name — bare or
    `mcp__kamerplanter__`-prefixed — is a call, and passes only when the skill's
    own `Permitted by name:` block names it. A skill has no `-apply` suffix to
    license a call, so that block is the whole licence; P3's loader bound in
    `permitting_skill_loads` keeps the block itself from becoming a bypass.

    Selector: every `.claude/skills/*/SKILL.md`, not only those that reference
    `mcp__kamerplanter__`. A bare name is a call too, and the prefix selector of
    `skill_missing_tools` cannot see it.

    Allowance: one line in `plant-planning`, as the exact stripped line, because a
    process spec mandates that line verbatim (`SKILL_LINE_ALLOWANCES` carries
    the reason). An allowance whose line is absent or duplicated holds nothing and fails the gate — see
    `stale_skill_allowances`.

    Limit: a call written under `## Gotchas` or `## Source` is explanation by
    declaration and invisible here. Telling a call from a mention there would
    mean reading the sentence, which is what the convention exists to avoid.
    spec/goose/recipe-project-pattern/en.md makes it a MUST enforced by review.
    """
    instruction = skill_instruction_text(text)
    spans = [
        span
        for marker in POLICY_MARKERS
        for span in policy_spans(instruction, marker)
    ]
    remainder = blank_spans(instruction, spans)
    permitted = skill_permitted_tools(text)
    originals = normalise_newlines(text).split("\n")
    stripped = [line.strip() for line in originals]
    held = {
        allowed
        for (name, allowed) in allowances
        if name == skill and stripped.count(allowed) == 1
    }
    calls = []
    for number, (line, original) in enumerate(
        zip(remainder.split("\n"), stripped), start=1
    ):
        if original in held:
            continue
        for tool in sorted(STATE_CHANGING_TOOLS - permitted):
            if tool_pattern(tool).search(line):
                calls.append((number, tool))
    return calls


def permitting_skill_loads(
    recipes: dict[str, tuple[bool, str]], skills: dict[str, str]
) -> list[tuple[str, str]]:
    """(recipe, skill) for each read-only recipe that loads a skill whose
    `Permitted by name:` block carries a state-changing name (#55).

    `recipes` maps a recipe filename to (is_apply, prose body); `skills` maps a
    skill directory name to its SKILL.md. A skill's permitted block exempts its
    calls from `skill_unpermitted_calls`, and a skill composes into the
    caller's context, so without this bound any skill could declare a write
    permitted and carry it into a recipe that claims to read. It is the
    skill-side counterpart of the rule in `check_recipe` that a recipe with a
    `Permitted by name:` block must carry the `-apply` suffix.

    The permitted block is read across the whole file, explanation included:
    the guard ignores a block under `## Gotchas`, but the model still reads it,
    so the bound is the stricter reading.

    A recipe loads a skill when the skill's directory name occurs anywhere in
    its text as a whole token — bounded by anything but a letter, digit, `_` or
    `-`, so `claimer-legacy` is not `claimer`. Fail-closed and deliberately
    without grammar: `SKILL_REF_PATTERN` was used first and missed a
    list ("the skills a and b"), a name after "Follow", "the b skill" without
    backticks, and a capitalised "Skill". A mere mention therefore counts as a load; that direction can only
    fail a recipe, never pass one. The same token rule is followed
    transitively through each loaded skill, so a skill-to-skill load cannot
    become the bypass — but there only in the skill's instruction text
    (`skill_instruction_text`). Counting explanation too was tried and
    withdrawn: plant-photo-read's `## Gotchas` says the claim tools belong to
    diary-analysis-claim, and that sentence alone made every read-only recipe
    loading plant-photo-read read as loading the claim skill.

    For the same reason a permitted block inside code still counts here
    (`skip_code=False`): a quoted template is a mention to the other guards,
    but the model reads it, and skipping it would pass the load (#84 review).
    """
    permitting = {
        name
        for name, text in skills.items()
        if any(
            tool_pattern(tool).search(
                policy_text(text, ("Permitted by name:",), skip_code=False)
            )
            for tool in STATE_CHANGING_TOOLS | set(HA_UNCLASSIFIED_INTENTS)
        )
    }

    def referenced(text: str) -> set[str]:
        return {
            name
            for name in skills
            if re.search(rf"(?<![A-Za-z0-9_-]){re.escape(name)}(?![A-Za-z0-9_-])", text)
        }

    loads = []
    for recipe, (is_apply, body) in sorted(recipes.items()):
        if is_apply:
            continue
        seen, pending = set(), referenced(body)
        while pending:
            skill = pending.pop()
            if skill in seen:
                continue
            seen.add(skill)
            pending |= referenced(skill_instruction_text(skills[skill])) - seen
        loads.extend((recipe, skill) for skill in sorted(seen & permitting))
    return loads


def check_permitting_skill_loads(findings: Findings) -> None:
    if not (SKILLS_DIR.is_dir() and RECIPES_DIR.is_dir()):
        return
    skills = {
        path.parent.name: path.read_text(encoding="utf-8")
        for path in SKILLS_DIR.glob("*/SKILL.md")
    }
    recipes = {}
    for path in sorted(RECIPES_DIR.glob("*.yaml")):
        try:
            recipe = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue  # check_recipe already reports it
        if not isinstance(recipe, dict):
            continue
        body = "\n".join(
            value
            for key in ("description", "instructions", "prompt")
            if isinstance(value := recipe.get(key), str)
        )
        recipes[path.name] = (path.stem.endswith("-apply"), body)
    for recipe, skill in permitting_skill_loads(recipes, skills):
        findings.error(
            f"recipes/{recipe}",
            f"loads the skill `{skill}`, whose `Permitted by name:` block "
            "declares a write, without an `-apply` filename suffix. A skill "
            "composes into the caller's context, so its permission becomes "
            "this recipe's: rename the recipe and say so in `description`, or "
            "load a skill that permits nothing.",
        )


def stale_skill_allowances(
    text: str,
    skill: str,
    allowances: dict[tuple[str, str], str] = SKILL_LINE_ALLOWANCES,
) -> list[str]:
    """Allowed lines for `skill` that do not occur in its SKILL.md exactly once.

    Absent, the entry would sit ready to hold whatever line takes that text
    next; duplicated, it would hold a copy nobody reviewed.
    """
    stripped = [line.strip() for line in normalise_newlines(text).split("\n")]
    return sorted(
        allowed
        for (name, allowed) in allowances
        if name == skill and stripped.count(allowed) != 1
    )


def load_yaml(path: Path, findings: Findings) -> dict | None:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        findings.error(path.name, f"is not parseable YAML — {exc}")
        return None


def check_flat_discovery(findings: Findings) -> None:
    """Goose lists *.yaml directly under each recipe directory; it does not walk
    subdirectories. A recipe in a subfolder is invisible, with no error."""
    for entry in RECIPES_DIR.iterdir():
        if entry.is_dir():
            findings.error(
                f"recipes/{entry.name}/",
                "is a subdirectory — recipe discovery is flat, so nothing "
                "inside it is reachable. Encode grouping in the filename.",
            )


def check_recipe(path: Path, findings: Findings) -> None:
    recipe = load_yaml(path, findings)
    if not isinstance(recipe, dict):
        return

    where = f"recipes/{path.name}"

    # Search the parsed prose fields rather than the raw file: a comment that
    # explains why a mechanism is *not* used names it too, and matching that
    # would fail the very recipe that documents the trap correctly.
    body = "\n".join(
        value
        for key in ("description", "instructions", "prompt")
        if isinstance(value := recipe.get(key), str)
    )

    # A recipe-local extensions block REPLACES the shared set rather than
    # extending it, silently dropping every server it does not redeclare.
    if "extensions" in recipe:
        findings.error(
            where,
            "declares its own `extensions:` block. That replaces "
            "extensions.yaml entirely for this run rather than extending it. "
            "Remove the block, or accept that the recipe forgoes every shared "
            "server it does not redeclare.",
        )

    # A recipe with only `instructions` loads and validates, then dies on a
    # headless run with `no text provided for prompt`.
    prompt = recipe.get("prompt")
    if not (isinstance(prompt, str) and prompt.strip()):
        findings.error(
            where,
            "has no non-empty `prompt`. A headless run fails with "
            "`no text provided for prompt`, and a constraint stated only in "
            "`instructions` has been observed to be ignored.",
        )

    description = recipe.get("description") or ""
    if not description.strip():
        findings.error(where, "has an empty `description`.")

    # A write-capable recipe announces itself in its filename and description.
    is_apply = path.stem.endswith("-apply")

    # Computed here, above the write-guard, because that guard reads `missing`
    # to tell which repair to advise: a prohibition written as one annotated
    # bullet per tool ends the block at the marker, leaving every name outside
    # it, and "rename the file to `-apply`" is the wrong advice for a recipe
    # that calls nothing. Both checks still report; only the wording varies.
    prompt_text = prompt if isinstance(prompt, str) else ""
    missing = missing_from_policy(prompt_text)
    for marker in conditional_policy_markers(prompt_text):
        findings.error(
            where,
            f"has `{marker}` inside a template conditional in its `prompt`. "
            "Goose renders the prompt first, so a run may never see that block "
            "while this check counts it; keep every policy block outside "
            "`{% if %}` / `{% for %}`.",
        )

    if not is_apply:
        # A recipe may name a state-changing tool purely to forbid it, so the
        # policy blocks are cut out before the remainder is read.
        calling = calls_state_changing_tools(body, is_apply=False)
        permitted = policy_spans(body, "Permitted by name:")
        if permitted:
            findings.error(
                where,
                "declares a `Permitted by name:` block without an `-apply` "
                "filename suffix. That marker says which writes a recipe is "
                "for, so a recipe that has one is a writer and has to say so "
                "in its name and its `description`.",
            )
        # A block that collapsed at its marker changes what the advice should
        # be, not whether there is a finding. Suppressing the report instead
        # was tried and removed: a recipe whose block collapses *and* calls a
        # tool for real then showed only the completeness finding, whose repair
        # — list the missing names — leaves the call in place.
        #
        # Keying the suppression on `missing` alone had also removed a check
        # `develop` has. Measured: a recipe with no `prompt` that calls
        # `archive_plant` from `instructions` reported twice on `develop` and
        # once here, because `missing` is the whole set for an empty prompt while
        # completeness stays silent for the same reason.
        block_collapsed = bool(policy_spans(prompt_text, "Forbidden by name:")) and len(
            missing
        ) == len(STATE_CHANGING_TOOLS)
        advice = (
            "Its `Forbidden by name:` block parses as empty, so every name in "
            "it reads as a call: put a plain run of names directly after the "
            "marker, and keep the prose out of that run."
            if block_collapsed
            else "Move the name into that block if the recipe forbids the "
            "tool — prose between two names ends the block there, and a "
            "conjunction is prose, so `` `a`, and `b`. `` leaves `b` outside "
            "it; rename the file and say so in `description` if the recipe "
            "really calls the tool."
        )
        if calling:
            findings.error(
                where,
                f"calls state-changing tools ({', '.join(calling)}) outside a "
                f"`Forbidden by name:` block and without an `-apply` filename "
                f"suffix. {advice}",
            )
    # The prohibition has to name each tool individually, and the catalog has
    # grown three times — four names, then seven, then twelve, then sixteen. A
    # list written against an earlier count is a subset today, and the guard
    # above cannot see that: it reads names OUTSIDE a policy block, and an
    # absent name is outside nothing. Measured on 2026-09-14: every recipe
    # here named all twelve then, so this check started green and stays a
    # floor.
    #
    # Scoped to `prompt`, never to `body`. The MUST is about the prompt
    # precisely because `instructions` is not enforced on a headless run, so
    # reading all three fields legitimised the placement the rule exists to
    # prevent — measured, moving the block out of `prompt` into `instructions`
    # left zero of the twelve in the prompt and the gate still green.
    #
    # Only where a prompt exists: reporting an incomplete policy on a recipe
    # that has none repeats one cause as three findings and buries the one
    # that matters.
    # Both markers count, for every recipe. Narrowing them to
    # `Forbidden by name:` on a read-only recipe was tried and removed as dead
    # logic: measured, the marker choice only changes the answer when a
    # `Permitted by name:` block carries names, and a read-only recipe that
    # has one is already rejected by the check above. The only two recipes
    # where the choice matters are the `-apply` pair, and those take both
    # markers either way.
    #
    # What this therefore does NOT bound is what an `-apply` recipe may
    # declare permitted: one that puts the whole set under `Permitted by name:`
    # passes completeness, measured. Bounding that needs a per-recipe
    # allowance register, which this branch removed deliberately after it
    # produced findings in every round it existed. Tracked in #34.
    # Unconditional, and a filter on "does this recipe reach the server" was
    # tried and withdrawn. It cannot be written from the data this file has:
    # the prefixed form is detectable, the bare form is not without a list of
    # read tools — and such a list is the stale-name defect this whole check
    # exists to catch. Measured, the filter let the case the check exists for
    # walk straight through: a read-only recipe naming `get_plant` and
    # `list_plants` in bare form, carrying no policy block at all, was skipped
    # with all twelve missing.
    #
    # The cost is the other direction: a future recipe that loads only Home
    # Assistant would have to name sixteen kamerplanter tools it never calls.
    # No such recipe exists — all ten reach this server — and when one arrives,
    # the filter belongs on the declared extensions, not on tool names.
    if prompt_text.strip() and missing:
        findings.error(
            where,
            f"declares {len(STATE_CHANGING_TOOLS) - len(missing)} of the "
            f"{len(STATE_CHANGING_TOOLS)} state-changing tools inside a policy "
            f"block in its `prompt`; missing {', '.join(missing)}. Naming a "
            "subset is the failure this rule exists to catch; a name in prose "
            "outside the block is not a prohibition, and a block in "
            "`instructions` is not enforced on a headless run. The block runs "
            "from the marker across name-only lines: a bullet or table cell "
            "that adds prose after a name ends it, and so does a conjunction "
            "before the last name (`` `a`, and `b`. ``). Keep the names "
            "together, unbroken by prose, and put the explanation after the "
            "block.",
        )

    # Home Assistant (#75), for read-only recipes only: the rule is scoped to
    # them (spec/mcp/home-assistant-mcp-server/en.md). An `-apply` recipe is
    # not selected, and what it may do on Home Assistant — CLAUDE.md lets it
    # actuate, and its `description` has to say so — is not checked here.
    # `extensions.yaml` loads the server into every run, so every read-only
    # recipe is selected, not only those that mention it. The category marker
    # and the intent block are read in `prompt` alone, for the reason the
    # sixteen are; a promptless recipe already has its finding. A call is a
    # call wherever it sits, so the outside-policy read covers the whole body,
    # as the write-guard's does.
    if not is_apply:
        if prompt_text.strip():
            if not ha_category_scopes(prompt_text):
                findings.error(
                    where,
                    f"has no `{HA_CATEGORY_MARKER}` marker in its `prompt`. "
                    "The Home Assistant catalog is assembled per instance, so "
                    "a read-only recipe cannot forbid its actuating tools by "
                    "name and has to forbid them by category "
                    "(spec/mcp/home-assistant-mcp-server/en.md). Write the "
                    "marker and name, in the same sentence: "
                    f"{', '.join(HA_CATEGORY_TERMS)}.",
                )
            elif omitted := ha_category_missing(prompt_text):
                findings.error(
                    where,
                    f"its `{HA_CATEGORY_MARKER}` sentence omits "
                    f"{', '.join(omitted)}. A Home Assistant category left "
                    "unnamed is one the per-instance catalog may still offer "
                    "(spec/mcp/home-assistant-mcp-server/en.md). The scope "
                    "ends at the marker's sentence end (`.`, `!` or `?` "
                    "before whitespace — `e.g.` counts), and earlier at a "
                    "blank line, at a list item no deeper than the marker's "
                    "line, or at a prose line indented less than the marker "
                    "line's text; a backticked marker opens none, and each "
                    "category must appear as a whole word.",
                )
            if absent := missing_from_policy(
                prompt_text, READ_ONLY_MARKERS, tools=HA_UNCLASSIFIED_INTENTS
            ):
                findings.error(
                    where,
                    "leaves unclassified Home Assistant intents out of its "
                    f"`Forbidden by name:` block ({', '.join(absent)}). Their "
                    "effect is unclassified, so a read-only recipe forbids "
                    "them by name in `prompt` "
                    "(spec/mcp/home-assistant-mcp-server/en.md); a prose "
                    "prohibition is not a block.",
                )
        if named := calls_state_changing_tools(
            body, is_apply=False, tools=HA_UNCLASSIFIED_INTENTS
        ):
            findings.error(
                where,
                f"calls unclassified Home Assistant intents ({', '.join(named)}) "
                "outside a `Forbidden by name:` block. Under the policy-block "
                "convention a name outside every block is a call, and a "
                "read-only recipe must not call either while their effect is "
                "unclassified (spec/mcp/home-assistant-mcp-server/en.md). Move "
                "the name into the block and keep the explanation out of it.",
            )

    # A recipe that writes a file says so, suffix or not. `-apply` is reserved
    # for backend state, so a report-writing recipe has nothing else to warn
    # with — and a reader who granted the run on the strength of "read-only"
    # finds files in their checkout.
    writes_a_file = re.search(r"(?i)\bwrite[s]?\b[^.\n]{0,60}?`?\.audits/", body)
    if writes_a_file and not re.search(r"(?i)\bwrite", description):
        findings.error(
            where,
            "instructs the run to write a file but its `description` never "
            "says so. The `-apply` suffix is reserved for backend state, so "
            "the description is the only place a reader can learn it.",
        )

    if is_apply and not re.match(r"(?i)\s*writes\b", description.strip()):
        findings.error(
            where,
            "carries the -apply suffix, so its `description` has to open by "
            "stating the effect (\"WRITES to ...\").",
        )

    # Skill discovery is relative to the Goose process's working directory. A
    # recipe run from elsewhere loses the skill without an error and still
    # answers from the prompt alone, so the requirement belongs in the
    # description where `--explain` surfaces it.
    # A skill name that does not resolve is the quietest failure here: the load
    # fails, the run keeps going, and it answers from the prompt alone — which
    # still looks like a plausible answer.
    available = {
        skill.name for skill in SKILLS_DIR.iterdir() if skill.is_dir()
    } if SKILLS_DIR.is_dir() else set()
    referenced = {
        name
        for match in SKILL_REF_PATTERN.finditer(body)
        for name in match.groups()
        if name
    }
    # Not `missing`: that name already holds the completeness result earlier in
    # this same function. Rebinding it here worked only because nothing below
    # reads it — the kind of silence this file exists to remove.
    for unresolved_skill in sorted(referenced - available):
        findings.error(
            where,
            f"names the skill `{unresolved_skill}`, which has no directory "
            "under .claude/skills/. The load fails silently and the run "
            "answers from the prompt alone.",
        )

    loads_skill = any(skill in body for skill in available)
    if loads_skill and "working directory" not in description.lower():
        findings.error(
            where,
            "loads a project skill but does not name the required working "
            "directory in its `description`. Skill discovery is relative to "
            "the Goose process's cwd; a run started elsewhere loses the skill "
            "silently.",
        )

    # Goose's own skill layer is absent under a provider that substitutes the
    # tool set; a recipe calling it fails without a clean error.
    if "load_skill" in body:
        findings.error(
            where,
            "references `load_skill`. Goose's own skill layer is unreachable "
            "under a provider that substitutes the Goose tool set.",
        )

    # sub_recipes registers as a Goose tool, so it disappears in that same
    # substitution — and the run reports a plausible tool name that never ran.
    if "sub_recipes" in recipe:
        findings.error(
            where,
            "declares `sub_recipes:`. The mechanism produces no callable tool "
            "under the claude-code provider; use one process per item instead "
            "(see scripts/analyse-queue.sh).",
        )


def check_extensions(findings: Findings) -> None:
    """Goose expands ${VAR} in an extension only for variables listed in that
    entry's env_keys. Omit one and the literal string goes over the wire as the
    header value, which the server answers with 401 — looking like a bad key."""
    if not EXTENSIONS_FILE.exists():
        findings.error("extensions.yaml", "is missing.")
        return

    config = load_yaml(EXTENSIONS_FILE, findings)
    if not isinstance(config, dict):
        return

    extensions = config.get("extensions")
    if not isinstance(extensions, dict):
        findings.error(
            "extensions.yaml",
            "`extensions:` has to be a MAP keyed by name in a shared config "
            "file (it is a LIST only inside a recipe).",
        )
        return

    for name, entry in extensions.items():
        where = f"extensions.yaml [{name}]"
        if not isinstance(entry, dict):
            findings.error(where, "is not a mapping.")
            continue

        if entry.get("enabled") is not True:
            findings.error(
                where,
                "needs `enabled: true` — entries in a shared config file are "
                "inert without it.",
            )

        declared = set(entry.get("env_keys") or [])
        referenced = set()
        for value in (entry.get("uri"), *(entry.get("headers") or {}).values()):
            if isinstance(value, str):
                referenced.update(VAR_PATTERN.findall(value))

        for undeclared_var in sorted(referenced - declared):
            findings.error(
                where,
                f"references ${{{undeclared_var}}} but does not list it in "
                "`env_keys`. Goose sends the literal string instead of the "
                "value, and the server answers 401 as though the credential "
                "were wrong.",
            )

        for unused in sorted(declared - referenced):
            findings.note(
                f"{where}: lists {unused} in `env_keys` without referencing "
                "it — harmless while it is set, but Goose still resolves it: "
                "an unset variable in `env_keys` aborts every run with "
                "`Configuration value not found` (measured for referenced "
                "variables, 2026-11-05)."
            )

        # A literal credential must never reach a tracked file.
        for header, value in (entry.get("headers") or {}).items():
            if isinstance(value, str) and "${" not in value and value.strip():
                findings.error(
                    where,
                    f"header `{header}` carries a literal value. Credentials "
                    "resolve from the environment, never from a tracked file.",
                )


def check_skills(findings: Findings) -> None:
    """`disable-model-invocation: true` means only a human may invoke the skill
    by slash command — and a recipe run has no human, so the skill is invisible
    to it. Goose's own `skills list` ignores the key and shows it anyway."""
    if not SKILLS_DIR.is_dir():
        return

    for skill_file in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8")
        if not text.startswith("---"):
            findings.error(
                f".claude/skills/{skill_file.parent.name}",
                "SKILL.md has no YAML frontmatter.",
            )
            continue
        frontmatter = load_yaml_frontmatter(text)
        if frontmatter.get("disable-model-invocation") is True:
            findings.error(
                f".claude/skills/{skill_file.parent.name}",
                "carries `disable-model-invocation: true`, which makes it "
                "invisible to every non-interactive recipe run.",
            )
        missing = skill_missing_tools(text)
        if missing:
            findings.error(
                f".claude/skills/{skill_file.parent.name}",
                f"references the Kamerplanter server but names only "
                f"{len(STATE_CHANGING_TOOLS) - len(missing)} of the "
                f"{len(STATE_CHANGING_TOOLS)} state-changing tools; missing "
                f"{', '.join(missing)}. Naming a subset is the failure "
                "spec/mcp/kamerplanter-mcp-server/en.md calls the one this rule "
                "exists to catch, and a skill loaded into a recipe carries its "
                "prohibitions into that run's context.",
            )
        skill = skill_file.parent.name
        calls = skill_unpermitted_calls(text, skill)
        if calls:
            located = ", ".join(f"{tool} (line {number})" for number, tool in calls)
            findings.error(
                f".claude/skills/{skill}",
                f"directs calls to state-changing tools its own `Permitted by "
                f"name:` block does not list: {located}. Under the skill "
                "structure convention (spec/goose/recipe-project-pattern/en.md) "
                "only `## Gotchas` and `## Source` are explanation; everything "
                "else is instruction, and a name there outside a policy block "
                "is a call. Move an explanatory sentence verbatim under "
                "`## Gotchas`, keep a prohibition inside the `Forbidden by "
                "name:` run, or — if the skill really writes — list the tool "
                "under `Permitted by name:` and load it only from `-apply` "
                "recipes.",
            )
        # A skill composes into the recipe's context, so an intent it names in
        # instruction text is a call in every recipe that loads it (#75).
        intents = calls_state_changing_tools(
            skill_instruction_text(text), tools=HA_UNCLASSIFIED_INTENTS
        )
        if intents:
            findings.error(
                f".claude/skills/{skill}",
                f"names unclassified Home Assistant intents ({', '.join(intents)}) "
                "in instruction text outside a policy block, which makes them "
                "calls in every recipe that loads the skill. Their effect is "
                "unclassified (spec/mcp/home-assistant-mcp-server/en.md): keep "
                "them inside a `Forbidden by name:` run, or move an "
                "explanatory sentence verbatim under `## Gotchas`.",
            )
        for allowed in stale_skill_allowances(text, skill):
            findings.error(
                f".claude/skills/{skill}",
                f"has a line allowance in SKILL_LINE_ALLOWANCES for {allowed!r}, "
                "but that exact line does not occur exactly once. Remove or "
                "update the entry: absent, it would hold whatever line takes "
                "that text next; duplicated, it holds a copy nobody reviewed.",
            )

    present = {path.parent.name for path in SKILLS_DIR.glob("*/SKILL.md")}
    for skill, allowed in sorted(SKILL_LINE_ALLOWANCES):
        if skill not in present:
            findings.error(
                f".claude/skills/{skill}",
                f"is named by a line allowance ({allowed!r}) but has no "
                "SKILL.md. Remove the stale entry.",
            )


def check_agents(findings: Findings) -> None:
    """A project agent is dispatchable only from `.claude/agents/`, relative to
    the Goose process's working directory. `.agents/agents/` — the location
    Goose's own documentation recommends — is not in the registry a run sees,
    and the failure is a plain "not found" against a list that looks complete."""
    for agent_file in sorted(AGENTS_DIR.glob("*.md")) if AGENTS_DIR.is_dir() else []:
        frontmatter = load_yaml_frontmatter(agent_file.read_text(encoding="utf-8"))
        where = f".claude/agents/{agent_file.name}"
        if not frontmatter:
            findings.error(where, "has no parseable YAML frontmatter.")
            continue
        for key in ("name", "description"):
            if not str(frontmatter.get(key) or "").strip():
                findings.error(where, f"has no `{key}` in its frontmatter.")
        if frontmatter.get("name") not in (None, agent_file.stem):
            findings.error(
                where,
                f"declares name `{frontmatter['name']}` but is filed as "
                f"`{agent_file.stem}`; dispatch uses the registered name.",
            )

    if not UNREACHABLE_AGENTS_DIR.is_dir():
        return
    for agent_file in sorted(UNREACHABLE_AGENTS_DIR.glob("*.md")):
        if agent_file.stem in UNREACHABLE_AGENTS_ALLOWED:
            findings.note(
                f".agents/agents/{agent_file.name}: kept deliberately — it is the "
                "probe that measures this directory's unreachability."
            )
            continue
        findings.error(
            f".agents/agents/{agent_file.name}",
            "is in the directory Goose's documentation recommends and the "
            "claude-code provider cannot see. Move it to .claude/agents/.",
        )


def load_yaml_frontmatter(text: str) -> dict:
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def run_goose_validate(findings: Findings) -> None:
    """Schema validation, when the binary is available. Skipped otherwise so CI
    does not depend on a Goose install."""
    if shutil.which("goose") is None:
        findings.note("`goose` not on PATH — schema validation skipped.")
        return

    for path in sorted(RECIPES_DIR.glob("*.yaml")):
        result = subprocess.run(
            ["goose", "recipe", "validate", str(path)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        if result.returncode != 0:
            output = (result.stderr or result.stdout).strip()
            findings.error(f"recipes/{path.name}", f"goose validate — {output}")


# Every shape the write-guard is known to get right. It is the only check here
# whose failure is silent — a broken guard reports OK — and it has already died
# twice unnoticed: once because `\b<tool>\b` cannot match `mcp__server__<tool>`,
# once because any prohibition anywhere exempted the whole recipe. Add the shape
# before changing the heuristic.
# One case per shape a review round actually turned up. They pin the
# convention, not a parser: every entry is a policy block or a call, and none
# of them depends on how the surrounding English reads.
CLASSIFIER_CASES = [
    (
        "both marker keys make a write, neither a read",
        {"get_plant": ["plant_key", "tenant"], "archive_plant": ["dry_run", "idempotency_key", "plant_key"]},
        ["archive_plant"],
        [],
    ),
    (
        "one marker key alone is refused, not guessed",
        {"new_tool": ["dry_run", "plant_key"], "other": ["idempotency_key"]},
        [],
        ["new_tool", "other"],
    ),
]


WRITE_GUARD_CASES = [
    (
        "names inside the block are policy",
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`,\n"
        "    `mcp__kamerplanter__create_site`.",
        [],
    ),
    (
        "a name after the block is a call",
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`.\n"
        "  - Then call `mcp__kamerplanter__create_site`.",
        ["create_site"],
    ),
    (
        "a complete forbidden list does not license a call",
        "  - Call NO tool that changes state.\n"
        "    Forbidden by name:\n"
        "    " + ", ".join(f"`mcp__kamerplanter__{t}`" for t in sorted(STATE_CHANGING_TOOLS)) + ".\n"
        "\n"
        "  Step 3 - call `mcp__kamerplanter__archive_plant`.",
        ["archive_plant"],
    ),
    (
        "prose ends the block, and a name after it is a call",
        "  - Forbidden by name:\n"
        "    `mcp__kamerplanter__archive_plant`.\n"
        "    The servers are loaded anyway. Then call "
        "`mcp__kamerplanter__create_site`.",
        ["create_site"],
    ),
    (
        "a bullet of bare names after a complete marker line is a call",
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`.\n"
        "  - `mcp__kamerplanter__create_site`, `mcp__kamerplanter__set_plant_location`",
        ["create_site", "set_plant_location"],
    ),
    (
        "a table separator does not hold the block open",
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`.\n"
        "  |---|---|\n"
        "  `mcp__kamerplanter__create_site`",
        ["create_site"],
    ),
    (
        "a nested name list stays inside the block",
        "  - Forbidden by name:\n"
        "    - `mcp__kamerplanter__archive_plant`\n"
        "    - `mcp__kamerplanter__create_site`",
        [],
    ),
    (
        "a wrapped list stays inside the block",
        "  - Forbidden by name: `mcp__kamerplanter__confirm_care_task`,\n"
        "    `mcp__kamerplanter__archive_plant`,\n"
        "    `mcp__kamerplanter__submit_diary_analysis`.",
        [],
    ),
    (
        "a second block of the same marker is policy too",
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`.\n"
        "  - Forbidden by name: `mcp__kamerplanter__create_site`.",
        [],
    ),
    (
        "the permitted block is policy too",
        "  - Permitted by name: `mcp__kamerplanter__claim_diary_analysis`.\n"
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`.",
        [],
    ),
    (
        "a nested block does not free the outer one",
        "  - Permitted by name: `mcp__kamerplanter__claim_diary_analysis`.\n"
        "    Forbidden by name: `mcp__kamerplanter__archive_plant`.",
        [],
    ),
    (
        "no marker means every name is a call",
        "Call `mcp__kamerplanter__archive_plant` and `create_site`.",
        ["archive_plant", "create_site"],
    ),
    (
        "bare and prefixed forms both count",
        "  - Forbidden by name: `archive_plant`, `mcp__kamerplanter__create_site`.",
        [],
    ),
    (
        "a call after the names on the marker line",
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`; call "
        "`mcp__kamerplanter__add_plant_diary_entry` instead.",
        ["add_plant_diary_entry"],
    ),
    (
        "prose then a call, still on the marker line",
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`, "
        "`mcp__kamerplanter__create_site` — and anything else. Then call "
        "`mcp__kamerplanter__set_plant_location`.",
        ["set_plant_location"],
    ),
    (
        "a sibling bullet ends a nested list too",
        "- Forbidden by name:\n"
        "  - `mcp__kamerplanter__archive_plant`\n"
        "- `mcp__kamerplanter__create_site`",
        ["create_site"],
    ),
    (
        "a punctuation-only line does not hold the block open",
        "- Forbidden by name: `mcp__kamerplanter__archive_plant`.\n"
        "---\n"
        "`mcp__kamerplanter__create_site`",
        ["create_site"],
    ),
    (
        "substring is not a match",
        "unarchive_plantx and archive_plants",
        [],
    ),
    (
        "a table row carrying names ends the block",
        "- Forbidden by name:\n"
        "| `mcp__kamerplanter__archive_plant` | `mcp__kamerplanter__create_site` |",
        ["archive_plant", "create_site"],
    ),
    (
        "an indented table row ends it too",
        "  - Forbidden by name:\n"
        "    | `mcp__kamerplanter__archive_plant` | "
        "`mcp__kamerplanter__create_site` |",
        ["archive_plant", "create_site"],
    ),
    (
        "an indented sibling bullet ends the nested list",
        "  - Forbidden by name:\n"
        "    - `mcp__kamerplanter__archive_plant`\n"
        "  - `mcp__kamerplanter__create_site`",
        ["create_site"],
    ),
    (
        "trailing whitespace does not deepen a sibling bullet",
        "  - Forbidden by name:\n"
        "    - `mcp__kamerplanter__archive_plant`\n"
        "  - `mcp__kamerplanter__create_site`   ",
        ["create_site"],
    ),
    (
        "asterisk bullets nest like dashes",
        "  * Forbidden by name:\n"
        "    * `mcp__kamerplanter__archive_plant`\n"
        "  * `mcp__kamerplanter__create_site`",
        ["create_site"],
    ),
    (
        "a one-space nested list still stays inside the block",
        "- Forbidden by name:\n"
        " - `mcp__kamerplanter__archive_plant`\n"
        " - `mcp__kamerplanter__create_site`",
        [],
    ),
    (
        "a deeper bullet after a marker line that already has names is a call",
        "- Forbidden by name: `mcp__kamerplanter__archive_plant`\n"
        "  - `mcp__kamerplanter__create_site`",
        ["create_site"],
    ),
    (
        "the left word boundary counts too",
        "x_archive_plant, 9archive_plant and unarchive_plant",
        [],
    ),
    (
        "a sentence after the block does not extend it",
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`. "
        "`mcp__kamerplanter__create_site` is called at step 4.",
        ["create_site"],
    ),
    # #78: a marker quoted as code is a mention and opens no block, so the
    # names after it stay calls.
    (
        "a backticked marker does not hide the call on the next line",
        "  - Quote the marker `Forbidden by name:`\n"
        "    `mcp__kamerplanter__archive_plant`",
        ["archive_plant"],
    ),
    (
        "a marker inside a double-backtick span opens no block",
        "  - Write ``Forbidden by name:``\n"
        "    `mcp__kamerplanter__archive_plant`",
        ["archive_plant"],
    ),
    (
        "a marker inside a fenced example opens no block",
        "  ```\n"
        "  Forbidden by name:\n"
        "  ```\n"
        "  `mcp__kamerplanter__archive_plant`",
        ["archive_plant"],
    ),
    (
        # As in CommonMark, the stray backtick pairs with the next single one
        # in the paragraph — before a policy marker that is always the first
        # name's — so the marker sits in code. The safe direction: the name
        # reads as a call, and the recipe fails instead of passing.
        "a stray backtick pairs with the next run in the paragraph",
        "  - Don`t call these. Forbidden by name:\n"
        "    `mcp__kamerplanter__archive_plant`.",
        ["archive_plant"],
    ),
]


# The completeness guard has its own shapes, because it answers a different
# question than the write-guard above and shares none of its marker logic.
ALL_SIXTEEN = ", ".join(f"`mcp__kamerplanter__{t}`" for t in sorted(STATE_CHANGING_TOOLS))

COMPLETENESS_CASES = [
    (
        "a complete list inside the block is complete",
        f"  - Call NO tool that changes state. Forbidden by name: {ALL_SIXTEEN}.",
        [],
    ),
    (
        "prose naming all sixteen declares nothing — no block, no policy",
        f"Never call {ALL_SIXTEEN}. This recipe reads and judges.",
        sorted(STATE_CHANGING_TOOLS),
    ),
    (
        "a name moved out of the block into prose stops counting",
        "  - Forbidden by name: "
        + ", ".join(
            f"`mcp__kamerplanter__{t}`"
            for t in sorted(STATE_CHANGING_TOOLS - {"create_inspection"})
        )
        + ".\n\nFor background the server also offers "
        "`mcp__kamerplanter__create_inspection`.",
        ["create_inspection"],
    ),
    (
        "the catalog's seven-name era is a subset today",
        "- Call no tool that changes state. Forbidden by name: "
        "`mcp__kamerplanter__confirm_care_task`, "
        "`mcp__kamerplanter__archive_plant`, "
        "`mcp__kamerplanter__set_plant_location`, "
        "`mcp__kamerplanter__create_site`, "
        "`mcp__kamerplanter__add_plant_diary_entry`, "
        "`mcp__kamerplanter__claim_diary_analysis`, "
        "`mcp__kamerplanter__submit_diary_analysis`.",
        sorted(
            STATE_CHANGING_TOOLS
            - {
                "confirm_care_task",
                "archive_plant",
                "set_plant_location",
                "create_site",
                "add_plant_diary_entry",
                "claim_diary_analysis",
                "submit_diary_analysis",
            }
        ),
    ),
    (
        "a permitted/forbidden split is complete as a union",
        "  - Permitted by name: `mcp__kamerplanter__claim_diary_analysis`, "
        "`mcp__kamerplanter__submit_diary_analysis`.\n"
        "  - Forbidden by name: "
        + ", ".join(
            f"`mcp__kamerplanter__{t}`"
            for t in sorted(
                STATE_CHANGING_TOOLS
                - {"claim_diary_analysis", "submit_diary_analysis"}
            )
        )
        + ".",
        [],
    ),
    (
        "a category is not a name",
        "  - Call no state-changing tool, and nothing else that writes.",
        sorted(STATE_CHANGING_TOOLS),
    ),
    (
        # Accepted as a false negative until #84; `code_spans` closes it.
        "a fenced example does not count as declared",
        "This recipe declares no policy of its own. It prints the template:\n"
        "```\n"
        f"Forbidden by name: {ALL_SIXTEEN}.\n"
        "```\n",
        sorted(STATE_CHANGING_TOOLS),
    ),
    (
        "a conjunction before the last name leaves it outside the block",
        "  - Forbidden by name: "
        + ", ".join(
            f"`mcp__kamerplanter__{t}`"
            for t in sorted(STATE_CHANGING_TOOLS - {"transition_plant_phase"})
        )
        + ", and `mcp__kamerplanter__transition_plant_phase`.",
        ["transition_plant_phase"],
    ),
    (
        "the bare name counts, not only the mcp__ form",
        "Forbidden by name: "
        + ", ".join(f"`{t}`" for t in sorted(STATE_CHANGING_TOOLS))
        + ".",
        [],
    ),
]


# Both lists above exercise a helper directly, and neither can reach what
# `check_recipe` decides on its own: which findings fire together, and which
# repair each one advises. That gap was not theoretical — a review restored the
# suppression this file had just removed, and every case above still held with
# the gate green. These cases run the real check against a synthetic recipe.
RECIPE_TEMPLATE = """\
version: "1.0.0"
title: "Self-test case"
description: >-
  Read-only: a synthetic recipe the self-test writes to a temporary directory.
instructions: |
{instructions}
"""

# Appended only when the case carries a prompt: a case that omits it is how the
# promptless path gets exercised at all.
PROMPT_FIELD = "prompt: |\n{prompt}\n"

PLAIN_INSTRUCTIONS = "Synthetic."
PLAIN_PROMPT = "Assess the plant and report. Load no skill."

REAL_CALL = "\n  Step 5 - then call `mcp__kamerplanter__archive_plant` for real.\n"

COMPLETE_BLOCK = (
    "  - Call NO tool that changes state.\n    Forbidden by name:\n    "
    + ALL_SIXTEEN
    + "."
)

# One annotated bullet per tool: the block ends at the marker, so every name in
# it lands outside policy and reads as a call.
COLLAPSED_BLOCK = (
    "  - Call NO tool that changes state. Forbidden by name:\n"
) + "".join(
    f"    - `mcp__kamerplanter__{tool}` - never; this recipe only reads.\n"
    for tool in sorted(STATE_CHANGING_TOOLS)
)

FIFTEEN_OF_SIXTEEN = (
    "  - Call NO tool that changes state.\n    Forbidden by name:\n    "
    + ", ".join(
        f"`mcp__kamerplanter__{tool}`"
        for tool in sorted(STATE_CHANGING_TOOLS - {"confirm_care_task"})
    )
    + "."
)

# The skill check answers the same question as COMPLETENESS_CASES but selects
# differently and reads the whole file: a name anywhere counts, inside or
# outside a policy block, in instruction or explanation. Which of those names
# are calls is SKILL_OBEDIENCE_CASES' question. One shape per way the selector
# or the count can be wrong.
SKILL_COMPLETENESS_CASES = [
    (
        "a skill naming all sixteen is complete",
        "Reads a garden through `mcp__kamerplanter__get_plant`.\n"
        f"Never call {ALL_SIXTEEN}.",
        [],
    ),
    (
        "the seven-name era is a subset today",
        "Reads a garden through `mcp__kamerplanter__get_plant`.\n"
        "Never call "
        + ", ".join(
            f"`mcp__kamerplanter__{t}`"
            for t in sorted(STATE_CHANGING_TOOLS)[:7]
        )
        + ".",
        sorted(STATE_CHANGING_TOOLS)[7:],
    ),
    (
        "a skill that reaches the server and names no write is the worst subset",
        "Reads the photos through `mcp__kamerplanter__get_diary_entry_photos`.",
        sorted(STATE_CHANGING_TOOLS),
    ),
    (
        "a skill that never reaches the server is not selected",
        "Reviews a recipe in this checkout as a casual owner of three plants.",
        [],
    ),
    (
        "naming the tools without the server prefix does not select the skill",
        "Never call " + ", ".join(f"`{t}`" for t in sorted(STATE_CHANGING_TOOLS)[:3]) + ".",
        [],
    ),
    (
        "bare names count once the skill is selected",
        "Reads a garden through `mcp__kamerplanter__get_plant`.\n"
        "Never call " + ", ".join(f"`{t}`" for t in sorted(STATE_CHANGING_TOOLS)) + ".",
        [],
    ),
    (
        "a name that is called still counts as named",
        "Reads a garden through `mcp__kamerplanter__get_plant`.\n"
        f"Never call {ALL_SIXTEEN}.\nStep 9 - call `mcp__kamerplanter__archive_plant`.",
        [],
    ),
]


ALLOWED_PLANT_PLANNING_LINE = next(
    line for skill, line in SKILL_LINE_ALLOWANCES if skill == "plant-planning"
)

SKILL_FORBID_ALL = "- Call no tool that changes state. Forbidden by name: " + ALL_SIXTEEN + "."

# One shape per way the skill obedience guard can misread a section. Each case
# is (name, skill directory name, SKILL.md text, expected calls, expected stale
# allowed lines). The guard reads by heading, so every case is a heading
# layout; none depends on how a sentence reads.
SKILL_OBEDIENCE_CASES = [
    (
        "a call in a procedure is a call",
        "selftest-skill",
        "## Procedure\n\n1. Then call `mcp__kamerplanter__archive_plant`.\n",
        ["archive_plant"],
        [],
    ),
    (
        "the same name under Gotchas is explanation",
        "selftest-skill",
        "## Procedure\n\n1. Read.\n\n## Gotchas\n\n"
        "- `mcp__kamerplanter__archive_plant` is the write a tidy-up reaches for.\n",
        [],
        [],
    ),
    (
        "the same name under Source is explanation",
        "selftest-skill",
        "## Procedure\n\n1. Read.\n\n## Source\n\n"
        "Measured while `archive_plant` was being called on another instance.\n",
        [],
        [],
    ),
    (
        "a name inside the forbidden block under Hard rules is policy",
        "selftest-skill",
        "## Hard rules\n\n" + SKILL_FORBID_ALL + "\n",
        [],
        [],
    ),
    (
        "prose after the forbidden run that names a tool is a call",
        "selftest-skill",
        "## Hard rules\n\n" + SKILL_FORBID_ALL
        + " `create_inspection` is the write an IPM path reaches for first.\n",
        ["create_inspection"],
        [],
    ),
    (
        "an unknown heading is instruction",
        "selftest-skill",
        "## Background\n\nThe server offers `mcp__kamerplanter__create_site`.\n",
        ["create_site"],
        [],
    ),
    (
        "a level-3 Gotchas nested in a procedure is instruction",
        "selftest-skill",
        "## Procedure\n\n### Gotchas\n\n- Call `mcp__kamerplanter__archive_plant`.\n",
        ["archive_plant"],
        [],
    ),
    (
        "a procedure after Gotchas is instruction again",
        "selftest-skill",
        "## Gotchas\n\n- `archive_plant` is dangerous.\n\n## Procedure\n\n"
        "1. Call `mcp__kamerplanter__archive_plant`.\n",
        ["archive_plant"],
        [],
    ),
    (
        "a Gotchas line inside a fence opens no explanation section",
        "selftest-skill",
        "## Procedure\n\n```\n## Gotchas\n```\n\n"
        "1. Call `mcp__kamerplanter__archive_plant`.\n",
        ["archive_plant"],
        [],
    ),
    (
        "a skill calls what its own permitted block lists, and nothing else",
        "selftest-skill",
        "## Procedure\n\n1. Call `mcp__kamerplanter__claim_diary_analysis`.\n"
        "2. Call `mcp__kamerplanter__archive_plant`.\n\n## Hard rules\n\n"
        "- Permitted by name: `mcp__kamerplanter__claim_diary_analysis`.\n",
        ["archive_plant"],
        [],
    ),
    (
        "a bare name in a skill that never names the server prefix is a call",
        "selftest-skill",
        "## Procedure\n\n1. Tidy up with `archive_plant`.\n",
        ["archive_plant"],
        [],
    ),
    (
        "frontmatter and text before the first heading are instruction",
        "selftest-skill",
        "---\nname: selftest-skill\ndescription: Calls create_site.\n---\n\n"
        "Then call `transition_plant_phase`.\n\n## Gotchas\n\n- Nothing.\n",
        ["create_site", "transition_plant_phase"],
        [],
    ),
    (
        "an allowlisted plant-planning line is held, the same names elsewhere are not",
        "plant-planning",
        "## Procedure\n\n```\n  " + ALLOWED_PLANT_PLANNING_LINE + "\n```\n\n"
        "2. Then call create_site.\n",
        ["create_site"],
        [],
    ),
    (
        "an allowance whose line is gone is stale",
        "plant-planning",
        "## Procedure\n\n1. Read the garden.\n",
        [],
        [ALLOWED_PLANT_PLANNING_LINE],
    ),
    (
        "a new line sharing the allowance's opening words is not held",
        "plant-planning",
        "## Procedure\n\n```\n  " + ALLOWED_PLANT_PLANNING_LINE + "\n```\n\n"
        "The measured catalog has no tool that creates a planting run, so first "
        "call `mcp__kamerplanter__create_site` and `archive_plant`.\n\n## Hard rules\n",
        ["archive_plant", "create_site"],
        [],
    ),
    (
        "the allowed line rewritten to carry a call is not held, and the entry is stale",
        "plant-planning",
        "## Procedure\n\n```\n  The measured catalog has no tool that creates a "
        "planting run. Call create_site now.\n```\n",
        ["create_site"],
        [ALLOWED_PLANT_PLANNING_LINE],
    ),
    (
        "the allowed line twice is stale and neither copy is held",
        "plant-planning",
        "## Procedure\n\n" + ALLOWED_PLANT_PLANNING_LINE + "\n\n"
        + ALLOWED_PLANT_PLANNING_LINE + "\n",
        sorted(
            t for t in STATE_CHANGING_TOOLS
            if tool_pattern(t).search(ALLOWED_PLANT_PLANNING_LINE)
        ),
        [ALLOWED_PLANT_PLANNING_LINE],
    ),
    (
        "a setext heading ends a Gotchas section",
        "selftest-skill",
        "## Gotchas\n\nx\n\nProcedure\n=========\n\n"
        "Call `mcp__kamerplanter__archive_plant`.\n",
        ["archive_plant"],
        [],
    ),
    (
        "a dash setext heading ends a Gotchas section too",
        "selftest-skill",
        "## Gotchas\n\nx\n\nProcedure\n---\n\n"
        "Call `mcp__kamerplanter__archive_plant`.\n",
        ["archive_plant"],
        [],
    ),
    (
        "a fence line with trailing text does not close the fence",
        "selftest-skill",
        "## Procedure\n\n```\n``` not a closer\n## Gotchas\n```\n\n"
        "Call `mcp__kamerplanter__archive_plant`.\n",
        ["archive_plant"],
        [],
    ),
    (
        "a shorter fence line does not close a longer fence",
        "selftest-skill",
        "## Procedure\n\n````\n```\n## Gotchas\n````\n\n"
        "Call `mcp__kamerplanter__archive_plant`.\n",
        ["archive_plant"],
        [],
    ),
    (
        "a Gotchas heading inside an HTML comment opens no explanation section",
        "selftest-skill",
        "## Procedure\n\n<!--\n## Gotchas\n-->\n\n"
        "Call `mcp__kamerplanter__archive_plant`.\n",
        ["archive_plant"],
        [],
    ),
    (
        "CRLF line endings parse like LF",
        "selftest-skill",
        "## Procedure\r\n\r\n1. Read.\r\n\r\n## Gotchas\r\n\r\n"
        "- `archive_plant` is the write a tidy-up reaches for.\r\n",
        [],
        [],
    ),
]


PERMITTING_SKILL = (
    "## Hard rules\n\n- Permitted by name: "
    "`mcp__kamerplanter__claim_diary_analysis`.\n"
)
READING_SKILL = "## Hard rules\n\n" + SKILL_FORBID_ALL + "\n"

# One shape per way the `Permitted`-loader bound can be wrong: (name, recipes
# as {filename: (is_apply, body)}, skills as {name: SKILL.md}, expected loads).
PERMITTING_LOAD_CASES = [
    (
        "a permitting skill loaded by an -apply recipe passes",
        {"claim-apply.yaml": (True, "Load the skill `claimer`.")},
        {"claimer": PERMITTING_SKILL},
        [],
    ),
    (
        "the same skill loaded by a read-only recipe fails",
        {"claim-check.yaml": (False, "Load the skill `claimer`.")},
        {"claimer": PERMITTING_SKILL},
        [("claim-check.yaml", "claimer")],
    ),
    (
        "a skill without a permitted block loaded by a read-only recipe passes",
        {"read-check.yaml": (False, "Load the skill `reader`.")},
        {"reader": READING_SKILL},
        [],
    ),
    (
        "a permitting skill reached through another skill fails too",
        {"read-check.yaml": (False, "Load the skill `reader`.")},
        {
            "reader": READING_SKILL + "\nThen follow the `claimer` skill.\n",
            "claimer": PERMITTING_SKILL,
        },
        [("read-check.yaml", "claimer")],
    ),
    (
        "a skill mentioning a permitting skill only under Gotchas creates no load",
        {"read-check.yaml": (False, "Load the skill `reader`.")},
        {
            "reader": READING_SKILL + "\n## Gotchas\n\n- The claim tools belong to "
            "`claimer`; this skill hands back to it.\n",
            "claimer": PERMITTING_SKILL,
        },
        [],
    ),
    (
        "a skill naming a permitting skill in its procedure loads it",
        {"read-check.yaml": (False, "Load the skill `reader`.")},
        {
            "reader": "## Procedure\n\n1. Hand the entry to `claimer`.\n\n"
            + READING_SKILL,
            "claimer": PERMITTING_SKILL,
        },
        [("read-check.yaml", "claimer")],
    ),
] + [
    (
        f"a read-only recipe naming the skill as {body!r} loads it",
        {"read-check.yaml": (False, body)},
        {"reader": READING_SKILL, "claimer": PERMITTING_SKILL},
        [("read-check.yaml", "claimer")],
    )
    for body in (
        "Load the skills `reader` and `claimer`.",
        "Load the skills `reader`, `claimer`.",
        "Follow `claimer`.",
        "Use the claimer skill.",
        "Load the Skill `claimer`.",
    )
] + [
    (
        "a longer name that contains the skill name is not a load",
        {"read-check.yaml": (False, "Load the skill `claimer-legacy`; see reclaimers.")},
        {"claimer": PERMITTING_SKILL},
        [],
    ),
    # #84: a permitted Home Assistant intent is a write for this bound too.
    (
        "a skill permitting the Home Assistant intents fails a read-only load",
        {"read-check.yaml": (False, "Load the skill `timer`.")},
        {"timer": "## Hard rules\n\n- Permitted by name: `TimeTillErnte`, `time_till`.\n"},
        [("read-check.yaml", "timer")],
    ),
    (
        "the same skill loaded by an -apply recipe passes",
        {"timer-apply.yaml": (True, "Load the skill `timer`.")},
        {"timer": "## Hard rules\n\n- Permitted by name: `TimeTillErnte`, `time_till`.\n"},
        [],
    ),
    # #84 review: here a block found is the failure, so code is no mention.
    (
        "a permitted block in a fence under Gotchas still fails a read-only load",
        {"read-check.yaml": (False, "Load the skill `quoter`.")},
        {
            "quoter": "# s\n\n## Steps\n\nRead only.\n\n## Gotchas\n\n```\n"
            "Permitted by name: `mcp__kamerplanter__archive_plant`.\n```\n"
        },
        [("read-check.yaml", "quoter")],
    ),
    (
        "a stray backtick before a heading does not hide the next section's block",
        {"read-check.yaml": (False, "Load the skill `quoter`.")},
        {
            "quoter": "# s\n\n## Gotchas\n\nDon`t trust the cache.\n## Steps\n"
            "- Permitted by name: `mcp__kamerplanter__archive_plant`.\n"
            "- Call `mcp__kamerplanter__archive_plant`.\n"
        },
        [("read-check.yaml", "quoter")],
    ),
]


# A read-only recipe splitting the set across both markers. Completeness reads
# the union and is satisfied; the write-guard, at `is_apply=False`, counts the
# permitted name as a call. That asymmetry is the whole point of the marker
# choice in `calls_state_changing_tools`, and nothing else measures it.
PERMITTED_SPLIT = (
    "  - Permitted by name: `mcp__kamerplanter__claim_diary_analysis`.\n"
    "  - Call NO other tool that changes state.\n    Forbidden by name:\n    "
    + ", ".join(
        f"`mcp__kamerplanter__{tool}`"
        for tool in sorted(STATE_CHANGING_TOOLS - {"claim_diary_analysis"})
    )
    + "."
)

# One shape per way the Home Assistant category scope can be bounded wrong:
# (name, prompt, expected scope count, expected missing terms). The count
# pins "no marker" apart from "marker with nothing after it", which
# `ha_category_missing` alone cannot tell apart.
HA_CATEGORY_CASES = [
    (
        "no marker is no scope, and every category is missing",
        "  - Call NO Home Assistant tool. Do not turn anything on or off, set a\n"
        "    value, or run a script, scene, or automation.",
        0,
        sorted(HA_CATEGORY_TERMS),
    ),
    (
        "a marker naming every category on its line is complete",
        "  - Forbidden on Home Assistant: on or off, value, script, scene, automation.",
        1,
        [],
    ),
    (
        "continuation lines belong to the sentence",
        "  - Forbidden on Home Assistant: any tool that turns something on or off,\n"
        "    sets a value, or runs a script, scene, or automation.",
        1,
        [],
    ),
    (
        "the categories match case-insensitively",
        "  - Forbidden on Home Assistant: turning ON OR OFF, a Value, a Script, a\n"
        "    Scene, an Automation.",
        1,
        [],
    ),
    # At column 0, so the blank line is the only cut: under an indented marker
    # an empty line is also a dedent and the row would not isolate this rule.
    (
        "a blank line ends an unterminated scope",
        "Forbidden on Home Assistant: turning on or off, setting a value\n"
        "\n"
        "nor run a script, scene, or automation.",
        1,
        ["automation", "scene", "script"],
    ),
    (
        "a sibling bullet ends an unterminated scope",
        "  - Forbidden on Home Assistant: turning on or off, setting a value\n"
        "  - Do not run a script, scene, or automation.",
        1,
        ["automation", "scene", "script"],
    ),
    (
        "a deeper bullet continues the scope",
        "  - Forbidden on Home Assistant:\n"
        "    - turning something on or off\n"
        "    - setting a value\n"
        "    - running a script, scene, or automation",
        1,
        [],
    ),
    # connectivity-check's shape: the marker opens a continuation line of a
    # bullet, so the next bullet sits shallower than the marker's line.
    (
        "a shallower bullet after a continuation-line marker ends the scope",
        "  - Call NO tool that changes state.\n"
        "    Forbidden on Home Assistant: any tool that turns something on or off,\n"
        "    sets a value, or runs a script or scene\n"
        "  - Never trigger an automation.",
        1,
        ["automation"],
    ),
    # Prompts are hard-wrapped, so a two-word category breaks across a line as
    # often as not; whitespace runs are collapsed before the match.
    (
        "a category wrapped across lines still counts",
        "  - Forbidden on Home Assistant: any tool that turns something on or\n"
        "    off, sets a value, or runs a script, scene, or automation.",
        1,
        [],
    ),
    (
        "categories before the marker on its line do not count",
        "  - No script, scene, or automation. Forbidden on Home Assistant: on or\n"
        "    off, value.",
        1,
        ["automation", "scene", "script"],
    ),
    (
        "two markers split the categories between them",
        "  - Forbidden on Home Assistant: turning on or off, setting a value.\n"
        "  - Forbidden on Home Assistant: running a script, scene, or automation.",
        2,
        [],
    ),
    (
        "a marker with nothing after it is a scope missing every category",
        "  - Forbidden on Home Assistant:\n"
        "  - Call no Kamerplanter write.",
        1,
        sorted(HA_CATEGORY_TERMS),
    ),
    # #77: a prose line back at the bullet's own indent is the next element,
    # not a continuation. Before the dedent rule this read as complete. No
    # period, so the dedent cut is the one tested, not the sentence end.
    (
        "a prose line dedented below the bullet's text ends the scope",
        "  - Forbidden on Home Assistant: turning anything on or off\n"
        "  Step 1 — Read the value of each script, scene and automation.\n",
        1,
        ["automation", "scene", "script", "value"],
    ),
    # provider-surface-check's shape: the marker opens a plain prose line, so
    # its continuation sits at the marker's own indent and must still count.
    (
        "a plain marker line continues at its own indent",
        "  Forbidden on Home Assistant: any tool that turns something on or off, sets a\n"
        "  value, or runs a script, scene, or automation.",
        1,
        [],
    ),
    (
        "a prose line dedented below a plain marker line ends the scope",
        "    Forbidden on Home Assistant: turning anything on or off, setting a value\n"
        "  Run a script, scene, or automation.",
        1,
        ["automation", "scene", "script"],
    ),
    (
        "a prose line dedented below nested bullets ends the scope",
        "  - Forbidden on Home Assistant:\n"
        "    - turning something on or off\n"
        "    - setting a value\n"
        "  Run a script, scene, or automation.",
        1,
        ["automation", "scene", "script"],
    ),
    (
        "a nested bullet's own continuation line continues the scope",
        "  - Forbidden on Home Assistant:\n"
        "    - turning something on or off, or setting a\n"
        "      value\n"
        "    - running a script, scene, or automation",
        1,
        [],
    ),
    # #77: a marker quoted as code is a mention of the rule, not the rule.
    (
        "a backticked marker opens no scope",
        "  - Report whether the `Forbidden on Home Assistant:` rule covers on or off,\n"
        "    value, script, scene and automation.",
        0,
        sorted(HA_CATEGORY_TERMS),
    ),
    (
        "a bare marker after a backticked one on the same line still opens",
        "  - The `Forbidden on Home Assistant:` rule. Forbidden on Home Assistant:\n"
        "    on or off, value, script, scene, automation.",
        1,
        [],
    ),
    # #77: the categories are words, not substrings. A plural `s` is allowed.
    (
        "plural category words count",
        "  - Forbidden on Home Assistant: turning things on or off, setting values,\n"
        "    running scripts, scenes, or automations.",
        1,
        [],
    ),
    (
        "a category inside a longer word does not count",
        "  - Forbidden on Home Assistant: a button or offset, devalued data, the\n"
        "    scenery, a transcript, any automationist.",
        1,
        sorted(HA_CATEGORY_TERMS),
    ),
    (
        "Evaluate does not name the value category",
        "  - Forbidden on Home Assistant: Evaluate nothing; turning on or off, a\n"
        "    script, scene, or automation.",
        1,
        ["value"],
    ),
    # Pre-merge review R1: a numbered list is a list. The next item is the
    # next step, not the marker's continuation.
    (
        "a numbered next item ends the scope",
        "1. Forbidden on Home Assistant: turning anything on or off.\n"
        "2. Read the value of each script, scene and automation.",
        1,
        ["automation", "scene", "script", "value"],
    ),
    # Pre-merge review R2: a plain marker line followed by plain prose at the
    # same indent. No structural boundary separates them; the sentence does.
    (
        "a sentence end ends a plain marker line's scope",
        "Forbidden on Home Assistant: turning on or off.\n"
        "Step 2: read value, script, scene, automation.",
        1,
        ["automation", "scene", "script", "value"],
    ),
    # The text column of a numbered marker line is past `1. `, so prose back
    # at the number's indent is the next element. (A following `2. ` item
    # needs no list rule: its period before a space is already a sentence end.)
    (
        "a prose line dedented below a numbered marker's text ends the scope",
        "1. Forbidden on Home Assistant: turning anything on or off\n"
        "Read the value of each script, scene and automation.",
        1,
        ["automation", "scene", "script", "value"],
    ),
    (
        "a parenthesised number and a plus bullet are list items too",
        "  1) Forbidden on Home Assistant: turning anything on or off\n"
        "  2) Read the value of each script\n"
        "  + Forbidden on Home Assistant: setting a value\n"
        "  + Read each scene and automation.",
        2,
        ["automation", "scene", "script"],
    ),
    # A numbered marker line wraps at its text column, past `1. `.
    (
        "a numbered marker line's wrapped text continues the sentence",
        "1. Forbidden on Home Assistant: turning anything on or off, setting a\n"
        "   value, and running a script, scene, or automation.\n"
        "2. Read the plant.",
        1,
        [],
    ),
    (
        "an exclamation or question mark ends the sentence",
        "  - Forbidden on Home Assistant: turning anything on or off! Setting a\n"
        "    value? Running a script, scene, or automation.",
        1,
        ["automation", "scene", "script", "value"],
    ),
    (
        "a closing bracket after the period still ends the sentence",
        "  - (Forbidden on Home Assistant: turning anything on or off.) Read the\n"
        "    value of each script, scene and automation.",
        1,
        ["automation", "scene", "script", "value"],
    ),
    # A period with no whitespace after it ends nothing: decimals and dotted
    # entity or tool names sit inside the sentence.
    (
        "a decimal or a dotted name does not end the sentence",
        "  - Forbidden on Home Assistant: turning anything on or off, setting a\n"
        "    value such as 0.5, calling `light.turn_on`, or running a script,\n"
        "    scene, or automation.",
        1,
        [],
    ),
    # Known limit, fail-closed: an abbreviation's period followed by a space is
    # a sentence end to this rule. It can fail a recipe, never pass one.
    (
        "an abbreviation's period ends the sentence",
        "  - Forbidden on Home Assistant: turning anything on or off, e.g. a\n"
        "    light, setting a value, or running a script, scene, or automation.",
        1,
        ["automation", "scene", "script", "value"],
    ),
    # The real recipes' shape: the sentence after the marker's is the next
    # rule, and its words do not count.
    (
        "the sentence after the marker's does not count",
        "  Forbidden on Home Assistant: any tool that turns something on or off,\n"
        "  sets a value, or runs a script or scene. Never trigger an automation.",
        1,
        ["automation"],
    ),
    # #84: whether a marker is code is decided by `code_spans`, not by
    # counting backticks on its line.
    (
        "a marker inside a fenced example opens no scope",
        "  Step 1 - read the state.\n"
        "\n"
        "  ```\n"
        "  Forbidden on Home Assistant: on or off, value, script, scene, automation.\n"
        "  ```",
        0,
        sorted(HA_CATEGORY_TERMS),
    ),
    (
        "a marker inside a tilde fence in a list item opens no scope",
        "  - Example:\n"
        "\n"
        "        ~~~\n"
        "        Forbidden on Home Assistant: on or off, value, script, scene, automation.\n"
        "        ~~~",
        0,
        sorted(HA_CATEGORY_TERMS),
    ),
    (
        "a marker after a closed fence opens its scope",
        "  ```\n"
        "  example\n"
        "  ```\n"
        "  - Forbidden on Home Assistant: on or off, value, script, scene, automation.",
        1,
        [],
    ),
    (
        "an unmatched backtick before the marker is literal text",
        "  - Don`t do it. Forbidden on Home Assistant: on or off, value, script,\n"
        "    scene, automation.",
        1,
        [],
    ),
    (
        "a marker inside a double-backtick span opens no scope",
        "  - Quote it as ``Forbidden on Home Assistant: on or off, value, script,\n"
        "    scene, automation.``",
        0,
        sorted(HA_CATEGORY_TERMS),
    ),
    (
        "a single backtick inside a double-backtick span does not close it",
        "  - Quote ``a ` b`` then Forbidden on Home Assistant: on or off, value,\n"
        "    script, scene, automation.",
        1,
        [],
    ),
]

# One shape per way the unclassified-intent guard can misread a recipe body:
# (name, text, expected outside policy, expected missing from policy), both
# read at the read-only recipe's markers.
HA_INTENT_CASES = [
    (
        "both intents inside the block are policy",
        "  - Forbidden by name: `TimeTillErnte`, `time_till`.",
        [],
        [],
    ),
    # The prose form nine recipes carry on develop: a prohibition in English,
    # which is outside every block and therefore reads as a call.
    (
        "a prose prohibition is outside policy and declares nothing",
        "  - Call NO Home Assistant tool, and do not call `TimeTillErnte` or\n"
        "    `time_till`: their effect is unclassified.",
        ["TimeTillErnte", "time_till"],
        ["TimeTillErnte", "time_till"],
    ),
    (
        "one intent in the block and the other in prose",
        "  - Forbidden by name: `TimeTillErnte`.\n"
        "  - Do not call `time_till` either.",
        ["time_till"],
        ["time_till"],
    ),
    (
        "a name after the block is outside it even when the block is complete",
        "  - Forbidden by name: `TimeTillErnte`, `time_till`.\n"
        "  - Step 4 - call `time_till` for the harvest estimate.",
        ["time_till"],
        [],
    ),
    (
        "the prefixed form counts as the intent",
        "  - Step 4 - call `mcp__home_assistant__time_till`.",
        ["time_till"],
        ["TimeTillErnte", "time_till"],
    ),
    # `_` is a word character, so a plain `\b` would also fail to separate a
    # longer name; the boundary has to treat it as part of the name.
    (
        "a longer name containing an intent is not the intent",
        "  - Read `time_till_days` and `TimeTillErnteSensor`.",
        [],
        ["TimeTillErnte", "time_till"],
    ),
    (
        "a permitted block is not policy on a read-only recipe",
        "  - Permitted by name: `TimeTillErnte`, `time_till`.",
        ["TimeTillErnte", "time_till"],
        ["TimeTillErnte", "time_till"],
    ),
    (
        "an intent named in the category sentence is outside policy",
        "  - Forbidden on Home Assistant: on or off, value, script, scene,\n"
        "    automation, and by name `TimeTillErnte` and `time_till`.",
        ["TimeTillErnte", "time_till"],
        ["TimeTillErnte", "time_till"],
    ),
]

# The skill side of the same guard, read through `skill_instruction_text` and
# both markers as `check_skills` will: (name, SKILL.md text, expected outside).
HA_SKILL_INTENT_CASES = [
    # harvest-planning's shape on develop.
    (
        "a prose prohibition in Hard rules is outside policy",
        "## Hard rules\n\n"
        "- Call no Home Assistant tool, and never `TimeTillErnte` or `time_till`.\n",
        ["TimeTillErnte", "time_till"],
    ),
    (
        "both intents in a Forbidden by name run are policy",
        "## Hard rules\n\n"
        "- Call no Home Assistant tool. Forbidden by name: `TimeTillErnte`, "
        "`time_till`.\n",
        [],
    ),
    (
        "an intent explained under Gotchas is not instruction",
        "## Hard rules\n\n"
        "- Forbidden by name: `TimeTillErnte`, `time_till`.\n\n"
        "## Gotchas\n\n"
        "- `TimeTillErnte` looks like the answer to a harvest question.\n",
        [],
    ),
    (
        "an intent in a procedure step is outside policy",
        "## Procedure\n\n1. Ask `time_till` for the estimate.\n\n"
        "## Hard rules\n\n- Forbidden by name: `TimeTillErnte`, `time_till`.\n",
        ["time_till"],
    ),
]

# A read-only recipe that satisfies both Home Assistant rules. Every
# `RECIPE_TEMPLATE` recipe is read-only, so after the guard lands every case
# below that omits this fragment also reports the Home Assistant findings —
# none of the earlier cases' forbidden needles occur in them, which is why
# every Home Assistant finding names "Home Assistant" and none of those needles.
HA_CATEGORY_BLOCK = (
    "  - Forbidden on Home Assistant: any tool that turns something on or off,\n"
    "    sets a value, or runs a script, scene, or automation."
)
HA_INTENT_BLOCK = "  - Forbidden by name: `TimeTillErnte`, `time_till`."
HA_CLEAN = HA_CATEGORY_BLOCK + "\n" + HA_INTENT_BLOCK

RECIPE_CASES = [
    (
        "a policy block inside a template conditional is reported",
        '  {% if view == "months" %}\n' + COMPLETE_BLOCK + "\n  {% endif %}\n",
        PLAIN_INSTRUCTIONS,
        ["has `Forbidden by name:` inside a template conditional"],
        [],
    ),
    (
        "a conditional beside a complete block reports nothing",
        COMPLETE_BLOCK + '\n  {% if view == "months" %}Season.{% else %}Runs.{% endif %}\n',
        PLAIN_INSTRUCTIONS,
        [],
        ["inside a template conditional"],
    ),
    (
        "a complete block reports nothing",
        COMPLETE_BLOCK,
        PLAIN_INSTRUCTIONS,
        [],
        ["calls state-changing tools", "state-changing tools inside a policy"],
    ),
    (
        "a collapsed block plus a real call reports the call as well",
        COLLAPSED_BLOCK + REAL_CALL,
        PLAIN_INSTRUCTIONS,
        [
            "calls state-changing tools",
            "parses as empty",
            f"declares 0 of the {len(STATE_CHANGING_TOOLS)}",
        ],
        [],
    ),
    (
        "fifteen of sixteen plus a real call advises the rename, not the list",
        FIFTEEN_OF_SIXTEEN + REAL_CALL,
        PLAIN_INSTRUCTIONS,
        [
            "calls state-changing tools",
            "rename the file",
            f"declares {len(STATE_CHANGING_TOOLS) - 1} of the {len(STATE_CHANGING_TOOLS)}",
        ],
        ["parses as empty"],
    ),
    (
        "a complete block in `instructions` declares nothing",
        PLAIN_PROMPT,
        COMPLETE_BLOCK,
        [f"declares 0 of the {len(STATE_CHANGING_TOOLS)}"],
        ["calls state-changing tools"],
    ),
    (
        "a recipe with no prompt reports that, and not an incomplete policy",
        "",
        "  Then call `mcp__kamerplanter__archive_plant`.",
        ["has no non-empty `prompt`", "calls state-changing tools"],
        ["state-changing tools inside a policy"],
    ),
    (
        "a permitted block on a read-only recipe is a call, not policy",
        PERMITTED_SPLIT,
        PLAIN_INSTRUCTIONS,
        [
            "calls state-changing tools (claim_diary_analysis)",
            "`Permitted by name:` block without an `-apply`",
        ],
        ["state-changing tools inside a policy"],
    ),
    (
        "no marker at all is not a collapsed block",
        "  Read-only run. Then call `mcp__kamerplanter__archive_plant`.",
        PLAIN_INSTRUCTIONS,
        ["rename the file", f"declares 0 of the {len(STATE_CHANGING_TOOLS)}"],
        ["parses as empty"],
    ),
    (
        "a block in `instructions` does not collapse the prompt's advice",
        "  Then call `mcp__kamerplanter__archive_plant`.",
        COMPLETE_BLOCK,
        ["calls state-changing tools", "rename the file", f"declares 0 of the {len(STATE_CHANGING_TOOLS)}"],
        ["parses as empty"],
    ),
    # The Home Assistant guard (#75). Each Home Assistant finding names "Home
    # Assistant"; the needles below pin which one fires, and "Home Assistant"
    # as a forbidden needle means none does.
    (
        "both Home Assistant rules met report no Home Assistant finding",
        COMPLETE_BLOCK + "\n" + HA_CLEAN,
        PLAIN_INSTRUCTIONS,
        [],
        ["Home Assistant"],
    ),
    (
        "a prompt without the category marker is a finding",
        COMPLETE_BLOCK + "\n" + HA_INTENT_BLOCK,
        PLAIN_INSTRUCTIONS,
        ["no `Forbidden on Home Assistant:` marker"],
        ["sentence omits"],
    ),
    (
        "a marker missing a category names the category",
        COMPLETE_BLOCK
        + "\n  - Forbidden on Home Assistant: any tool that turns something on or off,\n"
        "    sets a value, or runs a script or automation.\n"
        + HA_INTENT_BLOCK,
        PLAIN_INSTRUCTIONS,
        ["sentence omits scene"],
        ["no `Forbidden on Home Assistant:` marker"],
    ),
    # Only `prompt` counts, for the reason the sixteen's completeness check is
    # scoped to it: `instructions` is not enforced on a headless run.
    (
        "the category marker in `instructions` does not count",
        COMPLETE_BLOCK + "\n" + HA_INTENT_BLOCK,
        HA_CATEGORY_BLOCK,
        ["no `Forbidden on Home Assistant:` marker"],
        [],
    ),
    (
        "an intent named in prose in the prompt is a call",
        COMPLETE_BLOCK
        + "\n"
        + HA_CLEAN
        + "\n  - Do not call `TimeTillErnte` for a harvest date.",
        PLAIN_INSTRUCTIONS,
        ["calls unclassified Home Assistant intents (TimeTillErnte)"],
        ["out of its `Forbidden by name:` block"],
    ),
    (
        "an intent named in prose in `instructions` is a call too",
        COMPLETE_BLOCK + "\n" + HA_CLEAN,
        "  Do not call `time_till`.",
        ["calls unclassified Home Assistant intents (time_till)"],
        ["out of its `Forbidden by name:` block"],
    ),
    (
        "one intent absent from the block is a finding naming it",
        COMPLETE_BLOCK + "\n" + HA_CATEGORY_BLOCK + "\n  - Forbidden by name: `TimeTillErnte`.",
        PLAIN_INSTRUCTIONS,
        ["out of its `Forbidden by name:` block (time_till)"],
        ["calls unclassified Home Assistant intents"],
    ),
    (
        "both intents forbidden only in `instructions` are missing from the prompt",
        COMPLETE_BLOCK + "\n" + HA_CATEGORY_BLOCK,
        HA_INTENT_BLOCK,
        ["out of its `Forbidden by name:` block (TimeTillErnte, time_till)"],
        ["calls unclassified Home Assistant intents"],
    ),
    # The prose form on develop: categories without the marker, intents in an
    # English prohibition. Both rules fire, neither hides the other.
    (
        "the prose form on develop fails both rules",
        COMPLETE_BLOCK
        + "\n  - Call NO Home Assistant tool. Specifically, do not turn anything on or\n"
        "    off, do not set a value, do not run a script, scene, or automation, and\n"
        "    do not call `TimeTillErnte` or `time_till`.",
        PLAIN_INSTRUCTIONS,
        [
            "no `Forbidden on Home Assistant:` marker",
            "calls unclassified Home Assistant intents (TimeTillErnte, time_till)",
            "out of its `Forbidden by name:` block (TimeTillErnte, time_till)",
        ],
        [],
    ),
    # The rule is scoped to read-only recipes
    # (spec/mcp/home-assistant-mcp-server/en.md), so an `-apply` recipe is not
    # selected at all. What an `-apply` recipe may do on Home Assistant is not
    # checked here; this case pins only that it draws no finding.
    (
        "an -apply recipe reports no Home Assistant finding",
        COMPLETE_BLOCK + "\n  - Call NO Home Assistant tool at all, not `TimeTillErnte` either.",
        PLAIN_INSTRUCTIONS,
        [],
        ["Home Assistant"],
        "selftest-apply.yaml",
    ),
]


def indent_block(text: str) -> str:
    return "\n".join(
        ("  " + line) if line.strip() else "" for line in text.split("\n")
    )


def recipe_case_findings(
    prompt_body: str, instructions_body: str, filename: str = "selftest-check.yaml"
) -> list[str]:
    """Run the real `check_recipe` over a synthetic recipe built on disk.

    The default filename carries no `-apply` suffix, so this is the read-only
    path — the only one that calls the write-guard with `is_apply=False`, and
    therefore the only place the marker choice for `Permitted by name:` is
    observable at all. A case passes an `-apply` filename only to show a guard
    does not select it.
    """
    text = RECIPE_TEMPLATE.format(instructions=indent_block(instructions_body))
    if prompt_body.strip():
        text += PROMPT_FIELD.format(prompt=indent_block(prompt_body))
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / filename
        path.write_text(text, encoding="utf-8")
        findings = Findings()
        check_recipe(path, findings)
        return findings.errors


def run_self_test() -> int:
    failures = 0
    for name, tools, expected, expected_ambiguous in CLASSIFIER_CASES:
        writes, ambiguous = classify_tools(tools)
        if sorted(writes) != expected or ambiguous != expected_ambiguous:
            failures += 1
            print(
                f"  FAIL {name}\n       expected {expected} / ambiguous "
                f"{expected_ambiguous}, got {sorted(writes)} / ambiguous {ambiguous}"
            )
    if failures:
        print(f"\n{failures} of {len(CLASSIFIER_CASES)} classifier case(s) failed.")
        return 1
    print(
        f"OK — {len(CLASSIFIER_CASES)} classifier cases hold; "
        f"{len(STATE_CHANGING_TOOLS)} state-changing tools in {TOOLS_SNAPSHOT.name}."
    )

    for name, body, expected in WRITE_GUARD_CASES:
        actual = calls_state_changing_tools(body)
        if actual != sorted(expected):
            failures += 1
            print(f"  FAIL {name}\n       expected {sorted(expected)}, got {actual}")
    if failures:
        print(f"\n{failures} of {len(WRITE_GUARD_CASES)} write-guard case(s) failed.")
        return 1
    print(f"OK — {len(WRITE_GUARD_CASES)} write-guard cases hold.")

    for name, body, expected in COMPLETENESS_CASES:
        actual = missing_from_policy(body)
        if actual != sorted(expected):
            failures += 1
            print(f"  FAIL {name}\n       expected {sorted(expected)}, got {actual}")
    if failures:
        print(f"\n{failures} of {len(COMPLETENESS_CASES)} completeness case(s) failed.")
        return 1
    print(f"OK — {len(COMPLETENESS_CASES)} completeness cases hold.")

    for name, body, expected in SKILL_COMPLETENESS_CASES:
        actual = skill_missing_tools(body)
        if actual != sorted(expected):
            failures += 1
            print(f"  FAIL {name}\n       expected {sorted(expected)}, got {actual}")
    if failures:
        print(f"\n{failures} of {len(SKILL_COMPLETENESS_CASES)} skill completeness case(s) failed.")
        return 1
    print(f"OK — {len(SKILL_COMPLETENESS_CASES)} skill completeness cases hold.")

    for name, skill, body, expected, expected_stale in SKILL_OBEDIENCE_CASES:
        actual = sorted({tool for _, tool in skill_unpermitted_calls(body, skill)})
        stale = stale_skill_allowances(body, skill)
        if actual != sorted(expected) or stale != sorted(expected_stale):
            failures += 1
            print(
                f"  FAIL {name}\n       expected {sorted(expected)} / stale "
                f"{sorted(expected_stale)}, got {actual} / stale {stale}"
            )
    if failures:
        print(f"\n{failures} of {len(SKILL_OBEDIENCE_CASES)} skill obedience case(s) failed.")
        return 1
    print(f"OK — {len(SKILL_OBEDIENCE_CASES)} skill obedience cases hold.")

    for name, recipes, skills, expected in PERMITTING_LOAD_CASES:
        actual = permitting_skill_loads(recipes, skills)
        if actual != sorted(expected):
            failures += 1
            print(f"  FAIL {name}\n       expected {sorted(expected)}, got {actual}")
    if failures:
        print(f"\n{failures} of {len(PERMITTING_LOAD_CASES)} permitting-load case(s) failed.")
        return 1
    print(f"OK — {len(PERMITTING_LOAD_CASES)} permitting-load cases hold.")

    for name, prompt, count, expected in HA_CATEGORY_CASES:
        scopes = len(ha_category_scopes(prompt))
        actual = ha_category_missing(prompt)
        if scopes != count or actual != sorted(expected):
            failures += 1
            print(
                f"  FAIL {name}\n       expected {count} scope(s) / missing "
                f"{sorted(expected)}, got {scopes} / missing {actual}"
            )
    if failures:
        print(f"\n{failures} of {len(HA_CATEGORY_CASES)} Home Assistant category case(s) failed.")
        return 1
    print(f"OK — {len(HA_CATEGORY_CASES)} Home Assistant category cases hold.")

    for name, text, outside_expected, missing_expected in HA_INTENT_CASES:
        outside = calls_state_changing_tools(
            text, is_apply=False, tools=HA_UNCLASSIFIED_INTENTS
        )
        missing = missing_from_policy(
            text, READ_ONLY_MARKERS, tools=HA_UNCLASSIFIED_INTENTS
        )
        if outside != sorted(outside_expected) or missing != sorted(missing_expected):
            failures += 1
            print(
                f"  FAIL {name}\n       expected outside {sorted(outside_expected)} / "
                f"missing {sorted(missing_expected)}, got outside {outside} / "
                f"missing {missing}"
            )
    if failures:
        print(f"\n{failures} of {len(HA_INTENT_CASES)} Home Assistant intent case(s) failed.")
        return 1
    print(f"OK — {len(HA_INTENT_CASES)} Home Assistant intent cases hold.")

    for name, skill_text, expected in HA_SKILL_INTENT_CASES:
        actual = calls_state_changing_tools(
            skill_instruction_text(skill_text), tools=HA_UNCLASSIFIED_INTENTS
        )
        if actual != sorted(expected):
            failures += 1
            print(f"  FAIL {name}\n       expected {sorted(expected)}, got {actual}")
    if failures:
        print(
            f"\n{failures} of {len(HA_SKILL_INTENT_CASES)} Home Assistant skill "
            "intent case(s) failed."
        )
        return 1
    print(f"OK — {len(HA_SKILL_INTENT_CASES)} Home Assistant skill intent cases hold.")

    for name, prompt_body, instructions_body, required, forbidden, *filename in RECIPE_CASES:
        reported = "\n".join(
            recipe_case_findings(prompt_body, instructions_body, *filename)
        )
        for needle in required:
            if needle not in reported:
                failures += 1
                print(f"  FAIL {name}\n       no finding contains {needle!r}")
        for needle in forbidden:
            if needle in reported:
                failures += 1
                print(f"  FAIL {name}\n       a finding contains {needle!r}")
    if failures:
        print(f"\n{failures} recipe-level assertion(s) failed.")
        return 1
    print(f"OK — {len(RECIPE_CASES)} recipe-level cases hold.")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return run_self_test()

    if not RECIPES_DIR.is_dir():
        print("recipes/ is missing", file=sys.stderr)
        return 1

    # The write-guard reports OK when it is broken, so the recipes are only
    # meaningfully checked once its own cases hold.
    if run_self_test() != 0:
        return 1

    findings = Findings()
    check_flat_discovery(findings)
    for path in sorted(RECIPES_DIR.glob("*.yaml")):
        check_recipe(path, findings)
    check_extensions(findings)
    check_skills(findings)
    check_permitting_skill_loads(findings)
    check_agents(findings)
    run_goose_validate(findings)

    recipe_count = len(list(RECIPES_DIR.glob("*.yaml")))

    for note in findings.notes:
        print(f"note: {note}")

    if findings.errors:
        print(f"\n{len(findings.errors)} problem(s) across {recipe_count} recipe(s):\n")
        for error in findings.errors:
            print(f"  FAIL {error}")
        return 1

    print(f"\nOK — {recipe_count} recipe(s) match the house pattern.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
