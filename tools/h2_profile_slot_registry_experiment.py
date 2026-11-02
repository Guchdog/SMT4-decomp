#!/usr/bin/env python3
"""Final-VMA differential and H2 caller composition for 0x002B8794."""
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
SOURCE = ROOT / "src/engine/leaf_batch41_a.cpp"
ENTRY, SLOT = 0x002B8794, 304
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
DATA_BASE, DATA_SIZE = 0x00500000, 0x00020000
MANAGER_GLOBAL, GLOBAL_SIZE = 0x0043D000, 0x00002000
TBB_GLOBAL, TBB_GLOBAL_SIZE = 0x00493000, 0x00003000
MANAGER_POINTER = 0x0043DA2C
REGISTRY = 0x0043DA50
TBB_SLOTS = 0x0049382C
OBJECT, CONTAINER, TABLE = DATA_BASE, DATA_BASE + 0x8000, DATA_BASE + 0x8010
PAYLOAD, STACK = TABLE + 0x10, 0x08000000
STACK_SIZE, SP, STOP = 0x10000, STACK + 0x8000, STACK + 0x9000
TBL1, TBCR, U32 = 0x314C4254, 0x52434254, 0xFFFFFFFF
HOOKS = {0x002B85BC: 1, 0x0013851C: 1, 0x002AE874: 1}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_body(out: Path, source: Path = SOURCE):
    out.mkdir(parents=True, exist_ok=True)
    obj = out / source.name.replace(".cpp", ".o")
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "ARMv6K translation unit compile failed")
    body, relocs = extract_elf_functions_detailed(obj)["camp_func_002b8794"]
    if len(body) > SLOT or len(body) % 4:
        raise ValueError(f"body exceeds original slot: {len(body)}/{SLOT}")
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
        raise AssertionError("slot IPS replay mismatch")
    return staged, patch


def init_globals(uc, manager_address: int):
    uc.mem_write(MANAGER_POINTER, struct.pack("<I", manager_address))


class Machine:
    def __init__(self, image: bytes, seed: int = 1):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM,
                             unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
        self.uc.mem_map(CODE_BASE, CODE_SIZE)
        self.uc.mem_write(CODE_BASE, image)
        self.uc.mem_map(DATA_BASE, DATA_SIZE)
        self.uc.mem_map(TBB_GLOBAL, TBB_GLOBAL_SIZE)
        self.uc.mem_map(STACK, STACK_SIZE)
        rng = random.Random(seed)
        self.uc.mem_write(DATA_BASE, bytes(rng.randrange(256) for _ in range(DATA_SIZE)))
        self.uc.mem_write(MANAGER_GLOBAL, bytes(GLOBAL_SIZE))
        self.uc.mem_write(TBB_GLOBAL, bytes(TBB_GLOBAL_SIZE))
        self.events, self.writes = [], []
        self.stop = STOP
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _on_code(self, uc, address, _size, _data):
        if address == self.stop:
            uc.emu_stop()
            return
        if address == ENTRY:
            args = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4)]
            self.events.append({"address": hex(address), "args": args,
                                "sp_aligned": (uc.reg_read(arm.UC_ARM_REG_SP) & 7) == 0})
        elif address in HOOKS:
            argc = HOOKS[address]
            args = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(argc)]
            self.events.append({"address": hex(address), "args": args,
                                "sp_aligned": (uc.reg_read(arm.UC_ARM_REG_SP) & 7) == 0})
            if address == 0x002B85BC:
                result = 0xB85BC000 | (args[0] & 0xFFFF)
            elif address == 0x0013851C:
                result = 0x13851000 | (args[0] & 0xFFFF)
            else:
                result = 0xAE870000 | (args[0] & 0xFFFF)
            uc.reg_write(arm.UC_ARM_REG_R0, result & U32)
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

    def _on_write(self, _uc, _access, address, size, value, _data):
        if not STACK <= address < STACK + STACK_SIZE:
            self.writes.append([address, size, value & U32])

    def run(self, entry: int, args: tuple[int, int, int, int], setup=None, stop=STOP):
        if setup:
            setup(self.uc)
        self.stop = stop
        regs = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13)]
        initial = [(0xA1000000 + i * 0x01010101) & U32 for i in range(13)]
        for reg, value in zip(regs, initial):
            self.uc.reg_write(reg, value)
        for i, value in enumerate(args):
            self.uc.reg_write(regs[i], value & U32)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, STOP)
        fault = None
        try:
            self.uc.emu_start(entry, 0, count=100000)
        except unicorn.UcError as error:
            fault = str(error)
        after = [self.uc.reg_read(reg) for reg in regs]
        return {"fault": fault, "r0": after[0], "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
                "callee_saved": after[4:12] == initial[4:12],
                "manager_memory": bytes(self.uc.mem_read(DATA_BASE, DATA_SIZE)),
                "manager_globals": bytes(self.uc.mem_read(MANAGER_GLOBAL, GLOBAL_SIZE)),
                "tbb_globals": bytes(self.uc.mem_read(TBB_GLOBAL, TBB_GLOBAL_SIZE)),
                "events": self.events.copy(), "writes": self.writes.copy()}


