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
# Both orders occur, so match either side of the word. This pattern says what
# the author *meant* as a skill reference, which is what a typo check needs —
# it is not how the loaded set is resolved. Requiring the word "skill" next to
# the name let `Follow the procedure in \`diary-analysis-claim\`` slip past the
# write guard entirely, and the skills themselves are written that way.
SKILL_REF_PATTERN = re.compile(
    r"skills?\s+`([a-z0-9][a-z0-9-]*)`|`([a-z0-9][a-z0-9-]*)`\s+skill"
)

# Any backticked token that resolves to a directory here is a load, however the
# sentence around it is phrased. The set on disk is closed, so this needs no
# inference at all.
BACKTICK_TOKEN_PATTERN = re.compile(r"`([a-z0-9][a-z0-9-]*)`")


def available_skills() -> set[str]:
    """Directories that actually carry a SKILL.md.

    Counting every directory made a renamed or moved SKILL.md invisible twice
    over: the reference check saw the name as resolving, and the write guard
    silently skipped the file, losing that skill's calls. At runtime the load
    fails and the run answers from the prompt alone.
    """
    if not SKILLS_DIR.is_dir():
        return set()
    return {
        entry.name
        for entry in SKILLS_DIR.iterdir()
        if entry.is_dir() and (entry / "SKILL.md").is_file()
    }


def skills_loaded_by(text: str, available: set[str]) -> set[str]:
    return {
        name for name in BACKTICK_TOKEN_PATTERN.findall(text) if name in available
    }


def skill_texts(name: str) -> list[tuple[str, str]]:
    """A skill's own text plus every file under its `references/`.

    A skill instructs the run to read those, so a call in one is as reachable
    as a call in SKILL.md — and was invisible to every recipe.
    """
    directory = SKILLS_DIR / name
    texts = []
    for path in [directory / "SKILL.md", *sorted(directory.glob("references/*.md"))]:
        if path.is_file():
            texts.append(
                (str(path.relative_to(REPO_ROOT)), path.read_text(encoding="utf-8"))
            )
    return texts


def skill_closure(body: str, available: set[str]) -> list[str]:
    """Every skill reachable from `body`, following skill-to-skill references.

    Resolution was one level deep, so a write in a skill that only another
    skill loads was unreachable for the guard. Eleven such references exist.
    """
    seen, queue = set(), sorted(skills_loaded_by(body, available))
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        for _, text in skill_texts(name):
            queue.extend(sorted(skills_loaded_by(text, available) - seen))
    return sorted(seen)

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


def tool_pattern(tool: str) -> re.Pattern:
    """Match a tool by its bare name or, as every recipe writes it, in its
    `mcp__<server>__` form.

    A plain `\\b<tool>\\b` does not match the prefixed form: the separator is
    `__`, and `_` is a word character, so there is no boundary between
    `kamerplanter__` and `archive_plant`. That silently emptied the match set
    and left the write guard inert against every recipe in this repository.
    """
    return re.compile(rf"(?<![A-Za-z0-9_])(?:mcp__[A-Za-z0-9_]+__)?{re.escape(tool)}\b")


# A recipe declares its tool policy with two literal markers, each opening a
# bullet whose body is nothing but tool names. That convention replaces 147
# lines of prose analysis — sentence ends, list continuations, semicolon and
# em-dash clauses, name-only-line detection — which existed only to guess
# whether a named tool was being called or forbidden, and got it wrong in both
# directions in seven consecutive review rounds.
#
# Deciding it by convention rather than by inference is the whole point: a name
# inside a block is policy, a name outside every block is a call, and neither
# reading depends on how the surrounding English is phrased.
POLICY_MARKERS = ("Forbidden by name:", "Permitted by name:")

BULLET_PREFIX_PATTERN = re.compile(r"^\s*[-*]\s")
BACKTICK_SPAN_PATTERN = re.compile(r"`[^`]*`")


def is_name_line(text: str) -> bool:
    """True when `text` carries backticked names and punctuation, nothing else.

    This is what makes a block's extent unambiguous. Round 9 ended blocks on
    indentation, bullet depth, numbered steps and table pipes — four rules that
    each closed one reported shape and left the next one open, because the real
    question was never "where does the bullet end" but "is this line still a
    name list".

    The test reads no English: strip a leading bullet and every backticked
    span, and a name line has no letters or digits left. A recipe that wants to
    explain itself puts the explanation outside the block, which
    `check_policy_block_format` requires.
    """
    rest = BULLET_PREFIX_PATTERN.sub("", text)
    rest = BACKTICK_SPAN_PATTERN.sub("", rest)
    return not re.search(r"[A-Za-z0-9]", rest)


