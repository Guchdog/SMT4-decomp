#!/usr/bin/env python3
"""Production-source differential check for signed byte getter 0x00121d70."""
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

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import arm_branch, validate_leaf

FUNC = 0x00121D70
FUNC_SIZE = 12
CALL_START = 0x00110F3C
GLOBAL_PTR = 0x00433158
CALL_STOPS = (0x00110F50, 0x00111008)
TEXT = 0x00100000
TEXT_SIZE = 0x00400000
DATA = 0x02000000
DATA_SIZE = 0x1000
STACK = 0x08000000
STACK_SIZE = 0x2000
SP = STACK + 0x1000
INJECT = 0x01000000
RETURN = INJECT + 0x1000
REFERENCE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
ORIGINAL_BYTES = bytes.fromhex("030c80e2d003d0e11eff2fe1")


def verify_source(root: Path = ROOT) -> dict:
    root = Path(root)
    source = (root / "src/engine/leaf_matching.cpp").read_text(encoding="utf-8")
    header = (root / "include/engine/leaf_matching.h").read_text(encoding="utf-8")
    ledger_path = root / "config/functions.csv"
    match = re.search(
        r'extern\s+"C"\s+s32\s+func_00121d70\s*\(\s*const\s+u8\s*\*\s*p\s*\)\s*\{(?P<body>.*?)\}',
        source, re.DOTALL)
    if not match:
        raise ValueError("missing production definition with C-linkage s32(const u8*) ABI")
    body = match.group("body")
    if "asm" in body:
        raise ValueError("production body still contains assembly")
    if not re.search(r"reinterpret_cast\s*<\s*const\s+unsigned\s+char\s*\*\s*>\s*\(\s*p\s*\)\s*\[\s*0x330\s*\]", body):
        raise ValueError("production must read byte +0x330 through an alias-safe character pointer")
    if not re.search(r"return\s+byte\s*<\s*0x80u\s*\?\s*static_cast\s*<\s*s32\s*>\s*\(\s*byte\s*\)\s*:\s*static_cast\s*<\s*s32\s*>\s*\(\s*byte\s*\)\s*-\s*0x100\s*;", body):
        raise ValueError("production must explicitly sign-extend the byte to s32")
    if not re.search(r"s32\s+func_00121d70\s*\(\s*const\s+u8\s*\*\s*p\s*\)", header):
        raise ValueError("header declaration does not match the production function ABI")
    with ledger_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    row = next((item for item in rows if int(item["address"], 16) == FUNC), None)
    if row is None or int(row["size"]) != FUNC_SIZE or row["status"] != "non_matching":
        raise ValueError("ledger must retain the 12-byte non_matching classification")
    return {"symbol": "func_00121d70", "byte_offset": 0x330,
            "return_type": "s32", "explicit_sign_extension": True,
            "ledger_status": row["status"], "ledger_size": int(row["size"]),
            "alias_safe_access": "const unsigned char object-representation access"}


def _compile_tu(root: Path, source: Path, obj: Path) -> tuple[dict[str, tuple[bytes, tuple]], str]:
    result = compile_tu_armv6k(source, obj, root)
    if result.returncode:
        raise RuntimeError(result.stderr or f"ARMv6K compile failed: {source}")
    functions = extract_elf_functions_detailed(obj)
    return functions, hashlib.sha256(obj.read_bytes()).hexdigest()


def _compile_symbols(root: Path, output: Path) -> tuple[bytes, dict[str, bytes], dict]:
    source = root / "src/engine/leaf_matching.cpp"
    functions, object_hash = _compile_tu(root, source, output / "leaf_matching.production.o")
    symbol = "func_00121d70"
    if symbol not in functions:
        raise ValueError(f"production symbol missing from object: {symbol}")
    code, relocations = functions[symbol]
    if relocations:
        raise ValueError(f"unexpected relocations for {symbol}: {relocations}")
    validate_leaf(code)

    mutant_source = output / "signed_byte_negative_controls.cpp"
    mutant_source.write_text(
        '#include "types.h"\n'
        'extern "C" u32 mutant_unsigned(const u8* p) { '
        'return reinterpret_cast<const unsigned char*>(p)[0x330]; }\n'
        'extern "C" s32 mutant_wrong_offset(const u8* p) { '
        'const unsigned char byte = reinterpret_cast<const unsigned char*>(p)[0x331]; '
        'return byte < 0x80u ? static_cast<s32>(byte) : static_cast<s32>(byte)-0x100; }\n',
        encoding="utf-8")
    mutants, mutant_object_hash = _compile_tu(root, mutant_source,
                                               output / "signed_byte_negative_controls.o")
    result_mutants: dict[str, bytes] = {}
    for name in ("mutant_unsigned", "mutant_wrong_offset"):
        if name not in mutants:
            raise ValueError(f"negative control missing from object: {name}")
        mutant_code, mutant_relocations = mutants[name]
        if mutant_relocations:
            raise ValueError(f"unexpected relocations for negative control {name}")
        validate_leaf(mutant_code)
        result_mutants[name] = mutant_code
    return code, result_mutants, {
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "object_sha256": object_hash,
        "mutant_source_sha256": hashlib.sha256(mutant_source.read_bytes()).hexdigest(),
        "mutant_object_sha256": mutant_object_hash,
    }


