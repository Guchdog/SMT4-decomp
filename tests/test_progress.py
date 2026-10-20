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
                "0x00100000,36,non_matching,crt,__start,src/crt/start.cpp\n",
                encoding="utf-8",
            )
            with self.assertRaises(VerificationError):
                compute_progress(csv_path, root)

    def test_real_repo_progress_matches_text_size(self):
        stats = compute_progress(Path("config/functions.csv"), Path("."))
        self.assertEqual(stats["total_bytes"], 0x2FE624)
        self.assertEqual(stats["decompiled_functions"], 168)
        self.assertEqual(stats["decompiled_bytes"], 143732)


if __name__ == "__main__":
    unittest.main()
