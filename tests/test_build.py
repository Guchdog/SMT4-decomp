import csv
import os
import shutil
import subprocess
import tempfile
import threading
import io
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch
from tools.build_check import (compile_all_armv6k, default_job_count, main,
    find_clang, ensure_tu_armv6k, is_object_current, get_armv6k_flags)


class TestBuildScheduling(unittest.TestCase):
    def test_parallel_jobs_overlap_keep_distinct_paths_and_report_failures(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            for name in ("a/shared.cpp", "b/shared.cpp", "c/bad.cpp"):
                source = root / "src" / name
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text("// fixture\n")
            barrier = threading.Barrier(2, timeout=10)
            threads = set()
            lock = threading.Lock()

            def compile_fake(source, output, repo_root, force):
                self.assertEqual(repo_root, root)
                self.assertTrue(force)
                if source.name == "bad.cpp":
                    return subprocess.CompletedProcess([], 1, "", "intentional failure")
                with lock:
                    threads.add(threading.get_ident())
                barrier.wait()
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"object")
                return subprocess.CompletedProcess(["clang", str(source)], 0, "", "")

            with patch("tools.build_check.ensure_tu_armv6k", side_effect=compile_fake):
                result = compile_all_armv6k(root, force=True, jobs=2)
            self.assertEqual(len(threads), 2)
            self.assertEqual(result["jobs"], 2)
            self.assertEqual(result["succeeded"], 2)
            self.assertEqual(result["compiled_count"], 2)
            self.assertEqual(result["cached_count"], 0)
            self.assertEqual(result["failed"], [("src/c/bad.cpp", "intentional failure")])
            self.assertEqual(result["objects"]["src/a/shared.cpp"], root / "build/obj/armv6k/a/shared.o")
            self.assertEqual(result["objects"]["src/b/shared.cpp"], root / "build/obj/armv6k/b/shared.o")
            self.assertNotIn("src/c/bad.cpp", result["objects"])

    def test_job_selection_empty_tree_and_invalid_counts(self):
        with patch("tools.build_check.os.process_cpu_count", return_value=8, create=True):
            self.assertEqual(default_job_count(), 8)
        with patch("tools.build_check.os.process_cpu_count", return_value=None, create=True):
            self.assertEqual(default_job_count(), 1)
        with tempfile.TemporaryDirectory() as temp:
            result = compile_all_armv6k(Path(temp), jobs=8)
            self.assertEqual(result["total"], 0)
            self.assertEqual(result["jobs"], 0)
            self.assertEqual(result["failed"], [])
            for invalid in (0, -1, 1.5):
                with self.subTest(jobs=invalid), self.assertRaises(ValueError):
                    compile_all_armv6k(Path(temp), jobs=invalid)

    def test_single_tu_cli_reuses_canonical_object_and_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            for force in (False, True):
                argv = ["build_check.py", "--repo-root", str(root),
                        "--tu", "src/engine/example.cpp"] + (["--force"] if force else [])
                with self.subTest(force=force), patch.object(sys, "argv", argv), \
                        patch("tools.build_check.find_clang", return_value=Path("compiler")), \
                        patch("tools.build_check.ensure_tu_armv6k", return_value=
                              subprocess.CompletedProcess([], 0, "", "")) as ensure, \
                        redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as success:
                        main()
                    self.assertEqual(success.exception.code, 0)
                ensure.assert_called_once_with(root / "src/engine/example.cpp",
                    root / "build/obj/armv6k/engine/example.o", repo_root=root, force=force)

    def test_cli_rejects_invalid_job_counts_before_compiling(self):
        for count in ("0", "-2", "invalid"):
            with self.subTest(jobs=count), patch.object(sys, "argv",
                    ["build_check.py", "--jobs", count]), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as failure:
                    main()
                self.assertEqual(failure.exception.code, 2)


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
                # Index once instead of traversing the build tree twice per function.
                object_index = {}
                for obj in build.rglob("*"):
                    if obj.suffix in (".o", ".obj"):
                        object_index.setdefault(obj.name, []).append(obj)
                for row in matches:
                    basename = Path(row["src_file"]).name
                    objects = object_index.get(basename + ".o", [])
                    objects = objects + object_index.get(basename + ".obj", [])
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
