#!/usr/bin/env python3
"""Differential test for engine_func_0038b75c (0x0038B75C) using Unicorn ARM.

Compiles ``src/engine/leaf_batch44_b.cpp``, extracts
``engine_func_0038b75c``, resolves every direct call to a deterministic stub,
and runs the pinned original (``extracted/exefs/code.bin``) against the
candidate in separate Unicorn machines with identical fixtures.

The function receives seven arguments: four in r0-r3, then a pointer flag, an
integer flag and a 32-bit float/VFP payload on the stack (base AAPCS/softfp).
The harness sets all of them and compares:

  * return r0, continuation PC, final SP, callee-saved r4-r11, d8-d15;
  * the ordered call log with every register argument, the five stack words of
    the nine-argument 0x00361888 call, the object fields observed by that
    helper, the copied UTF-16 payload, and the 0x0035A614 in/out values;
  * full BSS (including the selector table and the byte written at +0xFFF),
    the output buffer, the untouched name fixture, and any emulated write
    outside the private stack / BSS page / output buffer.

Coverage: both flags zero/non-zero, 0x00361888 result zero/non-zero, the
``field_138 == 2`` gate, first/second 0x0035A614 results negative and
non-negative (including INT_MIN and -1), selector indices that hit the table,
overlap the +0xFFF byte, wrap around 32 bits, and fall outside the BSS page,
buffer sizes 0/1/3/4/16/0xFFFF/0x10000, UTF-16 strings with the terminator at
unit 0/1/64/65, no terminator, and longer than 65 units, and VFP payloads
covering +0/-0/1.0/Inf/NaN/pointer bit patterns.

Negative controls mutate the field-138 comparison, the BSS byte offset, the
UTF-16 copy bound, and one object field write; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch44_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_0038b75c"

FUNC_ADDR = 0x0038B75C
FUNC_SIZE = 404

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and every stub below 0x400000
BSS_ADDR = 0x00477000
BSS_SIZE = 0x00001000
BUFFER_ADDR = 0x00710000
BUFFER_SIZE = 0x00020000
NAME_ADDR = 0x00730000
NAME_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; stubs live at the same addresses so both the
# original bytes and the relocated candidate resolve to them.
STUB_CTOR = 0x00361710
STUB_COPY = 0x00100C74
STUB_SIZE = 0x003617EC
STUB_FIRST = 0x001472A8
STUB_619CC = 0x003619CC
STUB_619FC = 0x003619FC
STUB_INIT = 0x00361888
STUB_CONVERT = 0x0035A614
STUB_ERROR = 0x002BCE48
STUB_FILL = 0x002C3B48

THUMB_STUBS = {STUB_COPY}

STUB_NAMES = {
    STUB_CTOR: "engine_func_00361710",
    STUB_COPY: "crt_func_00100c74",
    STUB_SIZE: "func_003617ec",
    STUB_FIRST: "camp_func_001472a8",
    STUB_619CC: "func_003619cc",
    STUB_619FC: "func_003619fc",
    STUB_INIT: "engine_func_00361888",
    STUB_CONVERT: "func_0035a614",
    STUB_ERROR: "engine_func_002bce48",
    STUB_FILL: "engine_func_002c3b48",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_CTOR: 0,
    STUB_COPY: 0,
    STUB_SIZE: 0,
    STUB_FIRST: 0,
    STUB_619CC: 0,
    STUB_619FC: 0,
    STUB_INIT: 5,  # float payload, 0, 0, 0, 0
    STUB_CONVERT: 0,
    STUB_ERROR: 0,
    STUB_FILL: 0,
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
VFP_SAVED = {
    "d8": arm.UC_ARM_REG_D8,
    "d9": arm.UC_ARM_REG_D9,
    "d10": arm.UC_ARM_REG_D10,
    "d11": arm.UC_ARM_REG_D11,
    "d12": arm.UC_ARM_REG_D12,
    "d13": arm.UC_ARM_REG_D13,
    "d14": arm.UC_ARM_REG_D14,
    "d15": arm.UC_ARM_REG_D15,
}
VFP_SAVED_START = {
    "d8": 0x0123456789ABCDEF,
    "d9": 0x1111222233334444,
    "d10": 0x5555666677778888,
    "d11": 0x9999AAAABBBBCCCC,
    "d12": 0xDDDDEEEEFFFF0000,
    "d13": 0x13572468ACE0BDF1,
    "d14": 0x2468ACE013579BDF,
    "d15": 0xFEDCBA9876543210,
}

# Object fields observed by the 0x00361888 stub (ARM offsets).
OBJECT_FIELD_OFFSETS_U32 = (0x00, 0x08, 0x0C, 0x14)
OBJECT_FIELD_OFFSETS_U8 = (0x113, 0x114, 0x115)
TEXT_OFFSET = 0x90
OBJECT_FIELD_138 = 0x138
OBJECT_FIELD_144 = 0x144

# Distinct u16 table entries inside the BSS page.
TABLE_BASE = BSS_ADDR
TABLE_ENTRIES = {
    0: 0x1000,
    1: 0x1001,
    2: 0x1002,
    3: 0x1003,
    4: 0x1004,
    7: 0x1007,
    0x100: 0x1100,
    0x7FE: 0x17FE,
    0x7FF: 0x17FF,
}


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


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0038b75c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0038b75c not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
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

    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch44_b.o"
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
def build_bss() -> bytes:
    page = bytearray([0x5A] * BSS_SIZE)
    for index, value in TABLE_ENTRIES.items():
        struct.pack_into("<H", page, index * 2, value)
    return bytes(page)


def build_buffer() -> bytes:
    return bytes(((index * 0x0D + 0xA5) & 0xFF) for index in range(BUFFER_SIZE))


def build_name(units: list[int]) -> bytes:
    page = bytearray(NAME_SIZE)
    for index in range(NAME_SIZE // 2):
        value = 0x0042 + (index & 0x1F)
        struct.pack_into("<H", page, index * 2, value)
    for index, value in enumerate(units):
        struct.pack_into("<H", page, index * 2, value & 0xFFFF)
    return bytes(page)


class B75CRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        # Enable the VFP coprocessor (CP10/CP11) for the vpush/vldr/vstr block.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(BSS_ADDR, BSS_SIZE)
        self.uc.mem_map(BUFFER_ADDR, BUFFER_SIZE)
        self.uc.mem_map(NAME_ADDR, NAME_SIZE)
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
        self.copy_payloads: list = []
        self.fill_pre: list = []
        self.convert_index = 0
        self.case: dict = {}

    # ------------------------------------------------------------------ helpers
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    @staticmethod
    def _normalise(value):
        if isinstance(value, int) and STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _u32(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _u16(self, address: int) -> int:
        return struct.unpack("<H", self.uc.mem_read(address, 2))[0]

    def _u8(self, address: int) -> int:
        return self.uc.mem_read(address, 1)[0]

    def _write_u32(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _object_fields(self, obj: int) -> tuple:
        fields = tuple(self._u32(obj + off) for off in OBJECT_FIELD_OFFSETS_U32)
        fields += tuple(self._u8(obj + off) for off in OBJECT_FIELD_OFFSETS_U8)
        fields += (self._u16(obj + 0x20),)
        # First eight UTF-16 units prove the copy reached object+0x90.
        fields += tuple(self._u16(obj + TEXT_OFFSET + index * 2) for index in range(8))
        return fields

    # ------------------------------------------------------------------ stubs
    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_CTOR:
            self._log(address, self._normalise(r0))
            # The real constructor initialises at least 0x358 bytes; the
            # page-aligned size helper below is stubbed independently.
            uc.mem_write(r0, b"\x00" * 0x358)

        elif address == STUB_COPY:
            count = r2
            self._log(address, self._normalise(r0), r1, count)
            src = r1
            dst = r0
            remaining = count
            while remaining:
                unit = self._u16(src)
                self.uc.mem_write(dst, struct.pack("<H", unit))
                dst += 2
                if unit != 0:
                    src += 2
                remaining -= 1
            self.copy_payloads.append(bytes(uc.mem_read(r0, count * 2)))

        elif address == STUB_SIZE:
            self._log(address, self._normalise(r0), r1, r2)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["size"] & 0xFFFFFFFF)

        elif address == STUB_FIRST:
            self._log(address, r0)

        elif address == STUB_619CC:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x3619CC)

        elif address == STUB_619FC:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x3619FC)

        elif address == STUB_INIT:
            # Log the outgoing arguments and the object fields this function
            # has just written before applying the helper's documented result.
            self._log(
                address,
                self._normalise(r0),
                self._normalise(r1),
                r2,
                r3,
                self._object_fields(r1),
            )
            self._write_u32(r1 + OBJECT_FIELD_138, self.case["status"])
            self._write_u32(r1 + OBJECT_FIELD_144, self.case["index"])
            self.uc.mem_write(r0, struct.pack("<B", self.case["out_byte"]))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["init_result"])

        elif address == STUB_CONVERT:
            index = self.convert_index
            self.convert_index += 1
            in1 = self._u32(r1)
            in2 = self._u32(r3)
            table = None
            if BSS_ADDR <= r2 <= BSS_ADDR + BSS_SIZE - 2:
                table = self._u16(r2)
            self._log(
                address,
                index,
                r0,
                self._normalise(r1),
                r2,
                self._normalise(r3),
                in1,
                in2,
                table,
            )
            # Leave distinct values so the second call proves the same in/out
            # locals are reused rather than reinitialised.
            self._write_u32(r1, 0x22222222 if index == 0 else 0x44444444)
            self._write_u32(r3, 0x11111111 if index == 0 else 0x33333333)
            if r0 != 0:
                self.uc.mem_write(r0, struct.pack("<I", 0x54455854))  # "TEXT"
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case["convert_results"][index] & 0xFFFFFFFF
            )

        elif address == STUB_ERROR:
            self._log(address, r0)

        elif address == STUB_FILL:
            self._log(address, r0, r1)
            if r1:
                self.fill_pre.append(bytes(uc.mem_read(r0, min(r1, 16))))
                uc.mem_write(r0, b"\x00" * r1)
            else:
                self.fill_pre.append(b"")

        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.copy_payloads = []
        self.fill_pre = []
        self.convert_index = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(BSS_ADDR, build_bss())
        self.uc.mem_write(BUFFER_ADDR, build_buffer())
        self.uc.mem_write(NAME_ADDR, build_name(case["name_units"]))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        # Allocate the three outgoing stack arguments.
        self.uc.mem_write(
            ENTRY_SP,
            struct.pack(
                "<III",
                case["flag_a"] & 0xFFFFFFFF,
                case["flag_b"] & 0xFFFFFFFF,
                case["vfp_bits"] & 0xFFFFFFFF,
            ),
        )

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case.get("p0", 0xDEADBEEF))
        self.uc.reg_write(arm.UC_ARM_REG_R1, BUFFER_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, NAME_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case["buffer_size"] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for name, value in VFP_SAVED_START.items():
            self.uc.reg_write(VFP_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=10_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        buffer_len = min(case["buffer_size"], BUFFER_SIZE - 8) + 16

        unexpected_writes = []
        for address, size in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_bss = BSS_ADDR <= address < BSS_ADDR + BSS_SIZE
            in_buffer = BUFFER_ADDR <= address < BUFFER_ADDR + BUFFER_SIZE
            if not (in_stack or in_bss or in_buffer):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "vfp_saved": {
                name: self.uc.reg_read(reg) for name, reg in VFP_SAVED.items()
            },
            "call_log": [
                (name, tuple(self._normalise(arg) for arg in args))
                for name, args in self.call_log
            ],
            "copy_payloads": self.copy_payloads,
            "fill_pre": self.fill_pre,
            "bss": bytes(self.uc.mem_read(BSS_ADDR, BSS_SIZE)),
            "buffer": bytes(self.uc.mem_read(BUFFER_ADDR, buffer_len)),
            "name": bytes(self.uc.mem_read(NAME_ADDR, NAME_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "vfp_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    if orig["copy_payloads"] != cand["copy_payloads"]:
        problems.append(
            "copy payloads:\n    orig="
            + repr(orig["copy_payloads"])
            + "\n    cand="
            + repr(cand["copy_payloads"])
        )
    if orig["fill_pre"] != cand["fill_pre"]:
        problems.append(
            "fill pre-state:\n    orig="
            + repr(orig["fill_pre"])
            + "\n    cand="
            + repr(cand["fill_pre"])
        )
    for key in ("bss", "buffer", "name"):
        if orig[key] != cand[key]:
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
        "buffer_size": 0x10,
        "flag_a": 0,
        "flag_b": 0,
        "size": 0x20000,
        "status": 2,
        "index": 0,
        "init_result": 1,
        "out_byte": 0x5A,
        "convert_results": (0, 0),
        "vfp_bits": 0x3F800000,  # 1.0f
        "name_units": [0x0041, 0x0042, 0x0000],
        "p0": 0xDEADBEEF,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- flag block and the two 0x00361888 early-return paths
    for flag_a in (0, 1, 0xFFFFFFFF):
        for flag_b in (0, 1, 0xFFFFFFFF):
            cases.append(
                base_case(f"flags a={flag_a:#x} b={flag_b:#x}",
                          flag_a=flag_a, flag_b=flag_b)
            )
    cases.append(base_case("init helper returns 0", init_result=0))
    cases.append(base_case("init helper returns -1", init_result=0xFFFFFFFF))
    for status in (0, 1, 2, 3, 0xFFFFFFFF, 0x80000000):
        cases.append(base_case(f"object status {status:#x}", status=status))

    # --- selector index: table, +0xFFF overlap, 32-bit wrap, out of page
    for index in (0, 1, 2, 3, 4, 7, 0x100, 0x7FE, 0x7FF,
                  0x800, 0xFFFF, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"selector index {index:#x}", index=index))

    # --- 0x0035A614 results: only the sign bit is observed
    for first, second in (
        (0, 0),
        (-1, 0),
        (0, -1),
        (-1, -1),
        (0x80000000, 0),
        (0, 0x80000000),
        (0x7FFFFFFF, 0x7FFFFFFF),
        (0x80000000, 0x80000000),
    ):
        cases.append(
            base_case(f"convert results {first:#x}/{second:#x}",
                      convert_results=(first, second))
        )

    # --- buffer size: memset bound and u16 field truncation
    for size in (0, 1, 2, 3, 4, 0x10, 0x80, 0xFF, 0x100, 0xFFFF, 0x10000):
        cases.append(base_case(f"buffer size {size:#x}", buffer_size=size))

    # --- UTF-16 copy: terminator position / exact bound / no terminator
    short = [0x0041 + (i & 0x1F) for i in range(70)]
    for position in (0, 1, 2, 63, 64, 65, 69):
        units = short[:position] + [0] + short[position + 1 :]
        cases.append(base_case(f"name terminator at {position}", name_units=units))
    cases.append(base_case("name exactly 65 units", name_units=short[:65]))
    cases.append(base_case("name 66 units", name_units=short[:66]))
    cases.append(base_case("name 70 units", name_units=short[:70]))
    cases.append(base_case("name all zero", name_units=[0]))

    # --- VFP payload is opaque 32-bit data; cover FP and pointer patterns
    for bits, label in (
        (0x00000000, "+0.0"),
        (0x80000000, "-0.0"),
        (0x3F800000, "1.0"),
        (0x7F800000, "+Inf"),
        (0xFF800000, "-Inf"),
        (0x7FC00000, "NaN"),
        (0x7F800001, "signalling NaN"),
        (0x004776D4, "pointer-like"),
    ):
        cases.append(base_case(f"vfp payload {label}", vfp_bits=bits))

    # --- size helper return is forwarded untouched
    for size in (0, 1, 0x20000, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"size result {size:#x}", size=size))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = B75CRunner().run(orig_code, case)
        cand = B75CRunner().run(cand_code, case)
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
    print("Testing engine_func_0038b75c (0x0038B75C)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("status_gate",
         "if (object.field_138 != 2) {",
         "if (object.field_138 != 3) {"),
        ("bss_byte_offset",
         "*reinterpret_cast<volatile u8*>(kBssBase + 0xFFF) = 0;",
         "*reinterpret_cast<volatile u8*>(kBssBase + 0xFFE) = 0;"),
        ("copy_bound",
         "crt_func_00100c74(object.text_90, name, 0x41);",
         "crt_func_00100c74(object.text_90, name, 0x40);"),
        ("object_field",
         "object.field_08 = 4;",
         "object.field_08 = 5;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = B75CRunner().run(orig_code, case)
            bad = B75CRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
