"""Synthetic exact-match regressions require no proprietary game fixture."""
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.asm_diff import compare_function


class TestExactRelocations(unittest.TestCase):
    def test_wrong_relocated_branch_target_is_not_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "branch.cpp"
            source.write_text('extern "C" void branch() {}', encoding="utf-8")
            source.with_suffix(".o").write_bytes(b"mock object")
            original = struct.pack("<I", 0xEB000001)
            compiled = struct.pack("<I", 0xEB000000)
            with patch("tools.asm_diff.ensure_tu_armv6k", return_value=subprocess.CompletedProcess([], 0)), \
                 patch("tools.asm_diff.extract_elf_functions", return_value={"branch": (compiled, {0})}):
                result = compare_function(0x100000, 4, "branch", source, original)
            self.assertFalse(result["exact_match"])
            self.assertEqual(result["byte_match_ratio"], 0.75)

    def test_identical_unresolved_relocation_is_not_proof_of_linked_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "branch.cpp"
            source.write_text('extern "C" void branch() {}', encoding="utf-8")
            source.with_suffix(".o").write_bytes(b"mock object")
            raw = struct.pack("<I", 0xEB000000)
            with patch("tools.asm_diff.ensure_tu_armv6k", return_value=subprocess.CompletedProcess([], 0)), \
                 patch("tools.asm_diff.extract_elf_functions", return_value={"branch": (raw, {0})}):
                result = compare_function(0x100000, 4, "branch", source, raw)
            self.assertFalse(result["exact_match"])
            self.assertEqual(result["byte_match_ratio"], 1.0)
