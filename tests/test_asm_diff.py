import csv
import os
import tempfile
import unittest
import io
import sys
from contextlib import redirect_stdout
from unittest.mock import patch
from pathlib import Path
from tools.build_check import compile_tu_armv6k, find_clang
from tools.asm_diff import extract_elf_functions, compare_function, main
from tools.verify_decomp import audit_claimed_functions
from tools.find_candidates import find_leaf_candidates


class TestAsmDiffCli(unittest.TestCase):
    def test_exit_codes_and_root_relative_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "reference.bin").write_bytes(b"reference")
            (root / "ledger.csv").write_text(
                "address,size,name,src_file\n0x00100000,4,entry,src/entry.cpp\n",
                encoding="utf-8")
            for exact, compiled_size in ((True, 4), (False, 4), (False, 0)):
                with self.subTest(exact=exact, compiled_size=compiled_size):
                    result = dict(name="entry", addr="0x00100000", expected_size=4,
                        compiled_size=compiled_size, exact_match=exact,
                        byte_match_ratio=int(exact), mnemonic_match_ratio=int(exact),
                        diff_lines=["compile or symbol failure"] if not compiled_size else [])
                    argv = ["asm_diff.py", "--root", str(root), "--code", "reference.bin",
                            "--functions", "ledger.csv", "--addr", "0x00100000"]
                    with patch.object(sys, "argv", argv), patch(
                            "tools.asm_diff.compare_function", return_value=result) as compare, \
                            redirect_stdout(io.StringIO()):
                        if exact:
                            main()
                        else:
                            with self.assertRaises(SystemExit) as failure:
                                main()
                            self.assertEqual(failure.exception.code, 1)
                    self.assertEqual(compare.call_args.args[3], root / "src/entry.cpp")
                    self.assertEqual(compare.call_args.args[4], b"reference")


