#!/usr/bin/env python3
"""Differential-test isolated C++ candidates for a boolean record-writer pair."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
import unicorn
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference,
    validate_local_blob,
)
from tools.semantic_experiment_support import (
    compile_candidate_symbols, load_pinned_reference,
)
from tools.build_check import find_clang

FUNCTIONS = {
    0x001AA094: {"byte_value": 1},
    0x001AA0EC: {"byte_value": 0},
}
U32_MASK = 0xFFFFFFFF


def _decode(image: bytes, address: int, size: int):
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    offset = address - TEXT
    instructions = list(cs.disasm(image[offset:offset + size], address))
    return tuple(f"{item.mnemonic.lower()} {item.op_str.lower()}".strip()
                 for item in instructions), sum(item.size for item in instructions)


def _expected_instructions(byte_value: int):
    return (
        "str r4, [sp, #-4]!", "ldr r1, [r0, #0x18]",
        "add ip, r0, #0x20", f"mov r2, #{byte_value}",
        "add r1, r1, #1", "str r1, [r0, #0x18]",
        "ldr r4, [r0, #0xbc]", "ldr r3, [r0, #0x1c]",
        "ldr r1, [r4, r1, lsl #2]", "strb r2, [r3, ip]",
        "ldr r2, [r0, #0x1c]", "add r2, r0, r2, lsl #2",
        "str r1, [r2, #0x3c]", "ldr r1, [r0, #0x1c]",
        "add r1, r1, #1", "str r1, [r0, #0x1c]",
        "ldr r1, [r0, #0x18]", "add r1, r1, #1",
        "str r1, [r0, #0x18]", "pop {r4}", "mov r0, #1", "bx lr",
    )


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 does not match pinned game revision")
    rows = {int(row["address"], 16): row for row in ledger}
    result = {}
    for address, spec in FUNCTIONS.items():
        row = rows.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 88:
            raise ValueError(f"Missing matching 88-byte ledger row at {address:#010x}")
        actual, size = _decode(image, address, 88)
        expected = _expected_instructions(spec["byte_value"])
        if actual != expected or size != 88:
            raise ValueError(f"Pinned instruction sequence changed at {address:#010x}")
        body = image[address - TEXT:address - TEXT + size]
        result[hex(address)] = {
            "size": size,
            "sha256": hashlib.sha256(body).hexdigest(),
            "instructions": list(actual),
            "observed_contract": {
                "input": "r0 points to record-like ordinary memory; no caller signature is claimed",
                "byte_write": f"byte at r0 + 0x20 + *(u32 *)(r0+0x1c) becomes {spec['byte_value']}",
                "table_read": "u32 from *(u32 *)(r0+0xbc) + 4*(old *(u32 *)(r0+0x18)+1)",
                "word_write": "table value to r0 + 0x3c + 4*old *(u32 *)(r0+0x1c)",
                "cursors": "word at +0x1c increments once; word at +0x18 increments twice, with stores between",
                "return": "r0=1",
                "registers": "r4 preserved via stack; stack restored; instructions do not set NZCV",
            },
        }
    return {"code_sha256": digest, "functions": result}


def _case(address: int, seed: int, label: str, cursor: int, index: int,
          table_address: int | None = None) -> Case:
    rng = random.Random(seed ^ address ^ sum((i + 1) * ord(c) for i, c in enumerate(label)))
    data = bytearray(rng.randbytes(DATA_SIZE))
    base = DATA + 0x100
    table = DATA + 0x500 if table_address is None else table_address
    struct.pack_into("<I", data, base - DATA + 0x18, cursor & U32_MASK)
    struct.pack_into("<I", data, base - DATA + 0x1C, index & U32_MASK)
    struct.pack_into("<I", data, base - DATA + 0xBC, table & U32_MASK)
    if DATA <= table < DATA + DATA_SIZE:
        for slot in range(256):
            offset = table - DATA + slot * 4
            if offset + 4 <= DATA_SIZE:
                struct.pack_into("<I", data, offset, rng.getrandbits(32))
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = base
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def make_cases(address: int, samples: int, seed: int):
    directed = ((0, 0, "zero-indices"), (0xFFFFFFFF, 0, "cursor-wrap"),
                (126, 127, "high-valid-indices"),
                (17, 1, "small-distinct"), (73, 239, "mixed-pattern"))
    for cursor, index, label in directed:
        # 0xffffffff + 1 wraps to table slot zero; all other indexes are bounded.
        yield _case(address, seed, label, cursor, index)
    rng = random.Random(seed ^ address)
    for n in range(samples):
        yield _case(address, seed + n, f"random-{n}", rng.randrange(0, 120),
                    rng.randrange(0, 240))


def _run_trace(runner: Runner, case: Case):
    events = []

    def memory(_uc, access, address, size, _value, _data):
        if DATA <= address < DATA + DATA_SIZE:
            events.append(("read" if access == unicorn.UC_MEM_READ else "write",
                           address, size))

    def invalid(_uc, access, address, size, _value, _data):
        events.append(("fault_read" if access == unicorn.UC_MEM_READ_UNMAPPED
                       else "fault_write", address, size))
        return False

    hook = runner.uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE,
                              memory)
    invalid_hook = runner.uc.hook_add(unicorn.UC_HOOK_MEM_INVALID, invalid)
    try:
        execution = runner.run(case)
    finally:
        runner.uc.hook_del(hook)
        runner.uc.hook_del(invalid_hook)
    return execution, tuple(events)


def _compare(original, candidate, original_trace, candidate_trace):
    reason = difference(original, candidate, returns_value=True, compare_flags=True)
    if original_trace != candidate_trace:
        reason = "ordered ordinary-RAM access trace differs"
    return reason


def _fault_case(image: bytes, compiled: dict[str, bytes], address: int,
                seed: int, label: str, cursor: int, index: int,
                table_address: int | None = None):
    case = _case(address, seed, label, cursor, index, table_address)
    original, original_events = _run_trace(Runner(image, address), case)
    candidate, candidate_events = _run_trace(
        Runner(image, address, compiled[f"candidate_{address:08x}"],
               replacement_validator=validate_local_blob), case)
    base = case.registers[0]
    cursor_before = struct.unpack_from("<I", case.data, base - DATA + 0x18)[0]
    first_byte_address = base + 0x20 + index
    return {
        "label": label,
        "both_faulted": bool(original.fault and candidate.fault),
        "same_faulting_access": original_events[-1:] == candidate_events[-1:],
        "same_ordered_accesses": original_events == candidate_events,
        "same_partial_data": original.data == candidate.data,
        "same_write_footprint": original.writes == candidate.writes,
        "events": [[kind, hex(addr), size] for kind, addr, size in original_events],
        "cursor_first_increment_committed": (
            struct.unpack_from("<I", original.data, base - DATA + 0x18)[0]
            == (cursor_before + 1) & U32_MASK
            and struct.unpack_from("<I", candidate.data, base - DATA + 0x18)[0]
            == (cursor_before + 1) & U32_MASK),
        "byte_store_committed_before_word_fault": (
            original.data[first_byte_address - DATA] == FUNCTIONS[address]["byte_value"]
            and candidate.data[first_byte_address - DATA] == FUNCTIONS[address]["byte_value"])
        if label == "word-destination-fault" else None,
    }


def run(code_path: Path, output: Path, samples: int = 128,
        seed: int = 20261024) -> dict:
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    image, game, ledger = pinned.image, pinned.game_info, pinned.ledger
    reference = verify_reference(image, game, ledger)
    output.mkdir(parents=True, exist_ok=True)
    source_path = ROOT / "experiments/semantic_equivalence/boolean_record_writer_candidates.cpp"
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    names = {f"candidate_{address:08x}" for address in FUNCTIONS}
    names |= {"negative_wrong_boolean_value", "negative_missing_final_cursor_bump"}
    compiled = compile_candidate_symbols(source_path,
        output / "boolean_record_writer_candidates.o", ROOT, names)

    functions = []
    for address in FUNCTIONS:
        symbol = f"candidate_{address:08x}"
        original_runner = Runner(image, address)
        candidate_runner = Runner(image, address, compiled[symbol],
                                  replacement_validator=validate_local_blob)
        traces, failure, count = {}, None, 0
        for case in make_cases(address, samples, seed):
            original, trace_a = _run_trace(original_runner, case)
            rebuilt, trace_b = _run_trace(candidate_runner, case)
            reason = _compare(original, rebuilt, trace_a, trace_b)
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason,
                           "original_fault": original.fault,
                           "candidate_fault": rebuilt.fault,
                           "original_nzcv": hex(original.nzcv),
                           "candidate_nzcv": hex(rebuilt.nzcv)}
                break
            if case.label in ("zero-indices", "small-distinct"):
                traces[case.label] = [[kind, hex(addr), size]
                                      for kind, addr, size in trace_a]
        functions.append({"address": hex(address), "candidate_bytes": len(compiled[symbol]),
                          "comparisons": count, "passed": failure is None,
                          "ordered_access_traces": traces, "failure": failure})

    controls = []
    control_case = _case(0x001AA0EC, seed, "negative-controls", 7, 11)
    original, original_trace = _run_trace(Runner(image, 0x001AA0EC), control_case)
    for name in ("negative_wrong_boolean_value", "negative_missing_final_cursor_bump"):
        bad, bad_trace = _run_trace(Runner(image, 0x001AA0EC, compiled[name],
            replacement_validator=validate_local_blob), control_case)
        controls.append({"name": name, "detected": _compare(
            original, bad, original_trace, bad_trace) is not None})

    base = DATA + 0x100
    word_fault_index = (DATA_SIZE - 0x100 - 0x3C) // 4
    faults = []
    for address in FUNCTIONS:
        faults.extend((
            _fault_case(image, compiled, address, seed, "table-read-fault", 0, 0,
                        DATA + DATA_SIZE - 4),
            _fault_case(image, compiled, address, seed, "byte-destination-fault", 3,
                        DATA_SIZE - 0x100 - 0x20),
            _fault_case(image, compiled, address, seed, "word-destination-fault", 3,
                        word_fault_index),
        ))

    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True)
    report = {
        "schema": 1,
        "experiment": "boolean_record_writers_group41",
        "passed": (all(row["passed"] for row in functions)
                   and all(row["detected"] for row in controls)
                   and all(row["both_faulted"] and row["same_faulting_access"]
                           and row["same_ordered_accesses"] and row["same_partial_data"]
                           and row["same_write_footprint"]
                           and row["cursor_first_increment_committed"]
                           and (row["byte_store_committed_before_word_fault"] is not False)
                           for row in faults)),
        "scope": "isolated C++ candidates on aligned ordinary RAM; callers not claimed",
        "reference": reference,
        "candidate_source_sha256": source_hash,
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed,
        "random_samples_per_function": samples,
        "function_comparisons": sum(row["comparisons"] for row in functions),
        "functions": functions,
        "negative_controls": controls,
        "partial_fault_cases": faults,
        "callers": {"verified": [], "note": "No containing-function callsites manually verified; possible reference scans are not promoted to caller evidence."},
        "limitations": [
            "Static instruction pins and bounded Unicorn differential runs do not prove whole-game equivalence.",
            "MMIO, concurrent mutation, and externally visible intermediate writes are not modeled beyond recorded ordinary-RAM access order.",
            "Fault probes cover table read, byte store, and word store faults, not every mapping/alignment or OS exception detail.",
            "No higher-level record type or semantic field names are inferred; only r0-relative offsets are described.",
            "No direct caller windows or emulator execution were performed.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    report = run(args.code, args.output, args.samples, args.seed)
    print(json.dumps({"passed": report["passed"],
                      "function_comparisons": report["function_comparisons"],
                      "negative_controls": report["negative_controls"],
                      "fault_cases": len(report["partial_fault_cases"])}, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
