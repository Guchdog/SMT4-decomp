#!/usr/bin/env python3
"""Bounded final-VMA differential for 0x002B85BC and H2 caller slices."""
from __future__ import annotations

import argparse
import csv
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
SOURCE = ROOT / "src/engine/leaf_batch44_c.cpp"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
ENTRY, SLOT = 0x002B85BC, 472
WRAPPER = 0x002B8B78
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
DATA_BASE, DATA_SIZE = 0x00500000, 0x00020000
GLOBAL_BASE, GLOBAL_SIZE = 0x0043D000, 0x00002000
MANAGER_ROOT = 0x0043DA28
OBJECT, ALT_OBJECT = DATA_BASE, DATA_BASE + 0x2000
OLD_PROFILE, NEW_PROFILE = DATA_BASE + 0x8000, DATA_BASE + 0x8100
STACK, STACK_SIZE = 0x08000000, 0x00010000
SP, STOP = STACK + 0x8000, STACK + 0x9000
U32 = 0xFFFFFFFF

CALLEES = {
    0x002AEA28: ("camp_func_002aea28", 1),
    0x002BF030: ("camp_func_002bf030", 2),
    0x002A8A8C: ("ui_func_002a8a8c", 0),
    0x002BDAC0: ("camp_func_002bdac0", 3),
    0x002AA268: ("camp_func_002aa268", 3),
}
WRAPPER_CALLEES = {
    **CALLEES,
    0x002B8794: ("camp_func_002b8794", 4),
    0x0013851C: ("script_vm_func_0013851c", 1),
    0x002AE874: ("camp_func_002ae874", 1),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rows_by_name() -> dict[str, int]:
    with (ROOT / "config/functions.csv").open(encoding="utf-8-sig", newline="") as f:
        return {row["name"]: int(row["address"], 0) for row in csv.DictReader(f)}


def compile_body(out: Path, source: Path = SOURCE):
    out.mkdir(parents=True, exist_ok=True)
    obj = out / source.name.replace(".cpp", ".o")
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "ARMv6K TU compile failed")
    body, relocs = extract_elf_functions_detailed(obj)["ui_func_002b85bc"]
    if len(body) > SLOT or len(body) % 4:
        raise ValueError(f"candidate body does not fit 472-byte slot: {len(body)}")
    return body, relocs, list(result.args), obj


def stage_image(original: bytes, body: bytes, relocs):
    fixed = bytearray(body)
    names = rows_by_name()
    resolved = []
    for reloc in relocs:
        word = struct.unpack_from("<I", fixed, reloc.offset)[0]
        if reloc.relocation_type not in (28, 29):
            raise ValueError(f"unsupported relocation type {reloc.relocation_type}: {reloc}")
        name = reloc.symbol_name
        if name not in names:
            raise ValueError(f"unmapped relocation symbol {name}")
        target = names[name]
        site = ENTRY + reloc.offset
        delta = target - (site + 8)
        if target & 1 or delta & 3 or not -(1 << 25) <= delta < (1 << 25):
            raise ValueError(f"invalid ARM branch target {name}={target:#x} at {site:#x}")
        if reloc.relocation_type == 28 and word & 0xFF000000 != 0xEB000000:
            raise ValueError(f"expected ARM BL at relocation {reloc.offset:#x}: {word:#x}")
        if reloc.relocation_type == 29 and word & 0x0F000000 != 0x0A000000:
            raise ValueError(f"expected ARM B at relocation {reloc.offset:#x}: {word:#x}")
        struct.pack_into("<I", fixed, reloc.offset,
                         (word & 0xFF000000) | ((delta >> 2) & 0x00FFFFFF))
        resolved.append({"offset": reloc.offset, "symbol": name, "target": hex(target),
                         "target_bit0_clear": True, "relocation_type": reloc.relocation_type})
    off = ENTRY - CODE_BASE
    payload = bytes(fixed) + original[off + len(fixed):off + SLOT]
    staged = bytearray(original)
    staged[off:off + SLOT] = payload
    staged = bytes(staged)
    patch = encode_ips([(off, payload)], len(original))
    if apply_ips(original, patch) != staged:
        raise AssertionError("slot IPS replay mismatch")
    return staged, patch, payload, resolved


def write_u32(uc, address: int, value: int):
    uc.mem_write(address, struct.pack("<I", value & U32))


