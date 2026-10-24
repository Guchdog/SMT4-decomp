#!/usr/bin/env python3
"""Isolated ABI and differential experiment for two VFP matrix transposes."""
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
from tools.semantic_experiment import TEXT, DATA, STACK, STACK_SIZE, INJECT, RETURN
from tools.semantic_experiment import arm, require_unicorn, unicorn
from tools.semantic_experiment_support import load_pinned_reference

DATA_SIZE = 0x4000
SP = STACK + 0x1000
FUNCTIONS = {
    0x0023AFF0: ("candidate_0023aff0", 76),
    0x002A1B4C: ("candidate_002a1b4c", 76),
}
EXPECTED = (
    ("vldmia", "r1!, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15}"),
    ("str", "r2, [r0, #4]"),
    ("vstr", "s0, [r0, #0x10]"), ("vstr", "s1, [r0, #0xc]"),
    ("vstr", "s2, [r0, #8]"), ("vstr", "s3, [r0]"),
    ("vstr", "s4, [r0, #0x20]"), ("vstr", "s5, [r0, #0x1c]"),
    ("vstr", "s6, [r0, #0x18]"), ("vstr", "s7, [r0, #0x14]"),
    ("vstr", "s8, [r0, #0x30]"), ("vstr", "s9, [r0, #0x2c]"),
    ("vstr", "s10, [r0, #0x28]"), ("vstr", "s11, [r0, #0x24]"),
    ("vstr", "s12, [r0, #0x40]"), ("vstr", "s13, [r0, #0x3c]"),
    ("vstr", "s14, [r0, #0x38]"), ("vstr", "s15, [r0, #0x34]"),
    ("bx", "lr"),
)


def decode(image: bytes, address: int, size: int):
    code = image[address - TEXT:address - TEXT + size]
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = list(decoder.disasm(code, address))
    if sum(item.size for item in decoded) != size:
        raise ValueError(f"incomplete ARM disassembly at {address:#x}")
    return code, decoded


def verify_reference(image: bytes, expected_sha: str, ledger_rows: list[dict]) -> dict:
    ledger = {int(row["address"], 16): row for row in ledger_rows}
    functions = {}
    for address, (symbol, size) in FUNCTIONS.items():
        row = ledger.get(address)
        if row is None or int(row["size"]) != size or row["status"] != "matching":
            raise ValueError(f"matching ledger entry missing/changed at {address:#x}")
        code, decoded = decode(image, address, size)
        normalized = tuple((x.mnemonic.lower(), x.op_str.lower()) for x in decoded)
        if normalized != EXPECTED:
            raise ValueError(f"VFP transpose instruction sequence changed at {address:#x}: {normalized}")
        functions[hex(address)] = {
            "symbol": symbol, "size": size,
            "sha256": hashlib.sha256(code).hexdigest(), "bytes": code.hex(),
            "instructions": [f"{m} {o}" for m, o in EXPECTED],
            "observed_behavior": (
                "r0/r1/r2 are destination/source/raw slot-1 word; loads 16 source words "
                "through r1! before writes, transposes the 4x4 words into destination "
                "slots 0..16 while placing r2 in slot 1."
            ),
            "abi_evidence": (
                "Arguments are directly in AAPCS core registers r0-r2; r1 is caller-saved; "
                "only caller-saved VFP s0-s15 are used; SP, callee-saved r4-r11 and s16-s31 "
                "are untouched. This is compatible with an ordinary C++ free-function ABI."
            ),
        }
    return {"code_sha256": expected_sha, "functions": functions}


def pack_words(words):
    return b"".join(struct.pack("<I", value & 0xFFFFFFFF) for value in words)


def arm_branch(source: int, target: int) -> bytes:
    displacement = target - source - 8
    if displacement % 4 or not -(1 << 25) <= displacement < (1 << 25):
        raise ValueError("candidate trampoline is not representable as ARM B")
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
            if len(candidate) > 0x1000:
                raise ValueError("candidate exceeds injection code page")
            self.uc.mem_write(INJECT, candidate)
            self.uc.mem_write(address, arm_branch(address, INJECT))
        self.reads: set[int] = set()
        self.writes: set[int] = set()
        self.stack_writes: set[int] = set()
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
            if DATA <= byte < DATA + DATA_SIZE:
                target.add(byte)
            elif STACK <= byte < STACK + STACK_SIZE and access == unicorn.UC_MEM_WRITE:
                self.stack_writes.add(byte)

    def run(self, case):
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        for reg, value in zip(self.gp, case["gp"]):
            uc.reg_write(reg, value)
        uc.reg_write(arm.UC_ARM_REG_SP, SP)
        uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.reg_write(arm.UC_ARM_REG_FPSCR, 0)
        for reg, value in zip(self.sregs, case["s"]):
            uc.reg_write(reg, value)
        uc.mem_write(DATA, case["data"])
        uc.mem_write(STACK, case["stack"])
        self.reads.clear()
        self.writes.clear()
        self.stack_writes.clear()
        self.stopped = False
        fault = None
        try:
            uc.emu_start(self.address, 0, count=256)
        except unicorn.UcError as error:
            fault = str(error)
        return {
            "stopped": self.stopped, "fault": fault,
            "gp": tuple(uc.reg_read(reg) for reg in self.gp),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "s": tuple(uc.reg_read(reg) for reg in self.sregs),
            "data": bytes(uc.mem_read(DATA, DATA_SIZE)),
            "stack": bytes(uc.mem_read(STACK, STACK_SIZE)),
            "reads": frozenset(self.reads), "writes": frozenset(self.writes),
            "stack_writes": frozenset(self.stack_writes),
        }


