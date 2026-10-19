import unittest
from pathlib import Path
from tools.split_asm import disassemble_function
from tools.inspect_assets import parse_tbb_header, parse_bf_header


class TestDecompTools(unittest.TestCase):
    def test_disassemble_entrypoint(self):
        code_bytes = Path("extracted/exefs/code.bin").read_bytes()
        asm_text = disassemble_function(
            code_bytes, 0x00100000, 0x24, {}, {0x00100000: "__start", 0x00100024: "__init_bss"}
        )
        self.assertIn(".global __start", asm_text)
        self.assertIn("0x00100000:", asm_text)
        self.assertIn("__init_bss", asm_text)

    def test_parse_tbb_and_bf_headers(self):
        tbb_path = Path("extracted/romfs/saveLoadUI/SaveLoadUITable.tbb")
        tbb_info = parse_tbb_header(tbb_path.read_bytes())
        self.assertEqual(tbb_info["magic"], "TBCR")
        self.assertGreater(tbb_info["table_count"], 0)

        bf_path = Path("extracted/romfs/saveLoadUI/saveloadUI.bf")
        bf_info = parse_bf_header(bf_path.read_bytes())
        self.assertEqual(bf_info["magic"], "FLW0")
        self.assertGreater(bf_info["section_count"], 0)

    def test_disassemble_thumb_function(self):
        code_bytes = Path("extracted/exefs/code.bin").read_bytes()
        asm_text = disassemble_function(
            code_bytes, 0x00100048, 0x2C, {}, {0x00100048: "crt_thumb_00100048"}, thumb=True
        )
        self.assertIn(".thumb", asm_text)
        self.assertIn("push", asm_text)


if __name__ == "__main__":
    unittest.main()
