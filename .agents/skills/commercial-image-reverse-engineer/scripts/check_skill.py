#!/usr/bin/env python3
"""Dependency-free Skill packaging lint (not the upstream skills-ref validator)."""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "commercial-image-reverse-engineer"


def inspect_skill(root: Path = ROOT) -> list[str]:
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
        d = desc.group(1).strip().strip('"\'')
        if not d or len(d) > 1024:
            errors.append("SKILL.md description must be 1..1024 characters")
    body = raw[m.end():]
    if not body.strip():
        errors.append("SKILL.md body cannot be empty")
    if len(raw.splitlines()) > 500:
        errors.append("SKILL.md should be 500 lines or less")
    for path in re.findall(r"\]\((\.?\.?/[^)]+|references/[^)]+|assets/[^)]+)\)", body):
        if not (root / path).exists():
            errors.append(f"broken relative reference: {path}")
    meta = root / "agents/openai.yaml"
    if not meta.is_file():
        errors.append("agents/openai.yaml missing")
    else:
        y = meta.read_text(encoding="utf-8")
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