def compare(reference, candidate):
    for index in range(4, 12):
        if reference["gp"][index] != candidate["gp"][index]:
            return f"r{index} callee-saved GPR"
    for key in ("stopped", "fault", "sp", "data", "reads", "writes"):
        if reference[key] != candidate[key]:
            return key
    entry_sp_offset = SP - STACK
    if reference["stack"][entry_sp_offset:] != candidate["stack"][entry_sp_offset:]:
        return "stack at/above entry SP"
    if reference["s"][16:] != candidate["s"][16:]:
        return "callee-saved VFP registers s16-s31"
    if reference["fault"] or not reference["stopped"]:
        return "execution did not return normally"
    return None


def make_case(seed: int, index: int, overlap: bool = False):
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    src_off, dst_off = (0x400, 0x400 if overlap else 0x800)
    # Keep a unique lane tag while varying low bits across seeds and cases.
    source = [0x7FC00000 | (i << 16) | rng.getrandbits(16) for i in range(16)]
    data[src_off:src_off + 64] = pack_words(source)
    gp = [rng.getrandbits(32) for _ in range(13)]
    gp[0], gp[1], gp[2] = DATA + dst_off, DATA + src_off, rng.getrandbits(32)
    return {"gp": tuple(gp), "s": [rng.getrandbits(32) for _ in range(32)],
            "data": bytes(data), "stack": rng.randbytes(STACK_SIZE)}


def run(code_path: Path, output: Path, seed: int):
    require_unicorn()
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info["code_sha256"], pinned.ledger)
    source_path = ROOT / "experiments/semantic_equivalence/vfp_matrix_transpose_candidates.cpp"
    object_path = output / "vfp_matrix_transpose_candidates.o"
    required = {name for name, _ in FUNCTIONS.values()} | {
        "wrong_transpose_0023aff0", "wrong_slot_002a1b4c"}
    build = compile_tu_armv6k(source_path, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    symbols = {}
    for name, (code, relocations) in extract_elf_functions_detailed(object_path).items():
        if relocations:
            raise ValueError(f"unexpected relocation in {name}: {relocations}")
        symbols[name] = code
    missing = required - symbols.keys()
    if missing:
        raise ValueError(f"candidate symbols missing: {sorted(missing)}")
    flags = get_armv6k_flags(ROOT)
    if any(flag == "-Ofast" or flag.startswith("-ffast-math") for flag in flags):
        raise ValueError("ARMv6K compiler flags unexpectedly enable fast-math")
    cases = [make_case(seed, i, overlap=(i == 32)) for i in range(64)]
    results = []
    for address, (symbol, original_size) in FUNCTIONS.items():
        ref_runner = Runner(pinned.image, address)
        cand_runner = Runner(pinned.image, address, symbols[symbol])
        failure = None
        for index, case in enumerate(cases):
            ref = ref_runner.run(case)
            cand = cand_runner.run(case)
            reason = compare(ref, cand)
            if reason:
                failure = {"case": index, "field": reason}
                break
        results.append({"address": hex(address), "candidate": symbol,
                        "original_bytes": original_size, "candidate_bytes": len(symbols[symbol]),
                        "cases": index + 1, "passed": failure is None, "failure": failure,
                        "source_pattern": "16 lane-distinct raw uint32 words; overlap at case 32"})
    control_case = cases[0]
    negative_controls = []
    for address, symbol, field in (
        (0x0023AFF0, "wrong_transpose_0023aff0", "transpose lane order"),
        (0x002A1B4C, "wrong_slot_002a1b4c", "r2 destination slot"),
    ):
        ref = Runner(pinned.image, address).run(control_case)
        wrong = Runner(pinned.image, address, symbols[symbol]).run(control_case)
        negative_controls.append({"control": symbol, "detects": field,
                                  "detected": ref["data"] != wrong["data"]})
    report = {
        "experiment": "vfp_matrix_transpose_pair",
        "passed": all(item["passed"] for item in results)
                  and all(item["detected"] for item in negative_controls),
        "reference": reference,
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler_flags": flags, "fast_math": False, "seed": seed,
        "function_comparisons": len(cases) * len(FUNCTIONS),
        "cases_per_function": len(cases), "negative_controls": negative_controls,
        "functions": results,
        "comparison_policy": {
            "exact": ["normal return/fault", "r4-r11 and SP", "callee-saved s16-s31",
                       "all data and stack bytes", "ordinary data read/write byte sets"],
            "caller_saved": "r0-r3/r12 and s0-s15 may differ after return; r1 writeback is caller-saved.",
            "stack_accesses": "Candidate private spills below entry SP are allowed by AAPCS. SP, bytes at/above entry SP, and all data-region accesses are exact.",
            "candidate_stack_write_bytes": sorted(set().union(*(Runner(pinned.image, address, symbols[symbol]).run(cases[0])["stack_writes"] for address, (symbol, _) in FUNCTIONS.items()))),
        },
        "caller_windows": [],
        "limitations": [
            "Finite differential cases are evidence, not proof for all inputs.",
            "Only aligned ordinary RAM and listed overlap buffers are tested; MMIO, concurrency and timing are outside scope.",
            "No caller windows or full-game runtime were executed; candidates remain isolated and do not alter production sources or ledger.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed)
    print(json.dumps({"passed": report["passed"], "functions": report["functions"],
                      "negative_controls": report["negative_controls"],
                      "report": str(args.output / "report.json")}))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