def fixture_setup(*, old_flag=1, new_flag=0, statuses=(0, 0, 0, 0, 0, 0), mode=0,
                  lookup_results=None, mutate_manager_on=None,
                  mutate_status_on_service=None, mutate_status_slot=0, mutate_status_value=8):
    def setup(uc):
        uc.mem_write(GLOBAL_BASE, bytes(GLOBAL_SIZE))
        uc.mem_write(DATA_BASE, bytes(DATA_SIZE))
        old = bytearray(0x20)
        new = bytearray(0x20)
        old[0x0C] = old_flag
        new[0x0C] = new_flag
        struct.pack_into("<6H", new, 0, 0, 1, 0x100, 0xFFFF, 7, 9)
        uc.mem_write(OLD_PROFILE, bytes(old))
        uc.mem_write(NEW_PROFILE, bytes(new))
        for obj in (OBJECT, ALT_OBJECT):
            raw = bytearray(0x600)
            raw[0x4C8] = mode
            raw[0x4C9] = 3
            for i, status in enumerate(statuses):
                raw[0x494 + i * 4] = status & 0xFF
            uc.mem_write(obj, bytes(raw))
        write_u32(uc, MANAGER_ROOT + 4, OBJECT)
        write_u32(uc, MANAGER_ROOT + 0x10, 0)
        uc.mem_write(MANAGER_ROOT + 0x10, struct.pack("<i", 0))
        uc.mem_write(MANAGER_ROOT + 0x4B8, b"\0" * 6)
        return {"lookup_results": lookup_results or [OLD_PROFILE, NEW_PROFILE],
                "mutate_manager_on": mutate_manager_on, "object_switched": False,
                "mutate_status_on_service": mutate_status_on_service,
                "mutate_status_slot": mutate_status_slot,
                "mutate_status_value": mutate_status_value,
                "service_calls": 0}
    return setup


class Machine:
    def __init__(self, image: bytes, *, seed: int = 7, setup=None):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
        self.uc.mem_map(CODE_BASE, CODE_SIZE)
        self.uc.mem_write(CODE_BASE, image)
        self.uc.mem_map(DATA_BASE, DATA_SIZE)
        self.uc.mem_map(STACK, STACK_SIZE)
        rng = random.Random(seed)
        self.uc.mem_write(DATA_BASE, bytes(rng.randrange(256) for _ in range(DATA_SIZE)))
        self.events, self.writes = [], []
        self.fault_detail = None
        self.stop = STOP
        self.state = setup(self.uc) if setup else fixture_setup()(self.uc)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_READ_UNMAPPED, self._on_unmapped)

    def _on_unmapped(self, _uc, access, address, size, value, _data):
        self.fault_detail = {"access": access, "address": address, "size": size}
        return False

    def _on_write(self, _uc, _access, address, size, value, _data):
        if not STACK <= address < STACK + STACK_SIZE:
            self.writes.append([address, size, value & U32])

    def _hook_call(self, address: int):
        uc = self.uc
        name, argc = WRAPPER_CALLEES[address]
        args = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(argc)]
        self.events.append({"address": hex(address), "name": name,
                            "args": args, "sp_aligned": (uc.reg_read(arm.UC_ARM_REG_SP) & 7) == 0})
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        if address == 0x002AEA28:
            lookup_i = sum(1 for event in self.events if event["address"] == hex(address)) - 1
            results = self.state["lookup_results"]
            result = results[lookup_i] if lookup_i < len(results) else NEW_PROFILE
        elif address == 0x002BF030:
            call_i = sum(1 for event in self.events if event["address"] == hex(address))
            if self.state["mutate_manager_on"] == call_i and not self.state["object_switched"]:
                write_u32(uc, MANAGER_ROOT + 4, ALT_OBJECT)
                self.state["object_switched"] = True
            result = 0xBF030000 | (r0 & 0xFFFF)
        elif address == 0x002A8A8C:
            self.state["service_calls"] += 1
            if self.state["service_calls"] == self.state["mutate_status_on_service"]:
                status_address = OBJECT + 0x494 + self.state["mutate_status_slot"] * 4
                uc.mem_write(status_address, bytes([self.state["mutate_status_value"] & 0xFF]))
            result = 0xA8A80001
        elif address == 0x002BDAC0:
            result = 0xBDAC0003
        elif address == 0x002AA268:
            result = 0xAA268001
        elif address == 0x002B8794:
            result = 0xB87940000 | (r0 & 0xFFFF)
        elif address == 0x0013851C:
            result = 0x13851000 | (r0 & 0xFFFF)
        else:
            result = 0xAE874000 | (r0 & 0xFFFF)
        uc.reg_write(arm.UC_ARM_REG_R0, result & U32)
        uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

    def _on_code(self, uc, address, _size, _data):
        if address == self.stop:
            uc.emu_stop()
            return
        if address in WRAPPER_CALLEES:
            self._hook_call(address)

    def run(self, entry: int, args: tuple[int, int, int, int], *, stop=STOP):
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
        return {"fault": fault, "fault_detail": self.fault_detail,
                "r0": after[0], "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
                "callee_saved": after[4:12] == initial[4:12],
                "data": bytes(self.uc.mem_read(DATA_BASE, DATA_SIZE)),
                "globals": bytes(self.uc.mem_read(GLOBAL_BASE, GLOBAL_SIZE)),
                "events": self.events.copy(), "writes": self.writes.copy()}


