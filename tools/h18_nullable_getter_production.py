#!/usr/bin/env python3
"""Compile and compare production nullable-pointer getter 0x0014ec5c."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import re
import struct
import sys
import capstone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.h18_signed_byte_production as execution
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import validate_leaf

FUNC = 0x0014EC5C
FUNC_SIZE = 12
FIELD_OFFSET = 0x1C
DATA = execution.DATA
DATA_SIZE = execution.DATA_SIZE
STACK_SIZE = execution.STACK_SIZE
CALLERS = (
    {"name": "engine_func_002a6228", "start": 0x002A6294,
     "nonnull_stop": 0x002A62A8, "null_stop": 0x002A62F4},
    {"name": "engine_func_002aeb78", "start": 0x002AEBD8,
     "nonnull_stop": 0x002AEBE8, "null_stop": 0x002AEC14},
)
REFERENCE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
ORIGINAL_BYTES = bytes.fromhex("000050e31c0090151eff2fe1")


def verify_source(root: Path = ROOT) -> dict:
    root = Path(root)
    source = (root / "src/engine/leaf_matching.cpp").read_text(encoding="utf-8")
    header = (root / "include/engine/leaf_matching.h").read_text(encoding="utf-8")
    if "NullablePointerRecord" in source:
        raise ValueError("do not introduce the experiment-only struct as a production type")
    match = re.search(
        r'extern\s+"C"\s+void\s*\*\s+engine_func_0014ec5c\s*\(\s*void\s*\*\s*p\s*\)\s*\{(?P<body>.*?)\}',
        source, re.DOTALL)
    if not match:
        raise ValueError("missing production definition with C-linkage void*(void*) ABI")
    body = match.group("body")
    if "asm" in body:
        raise ValueError("production body still contains assembly")
    if not re.search(r"if\s*\(\s*p\s*==\s*nullptr\s*\)\s*\{?\s*return\s+nullptr\s*;", body):
        raise ValueError("production body must return null before any null-pointer access")
    if not re.search(r"__builtin_memcpy_inline\s*\(\s*&\w+\s*,\s*field\s*,\s*sizeof\s*\(\s*\w+\s*\)\s*\)", body):
        raise ValueError("copy the +0x1c word from object representation with an inline four-byte memcpy")
    if not re.search(r"reinterpret_cast\s*<\s*void\s*\*>\s*\(\s*static_cast\s*<\s*std::uintptr_t\s*>\s*\(\s*\w+\s*\)\s*\)", body):
        raise ValueError("production must convert the loaded 32-bit target address back to void*")
    if "sizeof(void*) == sizeof(u32)" not in body:
        raise ValueError("production must assert 32-bit target pointer width")
    if not re.search(r"void\s*\*\s+engine_func_0014ec5c\s*\(\s*void\s*\*\s*p\s*\)", header):
        raise ValueError("header declaration does not match production ABI")
    with (root / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    row = next((item for item in rows if int(item["address"], 16) == FUNC), None)
    if row is None or int(row["size"]) != FUNC_SIZE or row["status"] != "non_matching":
        raise ValueError("ledger must retain the original 12-byte span as non_matching")
    return {"symbol": "engine_func_0014ec5c", "field_offset": FIELD_OFFSET,
            "input_type": "void*", "return_type": "void*", "null_guard": True,
            "field_representation": "u32 copied from object representation by inline four-byte memcpy",
            "ledger_status": row["status"], "ledger_size": int(row["size"])}


def _compile(root: Path, source: Path, obj: Path) -> tuple[dict[str, tuple[bytes, tuple]], str]:
    result = compile_tu_armv6k(source, obj, root)
    if result.returncode:
        raise RuntimeError(result.stderr or f"ARMv6K compile failed: {source}")
    return extract_elf_functions_detailed(obj), hashlib.sha256(obj.read_bytes()).hexdigest()


def _validate_local_leaf(code: bytes) -> None:
    """Allow the null guard's local conditional branch; reject external control flow."""
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    cs.detail = True
    instructions = list(cs.disasm(code, FUNC))
    if not instructions or sum(item.size for item in instructions) != len(code):
        raise ValueError("candidate has incomplete ARM disassembly")
    if instructions[-1].mnemonic != "bx" or instructions[-1].op_str != "lr":
        raise ValueError("candidate must return through bx lr")
    end = FUNC + len(code)
    for item in instructions[:-1]:
        if item.group(capstone.CS_GRP_CALL) or "pc" in item.op_str:
            raise ValueError("candidate contains a call or PC-relative operand")
        if item.group(capstone.CS_GRP_JUMP):
            if item.mnemonic.startswith("bx") and item.op_str == "lr":
                continue
            if not item.operands or item.operands[-1].type != capstone.arm.ARM_OP_IMM:
                raise ValueError("candidate has an unresolved branch target")
            if not FUNC <= item.operands[-1].imm < end:
                raise ValueError("candidate branch leaves its compiled function")


