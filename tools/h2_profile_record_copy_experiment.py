#!/usr/bin/env python3
"""Final-VMA differential for 0x002AA268 and original 0x002B85BC composition."""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch13_b.cpp"
ENTRY, SLOT = 0x002AA268, 72
SELECTOR, SELECTOR_STOP = 0x002B85BC, 0x08009000
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
DATA_BASE, DATA_SIZE = 0x00600000, 0x00200000
INVALID = DATA_BASE + DATA_SIZE
OBJECT, STACK = 0x00680000, 0x08000000
STACK_SIZE, SP, STOP = 0x10000, STACK + 0x8000, 0x08009000
GLOBAL_MANAGER_ROOT = 0x0043DA28
U32 = 0xFFFFFFFF
OLD_PROFILE, NEW_PROFILE = DATA_BASE + 0xA0000, DATA_BASE + 0xA0100


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_body(out: Path, source: Path = SOURCE):
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch13_b.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "ARMv6K translation-unit compile failed")
    body, relocs = extract_elf_functions_detailed(obj)["camp_func_002aa268"]
    if len(body) > SLOT or len(body) % 4:
        raise ValueError(f"candidate body does not fit slot: {len(body)}/{SLOT}")
    if relocs:
        raise ValueError(f"unexpected relocations: {relocs}")
    return body, list(result.args), obj


def stage_image(original: bytes, body: bytes):
    off = ENTRY - CODE_BASE
    fixed = body + original[off + len(body):off + SLOT]
    staged = bytearray(original)
    staged[off:off + SLOT] = fixed
    staged = bytes(staged)
    patch = encode_ips([(off, fixed)], len(original))
    if apply_ips(original, patch) != staged:
        raise AssertionError("IPS replay mismatch")
    return staged, patch


class Machine:
    def __init__(self, image: bytes, seed: int = 7301):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM,
                             unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
        self.uc.mem_map(CODE_BASE, CODE_SIZE)
        self.uc.mem_write(CODE_BASE, image)
        self.uc.mem_map(DATA_BASE, DATA_SIZE)
        self.uc.mem_map(STACK, STACK_SIZE)
        rng = random.Random(seed)
        self.uc.mem_write(DATA_BASE, bytes(rng.randrange(256) for _ in range(DATA_SIZE)))
        self.events, self.writes = [], []
        self.fault_detail = None
        self.stop = STOP
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_INVALID, self._on_invalid)

    def _on_code(self, uc, address, _size, _data):
        if address == self.stop:
            uc.emu_stop()
            return
        if address == ENTRY:
            args = [uc.reg_read(arm.UC_ARM_REG_R0), uc.reg_read(arm.UC_ARM_REG_R1),
                    uc.reg_read(arm.UC_ARM_REG_R2)]
            self.events.append({"address": hex(address), "name": "camp_func_002aa268",
                                "args": args,
                                "sp_aligned": (uc.reg_read(arm.UC_ARM_REG_SP) & 7) == 0})
            return
        if address == 0x002AEA28:
            arg = uc.reg_read(arm.UC_ARM_REG_R0)
            result = OLD_PROFILE if arg == 3 else NEW_PROFILE
            self.events.append({"address": hex(address), "name": "camp_func_002aea28",
                                "args": [arg], "sp_aligned": (uc.reg_read(arm.UC_ARM_REG_SP) & 7) == 0})
            uc.reg_write(arm.UC_ARM_REG_R0, result)
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
            return
        if address == 0x002BF030:
            args = [uc.reg_read(arm.UC_ARM_REG_R0), uc.reg_read(arm.UC_ARM_REG_R1)]
            self.events.append({"address": hex(address), "name": "camp_func_002bf030",
                                "args": args,
                                "sp_aligned": (uc.reg_read(arm.UC_ARM_REG_SP) & 7) == 0})
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

    def _on_write(self, _uc, _access, address, size, value, _data):
        if not STACK <= address < STACK + STACK_SIZE:
            self.writes.append([address, size, value & U32])

    def _on_invalid(self, _uc, access, address, size, _value, _data):
        self.fault_detail = {"access": int(access), "address": int(address), "size": int(size)}
        return False

    def run(self, entry: int, args: tuple[int, int, int], setup=None, stop=STOP):
        if setup:
            setup(self.uc)
        self.events.clear()
        self.writes.clear()
        self.fault_detail = None
        self.stop = stop
        initial = [(0xA1100000 + i * 0x01010101) & U32 for i in range(13)]
        for i, value in enumerate(initial):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), value)
        for i, value in enumerate(args):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), value & U32)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, stop)
        fault = None
        try:
            self.uc.emu_start(entry, 0, count=100000)
        except unicorn.UcError as error:
            fault = str(error)
        regs = [self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(13)]
        return {"fault": fault, "fault_detail": self.fault_detail,
                "registers": regs, "r0": regs[0], "r2": regs[2],
                "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
                "callee_saved": regs[4:12] == initial[4:12],
                "data": bytes(self.uc.mem_read(DATA_BASE, DATA_SIZE)),
                "global_words": bytes(self.uc.mem_read(GLOBAL_MANAGER_ROOT, 8)),
                "events": self.events.copy(), "writes": self.writes.copy()}


