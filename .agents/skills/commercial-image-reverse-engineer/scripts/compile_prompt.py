#!/usr/bin/env python3
"""Deterministically compile a validated structured brief into reusable prompts.

Input facts must be written by a vision-capable agent or a human. No image reading occurs here.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from validate_brief import validate


def join_parts(values):
    return "；".join(str(v) for v in values if v)


def compile_zh(d: dict) -> tuple[str, str]:
    t, s, scene = d["task"], d["subject"], d["scene"]
    light, camera, color = d["lighting"], d["camera"], d["color"]
    quality, refs = d["quality"], d["reference_policy"]
    label = s["label"]
    mats = join_parts([f'{p["part"]}：{p["appearance"]}，受光：{p["light_response"]}' for p in s["materials"]])
    comps = join_parts([f'{p["part"]}：{p["appearance"]}（{p["lock"]}锁）' for p in s["components"]])
    label_policy = label["policy"]
    if label_policy == "preserve":
        label_text = f'只保留商品图中已确认的包装印刷：{join_parts(label["exact_text"])}；不添加其他字样。'
    elif label_policy == "unverified":
        label_text = "包装标签的具体内容尚未核实：保留原图标签区域与版式轮廓；不猜写品牌字，必要时后期精确合成。"
    elif label_policy == "none":
        label_text = "本商品无包装印刷标识；不要自行生成文字或商标。"
    else:
        label_text = "按用户明确授权移除包装文字；不得凭参考图新增品牌。"
    role = (f'图片角色：商品事实源 = {d["assets"]["subject_image"]}；'
            f'视觉参考 = {join_parts(d["assets"].get("reference_images", [])) or "文字描述（无参考图）"}；'
            f'仅迁移 = {join_parts(refs["transfer"])}；'
            f'禁止迁移 = {join_parts(refs["exclude"])}。')
    sections = [
        ("图片职责", role),
        ("场景总纲", f'{scene["concept"]}。主体必须是 {s["identity"]}（{s["category"]}），核心产品优先于装饰。'),
        ("主体锁定", f'数量：{s["quantity"]}；外形：{s["shape"]}。材质：{mats}。部件：{comps}。状态：{s["state"]}。不可更改：{join_parts(s["must_preserve"])}。{label_text}'),
        ("关系定位", f'位置/朝向：{scene["placement"]}。支撑类型：{scene["support_type"]}。接触：{scene["contact"] or "无实体接触"}。遮挡边界：{scene["occlusion"]}。运动与物理：{scene["physics"]}。'),
        ("场景承载", f'背景：{scene["background"]}。承载：{scene["support"] or "无实体承载"}。道具：{join_parts(scene.get("props", [])) or "无"}。'),
        ("光影材质", f'主光：{light["key"]}。补光：{light["fill"]}。轮廓光：{light.get("rim") or "无额外轮廓光"}。明暗：{light.get("contrast") or "依据实际画面"}。阴影：{light["shadows"]}。各材质受光以主体锁定栏逐部件规则为准。'),
        ("镜头景别", f'焦段（创作设定）：{camera.get("focal_length_equiv") or "未指定"}。机位：{camera["viewpoint"]}。景别：{camera["framing"]}。对焦：{camera["focus"]}。景深：{camera.get("depth_of_field") or "依据主体关键区域确定"}。'),
        ("构图色彩", f'主体尺度：{camera.get("subject_scale") or "以商品为第一主体"}。主色：{color.get("dominant") or "依商品"}。辅色：{color.get("accent") or "克制"}。主次：{color["hierarchy"]}。回避颜色：{color.get("avoid") or "无"}。'),
        ("画质比例", f'{quality["photographic_goal"]}。比例 {t["aspect_ratio"]}，生成数量 {t["output_count"]}。不以文字虚报原生像素数。'),
        ("反向约束", join_parts(d["negative_constraints"])),
    ]
    full = "\n\n".join(f'【{k}】\n{v}' for k, v in sections) + "\n"
    summary = (f'商品锚点：{s["identity"]}；数量：{s["quantity"]}；形状：{s["shape"]}；部件：{comps}；'
               f'状态：{s["state"]}。材料：{mats}。不可更改：{join_parts(s["must_preserve"])}。参考视觉：{join_parts(refs["transfer"])}。'
               f'场景：{scene["concept"]}；支撑/物理：{scene["support_type"]} / {scene["contact"] or scene["physics"]}。'
               f'主光：{light["key"]}。重要禁项：{join_parts(d["negative_constraints"])}。'
               f'画幅 {t["aspect_ratio"]}。{label_text}\n')
    return full, summary


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--brief", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    try:
        brief = json.loads(args.brief.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors, warnings = validate(brief)
    if errors:
        for err in errors: print("ERROR:", err, file=sys.stderr)
        print("Refusing to compile a contradictory brief.", file=sys.stderr)
        return 1
    full, summary = compile_zh(brief)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.out / "prompt_zh.txt").write_text(full, encoding="utf-8")
    (args.out / "prompt_summary.txt").write_text(summary, encoding="utf-8")
    repo = Path(__file__).resolve().parents[1]
    qa = (repo / "assets" / "qa-report.template.md").read_text(encoding="utf-8")
    (args.out / "qa-report.md").write_text(qa, encoding="utf-8")
    print(f"Wrote {args.out / 'prompt_zh.txt'}, brief.json, summary and QA template")
    for w in warnings: print("WARNING:", w)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