class TestAsmDiff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code_path = Path("extracted/exefs/code.bin")
        if os.environ.get("SMT4_SKIP_PRIVATE_TESTS") != "1" and cls.code_path.is_file():
            cls.code_bytes = cls.code_path.read_bytes()
        else:
            cls.code_bytes = b""

    def setUp(self):
        if self._testMethodName != "test_find_leaf_candidates_returns_pure_leaf_functions":
            try:
                find_clang()
            except FileNotFoundError as exc:
                self.skipTest(str(exc))

    def test_extract_elf_functions(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "test_extract.cpp"
            src.write_text(
                'extern "C" void engine_func_0011b838(char* p) {\n'
                "    *(volatile unsigned int*)(p) = 0;\n"
                "    *(volatile unsigned int*)(p + 4) = 0;\n"
                "    *(volatile unsigned short*)(p + 0x48) = 0;\n"
                "    *(volatile unsigned short*)(p + 0x4a) = 0;\n"
                "}\n",
                encoding="utf-8",
            )
            obj = Path(td) / "test_extract.o"
            res = compile_tu_armv6k(src, obj)
            self.assertEqual(res.returncode, 0, f"Compilation failed: {res.stderr}")
            funcs = extract_elf_functions(obj)
            self.assertIn("engine_func_0011b838", funcs)
            func_bytes, reloc_offsets = funcs["engine_func_0011b838"]
            self.assertEqual(len(func_bytes), 24)
            self.assertIsInstance(reloc_offsets, set)

    def test_compare_function_matching(self):
        if not self.code_bytes:
            self.skipTest("code.bin not available")
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "matching.cpp"
            src.write_text(
                'extern "C" void engine_func_0011b838(char* p) {\n'
                "    *(volatile unsigned int*)(p) = 0;\n"
                "    *(volatile unsigned int*)(p + 4) = 0;\n"
                "    *(volatile unsigned short*)(p + 0x48) = 0;\n"
                "    *(volatile unsigned short*)(p + 0x4a) = 0;\n"
                "}\n",
                encoding="utf-8",
            )
            res = compare_function(
                addr=0x0011B838,
                size=24,
                func_name="engine_func_0011b838",
                src_file=src,
                code_bytes=self.code_bytes,
                repo_root=Path("."),
            )
            self.assertTrue(res["exact_match"])
            self.assertEqual(res["compiled_size"], 24)
            self.assertEqual(res["byte_match_ratio"], 1.0)
            self.assertEqual(res["mnemonic_match_ratio"], 1.0)
            self.assertGreater(len(res["diff_lines"]), 0)

    def test_compare_function_non_matching(self):
        if not self.code_bytes:
            self.skipTest("code.bin not available")
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "non_matching.cpp"
            src.write_text(
                'extern "C" void engine_func_0011b838(char* p) {\n'
                "    *(int*)(p) = 42;\n"
                "}\n",
                encoding="utf-8",
            )
            res = compare_function(
                addr=0x0011B838,
                size=24,
                func_name="engine_func_0011b838",
                src_file=src,
                code_bytes=self.code_bytes,
                repo_root=Path("."),
            )
            self.assertFalse(res["exact_match"])
            self.assertLess(res["byte_match_ratio"], 1.0)

    def test_audit_claimed_functions(self):
        if not self.code_bytes:
            self.skipTest("code.bin not available")
        stats = audit_claimed_functions(
            functions_csv=Path("config/functions.csv"),
            repo_root=Path("."),
            code_path=self.code_path,
        )
        self.assertEqual(stats["total_claimed"], 10959)
        with Path("config/functions.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(stats["matching_verified"], sum(r["status"] == "matching" for r in rows))
        self.assertEqual(stats["matching_failed"], 0)
        self.assertEqual(stats["matching_spans_verified"], 8)
        self.assertEqual(stats["matching_spans_failed"], 0)
        self.assertEqual(stats["matching_spans_bytes"], 484)
        self.assertEqual(stats["compilation_failed"], 0)
        self.assertEqual(stats["compiled_count"] + stats["draft_count"],
                         sum(r["status"] == "non_matching" for r in rows))

    def test_find_leaf_candidates_returns_pure_leaf_functions(self):
        if not self.code_bytes:
            self.skipTest("code.bin not available")
        candidates = find_leaf_candidates(
            functions_csv=Path("config/functions.csv"),
            code_bytes=self.code_bytes,
            max_size=128,
            limit=50,
        )
        # The requested limit is an upper bound: a mature ledger may have
        # exhausted the pure-leaf shortlist within the configured size cap.
        self.assertLessEqual(len(candidates), 50)
        for c in candidates:
            self.assertLessEqual(c["size"], 128)
            self.assertGreater(c["instruction_count"], 0)
            self.assertTrue(c["address"].startswith("0x"))
            self.assertTrue(len(c["name"]) > 0)

    def test_all_matching_functions_in_ledger_are_byte_identical(self):
        if not self.code_bytes:
            self.skipTest("code.bin not available")
        csv_path = Path("config/functions.csv")
        matching_rows = []
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row["status"].strip() == "matching":
                    matching_rows.append(row)

        # Every exact claim must be true; semantic work need not retain a fixed
        # number of byte-identical implementations.
        validated_objects = set()
        for row in matching_rows:
            res = compare_function(
                addr=int(row["address"], 16),
                size=int(row["size"]),
                func_name=row["name"].strip(),
                src_file=Path(row["src_file"].strip()),
                code_bytes=self.code_bytes,
                repo_root=Path("."),
                validated_object_cache=validated_objects,
            )
            self.assertTrue(
                res["exact_match"],
                f"Function {row['name']} ({row['address']}) not exact match: {res['diff_lines']}",
            )
            self.assertEqual(res["byte_match_ratio"], 1.0)
            self.assertEqual(res["compiled_size"], int(row["size"]))

    def test_all_matching_raw_spans_in_ledger_are_byte_identical(self):
        if not self.code_bytes:
            self.skipTest("code.bin not available")
        with open(Path("config/functions.csv"), "r", encoding="utf-8", newline="") as f:
            span_rows = [
                row for row in csv.DictReader(f)
                if row["status"].strip() == "matching_span"
            ]

        self.assertEqual(len(span_rows), 8)
        self.assertEqual(sum(int(row["size"]) for row in span_rows), 484)
        validated_objects = set()
        for row in span_rows:
            result = compare_function(
                addr=int(row["address"], 16),
                size=int(row["size"]),
                func_name=row["name"].strip(),
                src_file=Path(row["src_file"].strip()),
                code_bytes=self.code_bytes,
                repo_root=Path("."),
                validated_object_cache=validated_objects,
            )
            self.assertTrue(
                result["exact_match"],
                f"Raw span {row['name']} ({row['address']}) not exact: {result['diff_lines']}",
            )
            self.assertEqual(result["compiled_size"], int(row["size"]))


if __name__ == "__main__":
    unittest.main()
