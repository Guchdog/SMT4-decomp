"""Synthetic exact-match regressions require no proprietary game fixture."""
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.asm_diff import ElfRelocation, compare_function, find_symbol_in_elf
from tools.build_check import find_clang


class TestExactRelocations(unittest.TestCase):
    def test_symbol_lookup_rejects_plain_substrings_and_ambiguous_mangling(self):
        unrelated = {"prefix_branch_suffix": (b"same bytes", ())}
        self.assertIsNone(find_symbol_in_elf(unrelated, "branch"))

        mangled = {"_Z3foov": (b"foo", ())}
        self.assertEqual(find_symbol_in_elf(mangled, "foo"), (b"foo", ()))

        with_lambda = {
            "_ZN3fooEv": (b"foo", ()),
            "_ZZN3fooEvENK3$_0clEv": (b"lambda", ()),
        }
        self.assertEqual(find_symbol_in_elf(with_lambda, "foo"), (b"foo", ()))

        ambiguous = {
            "_Z3foov": (b"one", ()),
            "_ZN3fooEv": (b"two", ()),
        }
        self.assertIsNone(find_symbol_in_elf(ambiguous, "foo"))

    def test_wrong_relocated_branch_target_is_not_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "branch.cpp"
            source.write_text('extern "C" void branch() {}', encoding="utf-8")
            source.with_suffix(".o").write_bytes(b"mock object")
            original = struct.pack("<I", 0xEB000001)
            compiled = struct.pack("<I", 0xEB000000)
            with patch("tools.asm_diff.ensure_tu_armv6k", return_value=subprocess.CompletedProcess([], 0)), \
                 patch(
                     "tools.asm_diff.extract_elf_functions_detailed",
                     return_value={"branch": (compiled, (ElfRelocation(0, 28, "target"),))},
                 ):
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
                 patch(
                     "tools.asm_diff.extract_elf_functions_detailed",
                     return_value={"branch": (raw, (ElfRelocation(0, 28, "unknown_target"),))},
                 ):
                result = compare_function(0x100000, 4, "branch", source, raw)
            self.assertFalse(result["exact_match"])
            self.assertEqual(result["byte_match_ratio"], 1.0)

    def test_resolved_arm_call_matches_when_target_address_agrees(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config"
            config.mkdir()
            ledger = config / "functions.csv"
            ledger.write_text(
                "address,size,status,category,name,src_file\n"
                "0x0010000c,4,todo,test,target,\n",
                encoding="utf-8",
            )
            source = root / "branch.cpp"
            source.write_text('extern "C" void branch() {}', encoding="utf-8")
            source.with_suffix(".o").write_bytes(b"mock object")
            expected = struct.pack("<I", 0xEB000001)  # BL to 0x0010000c
            compiled = struct.pack("<I", 0xEBFFFFFE)  # unapplied R_ARM_CALL
            details = {"branch": (compiled, (ElfRelocation(0, 28, "target"),))}

            with patch("tools.asm_diff.ensure_tu_armv6k", return_value=subprocess.CompletedProcess([], 0)), \
                 patch("tools.asm_diff.extract_elf_functions_detailed", return_value=details):
                result = compare_function(
                    0x00100000, 4, "branch", source, expected, repo_root=root
                )
            self.assertTrue(result["exact_match"])
            self.assertEqual(result["byte_match_ratio"], 1.0)

            ledger.write_text(
                "address,size,status,category,name,src_file\n"
                "0x00100010,4,todo,test,target,\n",
                encoding="utf-8",
            )
            with patch("tools.asm_diff.ensure_tu_armv6k", return_value=subprocess.CompletedProcess([], 0)), \
                 patch("tools.asm_diff.extract_elf_functions_detailed", return_value=details):
                result = compare_function(
                    0x00100000, 4, "branch", source, expected, repo_root=root
                )
            self.assertFalse(result["exact_match"])

            ledger.write_text(
                "address,size,status,category,name,src_file\n"
                "0x0010000c,4,todo,test,target,\n",
                encoding="utf-8",
            )
            altered_addend = struct.pack("<I", 0xEBFFFFFD)
            altered_details = {
                "branch": (altered_addend, (ElfRelocation(0, 28, "target"),))
            }
            with patch("tools.asm_diff.ensure_tu_armv6k", return_value=subprocess.CompletedProcess([], 0)), \
                 patch("tools.asm_diff.extract_elf_functions_detailed", return_value=altered_details):
                result = compare_function(
                    0x00100000, 4, "branch", source, expected, repo_root=root
                )
            self.assertFalse(result["exact_match"])

            rela_details = {
                "branch": (compiled, (ElfRelocation(0, 28, "target", -8),))
            }
            with patch("tools.asm_diff.ensure_tu_armv6k", return_value=subprocess.CompletedProcess([], 0)), \
                 patch("tools.asm_diff.extract_elf_functions_detailed", return_value=rela_details):
                result = compare_function(
                    0x00100000, 4, "branch", source, expected, repo_root=root
                )
            self.assertFalse(result["exact_match"])

    def test_compiled_arm_call_relocation_resolves_to_ledger_target(self):
        try:
            find_clang()
        except FileNotFoundError as exc:
            self.skipTest(str(exc))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config"
            config.mkdir()
            (config / "functions.csv").write_text(
                "address,size,status,category,name,src_file\n"
                "0x0010000c,4,todo,test,target,\n",
                encoding="utf-8",
            )
            source = root / "branch.cpp"
            source.write_text(
                'extern "C" void target();\n'
                'extern "C" __attribute__((naked)) void branch() {\n'
                '    __asm__ volatile("bl target\\n\\tbx lr");\n'
                '}\n',
                encoding="utf-8",
            )
            expected = bytes.fromhex("010000eb1eff2fe1")
            result = compare_function(
                0x00100000, 8, "branch", source, expected, repo_root=root
            )

        self.assertTrue(result["exact_match"], result["diff_lines"])
        self.assertEqual(result["byte_match_ratio"], 1.0)