def _execute(image: bytes, *, code: bytes | None, registers: list[int], data: bytes,
             stack: bytes, start: int = FUNC, stops: tuple[int, ...] = (RETURN,),
             global_pointer: int | None = None, budget: int = 256) -> dict:
    import unicorn
    from unicorn import arm_const as arm

    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
    uc.mem_map(TEXT, TEXT_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
    uc.mem_write(TEXT, image)
    uc.mem_map(INJECT, 0x2000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
    uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    if code is not None:
        validate_leaf(code)
        uc.mem_write(INJECT, code)
        uc.mem_write(FUNC, arm_branch(FUNC, INJECT))
    uc.mem_write(DATA, data)
    uc.mem_write(STACK, stack)
    if global_pointer is not None:
        uc.mem_write(GLOBAL_PTR, struct.pack("<I", global_pointer))

    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    for index, value in enumerate(registers):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{index}"), value & 0xFFFFFFFF)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    d_regs = tuple(getattr(arm, f"UC_ARM_REG_D{i}") for i in range(8, 16))
    rng = random.Random(registers[0] ^ registers[1] ^ registers[2] ^ start)
    d_values = tuple(rng.getrandbits(64) for _ in d_regs)
    for reg, value in zip(d_regs, d_values):
        uc.reg_write(reg, value)

    accesses: set[tuple[str, int, int]] = set()
    stopped_at = None

    def on_memory(_uc, access, address, size, _value, _user):
        kind = "write" if access == unicorn.UC_MEM_WRITE else "read"
        if DATA <= address < DATA + DATA_SIZE or STACK <= address < STACK + STACK_SIZE or GLOBAL_PTR <= address < GLOBAL_PTR + 4:
            accesses.add((kind, address, size))

    def on_code(_uc, address, _size, _user):
        nonlocal stopped_at
        if address in stops:
            stopped_at = address
            _uc.emu_stop()

    uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE, on_memory)
    uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
    fault = None
    try:
        uc.emu_start(start, 0, count=budget)
    except unicorn.UcError as error:
        fault = str(error)
    arm_regs = {f"r{i}": uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(13)}
    arm_regs.update({"sp": uc.reg_read(arm.UC_ARM_REG_SP), "lr": uc.reg_read(arm.UC_ARM_REG_LR),
                     "pc": uc.reg_read(arm.UC_ARM_REG_PC), "cpsr": uc.reg_read(arm.UC_ARM_REG_CPSR)})
    return {
        "state": arm_regs,
        "d8_d15": tuple(uc.reg_read(reg) for reg in d_regs),
        "data": bytes(uc.mem_read(DATA, DATA_SIZE)),
        "stack": bytes(uc.mem_read(STACK, STACK_SIZE)),
        "global_pointer": struct.unpack("<I", uc.mem_read(GLOBAL_PTR, 4))[0],
        "accesses": sorted(accesses), "stopped_at": stopped_at, "fault": fault,
    }


def _compare(original: dict, candidate: dict, *, caller_window: bool = False) -> str | None:
    if original["fault"] or candidate["fault"]:
        return f"fault original={original['fault']!r} candidate={candidate['fault']!r}"
    if original["stopped_at"] is None or candidate["stopped_at"] is None:
        return "did not reach expected return/continuation within instruction budget"
    old_state, new_state = dict(original["state"]), dict(candidate["state"])
    # r1-r3/r12 are caller-saved, and condition flags are not an isolated
    # function ABI result. The caller window compares the flags after its real
    # `cmp r0,#0`, which are consumed by the following conditional branch.
    relevant = ["r0", "r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11", "sp", "lr", "pc"]
    if caller_window:
        relevant.append("cpsr")
    else:
        relevant.append("cpsr")
        old_state["cpsr"] &= 0x1F
        new_state["cpsr"] &= 0x1F
    old_state = {key: old_state[key] for key in relevant}
    new_state = {key: new_state[key] for key in relevant}
    old_values, new_values = dict(original), dict(candidate)
    old_values["state"], new_values["state"] = old_state, new_state
    for key in ("state", "d8_d15", "data", "stack", "global_pointer", "accesses", "stopped_at"):
        if old_values[key] != new_values[key]:
            if key == "data":
                index = next(i for i, (a, b) in enumerate(zip(original[key], candidate[key])) if a != b)
                return f"data differs at +0x{index:x}"
            return f"{key} differs"
    return None


def _data(seed: int, index: int, value: int) -> tuple[list[int], bytes, bytes, int]:
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    pointer = DATA + 0x100
    data = bytearray(rng.randbytes(DATA_SIZE))
    data[pointer - DATA + 0x330] = value & 0xFF
    data[pointer - DATA + 0x331] = (value ^ 0x5A) & 0xFF
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0] = pointer
    stack = rng.randbytes(STACK_SIZE)
    return registers, bytes(data), stack, pointer


