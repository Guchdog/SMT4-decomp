import unittest
from pathlib import Path
from tools.extract import decompress_blz, load_aes_keys, CIAExtractor


class TestExtract(unittest.TestCase):
    def test_load_aes_keys(self):
        keys = load_aes_keys(Path("aes_keys.txt"))
        self.assertIn("slot0x2CKeyX", keys)
        self.assertIn("slot0x3DKeyX", keys)
        self.assertIn("common0", keys)
        self.assertEqual(len(keys["generator"]), 16)

    def test_extract_exefs_and_blz_page_alignment(self):
        cia = next(Path(".").glob("*.cia"))
        ext = CIAExtractor(cia, Path("aes_keys.txt"))
        info = ext.extract_exefs(Path("extracted"))
        code_bytes = Path("extracted/exefs/code.bin").read_bytes()
        # Page-aligned .text (0x2FF000) + page-aligned .rodata (0x2C000) + page-aligned .data (0x4C000) = 0x377000
        self.assertEqual(len(code_bytes), 0x377000)
        self.assertEqual(info["app_title"].strip(), "sdds4")

    def test_romfs_unaligned_file_extraction(self):
        cia = next(Path(".").glob("*.cia"))
        ext = CIAExtractor(cia, Path("aes_keys.txt"))
        index = ext.build_romfs_index(Path("extracted"))
        self.assertEqual(len(index), 20126)
        count = ext.extract_romfs_files(Path("extracted/romfs"), filter_dirs=["/saveLoadUI"])
        self.assertEqual(count, 3)
        tbb = Path("extracted/romfs/saveLoadUI/SaveLoadUITable.tbb").read_bytes()
        self.assertEqual(tbb[:4], b"TBCR")

    def test_verify_code_sha256_check(self):
        from tools.extract import verify_extracted_code
        self.assertTrue(
            verify_extracted_code(
                Path("extracted/exefs/code.bin"), Path("config/game_info.json")
            )
        )


if __name__ == "__main__":
    unittest.main()
