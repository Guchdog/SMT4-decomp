"""Check coordinator-owned task boards and prepare reproducible subagent briefs.

This tool neither spawns agents nor approves semantic equivalence. The coordinator
alone edits the board. Ownership and provenance checks supplement code review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
STATES = {"queued", "claimed", "working", "review", "accepted", "blocked"}
LEASED = {"claimed", "working", "review"}
ROLES = {"recon", "implementation", "validation", "integration"}
LEVELS = {"not_run", "passed", "partial", "failed"}
BOOTSTRAP_INPUTS = ("AGENTS.md", "docs/agent-workflow.md", "config/reconstruction.json",
                    "config/game_info.json", "tools/agent_workflow.py")


def effective_reads(task: dict) -> list[str]:
    """Include the instruction and policy inputs frozen in every task packet."""
    return sorted(set(task.get("read_paths", []) + list(BOOTSTRAP_INPUTS)))


def relative_path(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if (not value or path.is_absolute() or PureWindowsPath(value).drive
            or ".." in path.parts or str(path) == "." or any(c in value for c in "*?[]")):
        raise ValueError(f"Expected a concrete repository-relative path: {value!r}")
    return path.as_posix()


def overlaps(left: str, right: str) -> bool:
    a, b = relative_path(left).casefold(), relative_path(right).casefold()
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_board(board: dict) -> list[str]:
    errors = []
    tasks = board.get("tasks", [])
    if not isinstance(tasks, list) or any(not isinstance(task, dict) for task in tasks):
        return ["Board tasks must be a list of task objects"]
    if board.get("schema_version") != 1:
        errors.append("Unsupported board schema")
    max_workers, cpu_budget = board.get("max_workers", 3), board.get("cpu_budget", 8)
    if type(max_workers) is not int or max_workers < 1 or type(cpu_budget) is not int or cpu_budget < 1:
        return errors + ["Worker and CPU budgets must be positive integers"]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", board.get("batch", "")):
        errors.append("Board needs a safe batch identifier")
    ids = [task.get("id") for task in tasks]
    if any(not isinstance(x, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", x)
           for x in ids) or len(set(ids)) != len(ids):
        return errors + ["Task IDs must be unique safe identifiers"]
    by_id = dict(zip(ids, tasks))
    protected = board.get("coordinator_owned_paths", [])
    collections = [("coordinator_owned_paths", protected)]
    for task in tasks:
        collections.extend((f"{task['id']}: {field}", task.get(field, [])) for field in (
            "acceptance", "validation_plan", "read_paths", "write_paths", "depends_on",
            "function_claims", "exclusive_resources"))
    for label, values in collections:
        if not isinstance(values, list) or any(
                not isinstance(value, str) or not value.strip() for value in values):
            errors.append(f"{label} must be a list of nonempty strings")
    if errors:
        return errors
    try:
        for value in protected:
            relative_path(value)
    except ValueError as error:
        errors.append(str(error))
    for task in tasks:
        label = task["id"]
        if task.get("state") not in STATES or task.get("role") not in ROLES:
            errors.append(f"{label}: invalid role or state")
        if not isinstance(task.get("goal"), str) or not task["goal"].strip() or not task.get("acceptance"):
            errors.append(f"{label}: goal and acceptance criteria are required")
        owner, state = task.get("owner"), task.get("state")
        if state in LEASED and (not isinstance(owner, str) or not owner.strip()):
            errors.append(f"{label}: an active task needs an owner")
        if state in {"queued", "blocked"} and owner is not None:
            errors.append(f"{label}: queued/blocked tasks must release their owner")
        if state == "blocked" and (not task.get("blocker") or not task.get("unblock_condition")):
            errors.append(f"{label}: blocked tasks need a blocker and unblock condition")
        if task.get("role") == "integration" and state in LEASED and owner != "integrator":
            errors.append(f"{label}: integration belongs to the integrator")
        for dependency in task.get("depends_on", []):
            if dependency not in by_id:
                errors.append(f"{label}: unknown dependency {dependency}")
            elif state in LEASED | {"accepted"} and by_id[dependency]["state"] != "accepted":
                errors.append(f"{label}: dependency {dependency} is not accepted")
        for field in ("read_paths", "write_paths"):
            for value in task.get(field, []):
                try:
                    relative_path(value)
                    if field == "write_paths" and task.get("role") != "integration" and any(
                            overlaps(value, item) for item in protected):
                        errors.append(f"{label}: coordinator-owned path {value}")
                except ValueError as error:
                    errors.append(f"{label}: {error}")
        slots = task.get("compiler_slots", 0)
        if type(slots) is not int or slots < 0:
            errors.append(f"{label}: compiler_slots must be nonnegative")
        if any(not re.fullmatch(r"0x[0-9a-fA-F]{8}", item)
               for item in task.get("function_claims", [])):
            errors.append(f"{label}: function claims must be full hexadecimal addresses")
    visiting, done = set(), set()

    def visit(task_id):
        if task_id in visiting:
            errors.append(f"Dependency cycle at {task_id}")
            return
        if task_id in done:
            return
        visiting.add(task_id)
        for dependency in by_id[task_id].get("depends_on", []):
            if dependency in by_id:
                visit(dependency)
        visiting.remove(task_id)
        done.add(task_id)

    for task_id in ids:
        visit(task_id)
    active = [task for task in tasks if task.get("state") in LEASED]
    workers = [task for task in active if task.get("owner") != "integrator"]
    if len(workers) > max_workers:
        errors.append("Active worker count exceeds the board budget")
    if sum(task.get("compiler_slots", 0) for task in active
           if isinstance(task.get("compiler_slots", 0), int)) > cpu_budget:
        errors.append("Compiler allocation exceeds the board CPU budget")
    for i, left in enumerate(active):
        for right in active[i + 1:]:
            pair = f"{left['id']} / {right['id']}"
            if left.get("owner") == right.get("owner"):
                errors.append(f"{pair}: one agent cannot own two active tasks")
            for field in ("function_claims", "exclusive_resources"):
                if {item.casefold() for item in left.get(field, [])} & {
                        item.casefold() for item in right.get(field, [])}:
                    errors.append(f"{pair}: overlapping {field}")
            for writer, reader in ((left, right), (right, left)):
                try:
                    if any(overlaps(a, b) for a in writer.get("write_paths", [])
                           for b in reader.get("write_paths", []) + effective_reads(reader)):
                        errors.append(f"{pair}: write/write or write/frozen-input conflict")
                except ValueError:
                    pass  # Invalid paths were already reported above.
    return errors


def ready_tasks(board: dict) -> list[dict]:
    accepted = {task["id"] for task in board["tasks"] if task["state"] == "accepted"}
    return [task for task in board["tasks"] if task["state"] == "queued"
            and set(task.get("depends_on", [])) <= accepted]


def prepare(root: Path, board: dict, task_id: str, run: str, draft: bool = False) -> Path:
    errors = validate_board(board)
    if errors:
        raise ValueError("; ".join(errors))
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run):
        raise ValueError("Run ID must be a safe identifier")
    task = next((item for item in board["tasks"] if item["id"] == task_id), None)
    if task is None:
        raise ValueError(f"Unknown task {task_id}")
    if draft:
        if task not in ready_tasks(board):
            raise ValueError("Only a schedulable queued task can have a draft packet")
    elif task["state"] != "claimed":
        raise ValueError("Coordinator must claim and validate the task before dispatch")
    inputs, writable_baseline = {}, {}
    for value in effective_reads(task):
        if value in BOOTSTRAP_INPUTS and not (root / value).is_file():
            continue
        relative = relative_path(value)
        target = writable_baseline if any(overlaps(relative, owned)
            for owned in task.get("write_paths", [])) else inputs
        target[relative] = fingerprint(root / relative)
    revision = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    info = json.loads((root / "config/game_info.json").read_text(encoding="utf-8"))
    output = root / "build" / "agent-work" / board["batch"] / task_id / run
    output.mkdir(parents=True, exist_ok=False)
    packet = {"schema_version": 1, "dispatchable": not draft,
              "milestone": board["milestone"], "base_commit": revision,
              "reference_sha256": info["code_sha256"], "task": task,
              "input_sha256": inputs, "writable_baseline_sha256": writable_baseline,
              "output_root": output.relative_to(root).as_posix()}
    (output / "task.json").write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    brief = [f"# {task_id}: {task['goal']}", "",
             "DRAFT — claim the task before dispatch." if draft else f"Assigned owner: {task['owner']}", "",
             "Read AGENTS.md, docs/agent-workflow.md, and task.json before work.",
             "Semantic behavior is the goal; byte identity is not required.",
             "Edit only assigned write paths. Read dependencies must remain frozen.",
             "Do not edit the task board, shared runner/interfaces, or other workers' files.",
             "Do not run full builds/regressions or use the canonical build cache as a worker.",
             f"Use fresh outputs under `{packet['output_root']}` and compiler budget {task.get('compiler_slots', 0)}.",
             "Inspect each runner's CLI: --output may be a file or directory.",
             "Do not switch branches, commit, push, or control the emulator outside your assigned task.",
             "", "## Owned files", *[f"- {p}" for p in task.get("write_paths", [])],
             "", "## Acceptance", *[f"- {item}" for item in task["acceptance"]],
             "", "## Validation plan", *[f"- {item}" for item in task.get("validation_plan", [])],
             "", "Return a handoff using docs/templates/agent-handoff.json, with source/report hashes,",
             "commands and exits, evidence levels, limitations, and next action. Report blockers early.",
             "A packet or report does not establish equivalence. Do not weaken validators to get a pass.", ""]
    (output / "brief.md").write_text("\n".join(brief), encoding="utf-8")
    return output


def check_handoff(root: Path, packet: dict, handoff: dict, current_board: dict | None = None) -> list[str]:
    errors = []
    task = packet["task"]
    if current_board is not None:
        current = next((item for item in current_board["tasks"] if item["id"] == task["id"]), None)
        if current is None or current.get("state") not in LEASED or any(
                current.get(field) != task.get(field)
                for field in ("owner", "role", "goal", "acceptance", "validation_plan",
                              "write_paths", "read_paths", "depends_on", "function_claims",
                              "compiler_slots", "exclusive_resources")):
            errors.append("Task assignment or scope changed since dispatch")
    if not packet.get("dispatchable"):
        errors.append("Draft packets cannot authorize a worker handoff")
    if handoff.get("task_id") != task["id"] or handoff.get("owner") != task["owner"]:
        errors.append("Handoff task/owner differs from dispatch")
    if handoff.get("outcome") not in {"ready_for_review", "blocked"}:
        errors.append("Handoff outcome must be ready_for_review or blocked")
    for relative, expected in packet["input_sha256"].items():
        path = root / relative_path(relative)
        if not path.is_file() or fingerprint(path) != expected:
            errors.append(f"Frozen input changed: {relative}")
    info = json.loads((root / "config/game_info.json").read_text(encoding="utf-8"))
    if info["code_sha256"] != packet["reference_sha256"]:
        errors.append("Configured reference image identity changed")
    for item in handoff.get("changed_files", []):
        relative = relative_path(item["path"])
        if not any(relative.casefold() == relative_path(owned).casefold() or
                   relative.casefold().startswith(relative_path(owned).casefold().rstrip("/") + "/")
                   for owned in task.get("write_paths", [])):
            errors.append(f"Unowned changed file: {relative}")
        path = root / relative
        actual = fingerprint(path) if path.is_file() else None
        if actual != item.get("sha256"):
            errors.append(f"Changed file hash mismatch: {relative}")
    for item in handoff.get("reports", []):
        relative = relative_path(item["path"])
        if not relative.startswith(packet["output_root"].rstrip("/") + "/"):
            errors.append(f"Report is outside this task/run: {relative}")
        path = root / relative
        if not path.is_file() or fingerprint(path) != item.get("sha256"):
            errors.append(f"Report missing or changed: {relative}")
    for check in handoff.get("checks", []):
        if (not isinstance(check.get("argv"), list) or not check["argv"] or any(
                not isinstance(arg, str) or not arg.strip() for arg in check["argv"])):
            errors.append("Every command check needs a nonempty string argv list")
        if type(check.get("exit_code")) is not int or type(check.get("expected_exit", 0)) is not int:
            errors.append("Command exit_code and expected_exit must be explicit integers")
        elif check["exit_code"] != check.get("expected_exit", 0):
            errors.append(f"Unexpected command exit: {check.get('argv')}")
    evidence = handoff.get("evidence", {})
    for level in ("compiled", "arm_differential", "caller", "runtime"):
        if evidence.get(level) not in LEVELS:
            errors.append(f"Missing or invalid evidence level: {level}")
    if not handoff.get("summary") or not handoff.get("next_action"):
        errors.append("Summary and next action are required")
    if handoff.get("outcome") == "ready_for_review" and not handoff.get("changed_files"):
        errors.append("A review handoff must identify its owned deliverables")
    if any(value == "passed" for value in evidence.values()) and (
            not handoff.get("checks") or not handoff.get("reports")):
        errors.append("Passed execution evidence needs command records and hashed reports")
    if handoff.get("outcome") == "blocked" and (
            not handoff.get("blocker") or not handoff.get("unblock_condition")):
        errors.append("Blocked handoffs need a blocker and unblock condition")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "ready", "prepare", "check-handoff"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--board", type=Path)
    parser.add_argument("--task")
    parser.add_argument("--run")
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--handoff", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        policy = json.loads((root / "config/reconstruction.json").read_text(encoding="utf-8"))
        board_path = args.board or Path(policy["agent_workflow_board"])
        if not board_path.is_absolute():
            board_path = root / board_path
        board = json.loads(board_path.read_text(encoding="utf-8"))
        if args.command == "check-handoff":
            if not args.packet or not args.handoff:
                parser.error("check-handoff needs --packet and --handoff")
            errors = validate_board(board) + check_handoff(root,
                json.loads(args.packet.read_text(encoding="utf-8")),
                json.loads(args.handoff.read_text(encoding="utf-8")), board)
        else:
            errors = validate_board(board)
            if not errors and args.command == "ready":
                print(json.dumps(ready_tasks(board), indent=2))
            elif not errors and args.command == "prepare":
                if not args.task or not args.run:
                    parser.error("prepare needs --task and --run")
                print(prepare(root, board, args.task, args.run, args.draft))
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        if args.command in {"check", "check-handoff"}:
            print("Ownership/provenance checks passed; semantic approval still requires independent review.")
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
