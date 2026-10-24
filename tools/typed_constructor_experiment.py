#!/usr/bin/env python3
"""Differential-test two small typed-record constructor leaves in isolation."""
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
from tools.build_check import find_clang
from tools.semantic_experiment import DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference
from tools.semantic_experiment_support import compile_candidate_symbols, load_pinned_reference

FUNCTIONS = {
    0x003A80CC: {"tag": 0x0D, "table_slot": 0x004023E4},
    0x003A9644: {"tag": 0x08, "table_slot": 0x004022B4},
}
BODY_SIZE = 28
U32_MASK = 0xFFFFFFFF
EXACT_BYTES = {
    0x003A80CC: "0130a0e31030c0e5140080e20d10a0e30020a0e3060080e81eff2fe1",
    0x003A9644: "0130a0e31030c0e5140080e20810a0e30020a0e3060080e81eff2fe1",
}
TABLE_NEIGHBORS = {
    0x004023E4: (0x003A7D74, 0, 0x003A80CC, 0, 0x0022CD3C),
    0x004022B4: (0x003A95B4, 0, 0x003A9644, 0, 0x9B819B81),
}


def decode(image: bytes, address: int):
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    offset = address - TEXT
    decoded = list(decoder.disasm(image[offset:offset + BODY_SIZE], address))
    if sum(item.size for item in decoded) != BODY_SIZE:
        raise ValueError(f"incomplete function body at {address:#010x}")
    return tuple((item.mnemonic, item.op_str) for item in decoded)


def raw_pointer_sites(image: bytes, address: int):
    needle = struct.pack("<I", address)
    sites = []
    offset = 0
    while True:
        offset = image.find(needle, offset)
        if offset < 0:
            break
        sites.append(TEXT + offset)
        offset += 1
    return tuple(sites)


