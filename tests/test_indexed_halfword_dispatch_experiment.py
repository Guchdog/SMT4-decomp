import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.indexed_halfword_dispatch_experiment import (
    ADDRESSES, ROOT, make_cases, run, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestIndexedHalfwordDispatchReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )
        cls.image, cls.game, cls.ledger = pinned.image, pinned.game_info, pinned.ledger

    def test_exact_function_words_and_revision_are_pinned(self):
        report = verify_reference(self.image, self.game, self.ledger)
        self.assertEqual(set(int(address, 16) for address in report["functions"]), set(ADDRESSES))
        self.assertEqual(report["functions"]["0x1dc648"]["observed"]["return"],
                         "r0=1; r4/r5 and SP restored")
        changed = bytearray(self.image)
        changed[0x001DC648 - 0x00100000] ^= 1
        changed_game = {**self.game, "code_sha256": hashlib.sha256(changed).hexdigest()}
        with self.assertRaisesRegex(ValueError, "Pinned instruction words changed"):
            verify_reference(bytes(changed), changed_game, self.ledger)

    def test_order_sensitive_aliases_are_present(self):
        for address in ADDRESSES:
            labels = [case.label for case in make_cases(address, 19, samples=0)]
            self.assertIn("alias-output-slot-overwrites-input-cursor", labels)
            self.assertIn("alias-output-slot-overwrites-output-cursor", labels)


class TestIndexedHalfwordDispatchExperiment(unittest.TestCase):
    def test_two_seed_differential_runs_aliases_faults_and_negative_controls(self):
        for seed in (20261024, 0x5A17):
            with tempfile.TemporaryDirectory(prefix=f"smt4-halfword-dispatch-{seed}-") as temp:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temp), seed, samples=16)
                disk = json.loads((Path(temp) / "report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["passed"], seed)
            self.assertTrue(disk["passed"])
            self.assertEqual(len(report["functions"]), 2)
            self.assertTrue(all(row["passed"] and row["cases"] == 22
                                for row in report["functions"]))
            self.assertEqual(len(report["fault_probes"]), 6)
            self.assertTrue(all(row["passed"] and row["both_faulted"]
                                for row in report["fault_probes"]))
            self.assertEqual(len(report["negative_controls"]), 4)
            self.assertTrue(all(row["detected"] for row in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
