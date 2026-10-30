#!/usr/bin/env python3
"""Bounded H2 initializer orchestration experiment with declared HLE boundaries.

This compares the pinned initializer with readable C++ under identical helper
stubs and real mapper/pair-copy bodies. It is not a full engine or runtime test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import time
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.semantic_experiment import require_unicorn

try:
    import unicorn
    from unicorn import arm_const as arm
except ImportError:
    unicorn = None
    arm = None

SOURCE = ROOT / "experiments/semantic_equivalence/h2_init_orchestration_candidate.cpp"
CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"
TEXT = 0x00100000
IMAGE_MAP_SIZE = 0x00480000
INJECT = 0x01000000
INJECT_SIZE = 0x10000
DATA = 0x02000000
DATA_SIZE = 0x10000
WORK = DATA + 0x100
TABLE = DATA + 0x800
STACK = 0x08000000
STACK_SIZE = 0x4000
SP = STACK + 0x2000
RETURN = INJECT + INJECT_SIZE - 4
GLOBAL_WORK = 0x0044E2D0
CONFIG = 0x0044E0F8
INIT = 0x002F4CA0
U32 = 0xFFFFFFFF

# Address: direct helper boundary logged at entry, and either faithfully allowed
# to execute in the pinned image (None) or intercepted with a declared HLE.
OBSERVED = {
    0x002C4B84: "alloc",
    0x002C5978: "create_calc_wrapper",
    0x002C4C00: "create_draw_wrapper",
    0x00118488: "process_factory_hle",
    0x002C3344: "sprite_group_init_original",
    0x002C32F8: "sprite_group_bind_original",
    0x002BDB2C: "sprite_setup_hle",
    0x002BDAC0: "sprite_set_anim_original",
    0x0029FAE8: "cursor_setup_hle",
    0x0027EDF8: "fill_pair_original",
    0x00297704: "load_table_hle",
    0x002B8B78: "sound_hle",
    0x0029F10C: "ui_reset_hle",
    0x002CAB70: "mapper_a_original",
    0x0021F39C: "mapper_b_original",
    0x002E0AF4: "mapper_c_original",
    0x002ADB40: "copy_pair_original",
}
HLE = {0x002C4B84, 0x00118488, 0x002BDB2C, 0x0029FAE8,
       0x00297704, 0x002B8B78, 0x0029F10C}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & -alignment


def build_cases(seed: int, samples: int) -> list[dict]:
    """Valid byte triples plus directed baseline/distinct config-word cases."""
    result = [
        {"label": "h1-baseline", "arg": 0, "config": bytes.fromhex("3250503000000000")},
        {"label": "distinct-words", "arg": 0xFFFFFFFF,
         "config": bytes.fromhex("0113273B4D5F7183")},
        {"label": "different-incoming-r0", "arg": 0xA5A55A5A,
         "config": bytes.fromhex("7F0080FF10203040")},
    ]
    rng = random.Random(seed)
    for index in range(samples):
        result.append({"label": f"seeded-{index}", "arg": rng.getrandbits(32),
                       "config": rng.randbytes(8)})
    return result


def _decode_cstr(uc, address: int, limit: int = 128) -> str:
    if not address:
        return "<null>"
    try:
        data = bytearray()
        for i in range(limit):
            byte = uc.mem_read(address + i, 1)[0]
            if byte == 0:
                break
            data.append(byte)
        return data.decode("ascii", errors="replace")
    except unicorn.UcError:
        return f"<unmapped:{address:#x}>"


class InitRun:
    def __init__(self, image: bytes, replacement: bytes | None, entry: int,
                 *, seed: int):
        require_unicorn()
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, IMAGE_MAP_SIZE,
                        unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, INJECT_SIZE,
                        unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        self.uc.mem_map(DATA, DATA_SIZE,
                        unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE,
                        unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        if replacement is not None:
            if len(replacement) > 0x4000:
                raise ValueError("candidate exceeds reserved code area")
            self.uc.mem_write(INJECT, replacement)
            entry = INJECT
        self.entry = entry
        self.seed = seed
        self.trace: list[dict] = []
        self.stopped = False
        self.fault: str | None = None
        self.step_count = 0
        self.next_task_token = 0x01110001
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE,
                         self._on_mem)
        self.access_reads: list[int] = []
        self.access_writes: list[int] = []
        self.clobber = 0

    def _stack_words(self, sp: int, count: int = 7) -> list[int]:
        try:
            return list(struct.unpack("<" + "I" * count,
                                      self.uc.mem_read(sp, 4 * count)))
        except unicorn.UcError:
            return []

    def _capture(self, address: int) -> dict:
        uc = self.uc
        regs = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4)]
        sp = uc.reg_read(arm.UC_ARM_REG_SP)
        s_regs = [uc.reg_read(getattr(arm, f"UC_ARM_REG_S{i}")) for i in range(4)]
        record = {"address": f"0x{address:08x}", "name": OBSERVED[address],
                  "r0_r3": [f"0x{x:08x}" for x in regs],
                  "stack_words": [f"0x{x:08x}" for x in self._stack_words(sp)],
                  "s0_s3_bits": [f"0x{x:08x}" for x in s_regs]}
        if address in (0x00118488, 0x00297704):
            record["r0_string"] = _decode_cstr(uc, regs[0])
        return record

    def _set_hle_return(self, value: int) -> None:
        uc = self.uc
        # Model caller-saved clobbers; the value is the documented boundary return.
        salt = (0xA5A50000 ^ self.clobber) & U32
        for index, reg in enumerate((arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2,
                                     arm.UC_ARM_REG_R3, arm.UC_ARM_REG_R12)):
            uc.reg_write(reg, (salt + index * 0x10203) & U32)
        for i in range(4):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_S{i}"),
                         (salt + 0x11111111 * i) & U32)
        uc.reg_write(arm.UC_ARM_REG_R0, value & U32)
        uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
        self.clobber += 1

    def _hook_allocator(self, record: dict) -> None:
        # HLE: return a fixed arena address and fill it with a deterministic
        # poison pattern. This isolates initializer-owned writes; it deliberately
        # does NOT model AsdMem_Alloc's successful zero-fill behavior.
        pattern = bytes(((i * 37 + self.seed) & 0xFF) for i in range(0x158))
        self.uc.mem_write(WORK, pattern)
        record["hle_effect"] = "return WORK; fill 0x158 bytes with case poison"
        self._set_hle_return(WORK)

    def _hook_process(self, record: dict) -> None:
        # HLE: record process-factory ABI words, return stable calc/draw handles;
        # no pool insertion, scheduling, parent linking, or lifecycle is modeled.
        record["hle_effect"] = "return deterministic task token; no scheduler/pool mutation"
        token = self.next_task_token
        self.next_task_token += 1
        self._set_hle_return(token)

    def _hook_sprite_setup(self, record: dict) -> None:
        # HLE sets only the sprite table pointer needed to exercise the real
        # 0x002BDAC0 body. It does not model the resource setup's other fields.
        sprite = int(record["r0_r3"][0], 16)
        self.uc.mem_write(sprite + 0x4C, struct.pack("<I", TABLE))
        self.uc.mem_write(TABLE, struct.pack("<4h", 12, 24, 36, 48))
        record["hle_effect"] = "write sprite+0x4c=TABLE; provide one synthetic coordinate row"
        self._set_hle_return(0xC001C0DE)

    def _hook_cursor_setup(self, record: dict) -> None:
        record["hle_effect"] = "record arguments only; cursor memory unchanged"
        self._set_hle_return(0xC001C0DE)

    def _hook_load(self, record: dict) -> None:
        # HLE represents enqueue-only async request: leaves output slot unchanged.
        record["hle_effect"] = "record async request; no completion or output-slot write"
        self._set_hle_return(0xABCD0001)

    def _hook_sound(self, record: dict) -> None:
        record["hle_effect"] = "record sound ID; no audio subsystem mutation"
        self._set_hle_return(0xABCD0002)

    def _hook_ui_reset(self, record: dict) -> None:
        record["hle_effect"] = "record mode/color only; shared UI global state unchanged"
        self._set_hle_return(0xABCD0003)

    def _on_code(self, uc, address: int, size: int, _):
        self.step_count += 1
        if address == RETURN:
            self.stopped = True
            uc.emu_stop()
            return
        if address not in OBSERVED:
            return
        record = self._capture(address)
        self.trace.append(record)
        if address not in HLE:
            return
        if address == 0x002C4B84:
            self._hook_allocator(record)
        elif address == 0x00118488:
            self._hook_process(record)
        elif address == 0x002BDB2C:
            self._hook_sprite_setup(record)
        elif address == 0x0029FAE8:
            self._hook_cursor_setup(record)
        elif address == 0x00297704:
            self._hook_load(record)
        elif address == 0x002B8B78:
            self._hook_sound(record)
        elif address == 0x0029F10C:
            self._hook_ui_reset(record)

    def _on_mem(self, uc, access, address, size, value, _):
        target = self.access_writes if access == unicorn.UC_MEM_WRITE else self.access_reads
        if WORK <= address < WORK + 0x158 or GLOBAL_WORK <= address < GLOBAL_WORK + 4 \
                or CONFIG <= address < CONFIG + 8:
            target.extend(range(address, address + size))

    def run(self, case: dict) -> dict:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        for i in range(13):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"),
                         (0x51510000 + i * 0x10101 + case["arg"]) & U32)
        uc.reg_write(arm.UC_ARM_REG_R0, case["arg"])
        # Distinct sentinels on callee-saved VFP regs make ABI corruption visible.
        for i in range(8, 16):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i}"),
                         ((0x11223344 + i) << 32) | (0xAABBCC00 + i))
        uc.reg_write(arm.UC_ARM_REG_SP, SP)
        uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        uc.mem_write(SP - 0x40, bytes((0xD0 + i) & 0xFF for i in range(0x80)))
        uc.mem_write(GLOBAL_WORK, struct.pack("<I", 0xDEAD0001))
        uc.mem_write(CONFIG, case["config"])
        uc.mem_write(DATA, bytes([0xCC]) * DATA_SIZE)
        self.trace.clear()
        self.access_reads.clear()
        self.access_writes.clear()
        self.clobber = 0
        self.next_task_token = 0x01110001
        self.stopped = False
        self.fault = None
        self.step_count = 0
        try:
            uc.emu_start(self.entry, 0, count=30000)
        except unicorn.UcError as error:
            self.fault = str(error)
        preserved = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)]
        preserved.extend([uc.reg_read(arm.UC_ARM_REG_SP)])
        preserved.extend([uc.reg_read(getattr(arm, f"UC_ARM_REG_D{i}")) for i in range(8, 16)])
        return {"stopped": self.stopped, "fault": self.fault,
                "return": uc.reg_read(arm.UC_ARM_REG_R0),
                "pc": uc.reg_read(arm.UC_ARM_REG_PC),
                "fault_pc": uc.reg_read(arm.UC_ARM_REG_PC) if self.fault else None,
                "sp": uc.reg_read(arm.UC_ARM_REG_SP),
                "preserved": preserved, "trace": list(self.trace),
                "global_work": uc.mem_read(GLOBAL_WORK, 4).hex(),
                "work": bytes(uc.mem_read(WORK, 0x158)).hex(),
                "config": bytes(uc.mem_read(CONFIG, 8)).hex(),
                "reads": sorted(set(self.access_reads)),
                "writes": sorted(set(self.access_writes)),
                "steps": self.step_count}


def _trace_contract(trace: list[dict]) -> list[dict]:
    """Compare declared ABI inputs, not volatile scratch/register residue."""
    result = []
    stack_counts = {
        0x002C4B84: 1, 0x002C5978: 3, 0x002C4C00: 4,
        0x00118488: 1, 0x002C32F8: 7, 0x002BDB2C: 1,
        0x0029FAE8: 2, 0x00297704: 0,
    }
    register_counts = {
        0x002C4B84: 4, 0x002C5978: 4, 0x002C4C00: 4,
        0x00118488: 4, 0x002C3344: 1, 0x002C32F8: 4,
        0x002BDB2C: 4, 0x002BDAC0: 3, 0x0029FAE8: 4,
        0x0027EDF8: 2, 0x00297704: 3, 0x002B8B78: 1,
        0x0029F10C: 2, 0x002CAB70: 1, 0x0021F39C: 1,
        0x002E0AF4: 1, 0x002ADB40: 2,
    }
    for item in trace:
        address = int(item["address"], 16)
        row = {"address": item["address"], "name": item["name"],
               "r0_r3": item["r0_r3"][:register_counts[address]],
               "stack_words": item["stack_words"][:stack_counts.get(address, 0)]}
        if address == 0x00118488:
            row["s0_s3_bits"] = item["s0_s3_bits"]
            row["r0_string"] = item.get("r0_string")
        if "hle_effect" in item:
            row["hle_effect"] = item["hle_effect"]
        result.append(row)
    return result


def compare(original: dict, candidate: dict) -> str | None:
    for label, result in (("original", original), ("candidate", candidate)):
        if result["fault"]:
            return f"{label} fault: {result['fault']}"
        if not result["stopped"]:
            return f"{label} did not reach sentinel return"
    for field in ("return", "pc", "sp", "preserved", "global_work",
                  "work", "config", "writes"):
        if original[field] != candidate[field]:
            return f"{field} differs"
    if _trace_contract(original["trace"]) != _trace_contract(candidate["trace"]):
        return "declared helper argument trace differs"
    return None


def compile_candidate(output: Path) -> tuple[dict[str, bytes], dict]:
    obj = output / "h2_init_orchestration_candidate.o"
    built = compile_tu_armv6k(SOURCE, obj, ROOT)
    if built.returncode:
        raise RuntimeError(built.stderr or "ARMv6K candidate compilation failed")
    symbols = extract_elf_functions_detailed(obj)
    names = ("candidate_002f4ca0", "candidate_002f4ca0_wrong_count")
    result = {}
    relocations = {}
    for name in names:
        if name not in symbols:
            raise RuntimeError(f"missing compiled symbol {name}")
        body, relocs = symbols[name]
        if relocs:
            raise RuntimeError(f"unexpected unresolved relocations in {name}: {relocs}")
        result[name] = body
        relocations[name] = [r.__dict__ for r in relocs]
    return result, {"argv": built.args, "exit_code": built.returncode,
                    "object_sha256": sha256_file(obj), "object_path": str(obj),
                    "compiler_version": subprocess.run(
                        [str(find_clang()), "--version"], check=True,
                        capture_output=True, text=True).stdout.splitlines()[0],
                    "candidate_bytes": {name: len(body) for name, body in result.items()},
                    "relocations": relocations}


def run_experiment(code_path: Path, output: Path, seed: int, samples: int) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    if len(image) != game["code_bin_size"] or sha256_bytes(image) != game["code_sha256"]:
        raise ValueError("code.bin does not match configured pinned original")
    source_hash = sha256_file(SOURCE)
    candidates, build = compile_candidate(output)
    cases = build_cases(seed, samples)
    originals = []
    candidates_results = []
    failures = []
    for case in cases:
        left = InitRun(image, None, INIT, seed=seed).run(case)
        right = InitRun(image, candidates["candidate_002f4ca0"], INIT, seed=seed).run(case)
        error = compare(left, right)
        originals.append(left)
        candidates_results.append(right)
        if error:
            failures.append({"case": case["label"], "reason": error,
                             "original_return": f"0x{left['return']:08x}",
                             "original_fault_pc": f"0x{left['fault_pc']:08x}" if left["fault_pc"] else None,
                             "candidate_return": f"0x{right['return']:08x}",
                             "original_trace": left["trace"], "candidate_trace": right["trace"]})
            break

    control_case = cases[1]
    control_original = InitRun(image, None, INIT, seed=seed).run(control_case)
    control_bad = InitRun(image, candidates["candidate_002f4ca0_wrong_count"], INIT,
                          seed=seed).run(control_case)
    control_diff = compare(control_original, control_bad)
    negative = {"name": "sprite-group count 0x18 -> 0x17",
                "case": control_case["label"], "detected": control_diff is not None,
                "difference": control_diff,
                "expected_difference": "trace and sprite-group descriptor/work differ"}
    if sha256_file(SOURCE) != source_hash:
        raise RuntimeError("candidate source changed during experiment")
    passed = not failures and negative["detected"]
    report = {
        "schema": 1, "passed": passed,
        "scope": "0x002F4CA0 orchestration under shared HLE boundaries",
        "reference_sha256": game["code_sha256"], "image_sha256": sha256_bytes(image),
        "source_sha256": source_hash, "build": build,
        "seed": seed, "case_count": len(cases), "cases": [
            {"label": c["label"], "r0": f"0x{c['arg']:08x}",
             "config": c["config"].hex()} for c in cases],
        "cases_compared": len(candidates_results), "first_counterexample": failures[0] if failures else None,
        "negative_control": negative,
        "trace": candidates_results[0]["trace"] if candidates_results else [],
        "observed_effects": {"global_work": candidates_results[0]["global_work"] if candidates_results else None,
                             "work_hex": candidates_results[0]["work"] if candidates_results else None,
                             "config_hex": candidates_results[0]["config"] if candidates_results else None,
                             "return": f"0x{candidates_results[0]['return']:08x}" if candidates_results else None,
                             "caller_saved": "not compared; ABI volatile"},
        "stubs": {
            "0x002C4B84": "fixed WORK pointer and deterministic poison fill; deliberately bypasses original allocator and its zero-fill/pool semantics",
            "0x00118488": "records task-factory payload and returns deterministic handles; no process-pool mutation, scheduling, parent attachment or lifecycle",
            "0x002BDB2C": "writes only sprite+0x4c table pointer and a synthetic coordinate row; no actual resource setup",
            "0x0029FAE8": "records cursor setup args; no cursor state mutation",
            "0x00297704": "records asynchronous requests; no completion and no output-slot mutation",
            "0x002B8B78": "records sound ID; no audio state mutation",
            "0x0029F10C": "records reset mode/color; no shared UI state mutation"
        },
        "real_original_helpers": ["0x002C5978 wrapper", "0x002C4C00 wrapper",
            "0x002C3344", "0x002C32F8", "0x002BDAC0", "0x0027EDF8",
            "0x002CAB70", "0x0021F39C", "0x002E0AF4", "0x002ADB40"],
        "limits": [
            "This is an orchestration differential under declared shared HLE models, not end-to-end helper equivalence.",
            "Allocator poison HLE intentionally differs from the real successful zero-fill to expose initializer-owned writes; it does not validate allocator behavior.",
            "Task/process factory only captures forwarded registers/stack/VFP bits and tokens; no scheduling, order, lifecycle, or teardown is tested.",
            "Sprite/cursor/resource, async request completion, sound, and UI reset effects are stubbed as stated; visible UI and resource validity are open.",
            "Mapper and FillPair/CopyPair bodies execute from the pinned image; candidate mapper implementations are not under test.",
            "No caller scenario, editing, persistence, profile behavior, emulator, or whole-game equivalence is claimed."
        ],
        "elapsed_seconds": round(time.perf_counter() - started, 3)
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--samples", type=int, default=8)
    args = parser.parse_args()
    report = run_experiment(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "scope": report["scope"],
                      "report": str(args.output / "report.json"),
                      "first_counterexample": report["first_counterexample"],
                      "negative_control": report["negative_control"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

