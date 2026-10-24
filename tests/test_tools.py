import struct
import unittest
from pathlib import Path
from tools.split_asm import disassemble_function
from tools.inspect_assets import parse_tbb_header, parse_bf_header
from tests.fixtures import require_private_fixtures


def make_tbb_fixture() -> bytes:
    """Build a TBCR with deliberately non-sequential table offsets."""
    data = bytearray(0x70)
    data[:4] = b"TBCR"
    struct.pack_into("<II", data, 4, 0x20, 2)
    struct.pack_into("<II", data, 0x0C, 0x30, 0x00)

    # Table 0 appears second in the file: 10 payload bytes, 4-byte rows.
    struct.pack_into("<4I", data, 0x50, 0x314C4254, 10, 4, 0x10)
    data[0x60 : 0x6A] = b"0123456789"

    # Table 1 appears first: zero payload and a zero stride.
    struct.pack_into("<4I", data, 0x20, 0x314C4254, 0, 0, 0x10)
    return bytes(data)


class TestTbbParserSynthetic(unittest.TestCase):
    def test_uses_indexed_offsets_and_payload_stride_contract(self):
        info = parse_tbb_header(make_tbb_fixture())

        self.assertEqual(info["magic"], "TBCR")
        self.assertEqual(info["table_count"], 2)
        self.assertEqual(info["tables"][0]["offset"], 0x50)
        self.assertEqual(info["tables"][0]["payload_size"], 10)
        self.assertEqual(info["tables"][0]["row_stride"], 4)
        self.assertEqual(info["tables"][0]["row_count"], 2)
        self.assertEqual(info["tables"][1]["offset"], 0x20)
        self.assertEqual(info["tables"][1]["row_count"], 0)

    def test_rejects_invalid_container_and_subtable_ranges(self):
        with self.assertRaisesRegex(ValueError, "TBCR magic"):
            parse_tbb_header(b"NOPE" + bytes(32))

        bad_offsets = bytearray(make_tbb_fixture())
        struct.pack_into("<I", bad_offsets, 0x0C, 0xFFFFFFF0)
        with self.assertRaisesRegex(ValueError, "header 0 exceeds"):
            parse_tbb_header(bytes(bad_offsets))

        bad_payload = bytearray(make_tbb_fixture())
        struct.pack_into("<I", bad_payload, 0x54, 0x100)
        with self.assertRaisesRegex(ValueError, "payload 0 exceeds"):
            parse_tbb_header(bytes(bad_payload))


class TestDecompTools(unittest.TestCase):
    def test_disassemble_entrypoint(self):
        require_private_fixtures(self, "extracted/exefs/code.bin")
        code_bytes = Path("extracted/exefs/code.bin").read_bytes()
        asm_text = disassemble_function(
            code_bytes, 0x00100000, 0x24, {}, {0x00100000: "__start", 0x00100024: "__init_bss"}
        )
        self.assertIn(".global __start", asm_text)
        self.assertIn("0x00100000:", asm_text)
        self.assertIn("__init_bss", asm_text)

    def test_parse_tbb_and_bf_headers(self):
        require_private_fixtures(self, "extracted/romfs/saveLoadUI/SaveLoadUITable.tbb",
                                 "extracted/romfs/saveLoadUI/saveloadUI.bf")
        tbb_path = Path("extracted/romfs/saveLoadUI/SaveLoadUITable.tbb")
        tbb_info = parse_tbb_header(tbb_path.read_bytes())
        self.assertEqual(tbb_info["magic"], "TBCR")
        self.assertGreater(tbb_info["table_count"], 0)

        bf_path = Path("extracted/romfs/saveLoadUI/saveloadUI.bf")
        bf_info = parse_bf_header(bf_path.read_bytes())
        self.assertEqual(bf_info["magic"], "FLW0")
        self.assertGreater(bf_info["section_count"], 0)

    def test_disassemble_thumb_function(self):
        require_private_fixtures(self, "extracted/exefs/code.bin")
        code_bytes = Path("extracted/exefs/code.bin").read_bytes()
        asm_text = disassemble_function(
            code_bytes, 0x00100048, 0x2C, {}, {0x00100048: "crt_thumb_00100048"}, thumb=True
        )
        self.assertIn(".thumb", asm_text)
        self.assertIn("push", asm_text)

    def test_disassemble_thumb_trailing_halfwords(self):
        require_private_fixtures(self, "extracted/exefs/code.bin")
        code_bytes = Path("extracted/exefs/code.bin").read_bytes()
        asm_238 = disassemble_function(
            code_bytes, 0x00100238, 20, {}, {0x00100238: "thumb_func_00100238"}, thumb=True
        )
        self.assertIn(".thumb", asm_238)
        self.assertIn("0x00100238:", asm_238)

        asm_b44 = disassemble_function(
            code_bytes, 0x00100b44, 32, {}, {0x00100b44: "thumb_func_00100b44"}, thumb=True
        )
        self.assertIn(".thumb", asm_b44)
        self.assertIn("0x00100b44:", asm_b44)


if __name__ == "__main__":
    unittest.main()
