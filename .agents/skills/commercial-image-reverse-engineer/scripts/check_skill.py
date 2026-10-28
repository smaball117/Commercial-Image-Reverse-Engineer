#!/usr/bin/env python3
"""Dependency-free lint for this repository's Agent Skill package."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "commercial-image-reverse-engineer"
MARKDOWN_LINK = re.compile(r"!?\[[^]]*\]\(([^)]+)\)")


def project_root(root: Path) -> Path:
    expected_tail = (".agents", "skills", NAME)
    if tuple(root.parts[-3:]) == expected_tail:
        return root.parents[2]
    return root


def local_link_target(raw_target: str) -> str | None:
    target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
    target = target.split("#", 1)[0]
    if not target or target.startswith(("/", "#", "mailto:", "http:", "https:", "data:")):
        return None
    return target


def inspect_relative_links(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for document in repo_root.rglob("*.md"):
        text = document.read_text(encoding="utf-8-sig")
        for raw_target in MARKDOWN_LINK.findall(text):
            target = local_link_target(raw_target)
            if target and not (document.parent / target).exists():
                errors.append(f"broken relative reference: {document.relative_to(repo_root)} -> {target}")
    return errors


def inspect_skill(root: Path = ROOT) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    file = root / "SKILL.md"
    if not file.is_file():
        return ["SKILL.md missing at skill root"]
    raw = file.read_text(encoding="utf-8-sig")
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", raw, re.S)
    if not m:
        return ["SKILL.md requires YAML frontmatter surrounded by ---"]
    yaml = m.group(1)
    name = re.search(r"^name:\s*['\"]?([a-z0-9-]+)['\"]?\s*$", yaml, re.M)
    desc = re.search(r"^description:\s*(.*)$", yaml, re.M)
    if not name or name.group(1) != NAME:
        errors.append("SKILL.md name must match directory and be lowercase-hyphen")
    if not desc:
        errors.append("SKILL.md description missing")
    else:
        description = desc.group(1).strip().strip("\"'")
        if not description or len(description) > 1024:
            errors.append("SKILL.md description must be 1..1024 characters")
    if not raw[m.end():].strip():
        errors.append("SKILL.md body cannot be empty")
    if len(raw.splitlines()) > 500:
        errors.append("SKILL.md should be 500 lines or less")

    repo = project_root(root)
    expected_location = repo / ".agents" / "skills" / NAME
    if root != expected_location.resolve():
        errors.append("skill must be discoverable at .agents/skills/commercial-image-reverse-engineer")
    if (repo / "SKILL.md").exists():
        errors.append("root-level SKILL.md conflicts with the canonical project skill")
    errors.extend(inspect_relative_links(repo))

    meta = root / "agents/openai.yaml"
    if not meta.is_file():
        errors.append("agents/openai.yaml missing")
    else:
        y = meta.read_text(encoding="utf-8-sig")
        for keyword in ("interface:", "display_name:", "short_description:", "default_prompt:"):
            if keyword not in y:
                errors.append(f"openai.yaml missing: {keyword}")
        if "$" + NAME not in y:
            errors.append("openai.yaml default_prompt must mention $skill-name")
    return errors


def main() -> int:
    errors = inspect_skill()
    for issue in errors:
        print("ERROR:", issue)
    print(f"SKILL CHECK: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

