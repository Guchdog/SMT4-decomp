#!/usr/bin/env python3
"""Differential test for camp_func_0026a62c (0x0026a62c) using Unicorn ARM.

The routine rebuilds one of three camp identifier tables selected by its r0
mode (0xB, 0xC or 0xD), stores accepted ids as halfwords, calls the shared
page/cursor setup helper and tail-branches to the camp layout interpreter.

Compiles ``src/engine/leaf_batch41_c.cpp``, extracts ``camp_func_0026a62c``,
resolves every direct call relocation to a deterministic stub and the
``smt4::camp::g_CampWork`` ABS32 literal to the recorded global address
0x0043DA90.  The pinned original (``extracted/exefs/code.bin``) and the
compiled candidate then run on separate Unicorn machines with identical
fixtures.

Compared per case:
  * return r0, continuation PC, final SP and callee-saved r4-r11 / s16-s31;
  * the ordered call log with all arguments, including both stack words of
    0x0029FAE8 and the mode argument of 0x002831F0;
  * every emulated write outside the private stack;
  * the full work page, the 0x0043DA90 pointer page and the call log.

Coverage:
  * dispatch 0xB/0xC/0xD plus non-dispatch 0, 10, 14, 0xFFFFFFFF, 0x8000000B;
  * every loop start/end and the 0x47E/0x47F cross-pass boundary;
  * empty, single-entry and full tables;
  * 0x0028EC78 returning 0, 1 and 0x80000000 (non-zero but negative);
  * 0x0028FDE4 returning 0, 1, 0x7FFFFFFF, -1 and 0x80000000;
  * the 0xD second-predicate gate (0x0028FDE4 is not called when
    0x0028EC78 is zero);
  * the wrapped-address early exit for each mode-specific table/page base.

Negative controls recompile mutated source (loop bounds, predicate direction,
table offset, page row count, page item count, tail mode and early return
value); every mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_0026a62c"

FUNC_NAME = "camp_func_0026a62c"
FUNC_ADDR = 0x0026A62C
FUNC_SIZE = 408

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000          # target plus every direct-call stub
GLOBAL_ADDR = 0x0043D000
GLOBAL_SIZE = 0x00001000        # g_CampWork pointer at 0x0043DA90
G_CAMPWORK_ADDR = 0x0043DA90
GLOBAL_PTR_OFFSET = G_CAMPWORK_ADDR - GLOBAL_ADDR
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00008000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_28EC78 = 0x0028EC78
STUB_28FDE4 = 0x0028FDE4
STUB_29FAE8 = 0x0029FAE8
STUB_2831F0 = 0x002831F0

STUB_BY_SYMBOL = {
    "battle_func_0028ec78": STUB_28EC78,
    "camp_func_0028fde4": STUB_28FDE4,
    "camp_func_0029fae8": STUB_29FAE8,
    "camp_func_002831f0": STUB_2831F0,
}
# Mangled namespace-scope variable in the compiler output.
ABS32_TARGETS = {
    "_ZN4smt44camp10g_CampWorkE": G_CAMPWORK_ADDR,
}

# Mode-specific constants mirrored from the candidate source.  The expected
# model uses its own copy so an accidental disagreement is visible.
MODES = {
    0x0B: {
        "table": 0x147C,
        "page": 0x00B0,
        "passes": ((1, 0x3C, False),),
    },
    0x0C: {
        "table": 0x14F4,
        "page": 0x0114,
        "passes": ((0x3B7, 0x47E, False), (0x47F, 0x79E, False)),
    },
    0x0D: {
        "table": 0x1CC4,
        "page": 0x0178,
        "passes": ((0x33F, 0x3B6, False), (0x79F, 0x802, True)),
    },
}
PAGE_ROWS = 0x0B
PAGE_COLUMNS = 1
PAGE_WRAP_ROW = 1
PAGE_REPEAT = 1

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


# ---------------------------------------------------------------------------
# Fixtures and predicate specifications
# ---------------------------------------------------------------------------
def initial_work() -> bytes:
    page = bytearray(WORK_SIZE)
    for index in range(WORK_SIZE):
        page[index] = (index * 37 + 11) & 0xFF
    return bytes(page)


INITIAL_WORK = initial_work()


def accept_all(value: int) -> int:
    return 1


def accept_none(value: int) -> int:
    return 0


def accept_set(values, result: int = 1, default: int = 0):
    accepted = frozenset(values)
    return lambda value: result if value in accepted else default


def result_value(value: int) -> int:
    return value


def tail_value(value: int) -> int:
    return 0x7FFFFFFF


def wrapped(offset: int) -> int:
    return (-offset) & 0xFFFFFFFF


def make_case(name: str, mode: int, ec78=None, fde4=None,
              work: int = WORK_ADDR, tail_return: int = 0xA5A5A5A5,
              page_return: int = 0xDEADBEEF) -> dict:
    return {
        "name": name,
        "mode": mode & 0xFFFFFFFF,
        "ec78": ec78 or accept_all,
        "fde4": fde4 or accept_all,
        "work": work & 0xFFFFFFFF,
        "tail_return": tail_return & 0xFFFFFFFF,
        "page_return": page_return & 0xFFFFFFFF,
    }


def build_cases() -> list[dict]:
    cases = [
        # --- mode 0xB: ids 1..0x3C -------------------------------------
        make_case("B: first and last accepted", 0x0B, accept_set((1, 0x3C))),
        make_case("B: values outside the range only", 0x0B,
                  accept_set((0, 0x3D, 0x7FFFFFFF))),
        make_case("B: nothing accepted", 0x0B, accept_none),
        make_case("B: everything accepted", 0x0B, accept_all),
        make_case("B: only id 0x1E accepted", 0x0B, accept_set((0x1E,))),
        make_case("B: non-zero negative predicate result", 0x0B,
                  accept_set((1, 0x3C), result=0x80000000)),
        make_case("B: page base wraps to zero", 0x0B,
                  work=wrapped(0x00B0)),

        # --- mode 0xC: 0x3B7..0x47E then 0x47F..0x79E -------------------
        make_case("C: cross-pass boundary and outer limits", 0x0C,
                  accept_set((0x3B6, 0x3B7, 0x47E, 0x47F, 0x79E, 0x79F))),
        make_case("C: everything accepted", 0x0C, accept_all),
        make_case("C: nothing accepted", 0x0C, accept_none),
        make_case("C: only 0x47E and 0x47F accepted", 0x0C,
                  accept_set((0x47E, 0x47F))),
        make_case("C: only first id accepted", 0x0C, accept_set((0x3B7,))),
        make_case("C: only last id accepted", 0x0C, accept_set((0x79E,))),
        make_case("C: table base wraps to zero", 0x0C,
                  work=wrapped(0x14F4)),
        make_case("C: page base wraps to zero", 0x0C,
                  work=wrapped(0x0114)),

        # --- mode 0xD: 0x33F..0x3B6 then gated 0x79F..0x802 -------------
        make_case("D: cross-pass boundary and outer limits", 0x0D,
                  accept_set((0x33E, 0x33F, 0x3B6, 0x3B7,
                              0x79E, 0x79F, 0x802, 0x803))),
        make_case("D: everything accepted", 0x0D, accept_all, accept_all),
        make_case("D: second predicate zero", 0x0D, accept_all, accept_none),
        make_case("D: second predicate -1", 0x0D, accept_all,
                  lambda value: -1),
        make_case("D: second predicate INT_MIN", 0x0D, accept_all,
                  lambda value: 0x80000000),
        make_case("D: second predicate INT_MAX", 0x0D, accept_all,
                  lambda value: 0x7FFFFFFF),
        make_case("D: first predicate zero only in second pass", 0x0D,
                  lambda value: 1 if value < 0x79F else 0, accept_all),
        make_case("D: negative-but-non-zero first predicate", 0x0D,
                  lambda value: (0x80000000 if value >= 0x79F else 1),
                  accept_all),
        make_case("D: table base wraps to zero", 0x0D,
                  work=wrapped(0x1CC4)),

        # --- non-dispatch modes ---------------------------------------
        make_case("mode 0: early return", 0),
        make_case("mode 10: early return", 10),
        make_case("mode 14: early return", 14),
        make_case("mode 0xFFFFFFFF: early return", 0xFFFFFFFF),
        make_case("mode 0x8000000B: not equal to 0xB", 0x8000000B),
    ]
    return cases


def build_global(case: dict) -> bytes:
    page = bytearray(b"\x5A" * GLOBAL_SIZE)
    struct.pack_into("<I", page, GLOBAL_PTR_OFFSET, case["work"])
    return bytes(page)


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def sign_extend_24(value: int) -> int:
    return value - 0x1000000 if value & 0x800000 else value


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    entry = funcs.get(FUNC_NAME)
    if entry is None:
        raise RuntimeError(
            f"{FUNC_NAME} not found in {obj_file}: {sorted(funcs)}"
        )

    raw, relocs = entry
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = STUB_BY_SYMBOL.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unexpected call relocation: {rel}")
            instruction = struct.unpack_from("<I", code, rel.offset)[0]
            addend = sign_extend_24(instruction & 0x00FFFFFF) << 2
            place = FUNC_ADDR + rel.offset
            displacement = (target + addend - place) >> 2
            struct.pack_into(
                "<I", code, rel.offset,
                (instruction & 0xFF000000) | (displacement & 0x00FFFFFF),
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            target = ABS32_TARGETS.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unexpected abs32 relocation: {rel}")
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")
    return bytes(code)


def compile_variant(src_file: Path, obj_file: Path) -> bytes:
    result = compile_tu_armv6k(src_file, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return compile_variant(SOURCE, OUT_DIR / "leaf_batch41_c.o")


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(
            f"mutation anchor {old!r} occurs {text.count(old)} times"
        )
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (GLOBAL_ADDR, GLOBAL_SIZE),
            (WORK_ADDR, WORK_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        self.orig_code = get_orig_bytes()
        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for address, hook in (
            (STUB_28EC78, self._on_28ec78),
            (STUB_28FDE4, self._on_28fde4),
            (STUB_29FAE8, self._on_29fae8),
            (STUB_2831F0, self._on_2831f0),
        ):
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, hook, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    # -- stubs ------------------------------------------------------------
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & ((1 << (8 * size)) - 1)))

    def _stack_args(self, count: int) -> tuple:
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, count * 4)
        return struct.unpack("<%dI" % count, raw)

    def _on_28ec78(self, uc, address, size, user_data) -> None:
        value = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("battle_func_0028ec78", value))
        uc.reg_write(
            arm.UC_ARM_REG_R0, self.case["ec78"](value) & 0xFFFFFFFF
        )

    def _on_28fde4(self, uc, address, size, user_data) -> None:
        value = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("camp_func_0028fde4", value))
        uc.reg_write(
            arm.UC_ARM_REG_R0, self.case["fde4"](value) & 0xFFFFFFFF
        )

    def _on_29fae8(self, uc, address, size, user_data) -> None:
        r0, r1, r2, r3 = (
            uc.reg_read(arm.UC_ARM_REG_R0 + index) for index in range(4)
        )
        stack0, stack1 = self._stack_args(2)
        self.call_log.append(
            ("camp_func_0029fae8", r0, r1, r2, r3, stack0, stack1)
        )
        uc.reg_write(arm.UC_ARM_REG_R0, self.case["page_return"])

    def _on_2831f0(self, uc, address, size, user_data) -> None:
        self.call_log.append(
            ("camp_func_002831f0", uc.reg_read(arm.UC_ARM_REG_R0))
        )
        uc.reg_write(arm.UC_ARM_REG_R0, self.case["tail_return"])

    # -- execution --------------------------------------------------------
    def run(self, candidate: bytes | None, case: dict) -> dict:
        uc = self.uc
        self.case = case
        self.call_log = []

        uc.mem_write(FUNC_ADDR, self.orig_code if candidate is None else candidate)
        uc.mem_write(GLOBAL_ADDR, build_global(case))
        uc.mem_write(WORK_ADDR, INITIAL_WORK)
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []
        # Unicorn caches translated blocks; drop them after every mem_write.
        uc.ctl_flush_tb()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, case["mode"])
        uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, register in CALLEE_SAVED.items():
            uc.reg_write(register, CALLEE_SAVED_START[name])
        for index in range(16, 32):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_S{index}"),
                         0x3F000000 + index)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as error:
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "call_log": list(self.call_log),
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "callee_saved_vfp": [
                uc.reg_read(getattr(arm, f"UC_ARM_REG_S{index}"))
                for index in range(16, 32)
            ],
            "writes": [
                write for write in self.writes
                if not STACK_ADDR <= write[0] < STACK_ADDR + STACK_SIZE
            ],
            "work": bytes(uc.mem_read(WORK_ADDR, WORK_SIZE)),
            "global": bytes(uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
        }


# ---------------------------------------------------------------------------
# Independent expected model
# ---------------------------------------------------------------------------
def expected_case(case: dict):
    mode = case["mode"]
    work = case["work"]
    log: list = []
    table_writes: list = []

    if mode not in MODES:
        return log, work, table_writes

    spec = MODES[mode]
    table_addr = (work + spec["table"]) & 0xFFFFFFFF
    page_addr = (work + spec["page"]) & 0xFFFFFFFF
    if table_addr == 0 or page_addr == 0:
        return log, work, table_writes

    def signed32(value: int) -> int:
        value &= 0xFFFFFFFF
        return value - 0x100000000 if value & 0x80000000 else value

    count = 0
    for first, last, gated in spec["passes"]:
        for value in range(first, last + 1):
            log.append(("battle_func_0028ec78", value))
            if (case["ec78"](value) & 0xFFFFFFFF) == 0:
                continue
            if gated:
                log.append(("camp_func_0028fde4", value))
                if signed32(case["fde4"](value)) <= 0:
                    continue
            table_writes.append((spec["table"] + 2 * count, value & 0xFFFF))
            count += 1

    log.append(("camp_func_0029fae8", page_addr, count, PAGE_ROWS,
                PAGE_COLUMNS, PAGE_WRAP_ROW, PAGE_REPEAT))
    log.append(("camp_func_002831f0", mode))
    return log, case["tail_return"], table_writes


def expected_work(case: dict) -> bytes:
    _, _, table_writes = expected_case(case)
    page = bytearray(INITIAL_WORK)
    for offset, value in table_writes:
        if not 0 <= offset + 1 < WORK_SIZE:
            raise AssertionError(
                f"model table write outside work page: 0x{offset:x}"
            )
        struct.pack_into("<H", page, offset, value)
    return bytes(page)


def check_expected(case: dict, result: dict) -> None:
    log, ret, _ = expected_case(case)
    assert result["call_log"] == log, (
        f"expected call log mismatch on {case['name']}:\n"
        f"  Expected: {log}\n  Actual:   {result['call_log']}"
    )
    assert result["ret"] == ret, (
        f"expected return mismatch on {case['name']}: "
        f"0x{result['ret']:08x} != 0x{ret:08x}"
    )
    assert result["work"] == expected_work(case), (
        f"expected work-table mismatch on {case['name']}"
    )


def compare(orig: dict, cand: dict, name: str) -> None:
    for key in ("ret", "pc", "sp", "callee_saved", "callee_saved_vfp",
                "call_log", "writes", "work", "global"):
        assert orig[key] == cand[key], (
            f"{key} mismatch on {name}:\n"
            f"  Orig: {orig[key]!r}\n  Cand: {cand[key]!r}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def safe_run(machine: Machine, candidate: bytes, case: dict):
    try:
        return machine.run(candidate, case)
    except RuntimeError as error:
        return ("crash", str(error))


def main() -> None:
    print("Testing camp_func_0026a62c (0x0026a62c)...")
    candidate = compile_candidate()
    print(f"  original: {FUNC_SIZE} B, candidate: {len(candidate)} B")

    cases = build_cases()
    machine = Machine()
    passed = 0
    for case in cases:
        res_orig = machine.run(None, case)
        res_cand = machine.run(candidate, case)
        compare(res_orig, res_cand, case["name"])
        check_expected(case, res_orig)
        check_expected(case, res_cand)
        assert res_orig["pc"] == TRAP_ADDR, (
            f"original did not stop at trap on {case['name']}"
        )
        assert res_cand["pc"] == TRAP_ADDR, (
            f"candidate did not stop at trap on {case['name']}"
        )
        assert res_orig["sp"] == res_cand["sp"] == ENTRY_SP, (
            f"SP mismatch on {case['name']}"
        )
        passed += 1
        print(f"  [PASS] {case['name']}")

    print("\nNegative controls:")
    mutants = [
        (
            "mode_b_last_id_off_by_one",
            "id <= func_26a62c::kLastB; ++id",
            "id < func_26a62c::kLastB; ++id",
        ),
        (
            "mode_c_second_pass_start_off_by_one",
            "constexpr u32 kFirstCSecondPass = 0x47F;",
            "constexpr u32 kFirstCSecondPass = 0x480;",
        ),
        (
            "mode_d_second_pass_end_off_by_one",
            "constexpr u32 kLastDSecondPass = 0x802;",
            "constexpr u32 kLastDSecondPass = 0x803;",
        ),
        (
            "mode_d_second_predicate_strictness",
            "camp_func_0028fde4(id) > 0",
            "camp_func_0028fde4(id) != 0",
        ),
        (
            "mode_d_first_predicate_gate",
            "battle_func_0028ec78(id) != 0 &&",
            "battle_func_0028ec78(id) != 0 ||",
        ),
        (
            "mode_b_table_offset",
            "constexpr u32 kTableB = 0x147C;",
            "constexpr u32 kTableB = 0x147E;",
        ),
        (
            "page_row_count",
            "constexpr s32 kPageRows = 0x0B;",
            "constexpr s32 kPageRows = 0x0A;",
        ),
        (
            "page_item_count",
            "reinterpret_cast<volatile u8*>(page_address), count,",
            "reinterpret_cast<volatile u8*>(page_address), 0,",
        ),
        (
            "tail_mode_argument",
            "return camp_func_002831f0(mode);",
            "return camp_func_002831f0(0);",
        ),
        (
            "early_return_value",
            "    default:\n        return work_address;",
            "    default:\n        return 0;",
        ),
    ]
    for name, old, new in mutants:
        mutant = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            baseline = machine.run(None, case)
            mutated = safe_run(machine, mutant, case)
            if baseline != mutated:
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        print(f"  [PASS] mutant detected: {name}")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