def policy_spans(prompt: str, marker: str) -> list[tuple[int, int]]:
    """Character spans of every block introduced by `marker`, in order.

    Spans rather than strings, because excision by `str.replace` is
    position-blind: where one marker's block sat inside another's, cutting the
    inner one first left the outer string unmatchable, and it stayed in the
    text as an apparent call.

    A forbidden list split across two bullets is a natural shape — the `-apply`
    recipes already split Permitted from Forbidden that way — so every
    occurrence is taken, not just the first.
    """
    spans = []
    for match in re.finditer(re.escape(marker), prompt):
        end = prompt.find("\n", match.end())
        if end == -1:
            spans.append((match.start(), len(prompt)))
            continue
        if not is_name_line(prompt[match.end():end]):
            # Prose on the marker's own line: the block is the names it
            # carries and nothing more. check_policy_block_format reports it.
            spans.append((match.start(), end))
            continue
        for line in prompt[end + 1:].split("\n"):
            if not line.strip() or not is_name_line(line):
                break
            end += 1 + len(line)
        spans.append((match.start(), end))
    return spans


def policy_blocks(prompt: str, marker: str) -> list[str]:
    """Every block introduced by `marker`, in order; empty when absent."""
    return [prompt[start:end] for start, end in policy_spans(prompt, marker)]


def policy_block(prompt: str, marker: str) -> str:
    """Every block for `marker`, joined — what the completeness check reads."""
    return "\n".join(policy_blocks(prompt, marker))


def names_in(text: str) -> set[str]:
    """State-changing tools named in a stretch of text."""
    return {tool for tool in STATE_CHANGING_TOOLS if tool_pattern(tool).search(text)}


def outside_policy(prompt: str) -> str:
    """The prompt with every policy block cut out.

    Excision, not set subtraction. Subtracting the *names* declared in a policy
    block from the names found in the whole prompt made this guard structurally
    inert: `check_prohibition_completeness` requires all seven tools to appear
    in a block, so the subtrahend was always the full set and the difference
    always empty. A read-only recipe could call `archive_plant` in step 3 and
    pass clean. Cutting the block text out instead leaves every *occurrence*
    elsewhere visible.
    """
    spans = sorted(
        span for marker in POLICY_MARKERS for span in policy_spans(prompt, marker)
    )
    kept, cursor = [], 0
    for start, end in spans:
        if start >= cursor:
            kept.append(prompt[cursor:start])
            cursor = end
        else:  # nested or overlapping: keep the wider cut
            cursor = max(cursor, end)
    kept.append(prompt[cursor:])
    return "\n".join(kept)


def calls_state_changing_tools(prompt: str) -> list[str]:
    """State-changing tools named outside the policy blocks — i.e. called."""
    return sorted(names_in(outside_policy(prompt)))


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


