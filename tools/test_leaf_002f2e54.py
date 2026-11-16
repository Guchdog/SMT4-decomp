#!/usr/bin/env python3
"""Differential test for ui_func_002f2e54 (0x002f2e54) using Unicorn ARM.

Compiles ``src/engine/leaf_batch41_c.cpp``, extracts the ``ui_func_002f2e54``
body, resolves its four direct calls (0x002C5F7C, 0x002C1D3C, 0x002C0B1C and
0x002100F8) plus the 0x0044EA00 render-register global, and runs the pinned
original (``extracted/exefs/code.bin``) against the candidate on separate Unicorn
machines with identical fixtures.

Compared observables per case:
  * continuation PC, final SP, returned r0, callee-saved r4-r11 and d8-d15;
  * the caller's two stack argument words (must stay untouched);
  * the ordered call log: the viewport helper arguments, the render-mode helper
    (base, mode), both draw calls (four colour registers plus the raw bits of
    s0..s4 / s0..s5) and every indirect flush callback (target address, value);
  * the complete observable 2 MiB data region (render-stack nodes, the
    0x0044EA00 global, the 0x004724CC bias pair and every other byte), plus the
    ordered list of writes outside the private stack;
  * an independent Python model of the capture/push/draw/pop sequence that
    asserts the original's call log, returned r0, both render-stack nodes, the
    render base, the bias pair and the stack arguments.

Helpers are deterministic stubs: 0x002C5F7C reproduces its real bit-building
formula, the flush callback is an ARM ``bx lr`` stub at one of two addresses,
and 0x002C1D3C / 0x002C0B1C / 0x002100F8 return argument-dependent sentinels.
Several cases let the stubs switch the render-register global (during the
viewport helper, the mode helper or the push callback) and rewrite the
0x004724CC bias pair during the viewport helper, to prove the original's
capture-before-helper order and its separate reads of 0x0044EA00 for the push,
the mode call and the pop.

Coverage: both draw words zero / one non-zero / both non-zero; top-byte
boundaries 0x00FFFFFF, 0x01000000, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF; node
counts 0..3 including the count == 3 flat store that lands on the dirty word
(the dirty byte then observes the pushed low byte); dirty-forced and
previous-difference flushes; two indirect callback targets; base switches at
every helper; bias values 0, +/-0.5, 0.75/-1.25, 1e30, NaN, -inf; signed
coordinate boundaries including INT_MIN/INT_MAX saturation; and coordinates
chosen so that truncation crosses zero.  Negative controls mutate the push
kind/enable, render mode, stack offset, both literal floats, the bias address,
the alpha guard, a draw argument and the pop return value; each mutant must be
detected.
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
OUT_DIR = ROOT / "build/test_leaf_002f2e54"

FUNC_ADDR = 0x002F2E54
FUNC_SIZE = 440

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers 0x2F2E54 and every stub below 0x300000
DATA_ADDR = 0x00400000
DATA_SIZE = 0x00200000  # global, bias pair and both render nodes
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
CALLBACK_PAGE = 0x90001000
CALLBACK_A = 0x90001000
CALLBACK_B = 0x90001010

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

GLOBAL_ADDR = 0x0044EA00
BIAS_ADDR = 0x004724CC
RENDER_BASE_1 = 0x00500000
RENDER_BASE_2 = 0x00540000
RENDER_STACK_OFFSET = 0x124C

VIEWPORT_HELPER = 0x002C5F7C
RENDER_MODE_HELPER = 0x002C1D3C
FIRST_DRAW_HELPER = 0x002C0B1C
SECOND_DRAW_HELPER = 0x002100F8

STUB_NAMES = {
    VIEWPORT_HELPER: "ui_func_002c5f7c",
    RENDER_MODE_HELPER: "ui_func_002c1d3c",
    FIRST_DRAW_HELPER: "ui_func_002c0b1c",
    SECOND_DRAW_HELPER: "ui_func_002100f8",
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
    "s0": 0x3F800000,
    "s1": 0xBF800000,
    "s2": 0x40000000,
    "s3": 0xC0000000,
    "s4": 0x3F000000,
    "s5": 0xBF000000,
    "s6": 0x40400000,
    "s7": 0xC0400000,
    "s8": 0x40800000,
    "s9": 0xC0800000,
    "s10": 0x40A00000,
    "s11": 0xC0A00000,
    "s12": 0x40C00000,
    "s13": 0xC0C00000,
    "s14": 0x40E00000,
    "s15": 0xC0E00000,
}

BX_LR = 0xE12FFF1E


# ---------------------------------------------------------------------------
# Float helpers and the ARM conversion semantics
# ---------------------------------------------------------------------------
def bits_to_float(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def float_to_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def f32(value: float) -> float:
    """Round a Python double to single precision (RNE)."""
    if value != value or math.isinf(value):
        return value
    return struct.unpack("<f", struct.pack("<f", value))[0]


def arm_vcvt_f32_s32(value: int) -> float:
    """vcvt.f32.s32: exact round-to-nearest-even conversion of a s32."""
    return f32(float(value))


def arm_vcvt_s32_f32(value: float) -> int:
    """vcvt.s32.f32: truncation toward zero with ARM saturation and NaN -> 0."""
    if value != value:
        return 0
    if math.isinf(value):
        return 0x7FFFFFFF if value > 0 else 0x80000000
    truncated = math.trunc(value)
    if truncated > 0x7FFFFFFF:
        return 0x7FFFFFFF
    if truncated < -0x80000000:
        return 0x80000000
    return truncated & 0xFFFFFFFF


def biased_coordinate(value: int, bias_bits: int) -> int:
    """The 0x2F2E74..0x2F2EA0 vcvt/vadd/vcvt chain."""
    total = f32(arm_vcvt_f32_s32(value) + bits_to_float(bias_bits))
    return arm_vcvt_s32_f32(total)


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & 0x80000000 else value


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("ui_func_002f2e54")
    if candidate is None:
        raise RuntimeError(
            f"ui_func_002f2e54 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):  # PC24 / CALL / JUMP24
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
            if "g_RenderRegisterBase" not in rel.symbol_name:
                raise RuntimeError(f"unsupported abs32 relocation: {rel}")
            if addend != 0:
                raise RuntimeError(f"unexpected render-base addend 0x{addend:08x}")
            struct.pack_into("<I", code, rel.offset, GLOBAL_ADDR)
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")

    return bytes(code)


def compile_candidate(src: Path, obj: Path) -> bytes:
    obj.parent.mkdir(parents=True, exist_ok=True)
    result = compile_tu_armv6k(src, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compilation failed for {src}:\n{result.stderr}")
    return relocate_candidate(obj)


def compile_candidate_baseline() -> bytes:
    return compile_candidate(SOURCE, OUT_DIR / "leaf_batch41_c.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant = OUT_DIR / f"mutant_{name}.cpp"
    mutant.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Fixtures and the independent model
# ---------------------------------------------------------------------------
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


def build_node(spec: dict) -> bytes:
    buffer = bytearray(0x40)
    struct.pack_into("<I", buffer, 0x00, spec["count"] & 0xFFFFFFFF)
    for index, word in enumerate(spec["slots"]):
        struct.pack_into("<I", buffer, 0x08 + 4 * index, word & 0xFFFFFFFF)
    buffer[0x18] = spec["dirty"] & 0xFF
    struct.pack_into("<I", buffer, 0x1C, spec["callback"] & 0xFFFFFFFF)
    return bytes(buffer)


def node_spec(case: dict, which: int) -> dict:
    prefix = "node1" if which == 1 else "node2"
    callback = CALLBACK_A if case["callback"] == "A" else CALLBACK_B
    return {
        "count": case[f"{prefix}_count"],
        "slots": case[f"{prefix}_slots"],
        "dirty": case[f"{prefix}_dirty"],
        "callback": case.get(f"{prefix}_callback", callback),
    }


def other_base(base: int) -> int:
    return RENDER_BASE_2 if base == RENDER_BASE_1 else RENDER_BASE_1


class ModelState:
    """Independent flat-word model of the recovered ARM contract."""

    def __init__(self, case: dict) -> None:
        self.case = case
        self.global_base = (
            RENDER_BASE_1 if case["base"] == "1" else RENDER_BASE_2
        )
        self.push_base = self.global_base
        self.nodes = {
            RENDER_BASE_1: bytearray(build_node(node_spec(case, 1))),
            RENDER_BASE_2: bytearray(build_node(node_spec(case, 2))),
        }
        self.log: list = []
        self.flush_index = 0

    @staticmethod
    def read32(buffer: bytearray, offset: int) -> int:
        return struct.unpack_from("<I", buffer, offset & 0xFFFFFFFF)[0]

    @staticmethod
    def write32(buffer: bytearray, offset: int, value: int) -> None:
        struct.pack_into("<I", buffer, offset & 0xFFFFFFFF, value & 0xFFFFFFFF)

    def node(self, base: int) -> bytearray:
        return self.nodes[base]

    def flush(self, node: bytearray, value: int) -> int:
        callback = self.read32(node, 0x1C)
        self.log.append(("flush", callback, value))
        if self.case.get("switch_flush") == self.flush_index:
            self.global_base = other_base(self.global_base)
        self.flush_index += 1
        node[0x18] = 0
        return callback_return(callback, value)

    def maybe_flush(self, node: bytearray, previous: int, value: int):
        if node[0x18] != 0 or previous != value:
            return self.flush(node, value)
        return None

    def run(self) -> dict:
        case = self.case
        packed_a = case["packed_a"]
        packed_b = case["packed_b"]

        biased_x = biased_coordinate(s32(case["x"]), case["bias_x"])
        biased_y = biased_coordinate(s32(case["y"]), case["bias_y"])

        # 0x2F2E78: the stack words are captured before the helper calls.
        captured_a = packed_a
        captured_b = packed_b

        pushed = viewport_command(1, 1)
        self.log.append(("ui_func_002c5f7c", 1, 1))
        if case.get("switch_on_viewport"):
            self.global_base = other_base(self.global_base)
        if case.get("rewrite_bias_on_viewport"):
            # Mutates the memory, but both implementations captured the pair
            # before this point, so the draws must use the original bias.
            pass

        node = self.node(self.push_base)
        count = self.read32(node, 0x00)
        previous = self.read32(node, 0x08 + 4 * count)
        self.write32(node, 0x00, count + 1)
        self.write32(node, 0x08 + 4 * ((count + 1) & 0xFFFFFFFF), pushed)
        self.maybe_flush(node, previous, pushed)

        self.log.append(("ui_func_002c1d3c", self.global_base, 0))
        if case.get("switch_on_mode"):
            self.global_base = other_base(self.global_base)

        draw_x = arm_vcvt_f32_s32(s32(biased_x))
        draw_y = arm_vcvt_f32_s32(s32(biased_y))
        draw_width = arm_vcvt_f32_s32(s32(case["width"]))
        draw_height = arm_vcvt_f32_s32(s32(case["height"]))

        if (captured_b >> 24) != 0:
            swapped = int.from_bytes(
                struct.pack("<I", captured_b & 0xFFFFFFFF), "big"
            )
            self.log.append(
                (
                    "ui_func_002c0b1c",
                    swapped,
                    swapped,
                    swapped,
                    swapped,
                    float_to_bits(draw_x),
                    float_to_bits(draw_y),
                    float_to_bits(draw_width),
                    float_to_bits(draw_height),
                    0x00000000,
                )
            )

        if (captured_a >> 24) != 0:
            swapped = int.from_bytes(
                struct.pack("<I", captured_a & 0xFFFFFFFF), "big"
            )
            self.log.append(
                (
                    "ui_func_002100f8",
                    swapped,
                    swapped,
                    swapped,
                    swapped,
                    float_to_bits(draw_x),
                    float_to_bits(draw_y),
                    float_to_bits(draw_width),
                    float_to_bits(draw_height),
                    0x00000000,
                    0x3F800000,
                )
            )

        node = self.node(self.global_base)
        count = self.read32(node, 0x00)
        previous = self.read32(node, 0x08 + 4 * count)
        self.write32(node, 0x00, count - 1)
        new_top = self.read32(node, 0x08 + 4 * ((count - 1) & 0xFFFFFFFF))
        flushed = self.maybe_flush(node, previous, new_top)
        ret = new_top if flushed is None else flushed

        return {
            "log": self.log,
            "ret": ret,
            "global_base": self.global_base,
            "nodes": self.nodes,
        }


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
def write_u32(uc, address: int, value: int) -> None:
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


class Machine:
    """One Unicorn machine with deterministic stubs at the original addresses."""

    def __init__(self) -> None:
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
        self.global_base = RENDER_BASE_1
        self.flush_index = 0

    # -------------------------------------------------------------- stubs
    def _fp_bits(self, count: int) -> tuple:
        return tuple(
            self.uc.reg_read(getattr(arm, f"UC_ARM_REG_S{index}"))
            for index in range(count)
        )

    def _on_helper(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == VIEWPORT_HELPER:
            self.call_log.append(("ui_func_002c5f7c", r0, r1))
            if self.case.get("switch_on_viewport"):
                self.global_base = other_base(self.global_base)
                write_u32(uc, GLOBAL_ADDR, self.global_base)
            if self.case.get("rewrite_bias_on_viewport"):
                write_u32(uc, BIAS_ADDR, self.case["rewrite_bias"][0])
                write_u32(uc, BIAS_ADDR + 4, self.case["rewrite_bias"][1])
            uc.reg_write(arm.UC_ARM_REG_R0, viewport_command(r0, r1))
        elif address == RENDER_MODE_HELPER:
            self.call_log.append(("ui_func_002c1d3c", r0, r1))
            if self.case.get("switch_on_mode"):
                self.global_base = other_base(self.global_base)
                write_u32(uc, GLOBAL_ADDR, self.global_base)
            uc.reg_write(
                arm.UC_ARM_REG_R0, (0x2C1D0000 ^ r0 ^ (r1 << 8)) & 0xFFFFFFFF
            )
        elif address == FIRST_DRAW_HELPER:
            self.call_log.append(
                ("ui_func_002c0b1c", r0, r1, r2, r3) + self._fp_bits(5)
            )
            uc.reg_write(arm.UC_ARM_REG_R0, 0xD00D0001)
        elif address == SECOND_DRAW_HELPER:
            self.call_log.append(
                ("ui_func_002100f8", r0, r1, r2, r3) + self._fp_bits(6)
            )
            uc.reg_write(arm.UC_ARM_REG_R0, 0xD00D0002)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_callback(self, uc, address: int, size: int, user_data) -> None:
        value = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("flush", address, value))
        if self.case.get("switch_flush") == self.flush_index:
            self.global_base = other_base(self.global_base)
            write_u32(uc, GLOBAL_ADDR, self.global_base)
        self.flush_index += 1
        uc.reg_write(arm.UC_ARM_REG_R0, callback_return(address, value))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
            self.writes.append(
                (address, size, value & ((1 << (8 * size)) - 1))
            )

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        uc = self.uc
        self.call_log = []
        self.writes = []
        self.case = case
        self.global_base = RENDER_BASE_1 if case["base"] == "1" else RENDER_BASE_2
        self.flush_index = 0

        uc.mem_write(DATA_ADDR, b"\xCC" * DATA_SIZE)
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.mem_write(FUNC_ADDR, b"\x00" * FUNC_SIZE)
        uc.mem_write(FUNC_ADDR, code)
        write_u32(uc, GLOBAL_ADDR, self.global_base)
        write_u32(uc, BIAS_ADDR, case["bias_x"])
        write_u32(uc, BIAS_ADDR + 4, case["bias_y"])
        for which, base in ((1, RENDER_BASE_1), (2, RENDER_BASE_2)):
            uc.mem_write(
                base + RENDER_STACK_OFFSET, build_node(node_spec(case, which))
            )
        # The caller's outgoing argument area.
        write_u32(uc, ENTRY_SP, case["packed_a"])
        write_u32(uc, ENTRY_SP + 4, case["packed_b"])
        uc.ctl_flush_tb()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, case["x"] & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R1, case["y"] & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R2, case["width"] & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R3, case["height"] & 0xFFFFFFFF)
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
                name: uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "vfp_saved": {
                name: uc.reg_read(register)
                for name, register in VFP_SAVED.items()
            },
            "call_log": list(self.call_log),
            "writes": list(self.writes),
            "data": bytes(uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "stack_args": (
                read_u32(self.uc, ENTRY_SP),
                read_u32(self.uc, ENTRY_SP + 4),
            ),
            "global_base": read_u32(self.uc, GLOBAL_ADDR),
            "bias": (
                read_u32(self.uc, BIAS_ADDR),
                read_u32(self.uc, BIAS_ADDR + 4),
            ),
            "nodes": {
                1: bytes(
                    uc.mem_read(RENDER_BASE_1 + RENDER_STACK_OFFSET, 0x40)
                ),
                2: bytes(
                    uc.mem_read(RENDER_BASE_2 + RENDER_STACK_OFFSET, 0x40)
                ),
            },
        }


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "x": 12,
        "y": -7,
        "width": 33,
        "height": 45,
        "packed_a": 0x80FFFFFF,
        "packed_b": 0x40112233,
        "bias_x": float_to_bits(0.5),
        "bias_y": float_to_bits(0.5),
        "base": "1",
        "callback": "A",
        "node1_count": 0,
        "node1_slots": (0x1F10, 0x1F10, 0xDEAD0002, 0xDEAD0003),
        "node1_dirty": 0,
        "node2_count": 1,
        "node2_slots": (0x51515151, 0x1F10, 0xDEAD0004, 0xDEAD0005),
        "node2_dirty": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list:
    cases: list = []

    # --- both draws, no flush, then the dirty/previous matrix -------------
    cases.append(base_case("both draws, no flush"))
    cases.append(
        base_case(
            "dirty push flush, pop compares equal",
            node1_dirty=1,
            node1_slots=(0x1F10, 0x1F10, 0x33333333, 0x44444444),
        )
    )
    cases.append(
        base_case(
            "push and pop flush (all slots distinct)",
            node1_slots=(0x11111111, 0x22222222, 0x33333333, 0x44444444),
        )
    )
    cases.append(
        base_case(
            "dirty push and dirty-dependent pop",
            node1_dirty=0,
            node1_slots=(0x11111111, 0x1F10, 0x22222222, 0x33333333),
            node2_dirty=1,
            node2_slots=(0x41414141, 0x42424242, 0x43434343, 0x44444444),
        )
    )

    # --- node counts, including the count == 3 dirty-word alias -----------
    for count in (0, 1, 2, 3):
        cases.append(
            base_case(
                f"node count {count}",
                node1_count=count,
                node1_slots=(
                    0xAAAA0000 + count,
                    0xBBBB0000,
                    0xCCCC0000,
                    0xDDDD0000,
                ),
            )
        )
    # previous == pushed, dirty initially 0: only the count-3 flat store that
    # overwrites the dirty byte can force the push flush.
    cases.append(
        base_case(
            "count 3 slot store sets the dirty byte",
            node1_count=3,
            node1_slots=(0xAAAA0003, 0xBBBB0003, 0xCCCC0003, 0x1F10),
            node1_dirty=0,
        )
    )

    # --- indirect callback targets ---------------------------------------
    cases.append(
        base_case(
            "callback target B both ends",
            callback="B",
            node1_slots=(0x11111111, 0x22222222, 0x33333333, 0x44444444),
        )
    )

    # --- packed-word guards ----------------------------------------------
    for packed in (0x00000000, 0x00FFFFFF, 0x01000000, 0x7FFFFFFF,
                   0x80000000, 0xFFFFFFFF):
        cases.append(
            base_case(f"packed word B 0x{packed:08x}", packed_b=packed)
        )
        cases.append(
            base_case(f"packed word A 0x{packed:08x}", packed_a=packed)
        )
    cases.append(
        base_case("both draw words suppressed",
                   packed_a=0x00ABCDEF, packed_b=0x00765432)
    )

    # --- render-base switches at each helper ------------------------------
    cases.append(
        base_case(
            "base switch during viewport helper",
            switch_on_viewport=True,
            node2_count=1,
            node2_slots=(0x51515151, 0x52525252, 0x53535353, 0x54545454),
        )
    )
    cases.append(
        base_case(
            "base switch during mode helper",
            switch_on_mode=True,
            node2_count=2,
            node2_slots=(0x61616161, 0x62626262, 0x63636363, 0x64646464),
            node2_dirty=1,
        )
    )
    cases.append(
        base_case(
            "base switch during push callback",
            node1_dirty=1,
            node1_slots=(0x1F10, 0x1F10, 0x33333333, 0x44444444),
            switch_flush=0,
            node2_count=1,
            node2_slots=(0x71717171, 0x72727272, 0x73737373, 0x74747474),
        )
    )
    cases.append(
        base_case(
            "base switch during pop callback",
            node1_slots=(0x1F10, 0x22222222, 0x33333333, 0x44444444),
            switch_flush=0,
        )
    )
    cases.append(
        base_case(
            "base switch during second flush",
            node1_slots=(0x11111111, 0x22222222, 0x33333333, 0x44444444),
            switch_flush=1,
            node2_count=1,
            node2_slots=(0x81818181, 0x82828282, 0x83838383, 0x84848484),
        )
    )

    # --- bias pair, including a rewrite during the viewport helper --------
    for bias_x, bias_y in (
        (0.0, 0.0),
        (0.5, 0.5),
        (-0.5, -0.5),
        (0.75, -1.25),
        (1e30, -1e30),
        (float("nan"), 0.5),
        (float("-inf"), float("inf")),
    ):
        cases.append(
            base_case(
                f"bias {bias_x!r}/{bias_y!r}",
                bias_x=float_to_bits(bias_x),
                bias_y=float_to_bits(bias_y),
            )
        )
    cases.append(
        base_case(
            "bias rewritten during the viewport helper",
            rewrite_bias_on_viewport=True,
            rewrite_bias=(float_to_bits(-100.0), float_to_bits(100.0)),
        )
    )

    # --- signed coordinate boundaries and zero crossings ------------------
    for x, y in (
        (0x7FFFFFFF, 0x7FFFFFFF),
        (0x80000000, 0x80000000),
        (0x7FFFFFFF, 0x80000000),
        (0x80000000, 0x7FFFFFFF),
        (0, 0),
        (-1, 1),
        (1, -1),
        (0x7FFFFF00, 0x80000100),
    ):
        cases.append(base_case(f"coords 0x{x:08x}/0x{y:08x}", x=x, y=y))
    for width, height in (
        (0x7FFFFFFF, 0x80000000),
        (0x80000000, 0x7FFFFFFF),
        (0, 0),
        (-1, -1),
    ):
        cases.append(
            base_case(
                f"extent 0x{width:08x}/0x{height:08x}",
                width=width,
                height=height,
            )
        )

    # --- combined ---------------------------------------------------------
    cases.append(
        base_case(
            "combined: count 3, dirty, switch, rewrites",
            node1_count=3,
            node1_slots=(0xAAAA0003, 0xBBBB0003, 0xCCCC0003, 0x11111111),
            node1_dirty=0,
            switch_on_viewport=True,
            rewrite_bias_on_viewport=True,
            rewrite_bias=(float_to_bits(2.0), float_to_bits(-2.0)),
            packed_a=0xFFFFFFFF,
            packed_b=0x7FFFFFFF,
            x=-129,
            y=257,
        )
    )
    return cases


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "vfp_saved", "call_log",
                "writes"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["data"] != cand["data"]:
        for index in range(0, len(orig["data"]), 4):
            if orig["data"][index:index + 4] != cand["data"][index:index + 4]:
                problems.append(
                    f"data differs first at 0x{DATA_ADDR + index:08x}: "
                    f"orig={orig['data'][index:index + 4].hex()} "
                    f"cand={cand['data'][index:index + 4].hex()}"
                )
                break
    for key in ("stack_args", "global_base", "bias", "nodes"):
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
    assert result["stack_args"] == (case["packed_a"], case["packed_b"]), (
        f"stack arguments modified on {name}"
    )

    assert result["call_log"] == model["log"], (
        f"call log differs from model on {name}:\n"
        f"    actual={result['call_log']!r}\n    model={model['log']!r}"
    )
    assert result["ret"] == model["ret"], (
        f"r0 differs from model on {name}: "
        f"0x{result['ret']:08x} != 0x{model['ret']:08x}"
    )
    assert result["global_base"] == model["global_base"], (
        f"render base differs from model on {name}"
    )
    for which, base in ((1, RENDER_BASE_1), (2, RENDER_BASE_2)):
        expected = bytes(model["nodes"][base])
        assert result["nodes"][which] == expected, (
            f"render-stack node {which} differs from model on {name}:\n"
            f"    actual={result['nodes'][which].hex()}\n    model={expected.hex()}"
        )
    if case.get("rewrite_bias_on_viewport"):
        assert result["bias"] == tuple(case["rewrite_bias"]), (
            f"bias pair was not rewritten on {name}"
        )
    else:
        assert result["bias"] == (case["bias_x"], case["bias_y"]), (
            f"bias pair modified on {name}"
        )


def run_case_set(orig_code, cand_code, cases, orig_machine,
                 cand_machine) -> int:
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
    print("Testing ui_func_002f2e54 (0x002f2e54)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"  original: {len(orig_code)} B, candidate: {len(cand_code)} B "
        f"(relocations resolved)"
    )

    cases = make_cases()
    orig_machine = Machine()
    cand_machine = Machine()
    passed = run_case_set(
        orig_code, cand_code, cases, orig_machine, cand_machine
    )

    print("\nNegative controls:")
    for name, old, new in (
        ("push_kind",
         "constexpr u32 kPushKind = 1;\nconstexpr u32 kPushEnabled = 1;",
         "constexpr u32 kPushKind = 2;\nconstexpr u32 kPushEnabled = 1;"),
        ("push_enabled", "constexpr u32 kPushEnabled = 1;",
         "constexpr u32 kPushEnabled = 0;"),
        ("render_mode",
         "constexpr u32 kRenderMode = 0;\n\n// Literal pool 0x002F3004",
         "constexpr u32 kRenderMode = 1;\n\n// Literal pool 0x002F3004"),
        ("stack_offset",
         "constexpr u32 kRenderStackOffset = 0x124C;\n\n"
         "// Runtime float-pair",
         "constexpr u32 kRenderStackOffset = 0x1250;\n\n"
         "// Runtime float-pair"),
        ("zero_literal", "constexpr f32 kZero = 0.0f;  // 0x00000000",
         "constexpr f32 kZero = 1.0f;  // 0x00000000"),
        ("one_literal", "constexpr f32 kOne = 1.0f;   // 0x3F800000",
         "constexpr f32 kOne = 0.0f;   // 0x3F800000"),
        ("bias_address", "constexpr u32 kBiasAddress = 0x004724CC;",
         "constexpr u32 kBiasAddress = 0x004724C8;"),
        ("alpha_guard", "if ((captured_b >> 24) != 0) {",
         "if ((captured_b & 0x00FFFFFF) != 0) {"),
        ("draw_extent_swap", "draw_x, draw_y, draw_width, draw_height, kZero);",
         "draw_x, draw_y, draw_height, draw_width, kZero);"),
        ("pop_comparison",
         "if (*node_dirty(pop_node) != 0 || pop_previous != new_top) {",
         "if (*node_dirty(pop_node) != 0 || pop_previous == new_top) {"),
        ("pop_result",
         "        *node_dirty(pop_node) = 0;\n        return result;",
         "        *node_dirty(pop_node) = 0;\n        return result ^ 1;"),
    ):
        try:
            mutant_code = compile_candidate_mutant(name, old, new)
        except RuntimeError as error:
            raise SystemExit(f"negative control failed to build: {error}")
        detected = False
        reason = ""
        for case in cases:
            good = orig_machine.run(orig_code, case)
            bad = cand_machine.run(mutant_code, case)
            if compare(good, bad):
                detected = True
                reason = f" ({case['name']})"
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected{reason}")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
