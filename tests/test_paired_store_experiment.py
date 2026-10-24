import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.paired_store_experiment import (
    ALL_ADDRESSES, CALLERS, ROOT, caller_inventory, run, verify_reference,
)


class TestPairedStoreExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            import csv
            cls.rows = list(csv.DictReader(stream))

    def test_pinned_shapes_and_all_static_callers(self):
        specs = verify_reference(self.image, self.game["code_sha256"], self.rows)
        self.assertEqual({spec.address for spec in specs}, set(ALL_ADDRESSES))
        self.assertEqual({spec.address: spec.offset for spec in specs}, {
            0x00158784: 0x84,
            0x0023347C: 0x40,
            0x00292E88: 0x40,
        })
        inventory = caller_inventory(self.rows)["calls"]
        counts = {hex(address): sum(call["target"] == hex(address) for call in inventory)
                  for address in ALL_ADDRESSES}
        self.assertEqual(counts, {hex(address): len(calls)
                                  for address, calls in CALLERS.items()})
        self.assertEqual(sum(counts.values()), 26)

    def test_reference_hash_and_instruction_changes_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, "0" * 64, self.rows)
        changed = bytearray(self.image)
        changed[ALL_ADDRESSES[0] - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Original instruction sequence changed"):
            verify_reference(bytes(changed), hashlib.sha256(changed).hexdigest(), self.rows)

    def test_candidates_and_negative_controls_on_two_seeds(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                              samples=1, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(len(report["functions"]), 3)
            self.assertTrue(all(item["passed"] for item in report["functions"]))
            self.assertEqual(sum(item["cases"] for item in report["functions"]), 15)
            self.assertEqual(len(report["negative_controls"]), 3)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