def setup_direct(record: int, table: int, index: int, selector: int, value0=0x10203040,
                 value4=0x50607080, alias=False):
    def setup(uc):
        uc.mem_write(record, bytes(0x100))
        uc.mem_write(record + 0x64, struct.pack("<I", table))
        if table:
            if alias:
                uc.mem_write(table, struct.pack("<II", value0, value4))
            else:
                offset = (index * 12) & U32
                selected_entry = (table + offset) & U32
                if DATA_BASE <= selected_entry and selected_entry + 8 <= DATA_BASE + DATA_SIZE:
                    uc.mem_write(selected_entry, struct.pack("<II", value0, value4))
    return setup


def direct_compare(original: bytes, staged: bytes, label: str, record: int,
                   index: int, selector: int, setup):
    ref = Machine(original).run(ENTRY, (record, index, selector), setup)
    got = Machine(staged).run(ENTRY, (record, index, selector), setup)
    comparable = lambda x: {k: x[k] for k in
        ("fault", "fault_detail", "r0", "r2", "sp", "callee_saved", "data", "events", "writes")}
    return {"label": label, "equal": comparable(ref) == comparable(got),
            "fault": got["fault"], "fault_detail": got["fault_detail"],
            "r0": hex(got["r0"]), "writes": got["writes"], "events": got["events"]}, ref, got


def caller_setup():
    def setup(uc):
        uc.mem_write(GLOBAL_MANAGER_ROOT + 4, struct.pack("<I", OBJECT))
        uc.mem_write(OBJECT, bytes(0x800))
        uc.mem_write(OBJECT + 0x4C8, b"\0")
        uc.mem_write(OBJECT + 0x4C9, b"\x03")
        uc.mem_write(OLD_PROFILE, bytes(0x40))
        uc.mem_write(NEW_PROFILE, bytes(0x40))
        uc.mem_write(OLD_PROFILE + 0x0C, b"\0")
        uc.mem_write(NEW_PROFILE + 0x0C, b"\1")
        for i, value in enumerate((0xAABBCCDD, 0x11223344)):
            rec = OBJECT + 0x37C + i * 0x8C
            table = DATA_BASE + 0x10000 + i * 0x100
            uc.mem_write(rec + 0x64, struct.pack("<I", table))
            uc.mem_write(table + 4, struct.pack("<I", value))
    return setup


def mutate_store_order(source_text: str) -> str:
    block = '''    const u32 word_index = index * 3u + (selector == 0 ? 0u : 1u);
    const u32 selected_address = table_address + word_index * 4u;
    const u32 selected_value =
        *reinterpret_cast<volatile const u32*>(selected_address);
'''
    if source_text.count(block) != 1:
        raise ValueError("store-order mutation anchor mismatch")
    source_text = source_text.replace(block, "")
    anchor = "    if (table_address == 0) {\n        return reinterpret_cast<u32>(record);\n    }\n\n"
    if source_text.count(anchor) != 1:
        raise ValueError("store-order insertion anchor mismatch")
    return source_text.replace(anchor, anchor + block, 1)


