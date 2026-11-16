#!/usr/bin/env python3
"""Differential test for func_00153a58 (0x00153a58) using Unicorn ARM emulation.

The routine appends skinning matrices to the GPU command stream rooted at
0x004652A0.  The two matrix-copy helpers (0x002A1A90 / 0x002A1AC8) are stubbed
in Python and reproduce the exact 12/13-word component re-ordering of the
original VFP code (this Unicorn build cannot execute VFP instructions).
The two model vtable slots (0x1c, 0x24) are stubbed with deterministic
MatrixListView objects.

Every case runs the pinned original and the compiled candidate on separate
machines with identical fixtures and compares:
  - the ordered call log (vtable slots + copy helpers, with arguments),
  - the final g_GpuCommandCursor value,
  - the whole 8 KiB command buffer,
  - the render-state word at render_state+0x14.
"""

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
FUNC_ADDR = 0x00153A58
FUNC_SIZE = 400
TU_PATH = ROOT / "src/engine/leaf_batch44_b.cpp"
OBJ_PATH = ROOT / "build/test_leaf_00153a58/leaf_batch44_b.o"

# ---------------------------------------------------------------------------
# Emulated address space
# ---------------------------------------------------------------------------
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000          # covers 0x153a58 and the helper stubs at 0x2a...
DATA_ADDR = 0x00400000
DATA_SIZE = 0x00100000          # covers globals, fixtures and the command buffer
LOW_ADDR = 0x00000000
LOW_SIZE = 0x00001000           # null-offset relative tables read address 0..3
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

# Direct-call stubs (original branch targets).
STUB_2A1A90 = 0x002A1A90
STUB_2A1AC8 = 0x002A1AC8
# Local noinline load helper emitted by the candidate translation unit.
STUB_LOAD_UNTABLED = 0x002A1C00
# Model vtable slot stubs.
STUB_LIST_ONE = 0x002A1B00
STUB_LIST_TWO = 0x002A1B10

# Fixture objects (DATA range).
SCENE = 0x00431000
SCENE_RENDER = 0x00431100
RENDER_STATE = 0x00431200
UNIT = 0x00431300
MODEL = 0x00431400
CHAIN_ROOT = 0x00431500
DRAW_ENTRY = 0x00431600
INDEX_ARRAY = 0x00431700
LIST1_VIEW = 0x00431800
LIST2_VIEW = 0x00431900
VTABLE = 0x00431A00
CMD_BUFFER = 0x00440000
CMD_BUFFER_SIZE = 0x2000
MATRIX_ONE = 0x00480000
MATRIX_TWO = 0x00490000
MATRIX_AREA_SIZE = 0x00010000
CHAIN_TABLE = 0x004A0000
CHAIN_TABLE_SIZE = 0x00030000
CURSOR_GLOBAL = 0x004652A0

BX_LR = 0xE12FFF1E

