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
# outside a prohibition list has to carry the -apply suffix.
STATE_CHANGING_TOOLS = {
    "add_plant_diary_entry",
    "archive_plant",
    "claim_diary_analysis",
    "confirm_care_task",
    "create_site",
    "set_plant_location",
    "submit_diary_analysis",
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


PROHIBITION_PATTERN = re.compile(
    r"(?i)(forbidden|never call|do not call|must not call|must not be called)"
)

BULLET_PATTERN = re.compile(r"^(\s*)[-*]\s")

# A line that opens a new structural element rather than continuing the
# previous one: a bullet, a numbered step, a table row.
STRUCTURAL_LINE_PATTERN = re.compile(r"^\s*(?:[-*]\s|\d+[.)]\s|\|)")

# A token shaped like a tool identifier: snake_case, optionally carrying the
# `mcp__<server>__` prefix. Prose words never match, because they have no
# underscore.
TOOL_TOKEN_PATTERN = re.compile(
    r"^(?:mcp__[A-Za-z0-9]+__)?[a-z0-9]+(?:_[a-z0-9]+)+$"
)


def tool_pattern(tool: str) -> re.Pattern:
    """Match a tool by its bare name or, as every recipe actually writes it, in
    its `mcp__<server>__` form.

    A plain `\\b<tool>\\b` does not match the prefixed form: the separator is
    `__`, and `_` is a word character, so there is no boundary between
    `kamerplanter__` and `archive_plant`. That silently emptied the match set
    and left the write-guard below inert against every recipe in this
    repository.
    """
    return re.compile(rf"(?<![A-Za-z0-9_])(?:mcp__[A-Za-z0-9_]+__)?{re.escape(tool)}\b")


def instruction_units(body: str) -> list[tuple[int, int]]:
    """Split the body into the smallest self-contained instruction units:
    blank-line-separated paragraphs, and inside a paragraph, each top-level
    list item with its continuation lines.

    The unit — not the sentence — is what a prohibition governs. The house
    pattern writes a forbidden-tool list as a bullet whose items wrap over
    several lines, sometimes as nested bullets, and any sentence-based rule
    either stops inside that list (rejecting a correct recipe) or runs past
    the blank line into the steps below it (exempting a real call).
    """
    units = []
    for paragraph in re.finditer(r"[^\n]+(?:\n[^\n]+)*", body):
        lines = paragraph.group(0).split("\n")
        indents = [
            len(match.group(1))
            for line in lines
            if (match := BULLET_PATTERN.match(line))
        ]
        top_level = min(indents) if indents else None

        start, offset = paragraph.start(), paragraph.start()
        for line in lines:
            match = BULLET_PATTERN.match(line)
            is_sibling = match is not None and len(match.group(1)) == top_level
            if is_sibling and offset > start:
                units.append((start, offset))
                start = offset
            offset += len(line) + 1
        units.append((start, paragraph.end()))
    return units


def is_name_only(line: str) -> bool:
    """Whether a line carries nothing but tool names and punctuation — the
    continuation of a forbidden-tool list, rather than an instruction."""
    stripped = BULLET_PATTERN.sub("", line)
    tokens = [token for token in re.split(r"[\s`,;:.|]+", stripped) if token]
    return bool(tokens) and all(TOOL_TOKEN_PATTERN.match(t) for t in tokens)


SENTENCE_END_PATTERN = re.compile(r"\.(?=\s|$)")


def prohibition_spans(body: str) -> list[tuple[int, int]]:
    """Character ranges in which naming a state-changing tool forbids it.

    A prohibition covers **its own sentence, plus any following lines that
    consist only of tool names**, clipped to its instruction unit.

    Every part of that was learned from a shape that defeated an earlier
    version, and `--self-test` holds one case per lesson:

    - *Its own sentence*, not from the phrase forward, so "X and Y are
      forbidden" covers tools named before the phrase.
    - The sentence may *wrap over continuation lines*, because a real
      forbidden-tool list does — sometimes trailing off into prose on the
      closing line — but never over a line that opens a new structural element,
      which is what stops a table row or a numbered step carrying a real call
      from being swallowed.
    - *Name-only continuation lines* extend it further, covering a list written
      as nested bullets. Testing for names rather than for an English call verb
      is what makes this language-independent: "Then `create_site` with the
      plant_key" is not a list continuation whichever verb it uses, or none.
    - *Clipped to the unit*, so a prohibition never reaches past a blank line
      or a sibling bullet into the steps below it.
    """
    spans = []
    for start, end in instruction_units(body):
        unit = body[start:end]

        def line_bounds(position: int) -> tuple[int, int]:
            begin = unit.rfind("\n", 0, position) + 1
            stop = unit.find("\n", position)
            return begin, len(unit) if stop == -1 else stop

        for match in PROHIBITION_PATTERN.finditer(unit):
            region_start, region_end = line_bounds(match.start())

            # Walk back over continuation lines so a sentence that began on an
            # earlier line is covered whole.
            while region_start > 0 and not STRUCTURAL_LINE_PATTERN.match(
                unit[region_start : line_bounds(region_start)[1]]
            ):
                region_start = unit.rfind("\n", 0, region_start - 1) + 1

            while region_end < len(unit):
                next_start, next_end = region_end + 1, None
                next_end = unit.find("\n", next_start)
                next_end = len(unit) if next_end == -1 else next_end
                if STRUCTURAL_LINE_PATTERN.match(unit[next_start:next_end]):
                    break
                region_end = next_end

            before = [m.end() for m in SENTENCE_END_PATTERN.finditer(unit, region_start, match.start())]
            left = before[-1] if before else region_start
            after = SENTENCE_END_PATTERN.search(unit, match.end(), region_end)
            right = after.end() if after else region_end + 1

            # Then over any following lines that carry nothing but tool names.
            while right < len(unit):
                stop = unit.find("\n", right)
                stop = len(unit) if stop == -1 else stop
                if not is_name_only(unit[right:stop]):
                    break
                right = stop + 1

            spans.append((start + left, start + min(right, len(unit))))
    return spans


def calls_state_changing_tools(body: str) -> list[str]:
    """State-changing tools this body calls, ignoring those it only forbids."""
    spans = prohibition_spans(body)
    return sorted(
        {
            tool
            for tool in STATE_CHANGING_TOOLS
            for match in tool_pattern(tool).finditer(body)
            if not any(start <= match.start() < end for start, end in spans)
        }
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
        # A recipe may name a state-changing tool purely to forbid it, and the
        # house pattern requires naming every forbidden tool individually — so
        # a prohibition list is present in almost every recipe here.
        #
        # Exempting the whole recipe as soon as any prohibition appears
        # therefore disables this check entirely: a recipe that forbids one
        # write tool and calls another passes. Exempt per *occurrence* instead,
        # and only inside the prohibiting sentence itself.
        calling = calls_state_changing_tools(body)
        if calling:
            findings.error(
                where,
                "calls state-changing tools "
                f"({', '.join(calling)}) outside a prohibition and without an "
                "`-apply` filename suffix.",
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
WRITE_GUARD_CASES = [
    ("bare call, no prohibition", "Call confirm_care_task now.", ["confirm_care_task"]),
    (
        "prefixed call, no prohibition",
        "Then call `mcp__kamerplanter__archive_plant`.",
        ["archive_plant"],
    ),
    (
        "house-pattern prohibition list",
        "- Call NO tool that changes state. Forbidden on Kamerplanter, by name:\n"
        "  `mcp__kamerplanter__confirm_care_task`, `mcp__kamerplanter__archive_plant`,\n"
        "  `mcp__kamerplanter__submit_diary_analysis`.",
        [],
    ),
    (
        "nested bullet list, real call after a blank line",
        "- Call NO tool that changes state. Forbidden by name:\n"
        "  - `mcp__kamerplanter__confirm_care_task`\n"
        "  - `mcp__kamerplanter__archive_plant`\n"
        "\n"
        "Step 1 - Collect context, then call\n"
        "`mcp__kamerplanter__submit_diary_analysis` with the result.",
        ["submit_diary_analysis"],
    ),
    (
        "forbids one tool, calls another in the same paragraph",
        "Forbidden: `mcp__kamerplanter__archive_plant`.\n"
        "Now call mcp__kamerplanter__submit_diary_analysis to persist the result.",
        ["submit_diary_analysis"],
    ),
    (
        "sibling bullet ends the prohibition",
        "- Forbidden: `mcp__kamerplanter__archive_plant`.\n"
        "- Then call `mcp__kamerplanter__create_site`.",
        ["create_site"],
    ),
    (
        "period inside the prohibiting sentence",
        "Forbidden by name (see spec/mcp/kamerplanter-mcp-server/en.md): "
        "`mcp__kamerplanter__archive_plant`, `mcp__kamerplanter__create_site`.",
        [],
    ),
    (
        "tools named before the phrase",
        "`mcp__kamerplanter__archive_plant` and `mcp__kamerplanter__create_site` "
        "are forbidden.",
        [],
    ),
    (
        "passive prohibition",
        "`mcp__kamerplanter__create_site` must not be called.",
        [],
    ),
    (
        "prohibition after the call does not excuse it",
        "Call archive_plant.\n\nForbidden: create_site.",
        ["archive_plant"],
    ),
    ("substring is not a match", "unarchive_plantx and archive_plants", []),
    # The verb-independence cases. An earlier version asked whether the
    # sentence carried a call verb, which made the guard a list of English
    # words to keep guessing at; each of these slipped through it.
    (
        "call with no verb at all",
        "Forbidden: `mcp__kamerplanter__archive_plant`.\n"
        "Then `mcp__kamerplanter__create_site` with the plant_key.",
        ["create_site"],
    ),
    (
        "verb outside the guessed set",
        "Forbidden: `mcp__kamerplanter__archive_plant`.\n"
        "Trigger `mcp__kamerplanter__create_site`.",
        ["create_site"],
    ),
    (
        "table row carrying a call",
        "| Forbidden | `mcp__kamerplanter__archive_plant` |\n"
        "| Step 3 | call `mcp__kamerplanter__create_site` |",
        ["create_site"],
    ),
    (
        "numbered step carrying a call",
        "Forbidden: `mcp__kamerplanter__archive_plant`.\n"
        "1. Call `mcp__kamerplanter__create_site`.",
        ["create_site"],
    ),
    # connectivity-check's real shape: the list wraps, ends in an em dash, and
    # trails off into prose on the closing line.
    (
        "wrapped list ending in prose",
        "- Call NO tool that changes state. Forbidden on Kamerplanter, by name:\n"
        "    `confirm_care_task`, `archive_plant`, `set_plant_location`, "
        "`create_site` —\n"
        "    and anything else that writes.",
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
