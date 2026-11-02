#!/usr/bin/env python3
"""Differential and cumulative H2 staging for the two ASD slot getters."""
from __future__ import annotations

import hashlib
import json
import random
import struct
import sys
from pathlib import Path

from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools import h2_2a63f8_experiment as predicate

IMAGE_PATH = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch34_b.cpp"
BASE = ROOT / "build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin"
BASE_MANIFEST = BASE.with_name("manifest.json")
BASE_SHA = "7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291"
PREDICATE_IMAGE = ROOT / "build/agent-work/H2-semantic/h2-resource-flag-predicate-002a63f8/run001/staged-image/code.h2-resource-flag.bin"
PREDICATE_SHA = "818f8a104e1761860d3967789994990570838cfc2751d21ddca32caeb8c9cf8d"
OUT = ROOT / "build/agent-work/H2-semantic/h2-slot-getters-0029f248-0029f260/run001"
FUNCTIONS = {
    "camp_func_0029f248": (0x0029F248, 0x002CB84C),
    "camp_func_0029f260": (0x0029F260, 0x002D5674),
}
SPAN = 24
TEXT = 0x00100000
TEMP = 0x00800000
STOP = 0x0080F000
SLOT = 0x00901000
WORK = 0x00910000
DATA = 0x00900000
DATA_SIZE = 0x30000
STACK = 0x00A0FF00
CALLER_START = 0x001EA9F4
CALLER_STOP = 0x001EAA0C
NOP = struct.pack("<I", 0xE320F000)
MASK = 0xFFFFFFFF


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_candidates(name: str, entries: dict[str, int], source: Path = SOURCE,
                       targets: dict[str, int] | None = None):
    OUT.mkdir(parents=True, exist_ok=True)
    obj = OUT / name
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    symbols = extract_elf_functions_detailed(obj)
    output = {}
    for symbol, (address, target) in FUNCTIONS.items():
        target = (targets or {}).get(symbol, target)
        body, relocations = symbols[symbol]
        fixed = bytearray(body)
        resolved = []
        for relocation in relocations:
            if (relocation.relocation_type != 29 or relocation.symbol_name != ""
                    or relocation.explicit_addend is not None):
                raise AssertionError(f"unsupported tail relocation for {symbol}: {relocation}")
            ins = struct.unpack_from("<I", fixed, relocation.offset)[0]
            if ins & 0x0F000000 != 0x0A000000 or ins & 0x01000000:
                raise AssertionError(f"expected ARM B at {relocation.offset:#x}: {ins:#010x}")
            place = entries[symbol] + relocation.offset
            delta = target - (place + 8)
            struct.pack_into("<I", fixed, relocation.offset,
                             (ins & 0xFF000000) | ((delta >> 2) & 0x00FFFFFF))
            resolved.append({"offset": relocation.offset, "target": hex(target),
                             "type": relocation.relocation_type, "instruction": "ARM B"})
        if len(body) > SPAN or len(relocations) != 1:
            raise AssertionError(f"{symbol}: body {len(body)} or relocation count {len(relocations)} invalid")
        output[symbol] = {"body": bytes(fixed), "relocations": resolved, "object": obj}
    return output


def setup(image: bytes, code: dict[str, bytes] | None = None, stop_at: int = STOP):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(TEXT, (len(image) + 0xFFF) & ~0xFFF)
    uc.mem_write(TEXT, image)
    uc.mem_map(0x00800000, 0x10000)
    uc.mem_map(DATA, DATA_SIZE)
    uc.mem_map(0x00A00000, 0x10000)
    if code:
        for address, body in code.items():
            uc.mem_write(address, body)
    state = {"done": False, "reads": [], "writes": [], "last_pc": None}

    def on_code(machine, address, _size, _data):
        state["last_pc"] = address
        if address == stop_at:
            state["done"] = True
            machine.emu_stop()

    def on_read(machine, _kind, address, size, _value, _data):
        state["reads"].append((address, size, bytes(machine.mem_read(address, size))))

    def on_write(_machine, _kind, address, size, value, _data):
        state["writes"].append((address, size, value & MASK))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.hook_add(UC_HOOK_MEM_READ, on_read)
    uc.hook_add(UC_HOOK_MEM_WRITE, on_write)
    uc._state = state
    return uc


def prepare_slot(uc, slot: int, gate: int, field20: int, field24: int):
    uc.mem_write(slot + 0x20, struct.pack("<I", field20 & MASK))
    uc.mem_write(slot + 0x24, struct.pack("<I", field24 & MASK))
    uc.mem_write(slot + 0x62, bytes((gate & 0xFF,)))


