#!/usr/bin/env python3
"""Differential test for engine_func_0021e3c0 (0x0021e3c0).

The original is a script step that drives the placed-object loader behind the
singleton at 0x00447E70.  The candidate is the readable C++ reconstruction in
src/engine/leaf_batch45_a.cpp.

Both versions are executed with Unicorn ARM emulation.  Every helper is a
deterministic stub, the observable memory (context, slot array, placement
records) is compared byte-for-byte, and the ordered call log records all
arguments, including the stack buffer contents that are only reachable through
the helpers.

The original calls the Thumb variadic formatter at 0x002BE7FC with BLX.  Both
the original and the candidate call sites are normalised to an ARM BL to the
same state-agnostic ARM stub, so the interworking flag is not part of the
comparison domain (the stub only observes arguments and writes a string).
"""

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k  # noqa: E402

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
FUNC_ADDR = 0x0021E3C0
FUNC_SIZE = 680
FUNC_SYMBOL = "engine_func_0021e3c0"
TU_SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_0021e3c0"

# Memory map
STACK_ADDR, STACK_SIZE = 0x08000000, 0x00010000
CODE_ADDR, CODE_SIZE = 0x001F0000, 0x00100000
DATA_ADDR, DATA_SIZE = 0x00440000, 0x00010000  # holds the 0x00447E70 pointer
CTX_ARENA, CTX_ARENA_SIZE = 0x00500000, 0x00010000
CTX_ADDR = CTX_ARENA + 0x100  # leave room before it for the slot == -1 case
REC_ADDR, REC_SIZE = 0x00600000, 0x00010000
MODEL_ADDR, MODEL_SIZE = 0x00620000, 0x00001000
TRAP_ADDR = 0x90000000
ZERO_PAGE, ZERO_PAGE_SIZE = 0x00000000, 0x00001000
RODATA_BASE = 0x00700000

CTX_POINTER = 0x00447E70
SLOT_STRIDE = 0x48
SLOTS_OFFSET = 0x14
SLOT_COUNT = 24
CTX_WINDOW = 0x800  # covers the header, all slots, and slot == -1 spillover

# Helper addresses and their stub semantics
HELPERS = {
    0x0024F210: "engine_func_0024f210",  # record count
    0x0025C07C: "engine_func_0025c07c",  # placement record lookup
    0x002BE7FC: "ui_func_002be7fc",      # format path string
    0x0029A2D0: "engine_func_0029a2d0",  # start model load
    0x002AE16C: "engine_func_002ae16c",  # model ready?
    0x002A06C8: "engine_func_002a06c8",  # enable model
    0x002BF86C: "engine_func_002bf86c",  # strcpy
}
HELPER_NAMES = {name: addr for addr, name in HELPERS.items()}

# Context offsets
CTX_FILTER_A = 0x04
CTX_FILTER_B = 0x06
CTX_STATE = 0x08
CTX_CURSOR = 0x0A
CTX_SLOT = 0x0C
CTX_LOADED = 0x10

# Slot offsets
SLOT_ENABLED = 0x00
SLOT_POSITION = 0x04
SLOT_OFFSET = 0x10
SLOT_ANGLE = 0x1C
SLOT_FIELD_20 = 0x20
SLOT_OBJECT_ID = 0x24
SLOT_MODEL = 0x28
SLOT_NAME = 0x2C
SLOT_RECORD_INDEX = 0x44

# Record offsets
REC_ID_A = 0x00
REC_ID_B = 0x02
REC_OBJECT_ID = 0x04
REC_X = 0x06
REC_Y = 0x08
REC_Z = 0x0A
REC_ANGLE = 0x0C
REC_ALT_Y = 0x0E
REC_NAME = 0x10


def get_orig_bytes():
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        data = handle.read(FUNC_SIZE)
    if len(data) != FUNC_SIZE:
        raise RuntimeError("could not read the pinned original function")
    return data


def read_elf_sections(obj_path):
    data = Path(obj_path).read_bytes()
    e_shoff, = struct.unpack_from("<I", data, 32)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstr_data = data[shstr[4]:shstr[4] + shstr[5]]

    def section_name(offset):
        return shstr_data[offset:].split(b"\x00")[0].decode("ascii", "replace")

    return data, sections, [section_name(s[0]) for s in sections]