def run_control(out: Path, original: bytes, label: str, transform, case):
    text = SOURCE.read_text(encoding="utf-8")
    mutated = transform(text)
    if mutated == text:
        raise ValueError(f"mutation did not change source: {label}")
    src = out / "mutants" / f"{label}.cpp"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(mutated, encoding="utf-8")
    body, _args, _obj = compile_body(out / "mutants" / label / "compile", src)
    mutant = stage_image(original, body)[0]
    label0, rec, idx, sel, setup = case
    result, ref, got = direct_compare(original, mutant, label0, rec, idx, sel, setup)
    detected = not result["equal"]
    return {"detected": detected, "case": label0, "mutant_fault": got["fault"],
            "mutant_writes": got["writes"]}


def run_stride_instruction_control(original: bytes, body: bytes, case):
    mutated = bytearray(body)
    instruction_offset = 0x10
    word = struct.unpack_from("<I", mutated, instruction_offset)[0]
    if word != 0xE0811081:  # add r1, r1, r1, lsl #1 (index * 3)
        raise ValueError(f"unexpected scaled-index instruction: 0x{word:08x}")
    struct.pack_into("<I", mutated, instruction_offset,
                     (word & ~(0x1F << 7)) | (2 << 7))
    mutant = stage_image(original, bytes(mutated))[0]
    label, rec, idx, sel, setup = case
    result, _ref, got = direct_compare(original, mutant, label, rec, idx, sel, setup)
    return {"detected": not result["equal"], "case": label,
            "mutant_fault": got["fault"], "mutant_writes": got["writes"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned original image hash mismatch")
    body, compiler_args, obj = compile_body(args.out / "compile")
    staged, patch = stage_image(original, body)
    (args.out / "staged-image.bin").write_bytes(staged)
    (args.out / "staged-entry.ips").write_bytes(patch)

    normal_record = OBJECT + 0x20000
    tests = [
        ("null_table_full_args", normal_record, 0xFFFFFFFF, 0x100,
         setup_direct(normal_record, 0, 0xFFFFFFFF, 0x100)),
        ("index_zero_selector_zero", normal_record, 0, 0,
         setup_direct(normal_record, DATA_BASE + 0x10000, 0, 0)),
        ("index_one_selector_one", normal_record, 1, 1,
         setup_direct(normal_record, DATA_BASE + 0x10000, 1, 1, 0x11112222, 0x33334444)),
        ("selector_256_full_width_branch", normal_record, 0, 0x100,
         setup_direct(normal_record, DATA_BASE + 0x10000, 0, 0x100, 0x01234567, 0x89ABCDEF)),
        ("selector_high_full_width", normal_record, 2, U32,
         setup_direct(normal_record, DATA_BASE + 0x10000, 2, U32, 0x0BADCAFE, 0xFEEDBEEF)),
        ("index_ffff", normal_record, 0xFFFF, 1,
         setup_direct(normal_record, DATA_BASE + 0x10000, 0xFFFF, 1)),
        ("index_10000_full_width", normal_record, 0x10000, 1,
         setup_direct(normal_record, DATA_BASE + 0x20000, 0x10000, 1, 0x13572468, 0x24681357)),
        ("index_uint32_wrap", normal_record, U32, 1,
         setup_direct(normal_record, DATA_BASE + 0xC, U32, 1, 0xCAFEBABE, 0xDEADBEEF)),
        ("alias_metadata_before_selected_load", normal_record, 0, 0,
         setup_direct(normal_record, normal_record + 0x68, 0, 0,
                      0xA1A2A3A4, 0xB1B2B3B4, alias=True)),
        ("alias_selector_byte_before_selected_load", normal_record, 0, 0,
         setup_direct(normal_record, normal_record + 0x6C, 0, 0,
                      0xA1A2A3A4, 0xB1B2B3B4, alias=True)),
        ("invalid_record_fault", INVALID, 0, 1, lambda _uc: None),
        ("invalid_selected_table_fault_after_metadata", normal_record, 1, 0,
         setup_direct(normal_record, INVALID, 1, 0)),
    ]
    direct, mismatches = [], []
    for label, rec, idx, sel, setup in tests:
        result, ref, got = direct_compare(original, staged, label, rec, idx, sel, setup)
        direct.append(result)
        if not result["equal"]:
            mismatches.append({"case": label, "original_fault": ref["fault"],
                               "candidate_fault": got["fault"]})

    caller_ref = Machine(original, seed=880).run(SELECTOR, (0xDC, 0, 0), caller_setup(), SELECTOR_STOP)
    caller_got = Machine(staged, seed=880).run(SELECTOR, (0xDC, 0, 0), caller_setup(), SELECTOR_STOP)
    caller_keys = ("fault", "fault_detail", "r0", "sp", "callee_saved", "data", "global_words", "events", "writes")
    caller = {"equal": all(caller_ref[k] == caller_got[k] for k in caller_keys),
              "entry": hex(SELECTOR), "request": hex(0xDC), "fault": caller_got["fault"],
              "r0": hex(caller_got["r0"]), "events": caller_got["events"],
              "writes": caller_got["writes"]}
    if not caller["equal"]:
        mismatches.append({"caller": caller, "ref_fault": caller_ref["fault"],
                           "candidate_fault": caller_got["fault"]})

    controls = {
        "stride": run_stride_instruction_control(original, body,
            ("index_one_selector_one", normal_record, 1, 1,
             setup_direct(normal_record, DATA_BASE + 0x10000, 1, 1, 0x11112222, 0x33334444))),
        "branch": run_control(args.out, original, "branch",
            lambda s: s.replace("selector == 0 ? 0u : 1u",
                                "static_cast<u8>(selector) == 0 ? 0u : 1u"),
            ("selector_256_full_width_branch", normal_record, 0, 0x100,
             setup_direct(normal_record, DATA_BASE + 0x10000, 0, 0x100, 0x01234567, 0x89ABCDEF))),
        "field_offset": run_control(args.out, original, "field_offset",
            lambda s: s.replace("bytes + 0x2C", "bytes + 0x30"),
            ("index_one_selector_one", normal_record, 1, 1,
             setup_direct(normal_record, DATA_BASE + 0x10000, 1, 1, 0x11112222, 0x33334444))),
        "store_order": run_control(args.out, original, "store_order", mutate_store_order,
            ("alias_metadata_before_selected_load", normal_record, 0, 0,
             setup_direct(normal_record, normal_record + 0x68, 0, 0,
                          0xA1A2A3A4, 0xB1B2B3B4, alias=True))),
    }
    for name, value in controls.items():
        if not value["detected"]:
            mismatches.append({"mutation": name, "result": value})

    off = ENTRY - CODE_BASE
    changed_outside = any(a != b and not off <= i < off + SLOT
                          for i, (a, b) in enumerate(zip(original, staged)))
    report = {"schema_version": 1, "image_sha256": sha(original),
              "source_sha256": sha(SOURCE.read_bytes()), "object_sha256": sha(obj.read_bytes()),
              "entry": hex(ENTRY), "slot_size": SLOT, "compiled_body_size": len(body),
              "exact_matching": staged[off:off + SLOT] == original[off:off + SLOT],
              "relocations": [], "direct_cases": direct, "caller_case": caller,
              "mutation_controls": controls, "mismatch_count": len(mismatches),
              "mismatches": mismatches, "ips_replay": apply_ips(original, patch) == staged,
              "changed_outside_slot": changed_outside, "compiler_command": compiler_args}
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"body_size": len(body), "exact_matching": report["exact_matching"],
                      "direct_cases": [{"label": x["label"], "equal": x["equal"], "fault": x["fault"]} for x in direct],
                      "caller_equal": caller["equal"], "caller_events": caller["events"],
                      "mutation_controls": controls, "mismatch_count": len(mismatches),
                      "ips_replay": report["ips_replay"], "changed_outside_slot": changed_outside}, indent=2))
    return 1 if mismatches or changed_outside else 0


if __name__ == "__main__":
    raise SystemExit(main())
