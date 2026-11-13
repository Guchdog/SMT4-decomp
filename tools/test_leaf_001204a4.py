#!/usr/bin/env python3
"""Differential test for engine_func_001204a4 (0x001204A4) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the engine_func_001204a4 body,
resolves its single direct call (AsdMem_Zero) to a deterministic stub, and runs
the pinned original (extracted/exefs/code.bin) against the candidate in separate
Unicorn ARM machines with identical fixtures.  The 3DS ARM11 VFP unit is enabled
through CPACR/FPEXC because the constructor uses vcvt/mul (control input floats
are bit patterns, so the test must match the hardware conversions).

The function constructs two heap objects through an allocator supplied by the
caller: `allocator->vtable[2](allocator, size, flags)` at 0x001204B4,
0x00120530 and 0x001205CC.  The three indirect targets are stubs that log the
context/size/flags and return case-selected pointers (or null).

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered event log: each allocation with its call index, context, size
    and flags, AsdMem_Zero with its pointer and size, and the two vtable slot
    targets so a reloaded vtable is visible (no helper takes stack arguments);
  * the complete descriptor, allocator-context, primary/secondary vtable,
    record, sub-record and payload fixture pages (byte-identical);
  * every emulated write must stay inside a fixture page or the private stack.

Coverage:
  * both allocations null/non-null (the null paths fault like the original);
  * payload flag 0/1 (byte 0x80/0xFF included), zero-fill byte 0/1, payload
    allocation null/non-null and payload size 0/4/8/24;
  * signed size fields 0x80000000, -1, 0, 1, 0x7FFFFFFF, 0x20000000,
    0x1FFFFFFF, 0x40000000 and the exact 2^32 saturation edge;
  * record/sub/payload returned from alternate fixture pages, so both
    self-relative links are checked;
  * the vtable slot is reloaded at every call site: the allocator stub swaps
    the context vtable after call 1 and after call 2;
  * descriptor fields rewritten by the allocator during call 1, call 2 and
    call 3 prove the reload order of the size, size/flag reads.

Negative controls mutate the payload scale, the payload gate, the sub-record
context offset, the null-payload link test and the payload size store; each
mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_001204a4"

FUNC_ADDR = 0x001204A4
FUNC_SIZE = 444
# Literal pool at 0x0012064C..0x0012065F.
FUNC_LITERALS = {
    0x0012064C: 0x20000021,
    0x00120650: 0x48535854,
    0x00120654: 0x00006040,
    0x00120658: 0x00001405,
    0x0012065C: 0x40800000,  # 4.0f
}

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the body, 0x002C4B30 and the 0x002E0000 stubs

DESC_ADDR = 0x00700000
DESC_SIZE = 0x00001000
CONTEXT_ADDR = 0x00710000
CONTEXT_SIZE = 0x00001000
CONTEXT2_ADDR = 0x00711000
CONTEXT2_SIZE = 0x00001000
RECORD_ADDR = 0x00720000
RECORD_SIZE = 0x00001000
RECORD2_ADDR = 0x00721000
RECORD2_SIZE = 0x00001000
SUB_ADDR = 0x00730000
SUB_SIZE = 0x00001000
SUB2_ADDR = 0x00731000
SUB2_SIZE = 0x00001000
PAYLOAD_ADDR = 0x00740000
PAYLOAD_SIZE = 0x00001000
PAYLOAD2_ADDR = 0x00741000
PAYLOAD2_SIZE = 0x00001000
VT_ADDR = 0x00760000
VT_SIZE = 0x00001000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Direct callee: AsdMem_Zero(ptr, size), 0x002C4B30.
STUB_ASDMEM_ZERO = 0x002C4B30
# Indirect allocation targets installed in vtable slot 2 (+0x08).
ALLOC1 = 0x002E0000
ALLOC2 = 0x002E0020

STUB_NAMES = {
    STUB_ASDMEM_ZERO: "AsdMem_Zero",
    ALLOC1: "allocate_primary",
    ALLOC2: "allocate_secondary",
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

FIXTURE_PAGES = (
    (DESC_ADDR, DESC_SIZE),
    (CONTEXT_ADDR, CONTEXT_SIZE),
    (CONTEXT2_ADDR, CONTEXT2_SIZE),
    (RECORD_ADDR, RECORD_SIZE),
    (RECORD2_ADDR, RECORD2_SIZE),
    (SUB_ADDR, SUB_SIZE),
    (SUB2_ADDR, SUB2_SIZE),
    (PAYLOAD_ADDR, PAYLOAD_SIZE),
    (PAYLOAD2_ADDR, PAYLOAD2_SIZE),
    (VT_ADDR, VT_SIZE),
)

# Descriptor offsets read by the body.
DESC_SIZE_X = 0x00
DESC_SIZE_Y = 0x04
DESC_VALUE_08 = 0x08
DESC_VALUE_0C = 0x0C
DESC_FLAG_10 = 0x10
DESC_BYTE_11 = 0x11
DESC_VALUE_14 = 0x14
DESC_FLAG_18 = 0x18


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "001204a4" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_001204a4 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):  # PC24 / CALL / JUMP24
            if "2c4b30" not in rel.symbol_name.lower():
                raise RuntimeError(f"unexpected call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (STUB_ASDMEM_ZERO - pc) >> 2
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


def build_descriptor(case: dict) -> bytes:
    page = filler(DESC_SIZE)
    put_u32(page, DESC_SIZE_X, case["size_x"])
    put_u32(page, DESC_SIZE_Y, case["size_y"])
    put_u32(page, DESC_VALUE_08, case["value08"])
    put_u32(page, DESC_VALUE_0C, case["value0c"])
    put_u8(page, DESC_FLAG_10, case["flag10"])
    put_u8(page, DESC_BYTE_11, case["byte11"])
    put_u32(page, DESC_VALUE_14, case["value14"])
    put_u8(page, DESC_FLAG_18, case["flag18"])
    return bytes(page)


def build_context(page_addr: int, vtable: int) -> bytes:
    page = filler(CONTEXT_SIZE)
    put_u32(page, 0, vtable)
    return bytes(page)


def build_vtables() -> bytes:
    page = filler(VT_SIZE)
    for base, target in (
        (VT_ADDR + 0x000, ALLOC1),
        (VT_ADDR + 0x100, ALLOC2),
    ):
        put_u32(page, base - VT_ADDR + 0x00, 0xDEAD0000 | (base & 0xFF))
        put_u32(page, base - VT_ADDR + 0x04, 0xDEAD0004)
        put_u32(page, base - VT_ADDR + 0x08, target)
        put_u32(page, base - VT_ADDR + 0x0C, 0xDEAD000C)
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # ARM11 MPCore = the 3DS core.  VFP needs CP10/CP11 enabled through
        # CPACR and FPEXC.EN, otherwise qemu reports VFP instructions invalid.
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (DESC_ADDR, DESC_SIZE),
            (CONTEXT_ADDR, CONTEXT_SIZE),
            (CONTEXT2_ADDR, CONTEXT2_SIZE),
            (RECORD_ADDR, RECORD_SIZE),
            (RECORD2_ADDR, RECORD2_SIZE),
            (SUB_ADDR, SUB_SIZE),
            (SUB2_ADDR, SUB2_SIZE),
            (PAYLOAD_ADDR, PAYLOAD_SIZE),
            (PAYLOAD2_ADDR, PAYLOAD2_SIZE),
            (VT_ADDR, VT_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for address, handler in (
            (STUB_ASDMEM_ZERO, self._on_asdmem_zero),
            (ALLOC1, self._on_allocate),
            (ALLOC2, self._on_allocate),
        ):
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, handler, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.uc.hook_add(
            unicorn.UC_HOOK_MEM_WRITE_UNMAPPED, self._on_unmapped_write
        )

        self.call_log: list = []
        self.writes: list = []
        self.unmapped: list = []
        self.case: dict = {}
        self.alloc_calls = 0

    # ------------------------------------------------------------------ stubs
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_unmapped_write(self, uc, access, address, size, value, user_data) -> bool:
        self.unmapped.append((address, size))
        return False

    def _u32(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _set_u32(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _set_u8(self, address: int, value: int) -> None:
        self.uc.mem_write(address, bytes((value & 0xFF,)))

    def _on_asdmem_zero(self, uc, address: int, size: int, user_data) -> None:
        ptr = uc.reg_read(arm.UC_ARM_REG_R0)
        count = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append((STUB_NAMES[address], (ptr, count)))
        if ptr != 0 and count != 0:
            uc.mem_write(ptr, b"\x00" * count)
        uc.reg_write(arm.UC_ARM_REG_R0, 0)

    def _on_allocate(self, uc, address: int, size: int, user_data) -> None:
        context = uc.reg_read(arm.UC_ARM_REG_R0)
        requested = uc.reg_read(arm.UC_ARM_REG_R1)
        flags = uc.reg_read(arm.UC_ARM_REG_R2)
        self.alloc_calls += 1
        call_index = self.alloc_calls
        self.call_log.append(
            (
                STUB_NAMES[address],
                (call_index, context, requested, flags),
            )
        )
        case = self.case

        # Descriptor rewrites are visible to the loads that follow this call.
        for key, offset, width in (
            ("mutate_size_x", DESC_SIZE_X, 4),
            ("mutate_size_y", DESC_SIZE_Y, 4),
            ("mutate_value0c", DESC_VALUE_0C, 4),
            ("mutate_flag10", DESC_FLAG_10, 1),
            ("mutate_byte11", DESC_BYTE_11, 1),
            ("mutate_value14", DESC_VALUE_14, 4),
            ("mutate_flag18", DESC_FLAG_18, 1),
        ):
            if case.get(f"{key}_on_call") == call_index:
                if width == 4:
                    self._set_u32(DESC_ADDR + offset, case[key])
                else:
                    self._set_u8(DESC_ADDR + offset, case[key])

        if case.get("switch_vtable_on_call") == call_index:
            self._set_u32(CONTEXT_ADDR, VT_ADDR + 0x100)

        results = case["alloc_results"]
        if call_index - 1 < len(results) and results[call_index - 1] is not None:
            result = results[call_index - 1]
        else:
            result = 0
        uc.reg_write(arm.UC_ARM_REG_R0, result)

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
        self.unmapped = []
        self.case = case
        self.alloc_calls = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DESC_ADDR, build_descriptor(case))
        self.uc.mem_write(CONTEXT_ADDR, build_context(CONTEXT_ADDR, VT_ADDR))
        self.uc.mem_write(CONTEXT2_ADDR, bytes(filler(CONTEXT2_SIZE)))
        self.uc.mem_write(RECORD_ADDR, bytes(filler(RECORD_SIZE)))
        self.uc.mem_write(RECORD2_ADDR, bytes(filler(RECORD2_SIZE)))
        self.uc.mem_write(SUB_ADDR, bytes(filler(SUB_SIZE)))
        self.uc.mem_write(SUB2_ADDR, bytes(filler(SUB2_SIZE)))
        self.uc.mem_write(PAYLOAD_ADDR, bytes(filler(PAYLOAD_SIZE)))
        self.uc.mem_write(PAYLOAD2_ADDR, bytes(filler(PAYLOAD2_SIZE)))
        self.uc.mem_write(VT_ADDR, build_vtables())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []
        self.unmapped = []

        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)  # CPACR: CP10/CP11
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)  # FPEXC.EN
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, DESC_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, CONTEXT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        faulted = False
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError:
            faulted = True

        unexpected_writes = [
            (address, size)
            for address, size in self.writes
            if (address, size) not in self.unmapped
            and not self._in_fixture(address, size)
        ]

        result = {
            "faulted": faulted,
            "call_log": self._normalise(self.call_log),
            "fixtures": {
                f"{base:08x}": bytes(self.uc.mem_read(base, length))
                for base, length in FIXTURE_PAGES
            },
            "unexpected_writes": unexpected_writes,
            "unmapped_writes": list(self.unmapped),
        }
        if not faulted:
            result.update(
                {
                    "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
                    "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
                    "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
                    "callee_saved": {
                        name: self.uc.reg_read(reg)
                        for name, reg in CALLEE_SAVED.items()
                    },
                }
            )
        return result


def compare(orig: dict, cand: dict, case_name: str) -> list[str]:
    problems = []
    if orig["faulted"] != cand["faulted"]:
        problems.append(
            f"fault mismatch: orig={orig['faulted']} cand={cand['faulted']} "
            f"(orig unmapped {orig['unmapped_writes']}, "
            f"cand unmapped {cand['unmapped_writes']})"
        )
        return problems
    if not orig["faulted"]:
        for key in ("ret", "pc", "sp", "callee_saved"):
            if orig[key] != cand[key]:
                problems.append(f"{key}: orig={orig[key]!r} cand={cand[key]!r}")
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
                    for index, (left, right) in enumerate(
                        zip(value, cand["fixtures"][key])
                    )
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
    if orig["faulted"]:
        # The null-dereference paths are not required to fault at the same
        # instruction (the compiler is free to reorder independent stores), but
        # the access must be a null access in both.
        if not orig["unmapped_writes"] or not cand["unmapped_writes"]:
            problems.append("fault was not an unmapped write")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "size_x": 2,
        "size_y": 3,
        "value08": 0x02000000,
        "value0c": 0x0C0C0C0C,
        "flag10": 1,
        "byte11": 1,
        "value14": 0x3F800000,
        "flag18": 0,
        "alloc_results": (RECORD_ADDR, SUB_ADDR, PAYLOAD_ADDR),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- payload gate and size loop bounds
    cases.append(base_case("no payload (flag18=0)"))
    for size_x, size_y in ((1, 1), (1, 2), (2, 3), (4, 5)):
        cases.append(
            base_case(
                f"payload {size_x}x{size_y} zero-filled",
                flag18=1,
                size_x=size_x,
                size_y=size_y,
            )
        )
    cases.append(base_case("payload not zero-filled", flag18=1, flag10=0))
    cases.append(
        base_case("payload 0x80 flags", flag18=0x80, flag10=0x80, size_x=1, size_y=1)
    )
    cases.append(
        base_case("payload 0xFF flags", flag18=0xFF, flag10=0xFF, size_x=1, size_y=2)
    )
    cases.append(
        base_case("payload size zero", flag18=1, flag10=1, size_x=0, size_y=7)
    )
    cases.append(
        base_case("payload size zero, no fill", flag18=1, flag10=0, size_x=0, size_y=7)
    )
    cases.append(
        base_case("payload size zero, null buffer", flag18=1, flag10=1,
                  size_x=0, size_y=7,
                  alloc_results=(RECORD_ADDR, SUB_ADDR, None))
    )

    # --- signed size boundaries through vcvt.f32.s32 / vcvt.u32.f32
    for size_x, size_y in (
        (-1, 1),
        (1, -1),
        (-0x80000000, 1),
        (0x7FFFFFFF, 1),
        (1, 0x7FFFFFFF),
        (0x20000000, 2),   # exactly 2^32 -> saturates to 0xFFFFFFFF
        (0x1FFFFFFF, 2),   # rounds up to 2^32 -> saturates
        (0x0FFFFFFF, 2),   # 4 * 2^28 * 2 = 2^31
        (0x40000000, 1),   # 2^32 -> saturates
        (0x10000000, 1),   # 2^30
    ):
        cases.append(
            base_case(
                f"size {size_x:#x}x{size_y:#x}",
                flag18=1,
                flag10=0,
                size_x=size_x,
                size_y=size_y,
            )
        )

    # --- allocation results
    cases.append(
        base_case("record allocation null", alloc_results=(None, SUB_ADDR, PAYLOAD_ADDR))
    )
    cases.append(
        base_case("sub allocation null, no payload",
                  alloc_results=(RECORD_ADDR, None, PAYLOAD_ADDR))
    )
    cases.append(
        base_case("sub allocation null, payload",
                  flag18=1, alloc_results=(RECORD_ADDR, None, PAYLOAD_ADDR))
    )
    cases.append(
        base_case("payload allocation null, no fill",
                  flag18=1, flag10=0,
                  alloc_results=(RECORD_ADDR, SUB_ADDR, None))
    )
    cases.append(
        base_case("payload allocation null, fill",
                  flag18=1, flag10=1, size_x=2, size_y=3,
                  alloc_results=(RECORD_ADDR, SUB_ADDR, None))
    )
    cases.append(
        base_case("alternate fixture pages",
                  flag18=1,
                  alloc_results=(RECORD2_ADDR, SUB2_ADDR, PAYLOAD2_ADDR))
    )
    cases.append(
        base_case("alternate record and sub only",
                  alloc_results=(RECORD2_ADDR, SUB2_ADDR, PAYLOAD_ADDR))
    )
    cases.append(
        base_case("null record and null sub",
                  alloc_results=(None, None, PAYLOAD_ADDR))
    )

    # --- indirect target reload
    cases.append(
        base_case("vtable swapped after call 1",
                  flag18=1, switch_vtable_on_call=1)
    )
    cases.append(
        base_case("vtable swapped after call 2",
                  flag18=1, switch_vtable_on_call=2)
    )
    cases.append(
        base_case("vtable swapped after call 3",
                  flag18=1, switch_vtable_on_call=3)
    )

    # --- descriptor fields rewritten by the allocator
    cases.append(
        base_case("size rewritten during call 1",
                  flag18=1, size_x=2, size_y=3,
                  mutate_size_x=5, mutate_size_x_on_call=1,
                  mutate_size_y=7, mutate_size_y_on_call=1)
    )
    cases.append(
        base_case("size rewritten during call 2",
                  flag18=1, size_x=2, size_y=3,
                  mutate_size_x=5, mutate_size_x_on_call=2,
                  mutate_size_y=7, mutate_size_y_on_call=2)
    )
    cases.append(
        base_case("value0c rewritten during call 2",
                  mutate_value0c=0xABABABAB, mutate_value0c_on_call=2)
    )
    cases.append(
        base_case("flag18 set during call 2",
                  flag18=0, mutate_flag18=1, mutate_flag18_on_call=2)
    )
    cases.append(
        base_case("flag18 cleared during call 2",
                  flag18=1, flag10=0,
                  mutate_flag18=0, mutate_flag18_on_call=2)
    )
    cases.append(
        base_case("fill flag set during call 3",
                  flag18=1, flag10=0, size_x=1, size_y=2,
                  mutate_flag10=1, mutate_flag10_on_call=3)
    )
    cases.append(
        base_case("fill flag cleared during call 3",
                  flag18=1, flag10=1, size_x=1, size_y=2,
                  mutate_flag10=0, mutate_flag10_on_call=3)
    )
    cases.append(
        base_case("trailing fields rewritten during call 3",
                  flag18=1, size_x=1, size_y=1,
                  mutate_byte11=0x5A, mutate_byte11_on_call=3,
                  mutate_value14=0xDEADBEEF, mutate_value14_on_call=3)
    )

    # --- descriptor value extremes
    cases.append(
        base_case("value extremes",
                  value08=0xFFFFFFFF, value0c=0x80000000,
                  value14=0x7FC00000, byte11=0xFF)
    )
    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
        problems = compare(orig, cand, case["name"])
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        suffix = " [fault parity]" if orig["faulted"] else ""
        print(
            f"  [PASS] {case['name']}  "
            f"({len(orig['call_log'])} events){suffix}"
        )
    return passed


def main() -> None:
    print("Testing engine_func_001204a4 (0x001204a4)...")
    orig_code = get_orig_bytes()
    if len(orig_code) != FUNC_SIZE:
        raise SystemExit(f"original body is {len(orig_code)} bytes")
    for address, expected in FUNC_LITERALS.items():
        value = struct.unpack_from("<I", orig_code, address - FUNC_ADDR)[0]
        if value != expected:
            raise SystemExit(
                f"literal at 0x{address:08x} is 0x{value:08x}, "
                f"expected 0x{expected:08x}"
            )

    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocation resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("payload_scale", "constexpr f32 kPayloadScale = 4.0f;",
         "constexpr f32 kPayloadScale = 2.0f;"),
        ("payload_gate", "if (field<u8>(descriptor, kPayloadFlagOffset) == 0) {",
         "if (field<u8>(descriptor, kPayloadFlagOffset) != 0) {"),
        ("sub_context_offset", "constexpr u32 kSubContextOffset = 0x10;",
         "constexpr u32 kSubContextOffset = 0x14;"),
        ("null_payload_link", "if (payload != nullptr) {",
         "if (payload == nullptr) {"),
        ("sub_size_store", "field<u32>(sub, kSubSizeOffset) = payload_size;",
         "field<u32>(sub, kSubSizeOffset) = payload_size + 1;"),
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
                problems = compare(orig, bad, case["name"])
            except Exception as error:  # pragma: no cover - diagnostic path
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
