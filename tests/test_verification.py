import sys
import io
from contextlib import redirect_stdout, redirect_stderr
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.verify_decomp import audit_claimed_functions, main


class TestVerificationAudit(unittest.TestCase):
    def test_zero_similarity_is_only_compiled_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = root / "functions.csv"
            ledger.write_text(
                "address,size,status,category,name,src_file\n"
                "0x00100000,64,non_matching,test,Example,src/example.cpp\n",
                encoding="utf-8",
            )
            result = {"compiled_size": 16, "exact_match": False,
                      "byte_match_ratio": 0.0, "mnemonic_match_ratio": 0.0,
                      "diff_lines": []}
            with patch("tools.verify_decomp.compare_function", return_value=result) as compare:
                stats = audit_claimed_functions(ledger, root)
            self.assertEqual(stats["compiled_count"], 1)
            self.assertEqual(stats["verified_count"], stats["compiled_count"])
            self.assertEqual(stats["details"][0]["classification"], "compiled")
            self.assertEqual(compare.call_args.kwargs["code_bytes"], b"")

    def test_compile_failure_is_not_a_draft_or_successful_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = root / "functions.csv"
            ledger.write_text(
                "address,size,status,category,name,src_file\n"
                "0x00100000,64,non_matching,test,Example,src/example.cpp\n",
                encoding="utf-8",
            )
            result = {"compiled_size": 0, "exact_match": False,
                      "byte_match_ratio": 0.0, "mnemonic_match_ratio": 0.0,
                      "diff_lines": ["Compilation failed: bad header"]}
            with patch("tools.verify_decomp.compare_function", return_value=result):
                stats = audit_claimed_functions(ledger, root)
            self.assertEqual(stats["compilation_failed"], 1)
            self.assertEqual(stats["draft_count"], 0)
            self.assertEqual(stats["details"][0]["classification"], "compilation_failed")
            errors = io.StringIO()
            with patch("tools.verify_decomp.audit_claimed_functions", return_value=stats), patch.object(sys, "argv", ["verify_decomp.py"]), redirect_stdout(io.StringIO()), redirect_stderr(errors):
                with self.assertRaises(SystemExit) as failure:
                    main()
            self.assertEqual(failure.exception.code, 1)
            self.assertIn("bad header", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