def _compile_production(output: Path) -> tuple[bytes, dict[str, bytes], dict]:
    source = ROOT / "src/engine/leaf_matching.cpp"
    funcs, object_hash = _compile(ROOT, source, output / "leaf_matching.production.o")
    symbol = "engine_func_0014ec5c"
    if symbol not in funcs:
        raise ValueError(f"production object lacks {symbol}")
    code, relocs = funcs[symbol]
    if relocs:
        raise ValueError(f"production function contains relocations: {relocs}")
    _validate_local_leaf(code)
    mutants_source = output / "nullable_getter_negative_controls.cpp"
    mutants_source.write_text(
        '#include "types.h"\n'
        'extern "C" void* mutant_base(void* p) { if (!p) return nullptr; return p; }\n'
        'extern "C" void* mutant_null(void* p) { if (!p) return reinterpret_cast<void*>(1); '
        'const unsigned char* b=reinterpret_cast<const unsigned char*>(p)+0x1c; '
        'u32 bits=0; __builtin_memcpy_inline(&bits,b,sizeof(bits)); '
        'return reinterpret_cast<void*>(static_cast<std::uintptr_t>(bits)); }\n',
        encoding="utf-8")
    mutants, mutant_object_hash = _compile(ROOT, mutants_source,
                                            output / "nullable_getter_negative_controls.o")
    mutant_codes: dict[str, bytes] = {}
    for name in ("mutant_base", "mutant_null"):
        if name not in mutants:
            raise ValueError(f"negative control missing: {name}")
        mutant, relocs = mutants[name]
        if relocs:
            raise ValueError(f"negative control has relocations: {name}")
        _validate_local_leaf(mutant)
        mutant_codes[name] = mutant
    return code, mutant_codes, {
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "object_sha256": object_hash,
        "mutant_source_sha256": hashlib.sha256(mutants_source.read_bytes()).hexdigest(),
        "mutant_object_sha256": mutant_object_hash,
    }


def _reference(image: bytes) -> dict:
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    if hashlib.sha256(image).hexdigest() != REFERENCE_SHA256 or REFERENCE_SHA256 != game["code_sha256"]:
        raise ValueError("pinned original image hash mismatch")
    text_start = int(game["segments"]["text"]["vaddr"], 16)
    text_size = int(game["segments"]["text"]["size"], 16)
    branches = []
    for off in range(0, text_size - 3, 4):
        word = struct.unpack_from("<I", image, off)[0]
        site, destination, kind = text_start + off, None, None
        if word & 0x0F000000 == 0x0B000000:
            imm = word & 0xFFFFFF
            if imm & 0x800000:
                imm -= 1 << 24
            destination, kind = site + 8 + imm * 4, "BL"
        elif word & 0xFE000000 == 0xFA000000:
            imm = word & 0xFFFFFF
            if imm & 0x800000:
                imm -= 1 << 24
            destination, kind = site + 8 + imm * 4 + ((word >> 23) & 2), "BLX"
        if destination is not None and FUNC <= destination < FUNC + FUNC_SIZE:
            branches.append({"site": hex(site), "target": hex(destination), "kind": kind})
    pointer_words = [hex(text_start + off) for off in range(0, len(image) - 3, 4)
                     if FUNC <= struct.unpack_from("<I", image, off)[0] < FUNC + FUNC_SIZE]
    code = image[FUNC - text_start:FUNC - text_start + FUNC_SIZE]
    if code != ORIGINAL_BYTES:
        raise ValueError("original function bytes changed")
    if [item["site"] for item in branches] != ["0x2a62a0", "0x2aebe0"]:
        raise ValueError(f"direct caller inventory changed: {branches}")
    return {"reference_sha256": REFERENCE_SHA256, "original_bytes": code.hex(),
            "direct_callers": branches, "aligned_pointer_words": pointer_words}