def execute(uc, entry: int, slot: int, gate: int, field20: int, field24: int, which: str):
    state = uc._state
    state.update(done=False, reads=[], writes=[], last_pc=None)
    prepare_slot(uc, slot, gate, field20, field24)
    saved = {reg: 0x11110000 + i * 0x01010101 for i, reg in enumerate(
        (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
         UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11))}
    uc.reg_write(UC_ARM_REG_SP, STACK)
    uc.reg_write(UC_ARM_REG_LR, STOP)
    for reg, value in saved.items():
        uc.reg_write(reg, value)
    uc.reg_write(UC_ARM_REG_R0, slot)
    uc.reg_write(UC_ARM_REG_R1, 0xAABBCCDD)
    fault = None
    try:
        uc.emu_start(entry, 0, count=100)
    except (UcError, OSError) as exc:
        fault = str(exc)
    expected = 0 if gate & 0xFF else (field20 if which == "camp_func_0029f248" else field24) & MASK
    observed = {
        "return": uc.reg_read(UC_ARM_REG_R0), "expected": expected,
        "r1": uc.reg_read(UC_ARM_REG_R1),
        "callee_saved": all(uc.reg_read(reg) == value for reg, value in saved.items()),
        "sp": uc.reg_read(UC_ARM_REG_SP) == STACK,
        "reads": tuple(state["reads"]), "writes": tuple(state["writes"]),
        "done": state["done"], "fault": fault,
    }
    if fault or not observed["done"] or observed["return"] != expected or not observed["callee_saved"] or not observed["sp"] or observed["writes"]:
        raise AssertionError(f"{which} differs at slot={slot:#x}, gate={gate:#x}: {observed}")
    return observed


def comparable(result, entry: int):
    reads = []
    for address, size, value in result["reads"]:
        location = ("function-literal", address - entry) if entry <= address < entry + SPAN else address
        reads.append((location, size, value))
    return {**{k: v for k, v in result.items() if k not in ("expected", "reads")}, "reads": tuple(reads)}


