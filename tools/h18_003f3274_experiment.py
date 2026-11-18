#!/usr/bin/env python3
"""Offline differential validation for the initializer entry at 0x003f3274."""
from __future__ import annotations

import argparse
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

FUNC_ADDR = 0x003F3274
FUNC_EXTENT = 0x80  # 0x70 bytes of instructions plus four literal-pool words.
ORIGINAL_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CODE_BIN = ROOT / "extracted/exefs/code.bin"
GAME_INFO = ROOT / "config/game_info.json"
SOURCE = ROOT / "experiments/semantic_equivalence/h18_003f3274_candidate.cpp"
SYMBOL = "candidate_003f3274"
MEM_BASE = 0x20000000
MEM_SIZE = 0x00010000
STACK_TOP = MEM_BASE + MEM_SIZE - 0x100
TRAP_ADDR = 0x001F0000
ARM_CODE_BASE = 0x00100000
ARM_CODE_SIZE = 0x00400000

WATCHED = ((0x00465070, 0x30), (0x004E39E0 + 0x1C0, 0x50))
WRITE_RANGES = ((0x00465080, 0x10), (0x004E39E0 + 0x1D4, 0x2C))
EXPECTED_STORES = {
    0x00465080: 0xFFFFFFFF,
    0x00465084: 0xFFFFFFFF,
    0x00465088: 0,
    0x0046508C: 0,
    0x004E3BB4: 0x00100000,
    0x004E3BB8: 0x00000800,
    0x004E3BBC: 0x00080000,
    0x004E3BC0: 0x00000080,
    0x004E3BC4: 0x00080000,
    0x004E3BC8: 0,
    0x004E3BCC: 0x00000500,
    0x004E3BD0: 0,
    0x004E3BD4: 0,
    0x004E3BD8: 0x00008058,
    0x004E3BDC: 0x00008051,
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def original_function(image: bytes) -> bytes:
    offset = FUNC_ADDR - ARM_CODE_BASE
    code = image[offset : offset + FUNC_EXTENT]
    if len(code) != FUNC_EXTENT:
        raise ValueError("original image is too short for the 0x003f3274 entry")
    words = struct.unpack_from("<4I", code, 0x70)
    if words != (0x00465080, 0x00465088, 0x004E39E0, 0x00008058):
        raise ValueError(f"unexpected 0x003f3274 literal pool: {words!r}")
    if struct.unpack_from("<I", code, 0x6C)[0] != 0xE12FFF1E:
        raise ValueError("expected ARM BX LR at offset 0x6c")
    return code


def caller_inventory(image: bytes) -> dict:
    branches = []
    pointers = []
    for offset in range(0, len(image) - 3, 4):
        word = struct.unpack_from("<I", image, offset)[0]
        site = ARM_CODE_BASE + offset
        if word == FUNC_ADDR:
            pointers.append(hex(site))
        if (word & 0x0F000000) == 0x0B000000:
            displacement = word & 0x00FFFFFF
            if displacement & 0x00800000:
                displacement -= 0x01000000
            target = site + 8 + displacement * 4
            if target == FUNC_ADDR:
                branches.append(hex(site))
    return {"aligned_arm_bl_sites": branches, "aligned_pointer_words": pointers}


def compile_symbol(source_path: Path, object_path: Path) -> tuple[bytes, str]:
    result = compile_tu_armv6k(source_path, object_path, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "ARMv6K candidate compilation failed")
    symbols = extract_elf_functions_detailed(object_path)
    if SYMBOL not in symbols:
        raise ValueError(f"candidate symbol missing: {SYMBOL}")
    code, relocations = symbols[SYMBOL]
    if relocations:
        raise ValueError(f"candidate has unsupported relocations: {relocations}")
    if len(code) < 4 or len(code) > 256:
        raise ValueError(f"unexpected candidate code size: {len(code)}")
    return code, sha256(object_path.read_bytes())


def initial_bytes(rng: random.Random, length: int, pattern: int) -> bytes:
    if pattern == 0:
        return bytes(length)
    if pattern == 1:
        return bytes([0xFF]) * length
    if pattern == 2:
        return bytes([0xA5]) * length
    if pattern == 3:
        return bytes([0x5A]) * length
    return bytes(rng.getrandbits(8) for _ in range(length))


def run_one(code: bytes, case_seed: int, pattern: int, nzcv: int) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(ARM_CODE_BASE, ARM_CODE_SIZE)
    uc.mem_map(MEM_BASE, MEM_SIZE)
    uc.mem_write(FUNC_ADDR, code)
    rng = random.Random(case_seed)
    for idx, (address, length) in enumerate(WATCHED):
        uc.mem_write(address, initial_bytes(rng, length, (pattern + idx) % 5))

    writes: set[int] = set()

    def on_write(machine, access, address, size, value, user_data):
        for byte_addr in range(address, address + size):
            writes.add(byte_addr)

    hook = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    # Select ARM user mode before writing banked SP/LR; switching mode afterward
    # would replace the configured return address with the banked user LR.
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10 | ((nzcv & 0xF) << 28))
    for reg in range(13):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{reg}"), rng.getrandbits(32))
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
    try:
        uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=128)
    finally:
        uc.hook_del(hook)

    memory = [bytes(uc.mem_read(address, length)) for address, length in WATCHED]
    registers = {
        **{f"r{i}": uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)},
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "pc": uc.reg_read(arm.UC_ARM_REG_PC),
        "cpsr": uc.reg_read(arm.UC_ARM_REG_CPSR),
    }
    return {"memory": memory, "writes": writes, "registers": registers}


