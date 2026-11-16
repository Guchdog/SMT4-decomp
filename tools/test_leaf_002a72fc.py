#!/usr/bin/env python3
"""Differential test for script_vm_func_002a72fc (0x002a72fc).

Compiles src/engine/leaf_batch45_a.cpp, extracts the script_vm_func_002a72fc
body, resolves every direct call to a deterministic stub, and runs the pinned
original (extracted/exefs/code.bin) and the candidate in separate Unicorn ARM
machines with identical fixtures.

Compared outputs:
  * return value, continuation PC, final SP, callee-saved r4-r11
  * ordered call log (helper name and the helper's declared argument count)
  * the full 0x2000-byte context snapshot

Coverage: all-zero context, each of the four 0x28C slots individually and all
together, 0xFAC, 0xFB8, each of the twelve 0xD10/0xD28 slots individually and
all together, each of the nine individual cleanup slots, and one combined
fixture with every field populated. Two negative controls (wrong cleanup helper
and skipped pointer clear) must be detected by the same comparator.

The helpers are stubs. Nothing here claims their real destructor semantics.
"""

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
FUNC_ADDR = 0x002A72FC
FUNC_SIZE = 580

# Candidate code is placed away from the stubs: its body is larger than 580
# bytes and would otherwise overlap the 0x002A755C stub.
CAND_ADDR = 0x00300000
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000
CAND_SIZE = 0x00010000
CTX_ADDR = 0x00500000
CTX_SIZE = 0x00004000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_UI_2A7BD4 = 0x002A7BD4
STUB_2A7B50 = 0x002A7B50
STUB_2AEB2C = 0x002AEB2C
STUB_2AEA7C = 0x002AEA7C
STUB_2A4974 = 0x002A4974
STUB_14C968 = 0x0014C968
STUB_14C970 = 0x0014C970
STUB_2A4EF0 = 0x002A4EF0
STUB_2B2520 = 0x002B2520
STUB_152AF8 = 0x00152AF8
STUB_2A7AA0 = 0x002A7AA0
STUB_2A7604 = 0x002A7604
STUB_2A7540 = 0x002A7540
STUB_2A755C = 0x002A755C
STUB_2C4360 = 0x002C4360
STUB_2C0128 = 0x002C0128

# (name, number of meaningful arguments). The final call takes none.
STUB_NAMES = {
    STUB_UI_2A7BD4: ("ui_func_002a7bd4", 1),
    STUB_2A7B50: ("script_vm_func_002a7b50", 1),
    STUB_2AEB2C: ("script_vm_func_002aeb2c", 2),
    STUB_2AEA7C: ("engine_func_002aea7c", 1),
    STUB_2A4974: ("func_002a4974", 1),
    STUB_14C968: ("func_0014c968", 1),
    STUB_14C970: ("func_0014c970", 1),
    STUB_2A4EF0: ("engine_func_002a4ef0", 1),
    STUB_2B2520: ("engine_func_002b2520", 1),
    STUB_152AF8: ("script_vm_func_00152af8", 1),
    STUB_2A7AA0: ("script_vm_func_002a7aa0", 1),
    STUB_2A7604: ("script_vm_func_002a7604", 1),
    STUB_2A7540: ("ui_func_002a7540", 1),
    STUB_2A755C: ("script_vm_func_002a755c", 1),
    STUB_2C4360: ("engine_func_002c4360", 1),
    STUB_2C0128: ("script_vm_func_002c0128", 0),
}

CALLEE_SAVED_START = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}
CALLEE_SAVED_REGS = {
    "r4": arm.UC_ARM_REG_R4,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r9": arm.UC_ARM_REG_R9,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
}

OBJECT_LOOP_OFFSETS = [0x28C + 4 * i for i in range(4)]
SUB_OBJECT_OFFSETS = (
    [0xD10 + 4 * i for i in range(6)] + [0xD28 + 4 * i for i in range(6)]
)
INDIVIDUAL_OFFSETS = [0x5A8, 0x5A0, 0x5A4, 0x5B4, 0x5AC,
                      0x5B0, 0x5C0, 0x5B8, 0x5BC]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def compile_candidate() -> bytes:
    out_dir = ROOT / "build/test_leaf_002a72fc"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch45_a.o"
    src_file = ROOT / "src/engine/leaf_batch45_a.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")

    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002a72fc" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"script_vm_func_002a72fc not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} for {rel.symbol_name}"
            )
        target = None
        for address in STUB_NAMES:
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = CAND_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    return bytes(code)


def pointer_value(offset: int) -> int:
    # Deliberately unmapped: stubs only log the argument, never dereference it.
    return 0x60000000 + offset


def build_ctx(case: dict) -> bytes:
    ctx = bytearray(CTX_SIZE)
    for offset, value in case["slots"].items():
        struct.pack_into("<I", ctx, offset, value)
    return bytes(ctx)


class Runner:
    """One Unicorn machine with deterministic bx-lr stubs."""

    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(CAND_ADDR, CAND_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address)

        self.call_log = []

    def _on_stub(self, uc, address, size, user_data):
        name, arity = STUB_NAMES[address]
        args = tuple(
            uc.reg_read(register)
            for register in (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1,
                             arm.UC_ARM_REG_R2, arm.UC_ARM_REG_R3)[:arity]
        )
        self.call_log.append((name, args))

    def run(self, code: bytes, base: int, case: dict):
        self.call_log = []
        self.uc.mem_write(base, code)
        self.uc.mem_write(CTX_ADDR, build_ctx(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED_REGS[name], value)

        try:
            self.uc.emu_start(base, TRAP_ADDR, timeout=5000000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED_REGS.items()
            },
            "call_log": list(self.call_log),
            "ctx": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
        }


