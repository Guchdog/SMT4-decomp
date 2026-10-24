import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.semantic_experiment_support import (
    compile_candidate_symbols, load_pinned_reference,
)


class TestLoadPinnedReference(unittest.TestCase):
    def _fixture(self, root: Path, *, configured_size=None, configured_hash=None):
        image = b"synthetic-code-image"
        (root / "code.bin").write_bytes(image)
        metadata = {
            "code_bin_size": len(image) if configured_size is None else configured_size,
            "code_sha256": hashlib.sha256(image).hexdigest()
            if configured_hash is None else configured_hash,
        }
        (root / "game.json").write_text(json.dumps(metadata), encoding="utf-8")
        (root / "functions.csv").write_text(
            "address,size,status\n0x00100000,4,matching\n", encoding="utf-8"
        )
        return root / "code.bin", root / "game.json", root / "functions.csv", image

    def test_returns_image_metadata_and_ledger_after_pin(self):
        with tempfile.TemporaryDirectory() as temporary:
            code, metadata, ledger, image = self._fixture(Path(temporary))
            result = load_pinned_reference(code, metadata, ledger)
        self.assertEqual(result.image, image)
        self.assertEqual(result.game_info["code_bin_size"], len(image))
        self.assertEqual(result.ledger[0]["address"], "0x00100000")

    def test_rejects_size_and_hash_mismatches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            code, metadata, ledger, _ = self._fixture(root, configured_size=1)
            with self.assertRaisesRegex(ValueError, "size mismatch"):
                load_pinned_reference(code, metadata, ledger)
            code, metadata, ledger, _ = self._fixture(
                root, configured_hash="0" * 64
            )
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                load_pinned_reference(code, metadata, ledger)


class TestCompileCandidateSymbols(unittest.TestCase):
    def _compile(self, extracted):
        build = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        with patch("tools.semantic_experiment_support.compile_tu_armv6k",
                   return_value=build) as compile_mock, patch(
                       "tools.semantic_experiment_support.extract_elf_functions_detailed",
                       return_value=extracted):
            symbols = compile_candidate_symbols(
                Path("candidate.cpp"), Path("candidate.o"), Path("."), {"candidate"}
            )
        compile_mock.assert_called_once()
        return symbols

    def test_extracts_valid_required_symbol(self):
        bx_lr = b"\x1e\xff\x2f\xe1"
        self.assertEqual(self._compile({"candidate": (bx_lr, ())}), {"candidate": bx_lr})

    def test_rejects_missing_required_symbol(self):
        bx_lr = b"\x1e\xff\x2f\xe1"
        with self.assertRaisesRegex(ValueError, "Missing required"):
            self._compile({"other": (bx_lr, ())})

    def test_rejects_relocations(self):
        bx_lr = b"\x1e\xff\x2f\xe1"
        with self.assertRaisesRegex(ValueError, "Unsupported relocation in candidate"):
            self._compile({"candidate": (bx_lr, ("R_ARM_CALL",))})

    def test_rejects_invalid_leaf_code(self):
        with self.assertRaisesRegex(ValueError, "Invalid leaf candidate candidate"):
            self._compile({"candidate": (b"\x00\x00\x00\x00", ())})

    def test_reports_compilation_failure(self):
        build = subprocess.CompletedProcess(args=[], returncode=1, stdout="",
                                             stderr="synthetic compile failure")
        with patch("tools.semantic_experiment_support.compile_tu_armv6k",
                   return_value=build):
            with self.assertRaisesRegex(RuntimeError, "synthetic compile failure"):
                compile_candidate_symbols(Path("candidate.cpp"), Path("candidate.o"),
                                          Path("."), {"candidate"})


if __name__ == "__main__":
    unittest.main()
