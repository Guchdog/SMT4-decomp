#!/usr/bin/env python3
"""Offline differential for the H2 31-row input-counter refresh."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools.semantic_experiment import arm_branch

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch27_a.cpp"
ADDRESS = 0x001078D8
CALLER = 0x0010B578
READER = 0x0011C5EC
FOLLOWUP = 0x00108B10
CALLER_END = 0x0010B58C
INPUT = 0x004650A0
TABLE = 0x004099C0
STATE = 0x004E3C28
COUNTERS = 0x004E3C58
ENTRY = 0x00100000
CODE_SIZE = 0x00380000
STACK = 0x08000000
STACK_SIZE = 0x8000
SP = STACK + STACK_SIZE // 2
RETURN = 0x00F00000
U32 = 0xFFFFFFFF
ROWS = 31


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def branch_word(site: int, target: int) -> int:
    delta = target - (site + 8)
    if delta & 3 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError(f"ARM BL target out of range/alignment: {site:#x} -> {target:#x}")
    return 0xEB000000 | ((delta >> 2) & 0xFFFFFF)


def build_body(output: Path, source: Path = SOURCE) -> tuple[bytes, list[dict], list[str]]:
    output.mkdir(parents=True, exist_ok=True)
    obj = output / "leaf_batch27_a.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "affected TU build failed")
    functions = extract_elf_functions_detailed(obj)
    body, relocs = functions["func_001078d8"]
    fixed = bytearray(body)
    details = []
    for reloc in relocs:
        site = ADDRESS + reloc.offset
        original = struct.unpack_from("<I", fixed, reloc.offset)[0]
        if reloc.relocation_type == 2 and not reloc.symbol_name:
            value = (original + 0) & U32
        elif reloc.relocation_type in (28, 29) and reloc.symbol_name == "func_0011c5ec":
            if reloc.relocation_type != 28:
                raise ValueError("state reader must be called with ARM BL")
            value = branch_word(site, READER)
        else:
            raise ValueError(f"unsupported 0x001078D8 relocation: {reloc}")
        struct.pack_into("<I", fixed, reloc.offset, value)
        details.append({"offset": reloc.offset, "type": reloc.relocation_type,
                        "symbol": reloc.symbol_name, "old": hex(original),
                        "new": hex(value)})
    return bytes(fixed), details, list(result.args)


def relocated_image(original: bytes, body: bytes) -> bytes:
    if len(body) > 164:
        raise ValueError(f"production body is {len(body)} bytes, exceeds 164-byte slot")
    staged = bytearray(original)
    offset = ADDRESS - ENTRY
    staged[offset:offset + 164] = body + bytes(164 - len(body))
    return bytes(staged)


class Machine:
    def __init__(self, image: bytes):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
        self.uc.mem_map(ENTRY, CODE_SIZE)
        self.uc.mem_write(ENTRY, image)
        self.uc.mem_map(0x004E3000, 0x1000)
        self.uc.mem_map(STACK, STACK_SIZE)
        self.writes: list[tuple[int, int, int]] = []
        self.reader_calls: list[tuple[int, int]] = []
        self.followup_calls = 0
        self.spec = (0, 0)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._write)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook, begin=READER, end=READER)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._followup, begin=FOLLOWUP, end=FOLLOWUP)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._stop, begin=RETURN, end=RETURN)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._stop, begin=CALLER_END, end=CALLER_END)

    @staticmethod
    def _stop(uc, _addr, _size, _data):
        uc.emu_stop()

    def _write(self, uc, _access, addr, size, value, _data):
        self.writes.append((addr, size, value & U32))

    def _hook(self, uc, _addr, _size, _data):
        handle, state_ptr = uc.reg_read(arm.UC_ARM_REG_R0), uc.reg_read(arm.UC_ARM_REG_R1)
        self.reader_calls.append((handle, state_ptr))
        result, word = self.spec
        if state_ptr:
            uc.mem_write(state_ptr, struct.pack("<I", word & U32))
        uc.reg_write(arm.UC_ARM_REG_R0, result & U32)
        uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

    def _followup(self, uc, _addr, _size, _data):
        self.followup_calls += 1
        uc.reg_write(arm.UC_ARM_REG_R0, 0)
        uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

    def setup(self, result: int, word: int, table: list[tuple[int, int]], counters: list[int]):
        self.spec = (result, word)
        self.uc.mem_write(INPUT, struct.pack("<I", 0xA1B2C3D4))
        self.uc.mem_write(INPUT + 4, struct.pack("<I", 0xBAD0BAD0))
        self.uc.mem_write(STATE, bytes(0x30))
        self.uc.mem_write(TABLE, b"".join(struct.pack("<II", *pair) for pair in table))
        self.uc.mem_write(COUNTERS, b"".join(struct.pack("<I", x & U32) for x in counters))
        self.writes.clear(); self.reader_calls.clear(); self.followup_calls = 0

    def invoke(self, entry: int) -> dict:
        regs = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13)]
        initial = [(0xC1000000 + i * 0x01010101) & U32 for i in range(13)]
        for reg, value in zip(regs, initial): self.uc.reg_write(reg, value)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        fault = None
        try: self.uc.emu_start(entry, 0, count=10000)
        except unicorn.UcError as e: fault = str(e)
        after = [self.uc.reg_read(reg) for reg in regs]
        counters = list(struct.unpack("<32I", self.uc.mem_read(COUNTERS, 128)))
        relevant_writes = [row for row in self.writes
                           if row[0] == INPUT + 4 or COUNTERS <= row[0] < COUNTERS + 128]
        return {"fault": fault,
                "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
                "callee_saved": after[4:12] == initial[4:12],
                "counters": counters,
                "availability": struct.unpack("<I", self.uc.mem_read(INPUT + 4, 4))[0],
                "state_word": struct.unpack("<I", self.uc.mem_read(STATE, 4))[0],
                "reader_calls": self.reader_calls.copy(),
                "followup_calls": self.followup_calls,
                "global_writes": relevant_writes}


def fixtures(seed: int):
    # Directed records cover gate reset, match/miss, low/high row boundaries, and untouched row 31.
    for available in (0, 1, 2, U32):
        for state in (0, 1, 0x80000000, U32):
            table = []
            counters = []
            for i in range(ROWS):
                gate = 1 if i in (0, 15, 30) else 0
                mask = (1 << (i % 32)) if i not in (1, 29) else 0
                if i == 30: mask = 0x80000000
                table.append((gate, mask))
                counters.append(U32 if i == 30 and state else ((seed * 31 + i * 19) & 0xFFFFFFFF))
            counters.append(0xDEADBEEF)
            yield available, state, table, counters
    for target in range(ROWS):
        mask = 1 << target
        for available, state, initial in ((1, mask, U32), (1, 0, 7), (0, mask, 1)):
            table = [(0, 1 << i) for i in range(ROWS)]
            counters = [((seed * 31 + i * 19) & U32) for i in range(ROWS)] + [0xDEADBEEF]
            table[target] = (0, mask)
            counters[target] = initial
            yield available, state, table, counters
        table = [(0, 1 << i) for i in range(ROWS)]
        counters = [((seed * 31 + i * 19) & U32) for i in range(ROWS)] + [0xDEADBEEF]
        table[target] = (1, mask)
        counters[target] = 0x12345678
        yield 0, mask, table, counters


def run_case(image: bytes, candidate: bytes | None, case, entry: int) -> dict:
    available, state, table, counters = case
    m = Machine(image)
    m.setup(available, state, table, counters)
    return m.invoke(entry)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "build/agent-work/H2-semantic/h2-titleconfig-001078d8-counter-refresh-cpp/run002/checks/direct")
    parser.add_argument("--seed", type=int, default=20261102)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA: raise SystemExit("pinned original image hash mismatch")
    body, relocs, compiler_args = build_body(args.out / "compile")
    if READER & 3:
        raise ValueError("the original state reader is not ARM-word aligned")
    call_relocations = [r for r in relocs if r["symbol"] == "func_0011c5ec"]
    interworking_ok = len(call_relocations) == 1 and call_relocations[0]["type"] == 28
    if not interworking_ok:
        raise ValueError("state reader must remain an even ARM R_ARM_CALL target")
    patched = relocated_image(original, body)
    slot_offset = ADDRESS - ENTRY
    slot_payload = patched[slot_offset:slot_offset + 164]
    ips = encode_ips([(slot_offset, slot_payload)], len(original))
    replay = apply_ips(original, ips)
    if replay != patched:
        raise AssertionError("exact-slot IPS replay differs from staged image")
    (args.out / "staged-slot.ips").write_bytes(ips)
    (args.out / "staged-image.bin").write_bytes(patched)
    cases = list(fixtures(args.seed))
    mismatches = []
    for index, case in enumerate(cases):
        ref = run_case(original, None, case, ADDRESS)
        got = run_case(patched, None, case, ADDRESS)
        if ref != got:
            mismatches.append({"index": index, "case": {"available": case[0], "state": case[1]},
                               "original": ref, "candidate": got})
    changed = bytearray(body)
    # Negative control: shrink the loop bound from 31 to 30 at the observed CMP r3,#31.
    cmp_offset = 0x0010791C - ADDRESS
    cmp_word = struct.unpack_from("<I", changed, cmp_offset)[0]
    if cmp_word != 0xE353001F:
        raise ValueError(f"loop-bound instruction changed unexpectedly: {cmp_word:#010x}")
    struct.pack_into("<I", changed, cmp_offset, 0xE353001E)
    mutated = relocated_image(original, bytes(changed))
    mutation_case = (1, 0x80000000, cases[0][2], [0xFFFFFFFF] * 32)
    mutation_ref = run_case(original, None, mutation_case, ADDRESS)
    mutation_got = run_case(mutated, None, mutation_case, ADDRESS)
    mutation_detected = mutation_ref != mutation_got
    # Caller composition executes the original caller with its unrelated second service stubbed.
    caller_cases = []
    for success, state in ((0, 0xFFFFFFFF), (1, 0), (1, 0x12345678), (U32, 0x80000000)):
        case = (success, state, cases[0][2], [0xFFFFFFFF] * 32)
        caller_ref = run_case(original, None, case, CALLER)
        caller_new = run_case(patched, None, case, CALLER)
        caller_cases.append({"success": success, "state": state,
                             "equal": caller_ref == caller_new,
                             "original": caller_ref, "candidate": caller_new})
    report = {"image_sha256": sha(original), "source_sha256": sha(SOURCE.read_bytes()),
              "seed": args.seed, "compiled_body_bytes": len(body), "slot_bytes": 164,
              "relocations": relocs, "compiler_args": compiler_args,
              "arm_interworking": {"reader_entry": hex(READER), "entry_bit0": READER & 1,
                                   "relocation": "R_ARM_CALL", "passed": interworking_ok},
              "direct_cases": len(cases), "direct_mismatches": mismatches,
              "caller_cases": caller_cases,
              "exact_slot_ips_replay": replay == patched,
              "only_slot_changed": original[:slot_offset] == patched[:slot_offset] and
                                   original[slot_offset + 164:] == patched[slot_offset + 164:],
              "negative_control_loop_bound_detected": mutation_detected,
              "negative_control": {"mutated_compare": hex(cmp_word),
                                   "original_counters": mutation_ref["counters"],
                                   "mutated_counters": mutation_got["counters"]},
              "all_passed": not mismatches and all(x["equal"] and
                                                    x["original"]["fault"] is None and
                                                    x["original"]["followup_calls"] == 1
                                                    for x in caller_cases)
                            and replay == patched and mutation_detected,
              "scope": "synthetic mapped RAM, controlled 0x0011C5EC return/state word; caller follow-up stubbed"}
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_passed": report["all_passed"], "body_bytes": len(body),
                      "direct_cases": len(cases), "caller_cases": len(caller_cases),
                      "mismatches": len(mismatches), "mutation_detected": mutation_detected,
                      "exact_slot_ips_replay": replay == patched,
                      "report": str(args.out / "report.json")}))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