def check_recipe(path: Path, servers: set[str], findings: Findings) -> None:
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
    if not isinstance(description, str):
        findings.error(
            where,
            f"has a `description` that is not a string ({type(description).__name__}). "
            "`--explain` prints it verbatim and every rule below reads it.",
        )
        description = ""
    if not description.strip():
        findings.error(where, "has an empty `description`.")

    # A write-capable recipe announces itself in its filename and description.
    is_apply = path.stem.endswith("-apply")

    # A recipe may name a state-changing tool purely to forbid it, and the
    # house pattern requires naming every forbidden tool individually — so a
    # policy block is present in every recipe here. Names inside one are
    # policy; names anywhere else are calls.
    #
    # The skills a recipe loads are read with it. A recipe is orchestration;
    # the calls live in the procedures, so checking the YAML alone made this
    # guard vacuous for exactly the recipes it targets — both `-apply` files
    # delegate every write to `diary-analysis-claim`, and a skill that gained
    # a call to `archive_plant` would have passed clean in every recipe that
    # loads it.
    available = available_skills()
    referenced = {
        name
        for match in SKILL_REF_PATTERN.finditer(body)
        for name in match.groups()
        if name
    }
    reach = [(where, body)]
    for name in skill_closure(body, available):
        reach.extend(skill_texts(name))

    # Where the call sits, not just that one exists. A write added to a skill
    # produced one finding per loading recipe and named none of them the file
    # that held it.
    check_policy_block_format(where, body, findings)

    calls: dict[str, list[str]] = {}
    for source, text in reach:
        for tool in calls_state_changing_tools(text):
            calls.setdefault(tool, []).append(source)
    calling = sorted(calls)

    def sites(tools: list[str]) -> str:
        return "; ".join(f"{tool} in {', '.join(calls[tool])}" for tool in tools)
    if not is_apply:
        if calling:
            findings.error(
                where,
                f"calls state-changing tools ({sites(calling)}) outside a "
                "policy block and without an `-apply` filename suffix.",
            )
    else:
        # The suffix is not a blank cheque. `Permitted by name:` says which
        # writes this recipe is for; a write outside that list is one its own
        # description does not cover, and the filename is the only signal a
        # reader would otherwise get.
        permitted = names_in(policy_block(body, "Permitted by name:"))
        undeclared = sorted(set(calling) - permitted)
        if undeclared:
            findings.error(
                where,
                f"calls state-changing tools ({sites(undeclared)}) that its "
                "`Permitted by name:` block does not list. An `-apply` "
                "suffix announces writes; it does not authorise every write.",
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

    # An empty prompt is already reported above; a second finding listing all
    # seven tools as "silent" and a third demanding a server prohibition only
    # bury it.
    prompt_text = prompt if isinstance(prompt, str) else ""
    if prompt_text.strip():
        check_unused_server_prohibition(path, prompt_text, servers, findings)
        check_prohibition_completeness(path, prompt_text, is_apply, findings)

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
    for missing in sorted(referenced - available):
        findings.error(
            where,
            f"names the skill `{missing}`, which has no directory under "
            ".claude/skills/. The load fails silently and the run answers "
            "from the prompt alone.",
        )

    names_cwd = "working directory" in description.lower()
    if any(skill in body for skill in available) and not names_cwd:
        findings.error(
            where,
            "loads a project skill but does not name the required working "
            "directory in its `description`. Skill discovery is relative to "
            "the Goose process's cwd; a run started elsewhere loses the skill "
            "silently.",
        )

    # `.claude/agents/` resolves against the same cwd, and no frontmatter key
    # makes an agent selectively invisible when it does not — so a probe run
    # from elsewhere reports UNAVAILABLE and that reading is what the spec's
    # agent table rests on. The rule was stated for skills only, which is why
    # `provider-plugin-check` shipped without it.
    agents = {
        agent.stem for agent in AGENTS_DIR.glob("*.md")
    } if AGENTS_DIR.is_dir() else set()
    dispatched = sorted(name for name in agents if name in body)
    if dispatched and not names_cwd:
        findings.error(
            where,
            f"dispatches the project agent(s) {', '.join(dispatched)} but does "
            "not name the required working directory in its `description`. "
            "`.claude/agents/` resolves against the Goose process's cwd, so a "
            "run started elsewhere reports the agent as unreachable — and for "
            "a probe that reading is the measurement.",
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


def loaded_servers() -> set[str]:
    """Server names from the shared configuration.

    Swallows a parse error rather than raising: this runs from `check_recipe`,
    which is reached before `check_extensions`, and an unhandled `ParserError`
    here replaced every repository finding with a traceback — including the
    "extensions.yaml is not parseable YAML" finding designed for exactly that.
    """
    if not EXTENSIONS_FILE.exists():
        return set()
    try:
        config = yaml.safe_load(EXTENSIONS_FILE.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return set()
    return set((config.get("extensions") or {}).keys())


def check_policy_block_format(source: str, text: str, findings: Findings) -> None:
    """A policy block's body is names and punctuation, nothing else.

    Five recipes ran their block on into multi-sentence prose, and because the
    guard excises the block *text*, every word of that prose was a place a tool
    call could sit unseen. Requiring the format is what makes the excision safe
    — and it is the one rule here a maintainer can satisfy without reading any
    code: move the sentence to its own bullet.
    """
    for marker in POLICY_MARKERS:
        for start, end in policy_spans(text, marker):
            # The line the block stopped at. A name still standing on it means
            # the list ran on into prose — the shape five recipes shipped,
            # where every word after the last name was a place a call could
            # sit unseen.
            # Only the line the block stopped at, and only when a
            # state-changing name still stands on it. A separate bullet that
            # happens to follow — `calculate_mixing_protocol` is permitted:
            # ... — ends the block cleanly and is not a run-on.
            after = text[end:].split("\n")
            offender = after[1] if len(after) > 1 else ""
            # A block that ends because the next bullet opens another block is
            # the shape both `-apply` recipes use, and three guard cases call
            # correct. Without this it reads as a run-on and the message points
            # at a line with nothing wrong with it.
            if any(marker in offender for marker in POLICY_MARKERS):
                continue
            mixed = bool(names_in(offender))
            head = text[start:end].split("\n")[0][len(marker):]
            if not is_name_line(head):
                offender, mixed = head, True
            if mixed:
                findings.error(
                    source,
                    f"mixes prose and tool names on one `{marker}` line "
                    f"({offender.strip()[:70]!r}). A policy block carries "
                    "backticked tool names and punctuation only; the "
                    "explanation belongs on its own line, because the guard "
                    "excises the block and cannot see a call hidden in it.",
                )


def check_prohibition_completeness(
    path: Path, prompt: str, is_apply: bool, findings: Findings
) -> None:
    """Every state-changing tool appears in a policy block — no silence.

    Naming a subset is the failure this catches: `connectivity-check` sat at
    four of seven for as long as the catalog had four, and drifted when it grew
    to seven with nothing noticing. An `-apply` recipe may put a tool under
    `Permitted by name:` instead; a read-only one may not.
    """
    forbidden = names_in(policy_block(prompt, "Forbidden by name:"))
    permitted = names_in(policy_block(prompt, "Permitted by name:"))

    if permitted and not is_apply:
        findings.error(
            f"recipes/{path.name}",
            f"permits state-changing tools ({', '.join(sorted(permitted))}) "
            "without an `-apply` filename suffix.",
        )

    missing = STATE_CHANGING_TOOLS - forbidden - permitted
    if missing:
        findings.error(
            f"recipes/{path.name}",
            f"is silent on {', '.join(sorted(missing))} in its `prompt`. Every "
            "state-changing tool belongs under `Forbidden by name:` — or, in an "
            "`-apply` recipe, under `Permitted by name:`. Silence leaves the "
            "tool to the model's classification, and `instructions` alone is "
            "not enforced on a headless run.",
        )


UNUSED_SERVER_PROHIBITIONS = {
    # Measured across `recipes/` and `.claude/skills/`: 157 references to
    # `mcp__kamerplanter__*`, zero to `mcp__github__*`. The shared
    # configuration loads GitHub anyway and `.envrc` gives it a live token, so
    # every run held a repository write surface nothing here uses.
    #
    # Only servers the repository uses *nowhere* are listed. A rule of the form
    # "forbid every server you do not call" is not decidable from a prompt:
    # `connectivity-check` calls Home Assistant with bare tool names, and
    # `pest-pressure-check` calls Kamerplanter only through the skills it
    # loads, so neither names the server in a way any pattern can separate from
    # policy. Rather than guess, this list stays short and measured — add a
    # server to it when nothing in the repository references it.
    "github": re.compile(r"(?i)call\s+no\s+github\s+tool"),
}


def check_unused_server_prohibition(
    path: Path, prompt: str, servers: set[str], findings: Findings
) -> None:
    """Every recipe forbids each configured server the repository never uses.

    The server set is passed in rather than read here, so the self-test does
    not depend on the live `extensions.yaml`. It did, and a malformed file
    then turned into a self-test failure that masked the parse error the
    validator is designed to report."""
    for server, pattern in UNUSED_SERVER_PROHIBITIONS.items():
        if server not in servers:
            continue
        if pattern.search(prompt):
            continue
        findings.error(
            f"recipes/{path.name}",
            f"does not forbid the `{server}` server in its `prompt`. The "
            "shared configuration loads it with a live credential and nothing "
            "in this repository calls it, so the run holds a tool surface it "
            'has no use for. Say "Call NO ' + server + ' tool".',
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
        # Once per skill, here rather than per loading recipe: four recipes
        # reach `plant-context-collect` and produced four identical findings,
        # while a skill no recipe names was never format-checked at all.
        check_policy_block_format(f".claude/skills/{skill_file.parent.name}", text, findings)

        frontmatter = load_yaml_frontmatter(text)
        if frontmatter.get("disable-model-invocation") is True:
            findings.error(
                f".claude/skills/{skill_file.parent.name}",
                "carries `disable-model-invocation: true`, which makes it "
                "invisible to every non-interactive recipe run.",
            )


SPEC_SERVER_DIR = REPO_ROOT / "spec" / "mcp" / "kamerplanter-mcp-server"

# Both language files, each with its own headings. Checking only `en.md` would
# let a translation the project treats as strictly in sync fall behind silently.
SPEC_WRITE_HEADINGS = {
    "en.md": ("### Write tools", "### Setup tool"),
    "de.md": ("### Schreibtools", "### Setup-Tool"),
}


def check_tool_list_matches_spec(findings: Findings) -> None:
    """`STATE_CHANGING_TOOLS` and the spec's write/setup tables say the same thing.

    The list lives in three places — this constant and both language files —
    and nothing tied them together. That is exactly how the four-of-seven drift
    happened: the server grew a write tool, the spec eventually followed, the
    constant did not, and the guard under-enforced while reporting OK.

    A missing anchor file is an error, not a note. This check exists because a
    silently-passing guard caused that drift; letting it vanish from CI when
    the spec is renamed would reproduce the failure exactly.
    """
    for filename, headings in SPEC_WRITE_HEADINGS.items():
        path = SPEC_SERVER_DIR / filename
        if not path.exists():
            findings.error(
                f"spec/mcp/kamerplanter-mcp-server/{filename}",
                "is missing, so STATE_CHANGING_TOOLS is cross-checked against "
                "nothing. Point SPEC_WRITE_HEADINGS at the file that replaced it.",
            )
            continue

        text = path.read_text(encoding="utf-8")
        documented = set()
        for heading in headings:
            if heading not in text:
                findings.error(
                    f"spec/mcp/kamerplanter-mcp-server/{filename}",
                    f"has no `{heading}` section, so its write tools cannot be "
                    "read and the cross-check would pass vacuously.",
                )
                continue
            section = text.split(heading, 1)[1].split("\n### ", 1)[0]
            documented.update(re.findall(r"^\| `([a-z_]+)`", section, re.M))

        where = f"spec/mcp/kamerplanter-mcp-server/{filename}"
        for missing in sorted(documented - STATE_CHANGING_TOOLS):
            findings.error(
                "tests/validate_recipes.py",
                f"`{missing}` is documented as state-changing in {where} but "
                "absent from STATE_CHANGING_TOOLS, so no recipe is checked "
                "against it.",
            )
        for extra in sorted(STATE_CHANGING_TOOLS - documented):
            findings.error(
                where,
                f"does not list `{extra}` among its write or setup tools, "
                "though STATE_CHANGING_TOOLS does. One of the two is stale.",
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
# The convention, one case per way it can be got wrong. The previous suite
# pinned a prose parser — free-form phrasings, semicolons, em dashes, wrapped
# lists — which is gone; those cases described a mechanism, not a rule, and
# keeping them would have pinned the thing that kept breaking.
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
        "a blank line ends the block",
        "  Forbidden by name: `mcp__kamerplanter__archive_plant`\n"
        "\n"
        "  Step 4 - call `mcp__kamerplanter__create_site`.",
        ["create_site"],
    ),
    (
        "no marker means every name is a call",
        "Call `mcp__kamerplanter__archive_plant` and `create_site`.",
        ["archive_plant", "create_site"],
    ),
    (
        "the permitted block is policy too",
        "  - Permitted by name: `mcp__kamerplanter__claim_diary_analysis`.\n"
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`.",
        [],
    ),
    (
        "bare and prefixed forms both count",
        "  - Forbidden by name: `archive_plant`, `mcp__kamerplanter__create_site`.",
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
        "substring is not a match",
        "unarchive_plantx and archive_plants",
        [],
    ),
    # Round 9. The guard reported OK while enforcing nothing: the completeness
    # check requires all seven names in a block, and the call check subtracted
    # the *names* found there from the names found in the whole prompt — so the
    # difference was empty by construction, for every recipe here.
    (
        "a complete forbidden list does not license a call",
        "  - Call NO tool that changes state.\n"
        "    Forbidden by name:\n"
        "    " + ", ".join(f"`mcp__kamerplanter__{t}`" for t in sorted(STATE_CHANGING_TOOLS)) + ".\n"
        "\n"
        "  Step 3 - call `mcp__kamerplanter__archive_plant`, then "
        "`mcp__kamerplanter__create_site`.",
        ["archive_plant", "create_site"],
    ),
    (
        "a numbered step ends the block without a blank line",
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`.\n"
        "    1. Call `mcp__kamerplanter__submit_diary_analysis` now.",
        ["submit_diary_analysis"],
    ),
    (
        "a table row ends the block without a blank line",
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`.\n"
        "    | Step 4 | call `mcp__kamerplanter__submit_diary_analysis` |",
        ["submit_diary_analysis"],
    ),
    (
        "a nested bullet list is still the block",
        "  - Forbidden by name:\n"
        "    - `mcp__kamerplanter__archive_plant`\n"
        "    - `mcp__kamerplanter__create_site`",
        [],
    ),
    (
        "a second block of the same marker is policy too",
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`.\n"
        "  - Forbidden by name: `mcp__kamerplanter__create_site`.",
        [],
    ),
    # Round 10. Five recipes ran their block on into multi-sentence prose, and
    # because the guard excises the block text, every word of it was a place a
    # call could sit unseen. A block now ends at the first line that is not a
    # name list, and check_policy_block_format reports the run-on.
    (
        "prose ends the block, and a name after it is a call",
        "  - Forbidden by name:\n"
        "    `mcp__kamerplanter__archive_plant`.\n"
        "    The servers are loaded anyway. Then call "
        "`mcp__kamerplanter__create_site`.",
        ["create_site"],
    ),
    (
        "a name list at any indent stays in the block",
        "  - Forbidden by name:\n"
        "`mcp__kamerplanter__archive_plant`,\n"
        "        `mcp__kamerplanter__create_site`.",
        [],
    ),
    (
        "a nested block does not free the outer one",
        "  - Permitted by name: `mcp__kamerplanter__claim_diary_analysis`.\n"
        "    Forbidden by name: `mcp__kamerplanter__archive_plant`.",
        [],
    ),
]

SEVEN = " ".join(f"`mcp__kamerplanter__{t}`" for t in sorted(STATE_CHANGING_TOOLS))
FORBID_ALL = f"  - Forbidden by name: {SEVEN}"
FORBID_FIVE = "  - Forbidden by name: " + " ".join(
    f"`mcp__kamerplanter__{t}`"
    for t in sorted(STATE_CHANGING_TOOLS - {"claim_diary_analysis", "submit_diary_analysis"})
)
PERMIT_TWO = (
    "  - Permitted by name: `mcp__kamerplanter__claim_diary_analysis`, "
    "`mcp__kamerplanter__submit_diary_analysis`."
)

PROHIBITION_COMPLETENESS_CASES = [
    ("all seven forbidden", FORBID_ALL, False, False),
    ("a subset", "  - Forbidden by name: `mcp__kamerplanter__archive_plant`.", False, True),
    ("no policy block at all", "Do not change anything.", False, True),
    # No blanket exemption. Three rounds went into a predicate that tried to
    # tell "forbids everything" from "forbids everything in step 1, calls a
    # tool in step 4" by wording, and it failed both ways.
    ("a blanket does not substitute", "Call NO tool while doing it.", False, True),
    ("-apply splits the seven across both blocks", f"{PERMIT_TWO}\n{FORBID_FIVE}", True, False),
    ("-apply silent on one", FORBID_FIVE, True, True),
    ("a read-only recipe may not permit", f"{PERMIT_TWO}\n{FORBID_FIVE}", False, True),
    # Round 9. `prompt.find(marker)` saw only the first block, so a list split
    # across two bullets read as silent on everything in its second half.
    (
        "the forbidden list split across two bullets",
        "  - Forbidden by name: " + " ".join(
            f"`mcp__kamerplanter__{t}`" for t in sorted(STATE_CHANGING_TOOLS)[:4]
        ) + ".\n  - Forbidden by name: " + " ".join(
            f"`mcp__kamerplanter__{t}`" for t in sorted(STATE_CHANGING_TOOLS)[4:]
        ) + ".",
        False,
        False,
    ),
]


# Round 11. The format check was the one guard with no cases of its own, and
# it shipped rejecting three shapes the write-guard cases call correct — the
# two suites contradicted each other and nothing noticed.
POLICY_FORMAT_CASES = [
    ("a clean block", "  - Forbidden by name: `mcp__kamerplanter__archive_plant`.", False),
    (
        "two blocks in a row",
        "  - Permitted by name: `mcp__kamerplanter__claim_diary_analysis`.\n"
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`.",
        False,
    ),
    (
        "an explanation on its own line",
        "  - Forbidden by name:\n"
        "    `mcp__kamerplanter__archive_plant`.\n"
        "    This review reads files, not a garden.",
        False,
    ),
    (
        "an unrelated bullet after the block",
        "  - Forbidden by name: `mcp__kamerplanter__archive_plant`.\n"
        "  - `mcp__kamerplanter__calculate_mixing_protocol` is permitted.",
        False,
    ),
    (
        "a name and prose on one line",
        "  - Forbidden by name:\n"
        "    `mcp__kamerplanter__archive_plant`,\n"
        "    `mcp__kamerplanter__create_site` — and anything else that writes.",
        True,
    ),
    (
        "prose on the marker's own line",
        "  - Forbidden by name: everything that writes.",
        True,
    ),
]


# Round 12. Every defect in the last four rounds was a check that existed and
# was not reached: a guard whose subtrahend was always the full set, a reach
# that stopped at the YAML, a format check dropped from the recipe path by an
# edit that silently matched nothing. Testing the functions never caught any of
# them, because the functions were right. These drive `check_recipe` end to end
# against a temporary file, which is the only place wiring is observable.
RECIPE_CASES = [
    (
        "prose on the marker line hides a call",
        "x-check.yaml",
        {
            "description": "Read-only probe.",
            "prompt": "  - Forbidden by name: everything that writes, so never "
                      "`mcp__kamerplanter__archive_plant`. Then call "
                      "`mcp__kamerplanter__create_site`.",
        },
        True,
    ),
    (
        "a project agent without the cwd note",
        "y-check.yaml",
        {
            "description": "Dispatches a probe.",
            "prompt": "Call `Agent` with subagent_type `probe-agent-reachable`.",
        },
        True,
    ),
    (
        "a description that is not a string",
        "z-check.yaml",
        {"description": ["a", "list"], "prompt": "Nothing to see."},
        True,
    ),
    (
        "a clean read-only recipe",
        "w-check.yaml",
        {
            "description": "Read-only probe.",
            "prompt": "  - Call NO tool that changes state.\n"
                      "    Forbidden by name:\n"
                      "    " + ", ".join(
                          f"`mcp__kamerplanter__{t}`"
                          for t in sorted(STATE_CHANGING_TOOLS)
                      ) + ".\n"
                      "  - Call NO github tool.",
        },
        False,
    ),
]


def run_recipe_self_test() -> int:
    import tempfile

    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, filename, recipe, should_fail in RECIPE_CASES:
            path = Path(tmp) / filename
            path.write_text(yaml.safe_dump(recipe), encoding="utf-8")
            findings = Findings()
            check_recipe(path, {"github"}, findings)
            if bool(findings.errors) != should_fail:
                failures += 1
                verb = "should have failed" if should_fail else "should have passed"
                print(f"  FAIL {name} — {verb}: {findings.errors}")
    return failures


def run_policy_format_self_test() -> int:
    failures = 0
    for name, text, should_fail in POLICY_FORMAT_CASES:
        findings = Findings()
        check_policy_block_format("probe", text, findings)
        if bool(findings.errors) != should_fail:
            failures += 1
            verb = "should have failed" if should_fail else "should have passed"
            print(f"  FAIL {name} — {verb}")
    return failures


SERVER_PROHIBITION_CASES = [
    ("forbids the unused server", "Call NO GitHub tool at all.", False),
    ("silent on it", "Read-only run. Call NO Home Assistant tool.", True),
    # One tool named as forbidden says nothing about the rest of that server.
    ("one forbidden tool is not a forbidden server", "Forbidden by name: `mcp__github__push_files`.", True),
]


def run_server_self_test() -> int:
    failures = 0
    for name, prompt, should_fail in SERVER_PROHIBITION_CASES:
        findings = Findings()
        check_unused_server_prohibition(Path("probe.yaml"), prompt, {"github"}, findings)
        if bool(findings.errors) != should_fail:
            failures += 1
            verb = "should have failed" if should_fail else "should have passed"
            print(f"  FAIL server: {name} — {verb}")
    return failures


def run_tool_list_self_test() -> tuple[int, int]:
    """Both directions of the cross-check, plus a missing anchor file.

    Returns (failures, cases). The count is derived rather than written down:
    a hardcoded `+ 4` in the summary silently under-reported every case added
    here, so the line that exists to prove coverage stopped tracking it.

    Driven against a temporary spec tree rather than the real one. Reading the
    live files here made a genuine spec/constant drift abort `main()` before a
    single recipe was checked, so an unrelated broken recipe in the same change
    went unreported and the drift was framed as a broken self-test.
    """
    import tempfile

    original_dir = globals()["SPEC_SERVER_DIR"]
    original_tools = set(STATE_CHANGING_TOOLS)
    failures = 0
    cases = 0

    def spec_with(tools: list[str]) -> str:
        rows = "\n".join(f"| `{name}` | `plant_key` | Does a thing |" for name in tools)
        return f"### Write tools\n\n| Tool | Required | Purpose |\n|---|---|---|\n{rows}\n\n### Setup tool\n\n| Tool | Required | Purpose |\n|---|---|---|\n"

    try:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            globals()["SPEC_SERVER_DIR"] = directory

            for filename in SPEC_WRITE_HEADINGS:
                (directory / filename).write_text(spec_with(sorted(STATE_CHANGING_TOOLS)), encoding="utf-8")
            # The de.md fixture needs its own headings.
            (directory / "de.md").write_text(
                spec_with(sorted(STATE_CHANGING_TOOLS))
                .replace("### Write tools", "### Schreibtools")
                .replace("### Setup tool", "### Setup-Tool"),
                encoding="utf-8",
            )
            cases += 1
            findings = Findings()
            check_tool_list_matches_spec(findings)
            if findings.errors:
                failures += 1
                print(f"  FAIL tool-list: matching tree should pass — {findings.errors[0]}")

            # Spec documents a tool the constant lacks.
            STATE_CHANGING_TOOLS.discard("create_site")
            cases += 1
            findings = Findings()
            check_tool_list_matches_spec(findings)
            if not findings.errors:
                failures += 1
                print("  FAIL tool-list: a tool missing from the constant should fail")
            STATE_CHANGING_TOOLS.add("create_site")

            # Constant carries a tool the spec dropped.
            STATE_CHANGING_TOOLS.add("invented_tool")
            cases += 1
            findings = Findings()
            check_tool_list_matches_spec(findings)
            if not findings.errors:
                failures += 1
                print("  FAIL tool-list: a tool missing from the spec should fail")
            STATE_CHANGING_TOOLS.discard("invented_tool")

            # The anchor file is gone.
            (directory / "en.md").unlink()
            cases += 1
            findings = Findings()
            check_tool_list_matches_spec(findings)
            if not findings.errors:
                failures += 1
                print("  FAIL tool-list: a missing anchor file should fail")
    finally:
        globals()["SPEC_SERVER_DIR"] = original_dir
        STATE_CHANGING_TOOLS.clear()
        STATE_CHANGING_TOOLS.update(original_tools)
    return failures, cases


def run_completeness_self_test() -> int:
    failures = 0
    for name, prompt, is_apply, should_fail in PROHIBITION_COMPLETENESS_CASES:
        findings = Findings()
        check_prohibition_completeness(Path("probe.yaml"), prompt, is_apply, findings)
        if bool(findings.errors) != should_fail:
            failures += 1
            verb = "should have failed" if should_fail else "should have passed"
            print(f"  FAIL {name} — {verb}")
    return failures


def run_self_test() -> int:
    """Every suite runs, then the result is reported.

    Returning early on a write-guard failure hid whatever else broke in the
    same change — and these four suites break together, because they read the
    same policy blocks.
    """
    failures = 0
    for name, body, expected in WRITE_GUARD_CASES:
        actual = calls_state_changing_tools(body)
        if actual != sorted(expected):
            failures += 1
            print(f"  FAIL {name}\n       expected {sorted(expected)}, got {actual}")
    failures += run_completeness_self_test()
    failures += run_policy_format_self_test()
    failures += run_recipe_self_test()
    failures += run_server_self_test()
    tool_list_failures, tool_list_cases = run_tool_list_self_test()
    failures += tool_list_failures
    total = (len(WRITE_GUARD_CASES) + len(PROHIBITION_COMPLETENESS_CASES)
             + len(POLICY_FORMAT_CASES) + len(RECIPE_CASES)
             + len(SERVER_PROHIBITION_CASES)
             + tool_list_cases)
    if failures:
        print(f"\n{failures} of {total} self-test case(s) failed.")
        return 1
    print(f"OK — {total} guard cases hold.")
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
    servers = loaded_servers()
    for path in sorted(RECIPES_DIR.glob("*.yaml")):
        check_recipe(path, servers, findings)
    check_extensions(findings)
    check_skills(findings)
    check_agents(findings)
    check_tool_list_matches_spec(findings)
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
