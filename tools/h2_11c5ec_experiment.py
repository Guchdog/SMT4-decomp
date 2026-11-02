#!/usr/bin/env python3
"""Final-VMA ARM differential for H2 input reader 0x0011C5EC."""
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
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch30_a.cpp"
ADDRESS = 0x0011C5EC
CALLER = 0x001078D8
RING_READER = 0x0012A758
STATE = 0x004E3C28
INPUT = 0x004650A0
TABLE = 0x004099C0
MODE = 0x0047388B
FLAG_A = 0x0044E362
FLAG_B = 0x0044E381
POSTPROCESS_GATE = 0x00471AD8
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000
DATA_BASE = 0x00500000
DATA_SIZE = 0x00040000
STACK = 0x08000000
STACK_SIZE = 0x10000
SP = STACK + 0x8000
STOP = STACK + 0x9000
INJECT = 0x01000000
INJECT_SIZE = 0x1000
U32 = 0xFFFFFFFF
SLOT_SIZE = 304
CALL_TARGETS = {
    "func_00128c2c": 0x00128C2C,
    "func_001285c4": 0x001285C4,
    "func_0012a758": 0x0012A758,
    "func_00128610": 0x00128610,
    "func_002bb978": 0x002BB978,
    "func_002bc9c8": 0x002BC9C8,
    "func_0013bcac": 0x0013BCAC,
}
CALLEE_SAVED = [(f"r{i}", getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def branch_word(site: int, target: int) -> int:
    delta = target - (site + 8)
    if target & 3 or delta & 3 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError(f"invalid ARM R_ARM_CALL target {site:#x}->{target:#x}")
    return 0xEB000000 | ((delta >> 2) & 0xFFFFFF)


def compile_body(out: Path, source: Path = SOURCE,
                 function_vma: int = ADDRESS) -> tuple[bytes, list[dict], list[str]]:
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch30_a.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "production TU compilation failed")
    body, relocations = extract_elf_functions_detailed(obj)["func_0011c5ec"]
    if len(relocations) != len(CALL_TARGETS):
        raise ValueError(f"expected seven direct callee relocations; found {len(relocations)}")
    fixed = bytearray(body)
    seen = set()
    details = []
    for reloc in relocations:
        if reloc.relocation_type != 28 or reloc.symbol_name not in CALL_TARGETS:
            raise ValueError(f"unexpected relocation: {reloc}")
        if reloc.symbol_name in seen:
            raise ValueError(f"duplicate call relocation for {reloc.symbol_name}")
        seen.add(reloc.symbol_name)
        site = function_vma + reloc.offset
        word = branch_word(site, CALL_TARGETS[reloc.symbol_name])
        struct.pack_into("<I", fixed, reloc.offset, word)
        details.append({"offset": reloc.offset, "type": "R_ARM_CALL",
                        "symbol": reloc.symbol_name,
                        "target": hex(CALL_TARGETS[reloc.symbol_name]),
                        "entry_bit0": CALL_TARGETS[reloc.symbol_name] & 1,
                        "word": hex(word)})
    if seen != set(CALL_TARGETS):
        raise ValueError(f"missing call relocations: {set(CALL_TARGETS) - seen}")
    return bytes(fixed), details, list(result.args)


def stage_image(original: bytes, body: bytes) -> tuple[bytes, bytes]:
    if len(body) > SLOT_SIZE:
        raise ValueError(f"production body {len(body)} exceeds original slot {SLOT_SIZE}")
    padding = SLOT_SIZE - len(body)
    if padding % 4:
        raise ValueError("slot padding is not ARM-instruction aligned")
    payload = body + struct.pack("<I", 0xE320F000) * (padding // 4)
    staged = bytearray(original)
    offset = ADDRESS - CODE_BASE
    staged[offset:offset + SLOT_SIZE] = payload
    return bytes(staged), payload


class Machine:
    def __init__(self, image: bytes, ring_count: int, record: tuple[int, int, int, int, int],
                 helper_return: int = 0x76543210, injected_body: bytes | None = None):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM,
                             unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
        self.uc.mem_map(CODE_BASE, CODE_SIZE)
        self.uc.mem_write(CODE_BASE, image)
        if injected_body is not None:
            if len(injected_body) > INJECT_SIZE:
                raise ValueError("mutant exceeds injection page")
            self.uc.mem_map(INJECT, INJECT_SIZE)
            self.uc.mem_write(INJECT, injected_body)
        self.uc.mem_map(DATA_BASE, DATA_SIZE)
        self.uc.mem_map(0x004E3000, 0x1000)
        self.uc.mem_map(STACK, STACK_SIZE)
        self.ring_count = ring_count
        self.record = record
        self.helper_return = helper_return & U32
        self.ring_calls: list[dict] = []
        self.writes: list[tuple[int, int, int]] = []
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._write)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._ring,
                         begin=RING_READER, end=RING_READER)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._stop,
                         begin=STOP, end=STOP)

    def _write(self, uc, _access, address, size, value, _data):
        self.writes.append((address, size, value & U32))

    @staticmethod
    def _stop(uc, _address, _size, _data):
        uc.emu_stop()

    def _ring(self, uc, _address, _size, _data):
        sp = uc.reg_read(arm.UC_ARM_REG_SP)
        args = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4)]
        stack_args = list(struct.unpack("<II", uc.mem_read(sp, 8)))
        source, output, requested, count_ptr = args
        timestamp_ptr, index_ptr = stack_args
        local_low = SP - 0x200
        def local_pointer(pointer: int) -> bool:
            return local_low <= pointer < SP
        self.ring_calls.append({
            "source": source, "output": output, "requested": requested,
            "count_out_is_local": local_pointer(count_ptr),
            "timestamp_out_is_local": local_pointer(timestamp_ptr),
            "index_out_is_local": local_pointer(index_ptr),
            "timestamp_initial": struct.unpack("<Q", uc.mem_read(timestamp_ptr, 8))[0],
            "index_initial": struct.unpack("<I", uc.mem_read(index_ptr, 4))[0],
            "sp_aligned_8": sp % 8 == 0})
        if self.ring_count > 0:
            words = self.record[:3]
            x, y = self.record[3:]
            uc.mem_write(output, struct.pack("<IIIhh", *words, x, y))
        uc.mem_write(count_ptr, struct.pack("<i", self.ring_count))
        uc.mem_write(timestamp_ptr, struct.pack("<Q", 0x1122334455667788))
        uc.mem_write(index_ptr, struct.pack("<I", 0x12345678))
        uc.reg_write(arm.UC_ARM_REG_R0, self.helper_return)
        uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

    def setup(self, case: dict):
        context = case["context"]
        object_addr = case["object"]
        source_addr = case["source"]
        output = STATE
        self.uc.mem_write(context, bytes(case["context_bytes"]))
        self.uc.mem_write(object_addr, bytes(16))
        self.uc.mem_write(source_addr, bytes(0x100))
        self.uc.mem_write(context, struct.pack("<I", object_addr))
        self.uc.mem_write(object_addr + 4, struct.pack("<I", source_addr))
        self.uc.mem_write(output, bytes(case["output_bytes"]))
        self.uc.mem_write(MODE, bytes((case["mode"],)))
        self.uc.mem_write(FLAG_A, bytes((case["flag_a"],)))
        self.uc.mem_write(FLAG_B, bytes((case["flag_b"],)))
        self.uc.mem_write(POSTPROCESS_GATE, bytes((case["post_gate"],)))
        self.ring_calls.clear(); self.writes.clear()

    def invoke(self, entry: int, context: int, caller: bool = False) -> dict:
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        for i, (_name, reg) in enumerate(CALLEE_SAVED):
            self.uc.reg_write(reg, 0xC1000000 + i * 0x01010101)
        preserved_before = [self.uc.reg_read(reg) for _name, reg in CALLEE_SAVED]
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, STOP)
        if not caller:
            self.uc.reg_write(arm.UC_ARM_REG_R0, context)
            self.uc.reg_write(arm.UC_ARM_REG_R1, STATE)
        else:
            self.uc.mem_write(INPUT, struct.pack("<I", context))
        fault = None
        try:
            self.uc.emu_start(entry, 0, count=50000)
        except unicorn.UcError as e:
            fault = str(e)
        saved_after = [self.uc.reg_read(reg) for _name, reg in CALLEE_SAVED]
        output = bytes(self.uc.mem_read(STATE, 0x20))
        context_bytes = bytes(self.uc.mem_read(context, 0x60))
        counters = list(struct.unpack("<32I", self.uc.mem_read(0x004E3C58, 128)))
        available = struct.unpack("<I", self.uc.mem_read(INPUT + 4, 4))[0]
        relevant_writes = [row for row in self.writes if
                           STATE <= row[0] < STATE + 0x20 or
                           context <= row[0] < context + 0x60 or
                           row[0] == INPUT + 4 or
                           0x004E3C58 <= row[0] < 0x004E3CD8]
        return {"fault": fault, "return": self.uc.reg_read(arm.UC_ARM_REG_R0),
                "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
                "callee_saved": saved_after == preserved_before,
                "output": output.hex(), "context": context_bytes.hex(),
                "counters": counters, "availability": available,
                "ring_calls": self.ring_calls.copy(),
                "global_writes": relevant_writes}


