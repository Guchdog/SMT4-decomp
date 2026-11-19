#!/usr/bin/env python3
"""Per-entry differential validation of adjacent initializers at 0x003f32f4."""
from __future__ import annotations

import argparse
import capstone
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

REFERENCE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CODE_BIN = ROOT / "extracted/exefs/code.bin"
GAME_INFO = ROOT / "config/game_info.json"
SOURCE = ROOT / "experiments/semantic_equivalence/h18_003f32f4_family.cpp"
TEXT = 0x00100000
EXTENT = 0x2C  # 9 ARM instructions followed by a pair of literal words.
CODE_SIZE = 0x00400000
STACK_BASE = 0x20000000
STACK_SIZE = 0x10000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x100
TRAP = 0x001F0000

ENTRIES = [
    {"address": 0x003F32F4, "name": "candidate_003f32f4", "pair_base": 0x00464C68,
     "pair_offset": 0, "zero": 0x00464C70, "literals": (0x00464C68, 0x00464C70)},
    {"address": 0x003F3320, "name": "candidate_003f3320", "pair_base": 0x00433E18,
     "pair_offset": 8, "zero": 0x00433E28, "literals": (0x00433E18, 0x00433E28)},
    {"address": 0x003F334C, "name": "candidate_003f334c", "pair_base": 0x004719C8,
     "pair_offset": 0, "zero": 0x004719D0, "literals": (0x004719C8, 0x004719D0)},
    {"address": 0x003F3378, "name": "candidate_003f3378", "pair_base": 0x00471C30,
     "pair_offset": 0, "zero": 0x00471C38, "literals": (0x00471C30, 0x00471C38)},
    {"address": 0x003F33A4, "name": "candidate_003f33a4", "pair_base": 0x00433070,
     "pair_offset": 0, "zero": 0x00433078, "literals": (0x00433070, 0x00433078)},
    {"address": 0x003F33D0, "name": "candidate_003f33d0", "pair_base": 0x004330C0,
     "pair_offset": 0, "zero": 0x004330C8, "literals": (0x004330C0, 0x004330C8)},
    {"address": 0x003F33FC, "name": "candidate_003f33fc", "pair_base": 0x00433148,
     "pair_offset": 0, "zero": 0x00433150, "literals": (0x00433148, 0x00433150)},
    {"address": 0x003F3428, "name": "candidate_003f3428", "pair_base": 0x0044E598,
     "pair_offset": 8, "zero": 0x0044E5A8, "literals": (0x0044E598, 0x0044E5A8)},
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pair_start(entry: dict) -> int:
    return entry["pair_base"] + entry["pair_offset"]


def expected_words(entry: dict) -> dict[int, int]:
    start = pair_start(entry)
    return {start: 0xFFFFFFFF, start + 4: 0xFFFFFFFF,
            entry["zero"]: 0, entry["zero"] + 4: 0}


def original_entry(image: bytes, entry: dict) -> bytes:
    address = entry["address"]
    offset = address - TEXT
    body = image[offset:offset + EXTENT]
    if len(body) != EXTENT:
        raise ValueError(f"truncated entry at {address:#x}")
    if struct.unpack_from("<I", body, 0x20)[0] != 0xE12FFF1E:
        raise ValueError(f"missing BX LR at {address + 0x20:#x}")
    literals = struct.unpack_from("<II", body, 0x24)
    if literals != entry["literals"]:
        raise ValueError(f"literal mismatch at {address:#x}: {literals!r}")
    strd = struct.unpack_from("<I", body, 0x0C)[0]
    expected_strd = 0xE1C200F0 if entry["pair_offset"] == 0 else 0xE1C200F8
    if strd != expected_strd:
        raise ValueError(f"unexpected STRD displacement at {address:#x}: {strd:#010x}")
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    instructions = list(cs.disasm(body[:0x24], address))
    if len(instructions) != 9 or instructions[-1].mnemonic != "bx" or instructions[-1].op_str != "lr":
        raise ValueError(f"unexpected instruction boundary at {address:#x}")
    if any(i.mnemonic in ("bl", "blx") for i in instructions):
        raise ValueError(f"unexpected call in leaf initializer {address:#x}")
    return body


def caller_inventory(image: bytes, address: int) -> dict:
    branches, pointers = [], []
    for offset in range(0, len(image) - 3, 4):
        word = struct.unpack_from("<I", image, offset)[0]
        site = TEXT + offset
        if word == address:
            pointers.append(hex(site))
        if (word & 0x0F000000) == 0x0B000000:
            disp = word & 0x00FFFFFF
            if disp & 0x00800000:
                disp -= 0x01000000
            if site + 8 + disp * 4 == address:
                branches.append(hex(site))
    return {"aligned_arm_bl_sites": branches, "aligned_pointer_words": pointers}


def compile_symbols(source: Path, object_path: Path) -> tuple[dict[str, bytes], str]:
    result = compile_tu_armv6k(source, object_path, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "ARMv6K family compilation failed")
    functions = extract_elf_functions_detailed(object_path)
    codes = {}
    for entry in ENTRIES:
        symbol = entry["name"]
        if symbol not in functions:
            raise ValueError(f"candidate symbol missing: {symbol}")
        code, relocations = functions[symbol]
        if relocations:
            raise ValueError(f"unexpected relocation in {symbol}: {relocations}")
        codes[symbol] = code
    return codes, sha256(object_path.read_bytes())


def initial_region(rng: random.Random, length: int, pattern: int) -> bytes:
    if pattern == 0:
        return bytes(length)
    if pattern == 1:
        return bytes([0xFF]) * length
    if pattern == 2:
        return bytes([0xA5]) * length
    if pattern == 3:
        return bytes([0x5A]) * length
    return bytes(rng.getrandbits(8) for _ in range(length))


def run_one(code: bytes, entry: dict, case_seed: int, pattern: int, nzcv: int) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(TEXT, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_write(entry["address"], code)
    start = pair_start(entry)
    zero = entry["zero"]
    watch_start = start - 4
    watch_end = zero + 12
    watch_size = watch_end - watch_start
    rng = random.Random(case_seed)
    uc.mem_write(watch_start, initial_region(rng, watch_size, pattern))
    writes: set[int] = set()

    def on_write(machine, access, address, size, value, data):
        writes.update(range(address, address + size))

    hook = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10 | ((nzcv & 0xF) << 28))
    for index in range(13):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{index}"), rng.getrandbits(32))
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP)
    try:
        uc.emu_start(entry["address"], TRAP, count=64)
    finally:
        uc.hook_del(hook)
    return {
        "memory": bytes(uc.mem_read(watch_start, watch_size)),
        "write_bytes": writes,
        "registers": {**{f"r{i}": uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)},
                      "sp": uc.reg_read(arm.UC_ARM_REG_SP),
                      "pc": uc.reg_read(arm.UC_ARM_REG_PC),
                      "cpsr": uc.reg_read(arm.UC_ARM_REG_CPSR)},
        "watch_start": watch_start,
    }