def elf_function_layout(obj_path, symbol_name):
    """Return (st_value, st_size, symbol table, section names) for a symbol."""
    data, sections, names = read_elf_sections(obj_path)
    symtab = next(s for s in sections if s[1] == 2)
    strtab = sections[symtab[6]]
    strtab_data = data[strtab[4]:strtab[4] + strtab[5]]

    symbols = []
    for index in range(symtab[5] // 16):
        st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack_from(
            "<IIIBBH", data, symtab[4] + index * 16
        )
        name = strtab_data[st_name:].split(b"\x00")[0].decode("ascii", "replace")
        symbols.append((name, st_value, st_size, st_info & 0xF, st_shndx))

    for entry in symbols:
        if entry[0] == symbol_name:
            return data, sections, names, symbols, entry
    raise RuntimeError(f"symbol {symbol_name} not found in {obj_path}")


def collect_candidate(obj_path):
    """Extract the candidate code and resolve calls plus rodata references."""
    data, sections, names, symbols, entry = elf_function_layout(
        obj_path, FUNC_SYMBOL
    )
    _, st_value, st_size, _, st_shndx = entry
    text = sections[st_shndx]
    code = bytearray(data[text[4] + st_value:text[4] + st_value + st_size])
    relocs = []
    rodata_sections = {}
    for index, section in enumerate(sections):
        if section[1] not in (4, 9) or section[7] != st_shndx:
            continue
        for rel_index in range(section[5] // 8):
            r_offset, r_info = struct.unpack_from(
                "<II", data, section[4] + rel_index * 8
            )
            if not (st_value <= r_offset < st_value + st_size):
                continue
            relocs.append((r_offset - st_value, r_info & 0xFF, r_info >> 8))

    for offset, rel_type, sym_index in relocs:
        if rel_type in (28, 29, 10):
            symbol = symbols[sym_index][0]
            if symbol not in HELPER_NAMES:
                raise RuntimeError(f"unexpected call relocation to {symbol!r}")
            target = HELPER_NAMES[symbol]
            instruction = struct.unpack_from("<I", code, offset)[0]
            displacement = (target - (FUNC_ADDR + offset + 8)) >> 2
            struct.pack_into(
                "<I", code, offset,
                (instruction & 0xFF000000) | (displacement & 0x00FFFFFF),
            )
        elif rel_type == 2:
            sym_shndx = symbols[sym_index][4]
            section_name = names[sym_shndx]
            section = sections[sym_shndx]
            addend = struct.unpack_from("<I", code, offset)[0]
            if section_name not in rodata_sections:
                rodata_sections[section_name] = bytes(
                    data[section[4]:section[4] + section[5]]
                )
            struct.pack_into(
                "<I", code, offset,
                RODATA_BASE + list(rodata_sections).index(section_name) * 0x10000
                + addend,
            )
        else:
            raise RuntimeError(f"unexpected relocation type {rel_type}")
    return bytes(code), rodata_sections


def normalise_original_calls(code):
    """Rewrite BLX to an ARM BL so the shared ARM stubs stay in ARM state."""
    out = bytearray(code)
    seen = set()
    for offset in range(0, len(out) - 3, 4):
        word = struct.unpack_from("<I", out, offset)[0]
        pc = FUNC_ADDR + offset + 8
        if (word & 0xFE000000) == 0xFA000000:  # BLX (immediate)
            immediate = word & 0x00FFFFFF
            if immediate & 0x00800000:
                immediate -= 0x01000000
            half = (word >> 24) & 1
            target = (pc & ~3) + (immediate << 2) + (half << 1)
        elif (word & 0x0F000000) == 0x0B000000:  # BL
            immediate = word & 0x00FFFFFF
            if immediate & 0x00800000:
                immediate -= 0x01000000
            target = pc + immediate * 4
        else:
            continue
        if target not in HELPERS:
            continue
        displacement = (target - pc) >> 2
        # BLX (cond 0xF) becomes an unconditional ARM BL (cond 0xE).
        struct.pack_into(
            "<I", out, offset, 0xEB000000 | (displacement & 0x00FFFFFF)
        )
        seen.add(target)
    if seen != set(HELPERS):
        raise RuntimeError(f"original call sites not understood: {sorted(seen)}")
    return bytes(out)


def signed32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


class Runner:
    def __init__(self, rodata):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(CTX_ARENA, CTX_ARENA_SIZE)
        self.uc.mem_map(REC_ADDR, REC_SIZE)
        self.uc.mem_map(MODEL_ADDR, MODEL_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_map(ZERO_PAGE, ZERO_PAGE_SIZE)
        for index, (name, blob) in enumerate(rodata.items()):
            base = RODATA_BASE + index * 0x10000
            self.uc.mem_map(base, 0x10000)
            self.uc.mem_write(base, blob)

        self.call_log = []
        self.counts = []
        self.records = []
        self.model_seq = []
        self.model_index = 0
        self.ready = {}

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        hooks = {
            0x0024F210: self._on_count,
            0x0025C07C: self._on_record,
            0x002BE7FC: self._on_format,
            0x0029A2D0: self._on_load,
            0x002AE16C: self._on_ready,
            0x002A06C8: self._on_enable,
            0x002BF86C: self._on_strcpy,
        }
        for address, callback in hooks.items():
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, callback,
                             begin=address, end=address)

        # VFP is used by the model publishing path; grant CP10/CP11 and set
        # FPEXC.EN exactly like the other VFP differential tests.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0xF00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    # ---- helpers -------------------------------------------------------
    def _read_string(self, address, limit=64):
        try:
            raw = bytes(self.uc.mem_read(address, limit))
        except Exception:
            return b"<unmapped>"
        end = raw.find(b"\x00")
        return raw if end < 0 else raw[:end]

    def _on_count(self, uc, address, size, user_data):
        if self.counts:
            value = self.counts.pop(0)
        elif self.records:
            value = len(self.records)
        else:
            value = 0
        self.call_log.append(("count", value))
        uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)

    def _on_record(self, uc, address, size, user_data):
        index = signed32(uc.reg_read(arm.UC_ARM_REG_R0))
        self.call_log.append(("record", index))
        if 0 <= index < len(self.records):
            value = REC_ADDR + index * 0x20
        else:
            # The original dereferences the result without a null check; the
            # zero page is mapped so a null lookup reads a zeroed record.
            value = 0
        uc.reg_write(arm.UC_ARM_REG_R0, value)

    def _on_format(self, uc, address, size, user_data):
        dst = uc.reg_read(arm.UC_ARM_REG_R0)
        fmt = self._read_string(uc.reg_read(arm.UC_ARM_REG_R1))
        value = signed32(uc.reg_read(arm.UC_ARM_REG_R2))
        self.call_log.append(("format", fmt, value))
        uc.mem_write(dst, b"fmt_" + str(value).encode("ascii") + b"\x00")

    def _on_load(self, uc, address, size, user_data):
        path = self._read_string(uc.reg_read(arm.UC_ARM_REG_R0))
        kind = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("load", path, kind))
        if self.model_index < len(self.model_seq):
            handle = self.model_seq[self.model_index]
        else:
            handle = MODEL_ADDR + 0x40 * (self.model_index + 1)
        self.model_index += 1
        uc.reg_write(arm.UC_ARM_REG_R0, handle & 0xFFFFFFFF)

    def _on_ready(self, uc, address, size, user_data):
        handle = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("ready", handle))
        if handle == 0:
            value = 0  # 0x002AE16C returns 0 for a null model
        else:
            value = self.ready.get(handle, 1)
        uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)

    def _on_enable(self, uc, address, size, user_data):
        handle = uc.reg_read(arm.UC_ARM_REG_R0)
        mode = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("enable", handle, mode))

    def _on_strcpy(self, uc, address, size, user_data):
        dst = uc.reg_read(arm.UC_ARM_REG_R0)
        src = self._read_string(uc.reg_read(arm.UC_ARM_REG_R1))
        self.call_log.append(("strcpy", signed32(dst - CTX_ADDR), src))
        uc.mem_write(dst, src + b"\x00")

    # ---- scenario ------------------------------------------------------
    def run(self, code, scenario):
        self.call_log = []
        self.counts = list(scenario.get("counts", []))
        self.records = list(scenario.get("records", []))
        self.model_seq = list(scenario.get("models", []))
        self.model_index = 0
        self.ready = dict(scenario.get("ready", {}))

        self.uc.mem_write(FUNC_ADDR, code)
        # The original and the candidate are placed at the same address, so the
        # translated blocks of the previous run must be dropped.
        self.uc.ctl_remove_cache(CODE_ADDR, CODE_ADDR + CODE_SIZE)
        self.uc.mem_write(CTX_ARENA, b"\x00" * CTX_ARENA_SIZE)
        self.uc.mem_write(REC_ADDR, b"\x00" * REC_SIZE)
        self.uc.mem_write(MODEL_ADDR, b"\x00" * MODEL_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.mem_write(CTX_POINTER, struct.pack("<I", CTX_ADDR))
        header = bytearray(0x14)
        struct.pack_into("<I", header, 0, scenario.get("field_00", 0))
        struct.pack_into("<h", header, CTX_FILTER_A, scenario["filter_a"])
        struct.pack_into("<h", header, CTX_FILTER_B, scenario["filter_b"])
        struct.pack_into("<h", header, CTX_STATE, scenario["state"])
        struct.pack_into("<h", header, CTX_CURSOR, scenario["cursor"])
        struct.pack_into("<h", header, CTX_SLOT, scenario["slot"])
        struct.pack_into("<I", header, CTX_LOADED, scenario.get("loaded", 0))
        self.uc.mem_write(CTX_ADDR, bytes(header))

        for index, slot in scenario.get("slots", {}).items():
            base = CTX_ADDR + SLOTS_OFFSET + index * SLOT_STRIDE
            self.uc.mem_write(base + SLOT_ENABLED,
                              bytes([slot.get("enabled", 0) & 0xFF,
                                     slot.get("enabled_01", 0) & 0xFF,
                                     slot.get("enabled_02", 0) & 0xFF, 0]))
            self.uc.mem_write(base + SLOT_FIELD_20,
                              struct.pack("<I", slot.get("field_20", 0)))
            self.uc.mem_write(base + SLOT_OBJECT_ID,
                              struct.pack("<I", slot.get("object_id", 0)))
            self.uc.mem_write(base + SLOT_MODEL,
                              struct.pack("<I", slot.get("model", 0)))
            name = slot.get("name", b"")
            self.uc.mem_write(base + SLOT_NAME, name + b"\x00")
            self.uc.mem_write(base + SLOT_RECORD_INDEX,
                              struct.pack("<I", slot.get("record_index", 0)))
            for field, value in slot.get("floats", {}).items():
                self.uc.mem_write(base + field, struct.pack("<f", value))

        for index, record in enumerate(self.records):
            base = REC_ADDR + index * 0x20
            blob = bytearray(0x20)
            struct.pack_into("<h", blob, REC_ID_A, record[0])
            struct.pack_into("<h", blob, REC_ID_B, record[1])
            struct.pack_into("<h", blob, REC_OBJECT_ID, record[2])
            struct.pack_into("<h", blob, REC_X, record[3])
            struct.pack_into("<h", blob, REC_Y, record[4])
            struct.pack_into("<h", blob, REC_Z, record[5])
            struct.pack_into("<h", blob, REC_ANGLE, record[6])
            struct.pack_into("<h", blob, REC_ALT_Y, record[7])
            name = record[8]
            blob[REC_NAME:REC_NAME + len(name)] = name
            self.uc.mem_write(base, bytes(blob))

        stack_pointer = STACK_ADDR + STACK_SIZE - 0x800
        self.uc.reg_write(arm.UC_ARM_REG_SP, stack_pointer)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
        for index, register in enumerate((
            arm.UC_ARM_REG_R4, arm.UC_ARM_REG_R5, arm.UC_ARM_REG_R6,
            arm.UC_ARM_REG_R7, arm.UC_ARM_REG_R8, arm.UC_ARM_REG_R9,
            arm.UC_ARM_REG_R10, arm.UC_ARM_REG_R11,
        )):
            self.uc.reg_write(register, 0xA0 + index)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
        except Exception as error:  # pragma: no cover - failure diagnostics
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"crash at PC=0x{pc:08x}: {error}") from error

        result = {
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
        }
        for index, register in enumerate((
            arm.UC_ARM_REG_R4, arm.UC_ARM_REG_R5, arm.UC_ARM_REG_R6,
            arm.UC_ARM_REG_R7, arm.UC_ARM_REG_R8, arm.UC_ARM_REG_R9,
            arm.UC_ARM_REG_R10, arm.UC_ARM_REG_R11,
        )):
            result[f"r{4 + index}"] = self.uc.reg_read(register)
        result["log"] = tuple(self.call_log)
        result["ctx"] = bytes(self.uc.mem_read(CTX_ARENA, CTX_WINDOW))
        result["records"] = bytes(self.uc.mem_read(
            REC_ADDR, max(0x20, len(self.records) * 0x20)
        ))
        result["models"] = bytes(self.uc.mem_read(MODEL_ADDR, MODEL_SIZE))
        return result