def invoke(image, entry, args, setup, *, stop=STOP, seed=7):
    machine = Machine(image, seed=seed, setup=setup)
    return machine.run(entry, args, stop=stop)


def compare_case(original, staged, label, args, setup, *, entry=ENTRY, stop=STOP, seed=7):
    ref = invoke(original, entry, args, setup, stop=stop, seed=seed)
    got = invoke(staged, entry, args, setup, stop=stop, seed=seed)
    if ref["fault"] is not None or got["fault"] is not None:
        # Different prologues may have different transient SP/save state at the
        # same first unmapped dereference; compare fault class and prior effects.
        equal = (ref["fault"] == got["fault"] and ref["fault_detail"] == got["fault_detail"]
                 and ref["data"] == got["data"]
                 and ref["globals"] == got["globals"] and ref["events"] == got["events"]
                 and ref["writes"] == got["writes"])
    else:
        equal = ref == got
    return {"label": label, "equal": equal, "fault": got["fault"],
            "fault_detail": got["fault_detail"],
            "r0": hex(got["r0"]), "sp": hex(got["sp"]),
            "callee_saved": got["callee_saved"], "events": got["events"],
            "write_count": len(got["writes"])}, ref, got


def brief(result):
    return {"fault": result["fault"], "fault_detail": result["fault_detail"],
            "r0": hex(result["r0"]), "sp": hex(result["sp"]),
            "callee_saved": result["callee_saved"], "data_sha256": sha(result["data"]),
            "globals_sha256": sha(result["globals"]), "events": result["events"],
            "writes": result["writes"]}