def discover_direct_bl_callers(image: bytes):
    result = {address: [] for address in FUNCTIONS}
    for index in range(len(image) // 4):
        word = struct.unpack_from("<I", image, index * 4)[0]
        if (word & 0x0F000000) != 0x0B000000 or (word >> 28) == 0xF:
            continue
        displacement = (word & 0x00FFFFFF) << 2
        if displacement & (1 << 25):
            displacement -= 1 << 26
        target = (TEXT + index * 4 + 8 + displacement) & U32_MASK
        if target in result:
            result[target].append(TEXT + index * 4)
    return {address: tuple(sites) for address, sites in result.items()}


def verify_reference(image: bytes, ledger: list[dict[str, str]]):
    rows = {int(row["address"], 16): row for row in ledger}
    expected_common = (
        ("mov", "r3, #1"), ("strb", "r3, [r0, #0x10]"),
        ("add", "r0, r0, #0x14"),
    )
    for address, info in FUNCTIONS.items():
        row = rows.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != BODY_SIZE:
            raise ValueError(f"missing matching 28-byte ledger row at {address:#010x}")
        if image[address - TEXT:address - TEXT + BODY_SIZE].hex() != EXACT_BYTES[address]:
            raise ValueError(f"exact reference bytes changed at {address:#010x}")
        expected = expected_common + (
            ("mov", f"r1, #{info['tag']}" if info["tag"] < 10 else f"r1, #0x{info['tag']:x}"), ("mov", "r2, #0"),
            ("stm", "r0, {r1, r2}"), ("bx", "lr"),
        )
        actual = decode(image, address)
        if actual != expected:
            raise ValueError(f"instruction body changed at {address:#010x}: {actual}")
        slot = info["table_slot"]
        offset = slot - TEXT
        words = tuple(struct.unpack_from("<I", image, offset + delta * 4)[0]
                      for delta in range(-2, 3))
        if words != TABLE_NEIGHBORS[slot]:
            raise ValueError(f"table neighborhood changed at {slot:#010x}: {words}")
        if raw_pointer_sites(image, address) != (slot,):
            raise ValueError(f"raw pointer site changed for {address:#010x}")
    direct = discover_direct_bl_callers(image)
    if any(direct.values()):
        raise ValueError(f"unexpected direct BL caller(s): {direct}")
    return rows, direct


def make_case(seed: int, address: int, label: str, index: int):
    rng = random.Random(seed ^ address ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    base = DATA + 0x100 + (index % 8) * 4
    # Directed pre-state patterns ensure the stores really overwrite both old
    # and matching values; the remaining cases are independently seeded.
    patterns = (
        (0, 0, 0), (0xFF, U32_MASK, U32_MASK),
        (0xA5, 0x5A5AA5A5, 0xDEADBEEF),
        (1, FUNCTIONS[address]["tag"], 0),
    )
    if index < len(patterns):
        byte_value, first, second = patterns[index]
        data[base - DATA + 0x10] = byte_value
        struct.pack_into("<II", data, base - DATA + 0x14, first, second)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = base
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def attach_memory_trace(runner: Runner):
    events = []
    runner.uc.hook_add(
        unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE,
        lambda _uc, access, address, size, value, _user: events.append(
            ("write" if access == unicorn.UC_MEM_WRITE else "read",
             address, size, value)
        ),
        begin=DATA, end=DATA + DATA_SIZE - 1,
    )
    return events


def verify_candidate_shape(code: bytes, tag: int):
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    actual = tuple((item.mnemonic, item.op_str) for item in decoder.disasm(code, 0))
    expected = (
        ("mov", "r1, #1"), ("strb", "r1, [r0, #0x10]"),
        ("mov", f"r1, #{tag}" if tag < 10 else f"r1, #0x{tag:x}"), ("str", "r1, [r0, #0x14]"),
        ("mov", "r1, #0"), ("str", "r1, [r0, #0x18]"),
        ("add", "r0, r0, #0x14"), ("bx", "lr"),
    )
    if actual != expected:
        raise ValueError(f"candidate store shape/order differs: {actual}")


def run(code_path: Path, output: Path, samples: int = 64, seed: int = 20261024):
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    _rows, direct = verify_reference(pinned.image, pinned.ledger)
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "experiments/semantic_equivalence/typed_constructor_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    object_path = output / "typed_constructor_candidates.o"
    required = {f"candidate_{address:08x}" for address in FUNCTIONS} | {
        "negative_wrong_tag", "negative_wrong_offset", "negative_wrong_return",
    }
    compiled = compile_candidate_symbols(source, object_path, ROOT, required)
    for address, info in FUNCTIONS.items():
        verify_candidate_shape(compiled[f"candidate_{address:08x}"], info["tag"])

    function_results = []
    for address, info in FUNCTIONS.items():
        original = Runner(pinned.image, address)
        rebuilt = Runner(pinned.image, address, compiled[f"candidate_{address:08x}"])
        original_events = attach_memory_trace(original)
        rebuilt_events = attach_memory_trace(rebuilt)
        cases_run = 0
        representative_trace = None
        for index in range(samples + 4):
            case = make_case(seed, address, f"case-{index}", index)
            original_events.clear()
            rebuilt_events.clear()
            old = original.run(case)
            new = rebuilt.run(case)
            reason = difference(old, new, returns_value=True, compare_flags=True)
            if reason is None and original_events != rebuilt_events:
                reason = (f"ordered memory access trace differs: original={original_events}, "
                          f"candidate={rebuilt_events}")
            if reason:
                raise AssertionError(f"{address:#010x} {case.label}: {reason}")
            if representative_trace is None:
                representative_trace = [
                    {"kind": kind, "address": hex(site), "size_bytes": size,
                     "value": hex(value & U32_MASK)}
                    for kind, site, size, value in original_events
                ]
            cases_run += 1
        function_results.append({"address": hex(address), "tag": hex(info["tag"]),
                                 "candidate_bytes": len(compiled[f"candidate_{address:08x}"]),
                                 "cases": cases_run, "passed": True,
                                 "flags_checked": True,
                                 "ordered_read_write_width_trace_checked": True,
                                 "representative_ordered_memory_trace": representative_trace})

    controls = []
    address = 0x003A80CC
    base_case = make_case(seed + 0x31415, address, "negative-control", 3)
    original = Runner(pinned.image, address)
    original_events = attach_memory_trace(original)
    original_result = original.run(base_case)
    for symbol in ("negative_wrong_tag", "negative_wrong_offset", "negative_wrong_return"):
        wrong = Runner(pinned.image, address, compiled[symbol])
        wrong_events = attach_memory_trace(wrong)
        original_events.clear()
        wrong_events.clear()
        expected = original.run(base_case)
        actual = wrong.run(base_case)
        reason = difference(expected, actual, returns_value=True, compare_flags=True)
        if reason is None and original_events != wrong_events:
            reason = "ordered memory access trace differs"
        controls.append({"name": symbol, "detected": reason is not None,
                         "reason": reason, "original_result": hex(original_result.result)})

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("candidate source changed during experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True).stdout.splitlines()[0]
    report = {
        "schema": 1,
        "passed": all(item["passed"] for item in function_results)
        and all(item["detected"] for item in controls),
        "reference_sha256": pinned.game_info["code_sha256"],
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler,
        "seed": seed,
        "random_cases_per_function": samples,
        "functions": function_results,
        "direct_bl_callers": {hex(address): [hex(site) for site in sites]
                               for address, sites in direct.items()},
        "raw_function_pointer_sites": {
            hex(address): {"site": hex(info["table_slot"]),
                           "neighbor_words": [hex(word) for word in TABLE_NEIGHBORS[info["table_slot"]]],
                           "dispatch_verified": False}
            for address, info in FUNCTIONS.items()
        },
        "caller_windows": [],
        "negative_controls": controls,
        "contract": (
            "For aligned ordinary RAM and valid base pointers, write byte 1 at base+0x10, "
            "write tag (0x0D at 0x003A80CC, 0x08 at 0x003A9644) as a 32-bit word "
            "at base+0x14, write 32-bit zero at base+0x18, and return base+0x14; "
            "preserve ABI callee-saved state and incoming NZCV."
        ),
        "limitations": [
            "No direct ARM BL callers were found. Each function address occurs once as a raw word in a nearby data table; indirect dispatch and downstream callers were not executed.",
            "Original STM commits two words in one instruction; the reconstruction uses two ordered volatile STRs. Successful ordinary-RAM write addresses, widths, values, and order were compared, but partial data-abort/fault behavior is not claimed equivalent.",
            "Unaligned bases, MMIO, concurrency, exceptions, and partial-fault ordering are outside the bounded contract.",
            "Bounded differential tests are evidence, not a formal equivalence proof."
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/typed-constructors")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        report = run(args.code, args.output, args.samples, args.seed)
    except (RuntimeError, ValueError, OSError, AssertionError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    print(f"Typed-constructor experiment {'PASS' if report['passed'] else 'FAIL'}; report: {args.output / 'report.json'}")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
