#!/usr/bin/env python3
"""Focused production-source differential check for 0x00131414.

The checked domain is aligned writable ordinary RAM. This is not a loader or
whole-game runtime test.
"""
from __future__ import annotations

import argparse
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

FUNC = 0x00131414
CALL_START = 0x00121D14
CALL_STOP = 0x00121D24
TEXT = 0x00100000
TEXT_SIZE = 0x00400000
DATA = 0x02000000
DATA_SIZE = 0x1000
STACK = 0x08000000
STACK_SIZE = 0x2000
SP = STACK + 0x1000
INJECT = 0x01000000
RETURN = INJECT + 0x1000
IMAGE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"


def verify_source(root: Path = ROOT) -> dict:
    root = Path(root)
    source = (root / "src/engine/leaf_matching.cpp").read_text(encoding="utf-8")
    header = (root / "include/engine/leaf_matching.h").read_text(encoding="utf-8")
    caller = (root / "src/engine/leaf_batch34_c.cpp").read_text(encoding="utf-8")
    pattern = re.compile(
        r"u8\*\s+ui_func_00131414\s*\(\s*u8\*\s*p\s*,\s*u32\s+a\s*,\s*u32\s+b\s*\)\s*\{(?P<body>.*?)\}",
        re.DOTALL,
    )
    match = pattern.search(source)
    if not match:
        raise ValueError("production definition has an unexpected signature")
    body = match.group("body")
    if "asm" in body or re.search(r"\w+\s*\[\s*[01]\s*\]", body):
        raise ValueError("production stores must not use array indexing")
    if not re.search(r"\*\s*reinterpret_cast\s*<\s*u32\s*\*>\s*\(\s*p\s*\+\s*4\s*\)\s*=\s*a\s*;", body):
        raise ValueError("production body must independently store a at p+4")
    if not re.search(r"\*\s*reinterpret_cast\s*<\s*u32\s*\*>\s*\(\s*p\s*\+\s*8\s*\)\s*=\s*b\s*;", body):
        raise ValueError("production body must independently store b at p+8")
    if not re.search(r"return\s+p\s*\+\s*4\s*;", body):
        raise ValueError("production body must return p+4")
    if not re.search(r"u8\*\s+ui_func_00131414\s*\(\s*u8\*\s*p\s*,\s*u32\s+a\s*,\s*u32\s+b\s*\)", header):
        raise ValueError("public header declaration does not match production definition")
    if not re.search(r'extern\s+"C"\s+u8\*\s+AsdFont_AttachResource\s*\(\s*u8\*\s+info\s*,\s*u32\s+data\s*,\s*u32\s+chunk\s*\)\s*asm\("ui_func_00131414"\)', caller):
        raise ValueError("parser caller declaration does not match pointer return ABI")
    state = re.search(r"struct\s+AsdFontParseState\s*\{(?P<body>.*?)\};", caller, re.DOTALL)
    if not state or not all(re.search(rf"u32\s+{field}\s*;", state.group("body"))
                            for field in ("type", "data", "chunk")):
        raise ValueError("recovered parser state words are missing")
    asserts = [
        "offsetof(AsdFontParseState, type) == 0x00",
        "offsetof(AsdFontParseState, data) == 0x04",
        "offsetof(AsdFontParseState, chunk) == 0x08",
        "sizeof(AsdFontParseState) == 0x0C",
    ]
    if not all(item in caller for item in asserts):
        raise ValueError("parser state layout assertions are missing")
    return {"symbol": "ui_func_00131414", "stores": [4, 8],
            "independent_typed_stores": True,
            "return_offset": 4, "caller_declaration_return": "u8*",
            "caller_state_layout": {"type": 0, "data": 4, "chunk": 8, "size": 12}}


def _compile(root: Path, output: Path, source: Path, obj_name: str) -> tuple[dict[str, bytes], str]:
    obj = output / obj_name
    result = compile_tu_armv6k(source, obj, root)
    if result.returncode:
        raise RuntimeError(result.stderr or f"compile failed: {source}")
    extracted = extract_elf_functions_detailed(obj)
    return {name: code for name, (code, relocs) in extracted.items() if not relocs}, hashlib.sha256(obj.read_bytes()).hexdigest()