def _fixture(seed: int, index: int, input_pointer: bool, field_bits: int) -> tuple[list[int], bytes, bytes, int]:
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    pointer = DATA + 0x100
    data = bytearray(rng.randbytes(DATA_SIZE))
    struct.pack_into("<I", data, pointer - DATA + FIELD_OFFSET, field_bits & 0xFFFFFFFF)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = pointer if input_pointer else 0
    stack = rng.randbytes(STACK_SIZE)
    return regs, bytes(data), stack, pointer


def _direct_cases(seed: int, samples: int) -> list[dict]:
    cases = [
        {"label": "null_input", "kind": "null_input", "input_pointer": False, "field_bits": 0xDEADBEEF},
        {"label": "nonnull_zero_field", "kind": "nonnull_zero_field", "input_pointer": True, "field_bits": 0},
        {"label": "nonnull_low_pointer", "kind": "nonnull_pointer_field", "input_pointer": True, "field_bits": 1},
        {"label": "nonnull_data_pointer", "kind": "nonnull_pointer_field", "input_pointer": True, "field_bits": DATA + 0x200},
        {"label": "nonnull_high_bits", "kind": "nonnull_pointer_field", "input_pointer": True, "field_bits": 0xFFFFFFFF},
    ]
    rng = random.Random(seed)
    for i in range(samples):
        is_nonnull = bool(i & 1)
        cases.append({"label": f"random-{i}", "kind": "randomized",
                      "input_pointer": is_nonnull, "field_bits": rng.getrandbits(32)})
    return cases


def _run_one(image: bytes, code: bytes | None, seed: int, index: int,
             input_pointer: bool, field_bits: int, *, start: int = FUNC,
             stops: tuple[int, ...] = (execution.RETURN,)) -> dict:
    regs, data, stack, _pointer = _fixture(seed, index, input_pointer, field_bits)
    return execution._execute(image, code=code, registers=regs, data=data,
                              stack=stack, start=start, stops=stops)


def _compare_ram(original: dict, candidate: dict) -> str | None:
    """Compare ordinary-RAM read coverage independent of load width."""
    old, new = dict(original), dict(candidate)
    for result in (old, new):
        byte_coverage = set()
        for kind, address, size in result["accesses"]:
            if kind == "read":
                byte_coverage.update((kind, address + offset, 1) for offset in range(size))
            else:
                byte_coverage.add((kind, address, size))
        result["accesses"] = sorted(byte_coverage)
    return execution._compare(old, new)


