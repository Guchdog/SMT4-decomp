#!/usr/bin/env python3
"""Differentially test two isolated ARM VFP lane-add routines.

This experiment intentionally compares ABI-observable VFP state (FPSCR and
callee-saved d8-d15), GPR callee-saves, external memory, faults, and byte-level
read/write footprints. Caller-saved s0-s15/GPRs are reported diagnostically,
not treated as preserved by AAPCS. No callers are claimed or executed.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
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
import unicorn
from unicorn import arm_const as arm

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import TEXT, DATA, DATA_SIZE, STACK, STACK_SIZE, SP, INJECT, RETURN, U32_MASK, arm_branch
from tools.semantic_experiment_support import load_pinned_reference

FUNCTIONS = {
    0x0023E4E4: (0xEC920A0C, 0xEC916A03, 0xEE711A86, 0xEE733AA6,
                 0xEE755A87, 0xEC800A0C, 0xE12FFF1E),
    0x002A3788: (0xEC920A0C, 0xEC916A03, 0xEE711A86, 0xEE733AA6,
                 0xEE755A87, 0xEC800A0C, 0xE12FFF1E),
}
LEDGER_SIZES = {address: 28 for address in FUNCTIONS}
SYMBOLS = {0x0023E4E4: "candidate_0023e4e4", 0x002A3788: "candidate_002a3788"}
FPSCR_PINNED = 0x00000000  # RN, gradual underflow, default-NaN off, traps masked, flags clear.
FLOAT_EDGES = (
    0x00000000, 0x80000000,  # +0, -0
    0x00000001, 0x007FFFFF,  # smallest/largest positive subnormal
    0x80000001, 0x807FFFFF,  # smallest/largest negative subnormal
    0x00800000, 0x80800000,  # smallest positive/negative normal
    0x3F800000, 0xBF800000,  # +/-1
    0x7F7FFFFF, 0xFF7FFFFF,  # +/-max finite
    0x7F800000, 0xFF800000,  # +/-infinity
    0x7FC12345, 0xFFC54321,  # positive/negative qNaN with payload
    0x7F812345, 0xFF854321,  # positive/negative sNaN with payload
    0x3F800000, 0x33800000,  # 1 and half an ulp at 1 (rounding boundary)
)


@dataclass(frozen=True)
class Case:
    label: str
    registers: tuple[int, ...]
    data: bytes
    vfp: tuple[int, ...]
    cpsr: int


@dataclass(frozen=True)
class Execution:
    fault: str | None
    stopped: bool
    pc: int
    gpr: tuple[int, ...]
    cpsr: int
    fpscr: int
    sregs: tuple[int, ...]
    data: bytes
    reads: frozenset[int]
    writes: frozenset[int]


def verify_reference(reference) -> dict:
    by_address = {int(row["address"], 16): row for row in reference.ledger}
    functions = {}
    for address, expected in FUNCTIONS.items():
        row = by_address.get(address)
        if (row is None or row["status"] != "matching"
                or int(row["size"]) != LEDGER_SIZES[address]):
            raise ValueError(f"Ledger entry changed at {address:#010x}")
        start = address - TEXT
        actual = reference.image[start:start + LEDGER_SIZES[address]]
        words = struct.unpack("<7I", actual)
        if words != expected:
            raise ValueError(f"Instruction words changed at {address:#010x}: {words!r}")
        functions[hex(address)] = {
            "ledger_name": row["name"],
            "instruction_words": [f"0x{word:08x}" for word in words],
            "instruction_bytes_sha256": hashlib.sha256(actual).hexdigest(),
        }
    return {
        "code_bin_sha256": reference.game_info["code_sha256"],
        "functions": functions,
        "caller_evidence": "None collected; no caller behavior is claimed.",
    }


def _validate_candidate(code: bytes) -> None:
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    cs.detail = True
    instructions = list(cs.disasm(code, 0))
    if not instructions or sum(item.size for item in instructions) != len(code):
        raise ValueError("Candidate has incomplete ARM disassembly")
    if instructions[-1].mnemonic != "bx" or instructions[-1].op_str != "lr":
        raise ValueError("Candidate must return through bx lr")
    for insn in instructions[:-1]:
        if insn.group(capstone.CS_GRP_CALL):
            raise ValueError("Candidate must not call external code")
        if insn.group(capstone.CS_GRP_JUMP):
            raise ValueError("Candidate must not contain branches")
        if "pc" in insn.op_str:
            raise ValueError("Candidate must not depend on PC-relative data")


def compile_candidates(output: Path) -> dict[str, bytes]:
    src = ROOT / "experiments/semantic_equivalence/vfp_lane_add_candidates.cpp"
    obj = output / "vfp_lane_add_candidates.o"
    result = compile_tu_armv6k(src, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "VFP candidate compilation failed")
    extracted = extract_elf_functions_detailed(obj)
    compiled = {}
    expected = [*SYMBOLS.values()]
    for address in FUNCTIONS:
        expected.extend((f"wrong_lanes_{address:08x}", f"wrong_operation_{address:08x}"))
    for symbol, (code, relocations) in extracted.items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        _validate_candidate(code)
        compiled[symbol] = code
    missing = set(expected) - compiled.keys()
    if missing:
        raise ValueError(f"Missing candidate symbols: {sorted(missing)}")
    return compiled


def _put_words(memory: bytearray, offset: int, words: tuple[int, ...]) -> None:
    for index, word in enumerate(words):
        struct.pack_into("<I", memory, offset + index * 4, word & U32_MASK)


def make_cases(address: int, seed: int, samples: int):
    rng = random.Random(seed ^ address)
    # Include edge operands against 1.0, plus each edge in each addend lane.
    for index, edge in enumerate(FLOAT_EDGES):
        src = [0x3F800000 + ((lane * 13 + index) & 0x3FF) for lane in range(12)]
        adds = [0x3F800000, 0x3F800000, 0x3F800000]
        target = index % 3
        src[3 + target * 4] = edge
        adds[target] = FLOAT_EDGES[(index + 7) % len(FLOAT_EDGES)]
        yield _case(rng, f"edge-{index:02d}-{edge:08x}", src, adds, (0x100, 0x200, 0x300))

    # Deterministic mixed edge vectors exercise each lane and exception flag.
    for index in range(32):
        src = [FLOAT_EDGES[(index * 5 + lane * 3) % len(FLOAT_EDGES)] for lane in range(12)]
        adds = [FLOAT_EDGES[(index * 7 + lane * 5 + 1) % len(FLOAT_EDGES)] for lane in range(3)]
        yield _case(rng, f"mixed-edge-{index:02d}", src, adds, (0x100, 0x200, 0x300))

    # A variety of 4-byte-aligned aliases. Writes are applied after initial
    # src/addend data, so their initial overlapping contents are unambiguous.
    src_words = [rng.getrandbits(32) for _ in range(12)]
    add_words = [rng.getrandbits(32) for _ in range(3)]
    layouts = ((0x100, 0x200, 0x100),  # dst == src
               (0x100, 0x200, 0x200),  # dst == addend
               (0x100, 0x100, 0x300),  # src == addend
               (0x100, 0x108, 0x104),  # shifted partial overlap
               (0x104, 0x100, 0x108),
               (0x100, 0x100, 0x100))  # all pointers equal
    for index, (src_offset, add_offset, dst_offset) in enumerate(layouts):
        yield _case(rng, f"alias-{index}", src_words, add_words,
                    (src_offset, add_offset, dst_offset))

    for index in range(samples):
        # Mostly finite values, with occasional full bit-pattern cases.
        src = [rng.getrandbits(32) if index % 8 == 0
               else rng.randint(0x00800000, 0x7F7FFFFF) for _ in range(12)]
        adds = [rng.getrandbits(32) if index % 8 == 0
                else rng.randint(0x00800000, 0x7F7FFFFF) for _ in range(3)]
        yield _case(rng, f"random-{index:04d}", src, adds, (0x100, 0x200, 0x300))


def _case(rng: random.Random, label: str, src_words: list[int], add_words: list[int],
          offsets: tuple[int, int, int]) -> Case:
    src_offset, add_offset, dst_offset = offsets
    data = bytearray(rng.randbytes(DATA_SIZE))
    _put_words(data, src_offset, tuple(src_words))
    _put_words(data, add_offset, tuple(add_words))
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0] = DATA + dst_offset
    registers[1] = DATA + add_offset
    registers[2] = DATA + src_offset
    # VFP input values are arbitrary state. The FP mode itself is pinned in
    # FPSCR independently below; these S registers are caller-saved scratch.
    vfp = tuple(rng.getrandbits(32) for _ in range(32))
    cpsr = 0x10 | ((rng.getrandbits(4) & 0xF) << 28)
    return Case(label, tuple(registers), bytes(data), vfp, cpsr)


class VfpRunner:
    def __init__(self, image: bytes, entry: int, replacement: bytes | None = None):
        self.entry = entry
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        # The emulated ARM11 defaults CP10/CP11 and VFP disabled; the game
        # image executes in a configured user process with VFP access enabled.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(TEXT, 0x400000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, 0x2000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        if replacement is not None:
            _validate_candidate(replacement)
            self.uc.mem_write(INJECT, replacement)
            self.uc.mem_write(entry, arm_branch(entry, INJECT))
        self.gpr_ids = tuple(getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13))
        self.sreg_ids = tuple(getattr(arm, f"UC_ARM_REG_S{i}") for i in range(32))
        self.reads: set[int] = set()
        self.writes: set[int] = set()
        self.stopped = False
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE,
                         self._memory)

    def _code(self, uc, address, _size, _user):
        if address == RETURN:
            self.stopped = True
            uc.emu_stop()

    def _memory(self, _uc, access, address, size, _value, _user):
        target = self.writes if access == unicorn.UC_MEM_WRITE else self.reads
        for byte in range(address, address + size):
            if DATA <= byte < DATA + DATA_SIZE:
                target.add(byte)

    def run(self, case: Case) -> Execution:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_CPSR, case.cpsr)
        for reg, value in zip(self.gpr_ids, case.registers):
            uc.reg_write(reg, value)
        uc.reg_write(arm.UC_ARM_REG_SP, SP)
        uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        for reg, value in zip(self.sreg_ids, case.vfp):
            uc.reg_write(reg, value)
        uc.reg_write(arm.UC_ARM_REG_FPSCR, FPSCR_PINNED)
        uc.mem_write(DATA, case.data)
        uc.mem_write(STACK, bytes(STACK_SIZE))
        self.reads.clear()
        self.writes.clear()
        self.stopped = False
        fault = None
        try:
            uc.emu_start(self.entry, 0, count=512)
        except unicorn.UcError as error:
            fault = str(error)
        gpr = tuple(uc.reg_read(reg) for reg in self.gpr_ids)
        gpr += (uc.reg_read(arm.UC_ARM_REG_SP), uc.reg_read(arm.UC_ARM_REG_LR))
        return Execution(
            fault, self.stopped, uc.reg_read(arm.UC_ARM_REG_PC), gpr,
            uc.reg_read(arm.UC_ARM_REG_CPSR) & 0xF0000000,
            uc.reg_read(arm.UC_ARM_REG_FPSCR),
            tuple(uc.reg_read(reg) for reg in self.sreg_ids),
            bytes(uc.mem_read(DATA, DATA_SIZE)), frozenset(self.reads),
            frozenset(self.writes),
        )


def expected_footprint(case: Case) -> tuple[frozenset[int], frozenset[int]]:
    dst, addend, src = case.registers[:3]
    reads = frozenset((*range(src, src + 48), *range(addend, addend + 12)))
    writes = frozenset(range(dst, dst + 48))
    return reads, writes


def compare(original: Execution, rebuilt: Execution, case: Case) -> dict:
    details = []
    if original.fault != rebuilt.fault:
        details.append("fault behavior differs")
    if not original.stopped or not rebuilt.stopped:
        details.append("execution did not return normally")
    # AAPCS callee-saved GPRs r4-r11 and SP; LR must still hold the return address.
    if original.gpr[4:12] + original.gpr[13:15] != rebuilt.gpr[4:12] + rebuilt.gpr[13:15]:
        details.append("callee-saved GPR/SP or return-address LR differs")
    if original.fpscr != rebuilt.fpscr:
        details.append(f"FPSCR differs: {original.fpscr:#010x} vs {rebuilt.fpscr:#010x}")
    # AAPCS VFP callee-saves are d8-d15, i.e. s16-s31.
    if original.sregs[16:] != rebuilt.sregs[16:]:
        details.append("callee-saved VFP d8-d15 state differs")
    if original.cpsr != rebuilt.cpsr:
        details.append("NZCV differs (diagnostic; condition flags are caller-saved)")
    if original.data != rebuilt.data:
        details.append("DATA memory differs")
    if original.reads != rebuilt.reads:
        details.append("DATA read-byte footprint differs")
    if original.writes != rebuilt.writes:
        details.append("DATA write-byte footprint differs")
    expected_reads, expected_writes = expected_footprint(case)
    if original.reads != expected_reads or original.writes != expected_writes:
        details.append("original DATA access footprint differs from 12+3 reads and 12 writes")
    caller_vfp_differences = [i for i in range(16) if original.sregs[i] != rebuilt.sregs[i]]
    caller_gpr_differences = [i for i in range(4) if original.gpr[i] != rebuilt.gpr[i]]
    return {
        "passed": not details,
        "differences": details,
        "caller_saved_s_registers_changed": caller_vfp_differences,
        "caller_saved_gprs_changed": caller_gpr_differences,
    }


def run(code_path: Path, output: Path, seed: int, samples: int) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    output.mkdir(parents=True, exist_ok=True)
    reference = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                      ROOT / "config/functions.csv")
    reference_evidence = verify_reference(reference)
    compiled = compile_candidates(output)
    function_results, negative_results = [], []
    for address, symbol in SYMBOLS.items():
        original = VfpRunner(reference.image, address)
        candidate = VfpRunner(reference.image, address, compiled[symbol])
        count, failure = 0, None
        caller_saved_differences = 0
        for case in make_cases(address, seed, samples):
            old, new = original.run(case), candidate.run(case)
            result = compare(old, new, case)
            count += 1
            caller_saved_differences += bool(result["caller_saved_s_registers_changed"]
                                             or result["caller_saved_gprs_changed"])
            if not result["passed"]:
                failure = {"case": case.label, **result}
                break
        function_results.append({
            "address": hex(address), "candidate": symbol,
            "candidate_bytes": len(compiled[symbol]), "cases": count,
            "passed": failure is None, "failure": failure,
            "caller_saved_state_diff_cases": caller_saved_differences,
        })
        control_case = next(make_cases(address, seed, 0))
        for kind in ("wrong_lanes", "wrong_operation"):
            wrong_symbol = f"{kind}_{address:08x}"
            wrong = VfpRunner(reference.image, address, compiled[wrong_symbol])
            result = compare(original.run(control_case), wrong.run(control_case), control_case)
            negative_results.append({"address": hex(address), "control": wrong_symbol,
                                     "detected": not result["passed"],
                                     "differences": result["differences"]})

    report = {
        "experiment": "vfp_lane_add_pair",
        "seed": seed,
        "random_samples_per_function": samples,
        "pinned_fpscr": f"0x{FPSCR_PINNED:08x}",
        "fp_mode": "round-to-nearest, gradual underflow, default-NaN disabled, traps masked, cumulative flags clear at entry",
        "reference": reference_evidence,
        "functions": function_results,
        "negative_controls": negative_results,
        "passed": all(row["passed"] for row in function_results)
                  and all(row["detected"] for row in negative_results),
        "limitations": [
            "Caller-saved s0-s15 and r0-r3 are diagnostic only under AAPCS; the experiment does not claim any caller consumes their contents across the call.",
            "Only addresses within mapped ordinary DATA RAM are tested; unmapped-page fault ordering is not claimed.",
            "No callers were manually inspected or executed, so caller behavior is not claimed.",
            "This is bounded isolated ARM execution evidence, not production integration or whole-game equivalence.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "functions": function_results,
                      "negative_controls": negative_results}, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.code, args.output, args.seed, args.samples)


if __name__ == "__main__":
    main()
