import csv
import tempfile
import unittest
from pathlib import Path

import capstone

from tools.find_candidates import find_leaf_candidates, is_terminal_return


class TestFindCandidates(unittest.TestCase):
    def test_terminal_return_recognizes_common_arm_and_thumb_epilogues(self):
        samples = (
            (capstone.CS_MODE_ARM, bytes.fromhex("1eff2fe1")),  # bx lr
            (capstone.CS_MODE_ARM, bytes.fromhex("0ef0a0e1")),  # mov pc, lr
            (capstone.CS_MODE_ARM, bytes.fromhex("0080bde8")),  # ldm sp!, {pc}
            (capstone.CS_MODE_THUMB, bytes.fromhex("7047")),  # bx lr
            (capstone.CS_MODE_THUMB, bytes.fromhex("00bd")),  # pop {pc}
        )

        for mode, raw in samples:
            with self.subTest(mode=mode, raw=raw.hex()):
                decoder = capstone.Cs(capstone.CS_ARCH_ARM, mode)
                insn = next(iter(decoder.disasm(raw, 0x00102000)))
                self.assertTrue(is_terminal_return(insn))

    def test_terminal_return_rejects_padding_and_conditional_return(self):
        decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
        for raw in (bytes.fromhex("0000a0e1"), bytes.fromhex("1eff2f01")):
            with self.subTest(raw=raw.hex()):
                insn = next(iter(decoder.disasm(raw, 0x00102000)))
                self.assertFalse(is_terminal_return(insn))

    def test_candidate_range_must_end_in_unconditional_return(self):
        base = 0x00101308
        code = bytearray(base - 0x00100000)
        rows = (
            (base, 4, "empty_return"),
            (base + 4, 4, "padding_word"),
            (base + 8, 8, "conditional_fallthrough"),
            (base + 16, 8, "constant_return"),
        )
        code.extend(bytes.fromhex("1eff2fe1"))  # bx lr
        code.extend(bytes.fromhex("0000a0e1"))  # mov r0, r0
        code.extend(bytes.fromhex("000050e31eff2f01"))  # cmp r0, #0; bxeq lr
        code.extend(bytes.fromhex("0100a0e31eff2fe1"))  # mov r0, #1; bx lr

        with tempfile.TemporaryDirectory() as temp_dir:
            functions = Path(temp_dir) / "functions.csv"
            with functions.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(
                    ("address", "size", "status", "category", "name", "src_file")
                )
                for address, size, name in rows:
                    writer.writerow(
                        (f"0x{address:08x}", size, "todo", "test", name, "")
                    )

            candidates = find_leaf_candidates(
                functions_csv=functions,
                code_bytes=bytes(code),
                max_size=8,
                limit=0,
            )

        self.assertEqual(
            [candidate["name"] for candidate in candidates],
            ["empty_return", "constant_return"],
        )
        self.assertEqual(candidates[0]["terminal_instruction"], "bx lr")


if __name__ == "__main__":
    unittest.main()
