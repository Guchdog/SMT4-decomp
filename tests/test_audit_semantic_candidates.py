import tempfile
import unittest
from pathlib import Path

from tools.audit_semantic_candidates import _candidate_definitions, audit, render_markdown


class TestCandidateInventory(unittest.TestCase):
    def test_direct_definitions_ignore_comments_literals_and_negative_controls(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "fixture.cpp"
            source.write_text(
                '// candidate_00000001() {}\n'
                'const char* text = "candidate_00000002() {}";\n'
                'extern "C" int candidate_00000003(int x) { return x; }\n'
                'int negative_candidate_00000004() { return 0; }\n'
                'void caller() { candidate_00000003(1); }\n',
                encoding="utf-8",
            )
            self.assertEqual(_candidate_definitions(source), {"candidate_00000003"})

    def test_generated_macro_definitions_count_invocations_not_negative_symbols(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "fixture.cpp"
            source.write_text(
                "#define DEFINE(name, value) " + chr(92) + "\n"
                " extern int name() { return value; }\n"
                "DEFINE(candidate_00000010, 4)\n"
                "DEFINE(negative_candidate_00000010, 5)\n",
                encoding="utf-8",
            )
            self.assertEqual(_candidate_definitions(source), {"candidate_00000010"})

    def test_audit_separates_presence_test_and_report_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for directory in ("experiments/semantic_equivalence", "tools", "tests"):
                (root / directory).mkdir(parents=True)
            (root / "experiments/semantic_equivalence/family_candidates.cpp").write_text(
                'int candidate_00000020() { return 1; }\n'
                'int candidate_00000020_prefix() { return 1; }\n', encoding="utf-8")
            (root / "tools/family_experiment.py").write_text(
                'FUNCTIONS = {0x00000020: 4}\n'
                'SOURCE = ROOT / "experiments/semantic_equivalence/family_candidates.cpp"\n'
                'def run():\n    return {"passed": difference()}\n',
                encoding="utf-8")
            (root / "tests/test_family_experiment.py").write_text(
                'from tools.family_experiment import run\n'
                'def test_it():\n    report = run()\n'
                '    assertTrue(report["passed"])\n'
                '    assertEqual(report["function_comparisons"], 3)\n', encoding="utf-8")
            (root / "experiments/semantic_equivalence/family_report.md").write_text(
                'Candidate `0x00000020` was exercised.\n', encoding="utf-8")
            result = audit(root)
            self.assertEqual(result["candidate_count"], 2)
            self.assertEqual(result["counts"]["address_named_candidates"], 1)
            self.assertEqual(result["counts"]["prefix_or_helper_candidates"], 1)
            candidate = result["candidates"][0]
            self.assertTrue(candidate["presence"])
            self.assertEqual(candidate["linked_tests"], ["test_family_experiment"])
            self.assertEqual(candidate["differential_test_checks"], ["test_family_experiment"])
            self.assertEqual(len(candidate["associated_reports"]), 1)
            markdown = render_markdown(result)
            self.assertIn("| Address-named candidate definitions | 1 |", markdown)
            self.assertIn("candidate_00000020_prefix", markdown)
            self.assertIn("do not count equivalent, integrated, or runtime-validated", markdown)


if __name__ == "__main__":
    unittest.main()
