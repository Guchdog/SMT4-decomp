#!/usr/bin/env python3
"""Differential test for camp_func_003abd08 (0x003abd08) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the camp_func_003abd08 body,
resolves its twelve direct calls to deterministic stubs at the original call
targets, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log: every register argument, every architected stack word
    (2 for 0x231D60, 2 for 0x2B6F74, 5 for 0x230C80) and the S0-S4 bit patterns
    forwarded to 0x2BE744;
  * the text string behind 0x2BE744's r3 pointer, the `"%8d"` format string read
    by 0x2BE7FC and the formatted buffer contents;
  * full observable memory (ctx, work, anchor records, text page, rodata) and
    any emulated write outside the private stack.

Coverage: flag 0 / 1 / 2 / 0xFFFFFFFF; index 0..3 (slot addressing); 0x262EDC
returning 0, 1, 2 and 0xFFFFFFFF; 0x2890D0 returning 0, 1, 0x7FFF, 0x8000,
0xFFFF and 0x12345678 (s16 truncation); u16 ids including 0xFFFF/0x8000; signed
value words; arg5 values covering 0x100-arg5 wrap, 0x100, 0x1F, 0x20 and
0xFFFFFFFF; signed anchor-coordinate boundaries for every lookup record; rect
floats that flow through 0x231D4C into the bar coordinates (including negative
and fractional offsets); the signed mode byte; and a case where 0x22D994 writes
a new id into the slot so the early id (0x2890D0) and the reloaded id
(0x262EDC) are distinguishable. Negative controls mutate the bar-helper id, the
plain text label, the slot id offset and the value offset; each must be
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
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_003abd08"

FUNC_ADDR = 0x003ABD08
FUNC_SIZE = 668

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000
CTX_ADDR = 0x00710000
CTX_SIZE = 0x00010000
WORK_ADDR = 0x00720000
WORK_SIZE = 0x00010000
ANCHOR_ADDR = 0x00730000
ANCHOR_SIZE = 0x00010000
TEXT_ADDR = 0x00740000
TEXT_SIZE = 0x00010000
RODATA_ADDR = 0x00750000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; stubs live at the same addresses so both the
# original bytes and the relocated candidate resolve to them.
STUB_2BF6C8 = 0x002BF6C8  # layout-record lookup
STUB_22D994 = 0x0022D994  # selected-layout notification
STUB_262EDC = 0x00262EDC  # "has items" predicate
STUB_2BE744 = 0x002BE744  # rect-relative text draw
STUB_231D60 = 0x00231D60  # map/row helper (two float stack words)
STUB_231D4C = 0x00231D4C  # two-word copy helper
STUB_2890D0 = 0x002890D0  # u16 id query
STUB_2B6F74 = 0x002B6F74  # demon-bars draw
STUB_2BE7FC = 0x002BE7FC  # vararg text formatter (Thumb)
STUB_230C80 = 0x00230C80  # positioned text submit

# 0x2BE7FC is Thumb in the pinned binary (the original reaches it with `blx`);
# a real linker converts the candidate's R_ARM_CALL into BLX as well.
THUMB_STUBS = {STUB_2BE7FC}

STUB_NAMES = {
    STUB_2BF6C8: "camp_func_002bf6c8",
    STUB_22D994: "ui_func_0022d994",
    STUB_262EDC: "camp_func_00262edc",
    STUB_2BE744: "func_002be744",
    STUB_231D60: "camp_func_00231d60",
    STUB_231D4C: "func_00231d4c",
    STUB_2890D0: "camp_func_002890d0",
    STUB_2B6F74: "camp_func_002b6f74",
    STUB_2BE7FC: "ui_func_002be7fc",
    STUB_230C80: "func_00230c80",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_2BF6C8: 0,
    STUB_22D994: 0,
    STUB_262EDC: 0,
    STUB_2BE744: 0,
    STUB_231D60: 2,   # arg5 bits, 1.0 bits
    STUB_231D4C: 0,
    STUB_2890D0: 0,
    STUB_2B6F74: 2,   # 0, 0
    STUB_2BE7FC: 0,
    STUB_230C80: 5,   # 0, 7, 0xFFFFFFFF, arg5, text pointer
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
FLOAT_ARGS = {
    "s0": arm.UC_ARM_REG_S0,
    "s1": arm.UC_ARM_REG_S1,
    "s2": arm.UC_ARM_REG_S2,
    "s3": arm.UC_ARM_REG_S3,
    "s4": arm.UC_ARM_REG_S4,
}

# ctx layout proven by the ARM.
CTX_RECT_OFFSET = 0xC8       # four floats read by 0x2BE744 / copied by 0x231D4C
CTX_MODE_BYTE = 0x56D        # ldrsb mode selector, forwarded when flag != 0
CTX_SLOT_BASE = 0x5A8        # 0x20-byte records
CTX_ID_IN_SLOT = 0x04        # u16  -> absolute 0x5AC
CTX_VALUE_IN_SLOT = 0x0C     # s32  -> absolute 0x5B4
CTX_TEXT_IN_SLOT = 0x20      # u32  -> absolute 0x5C8

# 0x2BF6C8 lookup keys mapped to distinct anchor records.
RECORD_PLAIN_LAYOUT = 0x40E
RECORD_SELECTED_LAYOUT = 0x42F
RECORD_FRAME_PLAIN = 0x4CE
RECORD_FRAME_SELECTED = 0x4E0
RECORD_BAR_PLAIN = 0x4CD
RECORD_BAR_SELECTED = 0x476
RECORD_TEXT_PLAIN = 0x4DE
RECORD_TEXT_SELECTED = 0x4F0
RECORD_UNKNOWN = 0xF00

RECORD_OFFSETS = {
    RECORD_PLAIN_LAYOUT: 0x100,
    RECORD_SELECTED_LAYOUT: 0x200,
    RECORD_FRAME_PLAIN: 0x300,
    RECORD_FRAME_SELECTED: 0x400,
    RECORD_BAR_PLAIN: 0x500,
    RECORD_BAR_SELECTED: 0x600,
    RECORD_TEXT_PLAIN: 0x700,
    RECORD_TEXT_SELECTED: 0x800,
}

DEFAULT_RECORD_XY = {
    RECORD_PLAIN_LAYOUT: (0x0100, 0x0200),
    RECORD_SELECTED_LAYOUT: (-0x0100, -0x0200),
    RECORD_FRAME_PLAIN: (0x0010, 0x0020),
    RECORD_FRAME_SELECTED: (-0x0030, -0x0040),
    RECORD_BAR_PLAIN: (0x0050, -0x0060),
    RECORD_BAR_SELECTED: (-0x0070, 0x0080),
    RECORD_TEXT_PLAIN: (0x0090, 0x00A0),
    RECORD_TEXT_SELECTED: (-0x00B0, -0x00C0),
}

DEFAULT_RECT = (6.5, -2.25, 1.75, 0.5)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


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
        if "003abd08" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_003abd08 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    rodata_addends: list[int] = []
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
                    raise RuntimeError(f"unaligned Thumb call target 0x{target:08x}")
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
        elif rel.relocation_type == 2:  # R_ARM_ABS32 into .rodata.str1.1
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            rodata_addends.append(addend)
            struct.pack_into("<I", code, rel.offset, RODATA_ADDR + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )

    rodata = elf_sections(obj_file).get(".rodata.str1.1", b"")
    if not rodata_addends:
        raise RuntimeError("no rodata reference found in the candidate")
    for addend in rodata_addends:
        if rodata[addend : addend + 4] != b"%8d\x00":
            raise RuntimeError("could not locate the '%8d' format string in .rodata")
    return bytes(code), rodata


def compile_candidate_baseline() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
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
def build_ctx(case: dict) -> bytes:
    page = bytearray(CTX_SIZE)
    rect = case.get("rect", DEFAULT_RECT)
    struct.pack_into("<4f", page, CTX_RECT_OFFSET, *rect)
    page[CTX_MODE_BYTE] = case.get("mode_byte", 0x02) & 0xFF

    index = case.get("index", 0)
    slot = CTX_SLOT_BASE + index * 0x20
    struct.pack_into("<H", page, slot + CTX_ID_IN_SLOT, case.get("id", 0x1234) & 0xFFFF)
    struct.pack_into(
        "<i", page, slot + CTX_VALUE_IN_SLOT, case.get("value", 0x1234)
    )
    struct.pack_into(
        "<I", page, slot + CTX_TEXT_IN_SLOT, TEXT_ADDR + 0x100 + index * 0x20
    )
    return bytes(page)


def build_work() -> bytes:
    page = bytearray(WORK_SIZE)
    # Distinct sentinels at the two layout-key addresses so the selector logs
    # are exact even if a candidate reuses the wrong key.
    page[RECORD_PLAIN_LAYOUT] = 0x0E
    page[RECORD_SELECTED_LAYOUT] = 0x2F
    return bytes(page)


def build_anchor(case: dict) -> bytes:
    page = bytearray(ANCHOR_SIZE)
    overrides = case.get("records", {})
    for key, offset in RECORD_OFFSETS.items():
        for i in range(0x20):
            page[offset + i] = (0xA5 ^ (key + i)) & 0xFF
        x, y = overrides.get(key, DEFAULT_RECORD_XY[key])
        struct.pack_into("<h", page, offset + 8, x)
        struct.pack_into("<h", page, offset + 0xA, y)
    return bytes(page)


def build_text(case: dict) -> bytes:
    page = bytearray(TEXT_SIZE)
    for index in range(4):
        label = case.get("text_labels", {}).get(index, f"row{index}")
        blob = label.encode("ascii") + b"\x00"
        off = 0x100 + index * 0x20
        page[off : off + len(blob)] = blob
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


R0_HOOK = STUB_2BF6C8


class BD08Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # The original pushes d8 and both bodies use VFP; grant CP10/CP11
        # access and set FPEXC.EN before mapping/execution.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(ANCHOR_ADDR, ANCHOR_SIZE)
        self.uc.mem_map(TEXT_ADDR, TEXT_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            if address in THUMB_STUBS:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))  # thumb bx lr
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.format_dsts: list = []
        self.format_payloads: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, *args, floats=()) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]),
             floats)
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _record_for_key(self, key: int) -> int:
        if WORK_ADDR <= key < WORK_ADDR + WORK_SIZE:
            relative = key - WORK_ADDR
        else:
            relative = key
        return ANCHOR_ADDR + RECORD_OFFSETS.get(relative, RECORD_UNKNOWN)

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2BF6C8:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, self._record_for_key(r1))
        elif address == STUB_22D994:
            self._log(address, r0, r1, r2, r3)
            if self.case.get("diverge_ids"):
                index = self.case.get("index", 0)
                slot = CTX_ADDR + CTX_SLOT_BASE + index * 0x20 + CTX_ID_IN_SLOT
                uc.mem_write(slot, struct.pack("<H", self.case.get("new_id", 0x4321)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2200D994)
        elif address == STUB_262EDC:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("has_items", 0) & 0xFFFFFFFF
            )
        elif address == STUB_2BE744:
            floats = tuple(
                uc.reg_read(register) for register in FLOAT_ARGS.values()
            )
            text = read_c_string(uc, r3)
            self._log(address, r0, r1, r2, r3, text, floats=floats)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2200BE44)
        elif address == STUB_231D60:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2200D160)
        elif address == STUB_231D4C:
            self._log(address, r0, r1)
            uc.mem_write(r1, bytes(uc.mem_read(r0, 8)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2200D14C)
        elif address == STUB_2890D0:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("has_id", 0) & 0xFFFFFFFF
            )
        elif address == STUB_2B6F74:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x22006F74)
        elif address == STUB_2BE7FC:
            fmt = read_c_string(uc, r1)
            self._log(address, r0, fmt, r2)
            value = r2 - (1 << 32) if r2 & 0x80000000 else r2
            payload = str(value).encode("ascii")[:0x1F]
            uc.mem_write(r0, payload + b"\x00")
            self.format_dsts.append(r0)
            self.format_payloads.append(payload)
            uc.reg_write(arm.UC_ARM_REG_R0, len(payload))
        elif address == STUB_230C80:
            stack = self._stack_words(STACK_ARGS[address])
            text = read_c_string(uc, stack[4])
            self.call_log.append(
                (STUB_NAMES[address], (r0, r1, r2, r3) + stack + (text,), ())
            )
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2200C080)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args, floats in log:
            out = []
            for arg in args:
                if isinstance(arg, int) and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out), floats))
        return normalised

    def run(self, code: bytes, rodata: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.format_dsts = []
        self.format_payloads = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(CTX_ADDR, build_ctx(case))
        self.uc.mem_write(WORK_ADDR, build_work())
        self.uc.mem_write(ANCHOR_ADDR, build_anchor(case))
        self.uc.mem_write(TEXT_ADDR, build_text(case))
        self.uc.mem_write(RODATA_ADDR, rodata)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        # Fifth argument is passed on the stack at the caller's SP.
        self.uc.mem_write(ENTRY_SP, struct.pack("<I", case.get("arg5", 0) & 0xFFFFFFFF))
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, WORK_ADDR)
        self.uc.reg_write(
            arm.UC_ARM_REG_R2, case.get("index", 0) & 0xFFFFFFFF
        )
        self.uc.reg_write(
            arm.UC_ARM_REG_R3, case.get("flag", 0) & 0xFFFFFFFF
        )
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        format_buffers = [
            bytes(self.uc.mem_read(dst, 0x20)) for dst in self.format_dsts
        ]

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not in_stack:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "format_payloads": self.format_payloads,
            "format_buffers": format_buffers,
            "fixtures": {
                "ctx": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
                "work": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
                "anchor": bytes(self.uc.mem_read(ANCHOR_ADDR, ANCHOR_SIZE)),
                "text": bytes(self.uc.mem_read(TEXT_ADDR, TEXT_SIZE)),
                "rodata": bytes(self.uc.mem_read(RODATA_ADDR, RODATA_SIZE)),
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
    if orig["format_payloads"] != cand["format_payloads"]:
        problems.append(
            "format payloads:\n    orig="
            + repr(orig["format_payloads"])
            + "\n    cand="
            + repr(cand["format_payloads"])
        )
    for index, (left, right) in enumerate(
        zip(orig["format_buffers"], cand["format_buffers"])
    ):
        if left != right:
            problems.append(
                f"format buffer {index}:\n    orig={left!r}\n    cand={right!r}"
            )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "flag": 0,
        "index": 0,
        "arg5": 0x1F,
        "id": 0x1234,
        "value": 0x1234,
        "mode_byte": 0x02,
        "has_items": 0,
        "has_id": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- flag branch: plain vs selected layout/label/constant sets
    cases.append(base_case("flag 0 baseline"))
    cases.append(base_case("flag 1 selected", flag=1))
    cases.append(base_case("flag 2 treated as selected", flag=2))
    cases.append(base_case("flag 0xFFFFFFFF", flag=-1))

    # --- slot addressing: index 0..3 with both branches
    for index in (1, 2, 3):
        cases.append(base_case(f"index {index} plain", index=index))
        cases.append(base_case(f"index {index} selected", index=index, flag=1))

    # --- arg5: scale wrap, boundaries and forwarded words
    for arg5 in (
        0,
        1,
        0x1F,
        0x20,
        0xFF,
        0x100,
        0x101,
        0xFFFFFF00,
        0x7FFFFFFF,
        0x80000000,
        0xFFFFFFFF,
    ):
        cases.append(base_case(f"arg5 0x{arg5:08x} plain", arg5=arg5))
        cases.append(base_case(f"arg5 0x{arg5:08x} selected", arg5=arg5, flag=1))

    # --- 0x262EDC predicate: zero, non-zero and all-ones
    for has_items in (0, 1, 2, 0xFFFFFFFF):
        cases.append(base_case(f"has_items {has_items}", has_items=has_items))
        cases.append(
            base_case(f"has_items {has_items} selected", has_items=has_items, flag=1)
        )

    # --- 0x2890D0 result: s16 truncation boundaries
    for has_id in (0, 1, 0x7FFF, 0x8000, 0xFFFF, 0x12345678):
        cases.append(base_case(f"has_id 0x{has_id:08x}", has_id=has_id))
        cases.append(
            base_case(f"has_id 0x{has_id:08x} selected", has_id=has_id, flag=1)
        )

    # --- u16 ids: zero-extension into the two helpers
    for ident in (0x0000, 0x0001, 0x7FFF, 0x8000, 0xFFFF):
        cases.append(base_case(f"id 0x{ident:04x}", id=ident))
        cases.append(base_case(f"id 0x{ident:04x} selected", id=ident, flag=1))

    # --- value word formatted by 0x2BE7FC
    for value in (0, -1, 1, 0x7FFFFFFF, -0x80000000, 0x12345678):
        cases.append(base_case(f"value {value}", value=value))
        cases.append(base_case(f"value {value} selected", value=value, flag=1))

    # --- signed anchor-coordinate boundaries per lookup record
    for key in RECORD_OFFSETS:
        for x, y in (
            (-0x8000, -0x8000),
            (0x7FFF, 0x7FFF),
            (0x7FFF, -0x8000),
            (-0x8000, 0x7FFF),
            (0x0000, 0x0000),
            (-1, 1),
        ):
            cases.append(
                base_case(
                    f"record 0x{key:03x} {x}/{y}",
                    flag=1 if key in (RECORD_SELECTED_LAYOUT,
                                      RECORD_FRAME_SELECTED,
                                      RECORD_BAR_SELECTED,
                                      RECORD_TEXT_SELECTED) else 0,
                    records={key: (x, y)},
                )
            )

    # --- rect floats copied by 0x231D4C into the bar coordinates
    for rect in (
        (0.0, 0.0, 0.0, 0.0),
        (0.5, -0.5, 0.25, -0.25),
        (-3.75, 2.5, -0.25, 4.0),
        (127.9, -128.1, 1.5, 2.5),
        (0.999, -0.999, 0.0, 0.0),
    ):
        cases.append(base_case(f"rect {rect} plain", rect=rect))
        cases.append(base_case(f"rect {rect} selected", rect=rect, flag=1))

    # --- signed mode byte (only read when flag != 0)
    for mode in (0x00, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"mode byte 0x{mode:02x}", mode_byte=mode, flag=1))

    # --- the id reload is observable when 0x22D994 rewrites the slot
    cases.append(
        base_case(
            "id reload after 0x22D994",
            flag=1,
            diverge_ids=True,
            new_id=0xABCD,
            id=0x1111,
        )
    )
    cases.append(
        base_case(
            "id reload after 0x22D994 with items",
            flag=1,
            diverge_ids=True,
            new_id=0x0001,
            id=0x2222,
            has_items=1,
        )
    )

    return cases


def run_case_set(orig_code, cand_code, rodata, cases) -> int:
    passed = 0
    for case in cases:
        orig = BD08Runner().run(orig_code, rodata, case)
        cand = BD08Runner().run(cand_code, rodata, case)
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
    print("Testing camp_func_003abd08 (0x003abd08)...")
    orig_code = get_orig_bytes()
    cand_code, cand_rodata = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        f"rodata {len(cand_rodata)} B (relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cand_rodata, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("bar_helper_id", "constexpr u32 kBarHelperSelected = 0x4DF;",
         "constexpr u32 kBarHelperSelected = 0x4DE;"),
        ("plain_text_label", "constexpr u32 kTextLabelPlain = 0x4DE;",
         "constexpr u32 kTextLabelPlain = 0x4DF;"),
        ("row_id_offset", "constexpr u32 kRowIdOffset = 0x5AC;",
         "constexpr u32 kRowIdOffset = 0x5AA;"),
        ("row_value_offset", "constexpr u32 kRowValueOffset = 0x5B4;",
         "constexpr u32 kRowValueOffset = 0x5B8;"),
    ):
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = BD08Runner().run(orig_code, cand_rodata, case)
            bad = BD08Runner().run(mutant_code, mutant_rodata, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
