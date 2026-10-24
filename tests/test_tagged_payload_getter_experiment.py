import csv
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from tools.semantic_experiment import DATA
from tools.tagged_payload_getter_experiment import (
    FUNCTIONS,
    ROOT,
    make_cases,
    run,
    verify_reference,
)


class TestTaggedPayloadGetterPins(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads(
            (ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        with (ROOT / "config/functions.csv").open(
                encoding="utf-8", newline="") as stream:
            cls.ledger = list(csv.DictReader(stream))

    def test_functions_and_direct_call_sites_are_pinned(self):
        report = verify_reference(self.image, self.game, self.ledger)
        self.assertEqual(set(report["functions"]),
                         {hex(address) for address in FUNCTIONS})
        self.assertEqual(report["functions"]["0x3e6974"]["tag"], "0x300")
        self.assertEqual(report["functions"]["0x3e69a8"]["tag"], "0x4100")
        self.assertEqual(report["callers"]["0x3e6974"]["callsite"], "0x3e71e4")
        self.assertEqual(report["callers"]["0x3e69a8"]["callsite"], "0x3e7104")
        self.assertIn("static direct-BL", report["callers"]["0x3e6974"]["scope"])

    def test_reference_fails_closed_on_hash_or_function_byte_drift(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, self.game | {"code_sha256": "0" * 64},
                             self.ledger)
        changed = bytearray(self.image)
        changed[0x003E6974 - 0x00100000] ^= 1
        changed = bytes(changed)
        game = self.game | {"code_sha256": hashlib.sha256(changed).hexdigest()}
        with self.assertRaisesRegex(ValueError, "original bytes differ"):
            verify_reference(changed, game, self.ledger)


class TestTaggedPayloadGetterCases(unittest.TestCase):
    def test_boundary_cases_include_zero_offset_and_wrong_tags(self):
        for address, spec in FUNCTIONS.items():
            cases = make_cases(address, seed=7, samples=5)
            self.assertEqual(len(cases), 13)
            by_label = {case.label: case for case in cases}
            zero = by_label["valid-offset-zero"]
            base = zero.registers[0]
            self.assertEqual(struct.unpack_from("<H", zero.data, base - DATA)[0],
                             spec["tag"])
            self.assertEqual(struct.unpack_from("<I", zero.data,
                                                base - DATA + 4)[0], 0)
            self.assertEqual(struct.unpack_from("<I", zero.data,
                                                base - DATA + 8)[0], 0x87654321)
            self.assertEqual(by_label["wrong-tag-zero"].registers[0], base)
            self.assertEqual(struct.unpack_from(
                "<H", by_label["wrong-tag-adjacent"].data,
                by_label["wrong-tag-adjacent"].registers[0] - DATA)[0],
                (spec["tag"] + 1) & 0xFFFF)

    def test_candidates_differential_cases_controls_and_null_faults(self):
        with tempfile.TemporaryDirectory(prefix="smt4-tagged-payload-getters-") as temp:
            report = run(ROOT / "extracted/exefs/code.bin", Path(temp),
                         seed=7, samples=24)
        self.assertTrue(report["passed"])
        self.assertEqual(report["function_comparison_count"], 64)
        self.assertEqual(len(report["candidate_functions"]), 2)
        self.assertTrue(all(item["passed"] and item["case_count"] == 32
                            for item in report["candidate_functions"]))
        self.assertTrue(all(item["byte_identical"] is False
                            for item in report["candidate_functions"]))
        self.assertEqual(len(report["negative_controls"]), 4)
        self.assertEqual({item["control"] for item in report["negative_controls"]},
                         {"wrong_tag", "wrong_offset"})
        self.assertTrue(all(item["detected"]
                            for item in report["negative_controls"]))
        self.assertEqual(len(report["null_faults"]), 2)
        self.assertTrue(all(item["passed"] for item in report["null_faults"]))
        self.assertIn("null is outside", report["observed_contract"]["valid_base_precondition"])


if __name__ == "__main__":
    unittest.main()
