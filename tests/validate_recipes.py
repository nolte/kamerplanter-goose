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
    named_tools = {
        tool
        for tool in STATE_CHANGING_TOOLS
        if re.search(rf"\b{re.escape(tool)}\b", body)
    }
    is_apply = path.stem.endswith("-apply")
    if named_tools and not is_apply:
        # A recipe may name a state-changing tool purely to forbid it. Treat it
        # as a writer only when the tool is not inside a prohibition.
        forbidding = re.search(
            r"(?i)(forbidden|never call|do not call|must not call)", body
        )
        if not forbidding:
            findings.error(
                where,
                "calls state-changing tools "
                f"({', '.join(sorted(named_tools))}) without an `-apply` "
                "filename suffix.",
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


def main() -> int:
    if not RECIPES_DIR.is_dir():
        print("recipes/ is missing", file=sys.stderr)
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
