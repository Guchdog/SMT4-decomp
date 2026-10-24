#!/usr/bin/env python3
"""Differential VFP experiment for two twelve-lane block scalers.

Reports and compiler output are isolated under ignored build/ paths. The
reference bytes are taken from the hash-pinned private code.bin; no production
source or matching ledger is changed. Compilation uses the repository's ARMv6K
flags, which do not enable fast-math.
"""
from __future__ import annotations

import argparse
import csv
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
from tools.semantic_experiment import TEXT, DATA, STACK, STACK_SIZE, INJECT, RETURN, arm_branch, require_unicorn
from tools.semantic_experiment import unicorn, arm

DATA_SIZE = 0x4000
SP = STACK + 0x1000
FUNCTIONS = {
    0x0015F6D4: ("candidate_0015f6d4", 64),
    0x00256ED8: ("candidate_00256ed8", 64),
}
EXPECTED = (
    ("vldmia", "r2, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}"),
    ("vldmia", "r1, {s12, s13, s14}"),
    ("vmul.f32", "s0, s0, s12"), ("vmul.f32", "s1, s1, s12"),
    ("vmul.f32", "s2, s2, s12"), ("vmul.f32", "s3, s3, s12"),
    ("vmul.f32", "s4, s4, s13"), ("vmul.f32", "s5, s5, s13"),
    ("vmul.f32", "s6, s6, s13"), ("vmul.f32", "s7, s7, s13"),
    ("vmul.f32", "s8, s8, s14"), ("vmul.f32", "s9, s9, s14"),
    ("vmul.f32", "s10, s10, s14"), ("vmul.f32", "s11, s11, s14"),
    ("vstmia", "r0, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11}"),
    ("bx", "lr"),
)


def _decode(image: bytes, address: int, size: int):
    code = image[address - TEXT:address - TEXT + size]
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = list(decoder.disasm(code, address))
    if sum(x.size for x in decoded) != size:
        raise ValueError(f"incomplete ARM disassembly at {address:#x}")
    return code, decoded


