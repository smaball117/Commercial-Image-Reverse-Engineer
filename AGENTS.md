# Agent instructions for this repository

## Mission
Maintain and verify the standalone Codex Agent Skill at `.agents/skills/commercial-image-reverse-engineer/`. This is **not** a film-directing training repository.

## Canonical layout
- All runtime instructions in the one canonical `.agents/skills/commercial-image-reverse-engineer/SKILL.md`.
- Supporting rules: skill `references/`; reusable templates: `assets/`; deterministic scripts: `scripts/`; synthetic data: `examples/`; regression tests: `tests/`; optional UI metadata: `agents/openai.yaml`.
- Do not create another root-level `SKILL.md` with the same name. Codex loads this project skill from `.agents/skills`.

## Maintenance protocol
1. Read SKILL.md and the relevant references before modifying behavior.
2. Separate statements from the original article and project-added engineering rules; never claim original author published these scripts or tested their efficacy.
3. Preserve image-role precedence and product identity anchors. Never invent unreadable label text, exact lens settings from a JPEG, or true model success rates.
4. When changing a contract, update templates, validation, compilation and tests together.
5. Run `python -m unittest discover -s .agents/skills/commercial-image-reverse-engineer/tests -v` and example CLI smoke tests before stating it passes.
6. For actual image-model tests, record model/version, image IDs, unchanged controls, full prompts, all outputs (including failures), evaluator and score. Never label simulated or synthetic data as verified results.
7. This repo is publicly visible: no original copyrighted source PDF/MD, author's images, client product assets, logos, private model outputs or secrets without explicit authorization.

## Test report honesty
Distinguish: (A) structural metadata validation; (B) offline unit/contract tests; (C) visual experiments with an actual image model. A and B do NOT imply C.
