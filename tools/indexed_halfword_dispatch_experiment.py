"""Differentially test two indexed halfword-dispatch/update routines."""
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
from tools.semantic_experiment import DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner
from tools.semantic_experiment_support import compile_candidate_symbols, load_pinned_reference

ADDRESSES = (0x001DC648, 0x001DC6A8)
TABLE_OFFSETS = {0x001DC648: 0xEC, 0x001DC6A8: 0xE8}
WORDS = {
    0x001DC648: (0xE2802018, 0xE92D0030, 0xE8921004, 0xE3A05002,
                 0xE59010BC, 0xE59040EC, 0xE0855102, 0xE2802020,
                 0xE19110B5, 0xE3A03001, 0xE7941101, 0xE7CC3002,
                 0xE590201C, 0xE0802102, 0xE582103C, 0xE590101C,
                 0xE2811001, 0xE580101C, 0xE5901018, 0xE2811001,
                 0xE5801018, 0xE8BD0030, 0xE3A00001, 0xE12FFF1E),
    0x001DC6A8: (0xE2803018, 0xE92D0030, 0xE8931008, 0xE3A05002,
                 0xE59010BC, 0xE59040E8, 0xE0855103, 0xE2803020,
                 0xE19110B5, 0xE3A02000, 0xE7941101, 0xE7CC2003,
                 0xE590201C, 0xE0802102, 0xE582103C, 0xE590101C,
                 0xE2811001, 0xE580101C, 0xE5901018, 0xE2811001,
                 0xE5801018, 0xE8BD0030, 0xE3A00001, 0xE12FFF1E),
}


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if len(image) != int(game_info["code_bin_size"]) or digest != game_info["code_sha256"]:
        raise ValueError("code.bin size/SHA-256 does not match configured revision")
    by_address = {int(row["address"], 16): row for row in ledger}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    result = {}
    for address in ADDRESSES:
        row = by_address.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 96:
            raise ValueError(f"Missing matching 96-byte ledger row at {address:#010x}")
        raw = image[address - TEXT:address - TEXT + 96]
        words = struct.unpack("<24I", raw)
        if words != WORDS[address]:
            raise ValueError(f"Pinned instruction words changed at {address:#010x}")
        decoded = [(i.mnemonic.lower(), i.op_str.lower()) for i in decoder.disasm(raw, address)]
        if len(decoded) != 24 or decoded[-1] != ("bx", "lr"):
            raise ValueError(f"Unexpected function decode at {address:#010x}: {decoded}")
        result[hex(address)] = {
            "size": len(raw), "ledger_name": row["name"],
            "function_sha256": hashlib.sha256(raw).hexdigest(),
            "instruction_words": [f"0x{word:08x}" for word in words],
            "instructions": [f"{mnemonic} {operands}" for mnemonic, operands in decoded],
            "observed": {
                "input_cursor": "u32 at record+0x18",
                "output_cursor": "u32 at record+0x1c",
                "source_halfword": "u16 at *(u32*)(record+0xbc) + 2 + input_cursor*4",
                "selected_value": f"u32 from *(u32*)(record+0x{TABLE_OFFSETS[address]:x})[key]",
                "writes": ["byte 1 to record+0x20+output_cursor",
                           "selected u32 to record+0x3c+output_cursor*4"],
                "post_writes": ["reload and increment output cursor", "reload and increment input cursor"],
                "return": "r0=1; r4/r5 and SP restored",
            },
        }
    return {"code_sha256": digest, "functions": result}


def _put32(data: bytearray, address: int, value: int):
    struct.pack_into("<I", data, address - DATA, value & 0xFFFFFFFF)


def _put16(data: bytearray, address: int, value: int):
    struct.pack_into("<H", data, address - DATA, value & 0xFFFF)