def _compile_candidate(root: Path, output: Path) -> tuple[bytes, str, str]:
    source = root / "src/engine/leaf_matching.cpp"
    symbols, object_hash = _compile(root, output, source, "leaf_matching.production.o")
    if "ui_func_00131414" not in symbols:
        raise ValueError("production object did not contain relocation-free ui_func_00131414")
    code = symbols["ui_func_00131414"]
    validate_leaf(code)
    return code, hashlib.sha256(source.read_bytes()).hexdigest(), object_hash


def _execute(image: bytes, *, entry: int, code: bytes | None, registers: list[int],
             data: bytes, stack: bytes, start: int | None = None,
             stop: int = RETURN, budget: int = 96) -> dict:
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
        uc.mem_write(entry, arm_branch(entry, INJECT))
    uc.mem_write(DATA, data)
    uc.mem_write(STACK, stack)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    for index, value in enumerate(registers):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{index}"), value & 0xFFFFFFFF)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    writes: set[int] = set()
    stopped = False

    def on_write(_uc, access, address, size, _value, _user):
        if access == unicorn.UC_MEM_WRITE:
            writes.update(range(address, address + size))

    def on_code(_uc, address, _size, _user):
        nonlocal stopped
        if address == stop:
            stopped = True
            _uc.emu_stop()

    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
    fault = None
    try:
        uc.emu_start(entry if start is None else start, 0, count=budget)
    except unicorn.UcError as error:
        fault = str(error)
    state = {f"r{i}": uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(13)}
    state.update({"sp": uc.reg_read(arm.UC_ARM_REG_SP), "lr": uc.reg_read(arm.UC_ARM_REG_LR),
                  "pc": uc.reg_read(arm.UC_ARM_REG_PC),
                  "cpsr": uc.reg_read(arm.UC_ARM_REG_CPSR)})
    return {"state": state, "data": bytes(uc.mem_read(DATA, DATA_SIZE)),
            "stack": bytes(uc.mem_read(STACK, STACK_SIZE)),
            "writes": sorted(writes), "stopped": stopped, "fault": fault}


def _comparison(original: dict, candidate: dict) -> str | None:
    if original["fault"] or candidate["fault"]:
        return f"execution fault: original={original['fault']!r}, candidate={candidate['fault']!r}"
    if not original["stopped"] or not candidate["stopped"]:
        return "execution did not reach the expected continuation within budget"
    for key in ("state", "data", "stack", "writes"):
        if original[key] != candidate[key]:
            if key == "data":
                pos = next(i for i, (a, b) in enumerate(zip(original[key], candidate[key])) if a != b)
                return f"data first differs at +0x{pos:x}: {original[key][pos]:02x}!={candidate[key][pos]:02x}"
            return f"{key} differs"
    return None


def _case(seed: int, index: int) -> tuple[list[int], bytes, bytes]:
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    address = DATA + 0x100
    a, b = ((0, 0), (0xFFFFFFFF, 1), (0x80000000, 0x7FFFFFFF),
            (0x12345678, 0x89ABCDEF))[index % 4]
    if index >= 4:
        a, b = rng.getrandbits(32), rng.getrandbits(32)
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0:3] = [address, a, b]
    stack = bytearray(rng.randbytes(STACK_SIZE))
    return registers, bytes(data), bytes(stack)


def _run_caller(image: bytes, code: bytes | None, seed: int) -> tuple[dict, dict]:
    rng = random.Random(seed ^ 0x00121D14)
    data = bytearray(rng.randbytes(DATA_SIZE))
    info, resource, found = DATA + 0x100, DATA + 0x200, DATA + 0x300
    stack = bytearray(rng.randbytes(STACK_SIZE))
    struct.pack_into("<I", stack, SP - STACK, info)
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[4], registers[5] = resource, found
    original = _execute(image, entry=FUNC, code=None, registers=registers,
                        data=bytes(data), stack=bytes(stack), start=CALL_START,
                        stop=CALL_STOP)
    candidate = _execute(image, entry=FUNC, code=code, registers=registers,
                          data=bytes(data), stack=bytes(stack), start=CALL_START,
                          stop=CALL_STOP)
    return original, candidate


