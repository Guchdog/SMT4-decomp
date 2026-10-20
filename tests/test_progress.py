import tempfile
import unittest
from pathlib import Path
from tools.progress import compute_progress, VerificationError


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

    def test_real_repo_progress_matches_text_size(self):
        stats = compute_progress(Path("config/functions.csv"), Path("."))
        self.assertEqual(stats["total_bytes"], 0x2FE624)
        self.assertEqual(stats["decompiled_functions"], 214)
        self.assertEqual(stats["decompiled_bytes"], 259200)
        self.assertEqual(stats["stub_functions"], 39)
        self.assertEqual(stats["stub_bytes"], 248240)
        self.assertEqual(stats["total_explored_functions"], 253)
        self.assertEqual(stats["total_explored_bytes"], 507440)


if __name__ == "__main__":
    unittest.main()
