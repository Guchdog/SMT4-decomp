#!/usr/bin/env python3
"""Differential test for engine_func_0012aef4 (0x0012AEF4) using Unicorn ARM.

Compiles ``src/engine/leaf_batch41_c.cpp``, extracts the
``engine_func_0012aef4`` body, resolves its three direct calls to deterministic
stubs at the pinned addresses, and runs the original bytes
(``extracted/exefs/code.bin``) against the candidate in separate Unicorn ARM
machines with identical fixtures.

The function builds a 0xD0-byte block from a caller-supplied allocator:

  * the allocator is a context object whose vtable slot +0x08 is called as
    ``allocator->vtable[2](allocator, size, flags)`` at two sites, so the slot
    is re-loaded from ``[allocator]`` before each request;
  * the block is zeroed, given a fixed header, an optional copy of ``name``
    (capped at 0x100 bytes, self-relative link at +0x0C called ``name_link``),
    a fixed 1.0f/0.0f image and a twelve-word copy of the shared image at
    0x004EFD6C, whose lazy initialisation is gated by the guard word at
    0x00476634 and the Thumb one-shot helper 0x002C00D4.

Compared outputs:

  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log: both allocations (call index, context, size, flags),
    the strlen argument, the memcpy arguments and the guard word/address, all
    with the architected registers (no helper takes a stack argument);
  * every fixture page byte-for-byte: guard page (flag word), shared-image
    page (0x004EFD6C), allocator context, both vtables, both block candidates,
    both name-copy candidates and the source name page;
  * that every emulated write stays inside a writable fixture page or the
    private stack (the source name page is not writable).

Coverage:

  * guard word 0 (guard runs, image rebuilt), 1 and 3 (bit 0 set, no guard),
    2 and 0x80000000 (guard runs, non-zero word, no rebuild), plus other-bit
    noise;
  * name null, empty, 1, 0xFE, 0xFF, 0x100, 0x101 and 0x200 bytes, so both
    sides of the 0x100 cap and the terminator position are exercised, plus a
    non-ASCII payload;
  * primary/alternate block and copy pages (both self-relative links);
  * first allocation null, second allocation null and both null (fault parity
    with the original: an unmapped access is the observable contract);
  * the vtable pointer swapped in the allocator context after call 1, proving
    the per-site reload;
  * block boundaries: exactly 0xD0 bytes zeroed, 0x54..0x83 and 0xB4..0xCF
    cleared, byte 0xD0 left untouched.

Negative controls mutate the block size, the name cap, the tag word, the
image word count, the name-link base and the guard branch; each mutant must be
detected.
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
OUT_DIR = ROOT / "build/test_leaf_0012aef4"

FUNC_ADDR = 0x0012AEF4
FUNC_SIZE = 448
# Literal pool at 0x0012B098..0x0012B0B3.
FUNC_LITERALS = {
    0x0012B098: 0x40000422,
    0x0012B09C: 0x07010000,
    0x0012B0A0: 0x4E465443,
    0x0012B0A4: 0x3F800000,  # 1.0f
    0x0012B0A8: 0x00000000,  # 0.0f
    0x0012B0AC: 0x00476634,  # guard word
    0x0012B0B0: 0x004EFD6C,  # shared image
}

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # body, 0x002C3290/0x002C5FF4/0x002C00D4, 0x002E0020

GUARD_PAGE_ADDR = 0x00476000
GUARD_PAGE_SIZE = 0x00001000
GUARD_WORD_ADDR = 0x00476634

MATRIX_PAGE_ADDR = 0x004EF000
MATRIX_PAGE_SIZE = 0x00001000
MATRIX_ADDR = 0x004EFD6C

CONTEXT_ADDR = 0x00710000
CONTEXT_SIZE = 0x00001000
VT_ADDR = 0x00760000
VT_SIZE = 0x00002000  # primary vtable at +0x000, secondary at +0x100

BLOCK_ADDR = 0x00720000
BLOCK2_ADDR = 0x00721000
COPY_ADDR = 0x00730000
COPY2_ADDR = 0x00731000
NAME_ADDR = 0x00740000
PAGE_SIZE = 0x00001000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Direct callees at their pinned addresses.
STUB_STRLEN = 0x002C3290
STUB_MEMCPY = 0x002C5FF4
STUB_GUARD = 0x002C00D4  # Thumb in the pinned image (reached with `blx`)
# Indirect allocation targets installed in vtable slot 2 (+0x08).
ALLOC1 = 0x002E0000
ALLOC2 = 0x002E0020

THUMB_STUBS = {STUB_GUARD}
STUB_NAMES = {
    STUB_STRLEN: "strlen",
    STUB_MEMCPY: "memcpy",
    STUB_GUARD: "guard",
    ALLOC1: "allocate_primary",
    ALLOC2: "allocate_secondary",
}

# Recovered block layout constants (see the source comment at 0x0012AEF4).
BLOCK_SIZE = 0xD0
NAME_LINK_OFFSET = 0x0C
FLAGS_OFFSET = 0x18
MATRIX_OFFSET = 0x84
MATRIX_BYTES = 0x30
MAX_NAME_LENGTH = 0x100
BLOCK_FILLER = 0xA5

IDENTITY_IMAGE = struct.pack(
    "<12f", 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0
)

WRITABLE_PAGES = (
    (GUARD_PAGE_ADDR, GUARD_PAGE_SIZE),
    (MATRIX_PAGE_ADDR, MATRIX_PAGE_SIZE),
    (CONTEXT_ADDR, CONTEXT_SIZE),
    (VT_ADDR, VT_SIZE),
    (BLOCK_ADDR, PAGE_SIZE),
    (BLOCK2_ADDR, PAGE_SIZE),
    (COPY_ADDR, PAGE_SIZE),
    (COPY2_ADDR, PAGE_SIZE),
)

FIXTURE_PAGES = (
    (GUARD_PAGE_ADDR, GUARD_PAGE_SIZE),
    (MATRIX_PAGE_ADDR, MATRIX_PAGE_SIZE),
    (CONTEXT_ADDR, CONTEXT_SIZE),
    (VT_ADDR, VT_SIZE),
    (BLOCK_ADDR, PAGE_SIZE),
    (BLOCK2_ADDR, PAGE_SIZE),
    (COPY_ADDR, PAGE_SIZE),
    (COPY2_ADDR, PAGE_SIZE),
    (NAME_ADDR, PAGE_SIZE),
)

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


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0012aef4" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0012aef4 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):  # PC24 / CALL / JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name.lower():
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")

        pc = FUNC_ADDR + rel.offset + 8
        offset = target - pc
        if target in THUMB_STUBS:
            # BLX (immediate): cond = 1111 101H, H = bit 1 of the offset.
            if offset & 3:
                raise RuntimeError(f"unaligned Thumb call target 0x{target:08x}")
            instruction = (
                0xFA000000 | ((offset >> 2) & 0x00FFFFFF) | ((offset & 2) << 23)
            )
            struct.pack_into("<I", code, rel.offset, instruction)
        else:
            displacement = offset >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
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


def put_u32(page: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", page, offset, value & 0xFFFFFFFF)


def filler(size: int) -> bytearray:
    return bytearray((index * 37 + 11) & 0xFF for index in range(size))


def build_block_page() -> bytes:
    return bytes([BLOCK_FILLER]) * PAGE_SIZE


def build_copy_page() -> bytes:
    return bytes([0x5A]) * PAGE_SIZE


def build_context(vtable: int) -> bytes:
    page = filler(CONTEXT_SIZE)
    put_u32(page, 0, vtable)
    return bytes(page)


def build_vtables() -> bytes:
    page = filler(VT_SIZE)
    for base, target in ((VT_ADDR + 0x000, ALLOC1), (VT_ADDR + 0x100, ALLOC2)):
        put_u32(page, base - VT_ADDR + 0x00, 0xDEAD0000 | (base & 0xFF))
        put_u32(page, base - VT_ADDR + 0x04, 0xDEAD0004)
        put_u32(page, base - VT_ADDR + 0x08, target)
        put_u32(page, base - VT_ADDR + 0x0C, 0xDEAD000C)
    return bytes(page)


def build_guard_page(case: dict) -> bytes:
    page = filler(GUARD_PAGE_SIZE)
    put_u32(page, GUARD_WORD_ADDR - GUARD_PAGE_ADDR, case["flag_word"])
    return bytes(page)


def build_matrix_page() -> bytes:
    # A sentinel pattern that is not the identity image, so a rebuild is
    # visible in the copied block words as well.
    return bytes(filler(MATRIX_PAGE_SIZE))


def build_name_page(case: dict) -> bytes:
    page = filler(PAGE_SIZE)
    text = case["name_text"]
    if text is not None:
        page[0 : len(text)] = text
        page[len(text)] = 0
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the pinned addresses."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (GUARD_PAGE_ADDR, GUARD_PAGE_SIZE),
            (MATRIX_PAGE_ADDR, MATRIX_PAGE_SIZE),
            (CONTEXT_ADDR, CONTEXT_SIZE),
            (VT_ADDR, VT_SIZE),
            (BLOCK_ADDR, PAGE_SIZE),
            (BLOCK2_ADDR, PAGE_SIZE),
            (COPY_ADDR, PAGE_SIZE),
            (COPY2_ADDR, PAGE_SIZE),
            (NAME_ADDR, PAGE_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        for address, handler in (
            (STUB_STRLEN, self._on_strlen),
            (STUB_MEMCPY, self._on_memcpy),
            (STUB_GUARD, self._on_guard),
            (ALLOC1, self._on_allocate),
            (ALLOC2, self._on_allocate),
        ):
            if address in THUMB_STUBS:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
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

    def _on_unmapped_write(self, uc, access, address, size, value, user_data):
        self.unmapped.append((address, size))
        return False

    def _u32(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _set_u32(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _read_c_string(self, address: int, limit: int = 0x1000) -> bytes:
        raw = bytes(self.uc.mem_read(address, limit))
        end = raw.find(b"\x00")
        return raw if end < 0 else raw[:end]

    def _on_strlen(self, uc, address: int, size: int, user_data) -> None:
        text_ptr = uc.reg_read(arm.UC_ARM_REG_R0)
        text = self._read_c_string(text_ptr)
        self.call_log.append((STUB_NAMES[address], (text_ptr, text)))
        uc.reg_write(arm.UC_ARM_REG_R0, len(text))

    def _on_memcpy(self, uc, address: int, size: int, user_data) -> None:
        destination = uc.reg_read(arm.UC_ARM_REG_R0)
        source = uc.reg_read(arm.UC_ARM_REG_R1)
        count = uc.reg_read(arm.UC_ARM_REG_R2)
        self.call_log.append(
            (STUB_NAMES[address], (destination, source, count))
        )
        if count:
            payload = bytes(uc.mem_read(source, count))
            try:
                uc.mem_write(destination, payload)
            except unicorn.UcError:
                # A null destination faults like the real memcpy would; the
                # emulated write itself is out of range, so record it here.
                self.unmapped.append((destination, 1))
                raise
        uc.reg_write(arm.UC_ARM_REG_R0, destination)

    def _on_guard(self, uc, address: int, size: int, user_data) -> None:
        word_ptr = uc.reg_read(arm.UC_ARM_REG_R0)
        value = self._u32(word_ptr)
        self.call_log.append((STUB_NAMES[address], (word_ptr, value)))
        if value != 0:
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        else:
            self._set_u32(word_ptr, 1)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)

    def _on_allocate(self, uc, address: int, size: int, user_data) -> None:
        context = uc.reg_read(arm.UC_ARM_REG_R0)
        requested = uc.reg_read(arm.UC_ARM_REG_R1)
        flags = uc.reg_read(arm.UC_ARM_REG_R2)
        self.alloc_calls += 1
        call_index = self.alloc_calls
        self.call_log.append(
            (STUB_NAMES[address], (call_index, context, requested, flags))
        )

        if self.case.get("switch_vtable_on_call") == call_index:
            self._set_u32(CONTEXT_ADDR, VT_ADDR + 0x100)

        results = self.case["alloc_results"]
        result = results[call_index - 1] if call_index - 1 < len(results) else None
        uc.reg_write(arm.UC_ARM_REG_R0, result or 0)

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

    def _in_writable_page(self, address: int, size: int) -> bool:
        for base, length in WRITABLE_PAGES:
            if base <= address and address + size <= base + length:
                return True
        return STACK_ADDR <= address < STACK_ADDR + STACK_SIZE

    def run(self, code: bytes, case: dict, guard_page: bytes | None = None) -> dict:
        self.call_log = []
        self.writes = []
        self.unmapped = []
        self.case = case
        self.alloc_calls = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(
            GUARD_PAGE_ADDR, guard_page if guard_page is not None
            else build_guard_page(case)
        )
        self.uc.mem_write(MATRIX_PAGE_ADDR, build_matrix_page())
        self.uc.mem_write(CONTEXT_ADDR, build_context(VT_ADDR))
        self.uc.mem_write(VT_ADDR, build_vtables())
        self.uc.mem_write(BLOCK_ADDR, build_block_page())
        self.uc.mem_write(BLOCK2_ADDR, build_block_page())
        self.uc.mem_write(COPY_ADDR, build_copy_page())
        self.uc.mem_write(COPY2_ADDR, build_copy_page())
        self.uc.mem_write(NAME_ADDR, build_name_page(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []
        self.unmapped = []

        # The original uses vldr/vstr for the fixed 1.0f/0.0f image.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)  # CPACR
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)  # FPEXC.EN
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CONTEXT_ADDR)
        self.uc.reg_write(
            arm.UC_ARM_REG_R1,
            NAME_ADDR if case["name_text"] is not None else 0,
        )
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
            and not self._in_writable_page(address, size)
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


def compare(orig: dict, cand: dict) -> list[str]:
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
        # Null-allocation paths must fault on an unmapped access in both.
        if not orig["unmapped_writes"] or not cand["unmapped_writes"]:
            problems.append("fault was not an unmapped write")
    return problems


def base_case(name: str, **overrides) -> dict:
    text = overrides.pop("name_text", b"model")
    case = {
        "name": name,
        "name_text": text,
        "flag_word": 0,
        "alloc_results": (BLOCK_ADDR, COPY_ADDR),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- guard word: bit 0 clear (guard runs) and set (guard skipped)
    cases.append(base_case("flag 0, name 'model'"))
    cases.append(base_case("flag 1, name 'model'", flag_word=1))
    cases.append(base_case("flag 2 (guard runs, non-zero)", flag_word=2))
    cases.append(base_case("flag 3 (bit 0 set)", flag_word=3))
    cases.append(base_case("flag 0x80000000 (guard runs)", flag_word=0x80000000))
    cases.append(base_case("flag 0xFFFFFFFF", flag_word=0xFFFFFFFF))
    cases.append(base_case("flag 0x00010001", flag_word=0x00010001))
    cases.append(base_case("flag 0xFFFFFF00 (guard runs)", flag_word=0xFFFFFF00))

    # --- name: null and the empty string
    cases.append(base_case("name null", name_text=None))
    cases.append(base_case("name empty", name_text=b""))
    cases.append(base_case("name null, flag 1", name_text=None, flag_word=1))

    # --- name: both sides of the 0x100 cap
    for length in (1, 2, 0x7F, 0xFE, 0xFF, 0x100, 0x101, 0x180, 0x200):
        cases.append(
            base_case(
                f"name {length:#x} bytes",
                name_text=b"n" * length,
            )
        )
    cases.append(
        base_case(
            "name non-ASCII payload",
            name_text=bytes(range(0x80, 0x100)) * 2,
        )
    )

    # --- allocation results
    cases.append(
        base_case(
            "alternate block and copy",
            alloc_results=(BLOCK2_ADDR, COPY2_ADDR),
        )
    )
    cases.append(
        base_case(
            "alternate block only",
            alloc_results=(BLOCK2_ADDR, COPY_ADDR),
        )
    )
    cases.append(
        base_case("block allocation null", alloc_results=(None, COPY_ADDR))
    )
    cases.append(
        base_case("copy allocation null", alloc_results=(BLOCK_ADDR, None))
    )
    cases.append(
        base_case(
            "copy allocation null, long name",
            name_text=b"z" * 0x101,
            alloc_results=(BLOCK_ADDR, None),
        )
    )
    cases.append(
        base_case("both allocations null", alloc_results=(None, None))
    )
    cases.append(
        base_case("null name with null block", name_text=None,
                  alloc_results=(None, COPY_ADDR))
    )

    # --- the vtable pointer is re-read before the second request
    cases.append(
        base_case(
            "vtable swapped after call 1",
            name_text=b"swap",
            switch_vtable_on_call=1,
        )
    )
    cases.append(
        base_case(
            "vtable swapped after call 2",
            name_text=b"swap",
            switch_vtable_on_call=2,
        )
    )

    # --- guard image interleaved with a long name copy
    cases.append(
        base_case(
            "flag 0 with 0x100-byte name",
            name_text=b"q" * 0x100,
            flag_word=0,
            alloc_results=(BLOCK2_ADDR, COPY2_ADDR),
        )
    )
    return cases


def make_random_cases(count: int = 48) -> list[dict]:
    """Deterministic cross-product sweep of the independent inputs."""
    import random

    rng = random.Random(0x12AEF4)
    flag_words = (0, 1, 2, 3, 0x00010000, 0x80000003, 0xFFFFFFFE)
    results = (
        (BLOCK_ADDR, COPY_ADDR),
        (BLOCK_ADDR, COPY2_ADDR),
        (BLOCK2_ADDR, COPY_ADDR),
        (BLOCK2_ADDR, COPY2_ADDR),
        (None, COPY_ADDR),
        (BLOCK_ADDR, None),
        (None, None),
    )
    cases: list[dict] = []
    for index in range(count):
        length = rng.choice(
            (0, 1, 3, 0x10, 0x7F, 0xFE, 0xFF, 0x100, 0x101, 0x1FF, 0x250)
        )
        text = bytes(rng.randrange(0x20, 0x100) for _ in range(length))
        case = base_case(
            f"random {index}: flag 0x{rng.getrandbits(32):08x}",
            name_text=text,
            flag_word=rng.choice(flag_words),
            alloc_results=rng.choice(results),
        )
        # Recompute the label from the values actually chosen.
        case["name"] = (
            f"random {index}: flag 0x{case['flag_word']:08x}, "
            f"name {length:#x}, {case['alloc_results']}"
        )
        swap = rng.choice((None, 1, 2))
        if swap is not None:
            case["switch_vtable_on_call"] = swap
        cases.append(case)
    return cases


def check_contract(case: dict, result: dict) -> None:
    """Assert the recovered contract on the pinned original's own result."""
    if result["faulted"]:
        return
    name = case["name_text"]
    block_addr = case["alloc_results"][0]
    block = result["fixtures"][f"{block_addr:08x}"]
    matrix_page = result["fixtures"][f"{MATRIX_PAGE_ADDR:08x}"]
    guard_page = result["fixtures"][f"{GUARD_PAGE_ADDR:08x}"]
    calls = result["call_log"]
    call_names = [entry[0] for entry in calls]

    assert result["ret"] == block_addr, "return value is the block pointer"

    # --- fixed header and image
    assert block[0x00:0x04] == struct.pack("<I", 0x40000422)
    assert block[0x04:0x08] == struct.pack("<I", 0x4E465443)
    assert block[0x08:0x0C] == struct.pack("<I", 0x07010000)
    assert block[0x10:0x18] == b"\x00" * 8
    assert block[0x30:0x3C] == struct.pack("<3f", 1.0, 1.0, 1.0)
    assert block[0x3C:0x54] == b"\x00" * 0x18
    assert block[0x54:0x84] == b"\x00" * 0x30
    assert block[0xB4:BLOCK_SIZE] == b"\x00" * (BLOCK_SIZE - 0xB4)
    assert block[BLOCK_SIZE:] == bytes([BLOCK_FILLER]) * (PAGE_SIZE - BLOCK_SIZE)
    assert block[FLAGS_OFFSET:FLAGS_OFFSET + 4] == struct.pack("<I", 1)

    # --- guard word and image
    flag_word = struct.unpack(
        "<I", guard_page[GUARD_WORD_ADDR - GUARD_PAGE_ADDR:][:4]
    )[0]
    if case["flag_word"] & 1:
        assert "guard" not in call_names, "bit 0 set must skip the guard"
        image = matrix_page[
            MATRIX_ADDR - MATRIX_PAGE_ADDR:
            MATRIX_ADDR - MATRIX_PAGE_ADDR + MATRIX_BYTES
        ]
        assert flag_word == case["flag_word"], "guard word must be untouched"
    else:
        assert call_names.count("guard") == 1
        guard_args = calls[call_names.index("guard")][1]
        assert guard_args[0] == GUARD_WORD_ADDR
        assert guard_args[1] == case["flag_word"]
        if case["flag_word"] == 0:
            assert flag_word == 1, "guard stores 1 into a zero word"
            image = IDENTITY_IMAGE
        else:
            assert flag_word == case["flag_word"], "non-zero word is not rewritten"
            image = matrix_page[
                MATRIX_ADDR - MATRIX_PAGE_ADDR:
                MATRIX_ADDR - MATRIX_PAGE_ADDR + MATRIX_BYTES
            ]
    assert block[MATRIX_OFFSET:MATRIX_OFFSET + MATRIX_BYTES] == image

    # --- name copy
    if name is None:
        assert block[NAME_LINK_OFFSET:NAME_LINK_OFFSET + 4] == b"\x00" * 4
        assert "strlen" not in call_names
        assert call_names.count("allocate_primary") + call_names.count(
            "allocate_secondary"
        ) == 1
        return

    kept = min(len(name), MAX_NAME_LENGTH)
    copy_addr = case["alloc_results"][1]
    assert block[NAME_LINK_OFFSET:NAME_LINK_OFFSET + 4] == struct.pack(
        "<I", (copy_addr - (block_addr + NAME_LINK_OFFSET)) & 0xFFFFFFFF
    )
    assert call_names.count("strlen") == 1
    assert calls[call_names.index("strlen")][1] == (NAME_ADDR, name)
    copy_call = [entry for entry in calls if entry[0].startswith("allocate_")][1]
    assert copy_call[1][2] == kept + 1, "second request is kept + 1 bytes"
    assert copy_call[1][3] == 4
    memcpy_call = calls[call_names.index("memcpy")][1]
    assert memcpy_call == (copy_addr, NAME_ADDR, kept)
    copy = result["fixtures"][f"{copy_addr:08x}"]
    assert copy[0:kept] == name[:kept]
    assert copy[kept] == 0, "terminator directly after the copied prefix"
    assert copy[kept + 1:] == bytes([0x5A]) * (PAGE_SIZE - kept - 1)


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
        try:
            check_contract(case, orig)
        except AssertionError as error:
            print(f"  [FAIL] contract check: {case['name']}: {error}")
            raise SystemExit(1)
        passed += 1
        suffix = " [fault parity]" if orig["faulted"] else ""
        print(
            f"  [PASS] {case['name']}  "
            f"({len(orig['call_log'])} calls){suffix}"
        )
    return passed


