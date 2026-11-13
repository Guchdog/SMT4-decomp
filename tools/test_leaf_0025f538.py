#!/usr/bin/env python3
"""Differential test for ui_func_0025f538 (0x0025f538) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the ui_func_0025f538 body,
resolves its six direct calls (0x002BEF7C, 0x002BEF70, 0x002BF710,
0x002BF6D0, 0x002BF460, 0x002C5FA4) and the 0x0044EA00 render-register global,
then runs the pinned original (extracted/exefs/code.bin) and the candidate on
separate Unicorn machines with identical fixtures.

Compared per case:
  * continuation PC, final SP, returned r0, callee-saved r4-r11 and d8-d15;
  * the ordered call log: both 20.12 getters and their record pointer, the
    scale helper's s0 bit pattern, the node resolver (group, raw biased index),
    both command builders, every draw call (four register arguments plus the
    two architected stack words), and every indirect flush callback (target and
    value).  Stack arguments are logged from the callee's SP;
  * the whole 2 MiB data region (context page, render-register global, both
    render-stack nodes, relocated candidate rodata), the resolver-node page and
    the callback page, plus the ordered list of writes outside the private
    stack;
  * an independent Python model of the gates, node selection, store/callback
    rule, four unrolled draws and the tail call.

Helpers are deterministic stubs.  The two getters reproduce their real
`ldr; asr #12` contract, 0x002C5FA4 reproduces its real bit-building formula,
and the flush callbacks are ARM `bx lr` stubs at two addresses.  Cases make the
stubs rewrite the render-register global, the context state word, the draw node
offsets, the stack depth and the dirty byte to prove each re-read and the
store/callback ordering.

Coverage: flag zero/non-zero (0x01/0x80/0xFF), signed state values 0, 2, 3, 4,
0x7FFFFFFF, 0xFFFFFFFF and 0x80000000, the state re-read after 0x002BF710,
stack depths 0..3, dirty-driven and value-driven flushes, callbacks that switch
the render base / bump the depth / set the dirty byte, both callback targets,
render-base switches from the resolver, the first command builder and the
callback, draw-node offsets at both s16 endpoints, 20.12 source words at signed
boundaries, and per-draw node re-reads.  Negative controls mutate the state
limit, every observed offset, the group/bias, the sprite ids and attribute, the
second command selector, the final scale, the dirty condition and the first
base-read order; each mutant must be detected.

A null 0x002BF6D0 result is not exercised: the original dereferences the return
unconditionally (`ldrsh r4,[r4,#8]`), so both implementations fault on the same
load rather than producing a comparable result.
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
OUT_DIR = ROOT / "build/test_leaf_0025f538"

FUNC_ADDR = 0x0025F538
FUNC_SIZE = 436

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers 0x25F538 and every stub below 0x2C5FA4
DATA_ADDR = 0x00400000
DATA_SIZE = 0x00200000  # context, globals, both render nodes, candidate rodata
NODE_ADDR = 0x00600000
NODE_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
CALLBACK_PAGE = 0x90001000
CALLBACK_A = 0x90001000
CALLBACK_B = 0x90001010

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

CTX_ADDR = 0x00480000
CTX_SIZE = 0x00004000
GLOBAL_ADDR = 0x0044EA00
RENDER_BASE_1 = 0x00500000
RENDER_BASE_2 = 0x00540000
RENDER_STACK_OFFSET = 0x12AC
CAND_RODATA = 0x005F0000
NODE_VARIANT_A = 0x00000100
NODE_VARIANT_B = 0x00000200

GETTER_X = 0x002BEF7C
GETTER_Y = 0x002BEF70
SCALE_HELPER = 0x002BF710
RESOLVER = 0x002BF6D0
DRAW_HELPER = 0x002BF460
COMMAND_HELPER = 0x002C5FA4

STUB_NAMES = {
    GETTER_X: "ui_func_002bef7c",
    GETTER_Y: "shop_func_002bef70",
    SCALE_HELPER: "ui_func_002bf710",
    RESOLVER: "camp_func_002bf6d0",
    DRAW_HELPER: "ui_func_002bf460",
    COMMAND_HELPER: "battle_func_002c5fa4",
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

SCALE_RETURN = 0x2BF710F0
SPRITE_IDS = (0x4B, 0x4A, 0x4C, 0x4D)
NODE_GROUP = 0x15
NODE_BIAS = 0x52
SPRITE_ATTRIBUTE = 0x29
FIRST_VALUE = 0x16160000
SECOND_VALUE = 0x76760000

BX_LR = 0xE12FFF1E


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & 0x80000000 else value


def asr12(value: int) -> int:
    return s32(value) >> 12


def to_arm(value: int) -> int:
    return value & 0xFFFFFFFF


def write_u32(uc, address: int, value: int) -> None:
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def command_word(kind: int, selector: int, flags: int) -> int:
    """The exact 0x002C5FA4 bit construction (`orr` chain)."""
    value = flags | ((flags << 8) & 0xFFFFFFFF)
    value |= (kind << 16) & 0xFFFFFFFF
    value |= (selector << 20) & 0xFFFFFFFF
    value |= (kind << 24) & 0xFFFFFFFF
    value |= (selector << 28) & 0xFFFFFFFF
    return value & 0xFFFFFFFF


def callback_return(callback: int, value: int) -> int:
    if callback == CALLBACK_A:
        return (0xCBA5A500 ^ value) & 0xFFFFFFFF
    if callback == CALLBACK_B:
        return (0xCBA5B500 ^ value) & 0xFFFFFFFF
    raise AssertionError(f"unknown callback target 0x{callback:08x}")


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
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
    candidate = funcs.get("ui_func_0025f538")
    if candidate is None:
        raise RuntimeError(
            f"ui_func_0025f538 not found in {obj_file}: {sorted(funcs)}"
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
            elif rel.symbol_name in ("", ".rodata", ".rodata.str1.1"):
                struct.pack_into("<I", code, rel.offset, CAND_RODATA + addend)
            else:
                raise RuntimeError(f"unsupported abs32 relocation: {rel}")
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")

    rodata = elf_sections(obj_file).get(".rodata", b"")
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
# Fixtures
# ---------------------------------------------------------------------------
def build_ctx(case: dict) -> bytes:
    page = bytearray(b"\xCC" * CTX_SIZE)
    page[0x3084] = case["flag"] & 0xFF
    struct.pack_into("<I", page, 0x305C, case["state"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0xCC, case["scale_bits"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x12B8 + 0x0C, case["anchor_x"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x12B8 + 0x10, case["anchor_y"] & 0xFFFFFFFF)
    return bytes(page)


def build_render_node(case: dict, which: int) -> bytes:
    prefix = f"node{which}"
    buffer = bytearray(b"\xCC" * 0x20)
    struct.pack_into("<I", buffer, 0x00, case[f"{prefix}_depth"] & 0xFFFFFFFF)
    struct.pack_into("<I", buffer, 0x04, 0x04040404)
    for index, word in enumerate(case[f"{prefix}_slots"]):
        struct.pack_into("<I", buffer, 0x08 + 4 * index, word & 0xFFFFFFFF)
    buffer[0x18] = case[f"{prefix}_dirty"] & 0xFF
    buffer[0x19:0x1C] = b"\x19\x19\x19"
    struct.pack_into(
        "<I", buffer, 0x1C, case[f"{prefix}_callback"] & 0xFFFFFFFF
    )
    return bytes(buffer)


def build_node_page(case: dict) -> bytes:
    page = bytearray(b"\xCC" * NODE_SIZE)
    for variant in ("A", "B"):
        offset = NODE_VARIANT_A if variant == "A" else NODE_VARIANT_B
        struct.pack_into("<i", page, offset + 8, case[f"node_{variant}_x"])
        struct.pack_into("<i", page, offset + 0x0A, case[f"node_{variant}_y"])
        struct.pack_into("<I", page, offset + 0x00, 0xA5A5A500 | offset)
    return bytes(page)


def node_variant_address(case: dict) -> int:
    return NODE_ADDR + (
        NODE_VARIANT_A if case["draw_node"] == "A" else NODE_VARIANT_B
    )


# ---------------------------------------------------------------------------
# Python model
# ---------------------------------------------------------------------------
class Model:
    def __init__(self, case: dict) -> None:
        self.case = case
        self.ctx = bytearray(build_ctx(case))
        self.global_base = render_base(case)
        self.stack_nodes = {
            RENDER_BASE_1: bytearray(build_render_node(case, 1)),
            RENDER_BASE_2: bytearray(build_render_node(case, 2)),
        }
        self.node_page = bytearray(build_node_page(case))
        self.draw_node = node_variant_address(case)
        self.log: list = []

    # -- flat accessors -----------------------------------------------------
    @staticmethod
    def read32(buffer: bytearray, offset: int) -> int:
        return struct.unpack_from("<I", buffer, offset & 0xFFFFFFFF)[0]

    @staticmethod
    def write32(buffer: bytearray, offset: int, value: int) -> None:
        struct.pack_into("<I", buffer, offset & 0xFFFFFFFF, value & 0xFFFFFFFF)

    def stack_node(self, base: int) -> bytearray:
        return self.stack_nodes[base]

    def run_callback(self, node: bytearray, value: int) -> int:
        callback = self.read32(node, 0x1C)
        self.log.append(("flush", callback, value))
        case = self.case
        if case.get("callback_switch_base"):
            self.global_base = RENDER_BASE_2
        if case.get("callback_bump_depth"):
            depth = self.read32(node, 0x00)
            self.write32(node, 0x00, depth + 1)
        if case.get("callback_set_dirty"):
            node[0x18] = 1
        return callback_return(callback, value)

    def store_slot(self, node: bytearray, value: int) -> int:
        depth = self.read32(node, 0x00)
        previous = self.read32(node, 0x08 + 4 * depth)
        self.write32(node, 0x08 + 4 * depth, value)
        if node[0x18] != 0 or previous != value:
            result = self.run_callback(node, value)
            node[0x18] = 0
            return result
        return value

    def draw(self, sprite: int, origin_x: int, origin_y: int) -> None:
        offset = self.draw_node - NODE_ADDR
        dx = struct.unpack_from("<h", self.node_page, offset + 8)[0]
        dy = struct.unpack_from("<h", self.node_page, offset + 0x0A)[0]
        self.log.append(
            (
                "ui_func_002bf460",
                2,
                NODE_GROUP,
                sprite,
                (origin_x + dx) & 0xFFFFFFFF,
                (origin_y + dy) & 0xFFFFFFFF,
                SPRITE_ATTRIBUTE,
            )
        )
        if self.case.get("mutate_node_on_draw"):
            struct.pack_into(
                "<h", self.node_page, offset + 8, s16(dx + 1)
            )
            struct.pack_into(
                "<h", self.node_page, offset + 0x0A, s16(dy + 1)
            )

    # -- recovered algorithm ------------------------------------------------
    def run(self) -> dict:
        case = self.case
        flag = self.ctx[0x3084]
        if flag != 0:
            return self.result(flag)
        state = s32(self.read32(self.ctx, 0x305C))
        if state > 3:
            return self.result(to_arm(state))

        record = CTX_ADDR + 0x12B8
        origin_x = asr12(self.read32(self.ctx, 0x12B8 + 0x0C))
        self.log.append(("ui_func_002bef7c", record))
        origin_y = asr12(self.read32(self.ctx, 0x12B8 + 0x10))
        self.log.append(("shop_func_002bef70", record))

        self.log.append(("ui_func_002bf710", case["scale_bits"] & 0xFFFFFFFF))
        if case.get("scale_sets_state") is not None:
            self.write32(self.ctx, 0x305C, case["scale_sets_state"])
        state = self.read32(self.ctx, 0x305C)
        index = (state + NODE_BIAS) & 0xFFFFFFFF
        self.log.append(("camp_func_002bf6d0", NODE_GROUP, index))
        if case.get("resolver_switch_base"):
            self.global_base = RENDER_BASE_2

        first_node = self.stack_node(self.global_base)
        self.log.append(("battle_func_002c5fa4", 6, 1, 0))
        if case.get("cmd_switch_first"):
            self.global_base = RENDER_BASE_2
        self.store_slot(first_node, FIRST_VALUE)

        for sprite in SPRITE_IDS:
            self.draw(sprite, origin_x, origin_y)

        second_node = self.stack_node(self.global_base)
        self.log.append(("battle_func_002c5fa4", 6, 7, 0))
        if case.get("cmd_switch_second"):
            self.global_base = RENDER_BASE_1
        self.store_slot(second_node, SECOND_VALUE)

        self.log.append(("ui_func_002bf710", 0x3F800000))
        return self.result(SCALE_RETURN)

    def result(self, return_value: int) -> dict:
        return {
            "ret": return_value & 0xFFFFFFFF,
            "log": list(self.log),
            "ctx": bytes(self.ctx),
            "nodes": {
                which: bytes(self.stack_nodes[base])
                for which, base in ((1, RENDER_BASE_1), (2, RENDER_BASE_2))
            },
            "node_page": bytes(self.node_page),
            "base": self.global_base,
        }


def s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    """One Unicorn machine with deterministic stubs at the original addresses."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
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
        self.scale_calls = 0
        self.draw_node = 0

    # -------------------------------------------------------------- stubs
    def _stack_words(self, count: int) -> tuple:
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _write_global(self, base: int) -> None:
        write_u32(self.uc, GLOBAL_ADDR, base)

    def _on_helper(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        case = self.case

        if address == GETTER_X:
            self.call_log.append(("ui_func_002bef7c", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, to_arm(asr12(read_u32(uc, r0 + 0x0C))))
        elif address == GETTER_Y:
            self.call_log.append(("shop_func_002bef70", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, to_arm(asr12(read_u32(uc, r0 + 0x10))))
        elif address == SCALE_HELPER:
            self.call_log.append(("ui_func_002bf710", uc.reg_read(arm.UC_ARM_REG_S0)))
            self.scale_calls += 1
            if self.scale_calls == 1 and case.get("scale_sets_state") is not None:
                write_u32(uc, CTX_ADDR + 0x305C, case["scale_sets_state"])
            uc.reg_write(arm.UC_ARM_REG_R0, SCALE_RETURN)
        elif address == RESOLVER:
            self.call_log.append(("camp_func_002bf6d0", r0, r1))
            self.draw_node = node_variant_address(case)
            if case.get("resolver_switch_base"):
                self._write_global(RENDER_BASE_2)
            uc.reg_write(arm.UC_ARM_REG_R0, self.draw_node)
        elif address == COMMAND_HELPER:
            self.call_log.append(("battle_func_002c5fa4", r0, r1, r2))
            result = command_word(r0, r1, r2)
            if r1 == 1 and case.get("cmd_switch_first"):
                self._write_global(RENDER_BASE_2)
            if r1 == 7 and case.get("cmd_switch_second"):
                self._write_global(RENDER_BASE_1)
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == DRAW_HELPER:
            sp0, sp1 = self._stack_words(2)
            self.call_log.append(
                ("ui_func_002bf460", r0, r1, r2, r3, sp0, sp1)
            )
            if case.get("mutate_node_on_draw"):
                offset = self.draw_node - NODE_ADDR
                dx = struct.unpack("<h", uc.mem_read(self.draw_node + 8, 2))[0]
                dy = struct.unpack("<h", uc.mem_read(self.draw_node + 0x0A, 2))[0]
                uc.mem_write(
                    self.draw_node + 8, struct.pack("<h", s16(dx + 1))
                )
                uc.mem_write(
                    self.draw_node + 0x0A, struct.pack("<h", s16(dy + 1))
                )
            uc.reg_write(arm.UC_ARM_REG_R0, (0xD00D0000 ^ r2) & 0xFFFFFFFF)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_callback(self, uc, address: int, size: int, user_data) -> None:
        value = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("flush", address, value))
        case = self.case

        base = read_u32(uc, GLOBAL_ADDR)
        node_address = base + RENDER_STACK_OFFSET

        if case.get("callback_switch_base"):
            self._write_global(RENDER_BASE_2)
        if case.get("callback_bump_depth"):
            depth = read_u32(uc, node_address)
            write_u32(uc, node_address, depth + 1)
        if case.get("callback_set_dirty"):
            uc.mem_write(node_address + 0x18, b"\x01")

        uc.reg_write(arm.UC_ARM_REG_R0, callback_return(address, value))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
            self.writes.append((address, size, value & ((1 << (8 * size)) - 1)))

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict, rodata: bytes = b"") -> dict:
        uc = self.uc
        self.call_log = []
        self.writes = []
        self.case = case
        self.scale_calls = 0
        self.draw_node = 0

        uc.mem_write(DATA_ADDR, b"\xCC" * DATA_SIZE)
        uc.mem_write(NODE_ADDR, b"\xCC" * NODE_SIZE)
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.mem_write(FUNC_ADDR, b"\x00" * FUNC_SIZE)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(CTX_ADDR, build_ctx(case))
        uc.mem_write(NODE_ADDR, build_node_page(case))
        uc.mem_write(CAND_RODATA, rodata)
        self._write_global(render_base(case))
        uc.mem_write(
            RENDER_BASE_1 + RENDER_STACK_OFFSET, build_render_node(case, 1)
        )
        uc.mem_write(
            RENDER_BASE_2 + RENDER_STACK_OFFSET, build_render_node(case, 2)
        )
        uc.ctl_flush_tb()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, case["context"])
        uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)
        for name, value in VFP_SAVED_START.items():
            uc.reg_write(VFP_SAVED[name], value)
        for index in range(1, 16):
            uc.reg_write(
                getattr(arm, f"UC_ARM_REG_S{index}"), 0x3F800000 + index
            )

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
            "node_page": bytes(uc.mem_read(NODE_ADDR, NODE_SIZE)),
            "callback_page": bytes(uc.mem_read(CALLBACK_PAGE, 0x20)),
            "base": read_u32(uc, GLOBAL_ADDR),
            "ctx": bytes(uc.mem_read(CTX_ADDR, CTX_SIZE)),
            "nodes": {
                1: bytes(uc.mem_read(RENDER_BASE_1 + RENDER_STACK_OFFSET, 0x20)),
                2: bytes(uc.mem_read(RENDER_BASE_2 + RENDER_STACK_OFFSET, 0x20)),
            },
        }


