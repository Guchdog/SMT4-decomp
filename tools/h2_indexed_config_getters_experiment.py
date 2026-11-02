#!/usr/bin/env python3
"""Final-VMA differential for two indexed H2 configuration getters."""
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
from tools import h2_86928_experiment as helper_experiment

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
DATA_BASE, DATA_SIZE = 0x00500000, 0x1000
GLOBAL_SLOT = 0x0043DA2C
STACK, STACK_SIZE = 0x08000000, 0x10000
SP, STOP = STACK + 0x8000, STACK + 0x9000
U32 = 0xFFFFFFFF

TARGETS = {
    "func_002f5b2c": {
        "address": 0x002F5B2C,
        "slot": 44,
        "source": ROOT / "src/engine/leaf_batch29_b.cpp",
        "offset": 0x494,
        "width": 1,
        "needle": "+ 0x494u",
    },
    "func_002d65b4": {
        "address": 0x002D65B4,
        "slot": 52,
        "source": ROOT / "src/engine/leaf_batch32_c.cpp",
        "offset": 0x496,
        "width": 2,
        "needle": "+ 0x496u",
    },
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_target(out: Path, name: str, source: Path | None = None):
    spec = TARGETS[name]
    source = source or spec["source"]
    out.mkdir(parents=True, exist_ok=True)
    obj = out / source.name.replace(".cpp", ".o")
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or f"compile failed for {name}")
    body, relocations = extract_elf_functions_detailed(obj)[name]
    if relocations:
        raise ValueError(f"unexpected relocations for {name}: {relocations}")
    if len(body) > spec["slot"] or len(body) % 4:
        raise ValueError(f"invalid body size for {name}: {len(body)} / {spec['slot']}")
    return body, list(result.args), obj


def stage(original: bytes, replacements: dict[str, bytes]):
    image = bytearray(original)
    records = []
    for name, body in replacements.items():
        spec = TARGETS[name]
        address, slot = spec["address"], spec["slot"]
        payload = body + struct.pack("<I", 0xE320F000) * ((slot - len(body)) // 4)
        offset = address - CODE_BASE
        image[offset : offset + slot] = payload
        records.append((offset, payload))
    staged = bytes(image)
    patch = encode_ips(records, len(original))
    if apply_ips(original, patch) != staged:
        raise AssertionError("slot-only IPS replay failed")
    return staged, patch


class Machine:
    def __init__(self, image: bytes, seed: int, manager: int, index: int):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
        self.uc.mem_map(CODE_BASE, CODE_SIZE)
        self.uc.mem_write(CODE_BASE, image)
        self.uc.mem_map(DATA_BASE, DATA_SIZE)
        self.uc.mem_map(STACK, STACK_SIZE)
        self.writes = []
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._write)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._stop, begin=STOP, end=STOP)
        self.rng = random.Random(seed)
        self.memory = bytes(self.rng.randrange(256) for _ in range(DATA_SIZE))
        buf = bytearray(self.memory)
        # Distinguish each indexed result and the two bounds-control locations.
        for i in range(6):
            buf[i * 4 + 0x494] = 0x21 + i
            struct.pack_into("<H", buf, i * 4 + 0x496, 0x6120 + i)
        buf[6 * 4 + 0x494] = 0xE1
        struct.pack_into("<H", buf, 6 * 4 + 0x496, 0xE261)
        self.memory = bytes(buf)
        self.uc.mem_write(DATA_BASE, self.memory)
        self.manager = manager
        self.index = index
        self.uc.mem_write(GLOBAL_SLOT, struct.pack("<I", manager))

    def _write(self, uc, _access, address, size, value, _data):
        self.writes.append((address, size, value & U32))

    @staticmethod
    def _stop(uc, _address, _size, _data):
        uc.emu_stop()

    def run(self, address: int):
        regs = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13)]
        initial = [(0xC1000000 + i * 0x01010101) & U32 for i in range(13)]
        for reg, value in zip(regs, initial):
            self.uc.reg_write(reg, value)
        self.uc.reg_write(arm.UC_ARM_REG_R0, self.index & U32)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, STOP)
        fault = None
        try:
            self.uc.emu_start(address, 0, count=256)
        except unicorn.UcError as error:
            fault = str(error)
        after = [self.uc.reg_read(reg) for reg in regs]
        return {
            "fault": fault,
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": after[4:12] == initial[4:12],
            "manager": bytes(self.uc.mem_read(DATA_BASE, DATA_SIZE)).hex(),
            "global": bytes(self.uc.mem_read(GLOBAL_SLOT, 4)).hex(),
            "writes": self.writes.copy(),
        }


def execute(image: bytes, seed: int, manager: int, index: int, address: int):
    machine = Machine(image, seed, manager, index)
    return machine.run(address)


