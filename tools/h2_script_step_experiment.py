#!/usr/bin/env python3
"""Differentially exercise the H2 script-step dispatcher under explicit handlers."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unicorn
from unicorn import arm_const as arm
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ADDRESS = 0x0019DFBC
HANDLER_TABLE = 0x0044DED0
CODE_BASE = 0x00100000
CODE_MAP_SIZE = 0x00378000
DATA = 0x00500000
WORK = DATA
METHODS = DATA + 0x1000
STACK = 0x08000000
STACK_SIZE = 0x8000
SP = STACK + STACK_SIZE // 2
INJECT = 0x01000000
INJECT_SIZE = 0x1000
HANDLER_CODE = 0x02000000
HANDLER_CODE_SIZE = 0x1000
RETURN = INJECT + INJECT_SIZE - 4
SOURCE = ROOT / "experiments/semantic_equivalence/h2_script_step_candidate.cpp"
CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"
SYMBOL = "candidate_0019dfbc"
BAD_SYMBOL = "candidate_0019dfbc_bad"
OPCODES = {0: 1, 1: 2, 2: 3, 3: 4, 255: 5}
SCENARIOS = {
    "zero_terminates": [0],
    "two_returns_one": [2],
    "one_then_zero": [1, 0],
    "other_then_one_then_two": [3, 1, 2],
    "other_byte_then_zero": [255, 0],
}
EXPECTED = {
    "zero_terminates": {"return": 2, "index": 1, "cc": 0x13, "d0": 0, "calls": 1},
    "two_returns_one": {"return": 1, "index": 1, "cc": 0x14, "d0": 0x22, "calls": 1},
    "one_then_zero": {"return": 2, "index": 2, "cc": 0x13, "d0": 0, "calls": 2},
    "other_then_one_then_two": {"return": 1, "index": 3, "cc": 0x14, "d0": 1, "calls": 3},
    "other_byte_then_zero": {"return": 2, "index": 2, "cc": 0x13, "d0": 0, "calls": 2},
}
CALLEE_SAVED = [(f"r{i}", getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 7)]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_symbols(output: Path) -> tuple[dict[str, bytes], Path, list[str]]:
    output.mkdir(parents=True, exist_ok=True)
    obj = output / "h2_script_step_candidate.o"
    build = compile_tu_armv6k(SOURCE, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    extracted = extract_elf_functions_detailed(obj)
    code = {}
    for symbol in (SYMBOL, BAD_SYMBOL):
        if symbol not in extracted:
            raise ValueError(f"candidate object lacks {symbol}")
        body, relocations = extracted[symbol]
        if relocations:
            raise ValueError(f"candidate {symbol} has relocations: {relocations}")
        code[symbol] = body
    return code, obj, list(build.args)


def handler_stub(result: int, *, advance: bool = True) -> bytes:
    words = []
    if advance:
        words += [0xE5901018, 0xE2811001, 0xE5801018]  # ++work->script_index
    words += [0xE59010E4, 0xE2811001, 0xE58010E4]  # ++work->call_count
    words += [0xE3A00000 | (result & 0xFF), 0xE12FFF1E]  # mov r0,#result; bx lr
    return b"".join(struct.pack("<I", word) for word in words)


def machine(image: bytes, candidate: bytes | None, *, stuck: bool = False) -> tuple[unicorn.Uc, list[int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(CODE_BASE, CODE_MAP_SIZE)
    uc.mem_write(CODE_BASE, image)
    uc.mem_map(DATA, 0x3000)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_map(INJECT, INJECT_SIZE)
    uc.mem_map(HANDLER_CODE, HANDLER_CODE_SIZE)
    if candidate is not None:
        if len(candidate) > INJECT_SIZE - 4:
            raise ValueError("candidate is too large for the injection page")
        uc.mem_write(INJECT, candidate)
    uc.mem_write(RETURN, b"\x00\x00\xA0\xE1")
    callback_addrs = []
    for result, opcode in OPCODES.items():
        address = HANDLER_CODE + opcode * 0x40
        uc.mem_write(address, handler_stub(result, advance=not (stuck and result == 1)))
        uc.mem_write(HANDLER_TABLE + opcode * 4, struct.pack("<I", address))
        callback_addrs.append(address)
    return uc, callback_addrs


def initialize(uc: unicorn.Uc, outcomes: list[int]) -> None:
    uc.mem_write(WORK, b"\0" * 0x200)
    uc.mem_write(WORK + 0x18, struct.pack("<I", 0))
    uc.mem_write(WORK + 0xBC, struct.pack("<I", METHODS))
    uc.mem_write(WORK + 0xCC, struct.pack("<I", 0x13))
    uc.mem_write(WORK + 0xD0, struct.pack("<I", 0x21))
    uc.mem_write(WORK + 0xE4, struct.pack("<I", 0))
    for index, result in enumerate(outcomes):
        opcode = OPCODES[result]
        uc.mem_write(METHODS + index * 4, struct.pack("<H", opcode))


def invoke(uc: unicorn.Uc, entry: int, outcomes: list[int], callback_addrs: list[int], *,
           max_instructions: int = 10000, stop_after_callbacks: int | None = None) -> dict:
    initialize(uc, outcomes)
    for index, (_, register) in enumerate(CALLEE_SAVED):
        uc.reg_write(register, 0x55000000 | (index + 1))
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    uc.reg_write(arm.UC_ARM_REG_R0, WORK)
    result = {"fault": None, "completed": False, "bounded_stop": False}

    def stop_at_return(emu: unicorn.Uc, address: int, size: int, user_data: object) -> None:
        if address == RETURN:
            result["completed"] = True
            emu.emu_stop()
        elif (stop_after_callbacks is not None and address in callback_addrs and
              struct.unpack("<I", emu.mem_read(WORK + 0xE4, 4))[0] >= stop_after_callbacks):
            result["bounded_stop"] = True
            emu.emu_stop()

    uc.hook_add(unicorn.UC_HOOK_CODE, stop_at_return)
    try:
        uc.emu_start(entry, RETURN + 4, count=max_instructions)
    except unicorn.UcError as error:
        result["fault"] = str(error)
    result.update({
        "return": uc.reg_read(arm.UC_ARM_REG_R0),
        "pc": uc.reg_read(arm.UC_ARM_REG_PC),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "preserved": {name: uc.reg_read(register) == (0x55000000 | (index + 1))
                      for index, (name, register) in enumerate(CALLEE_SAVED)},
        "work": bytes(uc.mem_read(WORK, 0x200)).hex(),
        "script_index": struct.unpack("<I", uc.mem_read(WORK + 0x18, 4))[0],
        "counter_cc": struct.unpack("<I", uc.mem_read(WORK + 0xCC, 4))[0],
        "counter_d0": struct.unpack("<I", uc.mem_read(WORK + 0xD0, 4))[0],
        "callback_count": struct.unpack("<I", uc.mem_read(WORK + 0xE4, 4))[0],
    })
    return result


def compare(original: dict, candidate: dict) -> str | None:
    for key in ("fault", "completed", "return", "pc", "sp", "preserved", "work"):
        if original[key] != candidate[key]:
            return f"{key} differs"
    return None


def run(output: Path, code_path: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    symbols, obj, compiler_args = compile_symbols(output)
    cases = []
    mismatch = None
    start = time.time()
    for name, outcomes in SCENARIOS.items():
        original, original_handlers = machine(image, None)
        candidate, candidate_handlers = machine(image, symbols[SYMBOL])
        ref = invoke(original, ADDRESS, outcomes, original_handlers)
        got = invoke(candidate, INJECT, outcomes, candidate_handlers)
        reason = compare(ref, got)
        if not ref["completed"] or not got["completed"]:
            reason = reason or "finite scenario did not return"
        summary = (got["return"], got["script_index"], got["counter_cc"],
                   got["counter_d0"], got["callback_count"])
        expected_summary = (EXPECTED[name]["return"], EXPECTED[name]["index"],
                            EXPECTED[name]["cc"], EXPECTED[name]["d0"], EXPECTED[name]["calls"])
        if summary != expected_summary:
            reason = reason or "candidate did not match the directed state expectation"
        if not all(ref["preserved"].values()) or not all(got["preserved"].values()):
            reason = reason or "callee-saved register contract violated"
        cases.append({"name": name, "outcomes": outcomes, "original": ref,
                      "candidate": got, "expected": EXPECTED[name], "match": reason is None})
        if reason and mismatch is None:
            mismatch = {"scenario": name, "reason": reason}

    # Sensitivity: an always-return-2 mutant must fail the result-2 scenario.
    neg_original, neg_original_handlers = machine(image, None)
    neg_mutant, neg_mutant_handlers = machine(image, symbols[BAD_SYMBOL])
    neg_ref = invoke(neg_original, ADDRESS, [2], neg_original_handlers)
    neg_got = invoke(neg_mutant, INJECT, [2], neg_mutant_handlers)
    negative_detected = compare(neg_ref, neg_got) is not None
    if not negative_detected and mismatch is None:
        mismatch = {"scenario": "negative-control", "reason": "mutant escaped"}

    # A callback returning 1 forever without advancing is intentionally bounded.
    stuck_original, stuck_original_handlers = machine(image, None, stuck=True)
    stuck_candidate, stuck_candidate_handlers = machine(image, symbols[SYMBOL], stuck=True)
    stuck_ref = invoke(stuck_original, ADDRESS, [1], stuck_original_handlers,
                       max_instructions=10000, stop_after_callbacks=8)
    stuck_got = invoke(stuck_candidate, INJECT, [1], stuck_candidate_handlers,
                       max_instructions=10000, stop_after_callbacks=8)
    stuck_match = (not stuck_ref["completed"] and not stuck_got["completed"] and
                   stuck_ref["bounded_stop"] and stuck_got["bounded_stop"] and
                   stuck_ref["fault"] == stuck_got["fault"] and
                   stuck_ref["work"] == stuck_got["work"] and
                   stuck_ref["script_index"] == stuck_got["script_index"] and
                   stuck_ref["callback_count"] == stuck_got["callback_count"])
    if not stuck_match and mismatch is None:
        mismatch = {"scenario": "non-advancing-callback", "reason": "bounded stop drift"}

    report = {
        "schema": 1,
        "status": "passed" if mismatch is None else "failed",
        "scope": "valid mapped script table and handler IDs; callbacks explicitly modeled",
        "reference": {"address": hex(ADDRESS), "code_sha256": hashlib.sha256(image).hexdigest()},
        "candidate": {"source": str(SOURCE), "source_sha256": sha256(SOURCE),
                      "object": str(obj), "object_sha256": sha256(obj),
                      "function_size": len(symbols[SYMBOL]),
                      "negative_function_size": len(symbols[BAD_SYMBOL]),
                      "compiler_args": compiler_args},
        "scenarios": cases,
        "negative_control": {"detected": negative_detected,
                             "original_return": neg_ref["return"],
                             "mutant_return": neg_got["return"]},
        "nonadvancing_callback_guard": {"matched_bounded_stop": stuck_match,
                                        "stop_after_callbacks": 8,
                                        "original_pc": hex(stuck_ref["pc"]),
                                        "candidate_pc": hex(stuck_got["pc"]),
                                        "original_calls": stuck_ref["callback_count"],
                                        "candidate_calls": stuck_got["callback_count"]},
        "elapsed_seconds": round(time.time() - start, 3),
        "first_mismatch": mismatch,
    }
    path = output / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    args = parser.parse_args()
    report = run(args.output, args.code)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
