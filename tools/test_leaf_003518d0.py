#!/usr/bin/env python3
"""Differential test for engine_func_003518d0 (0x003518d0) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the engine_func_003518d0 body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log: every helper with all register arguments and its
    architected stack arguments, the `svc #0x23` close with r0, and every
    indirect vtable callback with its arguments;
  * the full object page, the 0x0044D158 global pair page, the owner, slot,
    SDK and vtable fixture pages (must be byte-identical);
  * every emulated write, which must stay inside a fixture page or the private
    stack.

Coverage: the [this+0x14] lifetime gate on and off; positive/zero/negative
0x2C42FC results; null, non-zero and 0xFFFFFFFF handles including callee-side
handle replacement; all four 0x0044D158 null/non-null combinations plus a
callee that rewrites the global; signed count boundaries and every loop bound
for the three cleanup passes; null and non-null elements/records; and callbacks
that grow, shrink or re-point the next iteration's count, owner and vtable.

Negative controls mutate an element base offset, the record stride, the second
vtable slot index, the Result sign test and the lock handle offset; each mutant
must be detected.
"""

from __future__ import annotations

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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_003518d0"

FUNC_ADDR = 0x003518D0
FUNC_SIZE = 440
FUNC_LITERAL_ADDR = 0x00351A84
FUNC_LITERAL = 0x0044D158

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000

GLOBAL_ADDR = 0x0044D000  # page containing the 0x0044D158 pair
GLOBAL_SIZE = 0x00001000
GLOBAL_SLOT = 0x0044D158

OBJECT_ADDR = 0x00700000
OBJECT_SIZE = 0x00020000  # the object plus its three dynamic arrays
OWNER_ADDR = 0x00720000
OWNER_SIZE = 0x00001000
OWNER2_ADDR = 0x00721000
OWNER2_SIZE = 0x00001000
SLOT_ADDR = 0x00730000
SLOT_SIZE = 0x00001000
SLOT2_ADDR = 0x00731000
SLOT2_SIZE = 0x00001000
SDK1_ADDR = 0x00740000
SDK1_SIZE = 0x00001000
SDK2_ADDR = 0x00741000
SDK2_SIZE = 0x00001000
VT_ADDR = 0x00760000
VT_SIZE = 0x00001000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Direct-call targets; stubs are placed at the original addresses so both the
# original bytes and the relocated candidate resolve to them.
STUB_2C4244 = 0x002C4244  # lock_prepare
STUB_2C42FC = 0x002C42FC  # memory_control (7 arguments, writes *out)
STUB_2C5468 = 0x002C5468  # report_failure
STUB_2C41E8 = 0x002C41E8  # lock_finish
STUB_2C4160 = 0x002C4160  # release_sdk_object
STUB_2B2520 = 0x002B2520  # destroy_sdk_object
STUB_2C4360 = 0x002C4360  # free_sdk_object
STUB_35074C = 0x0035074C  # reset_container
STUB_34F260 = 0x0034F260  # release_container

# Indirect vtable targets placed in the unused tail of the code page.
OWNER_SLOT1 = 0x003E0000
OWNER2_SLOT1 = 0x003E0010
SLOT_SLOT1 = 0x003E0020
SLOT_SLOT3 = 0x003E0030
SLOT2_SLOT1 = 0x003E0040
SLOT2_SLOT3 = 0x003E0050

STUB_NAMES = {
    STUB_2C4244: "nn_sdk_func_002c4244",
    STUB_2C42FC: "engine_func_002c42fc",
    STUB_2C5468: "engine_func_002c5468",
    STUB_2C41E8: "engine_func_002c41e8",
    STUB_2C4160: "script_vm_func_002c4160",
    STUB_2B2520: "engine_func_002b2520",
    STUB_2C4360: "engine_func_002c4360",
    STUB_35074C: "func_0035074c",
    STUB_34F260: "func_0034f260",
    OWNER_SLOT1: "owner_vtable_slot1",
    OWNER2_SLOT1: "owner2_vtable_slot1",
    SLOT_SLOT1: "slot_vtable_slot1",
    SLOT_SLOT3: "slot_vtable_slot3",
    SLOT2_SLOT1: "slot2_vtable_slot1",
    SLOT2_SLOT3: "slot2_vtable_slot3",
}

