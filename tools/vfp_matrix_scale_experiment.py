#!/usr/bin/env python3
"""Differential test of two VFP 3x4 matrix-scale routines.

This isolated experiment pins both exact reference bodies in the configured
code.bin, compiles non-identical C++ reconstructions without fast-math, and
compares their ordinary-RAM effects in an ARM11 MPCore Unicorn model. It does
not change production sources or the matching ledger.
"""
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
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import TEXT, DATA, STACK, STACK_SIZE, INJECT, RETURN
from tools.semantic_experiment import arm, require_unicorn, unicorn
from tools.semantic_experiment_support import load_pinned_reference
from tools.build_check import get_armv6k_flags

DATA_SIZE = 0x4000
SP = STACK + 0x1000
FUNCTIONS = {
    0x0023D368: ("candidate_0023d368", 52),
    0x0023E55C: ("candidate_0023e55c", 52),
}
EXPECTED = (
    ("vldmia", "r1, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}"),
    ("vldmia", "r2, {s12, s13, s14}"),
    ("vmul.f32", "s0, s0, s12"),
    ("vmul.f32", "s1, s1, s13"),
    ("vmul.f32", "s2, s2, s14"),
    ("vmul.f32", "s4, s4, s12"),
    ("vmul.f32", "s5, s5, s13"),
    ("vmul.f32", "s6, s6, s14"),
    ("vmul.f32", "s8, s8, s12"),
    ("vmul.f32", "s9, s9, s13"),
    ("vmul.f32", "s10, s10, s14"),
    ("vstmia", "r0, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}"),
    ("bx", "lr"),
)
SPECIAL = [
    0x00000000, 0x80000000, 0x00000001, 0x80000001,
    0x007FFFFF, 0x807FFFFF, 0x00800000, 0x80800000,
    0x7F7FFFFF, 0xFF7FFFFF, 0x7F800000, 0xFF800000,
    0x7FC12345, 0xFFC54321, 0x7F812345, 0xFF812345,
]


def decode(image: bytes, address: int, size: int):
    start = address - TEXT
    code = image[start:start + size]
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = list(decoder.disasm(code, address))
    if sum(item.size for item in decoded) != size:
        raise ValueError(f"incomplete ARM disassembly at {address:#x}")
    return code, decoded


def verify_reference(image: bytes, expected: dict, ledger_rows: list[dict]) -> dict:
    ledger = {int(row["address"], 16): row for row in ledger_rows}
    functions = {}
    for address, (symbol, size) in FUNCTIONS.items():
        row = ledger.get(address)
        if row is None or int(row["size"]) != size or row["status"] != "matching":
            raise ValueError(f"matching ledger entry missing/changed at {address:#x}")
        code, decoded = decode(image, address, size)
        normalized = tuple((item.mnemonic.lower(), item.op_str.lower()) for item in decoded)
        if normalized != EXPECTED:
            raise ValueError(f"VFP instructions changed at {address:#x}: {normalized}")
        functions[hex(address)] = {
            "symbol": symbol,
            "size": size,
            "sha256": hashlib.sha256(code).hexdigest(),
            "bytes": code.hex(),
            "instructions": [f"{mnemonic} {operands}" for mnemonic, operands in EXPECTED],
            "observed_behavior": (
                "Loads s0-s11 from r1 and s12-s14 from r2; multiplies lanes 0,1,2 "
                "by s12,s13,s14 respectively, repeats that routing for lanes 4,5,6 "
                "and 8,9,10, leaves lanes 3,7,11 unchanged, then stores all 12 lanes to r0."
            ),
            "unknowns": "Caller intent and non-ordinary-memory/device semantics are not inferred.",
        }
    return {"code_sha256": expected, "functions": functions}


def branch(source: int, target: int) -> bytes:
    displacement = target - source - 8
    if displacement % 4 or not -(1 << 25) <= displacement < (1 << 25):
        raise ValueError("candidate trampoline is not representable as ARM B")
    return struct.pack("<I", 0xEA000000 | ((displacement >> 2) & 0xFFFFFF))


def pack_words(words):
    return b"".join(struct.pack("<I", value & 0xFFFFFFFF) for value in words)


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
            self.uc.mem_write(address, branch(address, INJECT))
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
            if (DATA <= byte < DATA + DATA_SIZE
                    or STACK <= byte < STACK + STACK_SIZE):
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
        self.reads.clear()
        self.writes.clear()
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
            "lr": uc.reg_read(arm.UC_ARM_REG_LR),
            "cpsr": uc.reg_read(arm.UC_ARM_REG_CPSR),
            "fpscr": uc.reg_read(arm.UC_ARM_REG_FPSCR),
            "fpexc": uc.reg_read(arm.UC_ARM_REG_FPEXC),
            "s": tuple(uc.reg_read(reg) for reg in self.sregs),
            "data": bytes(uc.mem_read(DATA, DATA_SIZE)),
            "stack": bytes(uc.mem_read(STACK, STACK_SIZE)),
            "reads": frozenset(self.reads), "writes": frozenset(self.writes),
        }


