#!/usr/bin/env python3
"""Differential test for ui_func_001f6704 (0x001f6704) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the ui_func_001f6704 body,
resolves its seven direct calls (0x002C1D3C, 0x002C5F7C, 0x0025760C,
0x002575FC, 0x002B73A4, 0x002B740C, 0x0025B988) and the 0x0044EA00
render-register global, then runs the pinned original (extracted/exefs/code.bin)
and the candidate on separate Unicorn machines with identical fixtures.

Compared outputs per case:
  * continuation PC, final SP, returned r0, callee-saved r4-r11 and d8-d15;
  * the ordered call log: the render-mode helper (base, mode), the push helper
    (kind, enabled), the batch flush call, every point-sprite draw (colour in r0
    plus the x/y/z arguments as raw single-precision bit patterns), both table
    trigonometry inputs (raw bits) and every indirect render-stack callback
    (target address and value);
  * the full 2.0625 MiB data region (render global, both render-stack nodes,
    the parameter object and its fill bytes), plus the ordered list of writes
    outside the private stack;
  * an independent Python model of the push/draw/ring/pop sequence that asserts
    the original's call log, returned r0, both render-stack nodes and the final
    render base.

Float call arguments are compared as raw bit patterns, with one documented
exception: when an endpoint is NaN the original's `vmla.f32` (destination =
addend) and clang's `vmul`+`vadd` sequence select different NaN payloads.
`normalize_log` canonicalises NaN payloads at the float argument slots only;
NaN-ness, signed zero, subnormals, infinities, all finite values and every
integer argument are still compared exactly.

Coverage: node counts 0..3 (including the flat out-of-bounds slot access at
count 3), dirty cleared/set, no flush, push-only flush, pop-only flush and a
flush on both ends, two indirect callback targets, a callback that switches the
render-register global, render-mode and push helpers that switch it, a push
helper that rewrites the parameter object (the original loads the two endpoints
*after* the push and the colour *before* it), push values 0 / 0x1F51 /
0xFFFFFFFF, endpoint payloads including signed zero, subnormals, huge values,
NaN and infinities, equal endpoints (zero radius), and junk r0-r3/s0-s15.

Negative controls mutate the ring segment count, the three angle literals, the
alpha mask, the render-stack offset, the push kind and the endpoint field
selection, and hoist the endpoint loads above the helper calls; each mutant must
be detected.
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
OUT_DIR = ROOT / "build/test_leaf_001f6704"

FUNC_ADDR = 0x001F6704
FUNC_SIZE = 420

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and every stub below 0x2C6000
DATA_ADDR = 0x00400000
DATA_SIZE = 0x00210000  # render global, both node pages, the object page
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
CALLBACK_PAGE = 0x90001000
CALLBACK_A = 0x90001000
CALLBACK_B = 0x90001010

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Pinned data addresses used by the original image.
GLOBAL_ADDR = 0x0044EA00
RENDER_BASE_1 = 0x00500000
RENDER_BASE_2 = 0x00540000
RENDER_STACK_OFFSET = 0x124C
OBJ_ADDR = 0x00600000
OBJ_SIZE = 0x40

RENDER_MODE_HELPER = 0x002C1D3C
PUSH_HELPER = 0x002C5F7C
FLUSH_BATCH_HELPER = 0x0025760C
DRAW_HELPER = 0x002575FC
SIN_HELPER = 0x002B73A4
COS_HELPER = 0x002B740C
SUBMIT_HELPER = 0x0025B988

STUB_NAMES = {
    RENDER_MODE_HELPER: "ui_func_002c1d3c",
    PUSH_HELPER: "ui_func_002c5f7c",
    FLUSH_BATCH_HELPER: "func_0025760c",
    DRAW_HELPER: "ui_func_002575fc",
    SIN_HELPER: "ui_func_002b73a4",
    COS_HELPER: "ui_func_002b740c",
    SUBMIT_HELPER: "ui_func_0025b988",
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

# Recovered constants (literal pool 0x001F6890..0x001F68A7).
TWO_PI_BITS = 0x40C90FDB
RING_FRACTION_BITS = 0x3D638E39
TABLE_SCALE_BITS = 0x4222F983
HALF_BITS = 0x3F000000
ZERO_BITS = 0x00000000
RING_SEGMENTS = 19
ALPHA_MASK = 0xFFFFFF00


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


def f32_add(left: float, right: float) -> float:
    return f32(left + right)


def f32_sub(left: float, right: float) -> float:
    return f32(left - right)


def f32_mul(left: float, right: float) -> float:
    return f32(left * right)


def sine_bits(angle_bits: int) -> int:
    """Deterministic model of 0x002B73A4 (256-entry sine table).

    The argument is the turn angle scaled by 128/pi, i.e. one unit per table
    step, so `sin(x * pi/128)` is the value the table interpolates.
    """
    value = bits_to_float(angle_bits)
    if not math.isfinite(value):
        return 0x7FC00000
    return float_to_bits(f32(math.sin(value * (math.pi / 128.0))))


def cosine_bits(angle_bits: int) -> int:
    """Deterministic model of 0x002B740C (256-entry cosine table)."""
    value = bits_to_float(angle_bits)
    if not math.isfinite(value):
        return 0x7FC00000
    return float_to_bits(f32(math.cos(value * (math.pi / 128.0))))


def canonical_nan(bits: int) -> int:
    value = bits_to_float(bits)
    if value != value:
        return 0x7FC00000
    return bits


# Positions in each call-log entry that carry single-precision arguments.
FLOAT_LOG_POSITIONS = {
    "ui_func_002575fc": (2, 3, 4),
    "ui_func_002b73a4": (1,),
    "ui_func_002b740c": (1,),
}


def normalize_log(log) -> list:
    """Canonicalise NaN payloads at the float positions of the call log.

    The original computes the midpoint with `vmla.f32 s16, delta, 0.5`
    (destination register = addend) while clang reuses the `delta * 0.5`
    product and emits `vadd.f32 mid, product, from`.  Both are IEEE-equivalent
    for every non-NaN operand, but VFP NaN propagation selects the first NaN
    operand and therefore a different payload.  NaN payloads carry no
    semantics, so the harness canonicalises them in the float argument slots
    only; every other bit pattern (signed zero, subnormals, infinities, all
    finite values) and every integer argument is compared exactly.
    """
    normalised = []
    for entry in log:
        positions = FLOAT_LOG_POSITIONS.get(entry[0], ())
        items = list(entry)
        for position in positions:
            items[position] = canonical_nan(items[position])
        normalised.append(tuple(items))
    return normalised



# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("ui_func_001f6704")
    if candidate is None:
        raise RuntimeError(
            f"ui_func_001f6704 not found in {obj_file}: {sorted(funcs)}"
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


def compile_candidate_mutant(name: str, edits: list[tuple[str, str]]) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    for old, new in edits:
        if text.count(old) != 1:
            raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
        text = text.replace(old, new)
    mutant = OUT_DIR / f"mutant_{name}.cpp"
    mutant.write_text(text, encoding="utf-8")
    return compile_candidate(mutant, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def build_node(case: dict, which: str) -> bytes:
    spec = case[f"node{which}"]
    buffer = bytearray(0x40)
    struct.pack_into("<I", buffer, 0x00, spec["count"] & 0xFFFFFFFF)
    for index, word in enumerate(spec["slots"]):
        struct.pack_into("<I", buffer, 0x08 + 4 * index, word & 0xFFFFFFFF)
    buffer[0x18] = spec["dirty"] & 0xFF
    struct.pack_into("<I", buffer, 0x1C, case["callback"] & 0xFFFFFFFF)
    return bytes(buffer)


def default_object() -> dict:
    return {
        # Memory bytes at +0x0C..+0x0F: R, G, B, A.
        "rgba": (0x11, 0x22, 0x33, 0x44),
        "from": (float_to_bits(1.5), float_to_bits(-2.25)),
        "to": (float_to_bits(11.5), float_to_bits(6.75)),
    }


def build_object(case: dict) -> bytes:
    spec = case["object"]
    page = bytearray(b"\xA5" * OBJ_SIZE)
    for index, byte in enumerate(spec["rgba"]):
        page[0x0C + index] = byte & 0xFF
    struct.pack_into("<I", page, 0x14, spec["from"][0] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x18, spec["from"][1] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x1C, spec["to"][0] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x20, spec["to"][1] & 0xFFFFFFFF)
    return bytes(page)


def object_color(spec: dict) -> int:
    red, green, blue, alpha = spec["rgba"]
    return (red << 24) | (green << 16) | (blue << 8) | alpha


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "base": "1",
        "callback": CALLBACK_A,
        "push_value": 0x1F51,
        "object": default_object(),
        "node1": {
            "count": 0,
            "slots": (0x1F51, 0xDEAD0001, 0xDEAD0002, 0xDEAD0003),
            "dirty": 0,
        },
        "node2": {
            "count": 1,
            "slots": (0x51515151, 0x1F51, 0xDEAD0004, 0xDEAD0005),
            "dirty": 0,
        },
    }
    case.update(overrides)
    return case


# ---------------------------------------------------------------------------
# Independent model
# ---------------------------------------------------------------------------
def read32(buffer: bytearray, offset: int) -> int:
    return struct.unpack_from("<I", buffer, offset & 0xFFFFFFFF)[0]


def write32(buffer: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", buffer, offset & 0xFFFFFFFF, value & 0xFFFFFFFF)


def apply_object_mutation(buffer: bytearray, mutation: dict) -> None:
    if "rgba" in mutation:
        for index, byte in enumerate(mutation["rgba"]):
            buffer[0x0C + index] = byte & 0xFF
    for key, offset in (("from", 0x14), ("to", 0x1C)):
        if key in mutation:
            struct.pack_into("<I", buffer, offset, mutation[key][0] & 0xFFFFFFFF)
            struct.pack_into("<I", buffer, offset + 4, mutation[key][1] & 0xFFFFFFFF)


class Model:
    """Executable model of the recovered contract (no emulation involved)."""

    def __init__(self, case: dict) -> None:
        self.case = case
        self.g = RENDER_BASE_1 if case["base"] == "1" else RENDER_BASE_2
        self.nodes = {
            RENDER_BASE_1: bytearray(build_node(case, "1")),
            RENDER_BASE_2: bytearray(build_node(case, "2")),
        }
        self.obj = bytearray(build_object(case))
        self.log: list = []

    def callback(self, target: int, value: int) -> int:
        self.log.append(("flush", target, value))
        if self.case.get("switch_base_on_callback"):
            self.g = RENDER_BASE_2
        if target == CALLBACK_A:
            return (0xCBA5A500 ^ value) & 0xFFFFFFFF
        return (0xCBA5B500 ^ value) & 0xFFFFFFFF

    def maybe_flush(self, node: bytearray, previous: int, value: int) -> int | None:
        if node[0x18] != 0 or previous != value:
            node[0x18] = 0
            return self.callback(read32(node, 0x1C), value)
        return None

    def run(self) -> dict:
        case = self.case
        # The colour is read before any helper runs (`ldr`/`ldrb` at
        # 0x001F6714/0x001F6718), the two endpoints only after the push.
        rgba = [self.obj[0x0C + index] for index in range(4)]
        color = (rgba[0] << 24) | (rgba[1] << 16) | (rgba[2] << 8) | rgba[3]
        ring_color = color & ALPHA_MASK

        self.log.append(("ui_func_002c1d3c", self.g, 0))
        if case.get("switch_base_on_mode"):
            self.g = RENDER_BASE_2

        push_base = self.g
        self.log.append(("ui_func_002c5f7c", 1, 0))
        if case.get("switch_base_on_push"):
            self.g = RENDER_BASE_2
        mutation = case.get("mutate_object_on_push")
        if mutation:
            apply_object_mutation(self.obj, mutation)

        pushed = case["push_value"] & 0xFFFFFFFF
        node = self.nodes[push_base]
        count = read32(node, 0x00)
        previous = read32(node, 0x08 + 4 * count)
        write32(node, 0x00, count + 1)
        write32(node, 0x08 + 4 * ((count + 1) & 0xFFFFFFFF), pushed)
        self.maybe_flush(node, previous, pushed)

        to_x = bits_to_float(read32(self.obj, 0x1C))
        to_y = bits_to_float(read32(self.obj, 0x20))
        from_x = bits_to_float(read32(self.obj, 0x14))
        from_y = bits_to_float(read32(self.obj, 0x18))
        delta_x = f32_sub(to_x, from_x)
        delta_y = f32_sub(to_y, from_y)
        half = bits_to_float(HALF_BITS)
        mid_x = f32_add(from_x, f32_mul(delta_x, half))
        mid_y = f32_add(from_y, f32_mul(delta_y, half))
        radius = f32_mul(delta_x, half)

        self.log.append(("func_0025760c",))
        self.log.append(
            ("ui_func_002575fc", color, float_to_bits(mid_x),
             float_to_bits(mid_y), ZERO_BITS)
        )

        two_pi = bits_to_float(TWO_PI_BITS)
        fraction = bits_to_float(RING_FRACTION_BITS)
        scale = bits_to_float(TABLE_SCALE_BITS)
        for index in range(RING_SEGMENTS):
            angle = f32_mul(
                f32_mul(f32_mul(float(index), two_pi), fraction), scale
            )
            angle_bits = float_to_bits(angle)
            sine = bits_to_float(sine_bits(angle_bits))
            cosine = bits_to_float(cosine_bits(angle_bits))
            self.log.append(("ui_func_002b73a4", angle_bits))
            self.log.append(("ui_func_002b740c", angle_bits))
            self.log.append(
                ("ui_func_002575fc", ring_color,
                 float_to_bits(f32_add(mid_x, f32_mul(radius, sine))),
                 float_to_bits(f32_add(mid_y, f32_mul(radius, cosine))),
                 ZERO_BITS)
            )

        self.log.append(("ui_func_0025b988",))

        node = self.nodes[self.g]
        count = read32(node, 0x00)
        previous = read32(node, 0x08 + 4 * count)
        write32(node, 0x00, count - 1)
        new_top = read32(node, 0x08 + 4 * ((count - 1) & 0xFFFFFFFF))
        flushed = self.maybe_flush(node, previous, new_top)
        ret = new_top if flushed is None else flushed

        return {
            "log": self.log,
            "ret": ret,
            "g": self.g,
            "nodes": self.nodes,
            "object": self.obj,
        }


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
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

    # -------------------------------------------------------------- stubs
    def _on_helper(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == RENDER_MODE_HELPER:
            self.call_log.append(("ui_func_002c1d3c", r0, r1))
            if self.case.get("switch_base_on_mode"):
                write_u32(uc, GLOBAL_ADDR, RENDER_BASE_2)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2C1D0000 ^ r0 ^ (r1 << 8))
        elif address == PUSH_HELPER:
            self.call_log.append(("ui_func_002c5f7c", r0, r1))
            mutation = self.case.get("mutate_object_on_push")
            if mutation:
                page = bytearray(uc.mem_read(OBJ_ADDR, OBJ_SIZE))
                apply_object_mutation(page, mutation)
                uc.mem_write(OBJ_ADDR, bytes(page))
            if self.case.get("switch_base_on_push"):
                write_u32(uc, GLOBAL_ADDR, RENDER_BASE_2)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["push_value"] & 0xFFFFFFFF)
        elif address == FLUSH_BATCH_HELPER:
            # The wrapper sets r0 = 2 internally and derives everything from
            # that constant, so its incoming registers are dead.
            self.call_log.append(("func_0025760c",))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x25760000)
        elif address == DRAW_HELPER:
            x_bits = uc.reg_read(arm.UC_ARM_REG_S0)
            y_bits = uc.reg_read(arm.UC_ARM_REG_S1)
            z_bits = uc.reg_read(arm.UC_ARM_REG_S2)
            self.call_log.append(
                ("ui_func_002575fc", r0, x_bits, y_bits, z_bits)
            )
            uc.reg_write(arm.UC_ARM_REG_R0, 0xD00D0000 ^ r0)
        elif address == SIN_HELPER:
            angle_bits = uc.reg_read(arm.UC_ARM_REG_S0)
            self.call_log.append(("ui_func_002b73a4", angle_bits))
            uc.reg_write(arm.UC_ARM_REG_S0, sine_bits(angle_bits))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x51A00000)
        elif address == COS_HELPER:
            angle_bits = uc.reg_read(arm.UC_ARM_REG_S0)
            self.call_log.append(("ui_func_002b740c", angle_bits))
            uc.reg_write(arm.UC_ARM_REG_S0, cosine_bits(angle_bits))
            uc.reg_write(arm.UC_ARM_REG_R0, 0xC05A0000)
        elif address == SUBMIT_HELPER:
            self.call_log.append(("ui_func_0025b988",))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x25B90000)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_callback(self, uc, address: int, size: int, user_data) -> None:
        value = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("flush", address, value))
        if self.case.get("switch_base_on_callback"):
            write_u32(uc, GLOBAL_ADDR, RENDER_BASE_2)
        if address == CALLBACK_A:
            uc.reg_write(arm.UC_ARM_REG_R0, 0xCBA5A500 ^ value)
        else:
            uc.reg_write(arm.UC_ARM_REG_R0, 0xCBA5B500 ^ value)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
            self.writes.append((address, size, value & ((1 << (8 * size)) - 1)))

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        uc = self.uc
        self.call_log = []
        self.writes = []
        self.case = case

        uc.mem_write(DATA_ADDR, b"\xCC" * DATA_SIZE)
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.mem_write(FUNC_ADDR, b"\x00" * FUNC_SIZE)
        uc.mem_write(FUNC_ADDR, code)
        write_u32(uc, GLOBAL_ADDR,
                  RENDER_BASE_1 if case["base"] == "1" else RENDER_BASE_2)
        for which, base in (("1", RENDER_BASE_1), ("2", RENDER_BASE_2)):
            uc.mem_write(base + RENDER_STACK_OFFSET, build_node(case, which))
        uc.mem_write(OBJ_ADDR, build_object(case))
        uc.ctl_flush_tb()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R1, case["junk"][0])
        uc.reg_write(arm.UC_ARM_REG_R2, case["junk"][1])
        uc.reg_write(arm.UC_ARM_REG_R3, case["junk"][2])
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
            "g": read_u32(uc, GLOBAL_ADDR),
            "nodes": {
                "1": bytes(uc.mem_read(RENDER_BASE_1 + RENDER_STACK_OFFSET, 0x40)),
                "2": bytes(uc.mem_read(RENDER_BASE_2 + RENDER_STACK_OFFSET, 0x40)),
            },
            "object": bytes(uc.mem_read(OBJ_ADDR, OBJ_SIZE)),
        }


def write_u32(uc, address: int, value: int) -> None:
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def make_cases() -> list[dict]:
    cases: list[dict] = []
    default_junk = (0x22222222, 0x33333333, 0x44444444)

    def add(name: str, **overrides) -> None:
        overrides.setdefault("junk", default_junk)
        cases.append(base_case(name, **overrides))

    # --- push/pop flush matrix ---------------------------------------------
    add("node count 0, previous equals pushed (no flush)")
    add("node count 0, previous differs (push and pop flush)",
        node1={"count": 0, "slots": (0x11111111, 0x22222222,
                                     0x33333333, 0x44444444), "dirty": 0})
    add("node count 0, dirty forces push flush only",
        node1={"count": 0, "slots": (0x1F51, 0x1F51,
                                     0x33333333, 0x44444444), "dirty": 1})
    add("node count 1, push flush only",
        node1={"count": 1, "slots": (0x1F51, 0x1F51,
                                     0xAAAA0001, 0xBBBB0002), "dirty": 0})
    add("node count 1, both flush",
        node1={"count": 1, "slots": (0x0BADF00D, 0x1F51,
                                     0xAAAA0001, 0xBBBB0002), "dirty": 0})
    add("node count 2, both flush, dirty",
        node1={"count": 2, "slots": (0xDEADBEEF, 0x0BADF00D,
                                     0x1F51, 0xBBBB0002), "dirty": 1})
    add("node count 3, flat out-of-bounds slot access",
        node1={"count": 3, "slots": (0xAAAA0010, 0xAAAA0011,
                                     0xAAAA0012, 0xAAAA0013), "dirty": 0})

    # --- push value boundaries --------------------------------------------
    for value, slots in (
        (0x00000000, (0x00000000, 0x11111111, 0x22222222, 0x33333333)),
        (0x00000000, (0x99999999, 0x11111111, 0x22222222, 0x33333333)),
        (0xFFFFFFFF, (0xFFFFFFFF, 0x11111111, 0x22222222, 0x33333333)),
        (0xFFFFFFFF, (0xEEEEEEEE, 0x11111111, 0x22222222, 0x33333333)),
    ):
        add(f"push value 0x{value:08x} slot0 0x{slots[0]:08x}",
            push_value=value,
            node1={"count": 0, "slots": slots, "dirty": 0})

    # --- indirect callback targets ----------------------------------------
    add("callback target B",
        callback=CALLBACK_B,
        node1={"count": 0, "slots": (0x11111111, 0x22222222,
                                     0x33333333, 0x44444444), "dirty": 0})
    add("callback target B, dirty push only",
        callback=CALLBACK_B,
        node1={"count": 0, "slots": (0x1F51, 0x1F51,
                                     0x33333333, 0x44444444), "dirty": 1})

    # --- the three reads of 0x0044EA00 ------------------------------------
    add("render-mode helper switches the render base",
        switch_base_on_mode=True,
        node2={"count": 1, "slots": (0x61616161, 0x62626262,
                                     0x63636363, 0x64646464), "dirty": 1})
    add("push helper switches the render base",
        switch_base_on_push=True,
        node2={"count": 1, "slots": (0x61616161, 0x62626262,
                                     0x63636363, 0x64646464), "dirty": 0})
    add("callback switches the render base",
        switch_base_on_callback=True,
        node1={"count": 0, "slots": (0x11111111, 0x22222222,
                                     0x33333333, 0x44444444), "dirty": 0},
        node2={"count": 2, "slots": (0x51515151, 0x52525252,
                                     0x53535353, 0x54545454), "dirty": 0})
    add("callback switches the base on a dirty push",
        switch_base_on_callback=True,
        node1={"count": 1, "slots": (0x1F51, 0x1F51,
                                     0x33333333, 0x44444444), "dirty": 1},
        node2={"count": 1, "slots": (0x71717171, 0x72727272,
                                     0x73737373, 0x74747474), "dirty": 1})
    add("render base 2 from the start",
        base="2",
        node2={"count": 3, "slots": (0x81818181, 0x82828282,
                                     0x83838383, 0x84848484), "dirty": 0})

    # --- helper rewrites the parameter object -----------------------------
    add("push helper rewrites the endpoints and colour",
        mutate_object_on_push={
            "from": (float_to_bits(-9.5), float_to_bits(3.25)),
            "to": (float_to_bits(4.5), float_to_bits(-7.5)),
            "rgba": (0xAA, 0xBB, 0xCC, 0xDD),
        })
    add("push helper rewrites only the colour",
        mutate_object_on_push={"rgba": (0x01, 0x02, 0x03, 0x04)})
    add("push helper rewrites only the endpoints",
        mutate_object_on_push={
            "from": (float_to_bits(0.0), float_to_bits(0.0)),
            "to": (float_to_bits(1.0), float_to_bits(1.0)),
        })

    # --- colour bytes ------------------------------------------------------
    for rgba in (
        (0x00, 0x00, 0x00, 0x00),
        (0xFF, 0xFF, 0xFF, 0xFF),
        (0x00, 0x00, 0x00, 0xFF),
        (0xFF, 0x00, 0x00, 0x00),
        (0x12, 0x34, 0x56, 0x78),
        (0x80, 0x01, 0xFE, 0x7F),
    ):
        obj = default_object()
        obj["rgba"] = rgba
        add(f"rgba {rgba[0]:02x}{rgba[1]:02x}{rgba[2]:02x}{rgba[3]:02x}",
            object=obj)

    # --- endpoint payloads -------------------------------------------------
    special = [
        (0x00000000, 0x80000000),          # +0 and -0
        (0x7F7FFFFF, 0xFF7FFFFF),          # +max / -max
        (0x00800000, 0x80800000),          # smallest normals
        (0x00000001, 0x80000001),          # subnormals
        (0x7F800000, 0xFF800000),          # +inf / -inf
        (0x7FC00000, 0xFFC00001),          # NaN payloads
        (0x40A00000, 0xC0A00000),          # 5.0 / -5.0
    ]
    for index, (from_pair, to_pair) in enumerate(
        ((special[i], special[i - 1]) for i in range(len(special)))
    ):
        obj = default_object()
        obj["from"] = from_pair
        obj["to"] = to_pair
        add(f"endpoint payload pair {index}", object=obj)

    equal = default_object()
    equal["from"] = (float_to_bits(3.5), float_to_bits(-4.5))
    equal["to"] = (float_to_bits(3.5), float_to_bits(-4.5))
    add("equal endpoints (zero radius)", object=equal)

    for delta in (0.0, 1e-30, 1e30, -1e30):
        obj = default_object()
        obj["from"] = (float_to_bits(0.0), float_to_bits(0.0))
        obj["to"] = (float_to_bits(delta), float_to_bits(delta))
        add(f"symmetric endpoints delta {delta!r}", object=obj)

    # --- junk registers ----------------------------------------------------
    add("junk registers ignored",
        junk=(0xCAFEBABE, 0x9ABCDEF0, 0xFFFFFFFF))
    add("zero junk registers", junk=(0, 0, 0))

    return cases


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("pc", "sp", "callee_saved", "vfp_saved", "ret"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if normalize_log(orig["call_log"]) != normalize_log(cand["call_log"]):
        problems.append(
            "call_log:\n    orig="
            + repr(normalize_log(orig["call_log"]))
            + "\n    cand="
            + repr(normalize_log(cand["call_log"]))
        )
    if orig["writes"] != cand["writes"]:
        problems.append(
            "writes:\n    orig=" + repr(orig["writes"]) + "\n    cand="
            + repr(cand["writes"])
        )
    if orig["data"] != cand["data"]:
        for index in range(0, len(orig["data"]), 4):
            if orig["data"][index:index + 4] != cand["data"][index:index + 4]:
                problems.append(
                    f"data differs first at 0x{DATA_ADDR + index:08x}: "
                    f"orig={orig['data'][index:index + 4].hex()} "
                    f"cand={cand['data'][index:index + 4].hex()}"
                )
                break
    for key in ("g", "nodes", "object"):
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

    # NaN payloads may differ between a fused and an unfused multiply-add (see
    # normalize_log); the model comparison uses the same canonicalisation.
    actual_log = normalize_log(result["call_log"])
    expected_log = normalize_log(model["log"])
    assert actual_log == expected_log, (
        f"call log differs from model on {name}:\n"
        f"    actual={actual_log!r}\n    model={expected_log!r}"
    )
    assert result["ret"] == model["ret"], (
        f"r0 differs from model on {name}: "
        f"0x{result['ret']:08x} != 0x{model['ret']:08x}"
    )
    assert result["g"] == model["g"], f"render base differs from model on {name}"
    for which in ("1", "2"):
        expected = bytes(model["nodes"][
            RENDER_BASE_1 if which == "1" else RENDER_BASE_2
        ])
        assert result["nodes"][which] == expected, (
            f"render-stack node {which} differs from model on {name}:\n"
            f"    actual={result['nodes'][which].hex()}\n    model={expected.hex()}"
        )
    assert result["object"] == bytes(model["object"]), (
        f"parameter object differs from model on {name}"
    )


def run_case_set(
    orig_code, cand_code, cases, orig_machine, cand_machine
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
        check_expectations(case, orig, Model(case).run())
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing ui_func_001f6704 (0x001f6704)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"  original: {len(orig_code)} B, candidate: {len(cand_code)} B "
        f"(call and global relocations resolved)"
    )

    cases = make_cases()
    orig_machine = Machine()
    cand_machine = Machine()
    passed = run_case_set(orig_code, cand_code, cases, orig_machine, cand_machine)

    print("\nNegative controls:")
    hoisted = [
        (
            "    const u32 ring_color = color & kAlphaByteMask;\n",
            "    const u32 ring_color = color & kAlphaByteMask;\n"
            "    const f32 early_to_x = params->to_x_1c;\n"
            "    const f32 early_to_y = params->to_y_20;\n"
            "    const f32 early_from_x = params->from_x_14;\n"
            "    const f32 early_from_y = params->from_y_18;\n",
        ),
        (
            "    const f32 to_x = params->to_x_1c;\n"
            "    const f32 to_y = params->to_y_20;\n"
            "    const f32 from_x = params->from_x_14;\n"
            "    const f32 from_y = params->from_y_18;\n",
            "    const f32 to_x = early_to_x;\n"
            "    const f32 to_y = early_to_y;\n"
            "    const f32 from_x = early_from_x;\n"
            "    const f32 from_y = early_from_y;\n",
        ),
    ]
    mutants = [
        ("ring_segments", [("constexpr s32 kRingSegments = 19;",
                            "constexpr s32 kRingSegments = 18;")]),
        ("full_turn", [("constexpr f32 kFullTurn = 6.2831855f;",
                        "constexpr f32 kFullTurn = 6.283186f;")]),
        ("ring_fraction", [("constexpr f32 kRingFraction = 0.055555556f;",
                            "constexpr f32 kRingFraction = 0.055555560f;")]),
        ("table_scale", [("constexpr f32 kTableScale = 40.743664f;",
                          "constexpr f32 kTableScale = 40.74366f;")]),
        ("alpha_mask", [("constexpr u32 kAlphaByteMask = 0xFFFFFF00u;",
                         "constexpr u32 kAlphaByteMask = 0xFFFFFF01u;")]),
        ("render_stack_offset",
         [("// `add r4, r4, #0x1000` + `add r4, r4, #0x24C`: render-stack node offset.\n"
           "constexpr u32 kRenderStackOffset = 0x124C;",
           "// `add r4, r4, #0x1000` + `add r4, r4, #0x24C`: render-stack node offset.\n"
           "constexpr u32 kRenderStackOffset = 0x1248;")]),
        ("push_kind", [("constexpr u32 kPushKind = 1;",
                        "constexpr u32 kPushKind = 2;")]),
        ("endpoint_field", [("const f32 to_x = params->to_x_1c;",
                             "const f32 to_x = params->from_x_14;")]),
        ("endpoint_load_order", hoisted),
        ("half_scale", [("constexpr f32 kHalf = 0.5f;",
                         "constexpr f32 kHalf = 0.75f;")]),
        ("pop_dirty_order",
         [("    ui_func_0025b988();\n"
           "\n"
           "    // The pop re-reads 0x0044EA00; the node captured for the callback is the\n"
           "    // one addressed by *this* read even if the callback switches the global.\n"
           "    RenderStackNode* const pop_node =\n"
           "        render_stack(smt4::engine::g_RenderRegisterBase);\n"
           "    u32* const pop_slots = pop_node->slots;\n"
           "    const u32 pop_count = pop_node->count;\n"
           "    const u32 pop_previous = pop_slots[pop_count];\n"
           "    pop_node->count = pop_count - 1;\n"
           "    const u32 new_top = pop_slots[pop_count - 1];\n"
           "    if (pop_node->dirty != 0 || pop_previous != new_top) {",
           "    ui_func_0025b988();\n"
           "\n"
           "    // The pop re-reads 0x0044EA00; the node captured for the callback is the\n"
           "    // one addressed by *this* read even if the callback switches the global.\n"
           "    RenderStackNode* const pop_node =\n"
           "        render_stack(smt4::engine::g_RenderRegisterBase);\n"
           "    u32* const pop_slots = pop_node->slots;\n"
           "    const u32 pop_count = pop_node->count;\n"
           "    const u32 pop_previous = pop_slots[pop_count];\n"
           "    pop_node->count = pop_count - 1;\n"
           "    const u32 new_top = pop_slots[pop_count - 1];\n"
           "    if (pop_node->dirty != 0 && pop_previous != new_top) {")]),
    ]
    for name, edits in mutants:
        mutant_code = compile_candidate_mutant(name, edits)
        mutant_machine = Machine()
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
