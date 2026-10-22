import unittest
from pathlib import Path
from tools.build_check import compile_all_armv6k, find_clang


class TestArmv6kBuild(unittest.TestCase):
    def test_find_clang_exists(self):
        clang = find_clang()
        self.assertTrue(clang.exists(), f"Clang not found at {clang}")

    def test_all_translation_units_compile_to_armv6k(self):
        result = compile_all_armv6k(Path("."), Path("build/obj/armv6k"))
        self.assertGreaterEqual(result["total"], 68)
        self.assertEqual(
            result["failed"],
            [],
            f"Translation units failed ARMv6K compilation: {result['failed']}",
        )
        self.assertEqual(result["succeeded"], result["total"])


if __name__ == "__main__":
    unittest.main()
