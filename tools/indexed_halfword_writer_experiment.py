#!/usr/bin/env python3
"""Differentially test two indexed-halfword writer leaves against pinned ARM bytes."""
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
from tools.semantic_experiment import DATA, DATA_SIZE, INJECT, SP, STACK, TEXT, Case, Runner, difference
from tools.semantic_experiment_support import compile_candidate_symbols, load_pinned_reference

FUNCTIONS = {
    0x0035BBC4: {"symbol": "candidate_0035bbc4"},
    0x0035C00C: {"symbol": "candidate_0035c00c"},
}
CALLER = {
    "callee": 0x0035BBC4, "parent": 0x0035B364, "site": 0x0035B56C,
    "stop_success": 0x0035B578, "stop_failure": 0x0035B55C,
}
WORDS = (0xE5913000, 0xE3A02000, 0xE5C32008, 0xE1C020DC, 0xE5911000,
         0xE0822083, 0xE1D220B0, 0xE1C120BA, 0xE5901010, 0xE2811001,
         0xE5801010, 0xE3A00000, 0xE12FFF1E)
EXPECTED_INSTRUCTIONS = (
    ("ldr", "r3, [r1]"), ("mov", "r2, #0"), ("strb", "r2, [r3, #8]"),
    ("ldrd", "r2, r3, [r0, #0xc]"), ("ldr", "r1, [r1]"),
    ("add", "r2, r2, r3, lsl #1"), ("ldrh", "r2, [r2]"),
    ("strh", "r2, [r1, #0xa]"), ("ldr", "r1, [r0, #0x10]"),
    ("add", "r1, r1, #1"), ("str", "r1, [r0, #0x10]"),
    ("mov", "r0, #0"), ("bx", "lr"),
)
EXPECTED_CANDIDATE_INSTRUCTIONS = (
    ("ldr", "r2, [r1]"), ("mov", "r3, #0"), ("strb", "r3, [r2, #8]"),
    *EXPECTED_INSTRUCTIONS[3:],
)
U32_MASK = 0xFFFFFFFF


def _decode(image: bytes, address: int, size: int):
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    start = address - TEXT
    rows = list(decoder.disasm(image[start:start + size], address))
    return tuple((row.mnemonic.lower(), row.op_str.lower()) for row in rows), sum(
        row.size for row in rows
    )