def compare(reference, candidate):
    # Require callee-saved GPRs only; r0-r3/r12 are caller-saved. Likewise
    # s16-s31 are callee-saved under AAPCS/VFP PCS; s0-s15 are captured below.
    for index in range(4, 12):
        if reference["gp"][index] != candidate["gp"][index]:
            return f"r{index} callee-saved GPR"
    for key in ("stopped", "fault", "sp", "fpscr", "fpexc", "data", "stack",
                "reads", "writes"):
        if reference[key] != candidate[key]:
            return key
    if reference["s"][16:] != candidate["s"][16:]:
        return "callee-saved VFP registers s16-s31"
    if reference["fault"] or not reference["stopped"]:
        return "execution did not return normally"
    return None


def make_case(label: str, source: list[int], factors: list[int], fpscr: int,
              seed: int, index: int, alias: tuple[int, int, int] | None = None):
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    source_off, factor_off, destination_off = (0x400, 0x700, 0xA00)
    if alias:
        source_off, factor_off, destination_off = alias
    # The original issues both input loads before the destination store. When
    # inputs overlap, these overlays model the final bytes at function entry.
    data[source_off:source_off + 48] = pack_words(source)
    data[factor_off:factor_off + 12] = pack_words(factors)
    gp = [rng.getrandbits(32) for _ in range(13)]
    gp[0], gp[1], gp[2] = DATA + destination_off, DATA + source_off, DATA + factor_off
    sregs = [rng.getrandbits(32) for _ in range(32)]
    return {"label": label, "gp": tuple(gp), "s": tuple(sregs), "fpscr": fpscr,
            "data": bytes(data), "stack": rng.randbytes(STACK_SIZE)}


