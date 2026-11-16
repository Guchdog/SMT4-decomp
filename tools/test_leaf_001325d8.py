#!/usr/bin/env python3
"""Differential test for engine_func_001325d8 (0x001325d8) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the engine_func_001325d8 body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every register argument and the architected
    stack arguments of 0x2ABC9C and 0x13C030;
  * the column offset forwarded to 0x13C030 (relative to the scratch base), so
    the dump loop's accumulator and row reset are observable;
  * the format string read from the pointer passed to 0x13C030;
  * the 0x108-byte scratch buffer after the run;
  * the static guard block, registry slots, cursor word, receiver objects,
    command buffer and rodata string (must match exactly);
  * every emulated write outside the private stack (ordered).

Coverage: guard byte combinations, 0x1384F8 ready/not-ready, dump argument 0
and non-zero forms, cursor untouched / advanced 1..8 words / reset to 0 /
moved backwards, cursor snapshot 0, 0x13C030 returning 0/1/default/0x55/0x100/
0x200 (including size 0 and wrapped bounds), registry pointers re-read after
the registration calls, and signed-boundary words forwarded by the dump and by
the scratch construction.
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
OUT_DIR = ROOT / "build/test_leaf_001325d8"

FUNC_ADDR = 0x001325D8
FUNC_SIZE = 600

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and every stub below 0x400000
DATA_ADDR = 0x00410000
DATA_SIZE = 0x000D0000  # .rodata string, 0x464Bxx slots, 0x4DAD80, objects
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

RODATA_ADDR = 0x004A0000
FORMAT_STRING = b"0x%08x,\x00"
ORIGINAL_FORMAT_ADDR = 0x00410348  # literal-pool word of the original

# Fixed global/object layout used by every fixture.
STATE_ADDR = 0x004DAD80
SLOT_A = 0x00464B84
SLOT_B = 0x00464B8C
SLOT_C = 0x00464B7C
SLOT_D = 0x00464B94
CURSOR_ADDR = 0x004652A0
OBJECT_ADDR = 0x00490000
SOURCE_ADDR = 0x00490080
RECEIVER_A = 0x00480000
VTABLE_A = 0x00480040
RECEIVER_A2 = 0x00480060
VTABLE_A2 = 0x004800A0
RECEIVER_C = 0x00480100
RECEIVER_C2 = 0x00480140
LOCK_HANDLE = 0x00480200
RENDER_HANDLE = 0x00480300
COMMAND_BUFFER = 0x00480400

VIRTUAL_STUB = 0x002FF000

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_2ABE74 = 0x002ABE74
STUB_2ABDF4 = 0x002ABDF4
STUB_2ABDE8 = 0x002ABDE8
STUB_2C50D0 = 0x002C50D0
STUB_2ABC9C = 0x002ABC9C
STUB_2C52F0 = 0x002C52F0
STUB_2C028C = 0x002C028C
STUB_1384F8 = 0x001384F8
STUB_2ABB68 = 0x002ABB68
STUB_13C030 = 0x0013C030
STUB_138BB8 = 0x00138BB8
STUB_2ABBB8 = 0x002ABBB8
STUB_2C5094 = 0x002C5094
STUB_2B77B8 = 0x002B77B8
STUB_2ABB50 = 0x002ABB50

STUB_NAMES = {
    STUB_2ABE74: "engine_func_002abe74",
    STUB_2ABDF4: "engine_func_002abdf4",
    STUB_2ABDE8: "func_002abde8",
    STUB_2C50D0: "engine_func_002c50d0",
    STUB_2ABC9C: "func_002abc9c",
    STUB_2C52F0: "engine_func_002c52f0",
    STUB_2C028C: "engine_func_002c028c",
    STUB_1384F8: "func_001384f8",
    STUB_2ABB68: "battle_func_002abb68",
    STUB_13C030: "engine_func_0013c030",
    STUB_138BB8: "func_00138bb8",
    STUB_2ABBB8: "func_002abbb8",
    STUB_2C5094: "battle_func_002c5094",
    STUB_2B77B8: "func_002b77b8",
    STUB_2ABB50: "func_002abb50",
    VIRTUAL_STUB: "vtable_slot_0x10",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_2ABC9C: 1,
    STUB_13C030: 1,
}

# Absolute windows compared as observable memory.
OBSERVED_RANGES = (
    ("state", STATE_ADDR, 0x20),
    ("slots", 0x00464B70, 0x40),
    ("cursor", CURSOR_ADDR, 8),
    ("object", OBJECT_ADDR, 0x20),
    ("source", SOURCE_ADDR, 0x20),
    ("receivers", 0x00480000, 0x200),
    ("handles", 0x00480200, 0x200),
    ("command_buffer", COMMAND_BUFFER, 0x40),
    ("format_string", ORIGINAL_FORMAT_ADDR, 0x10),
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

SCRATCH_SIZE = 0x108


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
        if name:
            result[name] = data[section[4] : section[4] + section[5]]
    return result


def relocate_candidate(obj_file: Path) -> tuple[bytes, int]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "001325d8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_001325d8 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    sections = elf_sections(obj_file)
    rodata = sections.get(".rodata.str1.1", b"")

    resolved = set()
    rodata_refs = 0
    for rel in relocs:
        if rel.relocation_type in (28, 29):
            target = None
            for address, name in STUB_NAMES.items():
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(
                    f"unresolved call relocation: {rel.symbol_name!r}"
                )
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
            resolved.add(target)
        elif rel.relocation_type == 2:  # R_ARM_ABS32 into .rodata.str1.1
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if addend + len(FORMAT_STRING) > len(rodata):
                raise RuntimeError(f"rodata addend 0x{addend:x} out of range")
            if rodata[addend : addend + len(FORMAT_STRING)] != FORMAT_STRING:
                raise RuntimeError(
                    "could not locate the '0x%08x,' format string in .rodata"
                )
            struct.pack_into("<I", code, rel.offset, RODATA_ADDR + addend)
            rodata_refs += 1
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )

    expected = {address for address in STUB_NAMES if address != VIRTUAL_STUB}
    if resolved != expected:
        raise RuntimeError(
            "direct call relocation set mismatch: "
            f"missing {sorted(expected - resolved)} "
            f"unexpected {sorted(resolved - expected)}"
        )
    if rodata_refs != 1:
        raise RuntimeError(f"expected one format-string relocation, got {rodata_refs}")
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
def build_state(case: dict) -> bytes:
    page = bytearray(0x20)
    page[0x00] = 0xA5
    page[0x04] = case.get("active", 0) & 0xFF
    page[0x05] = case.get("inited", 0) & 0xFF
    struct.pack_into("<I", page, 0x08, LOCK_HANDLE)
    struct.pack_into("<I", page, 0x10, RENDER_HANDLE)
    return bytes(page)


def build_command_buffer(case: dict) -> bytes:
    page = bytearray(0x40)
    words = case.get("words", [])
    for index, word in enumerate(words[:16]):
        struct.pack_into("<I", page, index * 4, word & 0xFFFFFFFF)
    for index in range(len(words), 16):
        struct.pack_into("<I", page, index * 4, 0xDEAD0000 | index)
    return bytes(page)


def build_object(case: dict) -> bytes:
    page = bytearray(0x20)
    struct.pack_into("<I", page, 0x00, 0x4F000000)
    struct.pack_into("<I", page, 0x04, case.get("context", 0x12345678))
    struct.pack_into("<I", page, 0x14, SOURCE_ADDR)
    struct.pack_into("<I", page, 0x18, case.get("extra", 0x0BADF00D))
    return bytes(page)


def build_source(case: dict) -> bytes:
    page = bytearray(0x20)
    struct.pack_into("<I", page, 0x00, 0x5E000000)
    struct.pack_into("<I", page, 0x0C, case.get("range_lo", 0x11223344))
    struct.pack_into("<I", page, 0x10, case.get("range_hi", 0x55667788))
    return bytes(page)


def build_slots(case: dict) -> bytes:
    page = bytearray(0x40)
    base = 0x00464B70
    struct.pack_into("<I", page, SLOT_A - base, RECEIVER_A)
    struct.pack_into("<I", page, SLOT_B - base, case.get("slot_b", 0x0045B0B0))
    struct.pack_into("<I", page, SLOT_C - base, RECEIVER_C)
    struct.pack_into("<I", page, SLOT_D - base, case.get("slot_d", 0x0045D0D0))
    return bytes(page)


def build_receivers() -> bytes:
    page = bytearray(0x200)
    base = 0x00480000
    struct.pack_into("<I", page, RECEIVER_A - base, VTABLE_A)
    struct.pack_into("<I", page, VTABLE_A - base + 0x10, VIRTUAL_STUB)
    struct.pack_into("<I", page, RECEIVER_A2 - base, VTABLE_A2)
    struct.pack_into("<I", page, VTABLE_A2 - base + 0x10, VIRTUAL_STUB)
    struct.pack_into("<I", page, RECEIVER_C - base + 0x04, 0xC0DE0004)
    struct.pack_into("<I", page, RECEIVER_C - base + 0x08, 0xC0DE0008)
    struct.pack_into("<I", page, RECEIVER_C2 - base + 0x04, 0xC0DE0104)
    struct.pack_into("<I", page, RECEIVER_C2 - base + 0x08, 0xC0DE0108)
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class D258Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.scratch_base: int | None = None
        self.abc9c_calls = 0
        self.abe74_calls = 0

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

    def _write_slot(self, slot: int, value: int) -> None:
        self.uc.mem_write(slot, struct.pack("<I", value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2ABE74:
            self._log(address, r0, r1)
            if self.abe74_calls == self.case.get("mutate_a_after"):
                self._write_slot(SLOT_A, RECEIVER_A2)
            if self.abe74_calls == self.case.get("mutate_c_after"):
                self._write_slot(SLOT_C, RECEIVER_C2)
            self.abe74_calls += 1
        elif address == STUB_2ABDF4:
            self._log(address, r0, r1)
        elif address == STUB_2ABDE8:
            self._log(address, r0)
        elif address == STUB_2C50D0:
            self._log(address, r0)
        elif address == STUB_2ABC9C:
            self._log(address, r0, r1, r2, r3)
            self.scratch_base = r0
            self._write_pattern(r0, r1, r2, r3)
            update = self.case.get("cursor_updates", {})
            if self.abc9c_calls in update:
                self._write_slot(
                    CURSOR_ADDR, update[self.abc9c_calls] & 0xFFFFFFFF
                )
            self.abc9c_calls += 1
        elif address == STUB_2C52F0:
            self._log(address, r0, r1)
        elif address == STUB_2C028C:
            self._log(address, r0, r1)
        elif address == STUB_1384F8:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("ready", 1) & 0xFFFFFFFF)
        elif address == STUB_2ABB68:
            self._log(address, r0)
        elif address == STUB_13C030:
            fmt = read_c_string(uc, r3)
            value = self._stack_words(1)[0]
            offset = r0 - self.scratch_base if self.scratch_base is not None else r0
            self._log(address, offset, r1, r2, fmt, value)
            text = ("0x%08x," % value).encode("ascii")
            self._write_text(r0, r1, text)
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                self.case.get("dump_len", len(text)) & 0xFFFFFFFF,
            )
        elif address == STUB_138BB8:
            self._log(address, r0)
        elif address == STUB_2ABBB8:
            self._log(address, r0, r1, r2)
        elif address == STUB_2C5094:
            self._log(address, r0)
        elif address == STUB_2B77B8:
            self._log(address, r0)
        elif address == STUB_2ABB50:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == VIRTUAL_STUB:
            self._log(address, r0, r1)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _write_pattern(self, dst: int, r1: int, r2: int, r3: int) -> None:
        if self.scratch_base is None:
            self.scratch_base = dst
        seed = (r1 ^ r2 ^ r3 ^ self.case.get("extra", 0x0BADF00D)) & 0xFF
        pattern = bytes(((index * 7) + seed) & 0xFF for index in range(SCRATCH_SIZE))
        self.uc.mem_write(dst, pattern)

    def _write_text(self, dst: int, size: int, text: bytes) -> None:
        if self.scratch_base is None:
            return
        low = self.scratch_base
        high = low + SCRATCH_SIZE
        count = min(len(text), max(0, size - 1))
        count = max(0, min(count, high - dst))
        if dst < low or dst > high:
            return
        self.uc.mem_write(dst, text[:count])
        if dst + count < high:
            self.uc.mem_write(dst + count, b"\x00")

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

    def run(self, code: bytes, case: dict, rodata: bytes = b"") -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.scratch_base = None
        self.abc9c_calls = 0
        self.abe74_calls = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(STATE_ADDR, build_state(case))
        self.uc.mem_write(0x00464B70, build_slots(case))
        self.uc.mem_write(CURSOR_ADDR, struct.pack("<I", case.get("cursor_before", 0)))
        self.uc.mem_write(OBJECT_ADDR, build_object(case))
        self.uc.mem_write(SOURCE_ADDR, build_source(case))
        self.uc.mem_write(0x00480000, build_receivers())
        self.uc.mem_write(COMMAND_BUFFER, build_command_buffer(case))
        self.uc.mem_write(ORIGINAL_FORMAT_ADDR, FORMAT_STRING)
        self.uc.mem_write(RODATA_ADDR, rodata if rodata else FORMAT_STRING)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJECT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("state_arg", 0x12345678))
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("reserved", 0xABCDEF01))
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("dump", 0) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        scratch = (
            bytes(self.uc.mem_read(self.scratch_base, SCRATCH_SIZE))
            if self.scratch_base is not None
            else b""
        )

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not in_stack:
                unexpected_writes.append((address, size, _value))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "scratch": scratch,
            "observed": {
                name: bytes(self.uc.mem_read(address, size))
                for name, address, size in OBSERVED_RANGES
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
    if orig["scratch"] != cand["scratch"]:
        problems.append(
            "scratch:\n    orig="
            + orig["scratch"].hex()
            + "\n    cand="
            + cand["scratch"].hex()
        )
    for key, value in orig["observed"].items():
        if value != cand["observed"][key]:
            problems.append(f"observed {key} was modified differently")
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "writes outside the stack:\n    orig="
            + repr(orig["unexpected_writes"])
            + "\n    cand="
            + repr(cand["unexpected_writes"])
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "active": 0,
        "inited": 0,
        "ready": 1,
        "dump": 0,
        "state_arg": 0x12345678,
        "reserved": 0xABCDEF01,
        "context": 0x12345678,
        "extra": 0x0BADF00D,
        "range_lo": 0x11223344,
        "range_hi": 0x55667788,
        "cursor_before": 0,
        "words": [],
    }
    case.update(overrides)
    return case


def init_runs(case: dict) -> bool:
    return bool(case["active"]) and not case["inited"]


def with_cursor_update(case: dict, after: int | None, new_value: int | None) -> dict:
    """Attach a cursor update to the 0x2ABC9C call made by the main path."""
    updates = dict(case.get("cursor_updates", {}))
    index = 1 if init_runs(case) else 0
    index += after or 0
    if new_value is not None:
        updates[index] = new_value
    case["cursor_updates"] = updates
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- guard byte combinations (active/inited) and the ready probe
    for active in (0, 1):
        for inited in (0, 1):
            for ready in (0, 1):
                cases.append(
                    base_case(
                        f"active {active} inited {inited} ready {ready}",
                        active=active,
                        inited=inited,
                        ready=ready,
                    )
                )

    # --- dump argument: zero and every non-zero form
    for dump in (0, 1, 2, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"dump 0x{dump:08x}", dump=dump))

    # --- forwarded state argument (signed boundaries)
    for state in (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(
            base_case(f"state 0x{state:08x}", state_arg=state, active=1,
                      inited=1)
        )

    # --- object context word
    for context in (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"context 0x{context:08x}", context=context,
                               active=1))

    # --- scratch construction inputs (the range words and the extra word)
    for value in (0, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"range_lo 0x{value:08x}", range_lo=value,
                               active=1, inited=0))
        cases.append(base_case(f"range_hi 0x{value:08x}", range_hi=value,
                               active=0))
        cases.append(base_case(f"extra 0x{value:08x}", extra=value,
                               active=0))

    # --- registry tokens forwarded to 0x2ABE74 / 0x2C028C
    for value in (0, 0xFFFFFFFF):
        cases.append(
            base_case(f"registry tokens 0x{value:08x}", slot_b=value,
                      slot_d=value, active=1, inited=0, dump=1,
                      cursor_before=COMMAND_BUFFER, words=[0x11223344])
        )

    # --- command dump loop bounds: no advance, 1..8 words, reset paths
    base_words = [0x11111111 + index for index in range(12)]
    for count in (0, 1, 2, 3, 4, 5, 8):
        case = base_case(
            f"dump {count} words", dump=1, cursor_before=COMMAND_BUFFER,
            words=base_words[: max(count, 1)],
        )
        with_cursor_update(case, 0, COMMAND_BUFFER + 4 * count)
        cases.append(case)

    # --- cursor cleared / moved backwards by the construction call
    case = base_case("cursor cleared by 0x2ABC9C", dump=1,
                     cursor_before=COMMAND_BUFFER, words=base_words)
    with_cursor_update(case, 0, 0)
    cases.append(case)
    case = base_case("cursor moved backwards", dump=1,
                     cursor_before=COMMAND_BUFFER + 8, words=base_words)
    with_cursor_update(case, 0, COMMAND_BUFFER)
    cases.append(case)
    case = base_case("cursor snapshot is null", dump=1, cursor_before=0,
                     words=base_words)
    with_cursor_update(case, 0, COMMAND_BUFFER)
    cases.append(case)

    # --- dumped word values (signed boundaries reach 0x13C030)
    cases.append(
        with_cursor_update(
            base_case(
                "dump signed boundary words", dump=1,
                cursor_before=COMMAND_BUFFER,
                words=[0x00000000, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF,
                       0x0000FFFF, 0xFFFF0000, 0x12345678, 0x00000001],
            ),
            0,
            COMMAND_BUFFER + 32,
        )
    )

    # --- 0x13C030 return-length boundaries (column accumulator)
    for length in (0, 1, 0x55, 0x100, 0x200):
        cases.append(
            with_cursor_update(
                base_case(
                    f"format length 0x{length:03x}", dump=1,
                    cursor_before=COMMAND_BUFFER, dump_len=length,
                    words=base_words[:3],
                ),
                0,
                COMMAND_BUFFER + 12,
            )
        )

    # --- registry pointers re-read after the registration calls
    for after in (0, 1):
        cases.append(
            with_cursor_update(
                base_case(
                    f"registry A re-read after call {after}", active=1,
                    inited=0, ready=0, dump=1,
                    cursor_before=COMMAND_BUFFER, words=base_words[:5],
                    mutate_a_after=after,
                ),
                0,
                COMMAND_BUFFER + 20,
            )
        )
        cases.append(
            base_case(
                f"registry C re-read after call {after}", active=1,
                inited=0, ready=0, dump=0, mutate_c_after=after,
            )
        )

    # --- combined init + dump + advance + re-read
    cases.append(
        with_cursor_update(
            base_case(
                "init dump advance reload", active=1, inited=0, ready=0,
                dump=1, context=0xCAFEBABE, extra=0x13572468,
                range_lo=0x0000FF00, range_hi=0xFFFF00FF,
                cursor_before=COMMAND_BUFFER + 4,
                words=base_words[:6], mutate_a_after=0, mutate_c_after=1,
            ),
            0,
            COMMAND_BUFFER + 24,
        )
    )

    return cases


def run_case_set(orig_code, cand_code, cand_rodata, cases) -> int:
    passed = 0
    for case in cases:
        orig = D258Runner().run(orig_code, case)
        cand = D258Runner().run(cand_code, case, cand_rodata)
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
    print("Testing engine_func_001325d8 (0x001325d8)...")
    orig_code = get_orig_bytes()
    cand_code, cand_rodata = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        f"rodata {len(cand_rodata)} B (relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cand_rodata, cases)

    print("\nNegative controls:")
    controls = (
        ("dump_row_width", "constexpr u32 kDumpRowWidth = 4;",
         "constexpr u32 kDumpRowWidth = 3;"),
        ("dump_column_limit", "constexpr u32 kDumpColumnLimit = 0x100;",
         "constexpr u32 kDumpColumnLimit = 0x101;"),
        ("command_cursor", "constexpr u32 kCommandCursorAddr = 0x004652A0;",
         "constexpr u32 kCommandCursorAddr = 0x004652A4;"),
        ("inited_byte", "constexpr u32 kStateInitedByte = 0x05;",
         "constexpr u32 kStateInitedByte = 0x06;"),
        ("extra_offset", "constexpr u32 kObjExtraOffset = 0x18;",
         "constexpr u32 kObjExtraOffset = 0x1C;"),
    )
    for name, old, new in controls:
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = D258Runner().run(orig_code, case)
            bad = D258Runner().run(mutant_code, case, mutant_rodata)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
