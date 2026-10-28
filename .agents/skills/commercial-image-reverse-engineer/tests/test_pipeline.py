"""Offline regression checks, not image-generation quality measurement."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_brief import validate
from compile_prompt import compile_zh
from check_skill import inspect_skill


class BriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads((ROOT / "examples" / "forest-serum.brief.json").read_text(encoding="utf-8"))

    def mutated(self):
        return copy.deepcopy(self.baseline)

    def test_skill_structure(self):
        self.assertEqual(inspect_skill(ROOT), [])

    def test_valid_example(self):
        errors, warnings = validate(self.baseline)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_prompt_contains_nine_required_modules(self):
        full, summary = compile_zh(self.baseline)
        for name in ("场景总纲", "主体锁定", "关系定位", "场景承载", "光影材质", "镜头景别", "构图色彩", "画质比例", "反向约束"):
            self.assertIn(f"【{name}】", full)
        self.assertIn("磨砂玻璃", summary)
        self.assertIn("3:4", full)

    def test_deterministic_compilation(self):
        self.assertEqual(compile_zh(self.baseline), compile_zh(self.baseline))

    def test_rejects_identity_transfer(self):
        d = self.mutated()
        d["reference_policy"]["transfer"].append("brand_identity")
        self.assertTrue(any("identity" in err for err in validate(d)[0]))

    def test_rejects_unverified_copy_guess(self):
        d = self.mutated()
        d["subject"]["label"]["exact_text"] = ["随意编写的品牌名"]
        self.assertTrue(any("unverified" in err for err in validate(d)[0]))

    def test_rejects_blank_preserve(self):
        d = self.mutated()
        d["subject"]["label"] = {"policy":"preserve","exact_text":[],"source":"user_confirmed","legibility":"high"}
        self.assertTrue(any("preserve label" in err for err in validate(d)[0]))

    def test_rejects_global_no_logo_with_preserve(self):
        d = self.mutated()
        d["subject"]["label"] = {"policy":"preserve","exact_text":["DEMO"],"source":"user_confirmed","legibility":"high"}
        d["negative_constraints"].append("不要任何文字和Logo")
        self.assertTrue(any("label conflict" in err for err in validate(d)[0]))

    def test_allows_background_only_no_text(self):
        d = self.mutated()
        d["subject"]["label"] = {"policy":"preserve","exact_text":["DEMO"],"source":"user_confirmed","legibility":"high"}
        d["negative_constraints"].append("背景不要任何文字和Logo")
        self.assertEqual(validate(d)[0], [])
        self.assertIn("DEMO", compile_zh(d)[0])

    def test_rejects_suspension_with_solid_support(self):
        d = self.mutated()
        d["scene"]["support_type"] = "suspended"
        self.assertTrue(any("suspended scene" in err for err in validate(d)[0]))

    def test_allows_physical_free_suspension(self):
        d = self.mutated()
        d["scene"].update({"support_type":"suspended", "support":"无实体承载", "contact":"无实体接触，水流与瓶体交互"})
        self.assertEqual(validate(d)[0], [])

    def test_quantity_cannot_be_zero(self):
        d = self.mutated()
        d["subject"]["quantity"] = 0
        self.assertTrue(any("subject.quantity" in err for err in validate(d)[0]))

    def test_multi_product_count_is_not_output_count(self):
        d = self.mutated()
        d["subject"]["quantity"] = 2
        d["task"]["output_count"] = 1
        self.assertEqual(validate(d)[0], [])
        self.assertIn("数量：2", compile_zh(d)[0])

    def test_no_label_with_brand_text_fails(self):
        d = self.mutated()
        d["subject"]["label"] = {"policy": "none", "exact_text": ["SHOULD NOT BE HERE"], "source": "unknown"}
        self.assertTrue(any("none label" in err for err in validate(d)[0]))

    def test_physical_support_cannot_be_absent(self):
        d = self.mutated()
        d["scene"]["support"] = "无实体承载"
        self.assertTrue(any("physical scene" in err for err in validate(d)[0]))

    def test_missing_subject_identity(self):
        d = self.mutated()
        d["subject"]["identity"] = ""
        self.assertTrue(any("subject.identity" in err for err in validate(d)[0]))

    def test_rejects_aspect_ratio_conflict(self):
        d = self.mutated()
        d["quality"]["aspect_ratio"] = "16:9"
        self.assertTrue(any("aspect ratio conflict" in err for err in validate(d)[0]))

    def test_valid_water_splash_example(self):
        d = json.loads((ROOT / "examples" / "water-splash.brief.json").read_text(encoding="utf-8"))
        self.assertEqual(validate(d)[0], [])
        self.assertIn("无实体承载", compile_zh(d)[0])
        self.assertIn("1:1", compile_zh(d)[0])

    def test_verified_label_example(self):
        d = json.loads((ROOT / "examples" / "verified-label.brief.json").read_text(encoding="utf-8"))
        self.assertEqual(validate(d)[0], [])
        self.assertIn("LUMEN LAB", compile_zh(d)[0])

    def test_remove_label_needs_confirmation(self):
        d = self.mutated()
        d["subject"]["label"]["policy"] = "remove"
        self.assertTrue(any("user confirmation" in err for err in validate(d)[0]))

    def test_duplicate_material_parts_fail(self):
        d = self.mutated()
        d["subject"]["materials"].append(d["subject"]["materials"][0])
        self.assertTrue(any("repeated part" in err for err in validate(d)[0]))

    def test_generation_audit_without_result_is_warning_not_accepted_visual_proof(self):
        d = self.mutated()
        d["task"]["mode"] = "audit_repair"
        errors, warnings = validate(d)
        self.assertEqual(errors, [])
        self.assertTrue(any("generated image absent" in x for x in warnings))

    def test_reference_missing_is_warning_not_fake_observation(self):
        d = self.mutated()
        d["assets"]["reference_images"] = []
        errors, warnings = validate(d)
        self.assertEqual(errors, [])
        self.assertTrue(any("reference image unavailable" in x for x in warnings))

    def test_cli_writes_files(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out"
            proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "compile_prompt.py"), "--brief", str(ROOT / "examples" / "forest-serum.brief.json"), "--out", str(out)],capture_output=True,text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(set(p.name for p in out.iterdir()), {"brief.json", "prompt_zh.txt", "prompt_summary.txt", "qa-report.md"})

    def test_cli_does_not_write_on_invalid_brief(self):
        d = self.mutated()
        d["task"]["aspect_ratio"] = "invalid"
        with tempfile.TemporaryDirectory() as td:
            bad, out = Path(td) / "bad.json", Path(td) / "out"
            bad.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "compile_prompt.py"), "--brief", str(bad), "--out", str(out)], capture_output=True,text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