def make_cases(seed: int):
    rng = random.Random(seed)
    index = 0
    # Cross special values through all lanes/factors and FPSCR rounding/FZ/DN
    # combinations. Sticky exception flags vary as an additional input state.
    for special_index, _ in enumerate(SPECIAL):
        source = [SPECIAL[(special_index + i) % len(SPECIAL)] for i in range(12)]
        factors = [SPECIAL[(special_index * 3 + i * 5) % len(SPECIAL)] for i in range(3)]
        for rounding in range(4):
            for flush in (0, 1):
                for default_nan in (0, 1):
                    fpscr = ((rounding << 22) | (flush << 24) | (default_nan << 25)
                             | ((index * 7) & 0x1F))
                    yield make_case(f"special-{special_index}-rm{rounding}-fz{flush}-dn{default_nan}",
                                    source, factors, fpscr, seed, index)
                    index += 1
    for i in range(96):
        source = [rng.getrandbits(32) for _ in range(12)]
        factors = [rng.getrandbits(32) for _ in range(3)]
        fpscr = ((i % 4) << 22) | (((i // 4) & 1) << 24) | (((i // 8) & 1) << 25) | (i & 0x1F)
        yield make_case(f"random-{i}", source, factors, fpscr, seed, index)
        index += 1


def run(code_path: Path, output: Path, seed: int = 20261024) -> dict:
    require_unicorn()
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(
        code_path, ROOT / "config/game_info.json", ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info["code_sha256"], pinned.ledger)
    source_path = ROOT / "experiments/semantic_equivalence/vfp_matrix_scale_candidates.cpp"
    object_path = output / "vfp_matrix_scale_candidates.o"
    required = {name for name, _size in FUNCTIONS.values()} | {
        "wrong_factor_0023d368", "wrong_lane_0023e55c"}
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
    cases = list(make_cases(seed))
    alias_layouts = (
        (0x400, 0x700, 0x400),  # destination == source
        (0x400, 0x700, 0x404),  # destination one word into source
        (0x404, 0x700, 0x400),  # destination one word before source
        (0x400, 0x400, 0x700),  # source == factors
        (0x400, 0x700, 0x700),  # destination == factors
        (0x500, 0x500, 0x500),  # all pointers identical
    )
    for i, layout in enumerate(alias_layouts):
        src = [0x3F000000 + i * 0x100 + j * 0x101 for j in range(12)]
        fac = [0x3F800000 + i * 0x200 + j * 0x201 for j in range(3)]
        cases.append(make_case(f"alias-{i}", src, fac, 0x1F, seed, 10000 + i, layout))

    results = []
    for address, (symbol, original_size) in FUNCTIONS.items():
        ref_runner = Runner(pinned.image, address)
        candidate_runner = Runner(pinned.image, address, symbols[symbol])
        failure = None
        cases_run = 0
        scratch_diffs = []
        caller_gpr_diffs = []
        first_access = None
        for index, case in enumerate(cases):
            cases_run += 1
            ref = ref_runner.run(case)
            cand = candidate_runner.run(case)
            if first_access is None:
                first_access = {
                    "case": case["label"],
                    "reference_read_bytes": len(ref["reads"]),
                    "candidate_read_bytes": len(cand["reads"]),
                    "reference_write_bytes": len(ref["writes"]),
                    "candidate_write_bytes": len(cand["writes"]),
                    "read_sets_exact": ref["reads"] == cand["reads"],
                    "write_sets_exact": ref["writes"] == cand["writes"],
                }
            changed_s = [i for i, (a, b) in enumerate(zip(ref["s"], cand["s"])) if a != b]
            if changed_s and len(scratch_diffs) < 8:
                scratch_diffs.append({"case": case["label"], "registers": changed_s})
            changed_caller_gpr = [i for i, (a, b) in enumerate(zip(ref["gp"], cand["gp"]))
                                  if a != b and i in (0, 1, 2, 3, 12)]
            if changed_caller_gpr and len(caller_gpr_diffs) < 8:
                caller_gpr_diffs.append({"case": case["label"], "registers": changed_caller_gpr})
            reason = compare(ref, cand)
            if reason:
                failure = {"case": case["label"], "field": reason,
                           "reference_fpscr": f"0x{ref['fpscr']:08x}",
                           "candidate_fpscr": f"0x{cand['fpscr']:08x}",
                           "changed_s_registers": changed_s}
                break
        results.append({
            "address": hex(address), "candidate": symbol,
            "original_bytes": original_size, "candidate_bytes": len(symbols[symbol]),
            "cases": cases_run,
            "passed": failure is None, "failure": failure,
            "caller_saved_s_differences_sample": scratch_diffs,
            "caller_saved_gpr_differences_sample": caller_gpr_diffs,
            "callee_saved_vfp_registers": "s16-s31 (d8-d15)",
            "separate_buffer_access_footprint": first_access,
        })

    finite_case = next(case for case in cases if case["label"] == "random-0")
    negative_controls = []
    for address, symbol, field in (
        (0x0023D368, "wrong_factor_0023d368", "factor routing"),
        (0x0023E55C, "wrong_lane_0023e55c", "source lane selection"),
    ):
        ref = Runner(pinned.image, address).run(finite_case)
        wrong = Runner(pinned.image, address, symbols[symbol]).run(finite_case)
        reason = "data" if ref["data"] != wrong["data"] else compare(ref, wrong)
        negative_controls.append({"control": symbol, "detects": field,
                                  "detected": reason is not None, "first_difference": reason})

    report = {
        "experiment": "vfp_matrix_scale_pair",
        "passed": all(result["passed"] for result in results)
                  and all(control["detected"] for control in negative_controls),
        "reference": reference,
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler_flags": flags,
        "fast_math": False,
        "seed": seed,
        "random_cases": 96,
        "special_fpscr_cases": len(SPECIAL) * 16,
        "alias_cases": len(alias_layouts),
        "comparison_policy": {
            "exact": ["normal return/fault state", "r4-r11 and SP", "FPSCR including sticky flags",
                       "FPEXC", "callee-saved s16-s31", "all test data and stack bytes",
                       "ordinary RAM read/write byte sets including the modeled stack"],
            "caller_saved": "r0-r3/r12 and s0-s15 are recorded where changed; exact post-state is not ABI-required.",
            "fp_semantics": "ARM11 MPCore VFPv2 binary32; four rounding modes; FZ/DN both enabled and disabled; no fast-math.",
        },
        "functions": results,
        "negative_controls": negative_controls,
        "caller_windows": [],
        "caller_window_note": "No direct caller window was independently reviewed for this experiment.",
        "limitations": [
            "Finite differential cases are evidence, not a proof over every input or FPSCR state.",
            "Unicorn ARM11 MPCore VFPv2 ordinary-memory execution is the test oracle; hardware, traps, MMIO, concurrency and timing are outside scope.",
            "Alias cases cover the listed aligned layouts only; arbitrary unaligned VFP multiple-transfer semantics are not claimed.",
            "No callers or full-game runtime were executed. This isolated candidate is not integrated into production or the match ledger.",
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
