import tempfile
import unittest
import subprocess
from unittest.mock import patch
from pathlib import Path
from tools.progress import compute_progress, render_progress_md, render_readme_md, VerificationError
from tests.fixtures import require_private_fixtures


class TestProgress(unittest.TestCase):
    def test_rejects_claimed_function_without_src_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "functions.csv"
            csv_path.write_text(
                "address,size,status,category,name,src_file\n"
                "0x00100000,36,non_matching,crt,__start,src/crt/missing.cpp\n",
                encoding="utf-8",
            )
            with self.assertRaises(VerificationError):
                compute_progress(csv_path, root)

    def test_rejects_claimed_function_without_address_marker_in_src(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_dir = root / "src" / "crt"
            src_dir.mkdir(parents=True, exist_ok=True)
            (src_dir / "start.cpp").write_text("void __start() {}\n", encoding="utf-8")
            csv_path = root / "functions.csv"
            csv_path.write_text(
                "address,size,status,category,name,src_file\n"
                "0x00100000,36,stub,crt,__start,src/crt/start.cpp\n",
                encoding="utf-8",
            )
            with self.assertRaises(VerificationError):
                compute_progress(csv_path, root)

    def test_rejects_empty_stub_marked_as_non_matching(self):
        """Rigorous verification: empty or trivial stubs cannot be marked non_matching."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_dir = root / "src" / "test"
            src_dir.mkdir(parents=True, exist_ok=True)
            (src_dir / "stub.cpp").write_text(
                "// DECOMP_FUNC(0x00100000, 5000)\n"
                "void FakeFunc() {\n"
                "    // Just an empty stub\n"
                "}\n",
                encoding="utf-8",
            )
            csv_path = root / "functions.csv"
            csv_path.write_text(
                "address,size,status,category,name,src_file\n"
                "0x00100000,5000,non_matching,test,FakeFunc,src/test/stub.cpp\n",
                encoding="utf-8",
            )
            with self.assertRaises(VerificationError):
                compute_progress(csv_path, root)

    def test_accepts_valid_stub_status(self):
        """Scaffolded stubs marked as 'stub' are valid and counted under stub metrics."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_dir = root / "src" / "test"
            src_dir.mkdir(parents=True, exist_ok=True)
            (src_dir / "stub.cpp").write_text(
                "// DECOMP_FUNC(0x00100000, 5000)\n"
                "void FakeFunc() {\n"
                "}\n",
                encoding="utf-8",
            )
            csv_path = root / "functions.csv"
            csv_path.write_text(
                "address,size,status,category,name,src_file\n"
                "0x00100000,5000,stub,test,FakeFunc,src/test/stub.cpp\n",
                encoding="utf-8",
            )
            stats = compute_progress(csv_path, root)
            self.assertEqual(stats["stub_functions"], 1)
            self.assertEqual(stats["stub_bytes"], 5000)
            self.assertEqual(stats["decompiled_functions"], 0)
            self.assertEqual(stats["decompiled_bytes"], 0)

    def test_rejects_marker_left_behind_when_first_body_removed(self):
        """A leftover marker must not parse the following function's body."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_dir = root / "src" / "test"
            src_dir.mkdir(parents=True, exist_ok=True)
            (src_dir / "removed.cpp").write_text(
                "// First was removed here\n"
                "// DECOMP_FUNC(0x00100000, 64)\n"
                "// DECOMP_FUNC(0x00100040, 64)\n"
                "void Second() {\n"
                "    int value = 1;\n"
                "    (void)value;\n"
                "}\n",
                encoding="utf-8",
            )
            csv_path = root / "functions.csv"
            csv_path.write_text(
                "address,size,status,category,name,src_file\n"
                "0x00100000,64,non_matching,test,First,src/test/removed.cpp\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(VerificationError, "Could not parse function body"):
                compute_progress(csv_path, root)

    def test_rejects_marker_size_mismatch(self):
        """The DECOMP_FUNC size must match config/functions.csv."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_dir = root / "src" / "test"
            src_dir.mkdir(parents=True, exist_ok=True)
            (src_dir / "size.cpp").write_text(
                "// DECOMP_FUNC(0x00100000, 72)\n"
                "void First() {\n"
                "    int value = 1;\n"
                "    (void)value;\n"
                "}\n",
                encoding="utf-8",
            )
            csv_path = root / "functions.csv"
            csv_path.write_text(
                "address,size,status,category,name,src_file\n"
                "0x00100000,64,non_matching,test,First,src/test/size.cpp\n",
                encoding="utf-8",
            )
            with self.assertRaises(VerificationError):
                compute_progress(csv_path, root)

    def test_rejects_non_identical_function_marked_as_matching(self):
        """Marking a function matching when its compiled bytes do not match code.bin raises VerificationError."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code_dir = root / "extracted" / "exefs"
            code_dir.mkdir(parents=True, exist_ok=True)
            code_data = bytearray(0x20000)
            code_dir.joinpath("code.bin").write_bytes(bytes(code_data))

            src_dir = root / "src" / "engine"
            src_dir.mkdir(parents=True, exist_ok=True)
            (src_dir / "leaf.cpp").write_text(
                "// DECOMP_FUNC(0x0011b838, 24)\n"
                'extern "C" void engine_func_0011b838(char* p) {\n'
                "    *(int*)p = 1234;\n"
                "}\n",
                encoding="utf-8",
            )
            csv_path = root / "functions.csv"
            csv_path.write_text(
                "address,size,status,category,name,src_file\n"
                "0x0011b838,24,matching,engine,engine_func_0011b838,src/engine/leaf.cpp\n",
                encoding="utf-8",
            )
            with self.assertRaises(VerificationError):
                compute_progress(csv_path, root)

    def test_accepts_empty_body_when_it_is_an_exact_matching_return(self):
        """An empty C++ body is complete when it emits the original ``bx lr``."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code_dir = root / "extracted" / "exefs"
            code_dir.mkdir(parents=True, exist_ok=True)
            code_dir.joinpath("code.bin").write_bytes(bytes.fromhex("1eff2fe1"))

            src_dir = root / "src" / "engine"
            src_dir.mkdir(parents=True, exist_ok=True)
            (src_dir / "leaf.cpp").write_text(
                "// DECOMP_FUNC(0x00100000, 4)\n"
                'extern "C" void EmptyReturn() {}\n',
                encoding="utf-8",
            )
            csv_path = root / "functions.csv"
            csv_path.write_text(
                "address,size,status,category,name,src_file\n"
                "0x00100000,4,matching,engine,EmptyReturn,src/engine/leaf.cpp\n",
                encoding="utf-8",
            )

            stats = compute_progress(csv_path, root)

        self.assertEqual(stats["matching_functions"], 1)
        self.assertEqual(stats["matching_bytes"], 4)

    def test_real_repo_progress_matches_text_size(self):
        require_private_fixtures(self, Path("extracted/exefs/code.bin"))
        stats = compute_progress(Path("config/functions.csv"), Path("."))
        self.assertEqual(stats["total_bytes"], 0x2FE624)
        self.assertEqual(stats["decompiled_functions"], 2244)
        self.assertEqual(stats["decompiled_bytes"], 668704)
        self.assertEqual(stats["stub_functions"], 39)
        self.assertEqual(stats["stub_bytes"], 248240)
        self.assertEqual(stats["total_explored_functions"], 2283)
        self.assertEqual(stats["total_explored_bytes"], 916944)
        self.assertEqual(stats["matching_functions"], 1861)
        self.assertEqual(stats["matching_bytes"], 131812)
        self.assertEqual(stats["verified_functions"], 338)
        self.assertEqual(stats["verified_bytes"], 297424)
        self.assertEqual(stats["compiled_functions"], stats["verified_functions"])
        self.assertEqual(stats["compiled_bytes"], stats["verified_bytes"])
        self.assertEqual(stats["draft_functions"], 45)
        self.assertEqual(stats["draft_bytes"], 239468)
        self.assertEqual(
            stats["verified_functions"] + stats["draft_functions"] + stats["matching_functions"],
            stats["decompiled_functions"],
        )
        self.assertEqual(
            stats["verified_bytes"] + stats["draft_bytes"] + stats["matching_bytes"],
            stats["decompiled_bytes"],
        )
        self.assertEqual(stats["categories"]["engine"]["matching_funcs"], 266)
        self.assertEqual(stats["categories"]["engine"]["matching_bytes"], 15228)
        self.assertEqual(stats["categories"]["battle"]["matching_funcs"], 61)
        self.assertEqual(stats["categories"]["battle"]["matching_bytes"], 2624)
        self.assertEqual(stats["categories"]["ui"]["matching_funcs"], 116)
        self.assertEqual(stats["categories"]["ui"]["matching_bytes"], 9084)
        self.assertEqual(stats["categories"]["unknown"]["matching_funcs"], 1184)
        self.assertEqual(stats["categories"]["unknown"]["matching_bytes"], 93608)
        self.assertEqual(stats["categories"]["camp"]["matching_funcs"], 63)
        self.assertEqual(stats["categories"]["camp"]["matching_bytes"], 2992)
        self.assertEqual(stats["categories"]["shop"]["matching_funcs"], 13)
        self.assertEqual(stats["categories"]["shop"]["matching_bytes"], 1020)
        self.assertEqual(stats["categories"]["script_vm"]["matching_funcs"], 142)
        self.assertEqual(stats["categories"]["script_vm"]["matching_bytes"], 6560)
        self.assertEqual(stats["categories"]["nn_sdk"]["matching_funcs"], 7)
        self.assertEqual(stats["categories"]["nn_sdk"]["matching_bytes"], 340)
        self.assertEqual(stats["categories"]["unite"]["matching_funcs"], 5)
        self.assertEqual(stats["categories"]["unite"]["matching_bytes"], 216)
        self.assertEqual(stats["categories"]["crt"]["matching_funcs"], 4)
        self.assertEqual(stats["categories"]["crt"]["matching_bytes"], 140)

    def _nonmatching_project(self, root):
        src = root / "src" / "function.cpp"
        src.parent.mkdir()
        src.write_text(
            "// DECOMP_FUNC(0x00100000, 64)\n"
            'extern "C" int Example(int x) { return x + 1; }\n',
            encoding="utf-8",
        )
        ledger = root / "functions.csv"
        ledger.write_text(
            "address,size,status,category,name,src_file\n"
            "0x00100000,64,non_matching,test,Example,src/function.cpp\n",
            encoding="utf-8",
        )
        return src, ledger

    def test_progress_refreshes_objects_and_rejects_compilation_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, ledger = self._nonmatching_project(root)
            obj = root / "build/obj/armv6k/function.o"
            obj.parent.mkdir(parents=True)
            obj.touch()  # Even an existing object must go through freshness checking.
            with patch("tools.progress.ensure_tu_armv6k", return_value=subprocess.CompletedProcess([], 1, "", "bad header")) as ensure:
                with self.assertRaisesRegex(VerificationError, "Compilation failed.*bad header"):
                    compute_progress(ledger, root)
                ensure.assert_called_once_with(src, obj, repo_root=root.resolve())

    def test_compiled_coverage_is_not_reported_as_verified_logic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, ledger = self._nonmatching_project(root)
            obj = root / "build/obj/armv6k/function.o"
            obj.parent.mkdir(parents=True)
            obj.touch()
            with patch("tools.progress.ensure_tu_armv6k", return_value=subprocess.CompletedProcess([], 0, "", "")), patch("tools.progress.extract_elf_functions", return_value={"Example": (bytes(16), set())}):
                stats = compute_progress(ledger, root)
            self.assertEqual(stats["compiled_functions"], 1)
            self.assertEqual(stats["matching_functions"], 0)
            self.assertEqual(stats["categories"]["test"]["compiled_funcs"], 1)
            for report in (render_progress_md(stats), render_readme_md(stats)):
                self.assertIn("Compiled Coverage", report)
                self.assertIn("logic unverified", report)
                self.assertNotIn("Verified Logic", report)
                self.assertNotIn("object code verified against disassembly", report)


if __name__ == "__main__":
    unittest.main()
