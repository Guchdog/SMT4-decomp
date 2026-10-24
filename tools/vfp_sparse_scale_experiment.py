#!/usr/bin/env python3
"""Bounded ARM11 differential test for four sparse VFP scale leaves."""
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

DATA_SIZE = 0x6000
SP = STACK + 0x1000
FUNCTIONS = {
    0x002E5B24: ("candidate_002e5b24", 0xD8, 0xE0),
    0x002F29A4: ("candidate_002f29a4", 0xE4, 0xF0),
    0x0030C8BC: ("candidate_0030c8bc", 0xD8, 0xE0),
    0x003134F8: ("candidate_003134f8", 0xD8, 0xE0),
}
COMMON_OFFSETS = (0x64, 0x68, 0x74, 0x7C, 0x84, 0xC8, 0xCC, 0xD4)
SPECIAL = (
    0x00000000, 0x80000000, 0x00000001, 0x80000001,
    0x007FFFFF, 0x807FFFFF, 0x00800000, 0x80800000,
    0x3F800000, 0xBF800000, 0x7F7FFFFF, 0xFF7FFFFF,
    0x7F800000, 0xFF800000, 0x7FC12345, 0xFFC54321,
    0x7F812345, 0xFF812345,
)


def _decode(image: bytes, address: int, size: int):
    offset = address - TEXT
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    items = list(decoder.disasm(image[offset:offset + size], address))
    if sum(item.size for item in items) != size:
        raise ValueError(f"incomplete instruction decode at {address:#010x}")
    return tuple((x.mnemonic.lower(), x.op_str.lower()) for x in items)


def expected_instructions(penultimate: int, last: int):
    result = [("ldrd", "r0, r1, [r0, #0x20]")]
    for offset in (*COMMON_OFFSETS, penultimate, last):
        value_reg = "s1"
        output_reg = "s0" if offset == last else "s1"
        result.extend((
            ("vldr", f"{value_reg}, [r1, #0x{offset:x}]"),
            ("vmul.f32", f"{output_reg}, {value_reg}, s0"),
            ("vstr", f"{output_reg}, [r0, #0x{offset:x}]"),
        ))
    result.append(("bx", "lr"))
    return tuple(result)


def verify_reference(image: bytes, game_info: dict, ledger_rows: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 differs from configured pin")
    ledger = {int(row["address"], 16): row for row in ledger_rows}
    functions = {}
    for address, (symbol, penultimate, last) in FUNCTIONS.items():
        row = ledger.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 128:
            raise ValueError(f"missing matching 128-byte ledger row at {address:#010x}")
        instructions = _decode(image, address, 128)
        expected = expected_instructions(penultimate, last)
        if instructions != expected:
            raise ValueError(f"reference body changed at {address:#010x}: {instructions}")
        start = address - TEXT
        body = image[start:start + 128]
        functions[hex(address)] = {
            "name": row["name"], "status": row["status"], "size": 128,
            "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": body.hex(),
            "instructions": [f"{m} {ops}" for m, ops in expected],
            "observed": (
                "Loads two pointers from object+0x20, then in order multiplies "
                "ten listed source binary32 members by the incoming s0 and stores "
                "each at the same member offset in the destination object."
            ),
            "unknown": "Caller intent and behavior outside this pinned ordinary-RAM leaf are unknown.",
        }
    return {"code_sha256": digest, "functions": functions}


def _branch(source: int, target: int) -> bytes:
    displacement = target - source - 8
    if displacement % 4 or not -(1 << 25) <= displacement < (1 << 25):
        raise ValueError("candidate trampoline branch is not representable")
    return struct.pack("<I", 0xEA000000 | ((displacement >> 2) & 0xFFFFFF))


class Runner:
    def __init__(self, image: bytes, address: int, candidate: bytes | None = None):
        require_unicorn()
        self.address = address
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, 0x400000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, 0x2000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        if candidate is not None:
            self.uc.mem_write(INJECT, candidate)
            self.uc.mem_write(address, _branch(address, INJECT))
        self.reads: set[int] = set()
        self.writes: set[int] = set()
        self.stopped = False
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE,
                         self._memory)
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

    def run(self, case: dict):
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
            uc.emu_start(self.address, 0, count=256)
        except unicorn.UcError as error:
            fault = str(error)
        return {
            "stopped": self.stopped, "fault": fault,
            "gp": tuple(uc.reg_read(reg) for reg in self.gp),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP), "lr": uc.reg_read(arm.UC_ARM_REG_LR),
            "fpscr": uc.reg_read(arm.UC_ARM_REG_FPSCR),
            "fpexc": uc.reg_read(arm.UC_ARM_REG_FPEXC),
            "s": tuple(uc.reg_read(reg) for reg in self.sregs),
            "data": bytes(uc.mem_read(DATA, DATA_SIZE)),
            "stack": bytes(uc.mem_read(STACK, STACK_SIZE)),
            "reads": frozenset(self.reads), "writes": frozenset(self.writes),
        }