def direct_setup(manager_address: int, first_registry: tuple[int, ...] | None = None,
                 second_registry: tuple[int, ...] | None = None,
                 reservations: bytes = b"\0" * 6):
    def setup(uc):
        init_globals(uc, manager_address)
        if manager_address:
            uc.mem_write(manager_address, bytes([0x5A]) * 0x1000)
            uc.mem_write(manager_address + 0x4B8, reservations[:6])
        if first_registry:
            uc.mem_write(REGISTRY, struct.pack("<6I", *first_registry))
        if second_registry:
            uc.mem_write(REGISTRY + 0x18, struct.pack("<6I", *second_registry))
    return setup


def call_setup(request: int):
    def setup(uc):
        init_globals(uc, OBJECT)
        uc.mem_write(OBJECT, bytes(0x1000))
        uc.mem_write(OBJECT + 0x4C9, b"\x09")
        uc.mem_write(TBB_SLOTS + 14 * 16 + 4, struct.pack("<I", CONTAINER))
        uc.mem_write(CONTAINER, struct.pack("<4I", TBCR, 16, 1, 0))
        uc.mem_write(TABLE, struct.pack("<4I", TBL1, 0x100 * 16, 16, 0))
        old = bytes((0x21 + i * 7) & 0xFF for i in range(16))
        new = bytearray((0x49 + i * 11) & 0xFF for i in range(16))
        struct.pack_into("<H", new, 0, 1)
        struct.pack_into("<H", new, 2, 0x100)
        old_data = bytearray(old)
        old_data[0x0C] = 1
        new[0x0C] = 0
        uc.mem_write(PAYLOAD + 9 * 16, bytes(old_data))
        uc.mem_write(PAYLOAD + request * 16, bytes(new))
    return setup


def invoke(image: bytes, entry: int, args: tuple[int, int, int, int], setup=None):
    return Machine(image, seed=919).run(entry, args, setup)


def case_result(original: bytes, staged: bytes, label: str, args, setup):
    ref = invoke(original, ENTRY, args, setup)
    got = invoke(staged, ENTRY, args, setup)
    comparable_ref = {k: v for k, v in ref.items() if k != "r0"}
    comparable_got = {k: v for k, v in got.items() if k != "r0"}
    return {"label": label, "equal": comparable_ref == comparable_got,
            "fault": got["fault"], "writes": got["writes"], "events": got["events"]}, ref, got