def make_case(index: int, mode: int, count: int, selector: int,
              flag_a: int, flag_b: int, post_gate: int, seed: int) -> dict:
    rng = random.Random((seed & U32) ^ (0x11C5EC + index * 0x9E3779B1))
    ctx = 0x00500000
    cbytes = bytearray(rng.randrange(256) for _ in range(0x60))
    struct.pack_into("<I", cbytes, 0, 0x00510000)
    cbytes[0x30] = 1 if index & 1 else 0
    struct.pack_into("<B", cbytes, 0x18, selector)
    # Signed calibration halfwords include values on both sides of clamp bounds.
    for off, value in ((0x0C, 20 + index % 25), (0x0E, 28 + index % 21),
                       (0x12, 130 + index % 25), (0x14, 145 - index % 9),
                       (0x16, 200 - index % 60)):
        struct.pack_into("<h", cbytes, off, value)
    words = [rng.getrandbits(32) for _ in range(3)]
    words[0] |= 0x2000 if index & 2 else 0
    record = (words[0], words[1], words[2],
              rng.randint(-32768, 32767), rng.randint(-32768, 32767))
    output = bytes(rng.randrange(256) for _ in range(0x20))
    return {"context": ctx, "object": 0x00510000, "source": 0x00520000,
            "context_bytes": bytes(cbytes), "output_bytes": output,
            "mode": mode, "count": count, "selector": selector,
            "flag_a": flag_a, "flag_b": flag_b, "post_gate": post_gate,
            "record": record}


