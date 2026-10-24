import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.field_roundtrip_predicate_experiment import ROOT, SEEDS, SPECS, make_cases, run, verify_reference


class TestFieldRoundtripPredicatePins(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        import csv
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            cls.rows = list(csv.DictReader(stream))

    def test_selected_function_bytes_are_pinned(self):
        result = verify_reference(self.image, self.rows, self.game["code_sha256"])
        self.assertEqual(set(result["functions"]), {hex(a) for a in SPECS})
        for address, spec in SPECS.items():
            self.assertEqual(result["functions"][hex(address)]["sha256"], spec["sha256"])

    def test_modified_image_is_rejected(self):
        changed = bytearray(self.image)
        changed[next(iter(SPECS)) - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(bytes(changed), self.rows, hashlib.sha256(changed).hexdigest())

    def test_value_streams_cover_boundaries_and_seed_deterministically(self):
        for address in SPECS:
            a = list(make_cases(address, SEEDS[0], 12))
            b = list(make_cases(address, SEEDS[1], 12))
            if address == 0x00146D10:
                self.assertEqual(len(a), 268)
            else:
                self.assertEqual(len(a), 17 if address == 0x00146CE0 else 19)
            self.assertNotEqual([case.data for case in a[:12]], [case.data for case in b[:12]])

    def test_differential_controls_and_faults_for_two_seeds(self):
        for seed in SEEDS:
            with tempfile.TemporaryDirectory(prefix="smt4-field-roundtrip-predicate-") as directory:
                report = run(ROOT / "extracted/exefs/code.bin", Path(directory), seed=seed, samples=64)
            self.assertTrue(report["passed"], report)
            self.assertEqual(sum(f["comparisons"] for f in report["functions"]), 3 * 64 + 268)
            self.assertTrue(all(control["detected"] for control in report["negative_controls"]))
            self.assertTrue(all(fault["faults_match"] and fault["partial_write_parity"]
                                for fault in report["fault_probes"]))
            self.assertTrue(all(not callers for callers in report["direct_bl_callers"].values()))


if __name__ == "__main__":
    unittest.main()