def verify_reference(image: bytes, expected_sha256: str, ledger: dict[int, dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if not expected_sha256 or digest != expected_sha256:
        raise ValueError("code.bin SHA-256 does not match pinned game revision")
    funcs = {}
    for address, (symbol, size) in FUNCTIONS.items():
        row = ledger.get(address)
        if row is None or int(row["size"]) != size or row["status"] != "matching":
            raise ValueError(f"matching ledger entry missing/changed at {address:#x}")
        code, decoded = _decode(image, address, size)
        normalized = tuple((x.mnemonic.lower(), x.op_str.lower()) for x in decoded)
        if normalized != EXPECTED:
            raise ValueError(f"VFP instruction sequence changed at {address:#x}: {normalized}")
        funcs[hex(address)] = {
            "symbol": symbol, "size": size,
            "sha256": hashlib.sha256(code).hexdigest(), "bytes": code.hex(),
            "instructions": [f"{m} {o}".strip() for m, o in EXPECTED],
            "observed_behavior": (
                "Loads source words s0-s11 from r2 and factors s12-s14 from r1; "
                "multiplies lanes 0-3 by factor 0, lanes 4-7 by factor 1, "
                "lanes 8-11 by factor 2; stores s0-s11 to r0."
            ),
            "unknowns": "Caller intent and non-ordinary-memory/device semantics are not inferred.",
        }
    return {"code_sha256": digest, "functions": funcs}


def _branch(source: int, destination: int) -> bytes:
    displacement = destination - source - 8
    if displacement % 4 or not -(1 << 25) <= displacement < (1 << 25):
        raise ValueError("candidate trampoline is not representable as ARM B")
    return struct.pack("<I", 0xEA000000 | ((displacement >> 2) & 0xFFFFFF))


def _u32s(values):
    return b"".join(struct.pack("<I", v & 0xFFFFFFFF) for v in values)


class VfpRunner:
    def __init__(self, image: bytes, address: int, replacement: bytes | None = None):
        require_unicorn()
        self.address = address
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, 0x400000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, 0x2000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        if replacement is not None:
            if len(replacement) > 0x1000:
                raise ValueError("candidate exceeds injection code page")
            self.uc.mem_write(INJECT, replacement)
            self.uc.mem_write(address, _branch(address, INJECT))
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
            if DATA <= byte < DATA + DATA_SIZE:
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
            "fpscr": uc.reg_read(arm.UC_ARM_REG_FPSCR),
            "fpexc": uc.reg_read(arm.UC_ARM_REG_FPEXC),
            "s": tuple(uc.reg_read(reg) for reg in self.sregs),
            "data": bytes(uc.mem_read(DATA, DATA_SIZE)),
            "reads": frozenset(self.reads), "writes": frozenset(self.writes),
        }


def compare(a, b):
    # s0-s15 (d0-d7) are caller-saved under the ARM VFP procedure-call
    # standard. Their exact post-state is retained in the report; only the
    # callee-saved bank s16-s31 (d8-d15) is a required equivalence observable.
    for key in ("stopped", "fault", "gp", "sp", "fpscr", "fpexc",
                "data", "reads", "writes"):
        if a[key] != b[key]:
            return key
    if a["s"][16:] != b["s"][16:]:
        return "callee-saved VFP registers s16-s31"
    if a["fault"] or not a["stopped"]:
        return "execution did not return normally"
    return None


SPECIAL = [
    0x00000000, 0x80000000, 0x00000001, 0x80000001,
    0x007FFFFF, 0x807FFFFF, 0x00800000, 0x80800000,
    0x7F7FFFFF, 0xFF7FFFFF, 0x7F800000, 0xFF800000,
    0x7FC12345, 0xFFC54321, 0x7F812345, 0xFF812345,
]


def make_cases(seed: int):
    rng = random.Random(seed)
    case_index = 0
    for special_index, special in enumerate(SPECIAL):
        source = [SPECIAL[(special_index + i) % len(SPECIAL)] for i in range(12)]
        factors = [SPECIAL[(special_index * 3 + i * 5) % len(SPECIAL)] for i in range(3)]
        for rounding in range(4):
            for flush in (0, 1):
                # Include DN both ways; seeded sticky flags ensure accumulation is checked.
                for default_nan in (0, 1):
                    flags = (case_index * 7) & 0x1F
                    fpscr = (rounding << 22) | (flush << 24) | (default_nan << 25) | flags
                    yield _case(f"special-{special_index}-rm{rounding}-fz{flush}-dn{default_nan}",
                                source, factors, fpscr, seed, case_index)
                    case_index += 1
    # Explicit nontrivial products exercise rounding boundaries and broad exponents.
    for i in range(96):
        source = [rng.getrandbits(32) for _ in range(12)]
        factors = [rng.getrandbits(32) for _ in range(3)]
        rounding = i % 4
        flush = (i // 4) & 1
        dn = (i // 8) & 1
        fpscr = (rounding << 22) | (flush << 24) | (dn << 25) | (i & 0x1F)
        yield _case(f"random-{i}", source, factors, fpscr, seed, case_index)
        case_index += 1


def _case(label, source, factors, fpscr, seed, index, alias=None):
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    src_off, fac_off, dst_off = (0x400, 0x700, 0xA00)
    if alias:
        src_off, fac_off, dst_off = alias
    data[src_off:src_off + 48] = _u32s(source)
    data[fac_off:fac_off + 12] = _u32s(factors)
    gp = [rng.getrandbits(32) for _ in range(13)]
    gp[0], gp[1], gp[2] = DATA + dst_off, DATA + fac_off, DATA + src_off
    # VFP register seed includes signed zeros/NaNs as well as unique payloads.
    sregs = [rng.getrandbits(32) for _ in range(32)]
    return {"label": label, "gp": tuple(gp), "s": tuple(sregs), "fpscr": fpscr,
            "data": bytes(data), "stack": rng.randbytes(STACK_SIZE)}


def build_symbols(output: Path):
    source = ROOT / "experiments/semantic_equivalence/vfp_block_scale_candidates.cpp"
    obj = output / "vfp_block_scale_candidates.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    symbols = {}
    for name, (code, relocations) in extract_elf_functions_detailed(obj).items():
        if relocations:
            raise ValueError(f"unexpected relocation in {name}: {relocations}")
        symbols[name] = code
    flags = get_armv6k_flags(ROOT)
    if any(flag in ("-ffast-math", "-Ofast") or flag.startswith("-ffast-math=")
           for flag in flags):
        raise ValueError("compiler flags unexpectedly enable fast-math")
    return symbols, source, flags


def run(code_path: Path, output: Path, seed: int = 20261024) -> dict:
    require_unicorn()
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        ledger = {int(row["address"], 16): row for row in csv.DictReader(stream)}
    reference = verify_reference(image, game["code_sha256"], ledger)
    symbols, source, compile_flags = build_symbols(output)
    required = {v[0] for v in FUNCTIONS.values()} | {
        "wrong_factor_0015f6d4", "wrong_lane_00256ed8"}
    if required - symbols.keys():
        raise ValueError(f"candidate symbols missing: {sorted(required - symbols.keys())}")

    cases = list(make_cases(seed))
    # Word-aligned alias matrix: all reads occur before original stores. These
    # cases verify exact ordinary-RAM result and access-byte footprint.
    alias_matrix = (
        (0x400, 0x700, 0x400),  # exact dst == src
        (0x400, 0x700, 0x404),  # destination begins one word into source
        (0x404, 0x700, 0x400),  # destination ends one word before source
        (0x400, 0x400, 0x700),  # destination == factors
        (0x400, 0x700, 0x700),  # factors == source start
        (0x500, 0x500, 0x500),  # all pointers identical
    )
    for index, offsets in enumerate(alias_matrix):
        # Deterministic finite values ensure the alias signal itself is useful.
        src = [0x3F000000 + index * 0x100 + j * 0x101 for j in range(12)]
        fac = [0x3F800000 + index * 0x200 + j * 0x201 for j in range(3)]
        cases.append(_case(f"alias-{index}", src, fac, 0x1F, seed, 10000 + index, offsets))

    function_results = []
    for address, (symbol, original_size) in FUNCTIONS.items():
        reference_runner = VfpRunner(image, address)
        candidate_runner = VfpRunner(image, address, symbols[symbol])
        count = 0
        failure = None
        fp_scratch_diffs = []
        access_footprint = None
        for case in cases:
            left = reference_runner.run(case)
            right = candidate_runner.run(case)
            if access_footprint is None:
                access_footprint = {
                    "case": case["label"],
                    "reference_read_bytes": len(left["reads"]),
                    "candidate_read_bytes": len(right["reads"]),
                    "reference_write_bytes": len(left["writes"]),
                    "candidate_write_bytes": len(right["writes"]),
                    "read_sets_exact": left["reads"] == right["reads"],
                    "write_sets_exact": left["writes"] == right["writes"],
                }
            # Full S-state is compared for strict observability. ABI-preserved
            # bank s16-s31 is also reported separately for diagnosis.
            changed_s = [i for i, (a, b) in enumerate(zip(left["s"], right["s"])) if a != b]
            if changed_s and len(fp_scratch_diffs) < 8:
                fp_scratch_diffs.append({"case": case["label"], "registers": changed_s})
            reason = compare(left, right)
            count += 1
            if reason:
                failure = {"case": case["label"], "field": reason,
                           "reference_fpscr": f"0x{left['fpscr']:08x}",
                           "candidate_fpscr": f"0x{right['fpscr']:08x}",
                           "changed_s_registers": changed_s}
                break
        function_results.append({
            "address": hex(address), "candidate": symbol,
            "original_bytes": original_size, "candidate_bytes": len(symbols[symbol]),
            "cases": count, "passed": failure is None, "failure": failure,
            "full_s_register_exact": not fp_scratch_diffs,
            "s_register_differences_sample": fp_scratch_diffs,
            "abi_preserved_vfp_registers": "s16-s31 (d8-d15)",
            "separate_buffer_access_footprint": access_footprint,
        })

    negative_controls = []
    # Use separated, ordinary finite buffers and ensure different outputs.
    for address, wrong_symbol, field in (
        (0x0015F6D4, "wrong_factor_0015f6d4", "factor-group mapping"),
        (0x00256ED8, "wrong_lane_00256ed8", "source-lane order"),
    ):
        case = next(c for c in cases if c["label"] == "random-0")
        ref = VfpRunner(image, address).run(case)
        wrong = VfpRunner(image, address, symbols[wrong_symbol]).run(case)
        reason = "data" if ref["data"] != wrong["data"] else compare(ref, wrong)
        negative_controls.append({"control": wrong_symbol, "detects": field,
                                  "detected": reason is not None,
                                  "first_difference": reason})

    report = {
        "experiment": "vfp_twelve_lane_block_scale_pair",
        "passed": all(x["passed"] for x in function_results)
                  and all(x["detected"] for x in negative_controls),
        "reference": reference,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "object_sha256": hashlib.sha256((output / "vfp_block_scale_candidates.o").read_bytes()).hexdigest(),
        "compiler_flags": compile_flags,
        "fast_math": False,
        "seed": seed, "random_cases": 96, "edge_case_matrix": len(SPECIAL) * 16,
        "alias_cases": len(alias_matrix), "comparison_policy": {
            "exact": ["return PC/normal return", "FPSCR including sticky exception flags",
                       "callee-saved s16-s31 bit patterns", "all ordinary RAM bytes",
                       "ordinary RAM read-byte set", "ordinary RAM write-byte set",
                       "r0-r12", "SP", "FPEXC"],
            "caller_saved_vfp": "s0-s15 exact post-state is recorded; differences are permitted by ABI",
            "abi_vfp_preservation": "s16-s31 (d8-d15) exact post-state required",
            "fp_semantics": "ARM11 MPCore VFPv2; binary32 values; all four FPSCR rounding modes; FZ/DN on and off; compiler flags verified to exclude fast-math",
        },
        "functions": function_results,
        "negative_controls": negative_controls,
        "caller_windows": [],
        "caller_window_note": "None added; no caller setup/consumption window was independently inspected for this batch.",
        "limitations": [
            "Finite generated cases are differential evidence, not a proof for all IEEE-754 inputs or FPSCR states.",
            "Unicorn ARM11 MPCore VFPv2 ordinary-memory execution is the test oracle; hardware, exception traps, concurrent observers, MMIO, timing and OS behavior are outside scope.",
            "Aligned word pointers only. Aliasing is tested for the listed aligned layouts; arbitrary unaligned VFP multiple-transfer behavior is not claimed.",
            "No caller windows or game runtime were executed. Candidate reconstruction is isolated and not integrated into production or the match ledger.",
        ],
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
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