# Number of architected stack words each direct helper receives.
STACK_ARGS = {
    STUB_2C4244: 0,
    STUB_2C42FC: 3,  # operation, permission, handle
    STUB_2C5468: 0,
    STUB_2C41E8: 0,
    STUB_2C4160: 0,
    STUB_2B2520: 0,
    STUB_2C4360: 0,
    STUB_35074C: 0,
    STUB_34F260: 0,
}

CALLEE_SAVED = {
    "r4": arm.UC_ARM_REG_R4,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r9": arm.UC_ARM_REG_R9,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
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

# Vtable images (index 1 is used by loops A/C, index 3 by loop B).
VT_OWNER = VT_ADDR + 0x000
VT_OWNER2 = VT_ADDR + 0x100
VT_SLOT = VT_ADDR + 0x200
VT_SLOT2 = VT_ADDR + 0x300

FIXTURE_PAGES = (
    (OBJECT_ADDR, OBJECT_SIZE),
    (GLOBAL_ADDR, GLOBAL_SIZE),
    (OWNER_ADDR, OWNER_SIZE),
    (OWNER2_ADDR, OWNER2_SIZE),
    (SLOT_ADDR, SLOT_SIZE),
    (SLOT2_ADDR, SLOT2_SIZE),
    (SDK1_ADDR, SDK1_SIZE),
    (SDK2_ADDR, SDK2_SIZE),
    (VT_ADDR, VT_SIZE),
)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "003518d0" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_003518d0 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):  # PC24 / CALL / JUMP24
            target = None
            for address in STUB_NAMES:
                if f"{address:08x}" in rel.symbol_name.lower():
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def put_u8(page: bytearray, offset: int, value: int) -> None:
    page[offset] = value & 0xFF