def describe_difference(original, candidate):
    for key in original:
        if original[key] != candidate[key]:
            return key, original[key], candidate[key]
    return None


def slot(occupied=0, **kwargs):
    data = dict(kwargs)
    data["enabled"] = occupied
    return data


def record(id_a=0, id_b=0, object_id=0, x=0, y=0, z=0, angle=0, alt=0,
           name=b""):
    return (id_a, id_b, object_id, x, y, z, angle, alt, name)


def build_cases():
    cases = []

    # ---- dispatch ------------------------------------------------------
    cases.append(dict(
        name="dispatch: state 0 is a no-op",
        state=0, cursor=0, slot=0, filter_a=0, filter_b=0,
    ))
    cases.append(dict(
        name="dispatch: unrelated state 0x0D returns 0",
        state=0x0D, cursor=0, slot=0, filter_a=0, filter_b=0,
    ))
    cases.append(dict(
        name="dispatch: state 0x63 returns 1",
        state=0x63, cursor=0, slot=0, filter_a=0, filter_b=0,
    ))
    cases.append(dict(
        name="dispatch: negative state returns 0",
        state=-1, cursor=0, slot=0, filter_a=0, filter_b=0,
    ))

    # ---- scan state 0x0A ----------------------------------------------
    cases.append(dict(
        name="scan: count <= cursor finishes the step",
        state=0x0A, cursor=3, slot=0, filter_a=5, filter_b=6,
        counts=[3],
    ))
    cases.append(dict(
        name="scan: count < cursor (boundary below) finishes",
        state=0x0A, cursor=9, slot=0, filter_a=5, filter_b=6,
        counts=[2, 2],
    ))
    cases.append(dict(
        name="scan: negative cursor is probed before index 0",
        state=0x0A, cursor=-1, slot=0, filter_a=5, filter_b=6,
        counts=[2, 2, 2],
        records=[record(5, 6, 7, 1, 2, 3, 4, 5, b"JOB7")],
    ))
    cases.append(dict(
        name="scan: rejects negative id_a, id_a, id_b and object_id 100",
        state=0x0A, cursor=0, slot=0, filter_a=5, filter_b=6,
        counts=[6, 6, 6, 6, 6, 6],
        records=[
            record(-1, 6, 7),
            record(9, 6, 7),
            record(5, 9, 7),
            record(5, 6, 100),
            record(5, 6, 99, 1, 2, 3, 4, 5, b"JOB99"),
        ],
    ))
    cases.append(dict(
        name="scan: object_id 99 is the last accepted id",
        state=0x0A, cursor=0, slot=0, filter_a=5, filter_b=6,
        counts=[1],
        records=[record(5, 6, 99)],
    ))
    cases.append(dict(
        name="scan: re-reads a shrinking record count",
        state=0x0A, cursor=0, slot=0, filter_a=5, filter_b=6,
        counts=[5, 1],
        records=[record(9, 6, 7), record(9, 6, 7)],
    ))
    cases.append(dict(
        name="scan: re-reads a growing record count",
        state=0x0A, cursor=0, slot=0, filter_a=5, filter_b=6,
        counts=[1, 3, 3],
        records=[record(9, 6, 7), record(9, 6, 7), record(5, 6, 8)],
    ))
    cases.append(dict(
        name="scan: skips 23 occupied slots and uses slot 23",
        state=0x0A, cursor=0, slot=0, filter_a=5, filter_b=6,
        counts=[1],
        records=[record(5, 6, 7)],
        slots={index: slot(occupied=1) for index in range(23)},
    ))
    cases.append(dict(
        name="scan: all 24 slots occupied finishes the step",
        state=0x0A, cursor=0, slot=0, filter_a=5, filter_b=6,
        counts=[1],
        records=[record(5, 6, 7)],
        slots={index: slot(occupied=0xFF) for index in range(24)},
    ))
    cases.append(dict(
        name="scan: null record matches a zero filter",
        state=0x0A, cursor=1, slot=0, filter_a=0, filter_b=0,
        counts=[3, 3],
        records=[record(0, 0, 0)],
    ))

    # ---- load state 0x0B ----------------------------------------------
    cases.append(dict(
        name="load: formats the path and stores the model",
        state=0x0B, cursor=1, slot=0, filter_a=5, filter_b=6,
        records=[record(5, 6, 42, 10, 20, 30, 40, 50, b"JOB42")],
        models=[MODEL_ADDR + 0x100],
        slots={0: slot(name=b"PREVIOUS", object_id=1)},
    ))
    cases.append(dict(
        name="load: negative object id keeps the sign extension",
        state=0x0B, cursor=0, slot=5, filter_a=5, filter_b=6,
        records=[record(5, 6, -3, -10, -20, -30, -40, -50, b"NEG")],
        models=[0],
    ))
    cases.append(dict(
        name="load: object id 99 into the last slot clears the name",
        state=0x0B, cursor=0, slot=23, filter_a=5, filter_b=6,
        records=[record(5, 6, 99, 32767, -32768, 0, 1, 2, b"LAST")],
        models=[MODEL_ADDR + 0x180],
        slots={23: slot(name=b"OLD", object_id=7)},
    ))
    cases.append(dict(
        name="load: slot -1 spills before the slot array",
        state=0x0B, cursor=0, slot=-1, filter_a=5, filter_b=6,
        records=[record(5, 6, 7)],
        models=[MODEL_ADDR + 0x1C0],
    ))
    cases.append(dict(
        name="load: null lookup result formats object id 0",
        state=0x0B, cursor=3, slot=2, filter_a=5, filter_b=6,
        records=[],
        models=[MODEL_ADDR + 0x200],
    ))

    # ---- publish state 0x0C -------------------------------------------
    cases.append(dict(
        name="publish: model not ready leaves the state untouched",
        state=0x0C, cursor=0, slot=0, filter_a=5, filter_b=6,
        records=[record(5, 6, 7)],
        slots={0: slot(model=MODEL_ADDR + 0x240, object_id=7)},
        ready={MODEL_ADDR + 0x240: 0},
    ))
    cases.append(dict(
        name="publish: model ready publishes positions and count",
        state=0x0C, cursor=4, slot=2, filter_a=5, filter_b=6,
        loaded=9,
        records=[record(5, 6, 7, 10, -20, 30, 400, 50)],
        slots={2: slot(model=MODEL_ADDR + 0x280, object_id=7)},
    ))
    cases.append(dict(
        name="publish: object 6 uses the alternate height",
        state=0x0C, cursor=0, slot=0, filter_a=5, filter_b=6,
        records=[record(5, 6, 6, 1, 2, 3, 4, 999)],
        slots={0: slot(model=MODEL_ADDR + 0x2C0, object_id=6)},
    ))
    cases.append(dict(
        name="publish: object 7 keeps the record height",
        state=0x0C, cursor=0, slot=0, filter_a=5, filter_b=6,
        records=[record(5, 6, 7, 1, 2, 3, 4, 999)],
        slots={0: slot(model=MODEL_ADDR + 0x300, object_id=7)},
    ))
    cases.append(dict(
        name="publish: non empty name is copied into the slot",
        state=0x0C, cursor=2, slot=1, filter_a=5, filter_b=6,
        records=[record(5, 6, 8, 0, 0, 0, 0, 0, b"OBJ_NAME_8")],
        slots={1: slot(model=MODEL_ADDR + 0x340, object_id=8, name=b"STALE")},
    ))
    cases.append(dict(
        name="publish: empty name is not copied",
        state=0x0C, cursor=2, slot=1, filter_a=5, filter_b=6,
        records=[record(5, 6, 8)],
        slots={1: slot(model=MODEL_ADDR + 0x380, object_id=8, name=b"STALE")},
    ))
    cases.append(dict(
        name="publish: cursor -1 wraps the 16-bit increment to 0",
        state=0x0C, cursor=-1, slot=0, filter_a=5, filter_b=6,
        records=[record(5, 6, 7)],
        slots={0: slot(model=MODEL_ADDR + 0x3C0, object_id=7)},
    ))
    cases.append(dict(
        name="publish: cursor 0x7FFF wraps the 16-bit increment",
        state=0x0C, cursor=0x7FFF, slot=0, filter_a=5, filter_b=6,
        records=[record(5, 6, 7)],
        slots={0: slot(model=MODEL_ADDR + 0x400, object_id=7)},
    ))
    cases.append(dict(
        name="publish: loaded count wraps at 0xFFFFFFFF",
        state=0x0C, cursor=0, slot=0, filter_a=5, filter_b=6,
        loaded=0xFFFFFFFF,
        records=[record(5, 6, 7)],
        slots={0: slot(model=MODEL_ADDR + 0x440, object_id=7)},
    ))
    cases.append(dict(
        name="publish: null model handle stays not ready",
        state=0x0C, cursor=0, slot=3, filter_a=5, filter_b=6,
        records=[record(5, 6, 7)],
        slots={3: slot(model=0, object_id=7)},
    ))
    cases.append(dict(
        name="publish: slot -1 spills before the slot array",
        state=0x0C, cursor=0, slot=-1, filter_a=5, filter_b=6,
        records=[record(5, 6, 7, 1, 2, 3, 4, 5, b"SPILL")],
        slots={-1: slot(model=MODEL_ADDR + 0x480, object_id=7)},
    ))
    return cases


