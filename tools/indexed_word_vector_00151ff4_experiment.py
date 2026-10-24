#!/usr/bin/env python3
"""Differentially test an isolated 4-lane indexed-word writer reconstruction."""
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
import unicorn
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import (
    DATA, DATA_SIZE, INJECT, RETURN, SP, STACK, TEXT, Case, Runner,
    validate_local_blob,
)
from tools.semantic_experiment_support import load_pinned_reference

ADDRESS = 0x00151FF4
SIZE = 96
CALLER = {"parent": 0x0014D448, "callsite": 0x0014D4B4,
          "argument_setup": 0x0014D4AC, "continuation": 0x0014D4B8,
          "epilogue": 0x0014D4BC}
SYMBOLS = ("candidate_00151ff4", "negative_cached_count_00151ff4",
           "negative_inclusive_count_00151ff4")
EXPECTED_WORDS = (
    0xE5902004, 0xE0800002, 0xE3E02000, 0xE5903000, 0xE3530000,
    0x15903004, 0x05812000, 0x15813000, 0xE5903000, 0xE3530001,
    0x85903008, 0x95812004, 0x85813004, 0xE5903000, 0xE3530002,
    0x8590300C, 0x95812008, 0x85813008, 0xE5903000, 0xE3530003,
    0x85900010, 0x9581200C, 0x8581000C, 0xE12FFF1E,
)
U32_MASK = 0xFFFFFFFF


def _direct_arm_bl_callers(image: bytes) -> list[int]:
    callers = []
    for index in range(len(image) // 4):
        word = struct.unpack_from("<I", image, index * 4)[0]
        if word & 0x0F000000 != 0x0B000000 or word >> 28 == 0xF:
            continue
        displacement = (word & 0xFFFFFF) << 2
        if displacement & (1 << 25):
            displacement -= 1 << 26
        site = TEXT + index * 4
        if ((site + 8 + displacement) & U32_MASK) == ADDRESS:
            callers.append(site)
    return callers


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if len(image) != int(game_info["code_bin_size"]) or digest != game_info["code_sha256"]:
        raise ValueError("code.bin size/SHA-256 does not match configured revision")
    row = next((item for item in ledger if int(item["address"], 16) == ADDRESS), None)
    if row is None or row["status"].strip() != "matching" or int(row["size"]) != SIZE:
        raise ValueError("Pinned ledger must identify a matching 96-byte function")
    words = struct.unpack_from(f"<{SIZE // 4}I", image, ADDRESS - TEXT)
    if words != EXPECTED_WORDS:
        raise ValueError("Pinned instruction sequence changed")
    caller_call = struct.unpack_from("<I", image, CALLER["callsite"] - TEXT)[0]
    after_call = struct.unpack_from("<2I", image, CALLER["continuation"] - TEXT)
    before_call = struct.unpack_from("<2I", image, CALLER["argument_setup"] - TEXT)
    callers = _direct_arm_bl_callers(image)
    if callers != [CALLER["callsite"]] or caller_call != 0xEB0012CE:
        raise ValueError("Pinned direct caller BL inventory changed")
    if before_call != (0xE2841004, 0xE1A00005):
        raise ValueError("Pinned caller argument setup changed")
    if after_call != (0xE3A00001, 0xE8BD8070):
        raise ValueError("Pinned caller continuation/epilogue changed")
    return {
        "code_sha256": digest, "function_address": hex(ADDRESS),
        "function_size": SIZE, "instruction_words": [hex(x) for x in words],
        "direct_arm_bl_callers": [hex(x) for x in callers],
        "caller_callsite_word": hex(caller_call),
        "caller_argument_setup_words": [hex(x) for x in before_call],
        "caller_continuation_words": [hex(x) for x in after_call],
        "caller_scope": "The bounded scan covers ARM BL words only; Thumb BL and indirect calls remain unsearched.",
        "effects": [
            "load descriptor offset from [r0+4], then set base=r0+offset",
            "for lanes 0..3, reload unsigned active_count from [base]",
            "store [base+4*(lane+1)] when active_count>lane, else 0xffffffff, to [r1+4*lane]",
            "return the last source word when lane 3 is active, otherwise the base address in r0",
            "the sole direct ARM BL caller at 0x14d4b4 ignores r0 and immediately sets r0=1 before epilogue",
        ],
    }


def _case(seed: int, label: str, count: int, out_delta: int = 0x200) -> Case:
    rng = random.Random(seed ^ (count & U32_MASK) ^ out_delta)
    data = bytearray(rng.randbytes(DATA_SIZE))
    descriptor, base = DATA + 0x100, DATA + 0x180
    destination = base + out_delta
    struct.pack_into("<I", data, descriptor - DATA + 4, base - descriptor)
    struct.pack_into("<I", data, base - DATA, count & U32_MASK)
    for lane in range(1, 5):
        struct.pack_into("<I", data, base - DATA + lane * 4, rng.getrandbits(32))
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0], regs[1] = descriptor, destination
    return Case(label, tuple(regs), bytes(data), rng.randbytes(0x2000), rng.getrandbits(4) << 28)


