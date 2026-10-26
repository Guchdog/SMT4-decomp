import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from tools.find_candidates import main
from tools.semantic_candidates import find_semantic_candidates, load_policy


class TestSemanticCandidateDiscovery(unittest.TestCase):
    def test_project_priorities_refer_to_ledger_entries_not_interior_labels(self):
        root = Path(__file__).resolve().parents[1]
        policy = load_policy(root)
        with (root / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            addresses = {int(row["address"], 16) for row in csv.DictReader(stream)}
        for item in policy["priority_functions"]:
            self.assertIn(int(item["address"], 16), addresses)

    def fixture(self, root):
        (root / "config").mkdir()
        (root / "experiments/semantic_equivalence").mkdir(parents=True)
        (root / "extracted/exefs").mkdir(parents=True)
        rows = [
            ("0x00100000", 256, "matching", "ui", "menu_callback", "source.cpp"),
            ("0x00100100", 8, "matching", "engine", "tiny", "source.cpp"),
            ("0x00100108", 8, "matching", "ui", "existing", "source.cpp"),
            ("0x00100110", 8, "matching", "ui", "typed", "source.cpp"),
            ("0x00100118", 4, "matching_span", "raw_span", "span", "source.cpp"),
            ("0x0010011c", 16, "todo", "script_vm", "unmapped", ""),
            ("0x0010012c", 16, "non_matching", "ui", "prefix_only", "source.cpp"),
        ]
        ledger = root / "config/functions.csv"
        with ledger.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(("address", "size", "status", "category", "name", "src_file"))
            writer.writerows(rows)
        source = []
        for address, size, _, _, name, path in rows:
            if not path:
                continue
            source.append(f"// DECOMP_FUNC({address}, {size})\n")
            if name == "typed":
                source.append("int typed() { return 1; }\n")
            else:
                # A call-bearing body must remain eligible; discovery is not
                # restricted to shapes supported by the original leaf pilot.
                source.append(f'void {name}() {{ asm("bl helper\\nbx lr"); }}\n')
        (root / "source.cpp").write_text("".join(source), encoding="utf-8")
        (root / "experiments/semantic_equivalence/candidates.cpp").write_text(
            "int candidate_00100108() { return 1; }\n"
            "int candidate_0010012c_prefix() { return 2; }\n", encoding="utf-8")
        policy = {"active_milestone": "H1", "priority_sources": [], "priority_functions": [
            {"address": "0x00100000", "reason": "H1 calc callback"},
            {"address": "0x00100108", "reason": "H1 existing dependency"}]}
        (root / "config/reconstruction.json").write_text(json.dumps(policy), encoding="utf-8")
        (root / "extracted/exefs/code.bin").write_bytes(bytes(512))
        return ledger

    def test_prioritizes_milestone_calling_function_and_avoids_reconstructing_cpp(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = self.fixture(root)
            candidates = find_semantic_candidates(ledger, root)
            self.assertEqual(candidates[0]["name"], "menu_callback")
            self.assertGreater(candidates[0]["size"], 64)
            names = {c["name"] for c in candidates}
            self.assertEqual(names, {"menu_callback", "tiny", "prefix_only", "unmapped"})
            self.assertEqual(candidates[0]["reference_status"], "matching")
            self.assertEqual(candidates[0]["next_action"], "recover_contract_and_cpp")

    def test_existing_candidate_can_be_queued_for_validation_without_claiming_a_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            candidates = find_semantic_candidates(self.fixture(root), root, include_existing=True)
            existing = next(c for c in candidates if c["name"] == "existing")
            self.assertTrue(existing["existing_candidate"])
            self.assertEqual(existing["next_action"], "validate_or_integrate")
            self.assertNotIn("equivalent", existing)
            self.assertEqual(candidates[1]["name"], "existing")

    def test_filters_category_size_status_image_bounds_and_asm_requirement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = self.fixture(root)
            self.assertEqual([c["name"] for c in find_semantic_candidates(
                ledger, root, category="UI", max_size=16)], ["prefix_only"])
            self.assertEqual([c["name"] for c in find_semantic_candidates(
                ledger, root, statuses=("todo",))], ["unmapped"])
            self.assertEqual(find_semantic_candidates(
                ledger, root, statuses=("todo",), asm_backed_only=True), [])
            self.assertEqual(find_semantic_candidates(ledger, root, code_bytes=bytes(1)), [])

    def test_cli_defaults_to_semantic_discovery_and_writes_reviewable_queue(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            output = root / "build/queue.json"
            with patch.object(sys, "argv", ["find_candidates.py", "--root", str(root),
                    "--limit", "2", "--output", str(output)]), redirect_stdout(io.StringIO()):
                main()
            report = json.loads(output.read_text())
            self.assertEqual(report["objective"], "editable_cpp_semantic_behavior")
            self.assertEqual(report["active_milestone"], "H1")
            self.assertEqual(len(report["candidates"]), 2)
            self.assertEqual(report["candidates"][0]["name"], "menu_callback")
            self.assertIn("not identical bytes", report["note"])


if __name__ == "__main__":
    unittest.main()
