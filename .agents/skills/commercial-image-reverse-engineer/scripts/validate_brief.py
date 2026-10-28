#!/usr/bin/env python3
"""Validate a prompt/audit brief; this script does not inspect image pixels."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import Any

REQUIRED_SECTIONS = ("task", "assets", "reference_policy", "subject", "scene", "lighting", "camera", "color", "quality", "negative_constraints", "observations")
TRANSFER_FIELDS = {"lighting", "palette", "composition", "camera", "depth", "background", "prop_logic", "mood"}
VALID_MODES = {"prompt", "audit_repair"}
VALID_SUPPORT = {"physical", "suspended", "none"}
VALID_LABEL = {"preserve", "unverified", "remove", "none"}
VALID_PROVENANCE = {"visible_in_source", "user_confirmed", "inferred"}
ANCHOR_FIELDS = ("identity", "shape", "materials", "components", "state")
GLOBAL_TEXT_BANS = ("禁止任何文字", "不要任何文字", "禁止文字", "不要文字", "无文字", "禁止logo", "不要logo", "无logo", "no text", "no logo")

def _value(obj: dict, path: str) -> Any:
    current = obj
    for key in path.split("."):
        if not isinstance(current, dict): return None
        current = current.get(key)
    return current

def _filled(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())

def validate(brief: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if not isinstance(brief, dict): return ["root: expected object"], []
    for key in REQUIRED_SECTIONS:
        if key not in brief: errors.append(f"missing section: {key}")
    if errors: return errors, warnings
    if _value(brief, "task.mode") not in VALID_MODES:
        errors.append("task.mode: brief CLI supports prompt|audit_repair; reference analysis does not require a brief")
    ratio = _value(brief, "task.aspect_ratio")
    if not _filled(ratio) or not re.fullmatch(r"[1-9]\d*:[1-9]\d*", ratio): errors.append("task.aspect_ratio: expected W:H, e.g. 3:4")
    if _value(brief, "quality.aspect_ratio") != ratio: errors.append("aspect ratio conflict: task.aspect_ratio != quality.aspect_ratio")
    count = _value(brief, "task.output_count")
    if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 12: errors.append("task.output_count: expected integer 1..12")
    if not _filled(_value(brief, "assets.subject_image")): errors.append("assets.subject_image: must identify source image (do not invent file path)")
    refs = _value(brief, "assets.reference_images")
    if not isinstance(refs, list) or not refs or not all(_filled(x) for x in refs): warnings.append("reference image unavailable: only use explicitly supplied style text, not claimed visual observations")
    if _value(brief, "task.mode") == "audit_repair" and not _filled(_value(brief, "assets.generated_image")): warnings.append("audit_repair selected but generated image absent; do not claim visual QA")
    transfers = _value(brief, "reference_policy.transfer")
    if not isinstance(transfers, list): errors.append("reference_policy.transfer: must be a list")
    elif (disallowed := sorted(set(str(x) for x in transfers) - TRANSFER_FIELDS)): errors.append(f"reference_policy.transfer: invalid or identity-bearing values {disallowed}")
    if not isinstance(_value(brief, "reference_policy.exclude"), list): errors.append("reference_policy.exclude: must be a list")
    quantity = _value(brief, "subject.quantity")
    if not isinstance(quantity, int) or isinstance(quantity, bool) or not 1 <= quantity <= 12: errors.append("subject.quantity: expected integer 1..12 (distinct from output_count)")
    for field in ("subject.identity", "subject.category", "subject.shape", "subject.state"):
        if not _filled(_value(brief, field)): errors.append(f"{field}: missing product anchor")
    provenance = _value(brief, "subject.provenance")
    if not isinstance(provenance, dict): errors.append("subject.provenance: expected provenance for each product anchor")
    else:
        for field in ANCHOR_FIELDS:
            if provenance.get(field) not in VALID_PROVENANCE: errors.append(f"subject.provenance.{field}: expected visible_in_source|user_confirmed|inferred")
    for field in ("subject.materials", "subject.components"):
        arr = _value(brief, field)
        if not isinstance(arr, list) or not arr: errors.append(f"{field}: expected at least one confirmed part")
        else:
            names = [part.get("part", "") for part in arr if isinstance(part, dict)]
            if len(names) != len(set(names)): errors.append(f"{field}: repeated part name; distinguish part instances")
            for i, part in enumerate(arr):
                keys = ("part", "appearance", "light_response") if field.endswith("materials") else ("part", "appearance", "lock")
                if not isinstance(part, dict) or any(not _filled(part.get(k)) for k in keys): errors.append(f"{field}[{i}]: incomplete part specification")
    keep = _value(brief, "subject.must_preserve")
    if not isinstance(keep, list) or not keep or not all(_filled(x) for x in keep): errors.append("subject.must_preserve: at least one concrete invariant is required")
    label_obj, policy = _value(brief, "subject.label"), _value(brief, "subject.label.policy")
    if not isinstance(label_obj, dict): errors.append("subject.label: expected object")
    if policy not in VALID_LABEL: errors.append("subject.label.policy: expected preserve|unverified|remove|none")
    text = _value(brief, "subject.label.exact_text")
    if not isinstance(text, list): errors.append("subject.label.exact_text: expected list"); text = []
    if policy == "preserve":
        if not text or not all(_filled(x) for x in text): errors.append("preserve label requires user-confirmed, readable exact_text; else use unverified")
        if _value(brief, "subject.label.source") not in {"user_confirmed", "visible_in_source"}: errors.append("preserve label must have source=user_confirmed|visible_in_source")
    if policy in {"unverified", "none", "remove"} and text: errors.append(f"{policy} label must not include exact_text")
    if policy == "remove" and _value(brief, "subject.label.source") != "user_confirmed": errors.append("label removal requires explicit user confirmation")
    stype = _value(brief, "scene.support_type")
    if stype not in VALID_SUPPORT: errors.append("scene.support_type: expected physical|suspended|none")
    support, contact = str(_value(brief, "scene.support") or ""), str(_value(brief, "scene.contact") or "")
    if stype == "physical":
        if not _filled(support) or not _filled(contact): errors.append("physical scene requires scene.support and scene.contact")
        if any(x in support.lower() for x in ("无实体承载", "无承载", "no physical support")): errors.append("physical scene contradicts an explicitly absent support")
    if stype == "suspended":
        if support and not any(x in support.lower() for x in ("无实体", "none", "无承载", "no physical")): errors.append("suspended scene cannot specify a physical supporting surface")
        if any(x in contact for x in ("底部与", "落座于", "地面接触", "接触阴影", "稳稳坐落")): errors.append("suspended scene contradicts ground-contact instructions")
    if stype == "none" and (support or contact): errors.append("support_type=none must not specify support or contact")
    for field in ("scene.concept", "scene.background", "scene.placement", "scene.occlusion", "scene.physics", "lighting.key", "lighting.fill", "lighting.shadows", "camera.viewpoint", "camera.framing", "camera.focus", "color.hierarchy", "quality.photographic_goal"):
        if not _filled(_value(brief, field)): errors.append(f"{field}: missing required control")
    negatives = _value(brief, "negative_constraints")
    if not isinstance(negatives, list): errors.append("negative_constraints: expected list")
    else:
        if not all(_filled(x) for x in negatives): errors.append("negative_constraints: all entries must be nonblank text")
        if policy == "preserve":
            for item in negatives:
                low = str(item).lower().replace(" ", "")
                if any(p.lower().replace(" ", "") in low for p in GLOBAL_TEXT_BANS) and not any(s in low for s in ("背景", "额外", "水印", "画面其他", "非商品", "非包装", "outsideproduct")):
                    errors.append("label conflict: blanket no-text/no-logo contradicts preserved product labeling"); break
    obs = brief.get("observations")
    if not isinstance(obs, dict) or not all(isinstance(obs.get(k), list) for k in ("verified_from_image", "user_provided", "inferred_or_suggested", "unknown")): errors.append("observations: expected 4 provenance lists")
    return errors, warnings

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--brief", type=Path, required=True); args = parser.parse_args()
    try: data = json.loads(args.brief.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: print(f"ERROR: {exc}"); return 2
    errors, warnings = validate(data)
    for issue in errors: print("ERROR:", issue)
    for issue in warnings: print("WARNING:", issue)
    print(f"CHECK: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0

if __name__ == "__main__": raise SystemExit(main())