def _direct_arm_bl_callers(image: bytes) -> dict[int, tuple[int, ...]]:
    result = {address: [] for address in FUNCTIONS}
    for index in range(len(image) // 4):
        word = struct.unpack_from("<I", image, index * 4)[0]
        if word & 0x0F000000 != 0x0B000000 or word >> 28 == 0xF:
            continue
        displacement = (word & 0xFFFFFF) << 2
        if displacement & (1 << 25):
            displacement -= 1 << 26
        site = TEXT + index * 4
        target = (site + 8 + displacement) & U32_MASK
        if target in result:
            result[target].append(site)
    return {address: tuple(sites) for address, sites in result.items()}


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if len(image) != int(game_info["code_bin_size"]) or digest != game_info["code_sha256"]:
        raise ValueError("code.bin size/SHA-256 does not match configured revision")
    by_address = {int(row["address"], 16): row for row in ledger}
    functions = {}
    for address in FUNCTIONS:
        row = by_address.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 52:
            raise ValueError(f"Missing matching 52-byte ledger row at {address:#010x}")
        actual, size = _decode(image, address, 52)
        words = struct.unpack_from("<13I", image, address - TEXT)
        if actual != EXPECTED_INSTRUCTIONS or words != WORDS or size != 52:
            raise ValueError(f"Pinned instruction sequence changed at {address:#010x}")
        functions[hex(address)] = {
            "ledger_name": row["name"], "size": size,
            "function_sha256": hashlib.sha256(
                image[address - TEXT:address - TEXT + size]).hexdigest(),
            "words": [f"0x{word:08x}" for word in words],
            "instructions": [f"{mnemonic} {operands}" for mnemonic, operands in actual],
            "register_mapping": {
                "r0": "record/object; +0xc is source base and +0x10 is current index/cursor",
                "r1": "address of a pointer slot; dereferenced before and after the first byte store",
                "r2": "zero for the first byte clear, then source address and loaded halfword",
                "r3": "first target pointer, then index loaded with r2 by LDRD",
            },
            "ordered_effects": [
                "load *r1; clear one byte at first_target+8",
                "LDRD two adjacent words from record+0xc (base in r2, index in r3)",
                "reload *r1; read halfword at base + (index << 1)",
                "store that halfword at reloaded_target+0xa",
                "reload record+0x10, add one modulo 2^32, store record+0x10",
                "return zero",
            ],
        }
    callers = _direct_arm_bl_callers(image)
    if callers[CALLER["callee"]] != (CALLER["site"],) or callers[0x0035C00C] != ():
        raise ValueError(f"Direct ARM BL caller set changed: {callers}")
    parent = by_address.get(CALLER["parent"])
    if parent is None or parent["status"].strip() != "matching" or int(parent["size"]) != 616:
        raise ValueError("Direct caller parent ledger entry changed")
    pinned_caller = {
        "parent": parent["name"], "parent_address": hex(CALLER["parent"]),
        "parent_size": 616, "callsite": hex(CALLER["site"]),
        "callee": hex(CALLER["callee"]),
        "instructions": {},
        "context": (
            "At 0x0035B508-0x0035B510 the parent sets r0=r4 and r1=sp before parsing; "
            "at 0x0035B524, an unsigned range check can branch to 0x0035B568, then BL at "
            "0x0035B56C. The harness starts at the BL with r0=record and [sp]=target pointer; "
            "the earlier control-flow path is statically pinned, not executed."),
        "consumption": "cmp r0,#0 at 0x0035B570; bne to failure at 0x0035B55C, otherwise success at 0x0035B578",
    }
    for site, size, expected in (
        (0x0035B508, 4, (("mov", "r0, r4"),)),
        (0x0035B50C, 4, (("mov", "r1, sp"),)),
        (0x0035B524, 4, (("bhi", "#0x35b568"),)),
        (0x0035B56C, 12, (("bl", "#0x35bbc4"), ("cmp", "r0, #0"), ("bne", "#0x35b55c"))),
    ):
        actual, actual_size = _decode(image, site, size)
        if actual != expected or actual_size != size:
            raise ValueError(f"Direct caller context changed at {site:#010x}: {actual}")
        pinned_caller["instructions"][hex(site)] = [f"{m} {op}" for m, op in actual]
    return {
        "code_sha256": digest, "functions": functions,
        "direct_arm_bl_callers": {hex(address): [hex(site) for site in sites]
                                   for address, sites in callers.items()},
        "direct_caller_context": pinned_caller,
        "caller_search_scope": (
            "Full code.bin word-aligned scan for unconditional ARM BL encodings; "
            "not a control-flow-aware xref database. Thumb BL and indirect calls are not covered."),
    }


def _put_u32(data: bytearray, address: int, value: int):
    struct.pack_into("<I", data, address - DATA, value & U32_MASK)


def _put_u16(data: bytearray, address: int, value: int):
    struct.pack_into("<H", data, address - DATA, value & 0xFFFF)


def make_cases(address: int, seed: int, samples: int = 64):
    rng = random.Random(seed ^ address)
    # Boundary indices are still kept within the mapped data fixture.
    indices = (0, 1, 2, 0x7F, 0x80, 0x1FF, 0x3FF, 0x400)
    for index, cursor in enumerate(indices):
        data = bytearray(rng.randbytes(DATA_SIZE))
        record, slot, target, base = DATA + 0x200, DATA + 0x80, DATA + 0x300, DATA + 0x600
        _put_u32(data, slot, target)
        _put_u32(data, record + 0x0C, base)
        _put_u32(data, record + 0x10, cursor)
        source = base + cursor * 2
        value = ((index * 0x1F31) ^ 0xA55A) & 0xFFFF
        _put_u16(data, source, value)
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0], regs[1] = record, slot
        yield Case(f"boundary-cursor-{cursor:08x}", tuple(regs), bytes(data),
                   rng.randbytes(0x2000), rng.getrandbits(4) << 28)

    for index in range(samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        record, slot, target = DATA + 0x200, DATA + 0x80, DATA + 0x300
        base = DATA + 0x500 + rng.randrange(0x80) * 4
        cursor = rng.randrange(0x200)
        _put_u32(data, slot, target)
        _put_u32(data, record + 0x0C, base)
        _put_u32(data, record + 0x10, cursor)
        _put_u16(data, base + cursor * 2, rng.getrandbits(16))
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0], regs[1] = record, slot
        yield Case(f"random-{index}", tuple(regs), bytes(data), rng.randbytes(0x2000),
                   rng.getrandbits(4) << 28)


