#!/usr/bin/env python3
"""Bounded ARM11 differential for the H1 alpha helper at 0x0029BDB4."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, get_armv6k_flags
from tools.semantic_experiment import (
    TEXT, DATA, STACK, STACK_SIZE, INJECT, RETURN, arm, unicorn,
    require_unicorn,
)
from tools.semantic_experiment_support import load_pinned_reference

ADDRESS = 0x0029BDB4
DATA_SIZE = 0x6000
SP = STACK + 0x1000
SPECIAL = (0, 0x80000000, 1, 0x80000001, 0x3F800000, 0xBF800000,
           0x7F7FFFFF, 0xFF7FFFFF, 0x7F800000, 0xFF800000,
           0x7FC12345, 0xFFC54321, 0x7F812345, 0xFF812345)


def verify_reference(image: bytes, game_info: dict, ledger_rows: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 differs from configured pin")
    rows = {int(row["address"], 16): row for row in ledger_rows}
    row = rows.get(ADDRESS)
    if row is None or int(row["size"]) != 40 or row["status"].strip() != "matching":
        raise ValueError("missing pinned matching 40-byte ledger row")
    start = ADDRESS - TEXT
    body = image[start:start + 40]
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = list(decoder.disasm(body, ADDRESS))
    if sum(insn.size for insn in decoded) != 40:
        raise ValueError("incomplete original function decode")
    instructions = [(x.mnemonic.lower(), x.op_str.lower()) for x in decoded]
    expected = [
        ("ldr", "r1, [r0, #0x34]"), ("vstr", "s0, [r0, #0x78]"),
        ("cmp", "r1, #0"), ("ble", "#0x29bdd8"),
        ("vldr", "s1, [r0, #0x74]"), ("ldr", "r0, [r0, #0x4c]"),
        ("vmul.f32", "s0, s1, s0"), ("cmp", "r0, #0"),
        ("vstrne", "s0, [r0, #0x40]"), ("bx", "lr"),
    ]
    if instructions != expected:
        raise ValueError(f"pinned helper body changed: {instructions}")
    return {"name": row["name"], "status": row["status"], "size": 40,
            "sha256": hashlib.sha256(body).hexdigest(),
            "instructions": [f"{mnemonic} {operands}" for mnemonic, operands in instructions]}


def _branch(source: int, target: int) -> bytes:
    displacement = target - source - 8
    if displacement % 4 or not -(1 << 25) <= displacement < (1 << 25):
        raise ValueError("candidate branch is not representable")
    return struct.pack("<I", 0xEA000000 | ((displacement >> 2) & 0xFFFFFF))


class Runner:
    def __init__(self, image: bytes, candidate: bytes | None = None):
        require_unicorn()
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, 0x400000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, 0x2000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        if candidate is not None:
            self.uc.mem_write(INJECT, candidate)
            self.uc.mem_write(ADDRESS, _branch(ADDRESS, INJECT))
        self.reads: set[int] = set()
        self.writes: set[int] = set()
        self.stopped = False
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE, self._memory)
        self.gp = tuple(getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13))
        self.sregs = tuple(getattr(arm, f"UC_ARM_REG_S{i}") for i in range(32))

    def _code(self, uc, address, _size, _):
        if address == RETURN:
            self.stopped = True
            uc.emu_stop()

    def _memory(self, _uc, access, address, size, _value, _):
        target = self.reads if access == unicorn.UC_MEM_READ else self.writes
        for byte in range(address, address + size):
            if DATA <= byte < DATA + DATA_SIZE or STACK <= byte < STACK + STACK_SIZE:
                target.add(byte)

    def run(self, case: dict) -> dict:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        for reg, value in zip(self.gp, case["gp"]):
            uc.reg_write(reg, value)
        uc.reg_write(arm.UC_ARM_REG_SP, SP)
        uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.reg_write(arm.UC_ARM_REG_FPSCR, case["fpscr"])
        for reg, value in zip(self.sregs, case["s"]):
            uc.reg_write(reg, value)
        uc.mem_write(DATA, case["data"])
        uc.mem_write(STACK, case["stack"])
        self.reads.clear(); self.writes.clear(); self.stopped = False
        fault = None
        try:
            uc.emu_start(ADDRESS, 0, count=128)
        except unicorn.UcError as error:
            fault = str(error)
        return {
            "stopped": self.stopped, "fault": fault,
            "gp": tuple(uc.reg_read(reg) for reg in self.gp),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "fpscr": uc.reg_read(arm.UC_ARM_REG_FPSCR),
            "fpexc": uc.reg_read(arm.UC_ARM_REG_FPEXC),
            "s": tuple(uc.reg_read(reg) for reg in self.sregs),
            "data": bytes(uc.mem_read(DATA, DATA_SIZE)),
            "stack": bytes(uc.mem_read(STACK, STACK_SIZE)),
            "reads": frozenset(self.reads), "writes": frozenset(self.writes),
        }


def compare(reference: dict, candidate: dict) -> str | None:
    if reference["stopped"] != candidate["stopped"]:
        return "normal-return state"
    if bool(reference["fault"]) != bool(candidate["fault"]):
        return "fault state"
    for index in range(4, 12):
        if reference["gp"][index] != candidate["gp"][index]:
            return f"callee-saved r{index}"
    for key in ("sp", "fpscr", "fpexc", "data", "stack", "reads", "writes"):
        if reference[key] != candidate[key]:
            return key
    if reference["s"][16:] != candidate["s"][16:]:
        return "callee-saved s16-s31"
    return None


def _case(seed: int, index: int, label: str, gate: int, scale_bits: int,
          alpha_bits: int, target_delta: int | None, fpscr: int) -> dict:
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    child_off = 0x200
    target = 0 if target_delta is None else DATA + child_off + target_delta
    struct.pack_into("<i", data, child_off + 0x34, gate)
    struct.pack_into("<I", data, child_off + 0x4C, target)
    struct.pack_into("<I", data, child_off + 0x74, scale_bits)
    struct.pack_into("<I", data, child_off + 0x78, 0x41234567)
    gp = [rng.getrandbits(32) for _ in range(13)]
    gp[0] = DATA + child_off
    s = [rng.getrandbits(32) for _ in range(32)]
    s[0] = alpha_bits
    return {"label": label, "gp": tuple(gp), "s": tuple(s), "fpscr": fpscr,
            "data": bytes(data), "stack": rng.randbytes(STACK_SIZE)}


def make_cases(seed: int) -> list[dict]:
    cases = []
    index = 0
    for gate in (-0x80000000, -1, 0, 1, 0x7FFFFFFF):
        for target_delta in (0x1000, None, 0x38, 0x0C):
            for special_i, bits in enumerate(SPECIAL[:8]):
                scale = SPECIAL[(special_i * 3 + 1) % len(SPECIAL)]
                fpscr = ((special_i % 4) << 22) | (((special_i // 2) & 1) << 24) | (index & 0x1F)
                cases.append(_case(seed, index, f"directed-g{gate}-t{target_delta}-a{bits:08x}",
                                   gate, scale, bits, target_delta, fpscr))
                index += 1
    rng = random.Random(seed)
    for i in range(128):
        gate = (0, 1, -1, 0x7FFFFFFF, -0x80000000)[i % 5]
        target = (0x1000, None, 0x38, 0x0C)[i % 4]
        fpscr = ((i % 4) << 22) | (((i // 4) & 1) << 24) | (((i // 8) & 1) << 25) | (i & 0x1F)
        cases.append(_case(seed, index, f"random-{i}", gate, rng.getrandbits(32),
                           rng.getrandbits(32), target, fpscr))
        index += 1
    return cases


def run(code_path: Path, output: Path, seed: int) -> dict:
    require_unicorn()
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference_info = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    source_path = ROOT / "experiments/semantic_equivalence/h1_alpha_candidates.cpp"
    object_path = output / "h1_alpha_candidates.o"
    build = compile_tu_armv6k(source_path, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    symbols = {}
    for name, (code, relocations) in extract_elf_functions_detailed(object_path).items():
        if relocations:
            raise ValueError(f"unexpected relocation in {name}: {relocations}")
        symbols[name] = code
    for required in ("candidate_0029bdb4", "negative_wrong_offset"):
        if required not in symbols:
            raise ValueError(f"missing compiled symbol {required}")
    flags = get_armv6k_flags(ROOT)
    if any(flag == "-Ofast" or flag.startswith("-ffast-math") for flag in flags):
        raise ValueError("fast-math is disallowed for IEEE-sensitive VFP behavior")
    cases = make_cases(seed)
    ref_runner = Runner(pinned.image)
    candidate_runner = Runner(pinned.image, symbols["candidate_0029bdb4"])
    failure = None
    caller_saved_s_differences = []
    for case in cases:
        ref, candidate = ref_runner.run(case), candidate_runner.run(case)
        changed = [i for i, (a, b) in enumerate(zip(ref["s"][:16], candidate["s"][:16])) if a != b]
        if changed and len(caller_saved_s_differences) < 8:
            caller_saved_s_differences.append({"case": case["label"], "registers": changed})
        reason = compare(ref, candidate)
        if reason:
            failure = {"case": case["label"], "field": reason,
                       "reference_fault": ref["fault"], "candidate_fault": candidate["fault"]}
            break
    control_case = _case(seed, 0xBAD, "negative-control-positive", 1,
                         0x3F400000, 0x3F800000, 0x1000, 0)
    ref_control = Runner(pinned.image).run(control_case)
    wrong_control = Runner(pinned.image, symbols["negative_wrong_offset"]).run(control_case)
    negative = {"control": "negative_wrong_offset", "expected_detection": "child alpha store at +0x78 moved to +0x7C",
                "detected": ref_control["data"] != wrong_control["data"],
                "reference_write_bytes": len(ref_control["writes"]),
                "control_write_bytes": len(wrong_control["writes"])}
    report = {
        "schema": 1, "experiment": "h1_alpha_helper_0029bdb4",
        "passed": failure is None and negative["detected"],
        "scope": "isolated pinned ARM11 helper; ordinary memory only; not caller/runtime equivalence",
        "reference_sha256": pinned.game_info["code_sha256"], "reference_function": reference_info,
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler_flags": flags, "fast_math": False, "seed": seed,
        "cases": len(cases) if failure is None else next(i + 1 for i, c in enumerate(cases) if c["label"] == failure["case"]),
        "directed_cases": 160, "random_cases": 128,
        "coverage": {"signed_gate_values": [-2147483648, -1, 0, 1, 2147483647],
                     "gate_positive_and_nonpositive": True, "nullable_target": True,
                     "alias_target_plus_0x38_overlaps_child_alpha": True,
                     "alias_target_plus_0x0c_overlaps_child_pointer": True,
                     "special_float_bits": [f"0x{x:08x}" for x in SPECIAL],
                     "fpscr_rounding_flush_default_nan_variation": True},
        "comparison_policy": ["normal return/fault outcome", "callee-saved r4-r11 and SP",
                              "FPSCR/FPEXC", "callee-saved s16-s31", "all mapped ordinary RAM and stack",
                              "ordinary-RAM byte read/write sets"],
        "caller_saved_policy": "r0-r3/r12 and s0-s15 differences are diagnostic only in the isolated void helper.",
        "failure": failure, "caller_saved_s_differences": caller_saved_s_differences,
        "negative_control": negative,
        "limitations": ["Finite differential cases are evidence, not proof over all inputs.",
                        "Valid child object and ordinary RAM only; invalid pointers, MMIO, hardware traps, concurrency and timing are outside scope.",
                        "No caller window, game integration, emulator boot or whole callback equivalence was tested."],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed)
    print(json.dumps({"passed": report["passed"], "cases": report["cases"],
                      "failure": report["failure"], "negative_control": report["negative_control"],
                      "report": str(args.output / "report.json")}))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