def put_u32(page: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", page, offset, value & 0xFFFFFFFF)


def filler(size: int) -> bytearray:
    return bytearray((index * 37 + 11) & 0xFF for index in range(size))


def build_object(case: dict) -> bytes:
    page = filler(OBJECT_SIZE)
    put_u32(page, 0x08, case.get("state08", 0x12345678))
    put_u8(page, 0x10, case.get("byte10", 0xA7))
    put_u32(page, 0x14, 0 if case.get("gate_off") else case.get("owner", OWNER_ADDR))
    put_u32(page, 0x18, case.get("cleared18", 0x18181818))
    put_u32(page, 0x20, 0x20202020)
    put_u32(page, 0x24, 0x24242424)
    put_u32(page, 0x28, case.get("handle", 0x00000123))
    put_u8(page, 0x2C, case.get("lock_flag", 0x00))
    put_u32(page, 0x158, case.get("container", SDK1_ADDR))
    put_u32(page, 0x1B8, case.get("slot_object", SLOT_ADDR))
    put_u32(page, 0x1BC, 0x1BC1BC1B)
    put_u32(page, 0x1C0, 0x1C01C01C)
    put_u32(page, 0x1C4, case.get("count_c", 1))
    for index, value in enumerate(case.get("records", (0x11110001,))):
        put_u32(page, 0x1D8 + index * 0x18, value)
    put_u32(page, 0x2E8, case.get("count_a", 1))
    for index, value in enumerate(case.get("elements_a", (0xAAAA0001,))):
        put_u32(page, 0x2EC + index * 4, value)
    put_u32(page, 0x484, case.get("count_b", 1))
    for index, value in enumerate(case.get("elements_b", (0xBBBB0001,))):
        put_u32(page, 0x488 + index * 4, value)
    return bytes(page)


def build_global(case: dict) -> bytes:
    page = filler(GLOBAL_SIZE)
    put_u32(page, GLOBAL_SLOT - GLOBAL_ADDR, case.get("global0", SDK1_ADDR))
    put_u32(page, GLOBAL_SLOT - GLOBAL_ADDR + 4, case.get("global1", SDK2_ADDR))
    return bytes(page)


def build_owner(page_addr: int, vtable: int) -> bytes:
    page = filler(OWNER_SIZE)
    put_u32(page, 0, vtable)
    return bytes(page)


def build_vtables() -> bytes:
    page = bytearray(VT_SIZE)
    for base, vtable in (
        (VT_OWNER, VT_OWNER),
        (VT_OWNER2, VT_OWNER2),
        (VT_SLOT, VT_SLOT),
        (VT_SLOT2, VT_SLOT2),
    ):
        put_u32(page, base - VT_ADDR + 0x00, 0xDEAD0000 | (base & 0xFF))
        put_u32(page, base - VT_ADDR + 0x08, 0xDEAD0002)
        put_u32(page, base - VT_ADDR + 0x0C, 0xDEAD0003)
    put_u32(page, VT_OWNER - VT_ADDR + 0x04, OWNER_SLOT1)
    put_u32(page, VT_OWNER2 - VT_ADDR + 0x04, OWNER2_SLOT1)
    put_u32(page, VT_SLOT - VT_ADDR + 0x04, SLOT_SLOT1)
    put_u32(page, VT_SLOT - VT_ADDR + 0x0C, SLOT_SLOT3)
    put_u32(page, VT_SLOT2 - VT_ADDR + 0x04, SLOT2_SLOT1)
    put_u32(page, VT_SLOT2 - VT_ADDR + 0x0C, SLOT2_SLOT3)
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (GLOBAL_ADDR, GLOBAL_SIZE),
            (OBJECT_ADDR, OBJECT_SIZE),
            (OWNER_ADDR, OWNER_SIZE),
            (OWNER2_ADDR, OWNER2_SIZE),
            (SLOT_ADDR, SLOT_SIZE),
            (SLOT2_ADDR, SLOT2_SIZE),
            (SDK1_ADDR, SDK1_SIZE),
            (SDK2_ADDR, SDK2_SIZE),
            (VT_ADDR, VT_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_INTR, self._on_interrupt)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.slot1_calls = 0
        self.slot3_calls = 0
        self.owner1_calls = 0
        self.release_calls = 0

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS.get(address, 0)))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _u32(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _set_u32(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _on_interrupt(self, uc, intno, user_data) -> None:
        if intno != 2:  # SVC in Unicorn's ARM model
            raise RuntimeError(f"unexpected ARM interrupt {intno}")
        pc = uc.reg_read(arm.UC_ARM_REG_PC)
        word = struct.unpack("<I", uc.mem_read(pc, 4))[0]
        if (word & 0xFF000000) == 0xEF000000:  # PC still at the SVC
            immediate = word & 0xFFFFFF
            uc.reg_write(arm.UC_ARM_REG_PC, pc + 4)
        else:  # PC already advanced past the SVC
            previous = struct.unpack("<I", uc.mem_read(pc - 4, 4))[0]
            if (previous & 0xFF000000) != 0xEF000000:
                raise RuntimeError(f"interrupt {intno} at 0x{pc:08x} is not an SVC")
            immediate = previous & 0xFFFFFF
        self.call_log.append(
            ("svc", (immediate, uc.reg_read(arm.UC_ARM_REG_R0)))
        )

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        case = self.case

        if address == STUB_2C4244:
            self._log(address, r0)
            uc.mem_write(r0, struct.pack("<II", 0x4C4F434B, 0x52544E45))
            if case.get("mutate_handle_in_prepare") is not None:
                self._set_u32(OBJECT_ADDR + 0x28, case["mutate_handle_in_prepare"])
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2C424400)
        elif address == STUB_2C42FC:
            stack2 = self._stack_words(3)[2]
            self._log(address, r0, r1, r2, r3)
            if case.get("mutate_handle_in_control") is not None:
                self._set_u32(OBJECT_ADDR + 0x28, case["mutate_handle_in_control"])
            self._set_u32(r0, 0x5A000000 | (stack2 & 0xFF))
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("control_result", 0) & 0xFFFFFFFF
            )
        elif address == STUB_2C5468:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2C546800)
        elif address == STUB_2C41E8:
            flag = uc.mem_read(r0 + 4, 1)[0]
            self.call_log.append(
                (STUB_NAMES[address], (r0, flag, "ran" if flag == 0 else "skipped"))
            )
            if flag == 0:
                uc.mem_write(r0 + 4, b"\x01")
            if case.get("mutate_handle_in_finish") is not None:
                self._set_u32(OBJECT_ADDR + 0x28, case["mutate_handle_in_finish"])
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2C41E800)
        elif address == STUB_2C4160:
            self._log(address, r0)
            self.release_calls += 1
            if self.release_calls == 1 and case.get("mutate_global_on_release") is not None:
                self._set_u32(GLOBAL_SLOT + 4, case["mutate_global_on_release"])
            uc.reg_write(arm.UC_ARM_REG_R0, 0x7E1E0000 | (r0 & 0xFFFF))
        elif address == STUB_2B2520:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2B252000)
        elif address == STUB_2C4360:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2C436000)
        elif address == STUB_35074C:
            self.call_log.append(
                (
                    STUB_NAMES[address],
                    (
                        r0,
                        self._u32(OBJECT_ADDR + 0x08),
                        self._u32(OBJECT_ADDR + 0x14),
                        self._u32(OBJECT_ADDR + 0x158),
                    ),
                )
            )
            if case.get("mutate_container") is not None:
                self._set_u32(OBJECT_ADDR + 0x158, case["mutate_container"])
            uc.reg_write(arm.UC_ARM_REG_R0, 0x35074C00)
        elif address == STUB_34F260:
            self.call_log.append(
                (STUB_NAMES[address], (r0, self._u32(r0)))
            )
            self._set_u32(r0, 0)
            # The pinned 0x0034F260 ends with `mov r0,#0; str r0,[r4]`, so the
            # original leaves r0 = 0 for the caller; model that exactly.
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address in (SLOT_SLOT1, SLOT2_SLOT1):
            self._log(address, r0, r1, r2)
            self.slot1_calls += 1
            if self.slot1_calls == 1:
                if case.get("switch_slot") is not None:
                    self._set_u32(OBJECT_ADDR + 0x1B8, case["switch_slot"])
                if case.get("mutate_owner_a") is not None:
                    self._set_u32(OBJECT_ADDR + 0x14, case["mutate_owner_a"])
                if case.get("grow_a"):
                    self._set_u32(
                        OBJECT_ADDR + 0x2E8,
                        self._u32(OBJECT_ADDR + 0x2E8) + 1,
                    )
                if case.get("shrink_a") is not None:
                    self._set_u32(OBJECT_ADDR + 0x2E8, case["shrink_a"])
            uc.reg_write(arm.UC_ARM_REG_R0, 0x3E002000)
        elif address in (SLOT_SLOT3, SLOT2_SLOT3):
            self._log(address, r0, r1, r2)
            self.slot3_calls += 1
            if self.slot3_calls == 1:
                if case.get("switch_slot_b") is not None:
                    self._set_u32(OBJECT_ADDR + 0x1B8, case["switch_slot_b"])
                if case.get("mutate_owner_b") is not None:
                    self._set_u32(OBJECT_ADDR + 0x14, case["mutate_owner_b"])
                if case.get("grow_b"):
                    self._set_u32(
                        OBJECT_ADDR + 0x484,
                        self._u32(OBJECT_ADDR + 0x484) + 1,
                    )
                if case.get("shrink_b") is not None:
                    self._set_u32(OBJECT_ADDR + 0x484, case["shrink_b"])
            uc.reg_write(arm.UC_ARM_REG_R0, 0x3E003000)
        elif address in (OWNER_SLOT1, OWNER2_SLOT1):
            self._log(address, r0, r1, r2)
            self.owner1_calls += 1
            if self.owner1_calls == 1:
                if case.get("grow_c"):
                    self._set_u32(
                        OBJECT_ADDR + 0x1C4,
                        self._u32(OBJECT_ADDR + 0x1C4) + 1,
                    )
                if case.get("shrink_c") is not None:
                    self._set_u32(OBJECT_ADDR + 0x1C4, case["shrink_c"])
            uc.reg_write(arm.UC_ARM_REG_R0, 0x3E000000)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            out = []
            for arg in args:
                if isinstance(arg, int) and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def _in_fixture(self, address: int, size: int) -> bool:
        for base, length in FIXTURE_PAGES:
            if base <= address and address + size <= base + length:
                return True
        return STACK_ADDR <= address < STACK_ADDR + STACK_SIZE

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.slot1_calls = 0
        self.slot3_calls = 0
        self.owner1_calls = 0
        self.release_calls = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(OBJECT_ADDR, build_object(case))
        self.uc.mem_write(GLOBAL_ADDR, build_global(case))
        self.uc.mem_write(OWNER_ADDR, build_owner(OWNER_ADDR, VT_OWNER))
        self.uc.mem_write(OWNER2_ADDR, build_owner(OWNER2_ADDR, VT_OWNER2))
        self.uc.mem_write(SLOT_ADDR, build_owner(SLOT_ADDR, VT_SLOT))
        self.uc.mem_write(SLOT2_ADDR, build_owner(SLOT2_ADDR, VT_SLOT2))
        self.uc.mem_write(SDK1_ADDR, bytes(filler(SDK1_SIZE)))
        self.uc.mem_write(SDK2_ADDR, bytes(filler(SDK2_SIZE)))
        self.uc.mem_write(VT_ADDR, build_vtables())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJECT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = [
            (address, size)
            for address, size, _value in self.writes
            if not self._in_fixture(address, size)
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "fixtures": {
                f"{base:08x}": bytes(self.uc.mem_read(base, length))
                for base, length in FIXTURE_PAGES
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            first = next(
                (
                    index
                    for index, (left, right) in enumerate(zip(value, cand["fixtures"][key]))
                    if left != right
                ),
                None,
            )
            problems.append(f"fixture {key} differs (first byte {first})")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "handle": 0x00000123,
        "control_result": 0,
        "count_a": 1,
        "count_b": 1,
        "count_c": 1,
        "elements_a": (0xAAAA0001,),
        "elements_b": (0xBBBB0001,),
        "records": (0x11110001,),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- lifetime gate [this+0x14]
    cases.append(base_case("gate off", gate_off=True))
    cases.append(base_case("gate off with null globals", gate_off=True,
                           global0=0, global1=0, handle=0))
    cases.append(base_case("gate on baseline"))

    # --- 0x2C42FC Result sign test
    for result in (0, 1, -1, -2, 0x7FFFFFFF, 0x80000000):
        cases.append(
            base_case(f"control result 0x{result & 0xFFFFFFFF:08x}",
                      control_result=result)
        )

    # --- kernel handle paths (svc #0x23 only when non-zero after reload)
    for handle in (0, 1, 0xFFFFFFFF, 0x0000ABCD):
        cases.append(base_case(f"handle 0x{handle:08x}", handle=handle))
    cases.append(base_case("handle removed by lock_prepare",
                           mutate_handle_in_prepare=0))
    cases.append(base_case("handle replaced by lock_prepare",
                           mutate_handle_in_prepare=0x00000777))
    cases.append(base_case("handle replaced by control call",
                           mutate_handle_in_control=0x00000888))
    cases.append(base_case("handle zeroed by control call",
                           mutate_handle_in_control=0))
    cases.append(base_case("handle replaced by lock_finish",
                           mutate_handle_in_finish=0x00000999))
    cases.append(base_case("handle zeroed by lock_finish",
                           mutate_handle_in_finish=0))

    # --- 0x0044D158 pair: all null/non-null combinations
    for global0 in (0, SDK1_ADDR):
        for global1 in (0, SDK2_ADDR):
            cases.append(
                base_case(f"global0 0x{global0:08x} global1 0x{global1:08x}",
                          global0=global0, global1=global1)
            )
    cases.append(base_case("global1 replaced by release", global1=SDK2_ADDR,
                           mutate_global_on_release=SDK1_ADDR))
    cases.append(base_case("global1 cleared by release", global1=SDK2_ADDR,
                           mutate_global_on_release=0))

    # --- pass A: signed count and elements
    for count in (-0x80000000, -1, 0, 1, 2, 3, 4):
        cases.append(
            base_case(
                f"count A {count}",
                count_a=count,
                elements_a=(0xAAAA0001, 0xAAAA0002, 0xAAAA0003, 0xAAAA0004),
            )
        )
    cases.append(base_case("count A element zero",
                           elements_a=(0, 0xAAAA0002)))
    cases.append(base_case("count A grow in callback", grow_a=True,
                           elements_a=(0xAAAA0001, 0xAAAA0002, 0xAAAA0003)))
    cases.append(base_case("count A shrink in callback", count_a=3,
                           shrink_a=1,
                           elements_a=(0xAAAA0001, 0xAAAA0002, 0xAAAA0003)))
    cases.append(base_case("count A switch slot object",
                           switch_slot=SLOT2_ADDR,
                           elements_a=(0xAAAA0001, 0xAAAA0002)))
    cases.append(base_case("count A switch owner",
                           mutate_owner_a=OWNER2_ADDR,
                           elements_a=(0xAAAA0001, 0xAAAA0002)))

    # --- pass B: signed count and elements
    for count in (-0x80000000, -1, 0, 1, 2, 3, 4):
        cases.append(
            base_case(
                f"count B {count}",
                count_b=count,
                elements_b=(0xBBBB0001, 0xBBBB0002, 0xBBBB0003, 0xBBBB0004),
            )
        )
    cases.append(base_case("count B element zero",
                           elements_b=(0, 0xBBBB0002)))
    cases.append(base_case("count B grow in callback", grow_b=True,
                           elements_b=(0xBBBB0001, 0xBBBB0002, 0xBBBB0003)))
    cases.append(base_case("count B shrink in callback", count_b=3,
                           shrink_b=1,
                           elements_b=(0xBBBB0001, 0xBBBB0002, 0xBBBB0003)))
    cases.append(base_case("count B switch slot object",
                           switch_slot_b=SLOT2_ADDR,
                           elements_b=(0xBBBB0001, 0xBBBB0002)))
    cases.append(base_case("count B switch owner",
                           mutate_owner_b=OWNER2_ADDR,
                           elements_b=(0xBBBB0001, 0xBBBB0002)))

    # --- pass C: 0x18-byte records
    for count in (-0x80000000, -1, 0, 1, 2, 3, 4):
        cases.append(
            base_case(
                f"count C {count}",
                count_c=count,
                records=(0x11110001, 0x11110002, 0x11110003, 0x11110004),
            )
        )
    cases.append(base_case("record first is null",
                           records=(0, 0x11110002)))
    cases.append(base_case("record middle is null",
                           records=(0x11110001, 0, 0x11110003), count_c=3))
    cases.append(base_case("record grow in callback", grow_c=True, count_c=2,
                           records=(0x11110001, 0x11110002, 0x11110003)))
    cases.append(base_case("record shrink in callback", count_c=3, shrink_c=1,
                           records=(0x11110001, 0x11110002, 0x11110003)))
    cases.append(base_case("record owner switched by pass A",
                           mutate_owner_a=OWNER2_ADDR,
                           records=(0x11110001, 0x11110002), count_c=2))

    # --- container release and retained words
    cases.append(base_case("container null", container=0))
    cases.append(base_case("container replaced by reset",
                           mutate_container=SDK2_ADDR))
    cases.append(base_case("lock flag already set", lock_flag=0xFF))
    cases.append(base_case("shutdown byte already set", byte10=0x00))
    cases.append(base_case("slot object switched before pass C",
                           switch_slot=SLOT2_ADDR,
                           count_a=2, elements_a=(0xAAAA0001, 0xAAAA0002),
                           count_b=2, elements_b=(0xBBBB0001, 0xBBBB0002)))

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} events)")
    return passed


