import unittest
from pathlib import Path
from tools.analyze_code import analyze_binary, vaddr_to_offset
from tests.fixtures import require_private_fixtures


class TestAnalyzeCode(unittest.TestCase):
    def test_vaddr_to_offset_mapping(self):
        self.assertEqual(vaddr_to_offset(0x00100000), 0x0)
        self.assertEqual(vaddr_to_offset(0x003FF000), 0x2FF000)
        self.assertEqual(vaddr_to_offset(0x0042B000), 0x32B000)

    def test_contiguous_text_coverage_and_literal_pool_exclusion(self):
        require_private_fixtures(self, "extracted/exefs/code.bin")
        funcs, symbols = analyze_binary(
            Path("extracted/exefs/code.bin"), Path("config/game_info.json"), write_csv=False
        )
        self.assertGreater(len(funcs), 5000)
        # First function is entrypoint __start at 0x00100000
        self.assertEqual(funcs[0]["address"], "0x00100000")
        self.assertEqual(funcs[0]["name"], "__start")
        # Sum of all function sizes must equal exact .text size (0x2FE624 = 3,139,108 bytes) with zero overlaps/gaps
        total_size = sum(int(f["size"]) for f in funcs)
        self.assertEqual(total_size, 0x2FE624)
        # Ensure subsystems like ui, battle, camp, script_vm are discovered via .rodata string xrefs
        categories = {f["category"] for f in funcs}
        for expected_cat in ("crt", "ui", "battle", "camp", "script_vm", "nn_sdk"):
            self.assertIn(expected_cat, categories)

    def test_vldr_float_pools_and_thumb_crt_not_misidentified_as_bl(self):
        require_private_fixtures(self, "extracted/exefs/code.bin")
        funcs, _ = analyze_binary(
            Path("extracted/exefs/code.bin"), Path("config/game_info.json"), write_csv=False
        )
        addrs = {int(f["address"], 16) for f in funcs}
        # Bogus functions caused by VLDR float constants (0x4b000000) and Thumb pairs (0x00100fa8) must not exist
        for bogus_addr in (0x00282750, 0x00282918, 0x002885A8, 0x002919D0, 0x003EB4C8, 0x0011C548):
            self.assertNotIn(bogus_addr, addrs, f"Bogus float/Thumb target 0x{bogus_addr:08x} in functions")


if __name__ == "__main__":
    unittest.main()