# Chain record node offset used by the fixture (relative to record+0x28).
NODE_DELTA = 0x1000
NODE_STRIDE = 0x40
MAX_ELEMENT = (MATRIX_AREA_SIZE // 48) - 1

GLOBAL_CURSOR_SYMBOL = "g_GpuCommandCursor"


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def compile_candidate():
    OBJ_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = compile_tu_armv6k(TU_PATH, OBJ_PATH, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")

    funcs = extract_elf_functions_detailed(OBJ_PATH)
    if "func_00153a58" not in funcs:
        raise RuntimeError(
            f"func_00153a58 not found in {OBJ_PATH}: {sorted(funcs)}"
        )
    raw, relocs = funcs["func_00153a58"]
    code = bytearray(raw)

    helper_name = None
    helper_code = None
    for name, (helper_raw, helper_relocs) in funcs.items():
        if "LoadUntabled" in name:
            if helper_relocs:
                raise RuntimeError(f"helper relocations unsupported: {helper_relocs}")
            helper_name = name
            helper_code = helper_raw
            break
    if helper_name is None:
        raise RuntimeError(f"LoadUntabled helper not found in {OBJ_PATH}")

    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            targets = {
                "func_002a1a90": STUB_2A1A90,
                "func_002a1ac8": STUB_2A1AC8,
                helper_name: STUB_LOAD_UNTABLED,
            }
            if rel.symbol_name not in targets:
                raise RuntimeError(f"unexpected call relocation: {rel}")
            target = targets[rel.symbol_name]
            inst = struct.unpack_from("<I", code, rel.offset)[0]
            # R_ARM_CALL encodes S + A - P; the pre-relocation addend is -8.
            addend = sign_extend_24(inst & 0x00FFFFFF) << 2
            place = FUNC_ADDR + rel.offset
            disp = (target + addend - place) >> 2
            struct.pack_into(
                "<I", code, rel.offset, (inst & 0xFF000000) | (disp & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            if rel.symbol_name != GLOBAL_CURSOR_SYMBOL:
                raise RuntimeError(f"unexpected abs32 relocation: {rel}")
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if addend != 0:
                raise RuntimeError(f"unexpected {GLOBAL_CURSOR_SYMBOL} addend {addend}")
            struct.pack_into("<I", code, rel.offset, CURSOR_GLOBAL)
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")
    return bytes(code), {STUB_LOAD_UNTABLED: bytes(helper_code)}


def sign_extend_24(value):
    return value - 0x1000000 if value & 0x800000 else value


# ---------------------------------------------------------------------------
# Emulated helper functions (exact copies of the original VFP bodies)
# ---------------------------------------------------------------------------
def copy_matrix_12(uc, dst, src):
    """0x002A1A90: 12 floats from src, reordered into dst[0..11]."""
    w = struct.unpack("<12I", uc.mem_read(src, 48))
    out = [0] * 12
    out[3], out[2], out[1], out[0] = w[0], w[1], w[2], w[3]
    out[7], out[6], out[5], out[4] = w[4], w[5], w[6], w[7]
    out[11], out[10], out[9], out[8] = w[8], w[9], w[10], w[11]
    uc.mem_write(dst, struct.pack("<12I", *out))


def copy_matrix_13(uc, dst, src, tag):
    """0x002A1AC8: 12 floats from src reordered around the tag word."""
    w = struct.unpack("<12I", uc.mem_read(src, 48))
    out = [0] * 13
    out[1] = tag
    out[4], out[3], out[2], out[0] = w[0], w[1], w[2], w[3]
    out[8], out[7], out[6], out[5] = w[4], w[5], w[6], w[7]
    out[12], out[11], out[10], out[9] = w[8], w[9], w[10], w[11]
    uc.mem_write(dst, struct.pack("<13I", *out))


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(LOW_ADDR, LOW_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.call_log = []
        self._install_stubs()

    def _install_stubs(self):
        arm_bx_lr = struct.pack("<I", BX_LR)
        for addr, hook in (
            (STUB_2A1A90, self._on_copy_12),
            (STUB_2A1AC8, self._on_copy_13),
            (STUB_LIST_ONE, self._on_list_one),
            (STUB_LIST_TWO, self._on_list_two),
        ):
            self.uc.mem_write(addr, arm_bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, hook, begin=addr, end=addr)

    def _on_copy_12(self, uc, address, size, user_data):
        dst = uc.reg_read(arm.UC_ARM_REG_R0)
        src = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("copy12", dst, src))
        copy_matrix_12(uc, dst, src)

    def _on_copy_13(self, uc, address, size, user_data):
        dst = uc.reg_read(arm.UC_ARM_REG_R0)
        src = uc.reg_read(arm.UC_ARM_REG_R1)
        tag = uc.reg_read(arm.UC_ARM_REG_R2)
        self.call_log.append(("copy13", dst, src, tag))
        copy_matrix_13(uc, dst, src, tag)

    def _on_list_one(self, uc, address, size, user_data):
        model = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("list_slot_1c", model))
        uc.reg_write(arm.UC_ARM_REG_R0, LIST1_VIEW)

    def _on_list_two(self, uc, address, size, user_data):
        model = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("list_slot_24", model))
        uc.reg_write(arm.UC_ARM_REG_R0, LIST2_VIEW)

    def run(self, code, blobs, case):
        uc = self.uc
        self.call_log = []
        # Wipe mutable regions so cases never leak into each other.
        uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        uc.mem_write(LOW_ADDR, b"\x00" * LOW_SIZE)
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.mem_write(FUNC_ADDR, code)
        for addr, blob in blobs.items():
            uc.mem_write(addr, blob)
        # Unicorn 2.1.4 keeps translated blocks across mem_write; drop them.
        uc.ctl_flush_tb()
        # Command buffer sentinel: any unwritten byte stays 0xCC.
        uc.mem_write(CMD_BUFFER, b"\xCC" * CMD_BUFFER_SIZE)

        # Deterministic, position-dependent matrix contents.
        one = struct.pack(
            "<%dI" % (MATRIX_AREA_SIZE // 4),
            *[(0x10000000 + i * 0x00010001) & 0xFFFFFFFF
              for i in range(MATRIX_AREA_SIZE // 4)]
        )
        two = struct.pack(
            "<%dI" % (MATRIX_AREA_SIZE // 4),
            *[(0x20000000 + i * 0x00010003) & 0xFFFFFFFF
              for i in range(MATRIX_AREA_SIZE // 4)]
        )
        uc.mem_write(MATRIX_ONE, one)
        uc.mem_write(MATRIX_TWO, two)
        uc.mem_write(CHAIN_TABLE, b"\x00" * CHAIN_TABLE_SIZE)

        # Scene -> render context -> render state.
        _write_u32(uc, SCENE + 0x08, SCENE_RENDER)
        _write_u32(uc, SCENE_RENDER + 0x08, RENDER_STATE)
        _write_u32(uc, RENDER_STATE + 0x14, case["initial_flags"])

        # Unit -> model (+0x220); model vtable and chain root.
        _write_u32(uc, UNIT + 0x220, MODEL)
        _write_u32(uc, MODEL + 0x00, VTABLE)
        _write_u32(uc, MODEL + 0x08, CHAIN_ROOT)
        _write_u32(uc, VTABLE + 0x1C, STUB_LIST_ONE)
        _write_u32(uc, VTABLE + 0x24, STUB_LIST_TWO)

        # Matrix list views returned by the vtable stubs.
        _write_u32(uc, LIST1_VIEW + 0x04, MATRIX_ONE)
        _write_u32(uc, LIST2_VIEW + 0x04, MATRIX_TWO)

        # Draw entry: +4 relative index array, +8 entry type.
        _write_u32(uc, DRAW_ENTRY + 0x08, case["entry_type"])
        if case["zero_index_offset"]:
            _write_u32(uc, DRAW_ENTRY + 0x04, 0)
        else:
            _write_u32(uc, DRAW_ENTRY + 0x04, INDEX_ARRAY - (DRAW_ENTRY + 0x04))

        if case["zero_chain_offset"]:
            _write_u32(uc, CHAIN_ROOT + 0x1C, 0)
        else:
            _write_u32(uc, CHAIN_ROOT + 0x1C, CHAIN_TABLE - (CHAIN_ROOT + 0x1C))

        # Index array and per-element node flags.
        for i, (element, node_flags) in enumerate(case["elements"]):
            if case["zero_index_offset"]:
                _write_u32(uc, LOW_ADDR + i * 4, element)
            else:
                _write_u32(uc, INDEX_ARRAY + i * 4, element)

            if case["zero_chain_offset"]:
                # record lookup is skipped; flags are read at address 0x4
                _write_u32(uc, LOW_ADDR + 4, node_flags)
            else:
                record = CHAIN_TABLE + element * 16
                if case.get("zero_node_offset", False):
                    # zero node offset falls back to flags at address 0x4
                    _write_u32(uc, record + 0x28, 0)
                    _write_u32(uc, LOW_ADDR + 4, node_flags)
                else:
                    node = record + 0x28 + NODE_DELTA + element * NODE_STRIDE
                    _write_u32(uc, record + 0x28, NODE_DELTA + element * NODE_STRIDE)
                    _write_u32(uc, node + 0x04, node_flags)

        _write_u32(uc, CURSOR_GLOBAL, case["initial_cursor"])

        sp = STACK_ADDR + STACK_SIZE - 0x100
        uc.reg_write(arm.UC_ARM_REG_SP, sp)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, SCENE)
        uc.reg_write(arm.UC_ARM_REG_R1, UNIT)
        uc.reg_write(arm.UC_ARM_REG_R2, DRAW_ENTRY)
        uc.reg_write(arm.UC_ARM_REG_R3, case["count"] & 0xFFFFFFFF)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
        except Exception as exc:  # pragma: no cover - diagnostic path
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {exc}") from exc

        return {
            "call_log": list(self.call_log),
            "cursor": _read_u32(uc, CURSOR_GLOBAL),
            "flags": _read_u32(uc, RENDER_STATE + 0x14),
            "command_buffer": bytes(uc.mem_read(CMD_BUFFER, CMD_BUFFER_SIZE)),
        }


def _write_u32(uc, addr, value):
    uc.mem_write(addr, struct.pack("<I", value & 0xFFFFFFFF))


def _read_u32(uc, addr):
    return struct.unpack("<I", uc.mem_read(addr, 4))[0]


# ---------------------------------------------------------------------------
# Expected values (independent of the original)
# ---------------------------------------------------------------------------
def expected_tag(count):
    return (0xFFF00000 + (((count & 0xFFFFFFFF) * 3) << 22)) & 0xFFFFFFFF | 0x000F02C1


def selected_list(case, node_flags):
    """True when the secondary (slot 0x24) list must be selected."""
    if case["entry_type"] != 2:
        return False
    return ((node_flags >> 9) & 1) != 0


def expected_flags(case):
    if case["entry_type"] == 2:
        return ((case["initial_flags"] & ~6) | 2) & 0xFFFFFFFF
    return ((case["initial_flags"] & ~6) | 4) & 0xFFFFFFFF


def check_expectations(case, result):
    count = case["count"]
    flags = expected_flags(case)
    assert result["flags"] == flags, (
        f"flags mismatch on {case['name']}: 0x{result['flags']:08x} != 0x{flags:08x}"
    )

    words = struct.unpack_from("<%dI" % (CMD_BUFFER_SIZE // 4), result["command_buffer"])
    cursor = case["initial_cursor"]
    copy_calls = [c for c in result["call_log"] if c[0] in ("copy12", "copy13")]
    assert [c[0] for c in result["call_log"][:2]] == ["list_slot_1c", "list_slot_24"], (
        f"vtable slot order wrong on {case['name']}: {result['call_log']}"
    )

    if count <= 0:
        assert copy_calls == [], f"unexpected copies on {case['name']}: {copy_calls}"
        assert result["cursor"] == (cursor + 4) & 0xFFFFFFFF, (
            f"cursor on empty {case['name']}: 0x{result['cursor']:08x}"
        )
        return

    assert len(copy_calls) == count, (
        f"copy count on {case['name']}: {len(copy_calls)} != {count}"
    )
    base = cursor - CMD_BUFFER
    # Header of the first block.
    assert words[base // 4 + 0] == 0x80000019, f"header[0] on {case['name']}"
    assert words[base // 4 + 1] == 0x000F02C0, f"header[1] on {case['name']}"
    assert words[base // 4 + 3] == expected_tag(count), (
        f"tag on {case['name']}: 0x{words[base // 4 + 3]:08x} != 0x{expected_tag(count):08x}"
    )
    assert copy_calls[0][0] == "copy13", f"first copy must be copy13 on {case['name']}"
    assert copy_calls[0][1] == cursor + 8, f"copy13 dst on {case['name']}"
    for c in copy_calls[1:]:
        assert c[0] == "copy12", f"later copies must be copy12 on {case['name']}"

    # Verify the list chosen for every element and the matrix bytes copied.
    for i, (element, node_flags) in enumerate(case["elements"][:count]):
        secondary = selected_list(case, node_flags)
        matrix_base = (MATRIX_TWO if secondary else MATRIX_ONE)
        src = (matrix_base + ((element * 3) << 4)) & 0xFFFFFFFF
        if i == 0:
            assert copy_calls[0][2] == src, (
                f"src[0] on {case['name']}: 0x{copy_calls[0][2]:08x} != 0x{src:08x}"
            )
            dst = cursor + 8
        else:
            assert copy_calls[i][2] == src, (
                f"src[{i}] on {case['name']}: 0x{copy_calls[i][2]:08x} != 0x{src:08x}"
            )
            dst = cursor + 0x3C + (i - 1) * 0x30
            assert copy_calls[i][1] == dst, f"copy12 dst[{i}] on {case['name']}"

        wsrc = struct.unpack("<12I", _pattern_slice(secondary, element))
        if i == 0:
            # copy13 inserts the tag at dst word 1 and interleaves the floats.
            _check_block(words, case, dst, wsrc, PERM_13)
            assert words[(dst - CMD_BUFFER) // 4 + 1] == expected_tag(count)
        else:
            _check_block(words, case, dst, wsrc, PERM_12)

    # Cursor: 0x3c header block + (count-1) * 0x30 + trailing 4.
    expect_cursor = (cursor + 0x3C + (count - 1) * 0x30 + 4) & 0xFFFFFFFF
    assert result["cursor"] == expect_cursor, (
        f"cursor on {case['name']}: 0x{result['cursor']:08x} != 0x{expect_cursor:08x}"
    )


def _pattern_slice(secondary, element):
    base = 0x20000000 if secondary else 0x10000000
    step = 0x00010003 if secondary else 0x00010001
    return struct.pack("<12I", *[(base + (element * 12 + k) * step) & 0xFFFFFFFF
                                 for k in range(12)])


# Source-word index -> destination-word index of the two helper bodies.
PERM_12 = {0: 3, 1: 2, 2: 1, 3: 0, 4: 7, 5: 6, 6: 5, 7: 4,
           8: 11, 9: 10, 10: 9, 11: 8}
PERM_13 = {0: 4, 1: 3, 2: 2, 3: 0, 4: 8, 5: 7, 6: 6, 7: 5,
           8: 12, 9: 11, 10: 10, 11: 9}


def _check_block(words, case, dst, wsrc, perm):
    for src_word, dst_word in perm.items():
        got = words[(dst - CMD_BUFFER) // 4 + dst_word]
        assert got == wsrc[src_word], (
            f"matrix word {src_word} on {case['name']}: "
            f"0x{got:08x} != 0x{wsrc[src_word]:08x}"
        )


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def build_cases():
    cases = []

    def add(name, **kw):
        case = {
            "name": name,
            "count": 0,
            "entry_type": 2,
            "initial_flags": 0xFFFFFFFF,
            "initial_cursor": CMD_BUFFER,
            "elements": [],
            "zero_index_offset": False,
            "zero_chain_offset": False,
            "zero_node_offset": False,
        }
        case.update(kw)
        # Pattern slices are derived from the matrix pattern; rebuild them to
        # match Machine.run's actual fill.
        cases.append(case)

    add(
        "positive: type!=2 forces state bits and primary list (bit9 set)",
        count=1,
        entry_type=3,
        initial_flags=0x12345000,
        elements=[(0, 0x200)],
    )
    add(
        "positive: type==2, bit9 clear -> primary list",
        count=1,
        entry_type=2,
        initial_flags=0xFFFFFFFF,
        elements=[(0, 0x000)],
    )
    add(
        "positive: type==2, bit9 set -> secondary list",
        count=1,
        entry_type=2,
        initial_flags=0xFFFFFFFF,
        elements=[(0, 0x200)],
    )
    add(
        "boundary: type==2 mixed flag bits across three elements",
        count=3,
        entry_type=2,
        initial_flags=0xFFFF0000,
        elements=[(0, 0x000), (1, 0x200), (2, 0xFFFFFDFF)],
    )
    add(
        "boundary: type==0 masks bit9 and sets both state bits",
        count=4,
        entry_type=0,
        initial_flags=0x80000001,
        elements=[(7, 0x200), (3, 0x000), (7, 0x200), (0, 0xFFFFFFFF)],
    )
    add(
        "boundary: non-contiguous element indices select distinct matrices",
        count=2,
        entry_type=2,
        initial_flags=0x00000006,
        elements=[(11, 0x200), (5, 0x000)],
    )
    add(
        "zero count: only trailing word and state update",
        count=0,
        entry_type=2,
        initial_flags=0xABCDEF87,
        elements=[],
    )
    add(
        "negative count: only trailing word and state update",
        count=-1,
        entry_type=3,
        initial_flags=0xABCDEF87,
        elements=[],
    )
    add(
        "boundary: large element index 1000",
        count=1,
        entry_type=2,
        initial_flags=0,
        elements=[(1000, 0x200)],
    )
    add(
        "boundary: maximum matrix element index",
        count=1,
        entry_type=2,
        initial_flags=0,
        elements=[(MAX_ELEMENT, 0x000)],
    )
    add(
        "negative control: entry_type 0xFFFFFFFF behaves as non-two",
        count=1,
        entry_type=0xFFFFFFFF,
        initial_flags=0x55555555,
        elements=[(2, 0x200)],
    )
    add(
        "negative control: node flag word 0xFFFFFFFF uses secondary (type 2)",
        count=1,
        entry_type=2,
        initial_flags=0xFFFFFFFF,
        elements=[(4, 0xFFFFFFFF)],
    )
    add(
        "null-offset: zero index offset reads the index from address 0",
        count=1,
        entry_type=2,
        initial_flags=0xFFFFFFFF,
        elements=[(6, 0x200)],
        zero_index_offset=True,
    )
    add(
        "null-offset: zero node offset reads node flags from address 4",
        count=1,
        entry_type=2,
        initial_flags=0xFFFFFFFF,
        elements=[(2, 0x200)],
        zero_node_offset=True,
    )
    add(
        "null-offset: zero chain offset reads node flags from address 4",
        count=1,
        entry_type=2,
        initial_flags=0xFFFFFFFF,
        elements=[(6, 0x200)],
        zero_chain_offset=True,
    )
    add(
        "null-offset: zero index and chain offsets in one call",
        count=1,
        entry_type=2,
        initial_flags=0,
        elements=[(1, 0x000)],
        zero_index_offset=True,
        zero_chain_offset=True,
    )
    add(
        "boundary: initial state already has unrelated bits",
        count=1,
        entry_type=2,
        initial_flags=0xA5A5A5A5,
        elements=[(0, 0x200)],
    )
    add(
        "boundary: initial cursor at non-zero offset",
        count=2,
        entry_type=2,
        initial_flags=0xFFFFFFFF,
        initial_cursor=CMD_BUFFER + 0x400,
        elements=[(9, 0x200), (10, 0x000)],
    )
    return cases


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Testing func_00153a58 (0x00153a58)...")
    orig_code = get_orig_bytes()
    cand_code, cand_blobs = compile_candidate()
    print(f"  original: {len(orig_code)} B, candidate: {len(cand_code)} B")

    runner = Machine()
    cases = build_cases()
    passed = 0
    for case in cases:
        res_orig = runner.run(orig_code, {}, case)
        res_cand = runner.run(cand_code, cand_blobs, case)

        assert res_orig["call_log"] == res_cand["call_log"], (
            f"Call log mismatch on {case['name']}:\n"
            f"  Orig: {res_orig['call_log']}\n  Cand: {res_cand['call_log']}"
        )
        assert res_orig["cursor"] == res_cand["cursor"], (
            f"Cursor mismatch on {case['name']}: "
            f"0x{res_orig['cursor']:08x} != 0x{res_cand['cursor']:08x}"
        )
        assert res_orig["flags"] == res_cand["flags"], (
            f"State flags mismatch on {case['name']}: "
            f"0x{res_orig['flags']:08x} != 0x{res_cand['flags']:08x}"
        )
        assert res_orig["command_buffer"] == res_cand["command_buffer"], (
            f"Command buffer mismatch on {case['name']}"
        )
        check_expectations(case, res_cand)

        passed += 1
        print(f"  [PASS] {case['name']}")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