def main() -> None:
    print("Testing engine_func_003518d0 (0x003518d0)...")
    orig_code = get_orig_bytes()
    if len(orig_code) != FUNC_SIZE:
        raise SystemExit(f"original body is {len(orig_code)} bytes")
    literal = struct.unpack_from("<I", orig_code, FUNC_LITERAL_ADDR - FUNC_ADDR)[0]
    if literal != FUNC_LITERAL:
        raise SystemExit(f"literal word is 0x{literal:08x}, expected 0x{FUNC_LITERAL:08x}")

    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("element_base_a", "constexpr u32 kElementBaseAOffset = 0x2EC;",
         "constexpr u32 kElementBaseAOffset = 0x2F0;"),
        ("record_stride", "constexpr u32 kRecordStride = 0x18;",
         "constexpr u32 kRecordStride = 0x10;"),
        ("release_slot_index", "constexpr u32 kReleaseNotifyIndex = 3;",
         "constexpr u32 kReleaseNotifyIndex = 2;"),
        ("result_sign_test", "if (status < 0) {", "if (status <= 0) {"),
        ("lock_handle_offset", "constexpr u32 kLockHandleOffset = 0x28;",
         "constexpr u32 kLockHandleOffset = 0x24;"),
    ):
        try:
            mutant_code = compile_candidate_mutant(name, old, new)
        except Exception as error:  # pragma: no cover - build failure
            print(f"  [FAIL] mutant {name} did not compile: {error}")
            raise SystemExit(1)
        detected = False
        detail = ""
        for case in cases:
            try:
                orig = Runner().run(orig_code, case)
                bad = Runner().run(mutant_code, case)
                problems = compare(orig, bad)
            except Exception as error:
                detected = True
                detail = f"runtime divergence: {error}"
                break
            if problems:
                detected = True
                detail = problems[0]
                break
        if not detected:
            print(f"  [FAIL] mutant {name} was not detected")
            raise SystemExit(1)
        print(f"  [PASS] {name} mutant detected ({detail.splitlines()[0]})")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