def run_control(out: Path, original: bytes, label: str, before: str, after: str, args, setup):
    source_text = SOURCE.read_text(encoding="utf-8")
    if source_text.count(before) != 1:
        raise ValueError(f"mutation anchor is not unique: {label}")
    source = out / "mutants" / f"{label}.cpp"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(source_text.replace(before, after), encoding="utf-8")
    body, _compiler, _obj = compile_body(out / "mutants" / label / "compile", source)
    mutant = stage_image(original, body)[0]
    ref = invoke(original, ENTRY, args, setup)
    got = invoke(mutant, ENTRY, args, setup)
    return {"detected": any(ref[k] != got[k] for k in
            ("manager_memory", "manager_globals", "tbb_globals", "writes", "fault")),
            "case": label, "mutant_fault": got["fault"]}


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

    direct_cases = [
        ("slot_zero_default", (0, 0x12, 0x51, 0), direct_setup(OBJECT)),
        ("slot_five_special", (5, 7, 0x100, 0), direct_setup(OBJECT)),
        ("priority_eight", (1, 8, 0xFFFF, 0), direct_setup(OBJECT)),
        ("priority_nine", (2, 9, 0x12345, 0), direct_setup(OBJECT)),
        ("priority_seventeen", (3, 17, 0xABCDEF01, 0), direct_setup(OBJECT)),
        ("priority_eighteen_default", (4, 18, 0x51, 0), direct_setup(OBJECT)),
        ("slot_boundary_six", (6, 8, 0x1234, 0), direct_setup(OBJECT)),
        ("slot_max_unsigned", (U32, 8, 0x1234, 0), direct_setup(OBJECT)),
        ("null_manager", (2, 9, 0x55, 0), direct_setup(0)),
        ("registry_claim", (2, 9, 0x55, 1),
         direct_setup(OBJECT, (0, 0, U32, 0, 0, 0), (0, 0, 0, 0, 0, 0),
                      b"\0\1\0\0\0\0")),
        ("registry_release", (2, 9, 0x55, 1),
         direct_setup(OBJECT, (0, 0, 9, 0, 0, 0), (0, 0, 0x55, 0, 0, 0), b"\0" * 6)),
        ("registry_no_claim", (2, 0x12, 0x51, 1),
         direct_setup(OBJECT, (0, 0, U32, 0, 0, 0), (0, 0, 0, 0, 0, 0), b"\0" * 6)),
    ]
    directs, mismatches = [], []
    for label, call_args, setup in direct_cases:
        result, ref, got = case_result(original, staged, label, call_args, setup)
        directs.append(result)
        if not result["equal"]:
            mismatches.append({"case": label, "original": ref, "candidate": got})

    callers = []
    for site, stop, request, label in (
        (0x002F4DEC, 0x002F4DF4, 0x99, "title_config_init_0x99"),
        (0x00286B7C, 0x00286B84, 0xDC, "nested_callback_0xDC"),
    ):
        ref = Machine(original, seed=920).run(site, (request, 0, 0, 0), call_setup(request), stop)
        got_machine = Machine(staged, seed=920)
        got = got_machine.run(site, (request, 0, 0, 0), call_setup(request), stop)
        equal = ref == got
        callers.append({"caller": label, "start": hex(site), "stop": hex(stop),
                        "request": hex(request), "equal": equal,
                        "r0": hex(got["r0"]), "events": got["events"],
                        "fault": got["fault"]})
        if not equal:
            mismatches.append({"caller": label, "original": ref, "candidate": got})

    controls = {
        "slot_boundary": run_control(args.out, original, "slot_boundary",
            "slot >= 6", "slot > 6", (6, 8, 1, 0), direct_setup(OBJECT)),
        "priority_eight": run_control(args.out, original, "priority_eight",
            "priority == 8", "priority == 7", (1, 8, 0xFFFF, 0), direct_setup(OBJECT)),
        "registry_mode": run_control(args.out, original, "registry_mode",
            "if (mode != 0)", "if (mode == 0)", (2, 9, 0x55, 1),
            direct_setup(OBJECT, (0, 0, U32, 0, 0, 0), (0, 0, 0, 0, 0, 0),
                         b"\0\1\0\0\0\0")),
    }
    for label, result in controls.items():
        if not result["detected"]:
            mismatches.append({"mutation": label, "case": result})

    off = ENTRY - CODE_BASE
    changed_outside = any(a != b and not off <= i < off + SLOT
                          for i, (a, b) in enumerate(zip(original, staged)))
    report = {"schema_version": 1, "image_sha256": sha(original),
              "source_sha256": sha(SOURCE.read_bytes()), "object_sha256": sha(obj.read_bytes()),
              "entry": hex(ENTRY), "slot_size": SLOT, "compiled_body_size": len(body),
              "exact_matching": staged[off:off + SLOT] == original[off:off + SLOT],
              "relocations": [], "direct_cases": directs, "caller_cases": callers,
              "mutation_controls": controls, "mismatch_count": len(mismatches),
              "mismatches": mismatches, "ips_replay": apply_ips(original, patch) == staged,
              "changed_outside_slot": changed_outside, "compiler_command": compiler_args}
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"body_size": len(body), "exact_matching": report["exact_matching"],
                      "direct_cases": directs, "caller_cases": callers,
                      "mutation_controls": controls, "mismatch_count": len(mismatches),
                      "ips_replay": report["ips_replay"],
                      "changed_outside_slot": changed_outside}, indent=2))
    return 1 if mismatches or changed_outside else 0


if __name__ == "__main__":
    raise SystemExit(main())
