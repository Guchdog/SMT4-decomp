import hashlib
import json
import struct
import tempfile
import unittest
from unittest.mock import Mock
from pathlib import Path
from tools.extract import load_aes_keys, CIAExtractor, select_cia, verify_extracted_code
from tests.fixtures import require_private_fixtures


class TestExtractionInput(unittest.TestCase):
    def test_missing_and_ambiguous_cia_require_explicit_input(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaisesRegex(ValueError, "No CIA.*--cia"):
                select_cia(None, root)
            with self.assertRaisesRegex(ValueError, "does not exist"):
                select_cia(root / "missing.cia")
            one = root / "one.CIA"
            one.write_bytes(b"")
            self.assertEqual(select_cia(None, root), one)
            two = root / "two.cia"
            two.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "Multiple CIA.*--cia"):
                select_cia(None, root)
            self.assertEqual(select_cia(two, root), two)

    def _synthetic_extractor(self, code):
        ext = CIAExtractor.__new__(CIAExtractor)
        ext.product_code = "SYNTHETIC"
        ext.exefs_off = 0x1000
        exhdr = bytearray(0x800)
        exhdr[:8] = b"syntest\0"
        header = bytearray(0x200)
        header[:8] = b".code\0\0\0"
        struct.pack_into("<II", header, 8, 0, len(code))
        exefs = bytes(header) + code
        ext.exefs_size = len(exefs)
        ext.read_ncch_section = Mock(side_effect=[bytes(exhdr), exefs])
        return ext

    def test_valid_revision_is_written_and_mismatch_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            code = b"synthetic supported code"
            config = root / "game_info.json"
            config.write_text(json.dumps({
                "code_bin_size": len(code),
                "code_sha256": hashlib.sha256(code).hexdigest(),
            }), encoding="utf-8")
            output = root / "extracted"
            self._synthetic_extractor(code).extract_exefs(output, config)
            self.assertTrue(verify_extracted_code(output / "exefs/code.bin", config))
            original_info = (output / "exefs_info.json").read_bytes()
            bad_code = b"x" * len(code)
            with self.assertRaisesRegex(ValueError, "Verification FAILED"):
                self._synthetic_extractor(bad_code).extract_exefs(output, config)
            self.assertEqual((output / "exefs/code.bin").read_bytes(), code)
            self.assertEqual((output / "exefs_info.json").read_bytes(), original_info)
            with self.assertRaisesRegex(ValueError, "Verification FAILED"):
                self._synthetic_extractor(b"wrong size").extract_exefs(root / "new", config)
            self.assertFalse((root / "new").exists())


class TestExtract(unittest.TestCase):
    def test_load_aes_keys(self):
        require_private_fixtures(self, "aes_keys.txt")
        keys = load_aes_keys(Path("aes_keys.txt"))
        self.assertIn("slot0x2CKeyX", keys)
        self.assertIn("slot0x3DKeyX", keys)
        self.assertIn("common0", keys)
        self.assertEqual(len(keys["generator"]), 16)

    def test_extract_exefs_and_blz_page_alignment(self):
        require_private_fixtures(self, "aes_keys.txt")
        candidates = list(Path(".").glob("*.cia"))
        if len(candidates) != 1:
            self.skipTest("Private extraction test requires exactly one local CIA")
        cia = candidates[0]
        ext = CIAExtractor(cia, Path("aes_keys.txt"))
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)
            info = ext.extract_exefs(output)
            code_bytes = (output / "exefs/code.bin").read_bytes()
        # Page-aligned .text (0x2FF000) + page-aligned .rodata (0x2C000) + page-aligned .data (0x4C000) = 0x377000
        self.assertEqual(len(code_bytes), 0x377000)
        self.assertEqual(info["app_title"].strip(), "sdds4")

    def test_romfs_unaligned_file_extraction(self):
        require_private_fixtures(self, "aes_keys.txt")
        candidates = list(Path(".").glob("*.cia"))
        if len(candidates) != 1:
            self.skipTest("Private extraction test requires exactly one local CIA")
        cia = candidates[0]
        ext = CIAExtractor(cia, Path("aes_keys.txt"))
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)
            index = ext.build_romfs_index(output)
            self.assertEqual(len(index), 20126)
            count = ext.extract_romfs_files(output / "romfs", filter_dirs=["/saveLoadUI"])
            self.assertEqual(count, 3)
            tbb = (output / "romfs/saveLoadUI/SaveLoadUITable.tbb").read_bytes()
            self.assertEqual(tbb[:4], b"TBCR")

    def test_verify_code_sha256_check(self):
        require_private_fixtures(self, "extracted/exefs/code.bin")
        self.assertTrue(
            verify_extracted_code(
                Path("extracted/exefs/code.bin"), Path("config/game_info.json")
            )
        )


if __name__ == "__main__":
    unittest.main()