def build_stage(candidates: dict[str, dict], output: Path):
    original = IMAGE_PATH.read_bytes()
    base = BASE.read_bytes()
    if sha(original) != IMAGE_SHA or sha(base) != BASE_SHA:
        raise ValueError("pinned original or H2 run-013 base hash mismatch")
    if sha(PREDICATE_IMAGE.read_bytes()) != PREDICATE_SHA:
        raise ValueError("previous H2 predicate stage hash mismatch")
    base_manifest = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    if base_manifest.get("patched_sha256") != BASE_SHA or base_manifest.get("original_sha256") != IMAGE_SHA:
        raise ValueError("run-013 base manifest identity mismatch")
    staged = bytearray(base)
    rows = []
    patches = []
    replacements = {}
    # Carry the reviewed predicate integration forward into this cumulative H2 image.
    pred_body, pred_relocs = predicate.compile_candidate("predicate-final-for-stage.o", predicate.FUNCTION)
    replacements[predicate.FUNCTION] = pred_body + NOP * ((SPAN - len(pred_body)) // 4)
    rows.append({"address": hex(predicate.FUNCTION), "slot_bytes": SPAN,
                 "replacement_sha256": sha(replacements[predicate.FUNCTION]),
                 "source": str(predicate.SOURCE.relative_to(ROOT)),
                 "relocations": pred_relocs, "carried_forward": True})
    for symbol, (address, _target) in FUNCTIONS.items():
        body = candidates[symbol]["body"]
        replacement = body + NOP * ((SPAN - len(body)) // 4)
        replacements[address] = replacement
        rows.append({"address": hex(address), "symbol": symbol, "body_bytes": len(body),
                     "body_sha256": sha(body), "slot_bytes": SPAN,
                     "replacement_sha256": sha(replacement),
                     "relocations": candidates[symbol]["relocations"]})
    for address, replacement in sorted(replacements.items()):
        offset = address - TEXT
        staged[offset:offset + SPAN] = replacement
        patches.append((offset, replacement))
    staged_bytes = bytes(staged)
    changed = {i for i, (a, b) in enumerate(zip(base, staged_bytes)) if a != b}
    allowed = set()
    for address in replacements:
        start = address - TEXT
        allowed.update(range(start, start + SPAN))
    if not changed <= allowed:
        raise AssertionError("cumulative stage changed bytes outside the three declared function slots")
    patch = encode_ips(patches, len(base))
    if apply_ips(base, patch) != staged_bytes:
        raise AssertionError("cumulative H2 IPS round-trip failed")
    output.mkdir(parents=True, exist_ok=True)
    image_path, ips_path = output / "code.h2-slot-getters.bin", output / "code.h2-slot-getters.ips"
    image_path.write_bytes(staged_bytes)
    ips_path.write_bytes(patch)
    manifest = {
        "schema_version": 1, "milestone": "H2", "classification": "non_matching",
        "base_image": str(BASE.relative_to(ROOT)), "base_image_sha256": sha(base),
        "previous_predicate_image_sha256": sha(PREDICATE_IMAGE.read_bytes()),
        "original_code_image_sha256": sha(original), "patched_image_sha256": sha(staged_bytes),
        "ips_sha256": sha(patch), "changed_byte_count": len(changed),
        "slots": rows, "only_declared_function_slots_changed": True, "ips_roundtrip": True,
        "artifact_paths": {"image": str(image_path.relative_to(ROOT)), "ips": str(ips_path.relative_to(ROOT))},
        "evidence": {"differential": "pending", "caller_slice": "pending", "review": "pending", "runtime": "not_run"},
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return staged_bytes, manifest_path, manifest


def main():
    image = IMAGE_PATH.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise SystemExit("pinned code.bin hash mismatch")
    candidates = compile_candidates("candidates.o", {name: TEMP for name in FUNCTIONS})
    final_candidates = compile_candidates("candidates-final.o", {name: address for name, (address, _) in FUNCTIONS.items()})
    original_machine = setup(image)
    temp_code = {TEMP: candidates["camp_func_0029f248"]["body"] + NOP * (SPAN - len(candidates["camp_func_0029f248"]["body"]))}
    # Keep the two temporary entry points distinct, each with its own rebased branch.
    temp_entries = {name: TEMP + index * 0x100 for index, name in enumerate(FUNCTIONS)}
    candidates = compile_candidates("candidates-temp-distinct.o", temp_entries)
    temp_code = {temp_entries[name]: candidates[name]["body"] for name in FUNCTIONS}
    temp_machine = setup(image, temp_code)
    final_code = {FUNCTIONS[name][0]: final_candidates[name]["body"] for name in FUNCTIONS}
    final_machine = setup(image, final_code)
    staged_image, manifest_path, manifest = build_stage(final_candidates, OUT / "staged")
    staged_machine = setup(staged_image)
    directed = [(gate, f20, f24) for gate in (0, 1, 0x7F, 0xFF)
                for f20, f24 in ((0, 0), (1, 0x80000000), (0xFFFFFFFF, 0x7FFFFFFF))]
    rng = random.Random(0x29F248260)
    cases = directed + [(rng.randrange(256), rng.getrandbits(32), rng.getrandbits(32)) for _ in range(64)]
    for which, (address, _target) in FUNCTIONS.items():
        for index, (gate, f20, f24) in enumerate(cases):
            old = execute(original_machine, address, SLOT, gate, f20, f24, which)
            tmp = execute(temp_machine, temp_entries[which], SLOT, gate, f20, f24, which)
            final = execute(final_machine, address, SLOT, gate, f20, f24, which)
            staged = execute(staged_machine, address, SLOT, gate, f20, f24, which)
            if (comparable(old, address) != comparable(tmp, temp_entries[which])
                    or comparable(old, address) != comparable(final, address)
                    or comparable(old, address) != comparable(staged, address)):
                raise AssertionError(f"{which} case {index} differs")
    caller_cases = []
    for gate, f20, f24 in [(0, 7, 11), (1, 7, 11), (0, MASK, 0x80000000), (0xFF, 1, 2)]:
        old_caller = setup(image, stop_at=CALLER_STOP)
        new_caller = setup(staged_image, stop_at=CALLER_STOP)
        slot = WORK + 0xE8
        prepare_slot(old_caller, slot, gate, f20, f24)
        prepare_slot(new_caller, slot, gate, f20, f24)
        for machine in (old_caller, new_caller):
            machine.reg_write(UC_ARM_REG_SP, STACK)
            machine.reg_write(UC_ARM_REG_LR, STOP)
            machine.reg_write(UC_ARM_REG_R4, WORK)
            machine.emu_start(CALLER_START, 0, count=100)
            if not machine._state["done"]:
                raise AssertionError("TitleConfig_Calc slot-getter slice did not reach its sum")
        old_result = (old_caller.reg_read(UC_ARM_REG_R4), old_caller.reg_read(UC_ARM_REG_R0))
        new_result = (new_caller.reg_read(UC_ARM_REG_R4), new_caller.reg_read(UC_ARM_REG_R0))
        if old_result != new_result:
            raise AssertionError(f"TitleConfig_Calc getter pair differs for gate={gate:#x}: {old_result}/{new_result}")
        caller_cases.append({"gate": gate, "field20": f20, "field24": f24,
                             "sum_r4_and_second_return": old_result, "same": True})
    # Negative control 1: read a neighboring byte for the guard.
    source_text = SOURCE.read_text(encoding="utf-8")
    guard_old = "if (*reinterpret_cast<const u8*>(address + 0x62u) != 0) {"
    if source_text.count(guard_old) != 2:
        raise AssertionError("guard mutation anchors changed")
    mutant_guard = OUT / "mutant-guard.cpp"
    mutant_guard.write_text(source_text.replace(guard_old, "if (*reinterpret_cast<const u8*>(address + 0x61u) != 0) {", 1), encoding="utf-8")
    mutation_guard = compile_candidates("mutant-guard.o", {"camp_func_0029f248": TEMP + 0x400, "camp_func_0029f260": TEMP + 0x500}, mutant_guard)["camp_func_0029f248"]["body"]
    guard_control = setup(image, {TEMP + 0x400: mutation_guard})
    guard_control.mem_write(SLOT + 0x61, b"\x01")
    try:
        execute(guard_control, TEMP + 0x400, SLOT, 0, 1, 0, "camp_func_0029f248")
        guard_detected = False
    except AssertionError:
        guard_detected = True
    if not guard_detected:
        raise AssertionError("guard-offset negative control escaped")
    # Negative control 2: read the wrong tail field for the first getter.
    tail_old = ".set AsdSlot_GetField20Tail, 0x002CB84C"
    mutant_tail = OUT / "mutant-tail.cpp"
    if source_text.count(tail_old) != 1:
        raise AssertionError("tail mutation anchor changed")
    mutant_tail.write_text(source_text.replace(tail_old, ".set AsdSlot_GetField20Tail, 0x002D5674", 1), encoding="utf-8")
    tail_body = compile_candidates("mutant-tail.o", {"camp_func_0029f248": TEMP + 0x600, "camp_func_0029f260": TEMP + 0x700}, mutant_tail,
                                   {"camp_func_0029f248": 0x002D5674})["camp_func_0029f248"]["body"]
    tail_control = setup(image, {TEMP + 0x600: tail_body})
    try:
        execute(tail_control, TEMP + 0x600, SLOT, 0, 7, 11, "camp_func_0029f248")
        tail_detected = False
    except AssertionError:
        tail_detected = True
    if not tail_detected:
        raise AssertionError("tail-target negative control escaped")
    report = {
        "functions": {}, "image_sha256": sha(image), "source_sha256": sha(SOURCE.read_bytes()),
        "cases_per_function": len(cases), "directed_cases_per_function": len(directed),
        "seeded_cases_per_function": 64,
        "coverage": "guard byte at slot+0x62; getter words at +0x20/+0x24; return, ordered reads, no writes, callee-saved registers and SP",
        "negative_controls": [{"name": "guard-offset-62-to-61", "detected": guard_detected},
                              {"name": "field20-tail-to-field24-tail", "detected": tail_detected}],
        "titleconfig_caller": {"slice": [hex(CALLER_START), hex(CALLER_STOP)], "cases": caller_cases,
                               "description": "original code slice calls both getters on work+0xE8 and sums their results; staged image compared"},
        "staged_image_sha256": sha(staged_image), "staged_ips_sha256": manifest["ips_sha256"],
        "staged_differential": "passed: original/temp/final/staged direct cases and TitleConfig_Calc caller slice",
        "runtime": "not_run",
    }
    for symbol, (address, target) in FUNCTIONS.items():
        body = final_candidates[symbol]["body"]
        old = image[address - TEXT:address - TEXT + SPAN]
        report["functions"][symbol] = {
            "address": hex(address), "tail_target": hex(target), "candidate_body_bytes": len(body),
            "slot_bytes": SPAN, "candidate_body_sha256": sha(body), "original_slot_sha256": sha(old),
            "final_slot_match": body + NOP * (SPAN - len(body)) == old,
            "relocations": final_candidates[symbol]["relocations"],
            "semantic_result": "passed across original, temporary, final-VMA, and staged runs",
        }
    report_path = OUT / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    manifest["evidence"]["differential"] = "passed: 76 cases per getter across original/temp/final/staged"
    manifest["evidence"]["caller_slice"] = "passed: four actual TitleConfig_Calc call slices comparing original and cumulative staged image"
    manifest["validation_report"] = str(report_path.relative_to(ROOT))
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"report: {report_path}")


if __name__ == "__main__":
    main()
