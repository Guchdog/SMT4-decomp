import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.semantic_experiment import DATA
from tools.singleton_integer_leaves_experiment import (
    ROOT, SEEDS, SPECS, make_cases, run, verify_reference,
)


class TestSingletonIntegerLeafPins(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        import csv
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            cls.rows = list(csv.DictReader(stream))

    def test_selected_function_bytes_are_pinned(self):
        report = verify_reference(self.image, self.rows, self.game["code_sha256"])
        self.assertEqual(set(report["functions"]), {hex(a) for a in SPECS})
        for address, spec in SPECS.items():
            self.assertEqual(report["functions"][hex(address)]["sha256"], spec["sha256"])

    def test_modified_image_is_rejected(self):
        changed = bytearray(self.image)
        address = next(iter(SPECS))
        changed[address - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(bytes(changed), self.rows, hashlib.sha256(changed).hexdigest())

    def test_random_streams_are_seeded_and_address_specific(self):
        for address in SPECS:
            first = list(make_cases(address, SEEDS[0], 8))
            second = list(make_cases(address, SEEDS[1], 8))
            self.assertEqual(len(first), 8 + (7 if address == 0x00130FE8 else
                                               5 if address == 0x0015C408 else 8))
            self.assertNotEqual([case.data for case in first], [case.data for case in second])
        self.assertGreater(DATA, 0)

    def test_differential_results_controls_and_fault_probes_for_two_seeds(self):
        for seed in SEEDS:
            with tempfile.TemporaryDirectory(prefix="smt4-singleton-integer-leaves-") as directory:
                report = run(ROOT / "extracted/exefs/code.bin", Path(directory), seed=seed, samples=64)
            self.assertTrue(report["passed"], report)
            self.assertEqual(sum(f["comparisons"] for f in report["functions"]), 3 * 64 + 20)
            self.assertTrue(all(c["detected"] for c in report["negative_controls"]))
            self.assertEqual(len(report["fault_probes"]), 2)
            self.assertTrue(all(f["faults_match"] and f["partial_write_parity"]
                                for f in report["fault_probes"]))
            self.assertTrue(all(not calls for calls in report["direct_bl_callers"].values()))


if __name__ == "__main__":
    unittest.main()
