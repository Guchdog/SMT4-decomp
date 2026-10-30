#!/usr/bin/env python3
"""Bounded 0x002CAEF0 ARM differential with explicit helper models.

The harness compares callback orchestration, not scheduler or helper semantics.
It hooks only direct callees at their entry addresses and records every model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang

try:
    import unicorn
    from unicorn import arm_const as arm
except ImportError:
    unicorn = None
    arm = None

SOURCE = ROOT / "experiments/semantic_equivalence/h2_secondary_candidate.cpp"
CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"
TEXT = 0x00100000
TEXT_SIZE = 0x00480000
INJECT = 0x01000000
INJECT_SIZE = 0x10000
DATA = 0x02000000
DATA_SIZE = 0x4000
WORK = DATA + 0x100
MANAGER = DATA + 0x1000
SCRIPT = DATA + 0x2000
STACK = 0x08000000
STACK_SIZE = 0x4000
SP = STACK + 0x2000
RETURN = INJECT + 0x8000
GLOBAL_WORK = 0x0044E2D0
MANAGER_GLOBAL = 0x0043DCB0
ENTRY = 0x002CAEF0
U32 = 0xFFFFFFFF

HELPERS = {
    0x002B9008: "counter_side_effect",
    0x002A755C: "script_cleanup_opaque",
    0x002C4360: "release_opaque",
    0x002BF41C: "task_registered_predicate",
    0x002C45B8: "task_state_update_opaque",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_unicorn() -> None:
    if unicorn is None:
        raise RuntimeError("Install the optional experiment dependencies from requirements-experiment.txt")


def compile_candidates(output: Path) -> tuple[dict[str, bytes], dict]:
    obj = output / "h2_secondary_candidate.o"
    built = compile_tu_armv6k(SOURCE, obj, ROOT)
    if built.returncode:
        raise RuntimeError(built.stderr or "ARMv6K candidate compilation failed")
    extracted = extract_elf_functions_detailed(obj)
    names = ("candidate_002caef0", "candidate_002caef0_wrong_count",
             "candidate_002caef0_wrong_order")
    bodies: dict[str, bytes] = {}
    relocations: dict[str, list] = {}
    for name in names:
        if name not in extracted:
            raise RuntimeError(f"missing compiled symbol {name}")
        body, relocs = extracted[name]
        relocations[name] = [r.__dict__ for r in relocs]
        if relocs:
            raise RuntimeError(f"unsupported relocation in {name}: {relocs}")
        if len(body) > 0x7000:
            raise RuntimeError(f"candidate blob is too large for local code arena: {name}")
        bodies[name] = body
    details = {
        "argv": built.args,
        "exit_code": built.returncode,
        "object_path": str(obj),
        "object_sha256": sha256(obj.read_bytes()),
        "compiler_version": subprocess.run(
            [str(find_clang()), "--version"], check=True, capture_output=True,
            text=True).stdout.splitlines()[0],
        "candidate_bytes": {name: len(body) for name, body in bodies.items()},
        "relocations": relocations,
    }
    return bodies, details


def make_cases() -> list[dict]:
    """Directed loop, nullable-slot, predicate, and manager-boundary cases."""
    base = {"counter_a": 0, "counter_b": 0, "script": True,
            "first": True, "second": True, "active": True,
            "manager_halfword": 11, "context": 0xA5A55A5A}
    cases = [{"label": "zero-both", **base}]
    for label, field, value in (
        ("counter-a-negative", "counter_a", -1),
        ("counter-a-one", "counter_a", 1),
        ("counter-a-four", "counter_a", 4),
        ("counter-b-negative", "counter_b", -1),
        ("counter-b-one", "counter_b", 1),
        ("counter-b-four", "counter_b", 4),
    ):
        case = dict(base); case[field] = value; cases.append({"label": label, **case})
    for label, field in (("script-null", "script"), ("first-null", "first"),
                         ("second-null", "second")):
        case = dict(base); case[field] = False; cases.append({"label": label, **case})
    for active in (False, True):
        case = dict(base); case["active"] = active
        cases.append({"label": f"task-active-{str(active).lower()}", **case})
    for value in (9, 10, 11, 12):
        case = dict(base); case["manager_halfword"] = value; case["counter_a"] = 1
        cases.append({"label": f"manager-boundary-{value}", **case})
    # Exercise independent loops together and both cleanup slots with unique IDs.
    case = dict(base); case.update(counter_a=2, counter_b=3, manager_halfword=12)
    cases.append({"label": "both-loops-distinct", **case})
    return cases


class Run:
    def __init__(self, image: bytes, entry: int, candidate: bytes | None,
                 case: dict, seed: int):
        require_unicorn()
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, TEXT_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, INJECT_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        if candidate is not None:
            self.uc.mem_write(INJECT, candidate)
            entry = INJECT
        self.entry = entry
        self.case = case
        self.seed = seed
        self.trace: list[dict] = []
        self.writes: list[int] = []
        self.stopped = False
        self.fault: str | None = None
        self._clobber = 0
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self._initialize()

    def _initialize(self) -> None:
        uc = self.uc
        uc.mem_write(DATA, bytes(((i * 31 + self.seed) & 0xFF) for i in range(DATA_SIZE)))
        work = bytearray(((i * 17 + self.seed) & 0xFF) for i in range(0x158))
        struct.pack_into("<I", work, 0, 0x01234000)
        struct.pack_into("<h", work, 0x1A, self.case["counter_a"])
        struct.pack_into("<h", work, 0x24, self.case["counter_b"])
        struct.pack_into("<I", work, 0x14C, DATA + 0x3100 if self.case["first"] else 0)
        struct.pack_into("<I", work, 0x150, DATA + 0x3200 if self.case["second"] else 0)
        struct.pack_into("<I", work, 0x154, SCRIPT if self.case["script"] else 0)
        uc.mem_write(WORK, bytes(work))
        uc.mem_write(GLOBAL_WORK, struct.pack("<I", WORK))
        uc.mem_write(MANAGER_GLOBAL + 4, struct.pack("<I", MANAGER - 0x600))
        struct.pack_into("<h", bytearray(2), 0, 0)
        uc.mem_write(MANAGER + 0x64A, struct.pack("<h", self.case["manager_halfword"]))
        uc.mem_write(SP - 0x40, bytes(((0xA0 + i + self.seed) & 0xFF) for i in range(0x80)))
        uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        for index in range(13):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_R{index}"), (0x51000000 + index * 0x10203) & U32)
        uc.reg_write(arm.UC_ARM_REG_R0, self.case["context"])
        uc.reg_write(arm.UC_ARM_REG_SP, SP)
        uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        for index in range(8, 16):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_D{index}"), (0x1122334400000000 + index) & 0xFFFFFFFFFFFFFFFF)
        self.before = self._preserved()
        # AAPCS callees own memory below entry SP while saving registers or
        # spilling. Only the caller-owned area at and above entry SP is checked.
        self.stack_before = bytes(uc.mem_read(SP, 0x40))

    def _preserved(self) -> list[int]:
        uc = self.uc
        result = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)]
        result.append(uc.reg_read(arm.UC_ARM_REG_SP))
        result.extend(uc.reg_read(getattr(arm, f"UC_ARM_REG_D{i}")) for i in range(8, 16))
        return result

    def _arguments(self) -> list[int]:
        return [self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4)]

    def _on_write(self, uc, access, address, size, value, _):
        watched = ((WORK <= address < WORK + 0x158) or
                   (GLOBAL_WORK <= address < GLOBAL_WORK + 4) or
                   (MANAGER + 0x64A <= address < MANAGER + 0x64C))
        if watched:
            self.writes.extend(range(address, address + size))

    def _set_return(self, value: int) -> None:
        uc = self.uc
        salt = (0x6D2B0000 ^ (self._clobber * 0x010203)) & U32
        for index, reg in enumerate((arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2,
                                     arm.UC_ARM_REG_R3, arm.UC_ARM_REG_R12)):
            uc.reg_write(reg, (salt + index * 0x1111) & U32)
        for index in range(4):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_S{index}"), (salt + index * 0x10001) & U32)
        uc.reg_write(arm.UC_ARM_REG_R0, value & U32)
        uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
        self._clobber += 1

    def _on_code(self, uc, address, size, _):
        if address == RETURN:
            self.stopped = True
            uc.emu_stop()
            return
        if address not in HELPERS:
            return
        args = self._arguments()
        self.trace.append({"address": f"0x{address:08x}", "name": HELPERS[address],
                           "r0_r3": [f"0x{x:08x}" for x in args]})
        if address == 0x002B9008:
            # Exact direct helper effect from its 36-byte body: manager halfword
            # is decremented iff signed value > 10; r0 is ignored.
            current = struct.unpack("<h", bytes(uc.mem_read(MANAGER + 0x64A, 2)))[0]
            if current > 10:
                uc.mem_write(MANAGER + 0x64A, struct.pack("<h", current - 1))
            self._set_return(0xACED0001)
        elif address == 0x002BF41C:
            self._set_return(int(self.case["active"]))
        else:
            # Opaque cleanup/release/task-state boundaries are traced only.
            # Their deep side effects and scheduler interpretation are omitted.
            self._set_return(0xACED0000 | (address & 0xFFFF))

    def run(self) -> dict:
        try:
            self.uc.emu_start(self.entry, 0, count=100000)
        except unicorn.UcError as error:
            self.fault = str(error)
        manager_value = struct.unpack("<h", bytes(self.uc.mem_read(MANAGER + 0x64A, 2)))[0]
        return {
            "stopped": self.stopped, "fault": self.fault,
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "r0_diagnostic": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "preserved": self._preserved(), "preserved_before": self.before,
            "stack": bytes(self.uc.mem_read(SP, 0x40)).hex(),
            "stack_before": self.stack_before.hex(),
            "work": bytes(self.uc.mem_read(WORK, 0x158)).hex(),
            "global_work": bytes(self.uc.mem_read(GLOBAL_WORK, 4)).hex(),
            "manager_halfword": manager_value,
            "trace": self.trace, "writes": sorted(set(self.writes)),
        }


def compare(left: dict, right: dict) -> str | None:
    for label, result in (("original", left), ("candidate", right)):
        if result["fault"]:
            return f"{label} fault: {result['fault']}"
        if not result["stopped"]:
            return f"{label} did not return to sentinel"
        if result["preserved"] != result["preserved_before"]:
            return f"{label} violated callee-preserved GPR/SP/VFP state"
        if result["stack"] != result["stack_before"]:
            return f"{label} changed caller stack frame"
    if normalized_trace(left["trace"]) != normalized_trace(right["trace"]):
        return "declared helper arguments/order differ"
    for field in ("work", "global_work", "manager_halfword", "writes"):
        if left[field] != right[field]:
            return f"{field} differs"
    # r0 on this void ARM entry is incidental; record but do not compare it.
    return None


def normalized_trace(trace: list[dict]) -> list[dict]:
    argument_counts = {
        0x002B9008: 1,
        0x002A755C: 1,
        0x002C4360: 1,
        0x002BF41C: 1,
        0x002C45B8: 2,
    }
    result = []
    for item in trace:
        address = int(item["address"], 16)
        result.append({"address": item["address"], "name": item["name"],
                       "args": item["r0_r3"][:argument_counts[address]]})
    return result


def execute(image: bytes, entry: int, candidate: bytes | None, case: dict, seed: int) -> dict:
    return Run(image, entry, candidate, case, seed).run()


def run_experiment(code_path: Path, output: Path, seed: int) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    if len(image) != game["code_bin_size"] or sha256(image) != game["code_sha256"]:
        raise ValueError("code.bin does not match configured pinned original")
    source_hash = sha256(SOURCE.read_bytes())
    bodies, build = compile_candidates(output)
    cases = make_cases()
    results = []
    mismatches = []
    for case in cases:
        original = execute(image, ENTRY, None, case, seed)
        candidate = execute(image, ENTRY, bodies["candidate_002caef0"], case, seed)
        error = compare(original, candidate)
        results.append({"case": case, "error": error,
                        "original": original, "candidate": candidate})
        if error:
            mismatches.append({"case": case["label"], "reason": error,
                               "original": original, "candidate": candidate})
            break
    control_case = next(c for c in cases if c["label"] == "both-loops-distinct")
    negative_controls = []
    for name in ("candidate_002caef0_wrong_count", "candidate_002caef0_wrong_order"):
        original = execute(image, ENTRY, None, control_case, seed)
        mutant = execute(image, ENTRY, bodies[name], control_case, seed)
        difference = compare(original, mutant)
        negative_controls.append({"name": name, "detected": difference is not None,
                                  "difference": difference})
    if sha256(SOURCE.read_bytes()) != source_hash:
        raise RuntimeError("candidate source changed during experiment")
    report = {
        "schema": 1, "passed": not mismatches and all(x["detected"] for x in negative_controls),
        "scope": "0x002CAEF0 cleanup orchestration under explicit helper-entry models",
        "reference_sha256": game["code_sha256"], "image_sha256": sha256(image),
        "source_sha256": source_hash, "build": build, "seed": seed,
        "cases_total": len(cases), "cases_compared": len(results),
        "case_labels": [c["label"] for c in cases],
        "first_counterexample": mismatches[0] if mismatches else None,
        "negative_controls": negative_controls,
        "example_trace": results[0]["candidate"]["trace"] if results else [],
        "summary_results": [
            {"case": row["case"]["label"], "error": row["error"],
             "trace_count": len(row["candidate"]["trace"]),
             "manager_after": row["candidate"]["manager_halfword"]}
            for row in results],
        "helper_models": {
            "0x002B9008": "direct side effect modeled exactly from checked-in 36-byte body: manager halfword at global+4 object+0x64A decremented only if signed value > 10; r0 ignored",
            "0x002BF41C": "configurable active-predicate return; lookup/list side effects omitted",
            "0x002A755C": "trace-only; nested script resource/list cleanup omitted",
            "0x002C4360": "trace-only; allocator/free manager effects omitted",
            "0x002C45B8": "trace-only; task state/scheduler effects omitted",
        },
        "limits": [
            "This is ARM differential evidence for direct orchestration under shared declared stubs, not full helper or runtime equivalence.",
            "Only the direct manager-halfword mutation of 0x002B9008 is modeled; the other helpers are trace-only boundaries, including task transition and frees.",
            "The callback reads a global work pointer, has no null guard, and requires a valid 0x158-byte work fixture; no allocator failure or invalid-pointer behavior is tested.",
            "Scheduler invocation/order/count, task/work lifetime, reentry, caller behavior, UI edits, persistence, and emulator runtime remain untested.",
        ],
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    report = run_experiment(args.code, args.output, args.seed)
    print(json.dumps({"passed": report["passed"], "scope": report["scope"],
                      "report": str(args.output / "report.json"),
                      "cases_compared": report["cases_compared"],
                      "first_counterexample": report["first_counterexample"],
                      "negative_controls": report["negative_controls"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