def run(code_path: Path, output: Path, *, seed: int = 7, samples: int = 256,
        caller_randomized: int = 64) -> dict:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    source_contract = verify_source(ROOT)
    image = Path(code_path).read_bytes()
    reference = _reference(image)
    code, mutants, hashes = _compile_production(output)
    # The shared signed-byte executor only accepts branch-free leaves. This
    # contract needs the compiler's local null return; validate that control
    # flow here, then reuse the executor's register/memory comparison harness.
    # Its injection patch address is module-global and otherwise remains the
    # signed-byte function address; retarget it to this function before trials.
    execution.FUNC = FUNC
    execution.validate_leaf = _validate_local_leaf
    function_results = []
    for index, case in enumerate(_direct_cases(seed, samples)):
        old = _run_one(image, None, seed, index, case["input_pointer"], case["field_bits"])
        new = _run_one(image, code, seed, index, case["input_pointer"], case["field_bits"])
        reason = _compare_ram(old, new)
        function_results.append({**case, "passed": reason is None, "reason": reason})

    controls = []
    control_fixtures = (
        ("returns_base", mutants["mutant_base"], True, 0x00010000),
        ("nonnull_on_null", mutants["mutant_null"], False, 0),
    )
    for index, (name, mutant, input_pointer, field_bits) in enumerate(control_fixtures):
        old = _run_one(image, None, seed, 500 + index, input_pointer, field_bits)
        bad = _run_one(image, mutant, seed, 500 + index, input_pointer, field_bits)
        reason = _compare_ram(old, bad)
        controls.append({"name": name, "detected": reason is not None,
                         "reason": reason, "input_pointer_nonnull": input_pointer,
                         "field_bits": hex(field_bits)})

    caller_rows = []
    for ci, caller in enumerate(CALLERS):
        cases = [("null_guard", False, 0x12345678),
                 ("nonnull_guarded_call", True, DATA + 0x200)]
        rng = random.Random(seed ^ (ci * 0xA341316C))
        cases.extend((f"random-{i}", True, rng.getrandbits(32))
                     for i in range(caller_randomized))
        for case_index, (kind, input_pointer, field_bits) in enumerate(cases):
            regs, data, stack, _pointer = _fixture(seed + ci, case_index, input_pointer, field_bits)
            stops = (caller["nonnull_stop"], caller["null_stop"])
            old = execution._execute(image, code=None, registers=regs, data=data, stack=stack,
                                     start=caller["start"], stops=stops)
            new = execution._execute(image, code=code, registers=regs, data=data, stack=stack,
                                     start=caller["start"], stops=stops)
            reason = _compare_ram(old, new)
            expected_stop = caller["nonnull_stop"] if input_pointer else caller["null_stop"]
            if old["stopped_at"] != expected_stop or new["stopped_at"] != expected_stop:
                reason = reason or f"guard continuation mismatch: expected 0x{expected_stop:x}"
            caller_rows.append({"caller": caller["name"], "start": hex(caller["start"]),
                                "kind": kind, "input_pointer_nonnull": input_pointer,
                                "field_bits": hex(field_bits),
                                "continuation": None if old["stopped_at"] is None else hex(old["stopped_at"]),
                                "passed": reason is None, "reason": reason})

    direct_passed = all(row["passed"] for row in function_results)
    caller_passed = all(row["passed"] for row in caller_rows)
    control_passed = all(row["detected"] for row in controls)
    report = {
        "schema": 1, "address": hex(FUNC), "seed": seed,
        "random_samples": samples, "caller_randomized": caller_randomized,
        "passed": direct_passed and caller_passed and control_passed,
        "reference_sha256": reference["reference_sha256"],
        "source_sha256": hashes["source_sha256"], "object_sha256": hashes["object_sha256"],
        "candidate_bytes": len(code), "candidate_sha256": hashlib.sha256(code).hexdigest(),
        "candidate_bytes_match_original": code == ORIGINAL_BYTES,
        "function": {"passed": direct_passed, "directed_cases": 5,
                     "randomized_cases": samples, "cases": len(function_results),
                     "results": function_results, "original_bytes": ORIGINAL_BYTES.hex(),
                     "candidate_bytes": code.hex()},
        "callers": [{"name": caller["name"],
                     "start": hex(caller["start"]),
                     "cases": [row for row in caller_rows if row["caller"] == caller["name"]],
                     "passed": all(row["passed"] for row in caller_rows if row["caller"] == caller["name"]),
                     "continuations": sorted({row["continuation"] for row in caller_rows
                                               if row["caller"] == caller["name"]})}
                    for caller in CALLERS],
        "negative_controls": controls,
        "source_contract": source_contract,
        "reference_scan": reference,
        "limitations": [
            "No game object type or lifetime for the +0x1c word is recovered; production reads four bytes from a live object's representation and converts the 32-bit target address to void* under the ARMv6K pointer-width assertion.",
            "The two real callers guard null before the leaf and discard/overwrite its result; direct tests separately cover null input and null/non-null field values.",
            "Caller windows start at the guard after the preceding helper returns a prepared pointer; they do not execute those preceding functions or establish runtime object provenance.",
            "Tests use aligned ordinary RAM; invalid/unreadable pointers, MMIO, concurrency, exceptions, partial-fault ordering, loader/runtime, and whole-game behavior are not covered."
        ],
        "comparison_notes": [
            "For ordinary-RAM reads only, access comparison normalizes each read to covered bytes because compiler lowering may use one word load or multiple byte loads. Register/flag state, memory contents, writes, faults, and continuations remain compared."
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--caller-randomized", type=int, default=64)
    args = parser.parse_args()
    report = run(args.code, args.output, seed=args.seed,
                 samples=args.samples, caller_randomized=args.caller_randomized)
    print(json.dumps({"passed": report["passed"], "report": str(args.output / "report.json")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