def make_cases(seed: int, samples: int):
    rng = random.Random(seed ^ 0x151FF4)
    counts = [0, 1, 2, 3, 4, 5, 0x7FFFFFFF, 0x80000000, U32_MASK]
    counts.extend(rng.getrandbits(32) for _ in range(samples))
    cases = [_case(seed, f"count-{count:08x}", count) for count in counts]

    # Output overlaps the source count: each destination write changes the
    # count re-read by later lanes. A one-time count snapshot is observably wrong.
    cases.append(_case(seed, "alias-output-overwrites-live-count", 3, out_delta=0))
    # The output lane 1 aliases the live count, after lane 1 has already loaded it.
    cases.append(_case(seed, "alias-lane1-overwrites-live-count", 3, out_delta=-4))
    # Destination lane zero overwrites descriptor+4 after the offset was read.
    alias = _case(seed, "alias-destination-overwrites-offset", 2, out_delta=-0x7C)
    regs, data = list(alias.registers), bytearray(alias.data)
    regs[1] = DATA + 0x104
    cases.append(Case(alias.label, tuple(regs), bytes(data), alias.stack, alias.nzcv))
    return cases


def _trace_run(image: bytes, case: Case, replacement: bytes | None = None):
    runner = Runner(image, ADDRESS, replacement,
                    replacement_validator=validate_local_blob)
    events = []

    def record(_uc, access, mem_address, size, _value, _user):
        if access in (unicorn.UC_MEM_READ, unicorn.UC_MEM_WRITE) and DATA <= mem_address < DATA + DATA_SIZE:
            events.append(("read" if access == unicorn.UC_MEM_READ else "write", mem_address, size))

    runner.uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE, record)
    return runner.run(case), tuple(events)


def _compare(original, candidate, address: int, candidate_start: int = INJECT):
    old, old_events = original
    new, new_events = candidate
    if bool(old.fault) != bool(new.fault):
        return f"fault mismatch: original={old.fault!r}, candidate={new.fault!r}"
    if old.stopped != new.stopped:
        return "stop/return state differs"
    if not old.fault:
        old_pc = old.pc
        new_pc = new.pc
        if old_pc != new_pc:
            return f"return point differs: {old_pc:#x} vs {new_pc:#x}"
    if old.result != new.result:
        return f"r0 differs: {old.result:#x} vs {new.result:#x}"
    if old.preserved != new.preserved:
        return "callee-saved registers/SP differ"
    if old.data != new.data or old.live_stack != new.live_stack:
        return "visible memory differs"
    if old.reads != new.reads or old.writes != new.writes:
        return "memory footprint differs"
    if old_events != new_events:
        return f"ordered access width/trace differs: {old_events} != {new_events}"
    return None


def _caller_case(seed: int) -> Case:
    case = _case(seed, "caller-bl-0x14d4a8", 2)
    regs, stack = list(case.registers), bytearray(case.stack)
    regs[1] = DATA + 0x304  # Parent executes ADD r1,r4,#4 before the call.
    struct.pack_into("<4I", stack, SP - STACK, 0xA4A4A4A4, 0xB5B5B5B5,
                     0xC6C6C6C6, RETURN + 4)
    return Case(case.label, tuple(regs), case.data, bytes(stack), case.nzcv)


