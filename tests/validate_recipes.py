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
                if re.search(r"[A-Za-z0-9]", between):
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
        if calling:
            findings.error(
                where,
                f"calls state-changing tools ({', '.join(calling)}) outside a "
                "`Forbidden by name:` block and without an `-apply` filename "
                "suffix. Move the name into that block if the recipe forbids "
                "the tool; rename the file and say so in `description` if it "
                "calls it.",
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
    for missing in sorted(referenced - available):
        findings.error(
            where,
            f"names the skill `{missing}`, which has no directory under "
            ".claude/skills/. The load fails silently and the run answers "
            "from the prompt alone.",
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

        for missing in sorted(referenced - declared):
            findings.error(
                where,
                f"references ${{{missing}}} but does not list it in "
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
]


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