def run_one(image: bytes, case: dict, caller: bool,
            injected_body: bytes | None = None) -> dict:
    m = Machine(image, case["count"], case["record"], injected_body=injected_body)
    m.setup(case)
    entry = CALLER if caller else (INJECT if injected_body is not None else ADDRESS)
    return m.invoke(entry, case["context"], caller)


def caller_observable(result: dict) -> dict:
    return {key: value for key, value in result.items() if key != "return"}


def compile_mutation(out: Path, label: str, before: str, after: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise ValueError(f"mutation {label} source needle is not unique")
    path = out / "mutants" / f"{label}.cpp"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace(before, after), encoding="utf-8")
    body, _relocs, _args = compile_body(out / "mutants" / f"{label}-compile", path,
                                         function_vma=INJECT)
    return body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "build/agent-work/H2-semantic/h2-input-state-reader-cpp-0011c5ec/run001/checks/direct")
    ap.add_argument("--seed", type=int, default=20261110)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned original code.bin hash mismatch")
    body, relocs, compiler_args = compile_body(args.out / "compile")
    staged, payload = stage_image(original, body)
    offset = ADDRESS - CODE_BASE
    ips = encode_ips([(offset, payload)], len(original))
    if apply_ips(original, ips) != staged:
        raise AssertionError("exact-slot IPS replay failed")
    (args.out / "staged-image.bin").write_bytes(staged)
    (args.out / "staged-slot.ips").write_bytes(ips)

    cases = []
    index = 0
    for mode in (0, 3, 4, 255):
        for count in (-1, 0, 1):
            for selector in (0, 1, 2, 3):
                for flags in ((0, 0), (1, 0), (1, 1)):
                    for post_gate in (0, 1):
                        cases.append(make_case(index, mode, count, selector,
                                               flags[0], flags[1], post_gate, args.seed))
                        index += 1
    direct_mismatches = []
    direct_outputs = []
    for i, case in enumerate(cases):
        ref = run_one(original, case, False)
        got = run_one(staged, case, False)
        if ref != got:
            direct_mismatches.append({"case": i, "original": ref, "candidate": got})
        direct_outputs.append({"case": i, "mode": case["mode"], "count": case["count"],
                               "selector": case["selector"], "flags": [case["flag_a"], case["flag_b"]],
                               "post_gate": case["post_gate"], "equal": ref == got,
                               "reader_calls": ref["ring_calls"]})

    # Compose the original 31-row refresh caller around the final-VMA reader.
    caller_cases = []
    for j, case in enumerate(cases[::9]):
        original_result = run_one(original, case, True)
        staged_result = run_one(staged, case, True)
        caller_cases.append({"case": j,
                             "equal": caller_observable(original_result) == caller_observable(staged_result),
                             "original": original_result, "candidate": staged_result})

    mutation_inputs = {
        "wrong_cleared_state_bit": (
            "~0x2000u", "~0x1000u",
            make_case(2, 0, 1, 1, 0, 0, 1, args.seed)),
        "reversed_context_marker_branch": (
            "if (context[0x30] != 0)", "if (context[0x30] == 0)",
            make_case(1, 0, 1, 0, 0, 0, 1, args.seed)),
        "omitted_short_circuit_output_clear": (
            "*reinterpret_cast<u32*>(output + 8) = 0;",
            "*reinterpret_cast<u32*>(output + 8) = 1;",
            make_case(3, 0, 1, 2, 1, 0, 1, args.seed)),
    }
    mutation_controls = {}
    for label, (before, after, case) in mutation_inputs.items():
        if label == "wrong_cleared_state_bit":
            case["record"] = (case["record"][0] | 0x2000, *case["record"][1:])
        mutated = compile_mutation(args.out, label, before, after)
        ref = run_one(original, case, False)
        got = run_one(original, case, False, injected_body=mutated)
        mutation_controls[label] = {"detected": ref != got,
                                   "original": ref, "mutant": got}

    fixture_digest = sha(json.dumps(cases, sort_keys=True, separators=(",", ":"),
                                  default=lambda value: value.hex()).encode())
    report = {"image_sha256": sha(original), "source_sha256": sha(SOURCE.read_bytes()),
              "fixture_sha256": fixture_digest,
              "seed": args.seed, "body_bytes": len(body), "slot_bytes": SLOT_SIZE,
              "relocations": relocs, "compiler_args": compiler_args,
              "direct_cases": len(cases), "direct_mismatches": direct_mismatches,
              "caller_cases": caller_cases,
              "mutation_controls": mutation_controls,
              "direct_case_summary": direct_outputs,
              "exact_slot_ips_replay": apply_ips(original, ips) == staged,
              "only_slot_changed": original[:offset] == staged[:offset] and
                                   original[offset + SLOT_SIZE:] == staged[offset + SLOT_SIZE:],
              "all_passed": not direct_mismatches and
                            all(x["equal"] and x["original"]["fault"] is None and
                                x["original"]["callee_saved"] and
                                x["original"]["sp"] == SP for x in caller_cases) and
                            all(x["detected"] for x in mutation_controls.values()),
              "scope": "valid synthetic context/output and controlled 0x0012A758 ring-reader seam; other direct callees execute pinned original code"}
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_passed": report["all_passed"], "body_bytes": len(body),
                      "direct_cases": len(cases), "caller_cases": len(caller_cases),
                      "mismatches": len(direct_mismatches),
                      "mutations_detected": sum(x["detected"] for x in mutation_controls.values()),
                      "report": str(args.out / "report.json")}))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