def main():
    print("Testing engine_func_0021e3c0 (0x0021e3c0)...")
    orig = normalise_original_calls(get_orig_bytes())

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_path = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(TU_SOURCE, obj_path, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{result.stderr}")
    candidate, rodata = collect_candidate(obj_path)

    runner = Runner(rodata)
    failures = 0
    cases = build_cases()
    for scenario in cases:
        try:
            original_result = runner.run(orig, scenario)
            candidate_result = runner.run(candidate, scenario)
        except RuntimeError as error:
            failures += 1
            print(f"  [FAIL] {scenario['name']}: {error}")
            continue
        difference = describe_difference(original_result, candidate_result)
        if difference:
            failures += 1
            key, expected, actual = difference
            print(f"  [FAIL] {scenario['name']}: {key}")
            print(f"         original: {expected!r}")
            print(f"         candidate: {actual!r}")
        else:
            print(f"  [PASS] {scenario['name']}")

    # Negative controls: one-instruction mutations of the pinned original must
    # be detected by the same comparison, otherwise the harness is blind.
    controls = [
        # 0x0021E404: mov r5,#0x63 -> #0x62 (failure state)
        (0x0021E404, 0xE3A05063, 0xE3A05062,
         "scan: count <= cursor"),
        # 0x0021E444: cmp r0,#0x64 -> #0x63 (object id limit)
        (0x0021E444, 0xE3500064, 0xE3500063,
         "scan: object_id 99 is the last accepted"),
        # 0x0021E5BC: cmp r0,#6 -> #7 (alternate-height object id)
        (0x0021E5BC, 0xE3500006, 0xE3500007,
         "publish: object 6 uses the alternate height"),
    ]
    for address, original_word, mutated_word, prefix in controls:
        control = bytearray(get_orig_bytes())
        offset = address - FUNC_ADDR
        assert struct.unpack_from("<I", control, offset)[0] == original_word, (
            f"pinned original changed at 0x{address:08x}"
        )
        struct.pack_into("<I", control, offset, mutated_word)
        mutated = normalise_original_calls(bytes(control))
        scenario = next(c for c in cases if c["name"].startswith(prefix))
        try:
            baseline = runner.run(orig, scenario)
            broken = runner.run(mutated, scenario)
            detected = describe_difference(baseline, broken) is not None
        except RuntimeError as error:
            print(f"  [FAIL] negative control 0x{address:08x} crashed: {error}")
            detected = False
        if detected:
            print(f"  [PASS] negative control 0x{address:08x} is detected")
        else:
            failures += 1
            print(f"  [FAIL] negative control 0x{address:08x} was not detected")

    total = len(cases) + len(controls)
    if failures:
        print(f"\n{failures}/{total} differential checks FAILED")
        return 1
    print(f"\nAll {total}/{total} differential checks PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