def make_case(address: int, seed: int, label: str, source_cursor=1, output_cursor=2,
              source=DATA + 0x600, table=DATA + 0x700, key=3, selected=DATA + 0xA00,
              *, source_key_address=None, table_key=None) -> Case:
    rng = random.Random(seed ^ address ^ sum(map(ord, label)))
    data = bytearray(rng.randbytes(DATA_SIZE))
    record = DATA + 0x200
    _put32(data, record + 0x18, source_cursor)
    _put32(data, record + 0x1c, output_cursor)
    _put32(data, record + 0xbc, source)
    other_table = DATA + 0x740
    _put32(data, record + 0xec, table if TABLE_OFFSETS[address] == 0xec else other_table)
    _put32(data, record + 0xe8, table if TABLE_OFFSETS[address] == 0xe8 else other_table)
    key_address = source + 2 + source_cursor * 4 if source_key_address is None else source_key_address
    if DATA <= key_address and key_address + 2 <= DATA + DATA_SIZE:
        _put16(data, key_address, key)
    correct_entry = table + (key if table_key is None else table_key) * 4
    wrong_entry = other_table + key * 4
    if DATA <= correct_entry and correct_entry + 4 <= DATA + DATA_SIZE:
        _put32(data, correct_entry, selected)
    if DATA <= wrong_entry and wrong_entry + 4 <= DATA + DATA_SIZE:
        _put32(data, wrong_entry, selected ^ 0x80)
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0] = record
    return Case(label, tuple(registers), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def make_cases(address: int, seed: int, samples: int = 48) -> list[Case]:
    cases = [make_case(address, seed, f"boundary-{i}", source_cursor=cursor,
                       output_cursor=out, key=key, selected=DATA + 0xA00 + i * 4)
             for i, (cursor, out, key) in enumerate(((0, 0, 0), (1, 2, 1),
                                                       (7, 5, 0x7f), (0x20, 0x30, 0xff)))]
    rng = random.Random(seed ^ address)
    for index in range(samples):
        cases.append(make_case(address, seed + index, f"random-{index}",
                               source_cursor=rng.randrange(0, 48),
                               output_cursor=rng.randrange(0, 48), key=rng.randrange(0, 16),
                               selected=DATA + 0xA00 + rng.randrange(0, 0x100) * 4))
    # Both wraparound aliases are intentional: the pointer write overlaps the
    # input cursor (+0x18) or output cursor (+0x1c), which the original reloads.
    cases.append(make_case(address, seed, "alias-output-slot-overwrites-input-cursor",
                           source_cursor=1, output_cursor=0xFFFFFFF7, key=5,
                           selected=DATA + 0xA10))
    cases.append(make_case(address, seed, "alias-output-slot-overwrites-output-cursor",
                           source_cursor=2, output_cursor=0xFFFFFFF8, key=6,
                           selected=DATA + 0xA14))
    return cases


def _trace(image: bytes, address: int, case: Case, replacement: bytes | None = None):
    runner = Runner(image, address, replacement)
    events = []

    def memory(_uc, access, at, size, _value, _user):
        if DATA <= at < DATA + DATA_SIZE and access in (unicorn.UC_MEM_READ, unicorn.UC_MEM_WRITE):
            events.append(("read" if access == unicorn.UC_MEM_READ else "write", at, size))

    invalid = []

    def invalid_memory(_uc, access, at, size, _value, _user):
        invalid.append((access, at, size))
        return False

    runner.uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE, memory)
    runner.uc.hook_add(unicorn.UC_HOOK_MEM_INVALID, invalid_memory)
    result = runner.run(case, budget=160)
    return result, tuple(events), tuple(invalid)


def _same(old, new, *, compare_trace=True):
    a, a_events, a_invalid = old
    b, b_events, b_invalid = new
    if bool(a.fault) != bool(b.fault):
        return "fault/non-fault state differs"
    if not a.fault and (not a.stopped or not b.stopped):
        return "execution did not return"
    if a.result != b.result:
        return "return value differs"
    if a.fault:
        # After an interrupted routine, r4/r5 are instruction-specific scratch
        # state even though normal-return preservation is still checked below.
        # Keep SP and visible memory strict; the raw register comparison is
        # reported separately for exception consumers.
        if a.preserved[8] != b.preserved[8]:
            return "SP differs at fault"
        if a.live_stack != b.live_stack:
            return "live stack differs at fault"
    elif a.preserved != b.preserved:
        return "callee-saved registers or SP differ"
    if a.data != b.data:
        changed = [hex(DATA + i) for i, (x, y) in enumerate(zip(a.data, b.data)) if x != y]
        return f"visible data differs at {changed[:8]}"
    a_reads = {x for x in a.reads if DATA <= x < DATA + DATA_SIZE}
    b_reads = {x for x in b.reads if DATA <= x < DATA + DATA_SIZE}
    a_writes = {x for x in a.writes if DATA <= x < DATA + DATA_SIZE}
    b_writes = {x for x in b.writes if DATA <= x < DATA + DATA_SIZE}
    if a_reads != b_reads or a_writes != b_writes:
        return "memory footprint differs"
    if a.fault and a_invalid != b_invalid:
        return f"faulting memory access differs: {a_invalid} != {b_invalid}"
    if compare_trace and a_events != b_events:
        return f"ordered memory events differ: {a_events} != {b_events}"
    return None


def _negative_case(address: int, seed: int, kind: str) -> Case:
    if kind == "wrong_dispatch_table":
        return make_case(address, seed, kind, source_cursor=0, output_cursor=1,
                         key=2, selected=DATA + 0xA20,
                         table=DATA + 0x700, table_key=2)
    if kind == "wrong_flag_value":
        return make_case(address, seed, kind, source_cursor=0, output_cursor=4,
                         key=2, selected=DATA + 0xA24)
    raise ValueError(kind)