def read_word_from_snapshot(snapshot: list[bytes], address: int) -> int:
    for (base, length), region in zip(WATCHED, snapshot):
        if base <= address and address + 4 <= base + length:
            offset = address - base
            return struct.unpack_from("<I", region, offset)[0]
    raise ValueError(f"address is outside watched memory: {address:#x}")


def run_pair(original: bytes, candidate: bytes, seed: int, samples: int) -> tuple[list[dict], dict | None]:
    cases = []
    first_mismatch = None
    for index in range(samples):
        pattern = index % 5
        nzcv = index % 16
        case_seed = seed + index * 0x9E3779B1
        ref = run_one(original, case_seed, pattern, nzcv)
        got = run_one(candidate, case_seed, pattern, nzcv)
        allowed = {address + i for address, length in WRITE_RANGES for i in range(length)}
        actual_allowed = ref["writes"] & allowed
        candidate_allowed = got["writes"] & allowed
        stack_scratch = set(range(STACK_TOP - 0x1000, STACK_TOP))
        unexpected = (ref["writes"] | got["writes"]) - allowed - stack_scratch
        ref_nonstack_writes = ref["writes"] - stack_scratch
        candidate_nonstack_writes = got["writes"] - stack_scratch
        contract_memory = all(read_word_from_snapshot(ref["memory"], address) == value
                              for address, value in EXPECTED_STORES.items())
        contract_writes = ref_nonstack_writes == allowed
        passed = (ref["memory"] == got["memory"] and
                  ref["registers"] == got["registers"] and
                  actual_allowed == candidate_allowed and not unexpected and
                  contract_memory and contract_writes and
                  ref_nonstack_writes == actual_allowed and
                  candidate_nonstack_writes == candidate_allowed)
        case = {"index": index, "pattern": pattern, "nzcv_input": nzcv,
                "passed": passed, "write_byte_count": len(candidate_allowed),
                "unexpected_write_bytes": sorted(hex(x) for x in unexpected)}
        cases.append(case)
        if not passed and first_mismatch is None:
            first_mismatch = {"case": case, "original_registers": ref["registers"],
                              "candidate_registers": got["registers"],
                              "original_write_bytes": sorted(hex(x) for x in ref["writes"]),
                              "candidate_write_bytes": sorted(hex(x) for x in got["writes"])}
    return cases, first_mismatch