def compare(orig: dict, cand: dict):
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "call_log", "ctx"):
        if orig[key] != cand[key]:
            problems.append(
                f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}"
            )
    return problems


def make_cases():
    cases = []

    cases.append({"name": "all-zero context", "slots": {}})

    for offset in OBJECT_LOOP_OFFSETS:
        cases.append(
            {
                "name": f"0x28C slot +0x{offset - 0x28C:02X}",
                "slots": {offset: pointer_value(offset)},
            }
        )
    cases.append(
        {
            "name": "all four 0x28C slots",
            "slots": {offset: pointer_value(offset) for offset in OBJECT_LOOP_OFFSETS},
        }
    )

    cases.append({"name": "0xFAC populated", "slots": {0xFAC: pointer_value(0xFAC)}})
    cases.append({"name": "0xFB8 populated", "slots": {0xFB8: pointer_value(0xFB8)}})

    for offset in SUB_OBJECT_OFFSETS:
        cases.append(
            {
                "name": f"0x{offset:03X} slot populated",
                "slots": {offset: pointer_value(offset)},
            }
        )
    cases.append(
        {
            "name": "all twelve 0xD10/0xD28 slots",
            "slots": {offset: pointer_value(offset) for offset in SUB_OBJECT_OFFSETS},
        }
    )

    for offset in INDIVIDUAL_OFFSETS:
        cases.append(
            {
                "name": f"0x{offset:03X} cleanup slot",
                "slots": {offset: pointer_value(offset)},
            }
        )

    combined = {}
    for offset in OBJECT_LOOP_OFFSETS + SUB_OBJECT_OFFSETS + INDIVIDUAL_OFFSETS:
        combined[offset] = pointer_value(offset)
    combined[0xFAC] = pointer_value(0xFAC)
    combined[0xFB8] = pointer_value(0xFB8)
    cases.append({"name": "combined: every field populated", "slots": combined})

    return cases


def find_bl_targets(code: bytes):
    """Yield (offset, target) for every ARM BL in candidate code."""
    for offset in range(0, len(code) - 3, 4):
        inst = struct.unpack_from("<I", code, offset)[0]
        if (inst & 0x0F000000) != 0x0B000000:
            continue
        displacement = inst & 0x00FFFFFF
        if displacement & 0x00800000:
            displacement -= 0x01000000
        yield offset, CAND_ADDR + offset + 8 + displacement * 4


def retarget_first_call(code: bytes, source: int, target: int) -> bytes:
    mutated = bytearray(code)
    for offset, current in find_bl_targets(mutated):
        if current != source:
            continue
        new_displacement = ((target - (CAND_ADDR + offset + 8)) >> 2) & 0x00FFFFFF
        inst = struct.unpack_from("<I", mutated, offset)[0]
        struct.pack_into("<I", mutated, offset,
                         (inst & 0xFF000000) | new_displacement)
        return bytes(mutated)
    raise RuntimeError(f"negative control: no call to 0x{source:08x} found")


def skip_clear_after_first_call(code: bytes, call_target: int, slot: int) -> bytes:
    """NOP the first word store to `slot` following the first call to `call_target`."""
    mutated = bytearray(code)
    call_offset = None
    for offset, current in find_bl_targets(mutated):
        if current == call_target:
            call_offset = offset
            break
    if call_offset is None:
        raise RuntimeError(f"negative control: no call to 0x{call_target:08x} found")

    for offset in range(call_offset + 4, min(call_offset + 32, len(mutated)), 4):
        inst = struct.unpack_from("<I", mutated, offset)[0]
        is_word_store = (inst & 0x0F500000) == 0x05000000
        if is_word_store and (inst & 0x00000FFF) == slot:
            # MOV r0, r0 with the same condition: a true no-op.
            struct.pack_into("<I", mutated, offset,
                             (inst & 0xF0000000) | 0x01A00000)
            return bytes(mutated)
    raise RuntimeError(
        f"negative control: no store to 0x{slot:03x} after 0x{call_target:08x}"
    )


def main():
    print("Testing script_vm_func_002a72fc (0x002a72fc)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B (relocations resolved).")

    cases = make_cases()

    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, FUNC_ADDR, case)
        cand = Runner().run(cand_code, CAND_ADDR, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")

    # Negative controls: the same comparator must reject both mutants.
    print("\nNegative controls:")
    combined = cases[-1]

    bad_helper = retarget_first_call(cand_code, STUB_2A755C, STUB_2C4360)
    orig = Runner().run(orig_code, FUNC_ADDR, combined)
    mutant = Runner().run(bad_helper, CAND_ADDR, combined)
    assert compare(orig, mutant), "negative control failed: wrong cleanup helper not detected"
    print("  [PASS] wrong cleanup helper (0x2A755C -> 0x2C4360) is detected")

    skipped_clear = skip_clear_after_first_call(cand_code, STUB_2A755C, 0x5A8)
    mutant = Runner().run(skipped_clear, CAND_ADDR, combined)
    assert compare(orig, mutant), "negative control failed: skipped pointer clear not detected"
    print("  [PASS] skipped 0x5A8 pointer clear is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