def expected_value(name: str, memory: bytes, manager: int, index: int) -> int:
    spec = TARGETS[name]
    if manager == 0 or index >= 6:
        return 0
    offset = index * 4 + spec["offset"]
    return int.from_bytes(memory[offset : offset + spec["width"]], "little")


def run_original_caller(image: bytes, seed: int):
    """Run the pinned 0x00286928 ARM body, passing through both target getters."""
    case = helper_experiment.Case(
        seed=seed, selector=6, incoming_r2=0, state=0,
        state_2e=0, state_35=1, row=8, arg5=1, arg6=0,
        query_a=0, query_b=0, service_state=0,
    )
    uc = helper_experiment.fixture(case, image=image)
    manager = 0x00918000
    data = bytearray((i * 37 + seed) & 0xFF for i in range(DATA_SIZE))
    for i in range(6):
        data[i * 4 + 0x494] = 0x60 + i
        struct.pack_into("<H", data, i * 4 + 0x496, 0x7200 + i)
    data[6 * 4 + 0x494] = 0xE1
    struct.pack_into("<H", data, 6 * 4 + 0x496, 0xE261)
    uc.mem_write(manager, bytes(data))
    uc.mem_write(GLOBAL_SLOT, struct.pack("<I", manager))
    events = []
    writes = []
    stubs = {0x002C1F28, 0x002B89A0, 0x0028E974}

    def on_code(machine, address, _size, _data):
        if address == helper_experiment.STOP:
            machine.emu_stop()
            return
        if address in stubs:
            args = tuple(machine.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4))
            stack_args = ()
            if address == 0x0028E974:
                stack_args = tuple(struct.unpack("<III", machine.mem_read(machine.reg_read(arm.UC_ARM_REG_SP), 12)))
            events.append((address, args, stack_args, "stub-zero"))
            machine.reg_write(arm.UC_ARM_REG_R0, 0)
            machine.reg_write(arm.UC_ARM_REG_PC, machine.reg_read(arm.UC_ARM_REG_LR))
            return
        if address in (TARGETS["func_002f5b2c"]["address"], TARGETS["func_002d65b4"]["address"]):
            # These getters have one ABI input; caller-scratch r1-r3 may vary.
            args = (machine.reg_read(arm.UC_ARM_REG_R0),)
            events.append((address, args, (), "production-code"))

    def on_write(_machine, _kind, address, size, value, _data):
        writes.append((address, size, value & U32))

    uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    fault = None
    try:
        uc.emu_start(0x00286928, 0, count=10000)
    except unicorn.UcError as error:
        fault = str(error)
    regs = tuple(uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12))
    objects = tuple(bytes(uc.mem_read(base, 0x1800)) for base in helper_experiment.OBJECTS)
    final_manager = bytes(uc.mem_read(manager, DATA_SIZE))
    global_bytes = bytes(uc.mem_read(GLOBAL_SLOT, 4))
    call_sequence = [event[0] for event in events]
    getter_args = [(event[0], event[1]) for event in events
                   if event[0] in (TARGETS["func_002f5b2c"]["address"], TARGETS["func_002d65b4"]["address"])]
    expected_sequence = [0x002C1F28, 0x0028E974]
    expected_getter_args = [(address, (i,))
                            for i in range(6)
                            for address in (TARGETS["func_002f5b2c"]["address"],
                                            TARGETS["func_002d65b4"]["address"])]
    for i in range(6):
        expected_sequence.extend((0x002F5B2C, 0x002D65B4))
    valid = (
        fault is None
        and call_sequence[: len(expected_sequence)] == expected_sequence
        and getter_args == expected_getter_args
        and sum(event[0] == 0x002F5B2C for event in events) == 6
        and sum(event[0] == 0x002D65B4 for event in events) == 6
        and uc.reg_read(arm.UC_ARM_REG_SP) == 0x0080FF00
        and regs == tuple(0x22330000 + i for i in range(8))
    )
    return {
        "fault": fault,
        "valid": valid,
        "r0": uc.reg_read(arm.UC_ARM_REG_R0),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "events": events,
        "writes": writes,
        "objects": [item.hex() for item in objects],
        "manager": final_manager.hex(),
        "global": global_bytes.hex(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261120)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned original image hash mismatch")

    bodies, metadata = {}, {}
    for name, spec in TARGETS.items():
        body, compiler_args, obj = compile_target(args.out / "compile" / name, name)
        bodies[name] = body
        offset = spec["address"] - CODE_BASE
        original_body = original[offset : offset + spec["slot"]]
        metadata[name] = {
            "address": hex(spec["address"]),
            "slot_size": spec["slot"],
            "compiled_size": len(body),
            "relocations": [],
            "byte_identical": body == original_body,
            "object_sha256": sha(obj.read_bytes()),
            "compiler_command": compiler_args,
        }
    staged, patch = stage(original, bodies)
    (args.out / "staged-image.bin").write_bytes(staged)
    (args.out / "staged-slot.ips").write_bytes(patch)

    cases, mismatches = [], []
    managers = (0, DATA_BASE)
    indices = (0, 1, 2, 3, 4, 5, 6, 7, 0x7FFFFFFF, 0x80000000, U32)
    for name, spec in TARGETS.items():
        for manager_i, manager in enumerate(managers):
            for index_i, index in enumerate(indices):
                case_seed = args.seed + len(cases) * 101 + manager_i * 37 + index_i
                ref = execute(original, case_seed, manager, index, spec["address"])
                got = execute(staged, case_seed, manager, index, spec["address"])
                equal = ref == got
                expected = expected_value(name, Machine(original, case_seed, manager, index).memory, manager, index)
                valid = got["fault"] is None and got["r0"] == expected and got["sp"] == SP and got["callee_saved"]
                if not equal or not valid:
                    mismatches.append({"target": name, "manager": hex(manager), "index": hex(index),
                                       "equal": equal, "valid": valid, "original": ref, "candidate": got,
                                       "expected_r0": hex(expected)})
                cases.append({"target": name, "manager": hex(manager), "index": hex(index),
                              "equal": equal, "valid": valid, "r0": hex(got["r0"])})

    caller_compositions = []
    for caller_seed in (20261122, 20261123):
        ref = run_original_caller(original, caller_seed)
        got = run_original_caller(staged, caller_seed)
        equal = ref == got
        if not equal or not ref["valid"] or not got["valid"]:
            mismatches.append({"caller_seed": caller_seed, "equal": equal, "original": ref, "candidate": got})
        caller_compositions.append({"seed": caller_seed, "equal": equal, "valid": got["valid"],
                                    "getter_call_counts": {name: sum(event[0] == spec["address"] for event in got["events"])
                                                           for name, spec in TARGETS.items()},
                                    "getter_indices": [event[1][0] for event in got["events"]
                                                       if event[0] in (TARGETS["func_002f5b2c"]["address"],
                                                                       TARGETS["func_002d65b4"]["address"])],
                                    "external_stubs": [hex(address) for address in (0x002C1F28, 0x0028E974)]})

    controls = {}
    for name, spec in TARGETS.items():
        source_text = spec["source"].read_text(encoding="utf-8")
        mutations = {
            "wrong_field_offset": (spec["needle"], spec["needle"].replace(hex(spec["offset"]), hex(spec["offset"] + 4)), 2),
            "wrong_upper_bound": ("index >= 6", "index >= 7", 6),
        }
        for label, (before, after, case_index) in mutations.items():
            if source_text.count(before) != 1:
                raise ValueError(f"{label} mutation source anchor not unique for {name}")
            mutant_source = args.out / "mutants" / name / label / spec["source"].name
            mutant_source.parent.mkdir(parents=True, exist_ok=True)
            mutant_source.write_text(source_text.replace(before, after), encoding="utf-8")
            mutant_body, _cmd, _obj = compile_target(args.out / "mutants" / name / label / "compile", name, mutant_source)
            mutant_image, _patch = stage(original, {name: mutant_body})
            case_seed = args.seed + 9001 + spec["address"] + case_index
            ref = execute(original, case_seed, DATA_BASE, case_index, spec["address"])
            got = execute(mutant_image, case_seed, DATA_BASE, case_index, spec["address"])
            detected = ref != got
            controls[f"{name}_{label}"] = {"detected": detected, "index": case_index,
                                            "reference_r0": hex(ref["r0"]), "mutant_r0": hex(got["r0"])}
            if not detected:
                mismatches.append({"target": name, "mutation": label, "reference": ref, "mutant": got})

    report = {
        "schema_version": 1,
        "seed": args.seed,
        "image_sha256": sha(original),
        "source_sha256": {name: sha(spec["source"].read_bytes()) for name, spec in TARGETS.items()},
        "functions": metadata,
        "case_count": len(cases),
        "cases": cases,
        "caller_compositions": caller_compositions,
        "mutation_controls": controls,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "ips_replay": apply_ips(original, patch) == staged,
        "changed_slots_only": all(
            original_byte == staged_byte
            for offset, (original_byte, staged_byte) in enumerate(zip(original, staged))
            if not any(spec["address"] - CODE_BASE <= offset < spec["address"] - CODE_BASE + spec["slot"]
                       for spec in TARGETS.values())
        ),
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": len(cases), "mismatch_count": len(mismatches),
                      "functions": metadata, "mutation_controls": controls,
                      "caller_compositions": caller_compositions,
                      "ips_replay": report["ips_replay"], "changed_slots_only": report["changed_slots_only"]}, indent=2))
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