def make_alias_cases(seed: int):
    rng = random.Random(seed ^ 0xA11A5)
    record, slot = DATA + 0x200, DATA + 0x80
    cases = []

    # Initial clear aliases and changes the low byte of the slot's pointer;
    # the second LDR [r1] must observe the changed pointer.
    data = bytearray(rng.randbytes(DATA_SIZE))
    _put_u32(data, slot, slot - 8)
    _put_u32(data, record + 0x0C, DATA + 0x600)
    _put_u32(data, record + 0x10, 3)
    _put_u16(data, DATA + 0x606, 0xBEEF)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0], regs[1] = record, slot
    cases.append(Case("alias-clear-mutates-pointer-slot", tuple(regs), bytes(data),
                      rng.randbytes(0x2000), 0))

    # The initial byte clear aliases the loaded base word; the LDRD follows it.
    data = bytearray(rng.randbytes(DATA_SIZE))
    target = record + 4
    base = DATA + 0x65A
    _put_u32(data, slot, target)
    _put_u32(data, record + 0x0C, base)
    _put_u32(data, record + 0x10, 2)
    _put_u16(data, DATA + 0x604, 0xCAFE)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0], regs[1] = record, slot
    cases.append(Case("alias-clear-mutates-base-before-ldrd", tuple(regs), bytes(data),
                      rng.randbytes(0x2000), 0))

    # Halfword output overwrites record+0x10; original then reloads and adds 1.
    data = bytearray(rng.randbytes(DATA_SIZE))
    target = record + 6
    _put_u32(data, slot, target)
    _put_u32(data, record + 0x0C, DATA + 0x600)
    _put_u32(data, record + 0x10, 4)
    _put_u16(data, DATA + 0x608, 0x1234)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0], regs[1] = record, slot
    cases.append(Case("alias-halfword-overwrites-index-before-increment", tuple(regs),
                      bytes(data), rng.randbytes(0x2000), 0))
    return cases


def _trace_run(image: bytes, address: int, case: Case, replacement: bytes | None = None):
    runner = Runner(image, address, replacement)
    events = []

    def record(_uc, access, mem_address, size, _value, _user):
        if access in (unicorn.UC_MEM_READ, unicorn.UC_MEM_WRITE):
            if DATA <= mem_address < DATA + DATA_SIZE:
                events.append(("read" if access == unicorn.UC_MEM_READ else "write",
                               mem_address, size))

    runner.uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE, record)
    result = runner.run(case)
    return result, tuple(events)


def _caller_case(seed: int) -> Case:
    case = next(make_cases(CALLER["callee"], seed, 0))
    registers, stack = list(case.registers), bytearray(case.stack)
    registers[1] = SP
    target = struct.unpack_from("<I", case.data, 0x80)[0]
    struct.pack_into("<I", stack, SP - STACK, target)
    return Case(f"direct-parent-call-seed-{seed}", tuple(registers), case.data, bytes(stack), 0)


