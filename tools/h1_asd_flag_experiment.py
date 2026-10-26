#!/usr/bin/env python3
"""Private Thumb-vs-ARM differential for the bounded 0x002C00D4 candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys

import capstone
import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang

TEXT = 0x00100000
TEXT_MAP_SIZE = 0x00400000
ENTRY = 0x002C00D4
INJECT = 0x01000000
DATA = 0x02000000
DATA_SIZE = 0x1000
STACK = 0x08000000
STACK_SIZE = 0x2000
SP = STACK + 0x1000
RETURN = 0x01001000
MASK32 = 0xFFFFFFFF
REGS = tuple(getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13))
DREGS = tuple(getattr(arm, f"UC_ARM_REG_D{i}") for i in range(8, 16))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def original_boundary(image: bytes) -> dict:
    raw = image[ENTRY - TEXT:ENTRY - TEXT + 20]
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    insns = list(cs.disasm(raw, ENTRY))
    expected = [0x2C00D4, 0x2C00D6, 0x2C00D8, 0x2C00DA, 0x2C00DC,
                0x2C00DE, 0x2C00E0, 0x2C00E2, 0x2C00E4]
    if [i.address for i in insns] != expected:
        raise ValueError(f"Pinned Thumb instruction boundaries changed: {[hex(i.address) for i in insns]}")
    if insns[-1].mnemonic != "bx" or insns[-1].op_str != "lr":
        raise ValueError("Expected final executable instruction at 0x002C00E4 to be bx lr")
    padding = raw[0x12:0x14]
    if padding != b"\xff\xff":
        raise ValueError("Expected ledger-final 0xffff halfword at offset 0x12")
    return {
        "ledger_size": 20,
        "executed_addresses": [hex(i.address) for i in insns],
        "return_address": "0x002c00e4",
        "trailing_halfword_address": "0x002c00e6",
        "trailing_halfword": "0xffff",
        "trailing_halfword_executed": False,
        "thumb_bytes_sha256": hashlib.sha256(raw).hexdigest(),
        "disassembly": [f"0x{i.address:08x}: {i.mnemonic} {i.op_str}".rstrip() for i in insns],
    }


def directed_cases(samples: int, seed: int):
    rng = random.Random(seed)
    boundary_values = [
        ("zero", 0), ("one", 1), ("positive", 0x12345678),
        ("high-bit", 0x80000000), ("negative-u32", 0xFFFFFFFF),
        ("signed-min", 0x80000000), ("max-positive", 0x7FFFFFFF),
    ]
    # Word-aligned pointers at both an interior offset and the upper boundary
    # of the mapped ordinary-RAM region; surroundings remain seeded and visible.
    offsets = [0x100, 0x104, DATA_SIZE - 4]
    for index, (label, value) in enumerate(boundary_values):
        memory = bytearray(rng.randbytes(DATA_SIZE))
        offset = offsets[index % len(offsets)]
        memory[offset:offset + 4] = value.to_bytes(4, "little")
        yield {"label": label, "offset": offset, "value": value, "data": bytes(memory),
               "surroundings": (memory[max(0, offset-8):offset] + memory[offset+4:offset+12]).hex()}
    for index in range(samples):
        memory = bytearray(rng.randbytes(DATA_SIZE))
        offset = rng.randrange(DATA_SIZE // 4) * 4
        value = rng.getrandbits(32)
        memory[offset:offset + 4] = value.to_bytes(4, "little")
        yield {"label": f"seeded-{index}", "offset": offset, "value": value, "data": bytes(memory),
               "surroundings": (memory[max(0, offset-8):offset] + memory[offset+4:offset+12]).hex()}


class Machine:
    def __init__(self, image: bytes, code: bytes | None):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, TEXT_MAP_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, 0x2000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        if code is not None:
            self.uc.mem_write(INJECT, code)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.reads: set[int] = set()
        self.writes: set[int] = set()
        self.stopped = False
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._instruction)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE, self._memory)

    def _instruction(self, uc, address, _size, _user):
        if address == RETURN:
            self.stopped = True
            uc.emu_stop()

    def _memory(self, _uc, access, address, size, _value, _user):
        target = self.reads if access == unicorn.UC_MEM_READ else self.writes
        if DATA <= address < DATA + DATA_SIZE:
            target.update(range(address, min(address + size, DATA + DATA_SIZE)))

    def run(self, test_case: dict, *, thumb: bool) -> dict:
        uc = self.uc
        # Select user ARM state before writing banked SP/LR; Unicorn's CPSR
        # mode change otherwise switches away from the values just installed.
        uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        for reg_id in REGS:
            uc.reg_write(reg_id, 0xA5000000 | (reg_id & 0xFFFF))
        for reg_id in DREGS:
            uc.reg_write(reg_id, 0xD800000000000000 | (reg_id & 0xFFFFFFFF))
        uc.reg_write(arm.UC_ARM_REG_R0, DATA + test_case["offset"])
        uc.reg_write(arm.UC_ARM_REG_SP, SP)
        uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        uc.mem_write(DATA, test_case["data"])
        uc.mem_write(STACK, bytes([0xCC]) * STACK_SIZE)
        self.reads.clear()
        self.writes.clear()
        self.stopped = False
        fault = None
        try:
            # Unicorn uses the low begin-address bit to enter Thumb state; an
            # even address with only CPSR.T set is normalized back to ARM.
            uc.emu_start((ENTRY | 1) if thumb else INJECT, 0, count=64)
        except unicorn.UcError as error:
            fault = str(error)
        preserved = tuple(uc.reg_read(r) for r in REGS[4:12]) + (uc.reg_read(arm.UC_ARM_REG_SP),)
        preserved += tuple(uc.reg_read(r) for r in DREGS)
        return {
            "stopped": self.stopped, "fault": fault,
            "result": uc.reg_read(arm.UC_ARM_REG_R0), "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "preserved": [f"0x{x:x}" for x in preserved],
            "data": bytes(uc.mem_read(DATA, DATA_SIZE)),
            "stack": bytes(uc.mem_read(STACK, STACK_SIZE)),
            "reads": sorted(self.reads), "writes": sorted(self.writes),
        }


def compare(a: dict, b: dict) -> str | None:
    for label, result in (("original", a), ("candidate", b)):
        if result["fault"]:
            return f"{label} fault: {result['fault']}"
        if not result["stopped"]:
            return f"{label} did not return to sentinel"
    for key, reason in (("result", "r0 differs"), ("preserved", "callee-saved state/SP differs"),
                        ("data", "data memory differs"), ("stack", "stack differs"),
                        ("reads", "read footprint differs"), ("writes", "write footprint differs")):
        if a[key] != b[key]:
            return reason
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True, help="new private output directory")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261025)
    args = parser.parse_args()
    if args.samples < 0:
        parser.error("--samples must be nonnegative")
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)

    image_path = ROOT / "extracted/exefs/code.bin"
    image = image_path.read_bytes()
    boundary = original_boundary(image)
    candidate_path = ROOT / "experiments/semantic_equivalence/h1_asd_flag_candidate.cpp"
    candidate_obj = output / "candidate.o"
    compiled = compile_tu_armv6k(candidate_path, candidate_obj, ROOT)
    if compiled.returncode != 0:
        raise SystemExit(f"candidate compile failed:\n{compiled.stdout}\n{compiled.stderr}")
    symbols = extract_elf_functions_detailed(candidate_obj)
    name = "candidate_002c00d4"
    if name not in symbols:
        raise SystemExit(f"candidate symbol missing; available={sorted(symbols)}")
    code, relocations = symbols[name]
    if relocations:
        raise SystemExit(f"candidate must be relocation-free; found {relocations}")

    # A deliberately wrong, omitted-store implementation must be rejected by
    # the same observable comparator. It is compiled sequentially in this slot.
    control_src = output / "wrong_missing_store.cpp"
    control_src.write_text(
        '#include "types.h"\nextern "C" __attribute__((noinline)) u32 wrong_missing_store(u32* p) { return *p == 0 ? 1u : 0u; }\n',
        encoding="utf-8")
    control_obj = output / "wrong_missing_store.o"
    control_build = compile_tu_armv6k(control_src, control_obj, ROOT)
    if control_build.returncode != 0:
        raise SystemExit(f"negative-control compile failed:\n{control_build.stdout}\n{control_build.stderr}")
    control_functions = extract_elf_functions_detailed(control_obj)
    control, control_relocs = control_functions["wrong_missing_store"]
    if control_relocs:
        raise SystemExit(f"control unexpectedly has relocations: {control_relocs}")

    original = Machine(image, None)
    candidate = Machine(image, code)
    wrong = Machine(image, control)
    results = []
    passed = True
    cases = list(directed_cases(args.samples, args.seed))
    for case in cases:
        a, b = original.run(case, thumb=True), candidate.run(case, thumb=False)
        reason = compare(a, b)
        record = {"label": case["label"], "input_word": f"0x{case['value']:08x}",
                  "pointer_offset": case["offset"], "surrounding_bytes": case["surroundings"],
                  "original_r0": f"0x{a['result']:08x}", "candidate_r0": f"0x{b['result']:08x}",
                  "original_reads": [hex(x) for x in a["reads"]],
                  "original_writes": [hex(x) for x in a["writes"]],
                  "candidate_reads": [hex(x) for x in b["reads"]],
                  "candidate_writes": [hex(x) for x in b["writes"]],
                  "passed": reason is None, "difference": reason}
        results.append(record)
        if reason:
            passed = False

    control_case = next(c for c in cases if c["label"] == "zero")
    expected = original.run(control_case, thumb=True)
    actual = wrong.run(control_case, thumb=False)
    control_difference = compare(expected, actual)
    control_detected = control_difference == "data memory differs" or control_difference == "write footprint differs"
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True).stdout.splitlines()[0]
    report = {
        "schema_version": 1,
        "task_id": "h1-asd-flag-candidate",
        "passed": passed and control_detected,
        "reference_sha256": sha(image_path),
        "candidate_source_sha256": sha(candidate_path),
        "candidate_object_sha256": sha(candidate_obj),
        "negative_control_source_sha256": sha(control_src),
        "negative_control_object_sha256": sha(control_obj),
        "entry": hex(ENTRY), "state": "original Thumb / candidate ARMv6K C++",
        "boundary": boundary,
        "compiler": compiler,
        "unicorn_version": unicorn.__version__,
        "seed": args.seed,
        "random_cases": args.samples,
        "case_count": len(results),
        "candidate_bytes": len(code),
        "candidate_relocations": list(relocations),
        "cases": results,
        "negative_control": {"name": "missing-store", "case": "zero",
                             "detected": control_detected, "difference": control_difference,
                             "expected_difference": "data memory differs or write footprint differs"},
        "caller_evidence": [
            {"function": "Asd sound update", "callsite": "0x001099B4", "instruction": "ARM BLX 0x002C00D4",
             "observed_use": "cmp r0,#0 controls one-shot mixer initialization"},
            {"function": "effect matrix setup", "callsite": "0x001F6948", "instruction": "ARM BLX 0x002C00D4",
             "observed_use": "cmp r0,#0 gates one-time matrix initialization"},
            {"function": "UI panel command", "callsite": "0x0036C380", "instruction": "ARM BLX 0x002C00D4",
             "observed_use": "cmp r0,#0 gates command initialization"}
        ],
        "limitations": [
            "Differential covers selected ordinary RAM cases; it is not a formal proof or captured gameplay trace.",
            "Concurrent observers, interrupt races, MMIO, timing, exceptions and OS behavior are untested; C++ candidate is not atomic.",
            "Pointers are word-aligned; unaligned access behavior and invalid pointers are outside the supported contract.",
            "Compared r0, callee-saved r4-r11, SP, d8-d15, RAM, stack and read/write address footprints. Caller-saved registers and NZCV were not required by observed direct callers, which compare r0 after BLX.",
            "No H1 runtime/boot or production integration was performed."
        ]
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "case_count": len(results),
                      "negative_control_detected": control_detected,
                      "report": str(output / "report.json")}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
