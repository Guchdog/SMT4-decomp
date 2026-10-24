#!/usr/bin/env python3
"""Isolated differential check for simple TBCR/TBL1 accessors; emits no IPS."""
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

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.inspect_assets import parse_tbb_header
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference,
    validate_local_blob,
)


TBL1 = 0x314C4254
ENTRY = 0x002C0E9C


def make_cases(seed: int, samples: int):
    rng = random.Random(seed ^ ENTRY)
    fixtures = (
        ("null", None),
        ("wrong-magic", (0xDEADBEEF, 0, 0, 0x10)),
        ("valid-empty", (TBL1, 0, 4, 0x10)),
        ("valid-zero-stride", (TBL1, 0, 0, 0x10)),
        ("valid-partial-row", (TBL1, 10, 4, 0x10)),
        ("valid-single-row", (TBL1, 4, 4, 0x10)),
    )
    for label, header in fixtures:
        data = bytearray(rng.randbytes(DATA_SIZE))
        regs = [rng.getrandbits(32) for _ in range(13)]
        if header is None:
            regs[0] = 0
        else:
            regs[0] = DATA + 0x100
            struct.pack_into("<4I", data, 0x100, *header)
        yield Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                   rng.getrandbits(4) << 28)
    for index in range(samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        regs = [rng.getrandbits(32) for _ in range(13)]
        base_offset = rng.randrange(0x100, DATA_SIZE - 0x20) & ~3
        magic = TBL1 if rng.randrange(10) else 0xDEADBEEF
        header = (magic, rng.randrange(0x101), rng.randrange(0x21), rng.getrandbits(32))
        regs[0] = DATA + base_offset
        struct.pack_into("<4I", data, base_offset, *header)
        yield Case(f"random-{index}", tuple(regs), bytes(data),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def make_subtable_cases(seed: int, samples: int):
    rng = random.Random(seed ^ 0x002AC2F4)
    fixtures = (
        ("null-container", None, 0),
        ("wrong-container-magic", 0xDEADBEEF, 0),
        ("empty-container", 0x52434254, 0),
        ("valid-first-index", 0x52434254, 0),
        ("valid-second-index", 0x52434254, 1),
        ("wrong-child-magic", 0x52434254, 1),
        ("index-equals-count", 0x52434254, 2),
    )
    for label, magic, table_index in fixtures:
        data = bytearray(rng.randbytes(DATA_SIZE))
        regs = [rng.getrandbits(32) for _ in range(13)]
        if magic is None:
            regs[0] = 0
        else:
            base_offset = 0x100
            regs[0] = DATA + base_offset
            header_size = 0x20
            count = 0 if label == "empty-container" else 2
            struct.pack_into("<3I", data, base_offset, magic, header_size, count)
            offsets = (0x30, 0x50)
            struct.pack_into("<2I", data, base_offset + 0x0C, *offsets)
            child_magic = 0xDEADBEEF if label == "wrong-child-magic" else 0x314C4254
            for offset in offsets:
                child_offset = base_offset + header_size + offset
                struct.pack_into("<4I", data, child_offset, child_magic, 4, 4, 0x10)
        regs[1] = table_index
        yield Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                   rng.getrandbits(4) << 28)
    for index in range(samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        regs = [rng.getrandbits(32) for _ in range(13)]
        base_offset = rng.randrange(0x100, 0x300) & ~3
        count = rng.randrange(0, 5)
        header_size = (0x0C + count * 4 + 0xF) & ~0xF
        offsets = tuple(0x40 + table * 0x20 for table in range(count))
        magic = 0x52434254 if rng.randrange(20) else 0xDEADBEEF
        regs[0] = DATA + base_offset
        regs[1] = rng.randrange(count + 1)
        struct.pack_into("<3I", data, base_offset, magic, header_size, count)
        if offsets:
            struct.pack_into("<" + "I" * count, data, base_offset + 0x0C, *offsets)
        for table, offset in enumerate(offsets):
            child_offset = base_offset + header_size + offset
            child_magic = 0x314C4254 if rng.randrange(5) else 0xDEADBEEF
            struct.pack_into("<4I", data, child_offset, child_magic,
                             rng.randrange(0x101), rng.randrange(0x21), rng.getrandbits(32))
        yield Case(f"random-{index}", tuple(regs), bytes(data),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def make_row_count_cases(seed: int, samples: int):
    rng = random.Random(seed ^ 0x002C0E4C)
    fixtures = (
        ("null", None),
        ("wrong-magic", (0xDEADBEEF, 10, 4, 0)),
        ("zero-stride", (TBL1, 10, 0, 0)),
        ("zero-payload", (TBL1, 0, 4, 0)),
        ("payload-below-stride", (TBL1, 3, 4, 0)),
        ("exact-divisibility", (TBL1, 16, 4, 0)),
        ("truncated-division", (TBL1, 10, 4, 0)),
        ("large-u32-values", (TBL1, 0xFFFFFFFF, 0x80000001, 0)),
    )
    for label, header in fixtures:
        data = bytearray(rng.randbytes(DATA_SIZE))
        regs = [rng.getrandbits(32) for _ in range(13)]
        if header is None:
            regs[0] = 0
        else:
            regs[0] = DATA + 0x100
            struct.pack_into("<4I", data, 0x100, *header)
        yield Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                   rng.getrandbits(4) << 28)
    for index in range(samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        regs = [rng.getrandbits(32) for _ in range(13)]
        header = (TBL1 if rng.randrange(20) else 0xDEADBEEF,
                  rng.getrandbits(32), rng.randrange(1, 1 << 32),
                  rng.getrandbits(32))
        regs[0] = DATA + 0x100
        struct.pack_into("<4I", data, 0x100, *header)
        yield Case(f"random-{index}", tuple(regs), bytes(data),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def real_tbb_case(raw: bytes, label: str, *, table_index: int | None = None,
                  table_pointer: int | None = None, seed: int = 0) -> Case:
    if len(raw) > DATA_SIZE - 0x100:
        raise ValueError("Real TBB file does not fit in the experiment DATA region")
    rng = random.Random(seed)
    data = bytearray(rng.randbytes(DATA_SIZE))
    data[0x100 : 0x100 + len(raw)] = raw
    regs = [rng.getrandbits(32) for _ in range(13)]
    if table_pointer is None:
        regs[0] = DATA + 0x100
        regs[1] = table_index or 0
    else:
        regs[0] = table_pointer
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def run(code_path: Path, output: Path, seed: int, samples: int,
        real_tbb_path: Path | None = None):
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    reference_hash = hashlib.sha256(image).hexdigest()
    if len(image) != game["code_bin_size"] or reference_hash != game["code_sha256"]:
        raise ValueError("Private code.bin does not match the configured revision")

    source = ROOT / "experiments/semantic_equivalence/tbb_candidates.cpp"
    object_path = output / "tbb_candidates.o"
    build = compile_tu_armv6k(source, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    functions = extract_elf_functions_detailed(object_path)
    symbol = "candidate_002c0e9c"
    wrong_symbol = "wrong_tbb_payload_magic"
    for name in (symbol, wrong_symbol):
        if name not in functions:
            raise ValueError(f"Missing compiled function: {name}")
        _, relocations = functions[name]
        if relocations:
            raise ValueError(f"Unsupported relocation in {name}: {relocations}")

    candidate_code = functions[symbol][0]
    wrong_code = functions[wrong_symbol][0]
    validate_local_blob(candidate_code)
    validate_local_blob(wrong_code)

    original = Runner(image, ENTRY)
    rebuilt = Runner(image, ENTRY, candidate_code,
                     replacement_validator=validate_local_blob)
    correct_results = []
    for case in make_cases(seed, samples):
        reason = difference(original.run(case), rebuilt.run(case))
        correct_results.append({"case": case.label, "passed": reason is None,
                                "reason": reason})

    wrong_runner = Runner(image, ENTRY, wrong_code,
                          replacement_validator=validate_local_blob)
    negative = None
    for case in make_cases(seed, samples):
        reason = difference(original.run(case), wrong_runner.run(case))
        if reason:
            negative = {"detected": True, "case": case.label, "reason": reason}
            break
    if negative is None:
        negative = {"detected": False}

    subtable_symbol = "candidate_002ac2f4"
    wrong_subtable_symbol = "wrong_tbb_subtable_magic"
    for name in (subtable_symbol, wrong_subtable_symbol):
        if name not in functions:
            raise ValueError(f"Missing compiled function: {name}")
        _, relocations = functions[name]
        if relocations:
            raise ValueError(f"Unsupported relocation in {name}: {relocations}")
        validate_local_blob(functions[name][0])
    subtable_code = functions[subtable_symbol][0]
    wrong_subtable_code = functions[wrong_subtable_symbol][0]
    subtable_original = Runner(image, 0x002AC2F4)
    subtable_rebuilt = Runner(image, 0x002AC2F4, subtable_code,
                              replacement_validator=validate_local_blob)
    subtable_results = []
    for case in make_subtable_cases(seed, samples):
        reason = difference(subtable_original.run(case), subtable_rebuilt.run(case))
        subtable_results.append({"case": case.label, "passed": reason is None,
                                 "reason": reason})
    wrong_subtable_runner = Runner(image, 0x002AC2F4, wrong_subtable_code,
                                   replacement_validator=validate_local_blob)
    subtable_negative = None
    for case in make_subtable_cases(seed, samples):
        if case.label != "wrong-child-magic":
            continue
        reason = difference(subtable_original.run(case), wrong_subtable_runner.run(case))
        if reason:
            subtable_negative = {"detected": True, "case": case.label, "reason": reason}
            break
    if subtable_negative is None:
        subtable_negative = {"detected": False}

    row_count_symbol = "candidate_002c0e4c"
    wrong_row_count_symbol = "wrong_tbb_rowcount_divisor"
    for name in (row_count_symbol, wrong_row_count_symbol):
        if name not in functions:
            raise ValueError(f"Missing compiled function: {name}")
        _, relocations = functions[name]
        if relocations:
            raise ValueError(f"Unsupported relocation in {name}: {relocations}")
        validate_local_blob(functions[name][0])
    row_count_code = functions[row_count_symbol][0]
    wrong_row_count_code = functions[wrong_row_count_symbol][0]
    row_count_original = Runner(image, 0x002C0E4C)
    row_count_rebuilt = Runner(image, 0x002C0E4C, row_count_code,
                               replacement_validator=validate_local_blob)
    row_count_results = []
    for case in make_row_count_cases(seed, samples):
        reason = difference(row_count_original.run(case, budget=2048),
                            row_count_rebuilt.run(case, budget=2048))
        row_count_results.append({"case": case.label, "passed": reason is None,
                                  "reason": reason})
    wrong_row_count_runner = Runner(image, 0x002C0E4C, wrong_row_count_code,
                                    replacement_validator=validate_local_blob)
    row_count_negative = None
    for case in make_row_count_cases(seed, samples):
        if case.label != "truncated-division":
            continue
        reason = difference(row_count_original.run(case, budget=2048),
                            wrong_row_count_runner.run(case, budget=2048))
        if reason:
            row_count_negative = {"detected": True, "case": case.label,
                                  "reason": reason}
            break
    if row_count_negative is None:
        row_count_negative = {"detected": False}

    real_tbb_results = []
    real_tbb_sha256 = None
    if real_tbb_path is not None:
        real_tbb = real_tbb_path.read_bytes()
        real_tbb_sha256 = hashlib.sha256(real_tbb).hexdigest()
        parsed_tbb = parse_tbb_header(real_tbb)
        header_size = parsed_tbb["header_size"]
        table_count = parsed_tbb["table_count"]
        for table_index in range(table_count + 1):
            case = real_tbb_case(real_tbb, f"real-tbb-subtable-{table_index}",
                                 table_index=table_index, seed=seed ^ table_index)
            reason = difference(subtable_original.run(case), subtable_rebuilt.run(case))
            expected = None
            if table_index < table_count:
                relative_offset = struct.unpack_from("<I", real_tbb, 0x0C + table_index * 4)[0]
                expected = DATA + 0x100 + header_size + relative_offset
            actual = subtable_rebuilt.run(case).result
            passed = reason is None and actual == (expected or 0)
            real_tbb_results.append({"case": case.label, "passed": passed,
                                     "expected": expected, "actual": actual,
                                     "reason": reason})
        for table_index in range(table_count):
            relative_offset = struct.unpack_from("<I", real_tbb, 0x0C + table_index * 4)[0]
            table_pointer = DATA + 0x100 + header_size + relative_offset
            case = real_tbb_case(real_tbb, f"real-tbb-payload-{table_index}",
                                 table_pointer=table_pointer,
                                 seed=seed ^ 0xC0E9C ^ table_index)
            reason = difference(original.run(case), rebuilt.run(case))
            expected = table_pointer + 0x10
            actual = rebuilt.run(case).result
            passed = reason is None and actual == expected
            real_tbb_results.append({"case": case.label, "passed": passed,
                                     "expected": expected, "actual": actual,
                                     "reason": reason})
            row_case = real_tbb_case(real_tbb, f"real-tbb-row-count-{table_index}",
                                     table_pointer=table_pointer,
                                     seed=seed ^ 0x2C0E4C ^ table_index)
            reason = difference(row_count_original.run(row_case, budget=2048),
                                row_count_rebuilt.run(row_case, budget=2048))
            actual = row_count_rebuilt.run(row_case, budget=2048).result
            passed = reason is None and actual == 0
            real_tbb_results.append({"case": row_case.label, "passed": passed,
                                     "expected": 0, "actual": actual,
                                     "reason": reason})

    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                               text=True, check=True)
    report = {
        "passed": (all(item["passed"] for item in correct_results) and negative["detected"]
                   and all(item["passed"] for item in subtable_results)
                   and subtable_negative["detected"]
                   and all(item["passed"] for item in row_count_results)
                   and row_count_negative["detected"]
                   and all(item["passed"] for item in real_tbb_results)),
        "scope": "TBB getters; isolated calls; row count oracle follows the exact shared helper in the pinned original image; no IPS or game integration",
        "entry": hex(ENTRY),
        "reference_sha256": reference_hash,
        "candidate_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed,
        "random_cases_per_function": samples,
        "candidate_bytes": len(candidate_code),
        "cases": correct_results,
        "negative_control": negative,
        "subtable_entry": hex(0x002AC2F4),
        "subtable_candidate_bytes": len(subtable_code),
        "subtable_cases": subtable_results,
        "subtable_negative_control": subtable_negative,
        "row_count_entry": hex(0x002C0E4C),
        "row_count_candidate_bytes": len(row_count_code),
        "row_count_cases": row_count_results,
        "row_count_negative_control": row_count_negative,
        "real_tbb_path": str(real_tbb_path) if real_tbb_path else None,
        "real_tbb_sha256": real_tbb_sha256,
        "real_tbb_cases": real_tbb_results,
        "limitations": [
            "Tbb_GetRowCount oracle executes its exact tail-branch target at 0x002C6C10 in the hash-pinned image",
            "Real TitleTable.tbb coverage exercises only its existing two tables and boundary index",
            "A sampled differential test is not a proof for every input",
            "No caller-window, IPS, emulator, or game integration test",
            "Does not validate malformed offsets or payload memory bounds",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                         encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", required=True, type=Path, help="private extracted code.bin")
    parser.add_argument("--output", required=True, type=Path, help="ignored build output directory")
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--real-tbb", type=Path,
                        help="optional extracted TBCR asset for direct getter comparisons")
    args = parser.parse_args()
    run(args.code, args.output, args.seed, args.samples, args.real_tbb)


if __name__ == "__main__":
    main()
