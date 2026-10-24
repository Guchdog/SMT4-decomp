import unittest

from tools.group_candidate_signatures import group_candidates_by_mnemonics


class TestCandidateSignatures(unittest.TestCase):
    def test_groups_opcode_sequences_without_claiming_operand_equivalence(self):
        base = 0x00101300
        code = bytearray(base - 0x00100000)
        code.extend(bytes.fromhex("0100a0e31eff2fe1"))  # mov r0, #1; bx lr
        code.extend(bytes.fromhex("0200a0e31eff2fe1"))  # mov r0, #2; bx lr
        code.extend(bytes.fromhex("000091e51eff2fe1"))  # ldr r0, [r1]; bx lr
        candidates = [
            {"address": f"0x{base:08x}", "size": 8, "name": "one"},
            {"address": f"0x{base + 8:08x}", "size": 8, "name": "two"},
            {"address": f"0x{base + 16:08x}", "size": 8, "name": "load"},
        ]

        report = group_candidates_by_mnemonics(candidates, bytes(code))

        self.assertEqual(report["candidate_count"], 3)
        self.assertEqual(report["unique_signatures"], 2)
        self.assertEqual(report["repeated_signature_count"], 1)
        group = report["groups"][0]
        self.assertEqual(group["mnemonics"], ["mov", "bx"])
        self.assertEqual(group["count"], 2)
        self.assertNotEqual(
            group["candidates"][0]["instructions"],
            group["candidates"][1]["instructions"],
        )


if __name__ == "__main__":
    unittest.main()
