#!/usr/bin/env python3
"""Differential test for ui_func_002f4804 (0x002f4804) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the ui_func_002f4804 body,
resolves its three direct calls (0x002C5F7C, 0x002C1D3C, 0x0029705C), the
0x0044EA00 render-register global and the twelve-word color table, then runs the
pinned original (extracted/exefs/code.bin) and the candidate on separate Unicorn
machines with identical fixtures.

Compared outputs per case:
  * continuation PC, final SP, returned r0, callee-saved r4-r11 and d8-d15;
  * the ordered call log: the viewport-command helper arguments, the render-mode
    helper (base, mode), every draw call (four color registers plus the twelve
    single-precision corner registers s0..s11 as raw bit patterns) and every
    indirect flush callback (target address and value);
  * the complete observable 2 MiB data region (color table, records, record
    counter, render-stack nodes, render-register global and the candidate's
    relocated rodata), plus the ordered list of writes outside the private
    stack;
  * an independent Python model of the push/draw/pop sequence that asserts the
    original's call log, returned r0, record counter, both render-stack nodes
    and the final render base.

Helpers are deterministic stubs: 0x002C5F7C reproduces its real bit-building
formula, the flush callback is an ARM `bx lr` stub at one of two addresses, and
0x002C1D3C / 0x0029705C return argument-dependent sentinels.  Some cases make
the stubs mutate the record counter (+0x004BF898), or the flush callback switch
the render-register global to a second stack node, to prove the original's
per-iteration count re-read and its three separate reads of 0x0044EA00.

Coverage: zero/one/two/twelve/thirteen/twenty-four records, negative record
counts, node counts 0..3 (including the flat out-of-bounds slot write at count
3), dirty cleared/set, no flush, a push-only flush (dirty-driven, and through a
callback base switch), and a flush on both ends, two indirect callback targets,
count growth/shrink inside the helper stubs, a render-base switch during the
callback, junk r0-r3 and s1-s15, and record float patterns including signed
zero, NaNs, infinities, denormals and large values.  A lone pop flush cannot
occur for a balanced push/pop: when the push comparison is equal it writes that
same value into the slot the pop later compares against.
Negative controls mutate the color bits, the table entry, the vertical step, the
stack offset, the viewport command, the render mode, the record stride, a draw
argument and the record-count gate; each mutant must be detected.
"""

from __future__ import annotations

import math
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
OUT_DIR = ROOT / "build/test_leaf_002f4804"

FUNC_ADDR = 0x002F4804
FUNC_SIZE = 416

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers 0x2F4804 and the stub at 0x29705C
DATA_ADDR = 0x00400000
DATA_SIZE = 0x00200000  # table, global, records, render nodes, candidate rodata
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
CALLBACK_PAGE = 0x90001000
CALLBACK_A = 0x90001000
CALLBACK_B = 0x90001010

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Pinned data addresses used by the original image.
TABLE_ADDR = 0x004049B4
TABLE_BYTES = 0x30
GLOBAL_ADDR = 0x0044EA00
RECORD_BASE = 0x004BE698
RECORD_STRIDE = 0x20
RECORD_CAPACITY = 0x1200 // RECORD_STRIDE  # 144 records up to 0x004BF898
COUNT_ADDR = 0x004BF898
RENDER_BASE_1 = 0x00500000
RENDER_BASE_2 = 0x00540000
RENDER_STACK_OFFSET = 0x124C
CAND_RODATA = 0x005F0000

VIEWPORT_HELPER = 0x002C5F7C
RENDER_MODE_HELPER = 0x002C1D3C
DRAW_HELPER = 0x0029705C