def _same_execution(a, b, address: int, replacement: bool) -> str | None:
    if bool(a.fault) != bool(b.fault):
        return f"fault mismatch: original={a.fault!r}, candidate={b.fault!r}"
    if a.stopped != b.stopped:
        return "stop/return state differs"
    actual_start = INJECT if replacement else address
    # `a` is always original and `b` candidate. Normalize fault PCs to their
    # respective function starts; ordinary return PCs are both the same sentinel.
    a_pc = a.pc - address if a.fault else a.pc
    b_pc = b.pc - actual_start if b.fault else b.pc
    if a_pc != b_pc:
        return f"execution point differs: {a_pc:#x} vs {b_pc:#x}"
    if a.result != b.result:
        return "r0 return differs"
    if a.preserved != b.preserved:
        return "callee-saved registers/SP differ"
    if a.data != b.data or a.live_stack != b.live_stack:
        return "visible memory differs"
    if a.reads != b.reads or a.writes != b.writes:
        return "memory footprint differs"
    return None


def _compare(original, candidate, address, candidate_code):
    old, old_events = original
    new, new_events = candidate
    reason = _same_execution(old, new, address, True)
    if reason:
        return reason
    if old_events != new_events:
        return f"ordered access width/trace differs: {old_events} != {new_events}"
    return None


