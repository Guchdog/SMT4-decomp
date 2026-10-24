from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tools.scaffold_semantic_family import generate_scaffold


TEXT = 0x00100000
BX_LR_ARM = 0xE12FFF1E
BL_TO_NEXT_WORD = 0xEB000000


def signature_report(address: int, size: int, instructions: list[str]) -> dict:
    return {
        "candidate_count": 1,
        "groups": [{
            "mnemonics": [item.split()[0] for item in instructions],
            "count": 1,
            "candidates": [{
                "address": f"{address:#010x}",
                "size": size,
                "status": "matching",
                "category": "engine",
                "name": f"func_{address:08x}",
                "src_file": "src/example.cpp",
                "instructions": instructions,
            }],
        }],
    }


class TestScaffoldSemanticFamily(unittest.TestCase):
    def test_emits_pinned_review_scaffold_and_unverified_arm_callers(self):
        # BL at TEXT targets the candidate at TEXT+8; the word at +4 and the
        # candidate body are both bx lr.
        image = struct.pack("<III", BL_TO_NEXT_WORD, BX_LR_ARM, BX_LR_ARM)
        candidate_address = TEXT + 8
        report = signature_report(candidate_address, 4, ["bx lr"])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report_path = root / "groups.json"
            code_path = root / "code.bin"
            output = root / "scaffold"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            code_path.write_bytes(image)

            manifest = generate_scaffold(report_path, code_path, output, 0)

            candidate = manifest["candidates"][0]
            self.assertEqual(manifest["code_image_sha256"], hashlib.sha256(image).hexdigest())
            self.assertEqual(candidate["original_bytes_hex"], struct.pack("<I", BX_LR_ARM).hex())
            self.assertEqual(candidate["possible_arm_bl_callers"], [f"{TEXT:#010x}"])
            self.assertTrue(candidate["caller_review_required"])
            self.assertFalse(manifest["caller_xref_scan"]["confirmed"])
            self.assertFalse(manifest["caller_xref_scan"]["thumb_calls_scanned"])
            self.assertIn("TODO", (output / "candidate_skeleton.cpp").read_text(encoding="utf-8"))
            self.assertIn("unverified", (output / "review.md").read_text(encoding="utf-8"))
            self.assertEqual(
                {path.name for path in output.iterdir()},
                {"family_manifest.json", "review.md", "candidate_skeleton.cpp"},
            )

    def test_filters_only_candidates_inside_selected_group(self):
        image = struct.pack("<II", BX_LR_ARM, BX_LR_ARM)
        first = TEXT
        second = TEXT + 4
        report = {
            "groups": [{
                "mnemonics": ["bx"], "count": 2,
                "candidates": [
                    {"address": f"{first:#010x}", "size": 4, "instructions": ["bx lr"]},
                    {"address": f"{second:#010x}", "size": 4, "instructions": ["bx lr"]},
                ],
            }],
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report_path = root / "groups.json"
            code_path = root / "code.bin"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            code_path.write_bytes(image)

            manifest = generate_scaffold(
                report_path, code_path, root / "scaffold", 0, [f"{second:#x}"]
            )

        self.assertEqual(manifest["selected_candidate_count"], 1)
        self.assertEqual(manifest["candidates"][0]["address"], f"{second:#010x}")

    def test_fails_closed_on_instruction_drift_or_unknown_address(self):
        image = struct.pack("<I", BX_LR_ARM)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report_path = root / "groups.json"
            code_path = root / "code.bin"
            output = root / "scaffold"
            code_path.write_bytes(image)

            report_path.write_text(
                json.dumps(signature_report(TEXT, 4, ["mov r0, #0"])),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "instruction drift"):
                generate_scaffold(report_path, code_path, output, 0)
            self.assertFalse(output.exists())

            report_path.write_text(
                json.dumps(signature_report(TEXT, 4, ["bx lr"])),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "not members"):
                generate_scaffold(report_path, code_path, output, 0, ["0x00100004"])
            self.assertFalse(output.exists())

    def test_refuses_to_overwrite_existing_output_directory(self):
        image = struct.pack("<I", BX_LR_ARM)
        report = signature_report(TEXT, 4, ["bx lr"])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report_path = root / "groups.json"
            code_path = root / "code.bin"
            output = root / "scaffold"
            output.mkdir()
            sentinel = output / "keep.txt"
            sentinel.write_text("preserve", encoding="utf-8")
            report_path.write_text(json.dumps(report), encoding="utf-8")
            code_path.write_bytes(image)

            with self.assertRaises(FileExistsError):
                generate_scaffold(report_path, code_path, output, 0)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve")


if __name__ == "__main__":
    unittest.main()