def compare_entry(image: bytes, entry: dict, candidate: bytes,
                  seed: int, samples: int) -> tuple[list[dict], dict | None]:
    original = original_entry(image, entry)
    allowed = {address + i for address in expected_words(entry) for i in range(4)}
    stack_scratch = set(range(STACK_TOP - 0x1000, STACK_TOP))
    result, first = [], None
    for index in range(samples):
        pattern, nzcv = index % 5, index % 16
        case_seed = seed + index * 0x9E3779B1 + entry["address"]
        ref = run_one(original, entry, case_seed, pattern, nzcv)
        got = run_one(candidate, entry, case_seed, pattern, nzcv)
        ref_values = {a: struct.unpack_from("<I", ref["memory"], a - ref["watch_start"])[0]
                      for a in expected_words(entry)}
        expected = expected_words(entry)
        ref_writes = ref["write_bytes"] - stack_scratch
        got_writes = got["write_bytes"] - stack_scratch
        unexpected = (ref["write_bytes"] | got["write_bytes"]) - allowed - stack_scratch
        passed = (ref["memory"] == got["memory"] and ref["registers"] == got["registers"] and
                  ref_values == expected and ref_writes == allowed and got_writes == allowed and
                  not unexpected)
        row = {"index": index, "pattern": pattern, "nzcv_input": nzcv,
               "passed": passed, "write_byte_count": len(got_writes),
               "unexpected_writes": sorted(hex(x) for x in unexpected)}
        result.append(row)
        if not passed and first is None:
            first = {"case": row, "original_values": {hex(k): hex(v) for k, v in ref_values.items()},
                     "expected_values": {hex(k): hex(v) for k, v in expected.items()},
                     "original_registers": ref["registers"], "candidate_registers": got["registers"],
                     "original_writes": sorted(hex(x) for x in ref["write_bytes"]),
                     "candidate_writes": sorted(hex(x) for x in got["write_bytes"])}
    return result, first


