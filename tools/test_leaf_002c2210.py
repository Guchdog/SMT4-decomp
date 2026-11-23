#!/usr/bin/env python3
"""Differential test for engine_func_002c2210 (0x002C2210) using Unicorn ARM.

Compiles ``src/engine/leaf_batch41_c.cpp``, extracts the
``engine_func_002c2210`` body, resolves its eight direct calls to deterministic
stubs at the pinned addresses, and runs the original bytes
(``extracted/exefs/code.bin``) against the candidate in separate Unicorn ARM
machines with identical fixtures.

The function is the AsdCamera projection/view initializer:

  * zero-fill 0x508 bytes through 0x002C4B30, then clear byte +0x01;
  * one-shot twelve-float identity image at 0x004EFD6C, gated by the low bit of
    0x00476634 and the Thumb test-and-set helper 0x002C00D4;
  * 0x002C00B4 copies that twelve-float image into ``self + 0x38``;
  * one-shot sixteen-float identity image at 0x004EFD9C, gated by 0x00476638;
  * 0x002C0000 copies sixteen floats into ``self + 0xA8``;
  * the original repeats the 0x00476638 gate and the same 0x004EFD9C stores,
    then unconditionally copies sixteen floats into ``self + 0xE8``;
  * 5.0f at ``self + 0x498`` and the low byte of ``mode`` at +0x00;
  * when the full 32-bit mode is non-zero, 0x0011CED4 runs on ``self + 0x4A0``
    and 5.0f / 1.0f are stored at ``self + 0x504`` / ``self + 0x500``.

Compared outputs:

  * continuation PC, final SP and callee-saved r4-r11 (the symbol returns
    void, so r0 at the final pop is incidental and is recorded only for
    diagnosis);
  * the ordered call log, with the call index, every register argument and
    the architected stack words of each helper;
  * every fixture page byte-for-byte: the guard page (both flag words), the
    shared-image page (0x004EFD6C and 0x004EFD9C) and the full 0x1000-byte
    projection block;
  * any emulated write outside a writable fixture page or the private stack.

Coverage: both flag words at 0, 1, other even values and 0x80000000; authentic
helper behaviour (store 1 / return 1 on a zero word) plus scripted return
sequences that hit the repeated third identity block; mode 0, 1, 2, 0x100,
0x101, 0xFFFFFFFF and 0x80000000; and low-byte-only mode storage.

Negative controls mutate the distance constant, both matrix-copy offsets, one
identity value, the guard mask and the tail field offsets; each mutant must be
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
OUT_DIR = ROOT / "build/test_leaf_002c2210"

FUNC_ADDR = 0x002C2210
FUNC_SIZE = 468
# Literal pool at 0x002C23C4..0x002C23E3.
FUNC_LITERALS = {
    0x002C23C4: 0x00000508,
    0x002C23C8: 0x00000000,  # 0.0f
    0x002C23CC: 0x3F800000,  # 1.0f
    0x002C23D0: 0x00476634,  # guard word A
    0x002C23D4: 0x004EFD6C,  # 3x4 image
    0x002C23D8: 0x00476638,  # guard word B
    0x002C23DC: 0x004EFD9C,  # 4x4 image
    0x002C23E0: 0x40A00000,  # 20.0f
}

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # body and every stub below 0x002C4B30

GUARD_PAGE_ADDR = 0x00476000
GUARD_PAGE_SIZE = 0x00001000
ENEMY_FLAGS_ADDR = 0x00476634
FILTER_FLAGS_ADDR = 0x00476638

MATRIX_PAGE_ADDR = 0x004EF000
MATRIX_PAGE_SIZE = 0x00001000
ENEMY_MATRIX_ADDR = 0x004EFD6C
FILTER_MATRIX_ADDR = 0x004EFD9C

BLOCK_ADDR = 0x00710000
BLOCK_SIZE = 0x00001000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Direct callees at their pinned addresses.
STUB_ZERO = 0x002C4B30
STUB_GUARD = 0x002C00D4  # Thumb in the pinned image (reached with `blx`)
STUB_COPY12 = 0x002C00B4
STUB_COPY16 = 0x002C0000
STUB_TAIL = 0x0011CED4

THUMB_STUBS = {STUB_GUARD}
STUB_NAMES = {
    STUB_ZERO: "zero_fill",
    STUB_GUARD: "guard",
    STUB_COPY12: "copy12",
    STUB_COPY16: "copy16",
    STUB_TAIL: "tail_init",
}

BLOCK_SIZE_BYTES = 0x508
TAIL_MARKER = 0xC0DE2210

ENEMY_IMAGE = struct.pack(
    "<12f", 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0
)
FILTER_IMAGE = struct.pack(
    "<16f",
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0,
)

WRITABLE_PAGES = (
    (GUARD_PAGE_ADDR, GUARD_PAGE_SIZE),
    (MATRIX_PAGE_ADDR, MATRIX_PAGE_SIZE),
    (BLOCK_ADDR, BLOCK_SIZE),
)

FIXTURE_PAGES = (
    (GUARD_PAGE_ADDR, GUARD_PAGE_SIZE),
    (MATRIX_PAGE_ADDR, MATRIX_PAGE_SIZE),
    (BLOCK_ADDR, BLOCK_SIZE),
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
        if "002c2210" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_002c2210 not found in {obj_file}: {sorted(funcs)}"
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


def build_guard_page(case: dict) -> bytes:
    page = filler(GUARD_PAGE_SIZE)
    put_u32(page, ENEMY_FLAGS_ADDR - GUARD_PAGE_ADDR, case["enemy_flags"])
    put_u32(page, FILTER_FLAGS_ADDR - GUARD_PAGE_ADDR, case["filter_flags"])
    return bytes(page)


def build_matrix_page() -> bytes:
    # Deliberately not the identity images so any rebuild is visible.
    return bytes(filler(MATRIX_PAGE_SIZE))


def build_block_page() -> bytes:
    return bytes([0xA5]) * BLOCK_SIZE


class Runner:
    """One Unicorn machine with deterministic stubs at the pinned addresses."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (GUARD_PAGE_ADDR, GUARD_PAGE_SIZE),
            (MATRIX_PAGE_ADDR, MATRIX_PAGE_SIZE),
            (BLOCK_ADDR, BLOCK_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        for address, handler in (
            (STUB_ZERO, self._on_zero),
            (STUB_GUARD, self._on_guard),
            (STUB_COPY12, self._on_copy12),
            (STUB_COPY16, self._on_copy16),
            (STUB_TAIL, self._on_tail),
        ):
            if address in THUMB_STUBS:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, handler, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.guard_calls = 0

    # ------------------------------------------------------------------ stubs
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _u32(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _set_u32(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_zero(self, uc, address: int, size: int, user_data) -> None:
        destination = uc.reg_read(arm.UC_ARM_REG_R0)
        count = uc.reg_read(arm.UC_ARM_REG_R1)
        self._log(address, destination, count)
        if count:
            uc.mem_write(destination, b"\x00" * count)
        uc.reg_write(arm.UC_ARM_REG_R0, destination)

    def _on_guard(self, uc, address: int, size: int, user_data) -> None:
        word_ptr = uc.reg_read(arm.UC_ARM_REG_R0)
        value = self._u32(word_ptr)
        self.guard_calls += 1
        index = self.guard_calls
        self._log(address, index, word_ptr, value)

        scripted = self.case.get("guard_returns")
        if scripted is not None:
            # Scripted results never update the word, so the repeated filter
            # gate can observe success more than once.
            result = scripted[index - 1]
            uc.reg_write(arm.UC_ARM_REG_R0, result)
            return

        if value != 0:
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        else:
            self._set_u32(word_ptr, 1)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)

    def _copy(self, uc, count: int) -> None:
        destination = uc.reg_read(arm.UC_ARM_REG_R0)
        source = uc.reg_read(arm.UC_ARM_REG_R1)
        payload = bytes(uc.mem_read(source, count))
        uc.mem_write(destination, payload)
        uc.reg_write(arm.UC_ARM_REG_R0, destination)
        return destination, source

    def _on_copy12(self, uc, address: int, size: int, user_data) -> None:
        destination, source = self._copy(uc, 0x30)
        self._log(address, destination, source)

    def _on_copy16(self, uc, address: int, size: int, user_data) -> None:
        destination, source = self._copy(uc, 0x40)
        self._log(address, destination, source)

    def _on_tail(self, uc, address: int, size: int, user_data) -> None:
        destination = uc.reg_read(arm.UC_ARM_REG_R0)
        self._log(address, destination)
        self._set_u32(destination, TAIL_MARKER)
        uc.reg_write(arm.UC_ARM_REG_R0, TAIL_MARKER)

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

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.guard_calls = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(GUARD_PAGE_ADDR, build_guard_page(case))
        self.uc.mem_write(MATRIX_PAGE_ADDR, build_matrix_page())
        self.uc.mem_write(BLOCK_ADDR, build_block_page())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)  # CPACR
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)  # FPEXC.EN
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, BLOCK_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["mode"] & 0xFFFFFFFF)
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
            if not self._in_writable_page(address, size)
        ]

        result = {
            "faulted": faulted,
            "call_log": self._normalise(self.call_log),
            "fixtures": {
                f"{base:08x}": bytes(self.uc.mem_read(base, length))
                for base, length in FIXTURE_PAGES
            },
            "unexpected_writes": unexpected_writes,
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
            f"fault mismatch: orig={orig['faulted']} cand={cand['faulted']}"
        )
        return problems
    if not orig["faulted"]:
        # The symbol returns void: r0 at `pop {r4, r5, r6, pc}` is whatever the
        # last helper or constant materialisation left behind (the tail call
        # when mode != 0, otherwise the 0x002C0000 destination).  It is
        # recorded for diagnosis but is not part of the contract; PC, SP and
        # the callee-saved registers are.
        for key in ("pc", "sp", "callee_saved"):
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
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "enemy_flags": 0,
        "filter_flags": 0,
        "mode": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- baseline: both images rebuilt once, mode 0 skips the tail.
    cases.append(base_case("flag words 0, mode 0"))
    cases.append(base_case("flag words 0, mode 1", mode=1))
    cases.append(base_case("flag words 0, mode 2", mode=2))
    cases.append(base_case("flag words 0, mode 0x100", mode=0x100))
    cases.append(base_case("flag words 0, mode 0x101", mode=0x101))
    cases.append(base_case("flag words 0, mode 0xFFFFFFFF", mode=0xFFFFFFFF))
    cases.append(base_case("flag words 0, mode 0x80000000", mode=0x80000000))

    # --- both guard words: bit 0 set, other bits only, sign bit only.
    for enemy, filt in (
        (1, 0),
        (0, 1),
        (1, 1),
        (3, 0),
        (0, 3),
        (2, 0),
        (0, 2),
        (0x80000000, 0),
        (0, 0x80000000),
        (0xFFFFFF00, 0x00010001),
    ):
        cases.append(
            base_case(
                f"enemy 0x{enemy:08x} filter 0x{filt:08x}",
                enemy_flags=enemy,
                filter_flags=filt,
            )
        )

    # --- scripted guard results exercise the repeated third identity block.
    #     1,1,1 with the word not updated means both filter blocks run.
    cases.append(
        base_case(
            "guard sequence 1,1,1 without store",
            guard_returns=(1, 1, 1),
            mode=1,
        )
    )
    cases.append(
        base_case(
            "guard sequence 1,0,1 without store",
            guard_returns=(1, 0, 1),
            mode=1,
        )
    )
    cases.append(
        base_case(
            "guard sequence 1,1,0 without store",
            guard_returns=(1, 1, 0),
        )
    )
    cases.append(
        base_case(
            "guard sequence 0,0,0",
            guard_returns=(0, 0, 0),
        )
    )
    cases.append(
        base_case(
            "guard sequence 1,1,1 with filter bit set",
            filter_flags=1,
            guard_returns=(1, 1, 1),
            mode=2,
        )
    )

    # --- mode low byte storage on every non-zero and zero form.
    for mode in (0x00, 0x7F, 0x80, 0xFF, 0x1FF, 0xFFFFFF7F):
        cases.append(base_case(f"mode 0x{mode:08x}", mode=mode))

    return cases


