import csv
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.build_check import compile_all_armv6k, find_clang, ensure_tu_armv6k, is_object_current, get_armv6k_flags


class TestArmv6kBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.clang = find_clang()
        except FileNotFoundError as error:
            raise unittest.SkipTest(str(error))

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

    def test_header_and_compiler_flags_invalidate_cached_object(self):
        with tempfile.TemporaryDirectory(prefix="smt4 build ") as tmp:
            root = Path(tmp)
            (root / "include").mkdir()
            header = root / "include" / "value.h"
            header.write_text("#define VALUE 1\n", encoding="utf-8")
            src = root / "value.cpp"
            src.write_text('#include "value.h"\nextern "C" int value() { return VALUE; }\n', encoding="utf-8")
            obj = root / "value.o"
            result = ensure_tu_armv6k(src, obj, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(is_object_current(src, obj, root))
            initial = obj.read_bytes()
            timestamp = header.stat()
            header.write_text("#define VALUE 2\n", encoding="utf-8")
            # Content changes must invalidate even if timestamps are unchanged.
            os.utime(header, ns=(timestamp.st_atime_ns, timestamp.st_mtime_ns))
            self.assertFalse(is_object_current(src, obj, root))
            self.assertEqual(ensure_tu_armv6k(src, obj, root).returncode, 0)
            self.assertNotEqual(obj.read_bytes(), initial)
            flags = get_armv6k_flags(root, self.clang)
            with patch("tools.build_check.get_armv6k_flags", return_value=flags + ["-DNEW_FLAG=1"]):
                self.assertFalse(is_object_current(src, obj, root))
            with patch("tools.build_check._compiler_version", return_value="changed compiler version"):
                self.assertFalse(is_object_current(src, obj, root))

    def test_failed_header_rebuild_does_not_reuse_previous_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "include").mkdir()
            header = root / "include" / "value.h"
            header.write_text("#define VALUE 1\n", encoding="utf-8")
            src = root / "value.cpp"
            src.write_text('#include "value.h"\nint value() { return VALUE; }\n', encoding="utf-8")
            obj = root / "value.o"
            self.assertEqual(ensure_tu_armv6k(src, obj, root).returncode, 0)
            header.write_text("#error invalid header\n", encoding="utf-8")
            result = ensure_tu_armv6k(src, obj, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(obj.exists())
            self.assertFalse(is_object_current(src, obj, root))

    def test_cmake_arm_build_and_matching_objects(self):
        def find_tool(name):
            found = shutil.which(name)
            if found:
                return found
            sibling = self.clang.parent / (name + (".exe" if os.name == "nt" else ""))
            return str(sibling) if sibling.is_file() else None

        cmake, ninja = find_tool("cmake"), find_tool("ninja")
        if not cmake or not ninja:
            self.skipTest("CMake and Ninja are required for the CMake integration test")
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="smt4-cmake-") as tmp:
            build = Path(tmp)
            configure = subprocess.run([
                cmake, "-S", str(root), "-B", str(build), "-G", "Ninja",
                f"-DCMAKE_TOOLCHAIN_FILE={root / 'cmake' / 'armv6k-clang.cmake'}",
                f"-DCMAKE_CXX_COMPILER={self.clang}", f"-DCMAKE_MAKE_PROGRAM={ninja}",
            ], capture_output=True, text=True)
            self.assertEqual(configure.returncode, 0, configure.stdout + configure.stderr)
            result = subprocess.run([cmake, "--build", str(build)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            code_path = root / "extracted" / "exefs" / "code.bin"
            if code_path.is_file() and os.environ.get("SMT4_SKIP_PRIVATE_TESTS") != "1":
                from tools.asm_diff import (
                    extract_elf_functions_detailed,
                    find_symbol_in_elf,
                    normalize_resolved_arm_calls,
                )
                code = code_path.read_bytes()
                with (root / "config" / "functions.csv").open(encoding="utf-8") as ledger:
                    matches = [r for r in csv.DictReader(ledger) if r["status"] == "matching"]
                self.assertGreater(len(matches), 0)
                for row in matches:
                    objects = list(build.rglob(Path(row["src_file"]).name + ".o"))
                    objects += list(build.rglob(Path(row["src_file"]).name + ".obj"))
                    self.assertEqual(len(objects), 1, row["src_file"])
                    address = int(row["address"], 16)
                    symbol = find_symbol_in_elf(
                        extract_elf_functions_detailed(objects[0]), row["name"], address
                    )
                    self.assertIsNotNone(symbol, row["name"])
                    actual, relocations = symbol
                    offset, size = int(row["address"], 16) - 0x100000, int(row["size"])
                    expected = code[offset:offset + size]
                    normalized = normalize_resolved_arm_calls(
                        actual,
                        relocations,
                        expected,
                        address,
                        root / "config" / "functions.csv",
                    )
                    self.assertIsNotNone(normalized, row["name"])
                    self.assertEqual(normalized, expected, row["name"])


if __name__ == "__main__":
    unittest.main()
