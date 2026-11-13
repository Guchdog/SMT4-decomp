#!/usr/bin/env python3
"""Differential test for shop_func_003a8b14 (0x003a8b14) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the shop_func_003a8b14 body,
resolves its direct calls to deterministic stubs at the pinned target addresses,
and runs the original (extracted/exefs/code.bin) and the candidate in separate
Unicorn machines with identical fixtures.

Compared outputs:
  * r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log: every helper's arguments (the 0x002BE7FC strings are
    logged by content, the 0x002A0F68 value as a byte, and 0x00233804's count as
    a signed word);
  * the text published through 0x0029F10C (read back from the stack buffer);
  * the full 128 KiB work page, the 0x0043D000 global page and the pinned
    original 0x00402000 rodata page;
  * any emulated write outside the private stack or the work page.

Coverage:
  * sprite gate 0 and non-zero (early return after the coordinate store);
  * cursor reloaded after 0x002334D8, signed cursor boundaries (0, 1, 7,
    -1, 0x7FFF, 0x8000) and the resulting 140-byte record address;
  * both mode branches; mode values 0, 1, 2, 0x80, 0xFF;
  * mode mutated by 0x002B8B78 between the request and the second branch;
  * resource lookup returning a string, an empty string and null (pinned
    "＞＞＞" fallback);
  * list index 0, 1, 0x7FF and 0xFFFFFFFF (wrapped 0x20-byte stride);
  * signed row-count clamp boundaries -1, 0, 9, 10, 11, 0x7FFFFFFF, 0x80000000;
  * the refresh virtual swapping work+0x590 so the reload before the +0x04
    flag update is observable.

Negative controls mutate the record stride, the mode-non-zero sound request,
the signed row clamp and the post-helper cursor re-read; every mutant must be
detected by the same comparison.
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
OUT_DIR = ROOT / "build/test_leaf_003a8b14"

FUNC_ADDR = 0x003A8B14
FUNC_SIZE = 428

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000
WORK_ADDR = 0x00700000
WORK_SIZE = 0x00020000  # 128 KiB covers entries up to index 0x7FF
GLOBAL_ADDR = 0x0043D000
GLOBAL_SIZE = 0x00001000
ORIG_RODATA_ADDR = 0x00402000
ORIG_RODATA_SIZE = 0x00001000
RODATA_ADDR = 0x00750000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Pinned direct-call targets.  Both the original bytes and the relocated
# candidate resolve to these exact addresses.
STUB_2334D8 = 0x002334D8
STUB_2BEF70 = 0x002BEF70
STUB_2BEF7C = 0x002BEF7C
STUB_2313D4 = 0x002313D4
STUB_2B8B78 = 0x002B8B78
STUB_22CC38 = 0x0022CC38
STUB_2BE7FC = 0x002BE7FC
STUB_29F10C = 0x0029F10C
STUB_2337A0 = 0x002337A0
STUB_29DCD4 = 0x0029DCD4
STUB_2A0F68 = 0x002A0F68
STUB_233804 = 0x00233804

# The refresh virtual is fixture code; entry 3 is a distinct stub used by a
# negative control.
STUB_VIRTUAL = 0x003E0000
STUB_VIRTUAL_ALT = 0x003E0008

# 0x2BE7FC is Thumb code in the pinned binary (the original reaches it with
# `blx`).  A real linker turns the candidate's R_ARM_CALL into BLX as well.
THUMB_STUBS = {STUB_2BE7FC}

STUB_NAMES = {
    STUB_2334D8: "shop_func_002334d8",
    STUB_2BEF70: "shop_func_002bef70",
    STUB_2BEF7C: "ui_func_002bef7c",
    STUB_2313D4: "shop_func_002313d4",
    STUB_2B8B78: "script_vm_func_002b8b78",
    STUB_22CC38: "func_0022cc38",
    STUB_2BE7FC: "ui_func_002be7fc",
    STUB_29F10C: "camp_func_0029f10c",
    STUB_2337A0: "shop_func_002337a0",
    STUB_29DCD4: "camp_func_0029dcd4",
    STUB_2A0F68: "camp_func_002a0f68",
    STUB_233804: "unite_func_00233804",
    STUB_VIRTUAL: "sub_refresh",
    STUB_VIRTUAL_ALT: "sub_refresh_alt",
}

# No direct helper receives an architected stack argument; the variadic
# 0x002BE7FC call uses only r0-r3 as well.
STACK_ARGS = {address: 0 for address in STUB_NAMES}

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

MODE_OFFSET = 0x5A4
CURSOR_OFFSET = 0xA5B2
TARGET_ID_OFFSET = 0xA5B4
LIST_PANEL_OFFSET = 0x20
ROW_COUNT_OFFSET = 0x28
ROWS_OFFSET = 0x55C
SUB_OBJECT_OFFSET = 0x590
SPRITE_GROUP_OFFSET = 0xDC
COORD_OFFSET = 0xC8
ENTRY_BASE_OFFSET = 0x5A8
ENTRY_STRIDE = 0x20
ENTRY_ID_OFFSET = 0x04
CURSOR_RECORD_BASE = 0xFC
CURSOR_RECORD_STRIDE = 140

SUB_OBJECT_A = WORK_ADDR + 0x2000
SUB_OBJECT_B = WORK_ADDR + 0x2100
SUB_VTABLE = WORK_ADDR + 0x2300
SPRITE_GROUP = WORK_ADDR + 0x2400

LABEL_ADDR = RODATA_ADDR + 0x1000
RESOURCE_NAME_ADDR = RODATA_ADDR + 0x1100
RESOURCE_EMPTY_ADDR = RODATA_ADDR + 0x1200

LABEL_TEXT = "カウンターリスト".encode("cp932") + b"\x00"
MISSING_NAME_TEXT = b"\x81\x9b\x81\x9b\x81\x9b\x00"
NAME_FORMAT = b"%s%s\x00"


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def get_orig_rodata_page() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(ORIG_RODATA_ADDR - 0x00100000)
        return f.read(ORIG_RODATA_SIZE)


def elf_sections(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        result[name] = data[section[4] : section[4] + section[5]]
    return result


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "003a8b14" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"shop_func_003a8b14 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address, name in STUB_NAMES.items():
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            offset = target - pc
            if target in THUMB_STUBS:
                # BLX (immediate): cond=1111 101H, H = bit 1 of the offset.
                if offset & 3:
                    raise RuntimeError(
                        f"unaligned Thumb call target 0x{target:08x}"
                    )
                instruction = (
                    0xFA000000
                    | ((offset >> 2) & 0x00FFFFFF)
                    | ((offset & 2) << 23)
                )
                struct.pack_into("<I", code, rel.offset, instruction)
            else:
                displacement = offset >> 2
                original = struct.unpack_from("<I", code, rel.offset)[0]
                cond = original & 0xFF000000
                struct.pack_into(
                    "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
                )
        elif rel.relocation_type == 2:  # R_ARM_ABS32 into .rodata
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, RODATA_ADDR + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )

    rodata = elf_sections(obj_file).get(".rodata", b"")
    if MISSING_NAME_TEXT not in rodata:
        raise RuntimeError("could not locate the pinned fallback string in .rodata")
    if NAME_FORMAT not in rodata:
        raise RuntimeError("could not locate the '%s%s' format string in .rodata")
    return bytes(code), rodata


def compile_candidate_baseline() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
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
def read_c_string(uc, address: int, limit: int = 64) -> bytes:
    out = bytearray()
    for index in range(limit):
        try:
            byte = uc.mem_read(address + index, 1)[0]
        except Exception:
            break
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


def safe_read_s32(uc, address: int) -> int:
    try:
        return struct.unpack("<i", uc.mem_read(address, 4))[0]
    except Exception:
        # Deterministic fallback for cursor values whose 140-byte stride wraps
        # outside the mapped fixtures.  Both sides see the same address.
        return ((address ^ 0x5A5A5A5A) & 0xFFFFFFFF) - 0x10000000


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def build_work(case: dict) -> bytes:
    page = bytearray(WORK_SIZE)
    # Deterministic filler; comparisons cover the whole page.
    for offset in range(0, WORK_SIZE, 4):
        struct.pack_into("<I", page, offset, 0xA5A50000 | ((offset * 7) & 0xFFFF))

    page[MODE_OFFSET] = case.get("mode", 0) & 0xFF
    struct.pack_into("<h", page, CURSOR_OFFSET, case.get("cursor", 0))
    struct.pack_into("<I", page, TARGET_ID_OFFSET, case.get("target_id", 0) & 0xFFFFFFFF)
    struct.pack_into("<i", page, ROW_COUNT_OFFSET, s32(case.get("row_count", 0)))
    struct.pack_into("<I", page, COORD_OFFSET, 0x3F800000)
    struct.pack_into("<I", page, COORD_OFFSET + 4, 0xC0000000)
    struct.pack_into("<I", page, ROWS_OFFSET, 0xDEADBEEF)
    struct.pack_into("<I", page, SUB_OBJECT_OFFSET, case.get("sub_pointer", SUB_OBJECT_A))
    struct.pack_into("<I", page, SPRITE_GROUP_OFFSET, SPRITE_GROUP)

    # Sub-objects and their shared vtable.
    struct.pack_into("<I", page, SUB_OBJECT_A - WORK_ADDR, SUB_VTABLE)
    struct.pack_into("<H", page, SUB_OBJECT_A - WORK_ADDR + 4, 0x0200)
    struct.pack_into("<I", page, SUB_OBJECT_B - WORK_ADDR, SUB_VTABLE)
    struct.pack_into("<H", page, SUB_OBJECT_B - WORK_ADDR + 4, 0x0400)
    for index in range(8):
        struct.pack_into("<I", page, SUB_VTABLE - WORK_ADDR + index * 4, STUB_VIRTUAL_ALT)
    struct.pack_into("<I", page, SUB_VTABLE - WORK_ADDR + 2 * 4, STUB_VIRTUAL)

    # Cursor records for the small indices; other indices use the filler.
    for index in range(8):
        base = CURSOR_RECORD_BASE + index * CURSOR_RECORD_STRIDE
        struct.pack_into("<i", page, base + 0x0C, (100 + index) * 4096)
        struct.pack_into("<i", page, base + 0x10, -(200 + index) * 4096)

    # List entries.
    for index in range(8):
        base = ENTRY_BASE_OFFSET + index * ENTRY_STRIDE
        struct.pack_into("<H", page, base + ENTRY_ID_OFFSET, 0x1000 + index)
    # The 0xFFFFFFFF index wraps to entry base - 0x20; give that a unique id.
    struct.pack_into("<H", page, ENTRY_BASE_OFFSET - 0x20 + ENTRY_ID_OFFSET, 0xEFFF)

    page[LIST_PANEL_OFFSET] = 1
    return bytes(page)


def build_global_page() -> bytes:
    page = bytearray(GLOBAL_SIZE)
    struct.pack_into("<I", page, 0x998, LABEL_ADDR)
    return bytes(page)


def build_rodata_page(rodata: bytes) -> bytes:
    page = bytearray(RODATA_SIZE)
    page[: len(rodata)] = rodata
    page[LABEL_ADDR - RODATA_ADDR : LABEL_ADDR - RODATA_ADDR + len(LABEL_TEXT)] = (
        LABEL_TEXT
    )
    name = b"CounterTarget\x00"
    page[
        RESOURCE_NAME_ADDR - RODATA_ADDR : RESOURCE_NAME_ADDR - RODATA_ADDR + len(name)
    ] = name
    page[RESOURCE_EMPTY_ADDR - RODATA_ADDR] = 0
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the pinned addresses."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(ORIG_RODATA_ADDR, ORIG_RODATA_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            if address in THUMB_STUBS:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _normalise(self, value: int) -> int | str:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2334D8:
            self._log(address, r0, r1)
            after = self.case.get("cursor_after")
            if after is not None:
                work = r0 - SPRITE_GROUP_OFFSET
                uc.mem_write(
                    work + CURSOR_OFFSET,
                    struct.pack("<h", after),
                )
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("sprite_result", 1) & 0xFFFFFFFF
            )
        elif address == STUB_2BEF70:
            value = safe_read_s32(uc, r0 + 0x10) >> 12
            self._log(address, r0, value)
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_2BEF7C:
            value = safe_read_s32(uc, r0 + 0x0C) >> 12
            self._log(address, r0, value)
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_2313D4:
            x = s32(r1)
            y = s32(r2)
            self._log(address, r0, x, y)
            uc.mem_write(r0, struct.pack("<ff", float(x), float(y)))
        elif address == STUB_2B8B78:
            self._log(address, r0)
            if "mode_after_sound" in self.case:
                uc.mem_write(
                    WORK_ADDR + MODE_OFFSET,
                    bytes([self.case["mode_after_sound"] & 0xFF]),
                )
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("sound_result", 0x5B5B5B5B)
            )
        elif address == STUB_22CC38:
            self._log(address, self._normalise(r0), s32(r1))
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("resource_pointer", 0) & 0xFFFFFFFF
            )
        elif address == STUB_2BE7FC:
            fmt = read_c_string(uc, r1)
            first = read_c_string(uc, r2)
            second = read_c_string(uc, r3)
            self._log(address, fmt, first, second)
            payload = first + second
            uc.mem_write(r0, payload + b"\x00")
            uc.reg_write(arm.UC_ARM_REG_R0, len(payload))
        elif address == STUB_29F10C:
            self._log(address, read_c_string(uc, r0), r1)
        elif address == STUB_2337A0:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("list_index", 0) & 0xFFFFFFFF
            )
        elif address == STUB_29DCD4:
            self._log(address, r0, r1, r2, r3)
        elif address == STUB_2A0F68:
            self._log(address, r0 & 0xFF)
        elif address == STUB_233804:
            self._log(address, r0, r1, r2, s32(r3))
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("rows_result", 0x12345678)
            )
        elif address in (STUB_VIRTUAL, STUB_VIRTUAL_ALT):
            self._log(address, r0, r1)
            if self.case.get("swap_sub"):
                work = r1 - LIST_PANEL_OFFSET
                uc.mem_write(
                    work + SUB_OBJECT_OFFSET, struct.pack("<I", SUB_OBJECT_B)
                )
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, rodata: bytes, orig_rodata: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(WORK_ADDR, build_work(case))
        self.uc.mem_write(GLOBAL_ADDR, build_global_page())
        self.uc.mem_write(ORIG_RODATA_ADDR, orig_rodata)
        self.uc.mem_write(RODATA_ADDR, build_rodata_page(rodata))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
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

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_work = WORK_ADDR <= address < WORK_ADDR + WORK_SIZE
            if not (in_stack or in_work):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "work": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
            "global": bytes(self.uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
            "orig_rodata": bytes(
                self.uc.mem_read(ORIG_RODATA_ADDR, ORIG_RODATA_SIZE)
            ),
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
    for key in ("work", "global", "orig_rodata"):
        if orig[key] != cand[key]:
            # Report the first differing offset to keep the output readable.
            first = next(
                index
                for index, (left, right) in enumerate(zip(orig[key], cand[key]))
                if left != right
            )
            problems.append(f"{key} differs first at +0x{first:x}")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "sprite_result": 1,
        "mode": 0,
        "cursor": 0,
        "target_id": 0x1234,
        "row_count": 3,
        "list_index": 0,
        "resource_pointer": RESOURCE_NAME_ADDR,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- sprite gate: continue and early return
    cases.append(base_case("sprite gate zero (early return)", sprite_result=0, mode=1))
    cases.append(base_case("sprite gate non-zero (continue)", sprite_result=2, mode=1))

    # --- mode branches and zero/non-zero forms
    for mode in (0, 1, 2, 0x80, 0xFF):
        cases.append(base_case(f"mode 0x{mode:02x}", mode=mode))
    cases.append(
        base_case("mode mutated 1 -> 0 by sound helper", mode=1, mode_after_sound=0)
    )
    cases.append(
        base_case("mode mutated 0 -> 1 by sound helper", mode=0, mode_after_sound=1)
    )

    # --- resource lookup: string, empty string, null fallback
    cases.append(base_case("resource name", mode=1, resource_pointer=RESOURCE_NAME_ADDR))
    cases.append(base_case("resource empty", mode=1, resource_pointer=RESOURCE_EMPTY_ADDR))
    cases.append(base_case("resource null (fallback)", mode=1, resource_pointer=0))
    cases.append(
        base_case(
            "resource null with high target id",
            mode=1,
            resource_pointer=0,
            target_id=0x7FFFFFFF,
        )
    )
    cases.append(
        base_case(
            "resource null with negative target id",
            mode=1,
            resource_pointer=0,
            target_id=0x80000000,
        )
    )

    # --- cursor values and the post-helper re-read
    for cursor in (0, 1, 7, -1, 0x7FFF, -0x8000):
        cases.append(base_case(f"cursor {cursor} mode 0", cursor=cursor, mode=0))
        cases.append(base_case(f"cursor {cursor} mode 1", cursor=cursor, mode=1))
    cases.append(
        base_case("cursor re-read 0 -> 3", cursor=0, cursor_after=3, mode=1)
    )
    cases.append(
        base_case("cursor re-read 6 -> -1", cursor=6, cursor_after=-1, mode=0)
    )

    # --- list index: ordinary, boundary and 32-bit wrap
    for index in (0, 1, 0x7FF, 0xFFFFFFFF):
        cases.append(
            base_case(f"list index 0x{index & 0xFFFFFFFF:08x}", mode=0, list_index=index)
        )

    # --- signed row-count clamp boundaries
    for count in (-1, 0, 9, 10, 11, 0x7FFFFFFF, 0x80000000):
        cases.append(
            base_case(
                f"row count {s32(count)}",
                mode=1,
                row_count=count,
                resource_pointer=0,
            )
        )

    # --- refresh virtual pointer swap (reload before flag update)
    for mode in (0, 1):
        cases.append(base_case(f"sub object swapped mode {mode}", mode=mode, swap_sub=True))
        cases.append(
            base_case(
                f"sub object swapped with null resource mode {mode}",
                mode=mode,
                swap_sub=True,
                resource_pointer=0,
            )
        )

    return cases


def run_case_set(orig_code, cand_code, rodata, orig_rodata, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, rodata, orig_rodata, case)
        cand = Runner().run(cand_code, rodata, orig_rodata, case)
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
    print("Testing shop_func_003a8b14 (0x003a8b14)...")
    orig_code = get_orig_bytes()
    orig_rodata = get_orig_rodata_page()
    cand_code, cand_rodata = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        f"rodata {len(cand_rodata)} B (relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cand_rodata, orig_rodata, cases)

    print("\nNegative controls:")
    for name, old, new in (
        (
            "cursor_record_stride",
            "constexpr u32 kCursorRecordStride = 140;",
            "constexpr u32 kCursorRecordStride = 144;",
        ),
        (
            "sound_request_nonzero",
            "constexpr u32 kSoundModeNonZero = 0x46;",
            "constexpr u32 kSoundModeNonZero = 0x47;",
        ),
        (
            "row_count_clamp",
            "constexpr u32 kMaxRowCount = 10;",
            "constexpr u32 kMaxRowCount = 9;",
        ),
        (
            "cursor_reload",
            "const s16 cursor = *reinterpret_cast<const s16*>(work + kCursorOffset);",
            "const s16 cursor = initial_cursor;",
        ),
    ):
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, cand_rodata, orig_rodata, case)
            bad = Runner().run(mutant_code, mutant_rodata, orig_rodata, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
