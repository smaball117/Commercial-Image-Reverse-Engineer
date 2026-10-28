"""Offline contract tests; these do not measure image-generation quality."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_skill import inspect_skill
from compile_prompt import compile_zh
from validate_brief import validate


class BriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.examples = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "examples").glob("*.json")}
        cls.baseline = cls.examples["forest-serum.brief"]

    def mutated(self):
        return copy.deepcopy(self.baseline)

    def test_project_discovery_metadata_and_relative_links(self):
        self.assertEqual(inspect_skill(ROOT), [])

    def test_all_three_synthetic_examples_validate(self):
        self.assertEqual(set(self.examples), {"forest-serum.brief", "water-splash.brief", "verified-label.brief"})
        for name, brief in self.examples.items():
            with self.subTest(name=name): self.assertEqual(validate(brief)[0], [])

    def test_compiler_has_nine_control_modules(self):
        full, summary = compile_zh(self.baseline)
        for name in ("场景总纲", "主体锁定", "关系定位", "场景承载", "光影材质", "镜头景别", "构图色彩", "画质比例", "反向约束"):
            self.assertIn(f"【{name}】", full)
        self.assertIn("3:4", summary)

    def test_identity_transfer_and_unverified_copy_are_rejected(self):
        d = self.mutated(); d["reference_policy"]["transfer"].append("brand_identity")
        self.assertTrue(any("identity" in item for item in validate(d)[0]))
        d = self.mutated(); d["subject"]["label"]["exact_text"] = ["invented brand"]
        self.assertTrue(any("unverified" in item for item in validate(d)[0]))

    def test_preserved_label_rejects_blanket_no_text_but_allows_background_only(self):
        d = copy.deepcopy(self.examples["verified-label.brief"]); d["negative_constraints"].append("no text or logo")
        self.assertTrue(any("label conflict" in item for item in validate(d)[0]))
        d["negative_constraints"][-1] = "no extra background text or logo"
        self.assertEqual(validate(d)[0], [])

    def test_support_modes_reject_physical_suspension_conflict(self):
        d = self.mutated(); d["scene"].update({"support_type":"suspended", "support":"pine branch"})
        self.assertTrue(any("suspended scene" in item for item in validate(d)[0]))
        self.assertEqual(validate(self.examples["water-splash.brief"])[0], [])

    def test_reference_analysis_is_not_forced_through_prompt_brief_contract(self):
        d = self.mutated(); d["task"]["mode"] = "analyze"
        self.assertTrue(any("does not require a brief" in item for item in validate(d)[0]))

    def test_product_anchors_require_per_field_provenance(self):
        d = self.mutated(); del d["subject"]["provenance"]
        self.assertTrue(any("subject.provenance" in item for item in validate(d)[0]))

    def test_remove_label_cannot_retain_old_copy(self):
        d = self.mutated(); d["subject"]["label"] = {"policy":"remove", "exact_text":["old copy"], "source":"user_confirmed"}
        self.assertTrue(any("remove label" in item for item in validate(d)[0]))

    def test_cli_writes_outputs_only_for_valid_brief(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out"
            proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "compile_prompt.py"), "--brief", str(ROOT / "examples" / "forest-serum.brief.json"), "--out", str(out)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual({p.name for p in out.iterdir()}, {"brief.json", "prompt_zh.txt", "prompt_summary.txt", "qa-report.md"})

if __name__ == "__main__": unittest.main()

