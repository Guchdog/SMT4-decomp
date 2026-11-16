#!/usr/bin/env python3
"""Differential test for battle_func_00137730 (0x00137730) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the battle_func_00137730 body,
resolves its three direct calls to deterministic stubs at the original call
targets, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with the register argument of every helper
    (lock acquire, pending flush, lock release) - none of these helpers take
    architected stack arguments;
  * the flush helper's return value, which the original forwards to the lock
    release and therefore to the function's own r0;
  * the full render-node, replay-entry and 0x004C6290 state pages;
  * any emulated write outside the private stack and those three pages.

Coverage: the 5x5 accepted command-id matrix for both selectors with the blend
enabled and disabled; invalid ids around every accepted value including signed
boundaries; all three 0x500/0x501/0x502 modes and invalid modes; every mandatory
zero check; the full blend range test with equal/less/greater 16-bit pairs on
each axis; both 0x10/0x08 alignment classes and the sign-rounding path; 32-bit
product/sum wrap; 16-bit truncation of the extents; preserved flag bits 12..31;
bit 6/9 selection; the complete owner/gate/flush matrix with zero and non-zero
flush returns; and node counts that wrap the 32-bit entry-address product.
Negative controls mutate the entry stride, the entry kind, the 0x10 alignment
constant, the blend range conjunction and the flush helper argument; each
mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_00137730"

FUNC_ADDR = 0x00137730
FUNC_SIZE = 680

# 0x002BA5F8 is the highest helper address; the code window covers it.
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000
NODE_ADDR = 0x00700000
NODE_SIZE = 0x00001000
ENTRY_ADDR = 0x00710000
ENTRY_SIZE = 0x00010000
STATE_ADDR = 0x004C6000
STATE_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_TARGET = ENTRY_ADDR + 0x4000
STATE_BASE = 0x004C6290
STATE_OFFSET = STATE_BASE - STATE_ADDR
ENTRY_STRIDE = 28

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_ACQUIRE = 0x0013AF78
STUB_FLUSH = 0x002BA5F8
STUB_RELEASE = 0x0013AF88

STUB_NAMES = {
    STUB_ACQUIRE: "battle_func_0013af78",
    STUB_FLUSH: "battle_func_002ba5f8",
    STUB_RELEASE: "battle_func_0013af88",
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


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00137730" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"battle_func_00137730 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unexpected relocation type {rel.relocation_type} for "
                f"{rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_mutant(name: str, old: str, new: str) -> bytes:
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


def pattern(size: int, seed: int) -> bytes:
    return bytes(((index * 7 + seed) & 0xFF) for index in range(size))


def build_node(case: dict) -> bytes:
    page = bytearray(pattern(NODE_SIZE, 0x31))
    entries = (ENTRY_TARGET - case.get("count", 0) * ENTRY_STRIDE) & 0xFFFFFFFF
    struct.pack_into("<I", page, 0x18, entries)
    struct.pack_into("<I", page, 0x20, case.get("count", 0) & 0xFFFFFFFF)
    return bytes(page)


def build_entry(case: dict) -> bytes:
    page = bytearray(pattern(ENTRY_SIZE, 0xA5))
    offset = ENTRY_TARGET - ENTRY_ADDR
    page[offset + 0x00] = 0xEE
    struct.pack_into("<I", page, offset + 0x04, 0x11111111)
    struct.pack_into("<I", page, offset + 0x08, 0x22222222)
    struct.pack_into("<I", page, offset + 0x14, case.get("old_flags", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, offset + 0x18, 0xDEADBEEF)
    return bytes(page)


def build_state(case: dict) -> bytes:
    page = bytearray(pattern(STATE_SIZE, 0x5A))
    owner = case.get("owner", 0x5A5A5A5A)
    struct.pack_into("<I", page, STATE_OFFSET + 0xA0, owner & 0xFFFFFFFF)
    page[STATE_OFFSET + 0x11] = case.get("flush", 0) & 0xFF
    page[STATE_OFFSET + 0x12] = case.get("gate", 0) & 0xFF
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self, code: bytes) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
        self.uc.mem_map(ENTRY_ADDR, ENTRY_SIZE)
        self.uc.mem_map(STATE_ADDR, STATE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.uc.mem_write(FUNC_ADDR, code)
        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.flush_return = 0
        self.node_pointer = NODE_ADDR

    # ------------------------------------------------------------------ stubs
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        if address == STUB_ACQUIRE:
            self.call_log.append((STUB_NAMES[address], r0))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x13AF7800)
        elif address == STUB_FLUSH:
            self.call_log.append((STUB_NAMES[address], r0, self.flush_return))
            uc.reg_write(arm.UC_ARM_REG_R0, self.flush_return & 0xFFFFFFFF)
        elif address == STUB_RELEASE:
            self.call_log.append((STUB_NAMES[address], r0))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x004E6C5C)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.flush_return = case.get("flush_return", 0)

        self.uc.mem_write(NODE_ADDR, build_node(case))
        self.uc.mem_write(ENTRY_ADDR, build_entry(case))
        state = build_state(case)
        self.uc.mem_write(STATE_ADDR, state)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        stack_args = (
            case.get("a4", 0x8057),
            case.get("a5", 0x01020304),
            case.get("a6", 0x10),
            case.get("a7", 0x20),
            case.get("a8", 0x8057),
            case.get("a9", 0x500),
            case.get("a10", 0),
            case.get("a11", 0),
        )
        self.uc.mem_write(ENTRY_SP, struct.pack("<8I", *stack_args))
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_PC, FUNC_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, self.node_pointer)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("a1", 0x0BAD1234))
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("a2", 0x0004))
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("a3", 0x0006))
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        allowed = (
            (NODE_ADDR, NODE_ADDR + NODE_SIZE),
            (ENTRY_ADDR, ENTRY_ADDR + ENTRY_SIZE),
            (STATE_ADDR, STATE_ADDR + STATE_SIZE),
            (STACK_ADDR, STACK_ADDR + STACK_SIZE),
        )
        unexpected_writes = []
        for address, size, _value in self.writes:
            if not any(start <= address < end for start, end in allowed):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "node": bytes(self.uc.mem_read(NODE_ADDR, NODE_SIZE)),
            "entry": bytes(self.uc.mem_read(ENTRY_ADDR, ENTRY_SIZE)),
            "state": bytes(self.uc.mem_read(STATE_ADDR, STATE_SIZE)),
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
    for key in ("node", "entry", "state"):
        if orig[key] != cand[key]:
            first = next(
                index
                for index, (left, right) in enumerate(zip(orig[key], cand[key]))
                if left != right
            )
            problems.append(
                f"{key} memory differs first at +0x{first:x}: "
                f"orig=0x{orig[key][first]:02x} cand=0x{cand[key][first]:02x}"
            )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


PRIMARY_IDS = (0x8058, 0x8051, 0x8D62, 0x8057, 0x8056)
SECONDARY_IDS = (0x8058, 0x8051, 0x8D62, 0x8057, 0x8056)
INVALID_IDS = (
    0x8050,
    0x8052,
    0x8053,
    0x8054,
    0x8055,
    0x8059,
    0x8D61,
    0x8D63,
    0x00000000,
    0xFFFFFFFF,
    0x7FFFFFFF,
    0x80000000,
)


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "a1": 0x0BAD1234,
        "a2": 0x0102,
        "a3": 0x0304,
        "a4": 0x8057,
        "a5": 0x55667788,
        "a6": 0x0010,
        "a7": 0x0020,
        "a8": 0x8057,
        "a9": 0x502,
        "a10": 1,
        "a11": 0,
        "count": 1,
        "old_flags": 0,
        "owner": NODE_ADDR,
        "gate": 0,
        "flush": 0,
        "flush_return": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- selector matrix: every accepted id pair, blend on and off
    for primary in PRIMARY_IDS:
        for secondary in SECONDARY_IDS:
            cases.append(
                base_case(
                    f"selectors {primary:04x}/{secondary:04x} blend",
                    a4=primary,
                    a8=secondary,
                )
            )
    for primary in PRIMARY_IDS:
        for secondary in SECONDARY_IDS:
            cases.append(
                base_case(
                    f"selectors {primary:04x}/{secondary:04x} no blend",
                    a4=primary,
                    a8=secondary,
                    a10=0,
                )
            )

    # --- a9 modes and the 0x500-only / 0x502-only combinations
    for mode in (0x500, 0x501, 0x502):
        for primary, secondary in (
            (0x8057, 0x8057),
            (0x8058, 0x8051),
            (0x8D62, 0x8D62),
            (0x8056, 0x8058),
        ):
            cases.append(
                base_case(
                    f"mode {mode:03x} ids {primary:04x}/{secondary:04x}",
                    a4=primary,
                    a8=secondary,
                    a9=mode,
                )
            )
            cases.append(
                base_case(
                    f"mode {mode:03x} ids {primary:04x}/{secondary:04x} blend0",
                    a4=primary,
                    a8=secondary,
                    a9=mode,
                    a10=0,
                )
            )

    # --- invalid ids (each must return without touching memory)
    for ident in INVALID_IDS:
        cases.append(base_case(f"invalid primary 0x{ident:08x}", a4=ident))
        cases.append(base_case(f"invalid secondary 0x{ident:08x}", a8=ident))

    # --- invalid a9 modes
    for mode in (0x000, 0x4FF, 0x503, 0x504, 0xFFFFFFFF, 0x80000000):
        cases.append(base_case(f"invalid mode 0x{mode:08x}", a9=mode))

    # --- mandatory non-zero arguments
    for key in ("a2", "a3", "a6", "a7"):
        cases.append(base_case(f"{key} zero", **{key: 0}))
    cases.append(base_case("all mandatory zero", a2=0, a3=0, a6=0, a7=0))

    # --- blend range test on both axes, equal/less/greater
    # a6=0x10 (extent lo, x1 multiplier) and a7=0x20 are the defaults.
    for label, a2, a3, a6, a7 in (
        ("extent covers rect", 0x0010, 0x0020, 0x0010, 0x0020),
        ("lo below, hi equal", 0x0011, 0x0020, 0x0010, 0x0020),
        ("lo equal, hi below", 0x0010, 0x0021, 0x0010, 0x0020),
        ("both below", 0x0011, 0x0021, 0x0010, 0x0020),
        ("both above", 0x000F, 0x001F, 0x0010, 0x0020),
        ("u16 maximum rect", 0xFFFF, 0xFFFF, 0x0010, 0x0020),
        ("u16 maximum extent", 0x0010, 0x0020, 0xFFFF, 0xFFFF),
        ("extent zero hi", 0x0010, 0x0001, 0x0010, 0x0000),
        ("extent lo zero", 0x0001, 0x0020, 0x0000, 0x0020),
        ("rect wraps", 0xFFFF, 0x0001, 0x0001, 0x0001),
    ):
        for mode in (0x500, 0x501, 0x502):
            cases.append(
                base_case(
                    f"range {label} mode {mode:03x}",
                    a2=a2,
                    a3=a3,
                    a6=a6,
                    a7=a7,
                    a9=mode,
                )
            )

    # --- alignment classes: secondary 0x8051 -> scale 3 -> align 0x10,
    #     every other accepted id -> align 0x08; delta & align both ways.
    for secondary in SECONDARY_IDS:
        for a2 in (0x0011, 0x0018, 0x0021, 0x0029):
            cases.append(
                base_case(
                    f"align secondary {secondary:04x} rect {a2:04x}",
                    a4=0x8058,
                    a8=secondary,
                    a2=a2,
                    a3=0x0040,
                    a6=0x0010,
                    a7=0x0020,
                    a9=0x501,
                )
            )

    # --- sign-rounding and 32-bit product wrap in the 0x501/0x502 paths
    for a2, a3, a6, a7, a5 in (
        (0xFFFF, 0x0001, 0x0000, 0x0020, 0x00000010),
        (0xFFFF, 0x0001, 0x0001, 0x0020, 0x00000010),
        (0x8000, 0x0001, 0x0001, 0x8000, 0x00000000),
        (0x7FFF, 0x0002, 0x0000, 0x0002, 0x7FFFFFFF),
        (0x0002, 0x0001, 0x0000, 0xFFFFFFFF, 0x80000000),
        (0x0001, 0x0001, 0x0000, 0x0002, 0x00000001),
        (0xFFFF, 0x0001, 0x0000, 0x0000, 0x12345678),
        (0x0001, 0xFFFF, 0x0001, 0x0002, 0x00000000),
        (0xFFFF, 0x0001, 0x8000, 0xFFFF, 0x00000010),
        (0xFFFF, 0x0001, 0x8000, 0x10000, 0x00000010),
    ):
        for mode in (0x500, 0x501, 0x502):
            cases.append(
                base_case(
                    f"arith mode {mode:03x} a2={a2:04x} a5={a5:08x}",
                    a2=a2,
                    a3=a3,
                    a6=a6,
                    a7=a7,
                    a5=a5,
                    a9=mode,
                )
            )

    # 0x501/scale-3 path with a negative, odd intermediate product: the
    # original's `value += value >> 31` rounding is observable here.
    cases.append(
        base_case(
            "path2 negative odd product",
            a4=0x8058,
            a8=0x8051,
            a9=0x501,
            a2=0xFFFF,
            a3=0x0001,
            a6=0x8000,
            a7=0x10000,
            a5=0x00000000,
        )
    )
    # 0x500 path with a zero stored extent_hi (extent_hi - 1 wraps).
    cases.append(
        base_case(
            "path1 zero extent_hi",
            a9=0x500,
            a2=0xFFFF,
            a3=0x0001,
            a6=0x0001,
            a7=0x10000,
            a5=0x12345678,
        )
    )

    # --- 16-bit truncation of the stored extents and rect fields
    for a2, a3, a6, a7, mode in (
        (0x1234ABCD, 0x5678EF01, 0x00010000, 0x00018000, 0x502),
        (0x0001FFFF, 0x00010001, 0x00008001, 0x0000FFFF, 0x501),
        (0x00010010, 0x00010020, 0x00010010, 0x00010020, 0x500),
        (0x00000000, 0x00000000, 0x00000001, 0x00000001, 0x502),
    ):
        cases.append(
            base_case(
                f"truncate a2={a2:08x} a6={a6:08x}",
                a2=a2,
                a3=a3,
                a6=a6,
                a7=a7,
                a9=mode,
            )
        )

    # --- preserved flag bits 12..31 and the a11 bit 9
    for flags in (0xFFFFF000, 0x00000FFF, 0x12345678, 0xFFFFFFFF, 0x00000000):
        for a11 in (0x20, 0x21, 0x00, 0xFFFFFFFF):
            cases.append(
                base_case(
                    f"old flags 0x{flags:08x} a11 0x{a11:08x}",
                    old_flags=flags,
                    a11=a11,
                )
            )

    # --- owner / gate / flush matrix
    for owner in (NODE_ADDR, 0x00000000, 0x00700001, 0xFFFFFFFF):
        for gate in (0x00, 0x01, 0x80, 0xFF):
            for flush in (0x00, 0x01, 0xFF):
                cases.append(
                    base_case(
                        f"owner 0x{owner:08x} gate 0x{gate:02x} flush 0x{flush:02x}",
                        owner=owner,
                        gate=gate,
                        flush=flush,
                        flush_return=0xA5A50000 | flush,
                    )
                )
    for flush_return in (0x00000000, 0xFFFFFFFF, 0x212BA5F8, 0x00000001):
        cases.append(
            base_case(
                f"flush return 0x{flush_return:08x}",
                gate=1,
                flush=0,
                flush_return=flush_return,
            )
        )

    # --- entry-address product wrap
    for count in (0, 1, 2, 0xFFFFFFFF, 0x40000001, 0x80000002, 0x12345679):
        cases.append(base_case(f"count 0x{count:08x}", count=count))

    # --- blend with a null/zero a5 to prove the adjustment wraps
    cases.append(base_case("a5 zero blend", a5=0, a2=0x0011, a3=0x0030))
    cases.append(base_case("a5 maximum blend", a5=0xFFFFFFFF, a2=0x0011,
                           a3=0x0030))

    return cases


def run_case_set(orig_runner: Runner, cand_runner: Runner, cases) -> int:
    passed = 0
    for case in cases:
        orig = orig_runner.run(case)
        cand = cand_runner.run(case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {case['name']}  "
            f"({len(orig['call_log'])} calls, r0=0x{orig['ret']:08x})"
        )
    return passed


def main() -> None:
    print("Testing battle_func_00137730 (0x00137730)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    orig_runner = Runner(orig_code)
    cand_runner = Runner(cand_code)
    cases = make_cases()
    passed = run_case_set(orig_runner, cand_runner, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("entry_stride", "render_node->count_20 * kEntryStride",
         "render_node->count_20 * 24u"),
        ("entry_kind", "constexpr u8  kEntryKind = 3;",
         "constexpr u8  kEntryKind = 4;"),
        ("blend_align", "const u32 align = (scale == 3) ? 0x10u : 0x8u;",
         "const u32 align = (scale == 3) ? 0x20u : 0x8u;"),
        ("blend_range", "if (extent_lo < rect_lo || extent_hi < rect_hi) {",
         "if (extent_lo < rect_lo && extent_hi < rect_hi) {"),
        ("blend_rounding", "value += value >> 31;", "value += 0u;"),
        ("flush_argument",
         "release_r0 = battle_func_002ba5f8(kRenderStateAddress);",
         "release_r0 = battle_func_002ba5f8(0);"),
    ):
        mutant_code = compile_mutant(name, old, new)
        mutant_runner = Runner(mutant_code)
        detected = False
        for case in cases:
            orig = orig_runner.run(case)
            bad = mutant_runner.run(case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
