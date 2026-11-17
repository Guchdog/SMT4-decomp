import tempfile
import unittest
from pathlib import Path

from tools.h18_script_word_getters_production import (
    EXPECTED_BYTE_OFFSETS,
    run,
    verify_production_source,
)

ROOT = Path(__file__).resolve().parents[1]


class TestH18ScriptWordGettersProduction(unittest.TestCase):
    def test_production_symbols_use_the_alias_safe_byte_contract(self):
        self.assertEqual(
            verify_production_source(ROOT / "src/engine/leaf_matching.cpp"),
            EXPECTED_BYTE_OFFSETS,
        )

    def test_inline_assembly_or_wrong_offsets_are_rejected(self):
        bad_sources = (
            'extern "C" u32 script_vm_func_002345f0(const u8* p) { asm volatile("ldrh r0, [r0]"); return 0; }',
            'extern "C" u32 script_vm_func_002345fc(const u8* p) { return p[0x48]; }',
        )
        for source in bad_sources:
            with self.subTest(source=source), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "leaf_matching.cpp"
                path.write_text(source, encoding="utf-8")
                with self.assertRaises(ValueError):
                    verify_production_source(path)

    def test_production_source_differential_and_four_caller_compositions(self):
        with tempfile.TemporaryDirectory() as temp:
            report = run(
                ROOT / "extracted/exefs/code.bin",
                Path(temp),
                seed=7,
                samples=0,
            )
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["functions"]), 2)
        self.assertTrue(all(item["passed"] for item in report["functions"]))
        self.assertTrue(all(len(item["original_read_footprint"]) == 2
                            and len(item["candidate_read_footprint"]) == 1
                            for item in report["functions"]))
        self.assertEqual(len(report["caller_windows"]), 4)
        self.assertTrue(all(item["passed"] for item in report["caller_windows"]))
        self.assertTrue(all(item["detected"] for item in report["negative_controls"]))
        self.assertFalse(report["interior_branch_refs"])
        self.assertTrue(all(len(ref["branches"]) == 16
                            for ref in report["external_references"].values()))


if __name__ == "__main__":
    unittest.main()
