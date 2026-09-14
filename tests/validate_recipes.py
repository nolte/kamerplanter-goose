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

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RECIPES_DIR = REPO_ROOT / "recipes"
EXTENSIONS_FILE = REPO_ROOT / "extensions.yaml"
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

# Kamerplanter MCP tools that change server state. A recipe naming any of these
# outside a policy block has to carry the -apply suffix.
#
# Twelve as of 2026-08-16, counted against the server's live tool surface. The
# last five arrived after the first seven were written, and a tool this set has
# never heard of passes the guard silently: `task test` reports OK and CI stays
# green while a write-capable recipe carries no -apply suffix. Re-count this
# against the server whenever the MCP surface changes.
STATE_CHANGING_TOOLS = {
    "add_plant_diary_entry",
    "archive_plant",
    "assign_nutrient_plan",
    "assign_species_phase_sequence",
    "claim_diary_analysis",
    "confirm_care_task",
    "create_inspection",
    "create_site",
    "record_feeding_event",
    "set_plant_location",
    "submit_diary_analysis",
    "transition_plant_phase",
}

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

BULLET_PREFIX_PATTERN = re.compile(r"^\s*[-*]\s")
BACKTICK_SPAN_PATTERN = re.compile(r"`[^`]*`")
TABLE_ROW_PATTERN = re.compile(r"^\s*\|")


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


def policy_spans(prompt: str, marker: str) -> list[tuple[int, int]]:
    """Character spans of every block introduced by `marker`.

    Spans, not strings: excision by `str.replace` is position-blind and left an
    outer block standing whenever another sat inside it.
    """
    spans = []
    for match in re.finditer(re.escape(marker), prompt):
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
                # A deeper bullet is the nested list itself; a sibling or
                # shallower one is the next element, whichever shape the
                # marker line used.
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


def calls_state_changing_tools(body: str, is_apply: bool = True) -> list[str]:
    """State-changing tools named outside every policy block — i.e. called.

    `Permitted by name:` counts as policy only where the filename says the
    recipe writes. Excising it unconditionally let any recipe declare a write
    permitted and drop out of the guard: renaming
    `diary-photo-analysis-apply.yaml` to drop the suffix left a recipe that
    claims and submits diary analyses passing clean.
    """
    markers = POLICY_MARKERS if is_apply else ("Forbidden by name:",)
    remainder = outside_policy(body, markers)
    return sorted(
        tool for tool in STATE_CHANGING_TOOLS if tool_pattern(tool).search(remainder)
    )


def policy_text(body: str, markers: tuple[str, ...] = POLICY_MARKERS) -> str:
    """Everything INSIDE a policy block — the complement of `outside_policy`."""
    spans = sorted(span for marker in markers for span in policy_spans(body, marker))
    return "\n".join(body[start:end] for start, end in spans)


def missing_from_policy(
    body: str, markers: tuple[str, ...] = POLICY_MARKERS
) -> list[str]:
    """The twelve minus what the artefact names INSIDE a policy block.

    The guard above answers the opposite question — which names sit OUTSIDE a
    block, i.e. are called — and cannot see a subset at all, because an absent
    name is outside nothing. Measured: stripping eight of the twelve out of a
    read-only recipe's `Forbidden by name:` block left the whole gate green.

    Completeness is a property of the union. Both `-apply` recipes split the
    set as two permitted plus ten forbidden, so demanding twelve in the
    forbidden half alone would fail exactly the recipes that declare their
    writes correctly.

    A tool name inside a fenced example counts as declared. That is a false
    negative — it can only make a recipe look more complete than it is, never
    block a correct one — and it is the benign direction to leave open.
    """
    inside = policy_text(body, markers)
    return sorted(
        tool for tool in STATE_CHANGING_TOOLS if not tool_pattern(tool).search(inside)
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
        # once here, because `missing` is all twelve for an empty prompt while
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
    # grown twice — four names, then seven, then twelve. A list written against
    # an earlier count is a subset today, and the guard above cannot see that:
    # it reads names OUTSIDE a policy block, and an absent name is outside
    # nothing. Measured on 2026-09-14: every recipe here names all twelve, so
    # this check starts green and stays a floor.
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
    # declare permitted: one that puts all twelve under `Permitted by name:`
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
    # Assistant would have to name twelve kamerplanter tools it never calls.
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
                "it — harmless, but the entry is skipped entirely when the "
                "variable is unset, with no warning."
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
]