def compile_negative_controls(source_text: str, original: bytes, seed: int, samples: int,
                              output_dir: Path) -> list[dict]:
    mutations = (
        ("first_pair_value", "first_pair[0] = 0xFFFFFFFFu;", "first_pair[0] = 0u;"),
        ("config_start", "config + 0x1D4u) = 0x00100000u", "config + 0x1D0u) = 0x00100000u"),
        ("config_size", "0x00000800u", "0x00000801u"),
        ("final_marker", "0x00008051u", "0x00008050u"),
        ("second_pair_value", "second_pair[1] = 0u;", "second_pair[1] = 1u;"),
    )
    results = []
    mutant_dir = output_dir / "negative-controls"
    mutant_dir.mkdir()
    for name, old, new in mutations:
        if old not in source_text:
            raise ValueError(f"negative-control anchor missing: {name}: {old}")
        mutant = mutant_dir / f"mutant_{name}.cpp"
        mutant.write_text(source_text.replace(old, new, 1), encoding="utf-8")
        code, _ = compile_symbol(mutant, mutant.with_suffix(".o"))
        cases, _ = run_pair(original, code, seed, samples)
        detected = not all(case["passed"] for case in cases)
        if not detected:
            raise AssertionError(f"negative control escaped detection: {name}")
        results.append({"name": name, "detected": detected,
                        "first_counterexample": next(case["index"] for case in cases if not case["passed"])})
    return results


def run_validation(output_dir: Path, seed: int = 7, samples: int = 20,
                   include_negative_controls: bool = True) -> dict:
    if output_dir.exists():
        raise FileExistsError(f"output directory must be fresh: {output_dir}")
    output_dir.mkdir(parents=True)
    image = CODE_BIN.read_bytes()
    if sha256(image) != ORIGINAL_SHA256:
        raise ValueError("pinned original code.bin hash mismatch")
    game = json.loads(GAME_INFO.read_text(encoding="utf-8"))
    if game.get("code_sha256") != ORIGINAL_SHA256:
        raise ValueError("game_info.json reference identity mismatch")
    original = original_function(image)
    object_path = output_dir / "candidate.o"
    candidate, object_hash = compile_symbol(SOURCE, object_path)
    source_text = SOURCE.read_text(encoding="utf-8")
    cases, first_mismatch = run_pair(original, candidate, seed, samples)
    if first_mismatch:
        raise AssertionError(f"candidate differential failed: {first_mismatch}")
    controls = (compile_negative_controls(source_text, original, seed, samples, output_dir)
                if include_negative_controls else [])
    report = {
        "schema_version": 1,
        "task": "h18-003f3274-candidate",
        "reference_sha256": ORIGINAL_SHA256,
        "source_sha256": sha256(SOURCE.read_bytes()),
        "object_sha256": object_hash,
        "candidate_sha256": sha256(candidate),
        "candidate_size": len(candidate),
        "entry": hex(FUNC_ADDR),
        "original_extent": FUNC_EXTENT,
        "seed": seed,
        "samples": samples,
        "case_results": cases,
        "all_cases_passed": all(case["passed"] for case in cases),
        "write_ranges": [{"address": hex(a), "size": n} for a, n in WRITE_RANGES],
        "caller_inventory": caller_inventory(image),
        "negative_controls": controls,
        "negative_controls_detected": len(controls) == 5 and all(row["detected"] for row in controls),
        "first_counterexample": first_mismatch,
        "limitations": [
            "Caller identity and startup dispatch for this initializer are not established by this differential harness.",
            "The run proves the statically recovered ordinary-RAM initialization effects and ABI state in Unicorn only; no runtime/emulator scenario was run.",
        ],
    }
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--no-negative-controls", action="store_true")
    args = parser.parse_args(argv)
    report = run_validation(args.output_dir, args.seed, args.samples, not args.no_negative_controls)
    print(json.dumps({"report": str((args.output_dir / "report.json").resolve()),
                      "all_cases_passed": report["all_cases_passed"],
                      "negative_controls_detected": report["negative_controls_detected"],
                      "samples": report["samples"]}, indent=2))
    return 0 if report["all_cases_passed"] and report["negative_controls_detected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