STUB_NAMES = {
    VIEWPORT_HELPER: "ui_func_002c5f7c",
    RENDER_MODE_HELPER: "ui_func_002c1d3c",
    DRAW_HELPER: "func_0029705c",
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
    "d8": 0x1122334455667788,
    "d9": 0x2233445566778899,
    "d10": 0x33445566778899AA,
    "d11": 0x445566778899AABB,
    "d12": 0x5566778899AABBCC,
    "d13": 0x66778899AABBCCDD,
    "d14": 0x778899AABBCCDDEE,
    "d15": 0x8899AABBCCDDEEFF,
}
S_SCRATCH_START = {
    "s1": 0x3F800000,
    "s2": 0xBF800000,
    "s3": 0x40000000,
    "s4": 0xC0000000,
    "s5": 0x3F000000,
    "s6": 0xBF000000,
    "s7": 0x40400000,
    "s8": 0xC0400000,
    "s9": 0x40800000,
    "s10": 0xC0800000,
    "s11": 0x40A00000,
    "s12": 0xC0A00000,
    "s13": 0x40C00000,
    "s14": 0xC0C00000,
    "s15": 0x40E00000,
}

BX_LR = 0xE12FFF1E


# ---------------------------------------------------------------------------
# Float helpers
# ---------------------------------------------------------------------------
def bits_to_float(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def float_to_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def f32(value: float) -> float:
    """Round a Python double to single precision."""
    if value != value or math.isinf(value):
        return value
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_bits(bits: int) -> int:
    """Correctly-rounded binary32 sum with 100.0f (double holds the sum exactly
    for single-precision inputs, so double-then-single does not double-round).

    A NaN operand is propagated and quieted, matching the VFP `vadd.f32`
    result observed for the fixture payloads.
    """
    value = bits_to_float(bits)
    if value != value:
        return (bits | 0x00400000) & 0xFFFFFFFF
    if math.isinf(value):
        return float_to_bits(value)
    result = value + 100.0
    if math.isinf(result) or abs(result) > 3.4028234663852886e38:
        return float_to_bits(math.copysign(float("inf"), result))
    return float_to_bits(result)


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def pinned_table() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(TABLE_ADDR - 0x00100000)
        return f.read(TABLE_BYTES)


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
    candidate = funcs.get("ui_func_002f4804")
    if candidate is None:
        raise RuntimeError(
            f"ui_func_002f4804 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = None
            for address, name in STUB_NAMES.items():
                if name == rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into(
                "<I",
                code,
                rel.offset,
                (original & 0xFF000000) | (displacement & 0x00FFFFFF),
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if "g_RenderRegisterBase" in rel.symbol_name:
                if addend != 0:
                    raise RuntimeError(
                        f"unexpected render-base addend 0x{addend:08x}"
                    )
                struct.pack_into("<I", code, rel.offset, GLOBAL_ADDR)
            elif rel.symbol_name == "":
                struct.pack_into("<I", code, rel.offset, CAND_RODATA + addend)
            else:
                raise RuntimeError(f"unsupported abs32 relocation: {rel}")
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")

    rodata = elf_sections(obj_file).get(".rodata", b"")
    if len(rodata) < TABLE_BYTES:
        raise RuntimeError(f"candidate .rodata is only {len(rodata)} bytes")
    return bytes(code), rodata


def compile_candidate(src: Path, obj: Path) -> tuple[bytes, bytes]:
    obj.parent.mkdir(parents=True, exist_ok=True)
    result = compile_tu_armv6k(src, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compilation failed for {src}:\n{result.stderr}")
    return relocate_candidate(obj)


def compile_candidate_baseline() -> tuple[bytes, bytes]:
    return compile_candidate(SOURCE, OUT_DIR / "leaf_batch41_c.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant = OUT_DIR / f"mutant_{name}.cpp"
    mutant.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Fixtures and model
# ---------------------------------------------------------------------------
def s32(value: int) -> int:
    return value - (1 << 32) if value & 0x80000000 else value


def default_record_bits(index: int) -> tuple[int, int, int, int]:
    return (
        float_to_bits(f32(0.25 + 1.5 * index)),
        float_to_bits(f32(-1.0 - 0.5 * index)),
        float_to_bits(f32(3.5 * index)),
        float_to_bits(f32(1000.0 - index)),
    )


def record_bits(case: dict, index: int) -> tuple[int, int, int, int]:
    custom = case.get("record_bits")
    if custom is not None:
        return custom[index % len(custom)]
    return default_record_bits(index)


def build_records(case: dict) -> bytes:
    page = bytearray(RECORD_CAPACITY * RECORD_STRIDE)
    for index in range(RECORD_CAPACITY):
        base = index * RECORD_STRIDE
        fields = record_bits(case, index)
        struct.pack_into("<I", page, base + 0x00, fields[0])
        struct.pack_into("<I", page, base + 0x08, fields[1])
        struct.pack_into("<I", page, base + 0x0C, fields[2])
        struct.pack_into("<I", page, base + 0x14, fields[3])
        struct.pack_into("<I", page, base + 0x04, 0xA5A50000 | index)
        struct.pack_into("<I", page, base + 0x10, 0xB6B60000 | index)
        struct.pack_into("<I", page, base + 0x18, 0xC7C70000 | index)
        struct.pack_into("<I", page, base + 0x1C, 0xD8D80000 | index)
    return bytes(page)


def node_spec(case: dict, which: int) -> dict:
    prefix = "node1" if which == 1 else "node2"
    callback = CALLBACK_A if case["callback"] == "A" else CALLBACK_B
    return {
        "count": case[f"{prefix}_count"],
        "slots": case[f"{prefix}_slots"],
        "dirty": case[f"{prefix}_dirty"],
        "callback": case.get(f"{prefix}_callback", callback),
    }


def build_node(spec: dict) -> bytes:
    buffer = bytearray(0x40)
    struct.pack_into("<I", buffer, 0x00, spec["count"] & 0xFFFFFFFF)
    for index, word in enumerate(spec["slots"]):
        struct.pack_into("<I", buffer, 0x08 + 4 * index, word & 0xFFFFFFFF)
    buffer[0x18] = spec["dirty"] & 0xFF
    struct.pack_into("<I", buffer, 0x1C, spec["callback"] & 0xFFFFFFFF)
    return bytes(buffer)


def viewport_command(kind: int, enabled: int) -> int:
    selector = 0 if kind == 1 else 1
    word = selector | ((kind << 4) & 0xFFFFFFFF)
    high = 0x1000 if (enabled & 0xFFFFFFFF) != 0 else 0
    return (high | word | 0xF00) & 0xFFFFFFFF


def callback_return(callback: int, value: int) -> int:
    if callback == CALLBACK_A:
        return (0xCBA5A500 ^ value) & 0xFFFFFFFF
    if callback == CALLBACK_B:
        return (0xCBA5B500 ^ value) & 0xFFFFFFFF
    raise AssertionError(f"unknown callback target 0x{callback:08x}")


class ModelState:
    def __init__(self, case: dict) -> None:
        self.case = case
        self.count = case["record_count"] & 0xFFFFFFFF
        self.base = RENDER_BASE_1 if case["base"] == "1" else RENDER_BASE_2
        self.nodes = {
            RENDER_BASE_1: bytearray(build_node(node_spec(case, 1))),
            RENDER_BASE_2: bytearray(build_node(node_spec(case, 2))),
        }
        self.log: list = []
        self.draw_calls = 0

    # -- little helpers mirroring the flat ARM accesses ---------------------
    @staticmethod
    def read32(buffer: bytearray, offset: int) -> int:
        return struct.unpack_from("<I", buffer, offset & 0xFFFFFFFF)[0]

    @staticmethod
    def write32(buffer: bytearray, offset: int, value: int) -> None:
        struct.pack_into("<I", buffer, offset & 0xFFFFFFFF, value & 0xFFFFFFFF)

    def node(self) -> bytearray:
        return self.nodes[self.base]

    def flush(self, node: bytearray, value: int) -> int:
        callback = self.read32(node, 0x1C)
        self.log.append(("flush", callback, value))
        if self.case.get("switch_base_on_callback"):
            self.base = RENDER_BASE_2
        node[0x18] = 0
        return callback_return(callback, value)

    def maybe_flush(self, node: bytearray, previous: int, value: int):
        if node[0x18] != 0 or previous != value:
            return self.flush(node, value)
        return None

    def signed_count(self) -> int:
        return s32(self.count)

    def grow(self, new_count: int) -> None:
        self.count = new_count & 0xFFFFFFFF

    # -- the recovered algorithm --------------------------------------------
    def run(self) -> dict:
        if self.count == 0:
            return {
                "log": [],
                "ret": 0,
                "count": self.count,
                "base": self.base,
                "nodes": self.nodes,
            }

        pushed = viewport_command(5, 1)
        self.log.append(("ui_func_002c5f7c", 5, 1))
        if self.case.get("grow_on_viewport") is not None:
            self.grow(self.case["grow_on_viewport"])

        node = self.node()
        count = self.read32(node, 0x00)
        previous = self.read32(node, 0x08 + 4 * count)
        self.write32(node, 0x00, count + 1)
        self.write32(node, 0x08 + 4 * ((count + 1) & 0xFFFFFFFF), pushed)
        self.maybe_flush(node, previous, pushed)

        self.log.append(("ui_func_002c1d3c", self.base, 0))
        draw_y = f32_bits(self.case["vertical_offset"])

        index = 0
        while index < self.signed_count():
            x_lo, z_lo, z_hi, x_hi = record_bits(self.case, index)
            color = (
                struct.unpack_from(
                    "<I", pinned_table(), 4 * (index % 12)
                )[0]
                | 0x70
            )
            self.log.append(
                (
                    "func_0029705c",
                    color,
                    color,
                    color,
                    color,
                    x_lo,
                    draw_y,
                    z_lo,
                    x_lo,
                    draw_y,
                    x_hi,
                    z_hi,
                    draw_y,
                    z_lo,
                    z_hi,
                    draw_y,
                    x_hi,
                )
            )
            self.draw_calls += 1
            if self.case.get("grow_on_draw") is not None:
                cap = self.case["grow_on_draw"]
                if s32(self.count) < cap:
                    self.grow(self.count + 1)
            if self.case.get("shrink_on_draw") is not None:
                self.grow(self.case["shrink_on_draw"])
            index += 1

        node = self.node()
        count = self.read32(node, 0x00)
        previous = self.read32(node, 0x08 + 4 * count)
        self.write32(node, 0x00, count - 1)
        new_top = self.read32(node, 0x08 + 4 * ((count - 1) & 0xFFFFFFFF))
        flushed = self.maybe_flush(node, previous, new_top)
        ret = new_top if flushed is None else flushed

        return {
            "log": self.log,
            "ret": ret,
            "count": self.count,
            "base": self.base,
            "nodes": self.nodes,
        }


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    """One Unicorn machine with deterministic stubs at the original addresses."""

    def __init__(self, rodata: bytes | None = None) -> None:
        self.rodata = pinned_table() if rodata is None else rodata
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_map(CALLBACK_PAGE, 0x1000)

        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", BX_LR))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_helper, begin=address, end=address
            )
        for address in (CALLBACK_A, CALLBACK_B):
            self.uc.mem_write(address, struct.pack("<I", BX_LR))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_callback, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.grow_on_viewport = None
        self.grow_on_draw = None
        self.shrink_on_draw = None
        self.switch_base = False

    # -------------------------------------------------------------- stubs
    def _fp_bits(self) -> tuple[int, ...]:
        return tuple(
            self.uc.reg_read(getattr(arm, f"UC_ARM_REG_S{index}"))
            for index in range(12)
        )

    def _on_helper(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == VIEWPORT_HELPER:
            self.call_log.append(("ui_func_002c5f7c", r0, r1))
            result = viewport_command(r0, r1)
            if self.grow_on_viewport is not None:
                write_u32(uc, COUNT_ADDR, self.grow_on_viewport)
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == RENDER_MODE_HELPER:
            self.call_log.append(("ui_func_002c1d3c", r0, r1))
            uc.reg_write(
                arm.UC_ARM_REG_R0, (0x2C1D0000 ^ r0 ^ (r1 << 8)) & 0xFFFFFFFF
            )
        elif address == DRAW_HELPER:
            self.call_log.append(("func_0029705c", r0, r1, r2, r3) + self._fp_bits())
            if self.grow_on_draw is not None:
                current = s32(read_u32(uc, COUNT_ADDR))
                if current < self.grow_on_draw:
                    write_u32(uc, COUNT_ADDR, current + 1)
            if self.shrink_on_draw is not None:
                write_u32(uc, COUNT_ADDR, self.shrink_on_draw)
            uc.reg_write(arm.UC_ARM_REG_R0, 0xD00D0000 ^ r0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_callback(self, uc, address: int, size: int, user_data) -> None:
        value = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("flush", address, value))
        if self.switch_base:
            write_u32(uc, GLOBAL_ADDR, RENDER_BASE_2)
        uc.reg_write(arm.UC_ARM_REG_R0, callback_return(address, value))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
            self.writes.append((address, size, value & ((1 << (8 * size)) - 1)))

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        uc = self.uc
        self.call_log = []
        self.writes = []
        self.case = case
        self.grow_on_viewport = case.get("grow_on_viewport")
        self.grow_on_draw = case.get("grow_on_draw")
        self.shrink_on_draw = case.get("shrink_on_draw")
        self.switch_base = case.get("switch_base_on_callback", False)

        uc.mem_write(DATA_ADDR, b"\xCC" * DATA_SIZE)
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.mem_write(FUNC_ADDR, b"\x00" * FUNC_SIZE)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(TABLE_ADDR, pinned_table())
        uc.mem_write(CAND_RODATA, self.rodata)
        uc.mem_write(GLOBAL_ADDR, struct.pack("<I", case_render_base(case)))
        uc.mem_write(RECORD_BASE, build_records(case))
        write_u32(uc, COUNT_ADDR, case["record_count"])
        for which, base in ((1, RENDER_BASE_1), (2, RENDER_BASE_2)):
            uc.mem_write(base + RENDER_STACK_OFFSET, build_node(node_spec(case, which)))
        uc.ctl_flush_tb()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, case["junk"][0])
        uc.reg_write(arm.UC_ARM_REG_R1, case["junk"][1])
        uc.reg_write(arm.UC_ARM_REG_R2, case["junk"][2])
        uc.reg_write(arm.UC_ARM_REG_R3, case["junk"][3])
        uc.reg_write(arm.UC_ARM_REG_S0, case["vertical_offset"])
        for name, value in S_SCRATCH_START.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), value)
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)
        for name, value in VFP_SAVED_START.items():
            uc.reg_write(VFP_SAVED[name], value)

        self.writes = []
        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "vfp_saved": {
                name: uc.reg_read(reg) for name, reg in VFP_SAVED.items()
            },
            "call_log": list(self.call_log),
            "writes": list(self.writes),
            "data": bytes(uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "count": read_u32(uc, COUNT_ADDR),
            "base": read_u32(uc, GLOBAL_ADDR),
            "nodes": {
                1: bytes(uc.mem_read(RENDER_BASE_1 + RENDER_STACK_OFFSET, 0x40)),
                2: bytes(uc.mem_read(RENDER_BASE_2 + RENDER_STACK_OFFSET, 0x40)),
            },
            "records": bytes(uc.mem_read(RECORD_BASE, 0x1200)),
            "table": bytes(uc.mem_read(TABLE_ADDR, TABLE_BYTES)),
            "cand_rodata": bytes(uc.mem_read(CAND_RODATA, TABLE_BYTES)),
        }


def case_render_base(case: dict) -> int:
    return RENDER_BASE_1 if case["base"] == "1" else RENDER_BASE_2


def write_u32(uc, address: int, value: int) -> None:
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "record_count": 1,
        "vertical_offset": float_to_bits(1.5),
        "junk": (0x11111111, 0x22222222, 0x33333333, 0x44444444),
        "base": "1",
        "callback": "A",
        "node1_count": 0,
        "node1_slots": (0x1F51, 0xDEAD0001, 0xDEAD0002, 0xDEAD0003),
        "node1_dirty": 0,
        "node2_count": 1,
        "node2_slots": (0x51515151, 0x1F51, 0xDEAD0004, 0xDEAD0005),
        "node2_dirty": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- zero records: the early exit must touch nothing --------------------
    cases.append(base_case("zero records", record_count=0))
    cases.append(
        base_case(
            "zero records, dirty node and junk registers",
            record_count=0,
            node1_dirty=1,
            junk=(0xDEADBEEF, 0xFFFFFFFF, 0x80000000, 0),
        )
    )

    # --- push/pop callback matrix ------------------------------------------
    cases.append(
        base_case(
            "one record, slot0 equals pushed word (no flush)",
            node1_slots=(0x1F51, 0xDEAD0001, 0xDEAD0002, 0xDEAD0003),
        )
    )
    cases.append(
        base_case(
            "push flush and pop flush (slot0 differs)",
            node1_slots=(0x11111111, 0x1F51, 0x22222222, 0x33333333),
        )
    )
    cases.append(
        base_case(
            "push flush and pop flush (all slots distinct)",
            node1_slots=(0x11111111, 0x22222222, 0x33333333, 0x44444444),
        )
    )
    cases.append(
        base_case(
            "dirty forces push flush, pop compares equal (push only)",
            node1_dirty=1,
            node1_slots=(0x1F51, 0x1F51, 0x33333333, 0x44444444),
        )
    )
    cases.append(
        base_case(
            "dirty push flush then base switch, node 2 pop is clean",
            node1_dirty=1,
            node1_slots=(0x1F51, 0x1F51, 0x33333333, 0x44444444),
            switch_base_on_callback=True,
            node2_count=1,
            node2_slots=(0x51515151, 0x51515151, 0x53535353, 0x54545454),
        )
    )
    for count in (1, 2, 3):
        cases.append(
            base_case(
                f"node count {count}",
                node1_count=count,
                node1_slots=(0xAAAA0000 + count, 0xBBBB0000, 0xCCCC0000, 0xDDDD0000),
            )
        )

    # --- indirect callback targets ----------------------------------------
    cases.append(
        base_case(
            "callback target B",
            callback="B",
            node1_slots=(0x11111111, 0x22222222, 0x33333333, 0x44444444),
        )
    )
    cases.append(
        base_case(
            "callback target B on dirty push only",
            callback="B",
            node1_dirty=1,
            node1_slots=(0x1F51, 0x1F51, 0x33333333, 0x44444444),
        )
    )

    # --- record counts, modulo-12 cycling and table coverage --------------
    for count in (2, 12, 13, 24):
        cases.append(base_case(f"{count} records", record_count=count))

    # --- signed record-count bounds ---------------------------------------
    for raw in (0xFFFFFFFF, 0x80000000, 0xFFFFFFFE):
        cases.append(
            base_case(f"negative record count 0x{raw:08x}", record_count=raw)
        )

    # --- helper stubs mutate the live record counter ----------------------
    cases.append(
        base_case(
            "viewport helper grows count 1 -> 3",
            record_count=1,
            grow_on_viewport=3,
        )
    )
    cases.append(
        base_case(
            "draw helper grows count 2 -> 4",
            record_count=2,
            grow_on_draw=4,
        )
    )
    cases.append(
        base_case(
            "draw helper shrinks count to 1",
            record_count=5,
            shrink_on_draw=1,
        )
    )

    # --- render-base switch inside the push callback ----------------------
    cases.append(
        base_case(
            "callback switches render base, pop uses node 2",
            node1_slots=(0x11111111, 0x22222222, 0x33333333, 0x44444444),
            switch_base_on_callback=True,
            node2_count=1,
            node2_slots=(0x51515151, 0x52525252, 0x53535353, 0x54545454),
        )
    )
    cases.append(
        base_case(
            "switch base with dirty node 2",
            node1_slots=(0x1F51, 0x1F51, 0x33333333, 0x44444444),
            switch_base_on_callback=True,
            node2_count=2,
            node2_dirty=1,
            node2_slots=(0x61616161, 0x62626262, 0x63636363, 0x64646464),
        )
    )

    # --- float payloads and vertical offsets ------------------------------
    special = [
        (0x80000000, 0x7F800000, 0xFFC00000, 0x00000001),
        (0x00000000, 0xFF800000, 0x7FC00001, 0x807FFFFF),
        (0x7F7FFFFF, 0x00800000, 0x80000001, 0x3F800000),
    ]
    for index, offsets in enumerate(
        (0x00000000, 0x80000000, float_to_bits(1e30), 0x7FC00000, 0x7F800000, 0xFF800000)
    ):
        cases.append(
            base_case(
                f"special payloads, vertical offset 0x{offsets:08x}",
                record_count=3,
                vertical_offset=offsets,
                record_bits=special,
            )
        )
    cases.append(
        base_case(
            "junk registers ignored",
            record_count=2,
            junk=(0xCAFEBABE, 0x9ABCDEF0, 0x12345678, 0xFFFFFFFF),
        )
    )
    cases.append(
        base_case(
            "combined: dirty push, wrap offsets, count 13",
            record_count=13,
            node1_count=2,
            node1_dirty=1,
            node1_slots=(0x77777777, 0x1F51, 0x1F51, 0x88888888),
            vertical_offset=0xC2C80000,
            junk=(0, 0, 0, 0),
        )
    )
    return cases


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("pc", "sp", "callee_saved", "vfp_saved", "call_log", "ret"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["writes"] != cand["writes"]:
        problems.append(
            "writes:\n    orig=" + repr(orig["writes"]) + "\n    cand="
            + repr(cand["writes"])
        )
    if orig["data"] != cand["data"]:
        for index in range(0, len(orig["data"]), 4):
            if orig["data"][index : index + 4] != cand["data"][index : index + 4]:
                problems.append(
                    f"data differs first at 0x{DATA_ADDR + index:08x}: "
                    f"orig={orig['data'][index:index + 4].hex()} "
                    f"cand={cand['data'][index:index + 4].hex()}"
                )
                break
    for key in ("count", "base", "nodes", "records", "table", "cand_rodata"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    return problems


def check_expectations(case: dict, result: dict, model: dict) -> None:
    name = case["name"]
    assert result["pc"] == TRAP_ADDR, f"did not return on {name}"
    assert result["sp"] == ENTRY_SP, f"SP not restored on {name}"
    assert result["callee_saved"] == CALLEE_SAVED_START, (
        f"callee-saved registers clobbered on {name}: {result['callee_saved']}"
    )
    assert result["vfp_saved"] == VFP_SAVED_START, (
        f"VFP callee-saved registers clobbered on {name}: {result['vfp_saved']}"
    )

    assert result["call_log"] == model["log"], (
        f"call log differs from model on {name}:\n"
        f"    actual={result['call_log']!r}\n    model={model['log']!r}"
    )
    assert result["ret"] == model["ret"], (
        f"r0 differs from model on {name}: "
        f"0x{result['ret']:08x} != 0x{model['ret']:08x}"
    )
    assert result["count"] == model["count"], (
        f"record count differs from model on {name}"
    )
    assert result["base"] == model["base"], f"render base differs from model on {name}"
    for which in (1, 2):
        expected = bytes(model["nodes"][
            RENDER_BASE_1 if which == 1 else RENDER_BASE_2
        ])
        assert result["nodes"][which] == expected, (
            f"render-stack node {which} differs from model on {name}:\n"
            f"    actual={result['nodes'][which].hex()}\n    model={expected.hex()}"
        )
    assert result["records"] == build_records(case), (
        f"record page was modified on {name}"
    )
    assert result["table"] == pinned_table(), f"color table modified on {name}"
    assert result["cand_rodata"] == pinned_table(), (
        f"candidate rodata modified on {name}"
    )


def run_case_set(
    orig_code, cand_code, cand_rodata, cases, orig_machine, cand_machine
) -> int:
    passed = 0
    for case in cases:
        orig = orig_machine.run(orig_code, case)
        cand = cand_machine.run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        check_expectations(case, orig, ModelState(case).run())
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing ui_func_002f4804 (0x002f4804)...")
    orig_code = get_orig_bytes()
    cand_code, cand_rodata = compile_candidate_baseline()
    print(
        f"  original: {len(orig_code)} B, candidate: {len(cand_code)} B, "
        f"rodata: {len(cand_rodata)} B (relocations resolved)"
    )
    assert cand_rodata == pinned_table()

    cases = make_cases()
    orig_machine = Machine()
    cand_machine = Machine()
    passed = run_case_set(
        orig_code, cand_code, cand_rodata, cases, orig_machine, cand_machine
    )

    print("\nNegative controls:")
    for name, old, new in (
        (
            "color_command_bits",
            "constexpr u32 kColorCommandBits = 0x70;",
            "constexpr u32 kColorCommandBits = 0x71;",
        ),
        (
            "color_table_entry",
            "0xFF000000, 0x00FF0000, 0xFFFF0000, 0x0000FF00,",
            "0xFF000001, 0x00FF0000, 0xFFFF0000, 0x0000FF00,",
        ),
        (
            "vertical_step",
            "constexpr f32 kVerticalStep = 100.0f;",
            "constexpr f32 kVerticalStep = 101.0f;",
        ),
        (
            "render_stack_offset",
            "constexpr u32 kRenderStackOffset = 0x124C;",
            "constexpr u32 kRenderStackOffset = 0x1250;",
        ),
        (
            "viewport_command",
            "constexpr u32 kViewportCommand = 5;",
            "constexpr u32 kViewportCommand = 6;",
        ),
        (
            "render_mode",
            "constexpr u32 kRenderMode = 0;",
            "constexpr u32 kRenderMode = 1;",
        ),
        (
            "record_stride",
            "constexpr u32 kRecordStride = 0x20;",
            "constexpr u32 kRecordStride = 0x40;",
        ),
        (
            "draw_corner",
            "z_hi, draw_y, z_lo,\n                      z_hi, draw_y, x_hi);",
            "z_hi, draw_y, x_hi,\n                      z_hi, draw_y, x_hi);",
        ),
        (
            "color_cycle",
            "kColorTable[static_cast<u32>(index) % kColorCount] |",
            "kColorTable[static_cast<u32>(index) % 11] |",
        ),
        (
            "record_gate",
            "if (load_record_count() == 0) {",
            "if (load_record_count() <= 0) {",
        ),
    ):
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        mutant_machine = Machine(mutant_rodata)
        detected = False
        for case in cases:
            orig = orig_machine.run(orig_code, case)
            try:
                bad = mutant_machine.run(mutant_code, case)
            except RuntimeError:
                # A mutant that faults is observably different from the
                # original, which completes every case.
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