def render_base(case: dict) -> int:
    return RENDER_BASE_1 if case["base"] == "1" else RENDER_BASE_2


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "flag": 0,
        "state": 0,
        "scale_bits": 0x3F800000,
        "anchor_x": 0x00012000,   # 18.0
        "anchor_y": 0xFFFE0000,   # -32.0
        "base": "1",
        "draw_node": "A",
        "node_A_x": 4,
        "node_A_y": -6,
        "node_B_x": -0x80,
        "node_B_y": 0x60,
        "node1_depth": 0,
        "node1_slots": (FIRST_VALUE, 0xDEAD0001, 0xDEAD0002, 0xDEAD0003),
        "node1_dirty": 0,
        "node1_callback": CALLBACK_A,
        "node2_depth": 0,
        "node2_slots": (SECOND_VALUE, 0xDEAD0004, 0xDEAD0005, 0xDEAD0006),
        "node2_dirty": 0,
        "node2_callback": CALLBACK_A,
        "context": CTX_ADDR,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- flag gate ---------------------------------------------------------
    for flag in (0x01, 0x80, 0xFF):
        cases.append(base_case(f"flag 0x{flag:02x} returns", flag=flag))
    cases.append(base_case("flag wins over state 4", flag=0xFF, state=4))

    # --- signed state gate -------------------------------------------------
    for state in (4, 0x7FFFFFFF):
        cases.append(
            base_case(f"state 0x{state:08x} returns", state=state)
        )
    cases.append(base_case("state 3 continues", state=3))
    cases.append(base_case("state 2 continues", state=2))
    for state in (0xFFFFFFFF, 0x80000000, 0xFFFFFFFE):
        cases.append(
            base_case(f"state 0x{state:08x} continues", state=state)
        )

    # --- scale helper and state re-read ------------------------------------
    for bits in (0x00000000, 0x80000000, 0x7FC00000, 0xFF800000, 0x7F7FFFFF):
        cases.append(
            base_case(f"scale bits 0x{bits:08x}", scale_bits=bits)
        )
    cases.append(
        base_case("scale helper rewrites state 0 -> 2", state=0,
                  scale_sets_state=2)
    )
    cases.append(
        base_case("scale helper rewrites state 3 -> 0xFFFFFFFF",
                  state=3, scale_sets_state=0xFFFFFFFF)
    )

    # --- stack depth and callback matrix -----------------------------------
    for depth in (0, 1, 2, 3):
        slots = [0xAAAA0000 + depth, 0xBBBB0000, 0xCCCC0000, 0xDDDD0000]
        slots[depth] = FIRST_VALUE
        cases.append(
            base_case(f"node1 depth {depth} equal slot (no first flush)",
                      node1_depth=depth, node1_slots=tuple(slots))
        )
        slots = [0xAAAA0000 + depth, 0xBBBB0000, 0xCCCC0000, 0xDDDD0000]
        cases.append(
            base_case(f"node1 depth {depth} differing slot (first flush)",
                      node1_depth=depth, node1_slots=tuple(slots))
        )
    cases.append(
        base_case("node1 dirty with equal slot (dirty-only flush)",
                  node1_dirty=1)
    )
    cases.append(
        base_case("node1 dirty and differing slot", node1_dirty=1,
                  node1_slots=(0, 0, 0, 0))
    )
    # The original has no bounds check: depth 4 addresses node+0x18, i.e. the
    # dirty byte and its padding, and then reads the callback from +0x1C.
    cases.append(
        base_case("node1 depth 4 flat slot overlaps the dirty byte",
                  node1_depth=4,
                  node1_slots=(0x11111111, 0x22222222, 0x33333333, 0x44444444))
    )
    for depth in (0, 3):
        slots = [0x55550000, 0x55550001, 0x55550002, 0x55550003]
        slots[depth] = FIRST_VALUE
        cases.append(
            base_case(f"node1 depth {depth}, second store flushes the slot",
                      node1_depth=depth, node1_slots=tuple(slots))
        )
    cases.append(
        base_case("both nodes dirty (both flushes)", node1_dirty=1,
                  node2_dirty=1)
    )
    cases.append(
        base_case("callback target B on both nodes",
                  node1_callback=CALLBACK_B, node2_callback=CALLBACK_B,
                  node1_slots=(0, 0, 0, 0), node2_slots=(0, 0, 0, 0))
    )
    # A callback can move the depth so the second store lands on a slot that
    # already holds the second descriptor: first flush, then no flush.
    cases.append(
        base_case("callback bumps depth, second store reads equal slot",
                  node1_slots=(0, SECOND_VALUE, 0, 0),
                  callback_bump_depth=True)
    )
    cases.append(
        base_case("callback bumps depth, second store still differs",
                  node1_slots=(0, 0, 0, 0), callback_bump_depth=True)
    )

    # --- base switches -----------------------------------------------------
    cases.append(
        base_case("resolver switches base before first read",
                  resolver_switch_base=True)
    )
    cases.append(
        base_case("first command builder switches base after read",
                  cmd_switch_first=True)
    )
    cases.append(
        base_case("first command switches base, second store hits node2 depth 3",
                  cmd_switch_first=True, node2_depth=3,
                  node2_slots=(0x10101010, 0x20202020, 0x30303030,
                               SECOND_VALUE))
    )
    cases.append(
        base_case("first command switches base, node2 callback target B",
                  cmd_switch_first=True, node2_callback=CALLBACK_B,
                  node2_slots=(0, 0, 0, 0))
    )
    cases.append(
        base_case("first callback switches base before second read",
                  node1_slots=(0, 0, 0, 0), callback_switch_base=True,
                  node2_slots=(0, 0, 0, 0))
    )
    cases.append(
        base_case("second command builder switches base after read",
                  cmd_switch_second=True)
    )
    cases.append(
        base_case("callback bumps depth on node1",
                  node1_slots=(0, 0, 0, 0), callback_bump_depth=True,
                  node2_slots=(0, 0, 0, 0))
    )
    cases.append(
        base_case("callback sets dirty after flush",
                  node1_slots=(0, 0, 0, 0), callback_set_dirty=True)
    )
    cases.append(
        base_case("combined: dual callbacks, bump depth, base switch",
                  node1_slots=(0, 0, 0, 0), node1_dirty=1,
                  node2_slots=(0, 0, 0, 0), node2_dirty=1,
                  callback_bump_depth=True, callback_switch_base=True)
    )
    cases.append(
        base_case("initial base 2", base="2")
    )

    # --- draw node selection, offsets and re-reads -------------------------
    cases.append(base_case("draw node variant B", draw_node="B"))
    for x, y in ((0x7FFF, -0x8000), (-0x8000, 0x7FFF), (0, 0), (-1, 1)):
        cases.append(
            base_case(f"draw node boundary {x}/{y}",
                      node_A_x=x, node_A_y=y)
        )
    cases.append(
        base_case("draw node positions mutate after every draw",
                  mutate_node_on_draw=True,
                  node_A_x=0x7FFE, node_A_y=0x7FFE)
    )
    cases.append(
        base_case("draw node positions mutate, variant B",
                  mutate_node_on_draw=True, draw_node="B",
                  node_B_x=-3, node_B_y=-4)
    )

    # --- 20.12 source boundaries ------------------------------------------
    for value in (0x7FFFF000, 0x80000000, 0xFFFFFFFF, 0x00000FFF,
                  0x00001000, 0x7FFFFFFF, 0x00000000):
        cases.append(
            base_case(f"anchor x bits 0x{value:08x}", anchor_x=value)
        )
        cases.append(
            base_case(f"anchor y bits 0x{value:08x}", anchor_y=value)
        )

    # --- junk incoming registers are dead ---------------------------------
    cases.append(
        base_case("junk r1-r3 ignored", context=CTX_ADDR)
    )

    return cases


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "vfp_saved", "call_log"):
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
    for key in ("node_page", "callback_page"):
        if orig[key] != cand[key]:
            problems.append(f"{key} differs")
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
    bx_lr = b"\x1e\xff\x2f\xe1"
    assert result["callback_page"] == (
        bx_lr + b"\x00" * 0x0C + bx_lr + b"\x00" * 0x0C
    ), f"callback stubs modified on {name}"
    assert result["call_log"] == model["log"], (
        f"call log differs from model on {name}:\n"
        f"    actual={result['call_log']!r}\n    model={model['log']!r}"
    )
    assert result["ret"] == model["ret"], (
        f"r0 differs from model on {name}: "
        f"0x{result['ret']:08x} != 0x{model['ret']:08x}"
    )
    assert result["base"] == model["base"], f"render base differs on {name}"
    assert result["ctx"] == model["ctx"], f"context page differs from model on {name}"
    for which in (1, 2):
        assert result["nodes"][which] == model["nodes"][which], (
            f"render-stack node {which} differs from model on {name}:\n"
            f"    actual={result['nodes'][which].hex()}\n"
            f"    model={model['nodes'][which].hex()}"
        )
    assert result["node_page"] == model["node_page"], (
        f"resolver node page differs from model on {name}"
    )