def run(code_path: Path, output: Path, *, seed: int = 7, samples: int = 256) -> dict:
    root = ROOT
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    source_check = verify_source(root)
    image = Path(code_path).read_bytes()
    image_hash = hashlib.sha256(image).hexdigest()
    if image_hash != IMAGE_SHA256:
        raise ValueError(f"pinned original hash mismatch: {image_hash}")
    code, source_hash, object_hash = _compile_candidate(root, output)
    outcomes = []
    for index in range(samples + 4):
        registers, data, stack = _case(seed, index)
        original = _execute(image, entry=FUNC, code=None, registers=registers,
                            data=data, stack=stack)
        candidate = _execute(image, entry=FUNC, code=code, registers=registers,
                             data=data, stack=stack)
        reason = _comparison(original, candidate)
        outcomes.append({"index": index, "case": "directed" if index < 4 else "randomized",
                         "passed": reason is None, "reason": reason})
    mutant_source = output / "wrong_second_store.cpp"
    mutant_source.write_text(
        '#include "types.h"\nextern "C" u8* mutant(u8* p, u32 a, u32 b) { '
        'u32* fields = reinterpret_cast<u32*>(p + 4); fields[0] = a; '
        'fields[1] = b ^ 1; return p + 4; }\n', encoding="utf-8")
    mutant_symbols, mutant_object_hash = _compile(root, output, mutant_source, "wrong_second_store.o")
    mutant = mutant_symbols.get("mutant")
    if mutant is None:
        raise ValueError("negative-control symbol missing from object")
    validate_leaf(mutant)
    registers, data, stack = _case(seed, 1)
    original = _execute(image, entry=FUNC, code=None, registers=registers, data=data, stack=stack)
    bad = _execute(image, entry=FUNC, code=mutant, registers=registers, data=data, stack=stack)
    control_reason = _comparison(original, bad)

    original_caller, candidate_caller = _run_caller(image, code, seed)
    caller_reason = _comparison(original_caller, candidate_caller)
    report = {
        "schema": 1, "address": hex(FUNC), "seed": seed, "randomized_samples": samples,
        "passed": all(item["passed"] for item in outcomes) and control_reason is not None and caller_reason is None,
        "reference_sha256": image_hash, "source_sha256": source_hash,
        "object_sha256": object_hash, "candidate_bytes": len(code),
        "candidate_sha256": hashlib.sha256(code).hexdigest(),
        "candidate_differs_from_original": code != image[FUNC - TEXT:FUNC - TEXT + 12],
        "function": {"passed": all(item["passed"] for item in outcomes),
                     "cases": len(outcomes), "results": outcomes,
                     "candidate_bytes": len(code),
                     "original": image[FUNC - TEXT:FUNC - TEXT + 12].hex(),
                     "candidate": code.hex()},
        "negative_controls": [{"name": "second_store_xor_1",
                               "detected": control_reason is not None,
                               "reason": control_reason}],
        "caller_window": {"start": hex(CALL_START), "call": hex(0x00121D1C),
                          "stop": hex(CALL_STOP), "passed": caller_reason is None,
                          "reason": caller_reason,
                          "return": "parser sets r0=1 at 0x00121D20; stop before 0x00121D24",
                          "negative_control": {"name": "second_store_xor_1",
                                               "object_sha256": mutant_object_hash,
                                               "detected": control_reason is not None,
                                               "reason": control_reason}},
        "source_contract": source_check,
        "limitations": [
            "Differential domain is non-null, four-byte-aligned pointers to 12 writable bytes in ordinary RAM.",
            "No MMIO, unaligned pointers, invalid memory, concurrent observation, exceptions, or partial-fault ordering tested.",
            "Caller composition executes the real 0x00121D14..0x00121D24 argument setup, call, and success continuation with representative prepared state; it does not run the parser or loader.",
            "No game/runtime claim; byte identity is diagnostic only.",
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
    args = parser.parse_args()
    report = run(args.code, args.output, seed=args.seed, samples=args.samples)
    print(json.dumps({"passed": report["passed"], "report": str(args.output / "report.json")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