def _run_pair(image: bytes, original_code: bytes | None, candidate_code: bytes | None,
              seed: int, index: int, value: int, *, caller: bool = False) -> tuple[dict, dict]:
    regs, data, stack, pointer = _data(seed, index, value)
    if caller:
        regs[5] = GLOBAL_PTR
        run_start = CALL_START
        stops = CALL_STOPS
        global_pointer = pointer
    else:
        run_start = FUNC
        stops = (RETURN,)
        global_pointer = None
    old = _execute(image, code=original_code, registers=regs, data=data, stack=stack,
                   start=run_start, stops=stops, global_pointer=global_pointer)
    new = _execute(image, code=candidate_code, registers=regs, data=data, stack=stack,
                   start=run_start, stops=stops, global_pointer=global_pointer)
    return old, new


def _reference_scan(image: bytes) -> dict:
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(image).hexdigest()
    if digest != REFERENCE_SHA256 or digest != game["code_sha256"]:
        raise ValueError("pinned reference image hash mismatch")
    text_start = int(game["segments"]["text"]["vaddr"], 16)
    text_size = int(game["segments"]["text"]["size"], 16)
    branch_refs = []
    for off in range(0, text_size - 3, 4):
        word = struct.unpack_from("<I", image, off)[0]
        site = text_start + off
        destination = None
        kind = None
        if word & 0x0F000000 == 0x0B000000:
            imm = word & 0xFFFFFF
            if imm & 0x800000:
                imm -= 1 << 24
            destination = site + 8 + imm * 4
            kind = "BL"
        elif word & 0xFE000000 == 0xFA000000:
            imm = word & 0xFFFFFF
            if imm & 0x800000:
                imm -= 1 << 24
            destination = site + 8 + imm * 4 + ((word >> 23) & 2)
            kind = "BLX"
        if destination is not None and FUNC <= destination < FUNC + FUNC_SIZE:
            branch_refs.append({"site": hex(site), "target": hex(destination), "kind": kind})
    pointer_refs = [hex(text_start + off) for off in range(0, len(image) - 3, 4)
                    if FUNC <= struct.unpack_from("<I", image, off)[0] < FUNC + FUNC_SIZE]
    original = image[FUNC - text_start:FUNC - text_start + FUNC_SIZE]
    if original != ORIGINAL_BYTES:
        raise ValueError("original function bytes changed")
    return {"reference_sha256": digest, "original_bytes": original.hex(),
            "direct_branch_refs": branch_refs, "aligned_pointer_words": pointer_refs}


