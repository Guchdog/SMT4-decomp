import unittest
import csv
import json
import tempfile
from pathlib import Path
from tools.analyze_code import (analyze_binary, vaddr_to_offset,
                                compare_ledgers, write_analysis_proposal)
from tests.fixtures import require_private_fixtures


class TestAnalyzeCode(unittest.TestCase):
    def test_proposal_reports_boundary_drift_and_preserves_curated_files(self):
        old = [dict(address="0x00100000", size="4", status="matching", category="crt",
                    name="start", src_file="src/start.cpp"),
               dict(address="0x00100004", size="4", status="matching_span", category="raw_span",
                    name="span", src_file="src/span.cpp")]
        proposed = [dict(old[0], size=8), dict(old[0], address="0x00100008", size=4)]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = root / "config"
            config.mkdir()
            ledger = config / "functions.csv"
            with ledger.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(old[0]))
                writer.writeheader()
                writer.writerows(old)
            symbols = config / "symbols.csv"
            symbols.write_text("curated symbol metadata\n", encoding="utf-8")
            before = (ledger.read_bytes(), symbols.read_bytes())
            output = root / "build" / "analysis"
            report = write_analysis_proposal(output, config, proposed, [])
            self.assertEqual(report["removed_addresses"], ["0x00100004"])
            self.assertEqual(report["added_addresses"], ["0x00100008"])
            self.assertEqual(report["size_changes"], [dict(
                address="0x00100000", existing_size=4, proposed_size=8)])
            self.assertEqual(json.loads((output / "ledger_diff.json").read_text()), report)
            self.assertEqual((ledger.read_bytes(), symbols.read_bytes()), before)
            with self.assertRaisesRegex(ValueError, "curated"):
                write_analysis_proposal(config, config, proposed, [])
            self.assertEqual((ledger.read_bytes(), symbols.read_bytes()), before)

    def test_ledger_comparison_normalizes_address_spelling_and_size_types(self):
        self.assertEqual(compare_ledgers(
            [dict(address="0x0010000A", size="4")],
            [dict(address="0x0010000a", size=4)])["size_changes"], [])

    def test_real_analysis_writes_only_a_proposal_and_drops_stale_match_claims(self):
        require_private_fixtures(self, "extracted/exefs/code.bin")
        ledger = Path("config/functions.csv")
        before = ledger.read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            functions, _ = analyze_binary(Path("extracted/exefs/code.bin"),
                Path("config/game_info.json"), write_csv=True, output_dir=Path(temp))
            original = {r["address"]: r for r in csv.DictReader(before.decode().splitlines())}
            for row in functions:
                old = original.get(row["address"])
                if old is not None and int(old["size"]) != int(row["size"]):
                    self.assertEqual(row["status"], "todo")
                    self.assertEqual(row["src_file"], "")
            self.assertTrue((Path(temp) / "ledger_diff.json").is_file())
        self.assertEqual(ledger.read_bytes(), before)

    def test_vaddr_to_offset_mapping(self):
        self.assertEqual(vaddr_to_offset(0x00100000), 0x0)
        self.assertEqual(vaddr_to_offset(0x003FF000), 0x2FF000)
        self.assertEqual(vaddr_to_offset(0x0042B000), 0x32B000)

    def test_contiguous_text_coverage_and_literal_pool_exclusion(self):
        require_private_fixtures(self, "extracted/exefs/code.bin")
        funcs, symbols = analyze_binary(
            Path("extracted/exefs/code.bin"), Path("config/game_info.json"), write_csv=False
        )
        self.assertGreater(len(funcs), 5000)
        # First function is entrypoint __start at 0x00100000
        self.assertEqual(funcs[0]["address"], "0x00100000")
        self.assertEqual(funcs[0]["name"], "__start")
        # Sum of all function sizes must equal exact .text size (0x2FE624 = 3,139,108 bytes) with zero overlaps/gaps
        total_size = sum(int(f["size"]) for f in funcs)
        self.assertEqual(total_size, 0x2FE624)
        # Ensure subsystems like ui, battle, camp, script_vm are discovered via .rodata string xrefs
        categories = {f["category"] for f in funcs}
        for expected_cat in ("crt", "ui", "battle", "camp", "script_vm", "nn_sdk"):
            self.assertIn(expected_cat, categories)

    def test_vldr_float_pools_and_thumb_crt_not_misidentified_as_bl(self):
        require_private_fixtures(self, "extracted/exefs/code.bin")
        funcs, _ = analyze_binary(
            Path("extracted/exefs/code.bin"), Path("config/game_info.json"), write_csv=False
        )
        addrs = {int(f["address"], 16) for f in funcs}
        # Bogus functions caused by VLDR float constants (0x4b000000) and Thumb pairs (0x00100fa8) must not exist
        for bogus_addr in (0x00282750, 0x00282918, 0x002885A8, 0x002919D0, 0x003EB4C8, 0x0011C548):
            self.assertNotIn(bogus_addr, addrs, f"Bogus float/Thumb target 0x{bogus_addr:08x} in functions")


if __name__ == "__main__":
    unittest.main()
