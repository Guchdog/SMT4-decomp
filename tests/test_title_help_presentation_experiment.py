import hashlib
import struct
import unittest

from tools.semantic_experiment import DATA
from tools.title_help_presentation_experiment import (
    EXPECTED_HELP, ROOT, extract_help_entries, make_case,
    run_presentation_window,
)


class TestTitleHelpAsset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb"
        cls.raw = cls.path.read_bytes()

    def test_real_asset_contains_the_four_expected_help_strings(self):
        info = extract_help_entries(self.raw)
        self.assertEqual(tuple(row["text"] for row in info["entries"]), EXPECTED_HELP)
        self.assertEqual(info["payload_size"], 344)
        self.assertEqual(info["entries"][-1]["relative_payload_offset"], 0x118)

    def test_selection_case_stores_work_plus_eight_without_mutating_asset(self):
        before = hashlib.sha256(self.raw).hexdigest()
        for index in range(4):
            case = make_case(self.raw, index, seed=7)
            work = case.registers[5] - DATA
            self.assertEqual(struct.unpack_from("<I", case.data, work + 8)[0], index)
            self.assertEqual(case.data[0x100:0x100 + len(self.raw)], self.raw)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), before)
        with self.assertRaisesRegex(ValueError, "0..3"):
            make_case(self.raw, 4, seed=7)


class TestTitleHelpArmPresentationWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = ROOT / "extracted/exefs/code.bin"
        cls.tbb = ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb"

    def test_original_arm_selects_each_real_help_string_and_call_color(self):
        report = run_presentation_window(self.code, self.tbb, seed=20261024)
        self.assertTrue(report["passed"])
        self.assertEqual(tuple(row["text"] for row in report["selections"]), EXPECTED_HELP)
        self.assertTrue(all(row["passed"] for row in report["selections"]))
        self.assertTrue(all(row["rgba_argument"] == "0x323232ff"
                            for row in report["selections"]))
        self.assertEqual(report["stop_before_call"], "0x1ea15c")
        self.assertIn("no emulator/runtime observation", report["evidence_type"])


if __name__ == "__main__":
    unittest.main()