def run(code_path: Path, output: Path, *, seed: int = 7, samples: int = 256,
        caller_samples: int = 256) -> dict:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    source_contract = verify_source(ROOT)
    image = Path(code_path).read_bytes()
    reference = _reference_scan(image)
    code, mutants, hashes = _compile_symbols(ROOT, output)
    outcomes = []
    values = list(range(256)) + [random.Random(seed ^ n).getrandbits(8) for n in range(samples)]
    for index, value in enumerate(values):
        old, new = _run_pair(image, None, code, seed, index, value)
        reason = _compare(old, new)
        outcomes.append({"index": index, "input_byte": value, "kind": "all-byte-values" if index < 256 else "randomized",
                         "passed": reason is None, "reason": reason})

    control_cases = (("unsigned_return", mutants["mutant_unsigned"], 0x80),
                     ("wrong_offset", mutants["mutant_wrong_offset"], 0x80))
    controls = []
    for index, (name, mutant, value) in enumerate(control_cases):
        old, bad = _run_pair(image, None, mutant, seed, 900 + index, value)
        reason = _compare(old, bad)
        controls.append({"name": name, "detected": reason is not None, "reason": reason,
                         "input_byte": value})

    caller_values = list(range(256)) + [random.Random((seed << 1) ^ n).getrandbits(8)
                                        for n in range(caller_samples)]
    caller_rows = []
    observed_stops: set[str] = set()
    for index, value in enumerate(caller_values):
        old, new = _run_pair(image, None, code, seed, 1200 + index, value, caller=True)
        reason = _compare(old, new, caller_window=True)
        if old["stopped_at"] is not None:
            observed_stops.add(hex(old["stopped_at"]))
        caller_rows.append({"index": index, "input_byte": value, "passed": reason is None,
                            "continuation": None if old["stopped_at"] is None else hex(old["stopped_at"]),
                            "reason": reason})
    caller_passed = all(row["passed"] for row in caller_rows) and observed_stops == {hex(x) for x in CALL_STOPS}
    report = {
        "schema": 1, "address": hex(FUNC), "seed": seed, "randomized_samples": samples,
        "caller_randomized_samples": caller_samples,
        "passed": all(item["passed"] for item in outcomes) and all(x["detected"] for x in controls) and caller_passed,
        "reference_sha256": reference["reference_sha256"],
        "source_sha256": hashes["source_sha256"], "object_sha256": hashes["object_sha256"],
        "mutant_source_sha256": hashes["mutant_source_sha256"],
        "mutant_object_sha256": hashes["mutant_object_sha256"],
        "candidate_bytes": len(code), "candidate_sha256": hashlib.sha256(code).hexdigest(),
        "candidate_bytes_match_original": code == ORIGINAL_BYTES,
        "function": {"passed": all(item["passed"] for item in outcomes),
                     "directed_cases": 256, "randomized_cases": samples,
                     "cases": len(outcomes), "results": outcomes,
                     "original_bytes": ORIGINAL_BYTES.hex(), "candidate_bytes": code.hex()},
        "negative_controls": controls,
        "caller_window": {"start": hex(CALL_START), "global_pointer_word": hex(GLOBAL_PTR),
                          "callee": hex(FUNC), "stops": [hex(x) for x in CALL_STOPS],
                          "continuations": sorted(observed_stops), "passed": caller_passed,
                          "cases": len(caller_rows), "results": caller_rows,
                          "input_setup": "Execute real ldr r5 literal at 0x00110f3c and ldr r0,[r5] at 0x00110f40; seed global word 0x00433158 to an aligned synthetic RAM object."},
        "source_contract": source_contract,
        "reference_scan": reference,
        "limitations": [
            "The C++ byte access requires a valid object representation spanning p+0x330; the known runtime pointee's type, lifetime, and extent are not established by the synthetic caller fixture.",
            "The caller test starts at 0x00110f3c and seeds the global pointer word to a synthetic aligned RAM fixture; it does not execute the runtime producer of 0x00433158.",
            "No MMIO, invalid/null pointer, inaccessible span, concurrent observation, exceptions, or fault-order behavior was tested.",
            "Static reference scan is aligned ARM BL/BLX and aligned image words; indirect, computed, Thumb, relocated, unaligned, or runtime-generated references are outside scope.",
            "No emulator, loader, or whole-game runtime comparison was performed."
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
    parser.add_argument("--caller-samples", type=int, default=256)
    args = parser.parse_args()
    report = run(args.code, args.output, seed=args.seed,
                 samples=args.samples, caller_samples=args.caller_samples)
    print(json.dumps({"passed": report["passed"], "report": str(args.output / "report.json")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
