from __future__ import annotations

import unittest

from tools.h2_pair_fill_production_patch import (
    ADDRESS, ORIGINAL, audit_interior_references, validate_body,
)


class H2PairFillProductionPatchTests(unittest.TestCase):
    def test_accepts_six_instruction_body_in_original_slot(self):
        body = bytes.fromhex("7110efe6011481e1011881e1001080e5041080e51eff2fe1")
        result = validate_body(body)
        self.assertEqual(result["size"], 24)
        self.assertEqual(result["instructions"][-1]["mnemonic"], "bx")
        self.assertEqual(int(result["instructions"][0]["address"], 16), ADDRESS)

    def test_rejects_body_outside_original_slot(self):
        with self.assertRaisesRegex(ValueError, "original 24-byte slot"):
            validate_body(bytes(28))

    def test_rejects_unreviewed_instruction_layout(self):
        body = bytes.fromhex("ff1001e2011481e1011881e1001080e5041080e51eff2fe1")
        with self.assertRaisesRegex(ValueError, "reviewed six-instruction body"):
            validate_body(body)

    def test_original_has_no_covered_interior_entries(self):
        report = audit_interior_references(ORIGINAL.read_bytes())
        self.assertEqual(report["direct_branch_interior_hits"], [])
        self.assertEqual(report["aligned_absolute_pointer_interior_hits"], [])


if __name__ == "__main__":
    unittest.main()