def run_control(out, original, label, before, after, args, setup, *, entry=ENTRY, stop=STOP):
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(before) < 1:
        raise ValueError(f"mutation anchor for {label} is missing")
    mutant_source = out / "mutants" / f"{label}.cpp"
    mutant_source.parent.mkdir(parents=True, exist_ok=True)
    mutant_source.write_text(text.replace(before, after), encoding="utf-8")
    body, relocs, _args, _obj = compile_body(out / "mutants" / label / "compile", mutant_source)
    mutant = stage_image(original, body, relocs)[0]
    ref = invoke(original, entry, args, setup, stop=stop)
    got = invoke(mutant, entry, args, setup, stop=stop)
    detected = any(ref[k] != got[k] for k in ("r0", "data", "globals", "events", "writes", "fault"))
    return {"detected": detected, "label": label, "mutant_fault": got["fault"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned original image hash mismatch")
    body, relocs, compiler_args, obj = compile_body(args.out / "compile")
    staged, patch, _payload, resolved = stage_image(original, body, relocs)
    (args.out / "staged-image.bin").write_bytes(staged)
    (args.out / "staged-entry.ips").write_bytes(patch)

    statuses = (0, 1, 7, 8, 9, 0x22)
    direct_specs = [
        ("old_profile_null", [0, NEW_PROFILE], fixture_setup(lookup_results=[0, NEW_PROFILE])),
        ("new_profile_null", [OLD_PROFILE, 0], fixture_setup(lookup_results=[OLD_PROFILE, 0])),
        ("old_active_status_matrix", [OLD_PROFILE, NEW_PROFILE],
         fixture_setup(old_flag=1, new_flag=0, statuses=statuses)),
        ("status_7_mutates_to_8_then_three_call_block", [OLD_PROFILE, NEW_PROFILE],
         fixture_setup(old_flag=1, new_flag=0, statuses=(7, 0, 0, 0, 0, 0),
                       mutate_status_on_service=1, mutate_status_slot=0, mutate_status_value=8)),
        ("new_active_status_clear_mode_1", [OLD_PROFILE, NEW_PROFILE],
         fixture_setup(old_flag=0, new_flag=1, statuses=statuses, mode=1)),
        ("new_active_status_clear_mode_2", [OLD_PROFILE, NEW_PROFILE],
         fixture_setup(old_flag=0, new_flag=1, statuses=statuses, mode=2)),
        ("both_profile_flags_zero", [OLD_PROFILE, NEW_PROFILE],
         fixture_setup(old_flag=0, new_flag=0, statuses=statuses)),
        ("manager_pointer_reload", [OLD_PROFILE, NEW_PROFILE],
         fixture_setup(old_flag=0, new_flag=1, statuses=statuses, mode=1, mutate_manager_on=1)),
        ("null_object_fault", [OLD_PROFILE, NEW_PROFILE], fixture_setup()),
    ]
    direct_results, mismatches = [], []
    for i, (label, lookups, setup) in enumerate(direct_specs):
        if label == "null_object_fault":
            def null_setup(uc):
                state = fixture_setup(lookup_results=lookups)(uc)
                write_u32(uc, MANAGER_ROOT + 4, 0)
                return state
            setup = null_setup
        result, ref, got = compare_case(original, staged, label, (0xDC, 0, 0, 0), setup, seed=900 + i)
        direct_results.append(result)
        if not result["equal"]:
            mismatches.append({"case": label, "original": brief(ref), "candidate": brief(got)})

    caller_results = []
    for i, (site, stop, request, label) in enumerate((
        (0x002F4DEC, 0x002F4DF4, 0x99, "title_config_init_request_0x99"),
        (0x00286B7C, 0x00286B84, 0xDC, "nested_callback_request_0xDC"),
    )):
        setup = fixture_setup(old_flag=1, new_flag=0, statuses=(0, 1, 7, 8, 9, 0x22),
                              lookup_results=[OLD_PROFILE, NEW_PROFILE, OLD_PROFILE, NEW_PROFILE])
        result, ref, got = compare_case(original, staged, label, (request, 0, 0, 0), setup,
                                        entry=site, stop=stop, seed=950 + i)
        caller_results.append(result)
        if not result["equal"]:
            mismatches.append({"caller": label, "original": brief(ref), "candidate": brief(got)})

    old_active = fixture_setup(old_flag=1, statuses=(7, 0, 0, 0, 0, 0))
    new_active = fixture_setup(old_flag=0, new_flag=1, statuses=(1, 0, 0, 0, 0, 0), mode=1)
    controls = {
        "loop_bound": run_control(args.out, original, "loop_bound",
            "object + 0x34 + slot * 0x8C", "object + 0x34 + slot * 0x88",
            (0xDC, 0, 0, 0), old_active),
        "status_clear": run_control(args.out, original, "status_clear",
            "object[status_offset] = 0;", "object[status_offset] = 1;", (0xDC, 0, 0, 0), new_active),
        "service_multiplicity": run_control(args.out, original, "service_multiplicity",
            "            ui_func_002a8a8c();\n            ui_func_002a8a8c();\n            ui_func_002a8a8c();",
            "ui_func_002a8a8c();", (0xDC, 0, 0, 0),
            fixture_setup(old_flag=1, statuses=(8, 0, 0, 0, 0, 0))),
        "two_slot_args": run_control(args.out, original, "two_slot_args",
            "camp_func_002bdac0(const_cast<u8*>(slot_record), 3, 0);",
            "camp_func_002bdac0(const_cast<u8*>(slot_record), 0, 3);",
            (0xDC, 0, 0, 0), new_active),
        "cleanup_value": run_control(args.out, original, "cleanup_value",
            "reinterpret_cast<volatile u32*>(cleanup_object + 0x10) = 3;",
            "reinterpret_cast<volatile u32*>(cleanup_object + 0x10) = 4;",
            (0xDC, 0, 0, 0), old_active),
    }
    for name, result in controls.items():
        if not result["detected"]:
            mismatches.append({"mutation": name, "result": result})

    off = ENTRY - CODE_BASE
    changed_outside = any(a != b and not off <= i < off + SLOT
                          for i, (a, b) in enumerate(zip(original, staged)))
    report = {
        "schema_version": 1, "image_sha256": sha(original),
        "source_sha256": sha(SOURCE.read_bytes()), "object_sha256": sha(obj.read_bytes()),
        "entry": hex(ENTRY), "slot_size": SLOT, "compiled_body_size": len(body),
        "exact_matching": staged[off:off + SLOT] == original[off:off + SLOT],
        "relocations": resolved, "direct_cases": direct_results,
        "caller_cases": caller_results, "mutation_controls": controls,
        "mismatch_count": len(mismatches), "mismatches": mismatches,
        "ips_replay": apply_ips(original, patch) == staged,
        "changed_outside_slot": changed_outside, "compiler_command": compiler_args,
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"body_size": len(body), "relocations": resolved,
                      "direct_cases": [{"label": x["label"], "equal": x["equal"],
                                       "fault": x["fault"], "fault_detail": x["fault_detail"],
                                       "r0": x["r0"]}
                                      for x in direct_results],
                      "caller_cases": [{"label": x["label"], "equal": x["equal"],
                                       "fault": x["fault"], "fault_detail": x["fault_detail"],
                                       "r0": x["r0"]}
                                      for x in caller_results],
                      "mutation_controls": controls, "mismatch_count": len(mismatches),
                      "ips_replay": report["ips_replay"],
                      "changed_outside_slot": changed_outside}, indent=2))
    return 1 if mismatches or changed_outside or not report["ips_replay"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
