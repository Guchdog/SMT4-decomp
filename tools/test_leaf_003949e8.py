#!/usr/bin/env python3
"""Differential test for engine_func_003949e8 (0x003949e8) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts engine_func_003949e8, resolves
its direct calls to deterministic stubs at the original call-target addresses,
and runs the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11 and s16-s31;
  * the ordered event log: the 0x002C583C guard call, every 0x002BE7FC format
    call (destination, format bytes and table-entry pointer), every 0x002AA7F4
    comparison (both strings), the 0x00293C98 singleton fetch, every
    0x00250800 dispatch (all four register arguments plus the three architected
    stack words), and the singleton store;
  * the 0x20-byte format buffer after each format call;
  * the whole effect-table/config page, the singleton page, the requested-name
    page, the config page and the format rodata page;
  * every emulated write outside the private stack.

Coverage: the guard returning 0, 1, 0xFFFFFFFF and 0x80000000; matches at the
first, middle, 15-character-name and last (0x190) entry; a full scan with no
match; every jump-table selector (2..13, plus 0, 1, -1, -2, 100) including the
11-entry table default; all five sector results in both the absolute and the
relative threshold family at their exact float boundaries and both neighbours;
NaN, +-infinity, +-0, huge and tiny reference values; command-pair combinations
(a only, b only, neither, both), u16 id zero extension and state words
0/0x80000000/0xFFFFFFFF. Negative controls mutate the last-entry bound, the
singleton offset, one absolute threshold and the selector-11 jump-table slot.
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
OUT_DIR = ROOT / "build/test_leaf_003949e8"

FUNC_ADDR = 0x003949E8
FUNC_SIZE = 644

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every direct-call stub
DATA_ADDR = 0x00434000
DATA_SIZE = 0x00008000  # effect table + the 0x004342C8 config pointer
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
UI_ADDR = 0x00700000
UI_SIZE = 0x00010000
NAME_ADDR = 0x00710000
NAME_SIZE = 0x00001000
CONFIG_ADDR = 0x00720000
CONFIG_SIZE = 0x00001000
RODATA_ADDR = 0x00730000
RODATA_SIZE = 0x00001000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Effect table: literal 0x00436028, 0x191 records of 0x24 bytes.
TABLE_ADDR = 0x00436028
TABLE_OFFSET = TABLE_ADDR - DATA_ADDR
ENTRY_STRIDE = 0x24
ENTRY_COUNT = 0x191
# Global pointer literal 0x004342C8; the reference float lives at +0x574.
CONFIG_POINTER_OFFSET = 0x004342C8 - DATA_ADDR
REFERENCE_OFFSET = 0x574
# Singleton offset: `add r7,#0x4800; add r7,#0x1E4`.
UI_RESULT_OFFSET = 0x49E4

# Direct-call targets; stubs are placed at the same addresses so the original
# bytes and the relocated candidate resolve to them.
STUB_2C583C = 0x002C583C
STUB_2BE7FC = 0x002BE7FC
STUB_2AA7F4 = 0x002AA7F4
STUB_293C98 = 0x00293C98
STUB_250800 = 0x00250800
THUMB_STUBS = {STUB_2BE7FC}

STUB_NAMES = {
    STUB_2C583C: "engine_func_002c583c",
    STUB_2BE7FC: "ui_func_002be7fc",
    STUB_2AA7F4: "engine_func_002aa7f4",
    STUB_293C98: "ui_func_00293c98",
    STUB_250800: "battle_func_00250800",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_2C583C: 0,
    STUB_2BE7FC: 0,
    STUB_2AA7F4: 0,
    STUB_293C98: 0,
    STUB_250800: 3,   # 0, sector, 0
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
VFP_CALLEE_SAVED_START = 0x3F000000


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def bits_f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def near_bits(bits: int, delta: int) -> int:
    """Return the float whose bit pattern is bits + delta (both neighbours)."""
    return (bits + delta) & 0xFFFFFFFF


# Absolute thresholds from literal pool 0x394C48..0x394C54.
ABS_OUTER_LOW = 0xC03DC290   # -2.9650001525878906
ABS_INNER_LOW = 0xBF7D70A4   # -0.9900000095367432
ABS_INNER_HIGH = 0x403C28F6  #  2.940000057220459
ABS_OUTER_HIGH = 0x3F770A3E  #  0.9650000333786011

SELECTOR_ABSOLUTE = (2, 5, 8, 9, 12)
SELECTOR_THREE = (6, 7, 11)
SELECTOR_RELATIVE = (3, 4, 10, 13, 0, 1, -1, -2, 100)


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
        if "003949e8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_003949e8 not found in {obj_file}: {sorted(funcs)}"
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
    if b"%s.eft\x00" not in rodata:
        raise RuntimeError("could not locate the '%s.eft' format string in .rodata")
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
def default_entry_name(index: int) -> str:
    return f"ef_{index:03d}"


def build_data_page(case: dict) -> bytes:
    page = bytearray(DATA_SIZE)
    names = case.get("names", {})
    entries = case.get("entries", {})
    for index in range(ENTRY_COUNT):
        base = TABLE_OFFSET + index * ENTRY_STRIDE
        name = names.get(index, default_entry_name(index))
        raw = name.encode("ascii")
        if len(raw) > 0x10:
            raise RuntimeError(f"entry name too long for slot {index}: {name!r}")
        page[base : base + len(raw)] = raw
        if index in entries:
            command_a, id_a, command_b, id_b, value = entries[index]
            struct.pack_into("<I", page, base + 0x10, command_a & 0xFFFFFFFF)
            struct.pack_into("<H", page, base + 0x14, id_a & 0xFFFF)
            struct.pack_into("<I", page, base + 0x18, command_b & 0xFFFFFFFF)
            struct.pack_into("<H", page, base + 0x1C, id_b & 0xFFFF)
            struct.pack_into("<I", page, base + 0x20, value & 0xFFFFFFFF)
    pointer = 0 if case.get("null_config") else CONFIG_ADDR
    struct.pack_into("<I", page, CONFIG_POINTER_OFFSET, pointer)
    return bytes(page)


def build_config_page(case: dict) -> bytes:
    page = bytearray([0xCC] * CONFIG_SIZE)
    struct.pack_into("<I", page, REFERENCE_OFFSET,
                     case.get("reference", 0) & 0xFFFFFFFF)
    return bytes(page)


def build_name_page(case: dict) -> bytes:
    page = bytearray(NAME_SIZE)
    raw = case.get("arg_name", "ef_000.eft").encode("ascii") + b"\x00"
    page[: len(raw)] = raw
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 64) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(UI_ADDR, UI_SIZE)
        self.uc.mem_map(NAME_ADDR, NAME_SIZE)
        self.uc.mem_map(CONFIG_ADDR, CONFIG_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
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

        # Enable the VFP coprocessor (CP10/CP11) and the floating-point unit.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0)

        self.events: list = []
        self.format_dsts: list = []
        self.format_payloads: list = []
        self.format_buffers: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, *args) -> None:
        self.events.append(
            ("call", STUB_NAMES[address],
             args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return  # private frame scratch; helpers model the observable writes
        self.events.append(("write", address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2C583C:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("guard", 0))
        elif address == STUB_2BE7FC:
            fmt = read_c_string(uc, r1)
            if fmt != b"%s.eft":
                raise AssertionError(f"unexpected format string {fmt!r}")
            name = read_c_string(uc, r2)
            payload = name + b".eft"
            self._log(address, r0, fmt, r2)
            uc.mem_write(r0, payload + b"\x00")
            self.format_dsts.append(r0)
            self.format_payloads.append(payload)
            # Snapshot immediately: the original later reuses this scratch area
            # for the 0x250800 stack arguments.
            self.format_buffers.append(bytes(uc.mem_read(r0, 0x20)))
            uc.reg_write(arm.UC_ARM_REG_R0, len(payload))
        elif address == STUB_2AA7F4:
            left = read_c_string(uc, r0)
            right = read_c_string(uc, r1)
            self._log(address, left, right)
            uc.reg_write(arm.UC_ARM_REG_R0,
                         0 if left == right else (-1 if left < right else 1))
        elif address == STUB_293C98:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, UI_ADDR)
        elif address == STUB_250800:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x25080000)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(events: list) -> list:
        normalised = []
        for event in events:
            if event[0] == "call":
                name, args = event[1], event[2]
                out = []
                for arg in args:
                    if (isinstance(arg, int)
                            and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE):
                        out.append("<stack>")
                    else:
                        out.append(arg)
                normalised.append(("call", name, tuple(out)))
            else:
                normalised.append(event)
        return normalised

    def run(self, code: bytes, rodata: bytes, case: dict) -> dict:
        self.events = []
        self.format_dsts = []
        self.format_payloads = []
        self.format_buffers = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.ctl_remove_cache(FUNC_ADDR, FUNC_ADDR + 0x400)
        self.uc.mem_write(DATA_ADDR, build_data_page(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.uc.mem_write(UI_ADDR, b"\x00" * UI_SIZE)
        self.uc.mem_write(NAME_ADDR, build_name_page(case))
        self.uc.mem_write(CONFIG_ADDR, build_config_page(case))
        self.uc.mem_write(RODATA_ADDR, rodata)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, NAME_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("arg1", 0x1A2B3C4D)
                          & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("selector", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0xDEADBEEF)
        self.uc.reg_write(arm.UC_ARM_REG_S0, case.get("angle", 0) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for index in range(16, 32):
            self.uc.reg_write(
                getattr(arm, f"UC_ARM_REG_S{index}"),
                VFP_CALLEE_SAVED_START + index,
            )

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        format_buffers = list(self.format_buffers)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "callee_saved_vfp": [
                self.uc.reg_read(getattr(arm, f"UC_ARM_REG_S{index}"))
                for index in range(16, 32)
            ],
            "events": self._normalise(self.events),
            "format_payloads": self.format_payloads,
            "format_buffers": format_buffers,
            "fixtures": {
                "table": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
                "ui": bytes(self.uc.mem_read(UI_ADDR, UI_SIZE)),
                "name": bytes(self.uc.mem_read(NAME_ADDR, NAME_SIZE)),
                "config": bytes(self.uc.mem_read(CONFIG_ADDR, CONFIG_SIZE)),
                "rodata": bytes(self.uc.mem_read(RODATA_ADDR, RODATA_SIZE)),
            },
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "callee_saved_vfp"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["events"] != cand["events"]:
        problems.append(
            "events:\n    orig="
            + repr(orig["events"])
            + "\n    cand="
            + repr(cand["events"])
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
    return problems


# ----------------------------------------------------------------------- cases
def entry(command_a: int = 0, id_a: int = 0, command_b: int = 0,
          id_b: int = 0, value: int = 0) -> tuple:
    return (command_a, id_a, command_b, id_b, value)


BOTH_COMMANDS = {5: entry(0x010001A0, 0x1234, 0x010001A1, 0xABCD, 0xDEADBEEF)}


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        # BOTH_COMMANDS lives at entry 5, so sector-sweep cases dispatch and
        # expose the computed sector in the 0x250800 stack arguments.
        "arg_name": "ef_005.eft",
        "arg1": 0x1A2B3C4D,
        "selector": 2,
        "angle": 0x3F800000,  # 1.0f
        "guard": 0,
        "reference": 0x00000000,
        "entries": {},
        "names": {},
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- guard: any nonzero global word aborts before the lookup.
    for guard in (1, 0xFFFFFFFF, 0x80000000, 0x12345678):
        cases.append(base_case(f"guard 0x{guard:08x} aborts", guard=guard,
                               entries=BOTH_COMMANDS))

    # --- selector sweep: every jump-table slot plus the default range.
    for selector in SELECTOR_ABSOLUTE + SELECTOR_THREE + SELECTOR_RELATIVE:
        cases.append(base_case(f"selector {selector}", selector=selector,
                               entries=BOTH_COMMANDS))

    # --- sector sweep, absolute family (thresholds -2.965/-0.99/2.94/0.965).
    for selector in SELECTOR_ABSOLUTE:
        for angle in (0xC0400000, 0xBF800000, 0x00000000, 0x3F800000,
                      0x40400000):
            cases.append(base_case(
                f"absolute selector {selector} angle 0x{angle:08x}",
                selector=selector, angle=angle, entries=BOTH_COMMANDS))

    # --- sector sweep, relative family around reference == 0 (offsets +-9/+-17).
    for selector in (3, 4, 10, 13, -1):
        for angle in (0xC1A00000, 0xC1200000, 0x00000000, 0x41200000,
                      0x41A00000):
            cases.append(base_case(
                f"relative selector {selector} angle 0x{angle:08x}",
                selector=selector, angle=angle, entries=BOTH_COMMANDS))

    # --- exact absolute boundaries and their float neighbours.
    for boundary in (ABS_OUTER_LOW, ABS_INNER_LOW, ABS_INNER_HIGH,
                     ABS_OUTER_HIGH):
        for delta in (0, -1, 1):
            cases.append(base_case(
                f"absolute boundary 0x{boundary:08x}{delta:+d}",
                selector=2, angle=near_bits(boundary, delta),
                entries=BOTH_COMMANDS))
    for angle in (0x7FC00000, 0x7F800000, 0xFF800000, 0x00000000,
                  0x80000000, 0x00000001, 0x7F7FFFFF):
        cases.append(base_case(
            f"absolute special angle 0x{angle:08x}", selector=2, angle=angle,
            entries=BOTH_COMMANDS))

    # --- exact relative boundaries around several reference values.
    for reference in (0x3FC00000, 0x00000000, 0x80000000, 0x3F800000,
                      0x4B000000, 0x7F7FFFFF, 0x7F800000, 0x7FC00000):
        ref_value = bits_f32(reference)
        for offset in (-17.0, -9.0, 9.0, 17.0):
            try:
                boundary = f32_bits(ref_value + offset)
            except OverflowError:
                boundary = 0x7F800000
            for delta in (0, -1, 1):
                cases.append(base_case(
                    f"relative ref 0x{reference:08x} offset {offset:+g}"
                    f"{delta:+d}",
                    selector=3, reference=reference,
                    angle=near_bits(boundary, delta),
                    entries=BOTH_COMMANDS))
        for angle in (0x00000000, 0x80000000, 0x7FC00000, reference):
            cases.append(base_case(
                f"relative ref 0x{reference:08x} angle 0x{angle:08x}",
                selector=3, reference=reference, angle=angle,
                entries=BOTH_COMMANDS))

    # --- entry lookup boundaries.
    cases.append(base_case("first entry match",
                           arg_name="ef_000.eft",
                           entries={0: entry(0x11, 0, 0, 0, 0x11111111)}))
    cases.append(base_case("middle entry 7 match",
                           arg_name="ef_007.eft",
                           entries={7: entry(0x77, 0, 0, 0, 0x77777777)}))
    cases.append(base_case("entry 399 match",
                           arg_name="ef_399.eft",
                           entries={399: entry(0x99, 0, 0, 0, 0x99999999)}))
    cases.append(base_case("last entry 400 match",
                           arg_name="ef_400.eft",
                           entries={400: entry(0xAA, 0, 0, 0, 0xAAAAAAAA)}))
    cases.append(base_case("last entry 400 match relative",
                           arg_name="ef_400.eft", selector=3, angle=0x41A00000,
                           entries={400: entry(0xAA, 0, 0, 0, 0xAAAAAAAA)}))
    cases.append(base_case("last entry 400 match fixed three",
                           arg_name="ef_400.eft", selector=11, angle=0x41A00000,
                           entries={400: entry(0xAA, 0, 0, 0, 0xAAAAAAAA)}))
    cases.append(base_case("15-character entry name",
                           arg_name="ef_name_max_015.eft",
                           names={3: "ef_name_max_015"},
                           entries={3: entry(0x33, 0, 0, 0, 0x33333333)}))
    for selector in (2, 3, 11):
        cases.append(base_case(f"no match selector {selector}",
                               arg_name="zz_missing.eft",
                               selector=selector, angle=0x41A00000,
                               entries=BOTH_COMMANDS))
    cases.append(base_case("no match absolute null config",
                           arg_name="zz_missing.eft", selector=2,
                           null_config=True))

    # --- command-pair combinations, id extension and state words.
    combos = (
        ("neither command", entry(0, 0, 0, 0, 0x01234567)),
        ("first command only", entry(0x0100019F, 0, 0, 0, 0x89ABCDEF)),
        ("second command only", entry(0, 0, 0x01000195, 0, 0xFEDCBA98)),
        ("both, zero ids", entry(0x0100019F, 0x0000, 0x01000195, 0x0000, 0)),
        ("both, max ids", entry(0xFFFFFFFF, 0xFFFF, 0xFFFFFFFF, 0xFFFF,
                                0xFFFFFFFF)),
        ("both, mixed", entry(0x80000000, 0x8000, 0x7FFFFFFF, 0x7FFF,
                              0x80000000)),
    )
    for label, fixture in combos:
        cases.append(base_case(f"commands: {label}",
                               arg_name="ef_012.eft", selector=12,
                               angle=0xC1200000, entries={12: fixture}))
        cases.append(base_case(f"commands relative: {label}",
                               arg_name="ef_012.eft", selector=10,
                               angle=0x41200000, entries={12: fixture}))

    # --- arg1 passthrough and sector forwarded as stacked float bits.
    for arg1 in (0x00000000, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF):
        cases.append(base_case(f"arg1 0x{arg1:08x}", arg1=arg1,
                               entries={6: entry(0x21, 0x2222, 0x31, 0x3333,
                                                0x55555555)},
                               arg_name="ef_006.eft", selector=6,
                               angle=0x40400000))

    return cases


def run_case_set(orig_code, cand_code, rodata, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, rodata, case)
        cand = Runner().run(cand_code, rodata, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['events'])} events)")
    return passed


def main() -> None:
    print("Testing engine_func_003949e8 (0x003949e8)...")
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
        ("last_entry_bound",
         "constexpr u32 kLastEntryIndex = 0x190;",
         "constexpr u32 kLastEntryIndex = 0x18F;"),
        ("singleton_offset",
         "constexpr u32 kUiResultOffset = 0x49E4;",
         "constexpr u32 kUiResultOffset = 0x49E8;"),
        ("absolute_outer_high",
         "F32FromBits(0x3F770A3Eu)",
         "F32FromBits(0x3F770A3Du)"),
        ("selector_eleven",
         "    case 6:\n    case 7:\n    case 11:\n        sector = 3;",
         "    case 6:\n    case 7:\n    case 14:\n        sector = 3;"),
    ):
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, cand_rodata, case)
            bad = Runner().run(mutant_code, mutant_rodata, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
