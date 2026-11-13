#!/usr/bin/env python3
"""Differential test for battle_func_003aa014 (0x003aa014) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the battle_func_003aa014 body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every register argument and the architected stack
    arguments of each helper (including the five draw-call stack words);
  * the textual bytes written by each 0x2BE7FC format stub, its destination and
    the format string read from the passed pointer;
  * ctx, sb, anchor-table, record and rodata memory (must be unmodified);
  * any emulated write outside the private stack.

Coverage: flag = 0 and every non-zero form, each of the three 0x2B087C lookups
null and non-null, both 0x2BF6C8 record selections per branch, signed s16
coordinate boundaries and wrap-around frame counters, and the full 16-bit id
mask. Negative controls mutate the forwarded draw constant, a record field
offset, and one label-id selection; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_003aa014"

FUNC_ADDR = 0x003AA014
FUNC_SIZE = 592

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000
CTX_ADDR = 0x00710000
CTX_SIZE = 0x00010000
SB_ADDR = 0x00720000
SB_SIZE = 0x00010000
ANCHOR_ADDR = 0x00730000
ANCHOR_SIZE = 0x00010000
RECORD_ADDR = 0x00740000
RECORD_SIZE = 0x00010000
RODATA_ADDR = 0x00750000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_2BF6C8 = 0x002BF6C8
STUB_22D994 = 0x0022D994
STUB_22DE40 = 0x0022DE40
STUB_22DD28 = 0x0022DD28
STUB_22DC40 = 0x0022DC40
STUB_2B087C = 0x002B087C
STUB_22DB5C = 0x0022DB5C
STUB_2BE7FC = 0x002BE7FC
STUB_230C80 = 0x00230C80

# 0x2BE7FC is Thumb code in the pinned binary (the original reaches it with
# `blx`). A real linker turns the candidate's R_ARM_CALL into BLX as well.
THUMB_STUBS = {STUB_2BE7FC}

STUB_NAMES = {
    STUB_2BF6C8: "camp_func_002bf6c8",
    STUB_22D994: "ui_func_0022d994",
    STUB_22DE40: "camp_func_0022de40",
    STUB_22DD28: "script_vm_func_0022dd28",
    STUB_22DC40: "script_vm_func_0022dc40",
    STUB_2B087C: "battle_func_002b087c",
    STUB_22DB5C: "ui_func_0022db5c",
    STUB_2BE7FC: "ui_func_002be7fc",
    STUB_230C80: "func_00230c80",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_2BF6C8: 0,
    STUB_22D994: 0,
    STUB_22DE40: 2,   # flag, frame
    STUB_22DD28: 1,   # frame
    STUB_22DC40: 1,   # frame
    STUB_2B087C: 0,
    STUB_22DB5C: 2,   # frame, -1
    STUB_2BE7FC: 0,
    STUB_230C80: 5,   # 0, 7, opaque constant, frame, text pointer
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

# Anchor record placement inside the anchor page. The first lookup passes a
# pointer (sb + 0x40E / 0x42F); the label lookups pass small ids.
ANCHOR_LAYOUT_PLAIN = 0x100
ANCHOR_LAYOUT_SELECTED = 0x200
ANCHOR_LABEL_PLAIN_FIRST = 0x300
ANCHOR_LABEL_SELECTED_FIRST = 0x400
ANCHOR_LABEL_PLAIN_SECOND = 0x500
ANCHOR_LABEL_SELECTED_SECOND = 0x600
ANCHOR_UNKNOWN = 0x780

ANCHOR_KEY_PLAIN = 0x40E
ANCHOR_KEY_SELECTED = 0x42F
ANCHOR_IDS = {
    0x48F: ANCHOR_LABEL_PLAIN_FIRST,
    0x49D: ANCHOR_LABEL_SELECTED_FIRST,
    0x493: ANCHOR_LABEL_PLAIN_SECOND,
    0x4A1: ANCHOR_LABEL_SELECTED_SECOND,
}

RECORD_STRIDE = 0x40
LOOKUP_COUNT = 3


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
        if "003aa014" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"battle_func_003aa014 not found in {obj_file}: {sorted(funcs)}"
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
                    | (((offset >> 2) & 0x00FFFFFF))
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
            struct.pack_into("<I", code, rel.offset, RODATA_ADDR + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )

    rodata = elf_sections(obj_file).get(".rodata.str1.1", b"")
    # The only rodata reference in this function is the "%4d" format string.
    if rodata[0xB5 : 0xB9] != b"%4d\x00":
        raise RuntimeError("could not locate the '%4d' format string in .rodata")
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
DEFAULT_ANCHORS = {
    ANCHOR_LAYOUT_PLAIN: (0x0123, -0x0045),
    ANCHOR_LAYOUT_SELECTED: (-0x0200, 0x0064),
    ANCHOR_LABEL_PLAIN_FIRST: (0x0010, 0x0020),
    ANCHOR_LABEL_SELECTED_FIRST: (-0x0030, -0x0040),
    ANCHOR_LABEL_PLAIN_SECOND: (0x0050, -0x0060),
    ANCHOR_LABEL_SELECTED_SECOND: (-0x0070, 0x0080),
    ANCHOR_UNKNOWN: (0x7F7F, -0x7F7F),
}


def build_anchor(case: dict) -> bytes:
    page = bytearray(ANCHOR_SIZE)
    for offset, (x, y) in DEFAULT_ANCHORS.items():
        struct.pack_into("<h", page, offset + 8, x)
        struct.pack_into("<h", page, offset + 0xA, y)
        # Unrelated filler that must stay untouched.
        struct.pack_into("<I", page, offset, 0xA5A50000 | offset)
    for key, field in (
        ("anchor_layout_plain", ANCHOR_LAYOUT_PLAIN),
        ("anchor_layout_selected", ANCHOR_LAYOUT_SELECTED),
        ("anchor_label_plain_first", ANCHOR_LABEL_PLAIN_FIRST),
        ("anchor_label_selected_first", ANCHOR_LABEL_SELECTED_FIRST),
        ("anchor_label_plain_second", ANCHOR_LABEL_PLAIN_SECOND),
        ("anchor_label_selected_second", ANCHOR_LABEL_SELECTED_SECOND),
    ):
        if key in case:
            x, y = case[key]
            struct.pack_into("<h", page, field + 8, x)
            struct.pack_into("<h", page, field + 0xA, y)
    return bytes(page)


def build_record(case: dict) -> bytes:
    page = bytearray(RECORD_SIZE)
    records = (
        # (byte +2, word +4, word +8)
        (case.get("a_byte", 0x5A), case.get("a4", 0x11111111),
         case.get("a8", 0x22222222)),
        (case.get("b_byte", 0x5B), case.get("b4", 0x33333333),
         case.get("b8", 0x44444444)),
        (case.get("c_byte", 0x5C), case.get("c4", 0x55555555),
         case.get("c8", 0x66666666)),
    )
    for index, (byte, word4, word8) in enumerate(records):
        base = (index + 1) * RECORD_STRIDE
        page[base + 2] = byte & 0xFF
        struct.pack_into("<I", page, base + 4, word4 & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 8, word8 & 0xFFFFFFFF)
        page[base + 0] = 0xC0 | index
        page[base + 0xC] = 0xE0 | index
    return bytes(page)


def build_ctx(case: dict) -> bytes:
    page = bytearray(CTX_SIZE)
    struct.pack_into("<I", page, 0x594, case.get("frame", 0x00001234) & 0xFFFFFFFF)
    page[0x56D] = case.get("mode_byte", 0x02) & 0xFF
    return bytes(page)


def build_sb(case: dict) -> bytes:
    page = bytearray(SB_SIZE)
    # Distinct sentinels at every layout offset so the selector logs are exact.
    for offset in (ANCHOR_KEY_PLAIN, ANCHOR_KEY_SELECTED):
        page[offset] = (offset ^ 0x5A) & 0xFF
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class AA014Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(SB_ADDR, SB_SIZE)
        self.uc.mem_map(ANCHOR_ADDR, ANCHOR_SIZE)
        self.uc.mem_map(RECORD_ADDR, RECORD_SIZE)
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
        self.lookup_index = 0
        self.draw_index = 0
        self.format_dsts: list = []
        self.format_payloads: list = []
        self.case: dict = {}
        self.record_page = b""

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _anchor_for(self, key: int) -> int:
        if SB_ADDR <= key < SB_ADDR + SB_SIZE:
            offset = key - SB_ADDR
            if offset == ANCHOR_KEY_PLAIN:
                return ANCHOR_ADDR + ANCHOR_LAYOUT_PLAIN
            if offset == ANCHOR_KEY_SELECTED:
                return ANCHOR_ADDR + ANCHOR_LAYOUT_SELECTED
            return ANCHOR_ADDR + ANCHOR_UNKNOWN
        return ANCHOR_ADDR + ANCHOR_IDS.get(key, ANCHOR_UNKNOWN)

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2BF6C8:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, self._anchor_for(r1))
        elif address == STUB_22D994:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2200D994)
        elif address == STUB_22DE40:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2200DE40)
        elif address == STUB_22DD28:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2200DD28)
        elif address == STUB_22DC40:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2200DC40)
        elif address == STUB_2B087C:
            self._log(address, r0)
            self.lookup_index += 1
            prefix = ("first", "second", "third")[min(self.lookup_index, 3) - 1]
            if self.case.get(f"null_{prefix}", False):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(
                    arm.UC_ARM_REG_R0,
                    RECORD_ADDR + self.lookup_index * RECORD_STRIDE,
                )
        elif address == STUB_22DB5C:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2200DB5C)
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
            self._log(address, r0, r1, r2, r3)
            self.draw_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, 0xA5A50000 | self.draw_index)
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

    def run(self, code: bytes, rodata: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.lookup_index = 0
        self.draw_index = 0
        self.format_dsts = []
        self.format_payloads = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(CTX_ADDR, build_ctx(case))
        self.uc.mem_write(SB_ADDR, build_sb(case))
        anchor = build_anchor(case)
        self.uc.mem_write(ANCHOR_ADDR, anchor)
        record = build_record(case)
        self.record_page = record
        self.uc.mem_write(RECORD_ADDR, record)
        self.uc.mem_write(RODATA_ADDR, rodata)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, SB_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("flag", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("id", 0x1234ABCD) & 0xFFFFFFFF)
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
                "sb": bytes(self.uc.mem_read(SB_ADDR, SB_SIZE)),
                "anchor": bytes(self.uc.mem_read(ANCHOR_ADDR, ANCHOR_SIZE)),
                "record": bytes(self.uc.mem_read(RECORD_ADDR, RECORD_SIZE)),
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
        "id": 0x1234ABCD,
        "frame": 0x00001234,
        "mode_byte": 0x02,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- flag branch: plain vs selected layout/label/constant sets
    cases.append(base_case("flag 0 baseline"))
    cases.append(base_case("flag 1 selected", flag=1))
    cases.append(base_case("flag 2 treated as non-zero", flag=2))
    cases.append(base_case("flag 0xFFFFFFFF treated as non-zero", flag=-1))

    # --- the three 0x2B087C lookups: null and non-null combinations
    cases.append(base_case("first lookup null", null_first=True, flag=1))
    cases.append(base_case("second lookup null", null_second=True))
    cases.append(base_case("third lookup null", null_third=True, flag=1))
    cases.append(base_case("second and third lookups null", null_second=True,
                           null_third=True))
    cases.append(base_case("all lookups null", null_first=True,
                           null_second=True, null_third=True, flag=1))

    # --- signed coordinate boundaries and wrap-around sums
    for x, y in (
        (-0x8000, -0x8000),
        (0x7FFF, 0x7FFF),
        (0x7FFF, -0x8000),
        (-0x8000, 0x7FFF),
        (0x0000, 0x0000),
        (-1, 1),
    ):
        cases.append(
            base_case(f"layout boundary {x}/{y}", flag=0,
                      anchor_layout_plain=(x, y))
        )
        cases.append(
            base_case(f"selected layout boundary {x}/{y}", flag=1,
                      anchor_layout_selected=(x, y))
        )
    for key in (
        "anchor_label_plain_first",
        "anchor_label_selected_first",
        "anchor_label_plain_second",
        "anchor_label_selected_second",
    ):
        cases.append(
            base_case(f"{key} boundary", flag=1 if "selected" in key else 0,
                      **{key: (-0x8000, 0x7FFF)})
        )
        cases.append(
            base_case(f"{key} maximum", flag=1 if "selected" in key else 0,
                      **{key: (0x7FFF, -0x8000)})
        )

    # --- frame counter: plain, incremented, and 32-bit wrap
    for frame, flag in (
        (0x00000000, 0),
        (0x00000000, 1),
        (0xFFFFFFFF, 0),
        (0xFFFFFFFF, 1),
        (0x7FFFFFFF, 1),
        (0x80000000, 0),
        (0x80000000, 1),
    ):
        cases.append(
            base_case(f"frame 0x{frame:08x} flag {flag}", frame=frame, flag=flag)
        )

    # --- mode byte sign extension (only read when flag != 0)
    for mode in (0x00, 0x7F, 0x80, 0xFF):
        cases.append(
            base_case(f"mode byte 0x{mode:02x}", mode_byte=mode, flag=1)
        )

    # --- id mask: 16-bit truncation regardless of sign
    for ident in (0x00000000, 0x0000FFFF, 0x1234ABCD, 0xFFFFFFFF, 0x7FFF8000,
                  0x00010000, 0x00008000):
        cases.append(base_case(f"id 0x{ident:08x}", id=ident))
        cases.append(base_case(f"id 0x{ident:08x} flag 1", id=ident, flag=1))

    # --- record field values: distinct per record, signed and zero
    for b4, c8 in (
        (0x7FFFFFFF, 0x80000000),
        (0x00000000, 0xFFFFFFFF),
        (0x0000FFFF, 0xFFFF0000),
    ):
        cases.append(base_case(f"values b4=0x{b4:08x} c8=0x{c8:08x}",
                               b4=b4, c8=c8, flag=1))
    cases.append(base_case("record flag byte 0xFF", a_byte=0xFF))
    cases.append(base_case("record flag byte 0x80", a_byte=0x80))

    return cases


def run_case_set(orig_code, cand_code, rodata, cases) -> int:
    passed = 0
    for case in cases:
        orig = AA014Runner().run(orig_code, rodata, case)
        cand = AA014Runner().run(cand_code, rodata, case)
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
    print("Testing battle_func_003aa014 (0x003aa014)...")
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
        ("draw_constant", "constexpr u32 kOpaqueFirst = 0xFBEB39FF;",
         "constexpr u32 kOpaqueFirst = 0xFBEB39FE;"),
        ("record_first_word_offset",
         "constexpr u32 kRecordFirstWordOffset = 4;",
         "constexpr u32 kRecordFirstWordOffset = 8;"),
        ("label_plain_first", "constexpr u16 kLabelIdPlainFirst = 0x48F;",
         "constexpr u16 kLabelIdPlainFirst = 0x481;"),
    ):
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = AA014Runner().run(orig_code, cand_rodata, case)
            bad = AA014Runner().run(mutant_code, mutant_rodata, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