def main() -> None:
    print("Testing engine_func_0012aef4 (0x0012aef4)...")
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
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nRandomised sweep:")
    random_cases = make_random_cases()
    passed += run_case_set(orig_code, cand_code, random_cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("block_size", "constexpr u32 kBlockSize = 0xD0;",
         "constexpr u32 kBlockSize = 0xCF;"),
        ("name_cap", "constexpr u32 kMaxNameLength = 0x100;",
         "constexpr u32 kMaxNameLength = 0xFF;"),
        ("tag_word", "constexpr u32 kTag = 0x40000422;",
         "constexpr u32 kTag = 0x40000423;"),
        ("image_words", "constexpr u32 kMatrixWords = 12;",
         "constexpr u32 kMatrixWords = 11;"),
        ("name_link_base", "copy - (block + kNameLinkOffset));",
         "copy - (block + 0x10));"),
        ("guard_branch", "if ((guard_word() & kFlagReady) == 0) {",
         "if ((guard_word() & kFlagReady) != 0) {"),
        ("zero_fill_length",
         "    // 0x0012AF24..0x0012AF2C: unconditional zero fill of exactly 0xD0 bytes.\n"
         "    for (u32 index = 0; index < kBlockSize; ++index) {",
         "    // 0x0012AF24..0x0012AF2C: unconditional zero fill of exactly 0xD0 bytes.\n"
         "    for (u32 index = 0; index < kBlockSize - 4; ++index) {"),
        ("terminator",
         "        // 0x0012AF74..0x0012AFAC: copy the capped prefix and terminate it.\n"
         "        u8* const copy = static_cast<u8*>(\n"
         "            allocate_slot(allocator)(allocator, kept + 1, kBlockAlign));\n"
         "        engine_func_002c5ff4(copy, name, kept);\n"
         "        copy[kept] = 0;",
         "        // 0x0012AF74..0x0012AFAC: copy the capped prefix and terminate it.\n"
         "        u8* const copy = static_cast<u8*>(\n"
         "            allocate_slot(allocator)(allocator, kept + 1, kBlockAlign));\n"
         "        engine_func_002c5ff4(copy, name, kept);\n"
         "        copy[kept + 1] = 0;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        detail = ""
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            problems = compare(orig, bad)
            if problems:
                detected = True
                detail = problems[0].splitlines()[0]
                break
        if not detected:
            print(f"  [FAIL] mutant {name} was not detected")
            raise SystemExit(1)
        print(f"  [PASS] {name} mutant detected ({detail})")

    print(
        f"\nAll {passed}/{len(cases) + len(random_cases)} differential cases PASSED."
    )


if __name__ == "__main__":
    main()