def run_case_set(
    orig_code, cand_code, cand_rodata, cases, orig_machine, cand_machine
) -> int:
    passed = 0
    for case in cases:
        orig = orig_machine.run(orig_code, case, cand_rodata)
        cand = cand_machine.run(cand_code, case, cand_rodata)
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
    print("Testing ui_func_0025f538 (0x0025f538)...")
    orig_code = get_orig_bytes()
    cand_code, cand_rodata = compile_candidate_baseline()
    print(
        f"  original: {len(orig_code)} B, candidate: {len(cand_code)} B, "
        f"rodata: {len(cand_rodata)} B (relocations resolved)"
    )

    cases = make_cases()
    orig_machine = Machine()
    cand_machine = Machine()
    passed = run_case_set(
        orig_code, cand_code, cand_rodata, cases, orig_machine, cand_machine
    )

    # The original results are reused by the mutant controls.
    orig_results = {
        case["name"]: orig_machine.run(orig_code, case, cand_rodata)
        for case in cases
    }

    print("\nNegative controls:")
    mutants = (
        (
            "state_limit",
            "constexpr s32 kStateLimit = 3;",
            "constexpr s32 kStateLimit = 2;",
        ),
        (
            "flag_offset",
            "constexpr u32 kContextFlagOffset = 0x3084;",
            "constexpr u32 kContextFlagOffset = 0x3085;",
        ),
        (
            "state_offset",
            "constexpr u32 kContextStateOffset = 0x305C;",
            "constexpr u32 kContextStateOffset = 0x3060;",
        ),
        (
            "scale_offset",
            "constexpr u32 kContextScaleOffset = 0xCC;",
            "constexpr u32 kContextScaleOffset = 0xD0;",
        ),
        (
            "anchor_offset",
            "constexpr u32 kContextAnchorOffset = 0x12B8;",
            "constexpr u32 kContextAnchorOffset = 0x12B4;",
        ),
        (
            "stack_offset",
            "constexpr u32 kOverlayStackOffset = 0x12AC;",
            "constexpr u32 kOverlayStackOffset = 0x12B0;",
        ),
        (
            "node_group",
            "constexpr u32 kNodeGroup = 0x15;",
            "constexpr u32 kNodeGroup = 0x16;",
        ),
        (
            "node_bias",
            "constexpr u32 kNodeIndexBias = 0x52;",
            "constexpr u32 kNodeIndexBias = 0x53;",
        ),
        (
            "node_x_offset",
            "constexpr u32 kNodeXOffset = 8;",
            "constexpr u32 kNodeXOffset = 0x0C;",
        ),
        (
            "sprite_ids",
            "constexpr u32 kSpriteIds[4] = {0x4B, 0x4A, 0x4C, 0x4D};",
            "constexpr u32 kSpriteIds[4] = {0x4E, 0x4A, 0x4C, 0x4D};",
        ),
        (
            "sprite_attribute",
            "constexpr u32 kSpriteAttribute = 0x29;",
            "constexpr u32 kSpriteAttribute = 0x2A;",
        ),
        (
            "second_selector",
            "constexpr u32 kCommandSecondSelector = 7;",
            "constexpr u32 kCommandSecondSelector = 8;",
        ),
        (
            "final_scale",
            "constexpr f32 kFinalScale = 1.0f;",
            "constexpr f32 kFinalScale = 2.0f;",
        ),
        (
            "dirty_condition",
            "if (node->dirty != 0 || previous != value) {",
            "if (previous != value) {",
        ),
        (
            "first_base_read_order",
            "    u8* const first_base =\n"
            "        static_cast<u8*>(smt4::engine::g_RenderRegisterBase);\n"
            "    const u32 first_value =\n"
            "        battle_func_002c5fa4(kCommandKind, kCommandFirstSelector, 0);",
            "    const u32 first_value =\n"
            "        battle_func_002c5fa4(kCommandKind, kCommandFirstSelector, 0);\n"
            "    u8* const first_base =\n"
            "        static_cast<u8*>(smt4::engine::g_RenderRegisterBase);",
        ),
    )

    for name, old, new in mutants:
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        mutant_machine = Machine()
        detected = False
        for case in cases:
            orig = orig_results[case["name"]]
            try:
                bad = mutant_machine.run(mutant_code, case, mutant_rodata)
            except RuntimeError:
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
