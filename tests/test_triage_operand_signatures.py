import struct
import tempfile
import unittest
from pathlib import Path

from tools.triage_operand_signatures import (
    _decoder, find_known_candidate_addresses, group_operand_shapes,
    normalized_instruction,
)


TEXT = 0x00100000


def arm_word(value):
    return struct.pack("<I", value)


class TestOperandSignatureTriage(unittest.TestCase):
    def test_normalizes_registers_and_immediates_but_keeps_addressing_and_cc(self):
        image = bytearray(0x60)
        functions = [
            # add r0,r0,#1; bx lr
            (TEXT + 0x00, arm_word(0xE2800001) + arm_word(0xE12FFF1E)),
            # add r4,r4,#9; bx lr (same shape, different registers/immediate)
            (TEXT + 0x08, arm_word(0xE2844009) + arm_word(0xE12FFF1E)),
            # ldr r0,[r1,#4]; bx lr
            (TEXT + 0x10, arm_word(0xE5910004) + arm_word(0xE12FFF1E)),
            # ldr r0,[r1,r2]; bx lr (different addressing shape)
            (TEXT + 0x18, arm_word(0xE7910002) + arm_word(0xE12FFF1E)),
            # moveq r0,#0; bx lr (condition is part of the shape)
            (TEXT + 0x20, arm_word(0x03A00000) + arm_word(0xE12FFF1E)),
            # mov r0,#0; bx lr
            (TEXT + 0x28, arm_word(0xE3A00000) + arm_word(0xE12FFF1E)),
        ]
        for address, body in functions:
            start = address - TEXT
            image[start:start + len(body)] = body
        candidates = [
            {"address": f"0x{address:08x}", "size": len(body), "name": f"f{index}"}
            for index, (address, body) in enumerate(functions)
        ]

        report = group_operand_shapes(candidates, bytes(image))
        groups_by_first = {group["signature"][0].split("[", 1)[0]: group
                           for group in report["groups"]}

        self.assertEqual(report["decoded_integer_leaf_count"], 6)
        self.assertEqual(report["repeated_candidate_count"], 2)
        self.assertEqual(groups_by_first["add"]["count"], 2)
        self.assertIn("imm", groups_by_first["add"]["signature"][0])
        self.assertNotIn("ldr", groups_by_first)
        decoder = _decoder(TEXT)
        conditional, unconditional = list(decoder.disasm(
            arm_word(0x03A00000) + arm_word(0xE3A00000), TEXT))
        self.assertIn("[eq;", normalized_instruction(conditional))
        self.assertIn("[al;", normalized_instruction(unconditional))
        self.assertTrue(any("suggestions only" in item.lower()
                            for item in report["limitations"]))

    def test_known_symbol_scan_is_recursive_strict_and_deduplicated(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "one_candidate.cpp").write_text(
                "void candidate_0012aBcD();\nvoid negative_candidate_abcdef01();\n",
                encoding="utf-8",
            )
            nested = root / "nested"
            nested.mkdir()
            (nested / "more_candidates.cpp").write_text(
                "auto candidate_0012abcd() -> void;\n"
                "auto candidate_1234567() -> void;\n"
                "auto candidate_123456789() -> void;\n",
                encoding="utf-8",
            )
            (root / "ignored.cpp").write_text(
                "void candidate_ffffffff();\n", encoding="utf-8")

            addresses = find_known_candidate_addresses(root)

        self.assertEqual(addresses, {"0012abcd"})

    def test_coverage_annotation_partitions_group_without_filtering(self):
        image = bytearray(0x20)
        functions = [
            (TEXT, arm_word(0xE2800001) + arm_word(0xE12FFF1E)),
            (TEXT + 8, arm_word(0xE2844009) + arm_word(0xE12FFF1E)),
        ]
        for address, body in functions:
            image[address - TEXT:address - TEXT + len(body)] = body
        candidates = [
            {"address": f"0x{address:08x}", "size": len(body)}
            for address, body in functions
        ]

        report = group_operand_shapes(candidates, bytes(image), {"00100000"})

        group = report["groups"][0]
        self.assertEqual(group["count"], 2)
        self.assertEqual(group["covered_candidates"], ["0x00100000"])
        self.assertEqual(group["uncovered_candidates"], ["0x00100008"])
        self.assertEqual(len(group["candidates"]), 2)

    def test_coverage_is_unchecked_when_no_directory_was_supplied(self):
        image = bytearray(0x10)
        bodies = [arm_word(0xE2800001) + arm_word(0xE12FFF1E),
                  arm_word(0xE2844009) + arm_word(0xE12FFF1E)]
        candidates = []
        for index, body in enumerate(bodies):
            address = TEXT + index * 8
            image[index * 8:index * 8 + len(body)] = body
            candidates.append({"address": f"0x{address:08x}", "size": len(body)})

        report = group_operand_shapes(candidates, bytes(image))

        self.assertIsNone(report["groups"][0]["covered_candidates"])
        self.assertIsNone(report["groups"][0]["uncovered_candidates"])

    def test_thumb_leaves_are_disassembled_as_thumb(self):
        image = bytearray(0x60)
        functions = [
            (0x00100048, bytes.fromhex("01207047")),  # movs r0,#1; bx lr
            (0x0010004C, bytes.fromhex("08217047")),  # movs r1,#8; bx lr
        ]
        for address, body in functions:
            start = address - TEXT
            image[start:start + len(body)] = body
        candidates = [
            {"address": f"0x{address:08x}", "size": len(body)}
            for address, body in functions
        ]

        report = group_operand_shapes(candidates, bytes(image))

        self.assertEqual(report["decoded_integer_leaf_count"], 2)
        self.assertEqual(report["groups"][0]["count"], 2)
        self.assertTrue(all(item["mode"] == "thumb"
                            for item in report["groups"][0]["candidates"]))


if __name__ == "__main__":
    unittest.main()