def run(code_path: Path, output: Path, seed: int, samples: int = 64) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "experiments/semantic_equivalence/indexed_word_vector_00151ff4.cpp"
    object_path = output / "indexed_word_vector_00151ff4.o"
    build = compile_tu_armv6k(source, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    compiled = {}
    for symbol, (code, relocations) in extract_elf_functions_detailed(object_path).items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        validate_local_blob(code)
        compiled[symbol] = code
    if set(SYMBOLS) - compiled.keys():
        raise ValueError(f"Missing candidate symbols: {sorted(set(SYMBOLS) - compiled.keys())}")
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    candidate = compiled[SYMBOLS[0]]
    validate_local_blob(candidate)
    if candidate == pinned.image[ADDRESS - TEXT:ADDRESS - TEXT + SIZE]:
        raise ValueError("Candidate unexpectedly byte-matches the original; keep this semantic experiment separate")

    results, traces = [], []
    for case in make_cases(seed, samples):
        old = _trace_run(pinned.image, case)
        new = _trace_run(pinned.image, case, candidate)
        reason = _compare(old, new, ADDRESS)
        results.append({"case": case.label, "passed": reason is None, "difference": reason})
        if case.label == "count-00000003":
            traces = [{"operation": op, "data_offset": hex(addr - DATA), "width_bytes": width}
                      for op, addr, width in old[1]]

    negative_results = []
    control_cases = [next(c for c in make_cases(seed, 0)
                          if c.label == "alias-output-overwrites-live-count"),
                     next(c for c in make_cases(seed, 0) if c.label == "count-00000002")]
    for symbol, case in zip(SYMBOLS[1:], control_cases):
        old = _trace_run(pinned.image, case)
        wrong = _trace_run(pinned.image, case, compiled[symbol])
        reason = _compare(old, wrong, ADDRESS)
        negative_results.append({"control": symbol, "case": case.label,
                                 "detected": reason is not None, "difference": reason})

    # Invalid destination: first lane write is valid; second lane crosses mapped RAM.
    fault_case = _case(seed, "fault-destination-crosses-map", 4)
    fault_regs = list(fault_case.registers)
    fault_regs[1] = DATA + DATA_SIZE - 4
    fault_case = Case(fault_case.label, tuple(fault_regs), fault_case.data,
                      fault_case.stack, fault_case.nzcv)
    fault_old = _trace_run(pinned.image, fault_case)
    fault_new = _trace_run(pinned.image, fault_case, candidate)
    fault_reason = _compare(fault_old, fault_new, ADDRESS)

    # Direct parent window, starting at the pinned BL and running through POP PC.
    caller_case = _caller_case(seed)
    old_runner = Runner(pinned.image, ADDRESS)
    new_runner = Runner(pinned.image, ADDRESS, candidate,
                        replacement_validator=validate_local_blob)
    old = old_runner.run(caller_case, start=CALLER["callsite"],
                         stops=(RETURN + 4,), budget=40)
    new = new_runner.run(caller_case, start=CALLER["callsite"],
                         stops=(RETURN + 4,), budget=40)
    caller_reason = None
    if old.fault or new.fault or not old.stopped or not new.stopped:
        caller_reason = f"caller window did not complete: original={old.fault}, candidate={new.fault}"
    elif (old.result != new.result or old.pc != new.pc or old.preserved != new.preserved
          or old.data != new.data or old.live_stack != new.live_stack
          or old.reads != new.reads or old.writes != new.writes):
        caller_reason = "caller-observable register, memory, or continuation state differs"

    report = {
        "schema": 1, "experiment": "indexed_word_vector_00151ff4",
        "passed": all(item["passed"] for item in results)
                  and all(item["detected"] for item in negative_results)
                  and fault_reason is None and caller_reason is None,
        "seed": seed, "random_samples": samples, "reference": reference,
        "candidate": {"symbol": SYMBOLS[0], "bytes": len(candidate),
                      "disassembly": [(i.mnemonic, i.op_str) for i in cs.disasm(candidate, INJECT)],
                      "same_bytes_as_original": False},
        "cases": results, "ordered_trace_count_3": traces,
        "negative_controls": negative_results,
        "fault_probe": {"case": fault_case.label, "passed": fault_reason is None,
                        "difference": fault_reason, "original_fault": fault_old[0].fault,
                        "candidate_fault": fault_new[0].fault,
                        "original_writes": len(fault_old[0].writes),
                        "candidate_writes": len(fault_new[0].writes)},
        "caller_window": {"parent": hex(CALLER["parent"]),
                          "callsite": hex(CALLER["callsite"]), "passed": caller_reason is None,
                          "difference": caller_reason,
                          "scope": "Synthetic r0/r1 and saved-register stack at the exact BL; only the callee through parent's ADD and POP are executed."},
        "limitations": [
            "Direct-caller enumeration scans ARM BL words only; Thumb BL and indirect calls are not ruled out.",
            "Caller setup/control flow before the call was not executed; the BL input state was synthetic.",
            "Differential tests cover bounded Unicorn ARM11 ordinary-RAM states, explicit alias/fault cases and seeded values; not formal equivalence, MMIO, concurrency or a whole-game trace.",
            "Volatile typed C++ accesses assume the tested 4-byte-aligned ordinary RAM objects; arbitrary C++ object lifetime and unaligned behavior are outside scope.",
            "The candidate remains isolated; no production source, exact-match ledger, game image or runtime patch is changed.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/indexed-word-vector-00151ff4")
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=64)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "reference": report["reference"],
                      "failed_cases": [item for item in report["cases"] if not item["passed"]],
                      "negative_controls": report["negative_controls"],
                      "fault_probe": report["fault_probe"],
                      "caller_window": report["caller_window"]}, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
