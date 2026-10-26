import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.agent_workflow import (
    check_handoff, fingerprint, overlaps, prepare, ready_tasks, relative_path, validate_board,
)


def task(task_id="alpha", **changes):
    result = {"id": task_id, "role": "implementation", "state": "queued", "owner": None,
              "goal": "Recover one bounded behavior", "acceptance": ["Differential evidence"],
              "read_paths": ["inputs/reference.cpp"], "write_paths": [f"candidates/{task_id}.cpp"],
              "depends_on": [], "function_claims": [], "compiler_slots": 1,
              "exclusive_resources": []}
    result.update(changes)
    return result


def board(*tasks):
    return {"schema_version": 1, "batch": "H1-test", "milestone": "H1",
            "max_workers": 3, "cpu_budget": 8,
            "coordinator_owned_paths": ["config", "include", "tools/shared.py"],
            "tasks": list(tasks)}


class TestAgentBoard(unittest.TestCase):
    def test_ready_work_waits_for_accepted_dependency(self):
        plan = board(task("research"), task("implementation", depends_on=["research"]))
        self.assertEqual(validate_board(plan), [])
        self.assertEqual([t["id"] for t in ready_tasks(plan)], ["research"])
        plan["tasks"][0]["state"] = "accepted"
        self.assertEqual([t["id"] for t in ready_tasks(plan)], ["implementation"])

    def test_missing_dependencies_cycles_and_active_prerequisites_are_rejected(self):
        for plan in (board(task(depends_on=["missing"])),
                     board(task("a", depends_on=["b"]), task("b", depends_on=["a"])),
                     board(task("a"), task("b", depends_on=["a"], state="claimed", owner="worker"))):
            with self.subTest(plan=plan):
                self.assertTrue(validate_board(plan))

    def test_active_write_write_and_frozen_input_conflicts(self):
        first = task("a", state="working", owner="one", write_paths=["src/Shared.cpp"])
        for second in (task("b", state="working", owner="two", write_paths=["src/shared.cpp"]),
                       task("b", state="working", owner="two", read_paths=["src/shared.cpp"]),
                       task("b", state="working", owner="two", write_paths=["src"])):
            with self.subTest(second=second):
                self.assertTrue(any("conflict" in e for e in validate_board(board(first, second))))
        second = task("b", state="queued", write_paths=["src/Shared.cpp"])
        self.assertEqual(validate_board(board(first, second)), [])

    def test_cpu_worker_function_and_runtime_budgets(self):
        one = task("a", state="working", owner="one", compiler_slots=5,
                   function_claims=["0x0010ABCD"], exclusive_resources=["Azahar"])
        two = task("b", state="working", owner="two", compiler_slots=4,
                   function_claims=["0x0010abcd"], exclusive_resources=["azahar"])
        errors = validate_board(board(one, two))
        self.assertTrue(any("CPU" in e for e in errors))
        self.assertTrue(any("function_claims" in e for e in errors))
        self.assertTrue(any("exclusive_resources" in e for e in errors))
        plan = board(*[task(str(i), state="claimed", owner=str(i)) for i in range(4)])
        self.assertTrue(any("worker count" in e for e in validate_board(plan)))

    def test_shared_files_and_integration_are_coordinator_owned(self):
        plan = board(task(write_paths=["include/new.h"]))
        self.assertTrue(any("coordinator-owned" in e for e in validate_board(plan)))
        plan = board(task(role="integration", state="claimed", owner="worker"))
        self.assertTrue(any("integrator" in e for e in validate_board(plan)))

    def test_implicit_instruction_inputs_are_frozen_against_other_writers(self):
        worker = task("worker", state="working", owner="worker")
        integrator = task("integration", role="integration", state="working",
                          owner="integrator", write_paths=["AGENTS.md"])
        self.assertTrue(any("conflict" in e for e in validate_board(board(worker, integrator))))

    def test_collection_fields_require_lists_of_nonempty_strings(self):
        for field in ("acceptance", "validation_plan", "read_paths", "write_paths",
                      "depends_on", "function_claims", "exclusive_resources"):
            for value in ("not a list", [None], [" "]):
                with self.subTest(field=field, value=value):
                    self.assertTrue(validate_board(board(task(**{field: value}))))

    def test_blocked_work_releases_owner_and_records_unblock_condition(self):
        plan = board(task(state="blocked"))
        self.assertTrue(validate_board(plan))
        plan["tasks"][0].update(blocker="Missing caller contract", unblock_condition="Verified callsite")
        self.assertEqual(validate_board(plan), [])
        self.assertEqual(ready_tasks(plan), [])

    def test_paths_do_not_escape_and_prefixes_do_not_collide_by_accident(self):
        for value in ("../elsewhere", "/absolute", "C:\\absolute", "C:relative", "src/*.cpp", "."):
            with self.subTest(value=value), self.assertRaises(ValueError):
                relative_path(value)
        self.assertFalse(overlaps("src/a.cpp", "src/a.cpp.bak"))
        self.assertTrue(overlaps("src", "src/a.cpp"))

    def test_real_current_board_is_valid_and_ready_tasks_are_schedulable(self):
        root = Path(__file__).resolve().parents[1]
        plan = json.loads((root / "config/agent-workflows/h1.json").read_text())
        self.assertEqual(validate_board(plan), [])
        ready = ready_tasks(plan)
        accepted = {item["id"] for item in plan["tasks"] if item["state"] == "accepted"}
        self.assertTrue(all(item["state"] == "queued" and
                            set(item.get("depends_on", [])) <= accepted for item in ready))
        for item in ready:
            for relative in item["read_paths"]:
                self.assertTrue((root / relative).is_file(), relative)