def _compare(reference: dict, candidate: dict) -> str | None:
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


def _case(seed: int, index: int, label: str, source_bits: tuple[int, ...],
          scale_bits: int, fpscr: int, alias_delta: int | None = None,
          late_fault: bool = False) -> dict:
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    object_off, source_off, destination_off = 0x200, 0x800, 0x1200
    if alias_delta is not None:
        destination_off = source_off + alias_delta
    if late_fault:
        source_off = DATA_SIZE - 0x80
    struct.pack_into("<II", data, object_off + 0x20,
                     DATA + destination_off, DATA + source_off)
    for offset, bits in zip(COMMON_OFFSETS + (0xD8, 0xE0, 0xE4, 0xF0),
                            (source_bits[i % len(source_bits)] for i in range(12))):
        if source_off + offset + 4 <= DATA_SIZE:
            struct.pack_into("<I", data, source_off + offset, bits)
    gp = [rng.getrandbits(32) for _ in range(13)]
    gp[0] = DATA + object_off
    s = [rng.getrandbits(32) for _ in range(32)]
    s[0] = scale_bits
    return {"label": label, "gp": tuple(gp), "s": tuple(s), "fpscr": fpscr,
            "data": bytes(data), "stack": rng.randbytes(STACK_SIZE)}


def make_cases(seed: int) -> list[dict]:
    cases = []
    index = 0
    for special_index, _ in enumerate(SPECIAL):
        source = tuple(SPECIAL[(special_index + lane * 5) % len(SPECIAL)]
                       for lane in range(12))
        scale = SPECIAL[(special_index * 7 + 3) % len(SPECIAL)]
        for rounding in range(4):
            for flush in (0, 1):
                for default_nan in (0, 1):
                    fpscr = (rounding << 22) | (flush << 24) | (default_nan << 25) | (index & 0x1F)
                    cases.append(_case(seed, index, f"special-{special_index}-rm{rounding}-fz{flush}-dn{default_nan}",
                                       source, scale, fpscr))
                    index += 1
    rng = random.Random(seed)
    for i in range(96):
        source = tuple(rng.getrandbits(32) for _ in range(12))
        scale = rng.getrandbits(32)
        fpscr = ((i % 4) << 22) | (((i // 4) & 1) << 24) | (((i // 8) & 1) << 25) | (i & 0x1F)
        cases.append(_case(seed, index, f"random-{i}", source, scale, fpscr))
        index += 1
    for delta in (0, 4, -4):
        source = tuple(0x3F000001 + i * 0x101 for i in range(12))
        cases.append(_case(seed, index, f"alias-destination-{delta:+d}", source,
                           0x3F812345, 0x1F, alias_delta=delta))
        index += 1
    source = tuple(0x3F000001 + i * 0x101 for i in range(12))
    cases.append(_case(seed, index, "late-source-page-fault", source,
                       0x3F800001, 0x1F, late_fault=True))
    return cases


def run(code_path: Path, output: Path, seed: int) -> dict:
    require_unicorn()
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    source_path = ROOT / "experiments/semantic_equivalence/vfp_sparse_scale_candidates.cpp"
    object_path = output / "vfp_sparse_scale_candidates.o"
    controls = {"negative_wrong_offset", "negative_omit_final"}
    build = compile_tu_armv6k(source_path, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    symbols = {}
    for name, (code, relocations) in extract_elf_functions_detailed(object_path).items():
        if relocations:
            raise ValueError(f"unexpected relocation in {name}: {relocations}")
        symbols[name] = code
    required = {x[0] for x in FUNCTIONS.values()} | controls
    if required - symbols.keys():
        raise ValueError(f"missing compiled symbols: {sorted(required - symbols.keys())}")
    flags = get_armv6k_flags(ROOT)
    if any(flag == "-Ofast" or flag.startswith("-ffast-math") for flag in flags):
        raise ValueError("fast-math is disallowed for IEEE-sensitive VFP experiment")
    cases = make_cases(seed)
    functions = []
    for address, (symbol, penultimate, last) in FUNCTIONS.items():
        ref_runner = Runner(pinned.image, address)
        candidate_runner = Runner(pinned.image, address, symbols[symbol])
        failure = None
        first_access = None
        late_fault_evidence = None
        caller_saved_differences = []
        for case in cases:
            ref, candidate = ref_runner.run(case), candidate_runner.run(case)
            if first_access is None:
                first_access = {"case": case["label"],
                                "read_bytes_equal": ref["reads"] == candidate["reads"],
                                "write_bytes_equal": ref["writes"] == candidate["writes"]}
            if case["label"] == "late-source-page-fault":
                late_fault_evidence = {
                    "reference_faulted": bool(ref["fault"]),
                    "candidate_faulted": bool(candidate["fault"]),
                    "reference_committed_write_bytes": len(ref["writes"]),
                    "candidate_committed_write_bytes": len(candidate["writes"]),
                    "ordinary_memory_and_access_sets_equal": (
                        ref["data"] == candidate["data"]
                        and ref["reads"] == candidate["reads"]
                        and ref["writes"] == candidate["writes"]),
                }
            changed = [i for i, (a, b) in enumerate(zip(ref["s"][:16], candidate["s"][:16])) if a != b]
            if changed and len(caller_saved_differences) < 6:
                caller_saved_differences.append({"case": case["label"], "s_registers": changed})
            reason = _compare(ref, candidate)
            if reason:
                failure = {"case": case["label"], "field": reason,
                           "reference_fault": ref["fault"], "candidate_fault": candidate["fault"]}
                break
        functions.append({"address": hex(address), "candidate": symbol,
                          "original_bytes": 128, "candidate_bytes": len(symbols[symbol]),
                          "cases": len(cases) if failure is None else cases.index(case) + 1,
                          "passed": failure is None, "failure": failure,
                          "caller_saved_s_differences": caller_saved_differences,
                          "first_access": first_access,
                          "late_fault_evidence": late_fault_evidence})
    control_case = next(x for x in cases if x["label"] == "random-0")
    negative_controls = []
    for symbol, observed in (("negative_wrong_offset", "wrong source member"),
                             ("negative_omit_final", "omitted store")):
        address = next(iter(FUNCTIONS))
        ref = Runner(pinned.image, address).run(control_case)
        wrong = Runner(pinned.image, address, symbols[symbol]).run(control_case)
        detected = ref["data"] != wrong["data"]
        negative_controls.append({"control": symbol, "detects": observed,
                                  "detected": detected})
    report = {
        "schema": 1, "experiment": "vfp_sparse_scale_uncovered_family",
        "passed": all(x["passed"] for x in functions) and all(x["detected"] for x in negative_controls),
        "scope": "four pinned ARM11 VFP leaves; isolated ordinary-memory differential, not game boot",
        "reference_sha256": pinned.game_info["code_sha256"],
        "reference_functions": reference["functions"],
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler_flags": flags, "fast_math": False, "seed": seed,
        "function_comparisons": sum(x["cases"] for x in functions),
        "cases_per_function": len(cases),
        "case_mix": {"special_ieee_fpscr": len(SPECIAL) * 16, "random": 96,
                     "overlap_alias": 3, "late_source_fault": 1},
        "comparison_policy": ["return/fault outcome", "callee-saved r4-r11 and SP",
                              "FPSCR/FPEXC", "callee-saved s16-s31",
                              "all ordinary RAM and stack bytes", "ordinary-RAM byte read/write sets"],
        "caller_saved_policy": "r0-r3/r12 and s0-s15 differences are diagnostic only, not required equal by ABI.",
        "functions": functions, "negative_controls": negative_controls,
        "caller_windows": [],
        "limitations": ["Finite differential cases are evidence, not proof over all inputs.",
                        "Unicorn ARM11 MPCore VFPv2 and ordinary RAM only; hardware traps, MMIO, timing and concurrency are outside scope.",
                        "No callers, emulator boot or full game runtime were tested; no ledger or production code changes."],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed)
    print(json.dumps({"passed": report["passed"], "comparisons": report["function_comparisons"],
                      "functions": report["functions"], "controls": report["negative_controls"],
                      "report": str(args.output / "report.json")}))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