def check_contract(case: dict, result: dict) -> None:
    """Assert the recovered contract on the pinned original's own result."""
    if result["faulted"]:
        return
    block = result["fixtures"][f"{BLOCK_ADDR:08x}"]
    guard_page = result["fixtures"][f"{GUARD_PAGE_ADDR:08x}"]
    matrix_page = result["fixtures"][f"{MATRIX_PAGE_ADDR:08x}"]
    calls = result["call_log"]
    names = [entry[0] for entry in calls]

    assert names[0] == "zero_fill"
    assert calls[0][1] == (BLOCK_ADDR, BLOCK_SIZE_BYTES)
    assert names.count("copy12") == 1
    assert names.count("copy16") == 2
    copy12 = next(entry for entry in calls if entry[0] == "copy12")
    copy16 = [entry for entry in calls if entry[0] == "copy16"]
    assert copy12[1] == (BLOCK_ADDR + 0x38, ENEMY_MATRIX_ADDR)
    assert copy16[0][1] == (BLOCK_ADDR + 0xA8, FILTER_MATRIX_ADDR)
    assert copy16[1][1] == (BLOCK_ADDR + 0xE8, FILTER_MATRIX_ADDR)

    if case["mode"] == 0:
        assert "tail_init" not in names
    else:
        assert names.count("tail_init") == 1
        tail = next(entry for entry in calls if entry[0] == "tail_init")
        assert tail[1] == (BLOCK_ADDR + 0x4A0,)
        assert block[0x4A0:0x4A4] == struct.pack("<I", TAIL_MARKER)

    assert block[0x00] == case["mode"] & 0xFF
    assert block[0x01] == 0
    assert block[0x02:0x38] == b"\x00" * (0x38 - 0x02)
    assert block[0x498:0x49C] == struct.pack("<f", 5.0)
    if case["mode"] != 0:
        assert block[0x500:0x504] == struct.pack("<f", 1.0)
        assert block[0x504:0x508] == struct.pack("<f", 5.0)
    assert block[BLOCK_SIZE_BYTES:] == bytes([0xA5]) * (BLOCK_SIZE - BLOCK_SIZE_BYTES)

    assert block[0x38:0x68] == matrix_page[
        ENEMY_MATRIX_ADDR - MATRIX_PAGE_ADDR:
        ENEMY_MATRIX_ADDR - MATRIX_PAGE_ADDR + 0x30
    ]

    # Image contents, not just agreement: a guard rebuild must install the
    # exact identity image; a skipped rebuild must preserve the filler.
    scripted = case.get("guard_returns")
    matrix_filler = bytes(filler(MATRIX_PAGE_SIZE))
    filter_filler = matrix_filler[
        FILTER_MATRIX_ADDR - MATRIX_PAGE_ADDR:
        FILTER_MATRIX_ADDR - MATRIX_PAGE_ADDR + 0x40
    ]
    if scripted is None:
        assert block[0xA8:0xE8] == matrix_page[
            FILTER_MATRIX_ADDR - MATRIX_PAGE_ADDR:
            FILTER_MATRIX_ADDR - MATRIX_PAGE_ADDR + 0x40
        ]
        assert block[0xE8:0x128] == matrix_page[
            FILTER_MATRIX_ADDR - MATRIX_PAGE_ADDR:
            FILTER_MATRIX_ADDR - MATRIX_PAGE_ADDR + 0x40
        ]
    else:
        # With scripted (non-storing) results the two filter copies can see
        # different image states: copy 1 runs after the first gate and copy 2
        # after the repeated gate.
        if case["filter_flags"] & 1:
            first_copy = second_copy = filter_filler
        else:
            first_copy = FILTER_IMAGE if scripted[1] else filter_filler
            second_copy = (
                FILTER_IMAGE if (scripted[1] or scripted[2]) else filter_filler
            )
        assert block[0xA8:0xE8] == first_copy
        assert block[0xE8:0x128] == second_copy

    enemy_word = struct.unpack(
        "<I", guard_page[ENEMY_FLAGS_ADDR - GUARD_PAGE_ADDR:][:4]
    )[0]
    filter_word = struct.unpack(
        "<I", guard_page[FILTER_FLAGS_ADDR - GUARD_PAGE_ADDR:][:4]
    )[0]
    enemy_image = matrix_page[
        ENEMY_MATRIX_ADDR - MATRIX_PAGE_ADDR:
        ENEMY_MATRIX_ADDR - MATRIX_PAGE_ADDR + len(ENEMY_IMAGE)
    ]
    filter_image = matrix_page[
        FILTER_MATRIX_ADDR - MATRIX_PAGE_ADDR:
        FILTER_MATRIX_ADDR - MATRIX_PAGE_ADDR + len(FILTER_IMAGE)
    ]
    if scripted is None:
        if case["enemy_flags"] == 0:
            assert enemy_image == ENEMY_IMAGE
            assert enemy_word == 1
        else:
            # Bit 0 set skips the helper; an even non-zero word runs it but it
            # returns 0 without a store.
            assert enemy_image != ENEMY_IMAGE
            assert enemy_word == case["enemy_flags"]

        if case["filter_flags"] == 0:
            assert filter_image == FILTER_IMAGE
            assert filter_word == 1
        else:
            assert filter_image != FILTER_IMAGE
            assert filter_word == case["filter_flags"]
    else:
        assert enemy_image == (ENEMY_IMAGE if scripted[0] else enemy_image)
        if scripted[0]:
            assert enemy_image == ENEMY_IMAGE
        else:
            assert enemy_image != ENEMY_IMAGE
        assert enemy_word == case["enemy_flags"]
        if case["filter_flags"] & 1:
            assert filter_image != FILTER_IMAGE
            assert filter_word == case["filter_flags"]
        else:
            wrote_filter = bool(scripted[1] or scripted[2])
            if wrote_filter:
                assert filter_image == FILTER_IMAGE
            else:
                assert filter_image != FILTER_IMAGE
            assert filter_word == case["filter_flags"]


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
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing engine_func_002c2210 (0x002c2210)...")
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

    print("\nNegative controls:")
    for name, old, new in (
        ("distance", "constexpr f32 kDistance = 5.0f;",
         "constexpr f32 kDistance = 6.0f;"),
        ("enemy_matrix_offset", "constexpr u32 kEnemyMatrixOffset = 0x38;",
         "constexpr u32 kEnemyMatrixOffset = 0x3C;"),
        ("projection_matrix_offset",
         "constexpr u32 kProjectionMatrixOffset = 0xA8;",
         "constexpr u32 kProjectionMatrixOffset = 0xAC;"),
        ("view_matrix_offset", "constexpr u32 kViewMatrixOffset = 0xE8;",
         "constexpr u32 kViewMatrixOffset = 0xEC;"),
        ("far_plane_field_offset",
         "constexpr u32 kFarPlaneFieldOffset = 0x498;",
         "constexpr u32 kFarPlaneFieldOffset = 0x49C;"),
        ("mode_end_distance_offset",
         "constexpr u32 kModeEndDistanceOffset = 0x504;",
         "constexpr u32 kModeEndDistanceOffset = 0x508;"),
        ("guard_mask", "if ((*enemy_flags & 1u) == 0u &&",
         "if ((*enemy_flags & 2u) == 0u &&"),
        ("identity_last_word", "    image[15] = kOne;  // +0x3C",
         "    image[15] = kZero; // +0x3C"),
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

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