def run(code_path: Path, output: Path, seed: int, samples: int = 48) -> dict:
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "experiments/semantic_equivalence/indexed_halfword_dispatch_candidates.cpp"
    symbols = [f"candidate_{address:08x}" for address in ADDRESSES]
    symbols += ["negative_wrong_dispatch_001dc648", "negative_wrong_dispatch_001dc6a8",
                "negative_wrong_flag_value_001dc648", "negative_wrong_flag_value_001dc6a8"]
    compiled = compile_candidate_symbols(source, output / "indexed-halfword-dispatch.o", ROOT, symbols)
    function_results, fault_results, negatives = [], [], []
    for address in ADDRESSES:
        code = compiled[f"candidate_{address:08x}"]
        rows = []
        for case in make_cases(address, seed, samples):
            old = _trace(pinned.image, address, case)
            new = _trace(pinned.image, address, case, code)
            reason = _same(old, new)
            if reason:
                rows.append({"case": case.label, "passed": False, "difference": reason})
                break
            rows.append({"case": case.label, "passed": True})
        function_results.append({"address": hex(address), "candidate": f"candidate_{address:08x}",
                                 "candidate_bytes": len(code), "cases": len(rows),
                                 "passed": all(row["passed"] for row in rows), "failures": rows[:1] if not rows[-1]["passed"] else []})

        # Wrong dispatch table is address-specific because the originals differ
        # only in the table-pointer field at +0xe8/+0xec.
        wrong_symbol = ("negative_wrong_dispatch_001dc648" if address == 0x001DC648
                        else "negative_wrong_dispatch_001dc6a8")
        flag_symbol = ("negative_wrong_flag_value_001dc648" if address == 0x001DC648
                       else "negative_wrong_flag_value_001dc6a8")
        for kind, symbol in (("wrong_dispatch_table", wrong_symbol),
                             ("wrong_flag_value", flag_symbol)):
            case = _negative_case(address, seed, kind)
            old = _trace(pinned.image, address, case)
            wrong = _trace(pinned.image, address, case, compiled[symbol])
            reason = _same(old, wrong, compare_trace=False)
            negatives.append({"address": hex(address), "control": kind,
                              "detected": reason is not None, "difference": reason})

        record = DATA + 0x200
        fault_cases = [
            make_case(address, seed, "fault-source-halfword-crosses-map", source=DATA + DATA_SIZE - 3,
                      source_cursor=0, output_cursor=0),
            make_case(address, seed, "fault-dispatch-table-word-crosses-map", table=DATA + DATA_SIZE - 2,
                      source_cursor=0, output_cursor=0, key=1),
            make_case(address, seed, "fault-flag-destination-outside-map", output_cursor=0x2000),
        ]
        for case in fault_cases:
            old = _trace(pinned.image, address, case)
            new = _trace(pinned.image, address, case, code)
            reason = _same(old, new, compare_trace=True)
            fault_results.append({"address": hex(address), "case": case.label,
                                  "both_faulted": bool(old[0].fault and new[0].fault),
                                  "original_fault": old[0].fault, "candidate_fault": new[0].fault,
                                  "callee_saved_state_matches_at_fault": old[0].preserved == new[0].preserved,
                                  "original_invalid_access": old[2], "candidate_invalid_access": new[2],
                                  "passed": reason is None and bool(old[0].fault), "difference": reason})

    report = {
        "schema": 1, "experiment": "indexed_halfword_dispatch_pair", "seed": seed,
        "random_samples_per_function": samples, "reference": reference,
        "functions": function_results, "fault_probes": fault_results,
        "negative_controls": negatives,
        "passed": all(row["passed"] for row in function_results + fault_results)
                  and all(row["detected"] for row in negatives),
        "limitations": [
            "Ordinary mapped RAM only; these are synthetic differential cases, not gameplay traces.",
            "ARM BL scan not manually audited for these entries; no caller window is claimed.",
            "The +0x18/+0x1c output-slot aliases use 32-bit wrapped addresses to expose reload ordering.",
            "At invalid-memory interruption, the fault address, access width, data prefix, and SP match; r4/r5 scratch values differ from the original and are recorded per probe. Normal-return callee-saved state matches.",
            "C++ volatile accesses and Unicorn ARM11 execution do not prove portable C++ object-lifetime semantics or whole-game equivalence.",
            "Candidates are isolated and do not change production sources or the exact-match ledger.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/indexed-halfword-dispatch")
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=48)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "functions": report["functions"],
                      "fault_probes": report["fault_probes"],
                      "negative_controls": report["negative_controls"]}, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