# The completeness guard has its own shapes, because it answers a different
# question than the write-guard above and shares none of its marker logic.
ALL_TWELVE = ", ".join(f"`mcp__kamerplanter__{t}`" for t in sorted(STATE_CHANGING_TOOLS))

COMPLETENESS_CASES = [
    (
        "a complete list inside the block is complete",
        f"  - Call NO tool that changes state. Forbidden by name: {ALL_TWELVE}.",
        [],
    ),
    (
        "prose naming all twelve declares nothing — no block, no policy",
        f"Never call {ALL_TWELVE}. This recipe reads and judges.",
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
        [
            "assign_nutrient_plan",
            "assign_species_phase_sequence",
            "create_inspection",
            "record_feeding_event",
            "transition_plant_phase",
        ],
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
        "a fenced example counts as declared — the one way to silence this",
        "This recipe declares no policy of its own. It prints the template:\n"
        "```\n"
        f"Forbidden by name: {ALL_TWELVE}.\n"
        "```\n",
        [],
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
    + ALL_TWELVE
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

ELEVEN_OF_TWELVE = (
    "  - Call NO tool that changes state.\n    Forbidden by name:\n    "
    + ", ".join(
        f"`mcp__kamerplanter__{tool}`"
        for tool in sorted(STATE_CHANGING_TOOLS - {"confirm_care_task"})
    )
    + "."
)

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

RECIPE_CASES = [
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
            "declares 0 of the 12",
        ],
        [],
    ),
    (
        "eleven of twelve plus a real call advises the rename, not the list",
        ELEVEN_OF_TWELVE + REAL_CALL,
        PLAIN_INSTRUCTIONS,
        [
            "calls state-changing tools",
            "rename the file",
            "declares 11 of the 12",
        ],
        ["parses as empty"],
    ),
    (
        "a complete block in `instructions` declares nothing",
        PLAIN_PROMPT,
        COMPLETE_BLOCK,
        ["declares 0 of the 12"],
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
        ["rename the file", "declares 0 of the 12"],
        ["parses as empty"],
    ),
    (
        "a block in `instructions` does not collapse the prompt's advice",
        "  Then call `mcp__kamerplanter__archive_plant`.",
        COMPLETE_BLOCK,
        ["calls state-changing tools", "rename the file", "declares 0 of the 12"],
        ["parses as empty"],
    ),
]


def indent_block(text: str) -> str:
    return "\n".join(
        ("  " + line) if line.strip() else "" for line in text.split("\n")
    )


def recipe_case_findings(prompt_body: str, instructions_body: str) -> list[str]:
    """Run the real `check_recipe` over a synthetic recipe built on disk.

    The filename carries no `-apply` suffix, so this is the read-only path —
    the only one that calls the write-guard with `is_apply=False`, and
    therefore the only place the marker choice for `Permitted by name:` is
    observable at all.
    """
    text = RECIPE_TEMPLATE.format(instructions=indent_block(instructions_body))
    if prompt_body.strip():
        text += PROMPT_FIELD.format(prompt=indent_block(prompt_body))
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "selftest-check.yaml"
        path.write_text(text, encoding="utf-8")
        findings = Findings()
        check_recipe(path, findings)
        return findings.errors


def run_self_test() -> int:
    failures = 0
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

    for name, prompt_body, instructions_body, required, forbidden in RECIPE_CASES:
        reported = "\n".join(recipe_case_findings(prompt_body, instructions_body))
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
