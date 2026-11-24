#!/usr/bin/env python3
"""Differential test for ui_func_002247c8 (0x002247c8) using Unicorn ARM.

Compiles ``src/engine/leaf_batch42_b.cpp``, extracts the ``ui_func_002247c8``
body, resolves its five direct calls (0x002C0AC8, 0x00286834, 0x002C5F7C,
0x002C5FA4, 0x00281ADC) plus the 0x0044EA00 render-register global, then runs
the pinned original (``extracted/exefs/code.bin``) and the candidate on separate
Unicorn ARM machines with identical fixtures.

Compared output per case:
  * returned r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log: the handle passed to the object lookup, the packed
    command helpers with every core argument, the incoming VFP s0 of
    0x00286834 (the routine must force it to +0.0f), the state pointer handed
    to 0x00281ADC, and every indirect flush callback (target address and value);
  * the complete observable 2 MiB data region (object page, render-register
    global, both render bases, both sets of three stack nodes and the stack);
  * the ordered list of writes outside the private stack.

The three command stacks live at ``*0x0044EA00 + {0x126C, 0x124C, 0x12AC}`` and
share the push/pop layout ``{u32 count; u32 pad; u32 slots[4]; u8 dirty;
u32 flush_cb}``.  Helpers are deterministic stubs placed at the original call
targets; 0x00286834, 0x002C5F7C and 0x002C5FA4 reproduce their real bit-building
formulas, while 0x002C0AC8 returns the fixture object (or null) and 0x00281ADC
returns an argument-dependent sentinel.

Coverage:
  * the +0x10 gate: zero and non-zero bytes, the neighbouring bytes proving only
    the single gate byte is read, and a null lookup result (both bodies fault on
    the same ``ldrb``, after the same single call);
  * handle values across the 32-bit range, forwarded unchanged to the lookup;
  * stack counts 0..3 for every one of the three nodes (count 3 pushes the new
    word over the dirty byte at +0x18) and count 2 for the in-bounds top;
  * dirty cleared/set, slot values equal/different from the pushed word, so the
    flush fires on push only, pop only or both ends;
  * two indirect callback targets per node and a callback that switches the
    render base to the second node set, plus a 0x00281ADC stub that switches the
    base between the pushes and the pops (the original re-reads 0x0044EA00);
  * junk r0-r3/s0-s15 on entry, including an s0 value that the reconstruction
    must overwrite with 0.0f.

Negative controls mutate the gate offset, a stack offset, a helper argument,
the forced s0 constant, the callback argument and the early-exit return value;
each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch42_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_002247c8"

FUNC_ADDR = 0x002247C8
FUNC_SIZE = 504

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x00300000
DATA_ADDR = 0x00400000
DATA_SIZE = 0x00200000  # global, render bases, object page, candidate stack
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
CALLBACK_PAGE = 0x90001000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

GLOBAL_ADDR = 0x0044EA00
RENDER_BASE_1 = 0x00500000
RENDER_BASE_2 = 0x00540000
OBJ_ADDR = 0x00580000
OBJ_SIZE = 0x100
STATE_ADDR = 0x00590000

FIRST_OFFSET = 0x126C
SECOND_OFFSET = 0x124C
THIRD_OFFSET = 0x12AC
NODE_SIZE = 0x20  # count, pad, four slots, dirty, then the callback at +0x1C

LOOKUP = 0x002C0AC8
ENGINE_PACK = 0x00286834
VIEWPORT_PACK = 0x002C5F7C
BATTLE_PACK = 0x002C5FA4
STATE_CONSUME = 0x00281ADC

STUB_NAMES = {
    LOOKUP: "ui_func_002c0ac8",
    ENGINE_PACK: "engine_func_00286834",
    VIEWPORT_PACK: "ui_func_002c5f7c",
    BATTLE_PACK: "battle_func_002c5fa4",
    STATE_CONSUME: "engine_func_00281adc",
}

CALLBACKS = {
    "A": 0x90001000,
    "B": 0x90001010,
    "C": 0x90001020,
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
# Float helpers (single precision, matching the VFP reads of the stubs)
# ---------------------------------------------------------------------------
def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def bits_to_f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def f32_to_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("ui_func_002247c8")
    if candidate is None:
        raise RuntimeError(
            f"ui_func_002247c8 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(f"unexpected relocation: {rel}")
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
    return bytes(code)


def compile_candidate(src: Path, obj: Path) -> bytes:
    obj.parent.mkdir(parents=True, exist_ok=True)
    result = compile_tu_armv6k(src, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compilation failed for {src}:\n{result.stderr}")
    return relocate_candidate(obj)


def compile_candidate_baseline() -> bytes:
    return compile_candidate(SOURCE, OUT_DIR / "leaf_batch42_b.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant = OUT_DIR / f"mutant_{name}.cpp"
    mutant.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def engine_pack(kind: int, s0_bits: int) -> int:
    """0x00286834: ((kind != 1) | kind << 4) | ((u32)(0.5f + s0*255.0f) & 0xFF) << 8."""
    s0 = bits_to_f32(s0_bits)
    product = f32(f32(s0) * f32(255.0))
    total = f32(f32(0.5) + product)
    # vcvt.u32.f32 truncates toward zero.
    converted = int(total) if total == total else 0
    converted &= 0xFF
    selector = 0 if (kind & 0xFFFFFFFF) == 1 else 1
    return (selector | ((kind << 4) & 0xFFFFFFFF) | (converted << 8)) & 0xFFFFFFFF


def viewport_pack(kind: int, enabled: int) -> int:
    """0x002C5F7C: (kind == 1 ? 0 : 1) | kind << 4 | (enabled ? 0x1000 : 0) | 0xF00."""
    selector = 0 if (kind & 0xFFFFFFFF) == 1 else 1
    word = selector | ((kind << 4) & 0xFFFFFFFF)
    high = 0x1000 if (enabled & 0xFFFFFFFF) != 0 else 0
    return (high | word | 0xF00) & 0xFFFFFFFF


def battle_pack(kind: int, flag: int, mode: int) -> int:
    """0x002C5FA4: kind/mode/flag packed into the four byte lanes and both nibbles."""
    word = (mode | (mode << 8)) & 0xFFFFFFFF
    word |= (kind << 16) & 0xFFFFFFFF
    word |= (flag << 20) & 0xFFFFFFFF
    word |= (kind << 24) & 0xFFFFFFFF
    word |= (flag << 28) & 0xFFFFFFFF
    return word & 0xFFFFFFFF


def default_callback_value(callback: int, value: int) -> int:
    return (callback ^ (value * 0x01010101)) & 0xFFFFFFFF


BUILTIN_VALUES = {
    FIRST_OFFSET: engine_pack(6, 0),
    SECOND_OFFSET: viewport_pack(1, 0),
    THIRD_OFFSET: battle_pack(6, 1, 0),
}


def build_node(spec: dict) -> bytes:
    buffer = bytearray(NODE_SIZE)
    struct.pack_into("<I", buffer, 0x00, spec["count"] & 0xFFFFFFFF)
    for index, word in enumerate(spec["slots"]):
        struct.pack_into("<I", buffer, 0x08 + 4 * index, word & 0xFFFFFFFF)
    buffer[0x18] = spec["dirty"] & 0xFF
    struct.pack_into("<I", buffer, 0x1C, spec["callback"] & 0xFFFFFFFF)
    return bytes(buffer)


def node_spec(case: dict, base_tag: str, offset: int) -> dict:
    return case["nodes"][(base_tag, offset)]


def build_obj(case: dict) -> bytes:
    page = bytearray(OBJ_SIZE)
    struct.pack_into("<I", page, 0x0C, case.get("state", STATE_ADDR))
    for index in range(OBJ_SIZE):
        if index != 0x0C and index != 0x10:
            page[index] = (0x5A + index) & 0xFF
    page[0x10] = case.get("enabled", 1) & 0xFF
    for index in range(0x11, 0x14):
        page[index] = case.get(f"enabled_neighbor_{index}", 0xFF) & 0xFF
    return bytes(page)


def write_u32(uc, address: int, value: int) -> None:
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


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
        for address in CALLBACKS.values():
            self.uc.mem_write(address, struct.pack("<I", BX_LR))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_callback, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.switch_base = False

    # -------------------------------------------------------------- stubs
    def _on_helper(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == LOOKUP:
            self.call_log.append(("ui_func_002c0ac8", r0))
            uc.reg_write(
                arm.UC_ARM_REG_R0, OBJ_ADDR if self.case.get("found", True) else 0
            )
        elif address == ENGINE_PACK:
            s0_bits = uc.reg_read(arm.UC_ARM_REG_S0)
            self.call_log.append(("engine_func_00286834", r0, s0_bits))
            uc.reg_write(arm.UC_ARM_REG_R0, engine_pack(r0, s0_bits))
        elif address == VIEWPORT_PACK:
            self.call_log.append(("ui_func_002c5f7c", r0, r1))
            uc.reg_write(arm.UC_ARM_REG_R0, viewport_pack(r0, r1))
        elif address == BATTLE_PACK:
            self.call_log.append(("battle_func_002c5fa4", r0, r1, r2))
            uc.reg_write(arm.UC_ARM_REG_R0, battle_pack(r0, r1, r2))
        elif address == STATE_CONSUME:
            self.call_log.append(("engine_func_00281adc", r0))
            if self.case.get("switch_base_on_state"):
                write_u32(uc, GLOBAL_ADDR, RENDER_BASE_2)
            uc.reg_write(arm.UC_ARM_REG_R0, (0x5A7E0000 ^ r0) & 0xFFFFFFFF)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_callback(self, uc, address: int, size: int, user_data) -> None:
        value = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("flush", address, value))
        if self.switch_base:
            write_u32(uc, GLOBAL_ADDR, RENDER_BASE_2)
        uc.reg_write(arm.UC_ARM_REG_R0, default_callback_value(address, value))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
            self.writes.append((address, size, value & ((1 << (8 * size)) - 1)))

    # -------------------------------------------------------------- execution
    def _prepare_memory(self, code: bytes, case: dict) -> None:
        uc = self.uc
        uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.mem_write(FUNC_ADDR, b"\x00" * FUNC_SIZE)
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(OBJ_ADDR, build_obj(case))
        write_u32(uc, GLOBAL_ADDR, RENDER_BASE_1)
        for base_tag, base in (("1", RENDER_BASE_1), ("2", RENDER_BASE_2)):
            for offset in (FIRST_OFFSET, SECOND_OFFSET, THIRD_OFFSET):
                spec = node_spec(case, base_tag, offset)
                uc.mem_write(base + offset, build_node(spec))
        uc.ctl_flush_tb()

    def _set_registers(self, case: dict) -> None:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        junk = case["junk"]
        uc.reg_write(arm.UC_ARM_REG_R0, junk[0])
        uc.reg_write(arm.UC_ARM_REG_R1, junk[1])
        uc.reg_write(arm.UC_ARM_REG_R2, junk[2])
        uc.reg_write(arm.UC_ARM_REG_R3, junk[3])
        uc.reg_write(arm.UC_ARM_REG_S0, case["s0"])
        for name, value in S_SCRATCH_START.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), value)
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.switch_base = case.get("switch_base_on_callback", False)

        self._prepare_memory(code, case)
        self._set_registers(case)
        self.writes = []

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        uc = self.uc
        data = bytes(uc.mem_read(DATA_ADDR, DATA_SIZE))
        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "writes": list(self.writes),
            "data": data,
            "global": read_u32(uc, GLOBAL_ADDR),
            "obj": bytes(uc.mem_read(OBJ_ADDR, OBJ_SIZE)),
            "nodes": {
                (base_tag, offset): bytes(uc.mem_read(base + offset, NODE_SIZE))
                for base_tag, base in (("1", RENDER_BASE_1), ("2", RENDER_BASE_2))
                for offset in (FIRST_OFFSET, SECOND_OFFSET, THIRD_OFFSET)
            },
        }

    def run_expect_fault(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.switch_base = case.get("switch_base_on_callback", False)
        self._prepare_memory(code, case)
        self._set_registers(case)
        self.writes = []
        fault = None
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:
            fault = str(error)
        return {
            "fault": fault,
            "call_log": list(self.call_log),
            "writes": list(self.writes),
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
    if orig["writes"] != cand["writes"]:
        problems.append(
            "writes:\n    orig="
            + repr(orig["writes"])
            + "\n    cand="
            + repr(cand["writes"])
        )
    if orig["data"] != cand["data"]:
        diff = next(
            index for index, (a, b) in enumerate(zip(orig["data"], cand["data"]))
            if a != b
        )
        problems.append(
            f"data region differs first at 0x{DATA_ADDR + diff:08x}: "
            f"orig={orig['data'][diff]:02x} cand={cand['data'][diff]:02x}"
        )
    return problems


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def node(count: int, slots, dirty: int, callback: str) -> dict:
    return {
        "count": count,
        "slots": slots,
        "dirty": dirty,
        "callback": CALLBACKS[callback],
    }


def default_nodes() -> dict:
    # Clean nodes with slots[0] already equal to the pushed word: no flush.
    return {
        ("1", FIRST_OFFSET): node(0, [BUILTIN_VALUES[FIRST_OFFSET], 0, 0, 0], 0, "A"),
        ("1", SECOND_OFFSET): node(0, [BUILTIN_VALUES[SECOND_OFFSET], 0, 0, 0], 0, "B"),
        ("1", THIRD_OFFSET): node(0, [BUILTIN_VALUES[THIRD_OFFSET], 0, 0, 0], 0, "C"),
        ("2", FIRST_OFFSET): node(1, [0x11111111, 0x11111111, 0, 0], 0, "A"),
        ("2", SECOND_OFFSET): node(1, [0x22222222, 0x22222222, 0, 0], 0, "B"),
        ("2", THIRD_OFFSET): node(1, [0x33333333, 0x33333333, 0, 0], 0, "C"),
    }


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "found": True,
        "enabled": 1,
        "handle": 0x1234_5678,
        "state": STATE_ADDR,
        "junk": (0x11111111, 0x22222222, 0x33333333, 0x44444444),
        "s0": 0x3FC00000,  # 1.5f junk; the routine must overwrite it with 0.0f
        "nodes": default_nodes(),
    }
    case.update(overrides)
    return case


def set_node(case: dict, base_tag: str, offset: int, spec: dict) -> None:
    case["nodes"] = dict(case["nodes"])
    case["nodes"][(base_tag, offset)] = spec


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- gate -----------------------------------------------------------------
    cases.append(base_case("gate disabled (0x00) returns early", enabled=0))
    cases.append(
        base_case(
            "gate disabled, neighbours set, junk registers",
            enabled=0,
            enabled_neighbor_0x11=0xFF,
            enabled_neighbor_0x12=0xFF,
            enabled_neighbor_0x13=0xFF,
            junk=(0xDEADBEEF, 0xFFFFFFFF, 0x80000000, 0),
            s0=0x7FC00000,
        )
    )
    cases.append(base_case("gate 0x01 enabled", enabled=0x01))
    cases.append(base_case("gate 0xFF enabled", enabled=0xFF))
    cases.append(base_case("gate 0x80 enabled", enabled=0x80))

    # --- handle values forwarded unchanged -----------------------------------
    for handle in (0x00000000, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 0x002C0AC8,
                   0x00100000):
        cases.append(base_case(f"handle 0x{handle:08x}", handle=handle))

    # --- clean path (no flush for any node) -----------------------------------
    cases.append(base_case("clean nodes, no flush at all"))

    # --- flush matrix ---------------------------------------------------------
    case = base_case("all three nodes flush on push and pop")
    for offset, tag in ((FIRST_OFFSET, "A"), (SECOND_OFFSET, "B"),
                        (THIRD_OFFSET, "C")):
        set_node(case, "1", offset, node(0, [0xAAAA0000, 0xBBBB0000,
                                             0xCCCC0000, 0xDDDD0000], 0, tag))
    cases.append(case)

    case = base_case("dirty forces push flush only on all nodes")
    for offset, tag in ((FIRST_OFFSET, "A"), (SECOND_OFFSET, "B"),
                        (THIRD_OFFSET, "C")):
        value = BUILTIN_VALUES[offset]
        set_node(case, "1", offset, node(0, [value, value, 0, 0], 1, tag))
    cases.append(case)

    case = base_case("first node flush, other nodes dirty")
    set_node(case, "1", FIRST_OFFSET,
             node(0, [0xAAAA0000, 0xBBBB0000, 0, 0], 0, "A"))
    set_node(case, "1", SECOND_OFFSET,
             node(0, [BUILTIN_VALUES[SECOND_OFFSET], 0, 0, 0], 1, "B"))
    set_node(case, "1", THIRD_OFFSET,
             node(0, [BUILTIN_VALUES[THIRD_OFFSET], 0, 0, 0], 1, "C"))
    cases.append(case)

    # --- counts 0..3 on each node (count 3 overlaps the dirty byte) ----------
    for count in (0, 1, 2, 3):
        case = base_case(f"all node counts {count}")
        for offset, tag in ((FIRST_OFFSET, "A"), (SECOND_OFFSET, "B"),
                            (THIRD_OFFSET, "C")):
            slots = [0x11110000 + count, 0x22220000, 0x33330000, 0x44440000]
            set_node(case, "1", offset, node(count, slots, 0, tag))
        cases.append(case)

    # --- slot values on a signed/unsigned boundary ---------------------------
    case = base_case("slot boundary values")
    set_node(case, "1", FIRST_OFFSET,
             node(0, [0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 0], 0, "A"))
    set_node(case, "1", SECOND_OFFSET,
             node(0, [0x80000000, 0x7FFFFFFF, 0, 0], 0, "B"))
    set_node(case, "1", THIRD_OFFSET,
             node(0, [0xFFFFFFFF, 0, 0, 0], 0, "C"))
    cases.append(case)

    # --- base switching -------------------------------------------------------
    case = base_case(
        "push flush callback switches the render base",
        switch_base_on_callback=True,
    )
    set_node(case, "1", FIRST_OFFSET,
             node(0, [0xAAAA0000, 0xBBBB0000, 0, 0], 0, "A"))
    cases.append(case)

    case = base_case(
        "dirty push callback switches the render base",
        switch_base_on_callback=True,
        switch_base_on_state=False,
    )
    set_node(case, "1", FIRST_OFFSET,
             node(0, [BUILTIN_VALUES[FIRST_OFFSET], 0, 0, 0], 1, "A"))
    cases.append(case)

    case = base_case(
        "state helper switches base between pushes and pops",
        switch_base_on_state=True,
    )
    cases.append(case)

    case = base_case(
        "state helper switches base, second set is dirty",
        switch_base_on_state=True,
    )
    for offset, tag in ((FIRST_OFFSET, "A"), (SECOND_OFFSET, "B"),
                        (THIRD_OFFSET, "C")):
        set_node(case, "2", offset,
                 node(0, [0x99990000, 0, 0, 0], 1, tag))
    cases.append(case)

    # --- state pointer variants ----------------------------------------------
    for state in (0x00000000, 0xFFFFFFFF, 0x00100000, STATE_ADDR + 0x40):
        cases.append(base_case(f"state pointer 0x{state:08x}", state=state))

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases) -> int:
    runner = Machine()
    passed = 0
    for case in cases:
        orig = runner.run(orig_code, case)
        cand = runner.run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {case['name']}  "
            f"({len(orig['call_log'])} calls, ret=0x{orig['ret']:08x})"
        )
    return passed


def check_fault_equivalence(orig_code: bytes, cand_code: bytes) -> None:
    case = base_case("null lookup result faults on the gate read", found=False)
    runner = Machine()
    orig = runner.run_expect_fault(orig_code, case)
    cand = runner.run_expect_fault(cand_code, case)
    if orig["fault"] is None or cand["fault"] is None:
        raise SystemExit(
            f"  [FAIL] expected both bodies to fault: "
            f"orig={orig['fault']!r} cand={cand['fault']!r}"
        )
    if orig["call_log"] != cand["call_log"]:
        raise SystemExit(
            "  [FAIL] null-lookup call log differs:\n"
            f"    orig={orig['call_log']!r}\n    cand={cand['call_log']!r}"
        )
    if orig["writes"] != cand["writes"]:
        raise SystemExit("  [FAIL] null-lookup writes differ")
    print("  [PASS] null lookup: both bodies fault after the same lookup call")


def main() -> None:
    print("Testing ui_func_002247c8 (0x002247c8)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(5 call relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)
    check_fault_equivalence(orig_code, cand_code)

    print("\nNegative controls:")
    mutants = (
        ("gate_offset",
         "if (object->enabled_10 == 0) {",
         "if (*reinterpret_cast<const u8*>(object) == 0) {"),
        ("first_stack_offset", "constexpr u32 kFirstStackOffset = 0x126C;",
         "constexpr u32 kFirstStackOffset = 0x1268;"),
        ("third_stack_offset", "constexpr u32 kThirdStackOffset = 0x12AC;",
         "constexpr u32 kThirdStackOffset = 0x12A8;"),
        ("engine_command", "constexpr u32 kEngineCommand = 6;",
         "constexpr u32 kEngineCommand = 5;"),
        ("zero_scale", "constexpr f32 kZeroScale = 0.0f;",
         "constexpr f32 kZeroScale = 1.0f;"),
        ("callback_argument",
         "reinterpret_cast<FlushCallback>(node->flush_cb)(value);",
         "reinterpret_cast<FlushCallback>(node->flush_cb)(value ^ 1u);"),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        runner = Machine()
        for case in cases:
            orig = runner.run(orig_code, case)
            try:
                bad = runner.run(mutant_code, case)
            except RuntimeError:
                # A mutant that faults where the original does not is still a
                # detected behavioural difference.
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")
    print(f"{len(mutants)}/{len(mutants)} negative controls detected.")


if __name__ == "__main__":
    main()