class TestAgentPackets(unittest.TestCase):
    def fixture(self, root):
        (root / "inputs").mkdir()
        (root / "inputs/reference.cpp").write_text("original input")
        (root / "candidates").mkdir()
        (root / "candidates/alpha.cpp").write_text("old candidate")
        (root / "config").mkdir()
        (root / "config/game_info.json").write_text(json.dumps({"code_sha256": "pinned-image"}))
        plan = board(task(state="claimed", owner="worker-alpha",
                          read_paths=["inputs/reference.cpp", "candidates/alpha.cpp"]))
        with patch("tools.agent_workflow.subprocess.run", return_value=
                   subprocess.CompletedProcess([], 0, "base-commit\n", "")):
            output = prepare(root, plan, "alpha", "run-001")
        packet = json.loads((output / "task.json").read_text())
        (root / "candidates/alpha.cpp").write_text("new readable candidate")
        report = output / "checks/report.json"
        report.parent.mkdir()
        report.write_text('{"passed": true}')
        handoff = {"task_id": "alpha", "owner": "worker-alpha", "outcome": "ready_for_review",
                   "summary": "Bounded function cases checked", "next_action": "Independent caller review",
                   "changed_files": [{"path": "candidates/alpha.cpp",
                                      "sha256": fingerprint(root / "candidates/alpha.cpp")}],
                   "checks": [{"argv": ["python", "focused_check.py"], "exit_code": 0}],
                   "reports": [{"path": report.relative_to(root).as_posix(), "sha256": fingerprint(report)}],
                   "evidence": {"compiled": "passed", "arm_differential": "partial",
                                "caller": "not_run", "runtime": "not_run"}}
        return plan, packet, handoff, output

    def test_owned_inputs_can_change_but_frozen_inputs_and_scope_are_pinned(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan, packet, handoff, _ = self.fixture(root)
            self.assertEqual(packet["base_commit"], "base-commit")
            self.assertIn("candidates/alpha.cpp", packet["writable_baseline_sha256"])
            self.assertNotIn("candidates/alpha.cpp", packet["input_sha256"])
            self.assertEqual(check_handoff(root, packet, handoff, plan), [])
            changed_scope = copy.deepcopy(plan)
            changed_scope["tasks"][0]["owner"] = "another-worker"
            self.assertTrue(any("assignment" in e for e in check_handoff(root, packet, handoff, changed_scope)))
            (root / "inputs/reference.cpp").write_text("changed while testing")
            self.assertTrue(any("Frozen input changed" in e for e in check_handoff(root, packet, handoff)))

    def test_unowned_edits_stale_reports_and_wrong_exits_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, packet, handoff, output = self.fixture(root)
            handoff["changed_files"][0]["path"] = "inputs/reference.cpp"
            handoff["checks"][0]["exit_code"] = 1
            (output / "checks/report.json").write_text("failed rerun")
            errors = check_handoff(root, packet, handoff)
            self.assertTrue(any("Unowned" in e for e in errors))
            self.assertTrue(any("Report missing or changed" in e for e in errors))
            self.assertTrue(any("Unexpected command exit" in e for e in errors))

    def test_other_run_reports_and_unbacked_pass_claims_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, packet, handoff, _ = self.fixture(root)
            handoff["reports"][0]["path"] = "build/old-run/report.json"
            self.assertTrue(any("outside this task/run" in e for e in check_handoff(root, packet, handoff)))
            handoff["reports"] = []
            self.assertTrue(any("hashed reports" in e for e in check_handoff(root, packet, handoff)))

    def test_malformed_command_records_cannot_pass_exit_checks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, packet, handoff, _ = self.fixture(root)
            for check in ({"argv": ["python"], "expected_exit": None},
                          {"argv": ["python", 7], "exit_code": 0},
                          {"argv": ["python"], "exit_code": False},
                          {"argv": ["python"], "exit_code": 0, "expected_exit": True}):
                with self.subTest(check=check):
                    handoff["checks"] = [check]
                    self.assertTrue(check_handoff(root, packet, handoff))

    def test_draft_does_not_claim_work_and_run_directories_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan, packet, handoff, _ = self.fixture(root)
            with patch("tools.agent_workflow.subprocess.run", return_value=
                       subprocess.CompletedProcess([], 0, "base-commit\n", "")):
                with self.assertRaises(FileExistsError):
                    prepare(root, plan, "alpha", "run-001")
                plan["tasks"][0].update(state="queued", owner=None)
                with self.assertRaises(ValueError):
                    prepare(root, plan, "alpha", "run-002")
                output = prepare(root, plan, "alpha", "preview", draft=True)
            draft = json.loads((output / "task.json").read_text())
            self.assertFalse(draft["dispatchable"])
            self.assertEqual(plan["tasks"][0]["state"], "queued")
            self.assertTrue(any("Draft" in e for e in check_handoff(root, draft, handoff)))


if __name__ == "__main__":
    unittest.main()
