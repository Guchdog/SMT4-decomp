#!/usr/bin/env python3
"""Differential test for engine_func_0034ebc8 (0x0034ebc8) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the engine_func_0034ebc8 body,
resolves its direct-call relocations to deterministic stubs at the pinned
addresses, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

The original is the S4 audio-device teardown at 0x0044D0F8:

  * [device+0x04] == 0 returns 0 immediately;
  * a locked pass releases slot+0x00 of every slot through 0x0015A3F4(x, 1);
  * one 0x002C42FC wait on the 0x0044D128 thread handle, a flag-guarded
    0x002C41E8 wait, and `svc #0x23` when the handle is non-zero;
  * a heap release pair (0x002C4160 twice, then 0x002B2520) and a 0x002C4360
    heap-buffer free;
  * a second locked slot pass releasing slot+0x00 through 0x002BD620 and
    slot+0x04 through the device's vtable slot +0x04;
  * lock+0x08 = -1, a vtable release of the whole slot array, then the chained
    shutdown stages 0x0010FE58 -> 0x0010FB6C -> 0x0010FB9C.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every declared register argument and the two
    architected stack words of 0x002C42FC (including the handle array it
    points at);
  * the complete 0x1000-byte device page (device block + thread block), the
    complete 0x1000-byte lock page, the complete 0x10000-byte slot page, and
    the device-object/vtable pages;
  * any emulated write outside those fixtures and the private stack.

Coverage: device gate null/non-null; slot count 0/1/2/3 and a buffer pointer
that is null when the count is zero; every first/second slot null/non-null
combination; null and non-null heap, heap buffer and thread handle; wait result
0, positive and negative; thread state byte overwritten; and the shutdown-stage
r0 chain.  The (s32)index >= 0 guard at the latch is evaluated on every
iteration but its skip path needs 2^31 iterations for a count with bit 31 set,
so that exact path is recorded as an untested runtime limit rather than
emulated.
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
OUT_DIR = ROOT / "build/test_leaf_0034ebc8"

FUNC_ADDR = 0x0034EBC8
FUNC_SIZE = 468

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and every stub up to 0x3FFFFF
DEV_PAGE_ADDR = 0x0044D000
DEV_PAGE_SIZE = 0x00001000
LOCK_PAGE_ADDR = 0x004C4000
LOCK_PAGE_SIZE = 0x00001000
SLOT_ADDR = 0x00500000
SLOT_SIZE = 0x00010000
OBJECT_ADDR = 0x00510000
OBJECT_SIZE = 0x00001000
VTABLE_ADDR = 0x00520000
VTABLE_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

DEVICE_BLOCK = 0x0044D0F8  # S4AudioDevice
THREAD_BLOCK = 0x0044D128  # handle + state byte
LOCK_BLOCK = 0x004C40F8    # AsdMemLock

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

SLOT_STRIDE = 0x70

# Direct-call targets; stubs are placed at the original addresses so both the
# original bytes and the relocated candidate resolve to them.
STUB_15A3F4 = 0x0015A3F4
STUB_2BD620 = 0x002BD620
STUB_2B2520 = 0x002B2520
STUB_2C3AA8 = 0x002C3AA8
STUB_2C3A24 = 0x002C3A24
STUB_2C4160 = 0x002C4160
STUB_2C41E8 = 0x002C41E8
STUB_2C42FC = 0x002C42FC
STUB_2C4360 = 0x002C4360
STUB_2C5468 = 0x002C5468
STUB_10FE58 = 0x0010FE58
STUB_10FB6C = 0x0010FB6C
STUB_10FB9C = 0x0010FB9C

STUB_VTABLE1 = 0x002F0000  # device vtable slot +0x04 (the one used)
STUB_VTABLE0 = 0x002F0040  # device vtable slot +0x00 (decoy)

STUB_NAMES = {
    STUB_15A3F4: "func_0015a3f4",
    STUB_2BD620: "func_002bd620",
    STUB_2B2520: "engine_func_002b2520",
    STUB_2C3AA8: "engine_func_002c3aa8",
    STUB_2C3A24: "engine_func_002c3a24",
    STUB_2C4160: "script_vm_func_002c4160",
    STUB_2C41E8: "engine_func_002c41e8",
    STUB_2C42FC: "engine_func_002c42fc",
    STUB_2C4360: "engine_func_002c4360",
    STUB_2C5468: "engine_func_002c5468",
    STUB_10FE58: "func_0010fe58",
    STUB_10FB6C: "func_0010fb6c",
    STUB_10FB9C: "func_0010fb9c",
    STUB_VTABLE0: "device_vtable[0]",
    STUB_VTABLE1: "device_vtable[1]",
}

# Architected stack words each helper receives.
STACK_ARGS = {address: 0 for address in STUB_NAMES}
STACK_ARGS[STUB_2C42FC] = 2  # timeout_lo, timeout_hi

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

# Shutdown-stage stub returns; each stage must receive the previous stage's r0.
STAGE_A_RET = 0xA1A10001
STAGE_B_RET = 0xB2B20002
STAGE_C_RET = 0xC3C30003
VTABLE_RET_BASE = 0x0A0A0000

U32 = struct.Struct("<I")


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0034ebc8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0034ebc8 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address in STUB_NAMES:
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
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


# --------------------------------------------------------------------- fixtures
def filler(size: int, seed: int = 0) -> bytearray:
    return bytearray(((i * 13 + seed * 31 + 5) & 0xFF) for i in range(size))


def build_device_page(case: dict) -> bytes:
    page = filler(DEV_PAGE_SIZE, 1)
    base = DEVICE_BLOCK - DEV_PAGE_ADDR
    thread = THREAD_BLOCK - DEV_PAGE_ADDR

    page[base + 0x00] = case.get("gate", 0xA5) & 0xFF        # cleared to 0
    page[base + 0x01] = 0xC3                                # must survive
    page[base + 0x02] = 0x5A                                # must survive
    page[base + 0x03] = 0x77                                # must survive
    struct.pack_into("<I", page, base + 0x04, case.get("device", OBJECT_ADDR))
    struct.pack_into("<I", page, base + 0x08, case.get("slots", SLOT_ADDR))
    struct.pack_into("<I", page, base + 0x0C, case.get("heap_buffer", 0))
    struct.pack_into("<I", page, base + 0x10, case.get("heap", 0))
    struct.pack_into("<I", page, base + 0x14, case.get("count", 0))

    struct.pack_into("<I", page, thread + 0x00, case.get("thread_handle", 0))
    page[thread + 0x04] = case.get("thread_state", 0x11) & 0xFF  # set to 1
    page[thread + 0x05] = 0x6B                                   # must survive
    page[thread + 0x06] = 0x6C                                   # must survive
    page[thread + 0x07] = 0x6D                                   # must survive
    return bytes(page)


def build_lock_page(case: dict) -> bytes:
    page = filler(LOCK_PAGE_SIZE, 2)
    base = LOCK_BLOCK - LOCK_PAGE_ADDR
    struct.pack_into("<I", page, base + 0x00, 0x11111111)
    struct.pack_into("<I", page, base + 0x04, 0x22222222)
    struct.pack_into("<I", page, base + 0x08, case.get("lock_marker", 0x33333333))
    return bytes(page)


def build_slot_page(case: dict) -> bytes:
    page = filler(SLOT_SIZE, 3)
    first = case.get("first", [])
    second = case.get("second", [])
    for index in range(max(len(first), len(second))):
        base = index * SLOT_STRIDE
        if index < len(first):
            struct.pack_into("<I", page, base + 0x00, first[index])
        if index < len(second):
            struct.pack_into("<I", page, base + 0x04, second[index])
    return bytes(page)


def build_object_page() -> bytes:
    page = filler(OBJECT_SIZE, 4)
    struct.pack_into("<I", page, 0x00, VTABLE_ADDR)
    return bytes(page)


def build_vtable_page() -> bytes:
    page = filler(VTABLE_SIZE, 5)
    struct.pack_into("<I", page, 0x00, STUB_VTABLE0)
    struct.pack_into("<I", page, 0x04, STUB_VTABLE1)
    return bytes(page)


class EBC8Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DEV_PAGE_ADDR, DEV_PAGE_SIZE)
        self.uc.mem_map(LOCK_PAGE_ADDR, LOCK_PAGE_SIZE)
        self.uc.mem_map(SLOT_ADDR, SLOT_SIZE)
        self.uc.mem_map(OBJECT_ADDR, OBJECT_SIZE)
        self.uc.mem_map(VTABLE_ADDR, VTABLE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_INTR, self._on_intr)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.vtable_calls = 0
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    @staticmethod
    def _normalise(value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, *args) -> None:
        normalised = tuple(
            self._normalise(arg) if isinstance(arg, int) else arg for arg in args
        )
        self.call_log.append(
            (STUB_NAMES[address], normalised + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_intr(self, uc, intno, user_data) -> None:
        # Unicorn reports ARM SVC as interrupt number 2.  The original only
        # executes `svc #0x23` (svcCloseHandle); log the handle and continue.
        if intno == 2:
            self.call_log.append(
                ("svc #0x23", (uc.reg_read(arm.UC_ARM_REG_R0),))
            )

    def _read_words(self, address: int, count: int) -> tuple:
        if address == 0:
            return ()
        count = min(count, 8)
        if count == 0:
            return ()
        try:
            raw = self.uc.mem_read(address, 4 * count)
        except Exception:
            return ("<unmapped>",)
        return struct.unpack(f"<{count}I", raw)

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2C42FC:
            handles = self._read_words(r1, r2)
            self.call_log.append(
                (
                    STUB_NAMES[address],
                    (self._normalise(r0), handles, r2, r3)
                    + self._stack_words(2),
                )
            )
            uc.mem_write(r0, U32.pack(self.case.get("wait_out", 0xDEADBEEF) & 0xFFFFFFFF))
            result = self.case.get("wait_result", 0) & 0xFFFFFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_2C5468:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_15A3F4:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address in (STUB_2BD620, STUB_2C4160, STUB_2B2520, STUB_2C4360,
                         STUB_2C3AA8, STUB_2C3A24, STUB_2C41E8):
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address in (STUB_10FE58, STUB_10FB6C, STUB_10FB9C):
            self._log(address, r0)
            if address == STUB_10FE58:
                uc.reg_write(arm.UC_ARM_REG_R0, STAGE_A_RET)
            elif address == STUB_10FB6C:
                uc.reg_write(arm.UC_ARM_REG_R0, STAGE_B_RET)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, STAGE_C_RET)
        elif address in (STUB_VTABLE0, STUB_VTABLE1):
            self.vtable_calls += 1
            self._log(address, r0, r1)
            uc.reg_write(
                arm.UC_ARM_REG_R0, (VTABLE_RET_BASE + self.vtable_calls) & 0xFFFFFFFF
            )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.vtable_calls = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DEV_PAGE_ADDR, build_device_page(case))
        self.uc.mem_write(LOCK_PAGE_ADDR, build_lock_page(case))
        self.uc.mem_write(SLOT_ADDR, build_slot_page(case))
        self.uc.mem_write(OBJECT_ADDR, build_object_page())
        self.uc.mem_write(VTABLE_ADDR, build_vtable_page())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0xDEAD0000)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0xDEAD0001)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0xDEAD0002)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0xDEAD0003)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            in_fixture = (
                DEV_PAGE_ADDR <= address < DEV_PAGE_ADDR + DEV_PAGE_SIZE
                or LOCK_PAGE_ADDR <= address < LOCK_PAGE_ADDR + LOCK_PAGE_SIZE
                or SLOT_ADDR <= address < SLOT_ADDR + SLOT_SIZE
            )
            if not in_fixture:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "device_page": bytes(self.uc.mem_read(DEV_PAGE_ADDR, DEV_PAGE_SIZE)),
            "lock_page": bytes(self.uc.mem_read(LOCK_PAGE_ADDR, LOCK_PAGE_SIZE)),
            "slot_page": bytes(self.uc.mem_read(SLOT_ADDR, SLOT_SIZE)),
            "object_page": bytes(self.uc.mem_read(OBJECT_ADDR, OBJECT_SIZE)),
            "vtable_page": bytes(self.uc.mem_read(VTABLE_ADDR, VTABLE_SIZE)),
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
    for key in ("device_page", "lock_page", "slot_page", "object_page",
                "vtable_page"):
        if orig[key] != cand[key]:
            problems.append(f"{key} differs")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "device": OBJECT_ADDR,
        "slots": SLOT_ADDR,
        "heap_buffer": 0x00300000,
        "heap": 0x00310000,
        "count": 0,
        "gate": 0xA5,
        "thread_handle": 0x00001234,
        "thread_state": 0x11,
        "wait_result": 0,
        "first": [],
        "second": [],
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- lifetime gate: null returns before touching anything.
    cases.append(base_case("device gate null", device=0))
    cases.append(base_case("device gate null, everything else set",
                           device=0, count=3, first=[1, 2, 3],
                           second=[4, 5, 6]))

    # --- empty device: no slots, null heap/handle.
    cases.append(base_case("empty device, all pointers null",
                           count=0, slots=0, heap=0, heap_buffer=0,
                           thread_handle=0))
    cases.append(base_case("empty device, heap release pair non-null",
                           count=0, heap=0x00310000, heap_buffer=0x00300000,
                           thread_handle=0x12345678))

    # --- one slot, every first/second null combination.
    cases.append(base_case("count 1, first only", count=1,
                           first=[0x11110000], second=[0]))
    cases.append(base_case("count 1, second only", count=1,
                           first=[0], second=[0x22220000]))
    cases.append(base_case("count 1, both fields", count=1,
                           first=[0x11110000], second=[0x22220000]))
    cases.append(base_case("count 1, both null", count=1,
                           first=[0], second=[0]))

    # --- ordered slot passes.
    cases.append(base_case("count 3 mixed fields", count=3,
                           first=[0x11110000, 0, 0x33330000],
                           second=[0, 0x22220000, 0x44440000]))
    cases.append(base_case("count 2 reversed mix", count=2,
                           first=[0, 0x11110000],
                           second=[0x22220000, 0]))
    cases.append(base_case("count 3 all zero", count=3,
                           first=[0, 0, 0], second=[0, 0, 0]))

    # --- thread/sync: handle present or absent, state byte overwritten.
    for handle in (0, 1, 0xFFFFFFFF):
        cases.append(base_case(f"thread handle 0x{handle:08x}", count=0,
                               thread_handle=handle))
    for state in (0x00, 0x01, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"thread state 0x{state:02x}", count=0,
                               thread_state=state))

    # --- wait result: zero, positive, negative (abort path).
    for result in (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"wait result 0x{result:08x}", count=0,
                               wait_result=result))

    # --- heap combinations.
    cases.append(base_case("heap null, buffer non-null", count=0,
                           heap=0, heap_buffer=0x00300000))
    cases.append(base_case("heap non-null, buffer null", count=0,
                           heap=0x00310000, heap_buffer=0))
    cases.append(base_case("heap and buffer null", count=0,
                           heap=0, heap_buffer=0))

    # --- gate byte and neighbouring bytes.
    for gate in (0x00, 0x01, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"gate byte 0x{gate:02x}", count=0, gate=gate))

    # --- slot buffer pointer is only dereferenced when the count is non-zero.
    cases.append(base_case("count 0 with null slot buffer", count=0, slots=0))
    cases.append(base_case("count 1 with four prepared slots", count=1,
                           first=[0x11110000, 0x22220000, 0x33330000, 0x44440000],
                           second=[0x55550000, 0, 0, 0]))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = EBC8Runner().run(orig_code, case)
        cand = EBC8Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing engine_func_0034ebc8 (0x0034ebc8)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("slot_release_mode",
         "constexpr u32 kSlotReleaseMode = 1;",
         "constexpr u32 kSlotReleaseMode = 2;"),
        ("wait_count",
         "constexpr u32 kWaitCount = 1;                // r2 of 0x002C42FC",
         "constexpr u32 kWaitCount = 2;                // r2 of 0x002C42FC"),
        ("abort_condition",
         "    if (status < 0) {\n        S4AudioTd_AbortOnFailure(status);",
         "    if (status <= 0) {\n        S4AudioTd_AbortOnFailure(status);"),
        ("lock_marker_offset", "constexpr u32 kLockCountOffset = 0x08;",
         "constexpr u32 kLockCountOffset = 0x0C;"),
        ("second_field_argument",
         "notify(current_device, slot->second);",
         "notify(current_device, slot->first);"),
        ("thread_state_value", "thread->state = 1;", "thread->state = 2;"),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = EBC8Runner().run(orig_code, case)
            bad = EBC8Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