def negative_controls(image: bytes, source_text: str, seed: int, samples: int,
                      output_dir: Path) -> list[dict]:
    folder = output_dir / "negative-controls"
    folder.mkdir()
    results = []
    for entry in ENTRIES:
        address = pair_start(entry)
        anchor = f"*reinterpret_cast<u32*>(0x{address:08X}u) = 0xFFFFFFFFu;"
        if anchor not in source_text:
            raise ValueError(f"missing negative-control anchor for {entry['name']}: {anchor}")
        mutant = folder / f"mutant_{entry['address']:08x}.cpp"
        mutant.write_text(source_text.replace(anchor, anchor.replace("0xFFFFFFFFu", "0u"), 1),
                          encoding="utf-8")
        codes, _ = compile_symbols(mutant, mutant.with_suffix(".o"))
        cases, _ = compare_entry(image, entry, codes[entry["name"]], seed, samples)
        detected = not all(case["passed"] for case in cases)
        if not detected:
            raise AssertionError(f"negative control escaped detection: {entry['name']}")
        results.append({"entry": hex(entry["address"]), "detected": detected,
                        "first_counterexample": next(row["index"] for row in cases if not row["passed"])})
    return results


def validate(output_dir: Path, seed: int, samples: int, do_negative_controls: bool) -> dict:
    if output_dir.exists():
        raise FileExistsError(f"output directory must be fresh: {output_dir}")
    output_dir.mkdir(parents=True)
    image = CODE_BIN.read_bytes()
    if sha256(image) != REFERENCE_SHA256:
        raise ValueError("pinned code.bin hash mismatch")
    game = json.loads(GAME_INFO.read_text(encoding="utf-8"))
    if game.get("code_sha256") != REFERENCE_SHA256:
        raise ValueError("game_info reference hash mismatch")
    for entry in ENTRIES:
        original_entry(image, entry)
    codes, object_hash = compile_symbols(SOURCE, output_dir / "family.o")
    per_entry = []
    for entry in ENTRIES:
        cases, first = compare_entry(image, entry, codes[entry["name"]], seed, samples)
        if first:
            raise AssertionError(f"differential failed at {entry['address']:#x}: {first}")
        per_entry.append({"address": hex(entry["address"]), "extent": EXTENT,
                          "callable_instruction_size": 0x24,
                          "original_literals": [hex(x) for x in entry["literals"]],
                          "initialized_words": {hex(k): hex(v) for k, v in expected_words(entry).items()},
                          "direct_callers": caller_inventory(image, entry["address"]),
                          "candidate_size": len(codes[entry["name"]]),
                          "candidate_sha256": sha256(codes[entry["name"]]),
                          "cases": len(cases), "passed_cases": sum(c["passed"] for c in cases),
                          "all_cases_passed": all(c["passed"] for c in cases),
                          "first_counterexample": first})
    controls = (negative_controls(image, SOURCE.read_text(encoding="utf-8"), seed, samples, output_dir)
                if do_negative_controls else [])
    report = {
        "schema_version": 1,
        "task": "h18-003f32f4-family",
        "reference_sha256": REFERENCE_SHA256,
        "source_sha256": sha256(SOURCE.read_bytes()),
        "object_sha256": object_hash,
        "seed": seed,
        "samples_per_entry": samples,
        "entry_count": len(ENTRIES),
        "entries": per_entry,
        "all_entries_passed": all(item["all_cases_passed"] for item in per_entry),
        "negative_controls": controls,
        "negative_controls_detected": (len(controls) == len(ENTRIES) and
                                        all(item["detected"] for item in controls)) if do_negative_controls else None,
        "limitations": [
            "Code.bin scans find no aligned direct BL or exact aligned pointer word for these entries; startup/registration callers are not established.",
            "Only bounded initializer memory effects and ABI state are differentially checked in Unicorn; no global object meanings, caller composition, or runtime timing is proven.",
            "Compiler stack scratch below the incoming SP is allowed; persistent writes outside each entry's four expected words are rejected.",
        ],
    }
    (output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--no-negative-controls", action="store_true")
    args = parser.parse_args(argv)
    report = validate(args.output_dir, args.seed, args.samples, not args.no_negative_controls)
    print(json.dumps({"report": str((args.output_dir / "report.json").resolve()),
                      "entries": report["entry_count"],
                      "all_entries_passed": report["all_entries_passed"],
                      "negative_controls_detected": report["negative_controls_detected"]}, indent=2))
    return 0 if report["all_entries_passed"] and report["negative_controls_detected"] is not False else 1


if __name__ == "__main__":
    raise SystemExit(main())