def run(code_path: Path, output: Path, seed: int, samples: int = 64) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "experiments/semantic_equivalence/indexed_halfword_writer_candidates.cpp"
    compiled = compile_candidate_symbols(source, output / "indexed_halfword_writer_candidates.o",
                                         ROOT, [v["symbol"] for v in FUNCTIONS.values()])
    disasm = {}
    for address, spec in FUNCTIONS.items():
        code = compiled[spec["symbol"]]
        decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
        decoded = list(decoder.disasm(code, 0))
        actual = tuple((row.mnemonic.lower(), row.op_str.lower()) for row in decoded)
        size = sum(row.size for row in decoded)
        if actual != EXPECTED_CANDIDATE_INSTRUCTIONS or size != 52:
            raise ValueError(f"Candidate instruction shape differs at {address:#010x}: {actual}")
        disasm[hex(address)] = {"candidate_bytes": code.hex(), "candidate_size": len(code),
                                "instruction_sequence_matches": True}

    function_results, negatives, fault_results, caller_results = [], [], [], []
    for address, spec in FUNCTIONS.items():
        original = compiled[spec["symbol"]]
        candidates = [*make_cases(address, seed, samples), *make_alias_cases(seed)]
        representative_case = candidates[0]
        comparisons, failure = 0, None
        for case in candidates:
            old = _trace_run(pinned.image, address, case)
            new = _trace_run(pinned.image, address, case, original)
            comparisons += 1
            reason = _compare(old, new, address, original)
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        old_trace = _trace_run(pinned.image, address, representative_case)
        new_trace = _trace_run(pinned.image, address, representative_case, original)
        if old_trace[1] != new_trace[1]:
            failure = {"case": representative_case.label,
                       "reason": "representative ordered access trace differs"}
        access_trace = [
            {"operation": operation, "data_offset": hex(mem_address - DATA), "width_bytes": width}
            for operation, mem_address, width in old_trace[1]
        ]
        function_results.append({"address": hex(address), "candidate": spec["symbol"],
                                 "candidate_bytes": len(original), "cases": comparisons,
                                 "ordered_access_trace": access_trace,
                                 "ordered_trace_matches_candidate": old_trace[1] == new_trace[1],
                                 "passed": failure is None, "failure": failure})

        # Target source index is wrong-stride-sensitive; output marker catches
        # accidental byte store; the alias input catches reordered increment.
        # Cursor=1 ensures the wrong-stride control reads a distinct marked cell.
        control_case = next(item for item in make_cases(address, seed, 0)
                            if item.label == "boundary-cursor-00000001")
        alias_case = make_alias_cases(seed)[2]
        for control in ("negative_wrong_stride", "negative_byte_store",
                        "negative_increment_before_store"):
            control_code = compiled[control]
            case = alias_case if control == "negative_increment_before_store" else control_case
            old = _trace_run(pinned.image, address, case)
            wrong = _trace_run(pinned.image, address, case, control_code)
            reason = _compare(old, wrong, address, control_code)
            negatives.append({"address": hex(address), "control": control,
                              "detected": reason is not None, "difference": reason})

    # Partial-effect fault probes: bad slot faults at the first load with no
    # writes; a source crossing the mapped DATA boundary faults after the clear.
    for address, spec in FUNCTIONS.items():
        record, slot, target = DATA + 0x200, DATA + 0x80, DATA + 0x300
        base_case = next(make_cases(address, seed, 0))
        cases = []
        regs = list(base_case.registers)
        regs[1] = DATA + DATA_SIZE + 0x80
        cases.append(Case("fault-invalid-pointer-slot", tuple(regs), base_case.data,
                          base_case.stack, 0))
        data = bytearray(base_case.data)
        _put_u32(data, slot, target)
        _put_u32(data, record + 0x0C, DATA + DATA_SIZE - 1)
        _put_u32(data, record + 0x10, 0)
        regs = list(base_case.registers)
        regs[0], regs[1] = record, slot
        cases.append(Case("fault-source-halfword-crosses-data-map", tuple(regs), bytes(data),
                          base_case.stack, 0))
        code = compiled[spec["symbol"]]
        for case in cases:
            old = _trace_run(pinned.image, address, case)
            new = _trace_run(pinned.image, address, case, code)
            reason = _compare(old, new, address, code)
            fault_results.append({"address": hex(address), "case": case.label,
                                  "original_fault": old[0].fault,
                                  "candidate_fault": new[0].fault,
                                  "writes_before_fault": len(old[0].writes),
                                  "passed": reason is None, "difference": reason})

        if address == CALLER["callee"]:
            case = _caller_case(seed)
            old_runner = Runner(pinned.image, address)
            new_runner = Runner(pinned.image, address, code)
            old = old_runner.run(case, start=CALLER["site"],
                                 stops=(CALLER["stop_success"], CALLER["stop_failure"]),
                                 budget=32)
            new = new_runner.run(case, start=CALLER["site"],
                                 stops=(CALLER["stop_success"], CALLER["stop_failure"]),
                                 budget=32)
            caller_reason = difference(old, new, returns_value=False, caller_window=True,
                                       compare_flags=True)
            caller_results.append({
                "parent": hex(CALLER["parent"]), "callsite": hex(CALLER["site"]),
                "passed": caller_reason is None, "difference": caller_reason,
                "original_continuation": hex(old.pc), "candidate_continuation": hex(new.pc),
                "cases": 1,
                "scope": "Starts at the pinned BL with synthetic r0 and [sp] values; parent setup path is pinned, not executed.",
            })

    report = {
        "schema": 1, "experiment": "indexed_halfword_writer_pair",
        "passed": all(row["passed"] for row in function_results + fault_results + caller_results)
                  and all(row["detected"] for row in negatives),
        "seed": seed, "random_samples_per_function": samples,
        "reference": reference, "candidate_disassembly": disasm,
        "functions": function_results, "negative_controls": negatives,
        "fault_probes": fault_results, "caller_results": caller_results,
        "limitations": [
            "ARM direct-BL scan found no callers; this is not a proof of no callers. Thumb BL and indirect calls were not scanned.",
            "Differential cases use Unicorn ARM11 MPCore, mapped ordinary RAM, aligned record/target objects, and selected alias/fault probes; they are not gameplay traces or formal equivalence.",
            "The C++ reconstruction uses volatile typed accesses over simulator memory. Object-lifetime and arbitrary unaligned-pointer behavior are outside the tested C++ abstract-machine contract.",
            "In particular, the volatile uint64_t view at record+0xc relies on this ARM compiler's 4-byte-aligned LDRD lowering; portable C++ does not guarantee uint64_t alignment/lifetime for that address.",
            "LDRD was retained by the compiler in the candidate. Tests compare exact ordered data access widths when Unicorn reports them, visible RAM, register preservation, return value and fault point.",
            "No caller windows were claimed or executed; no Thumb/indirect xrefs, MMIO/concurrency, exception-handler behavior, or whole-game run was established.",
            "Candidates remain isolated and do not change production sources or exact-match ledger status.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/indexed-halfword-writer")
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=64)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "functions": report["functions"],
                      "negative_controls": report["negative_controls"],
                      "fault_probes": report["fault_probes"]}, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
