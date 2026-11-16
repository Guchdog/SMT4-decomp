#!/usr/bin/env python3
"""Differential test for ui_func_003beb40 (0x003beb40) using Unicorn ARM emulation.

Compiles src/engine/leaf_batch45_a.cpp, extracts the ui_func_003beb40 body,
resolves its direct calls to deterministic stub addresses, and runs the pinned
original (extracted/exefs/code.bin) against the candidate in separate Unicorn
machines with identical fixtures.

Compared outputs:
  * signed return value, continuation PC, final SP;
  * callee-saved r4-r11 and the VFP callee-saved pair d8-d11 (s16-s23);
  * the ordered call log (helper name + every register argument, with stack
    pointers replaced by a fixed marker, plus s0/s1 raw float bits);
  * fixture memory that the function must not modify (UI singleton, unit table,
    camp modifier table, low-page null-record fixture, context page);
  * the 0x22-byte view written by the 0x2475E4 stub and the 4-byte dead output
    of the 0x22AC9C stub;
  * any emulated write outside the private stack.

Coverage includes every observable branch outcome: the record-bit-2 0.8/1.0
factor, the row-bit-1 bonus gate with null and non-null objects, the
ui+0x44A0 bit-18 camp-multiplier gate, the secondary-record bit-2 camp table
offset selection, the affinity-byte gate, missing rows (address-zero fixture),
zero/opposite-sign denominators, category helper edge values, and a broad
float/rounding sweep.  Negative controls mutate one float multiplier and one
branch constant in a generated copy of the source; both must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_003beb40"

FUNC_ADDR = 0x003BEB40
FUNC_SIZE = 576

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and all stub addresses below 0x3F0000
LOW_ADDR = 0x00000000
LOW_SIZE = 0x00001000
UI_ADDR = 0x00500000
UI_SIZE = 0x00010000
TABLE_ADDR = 0x00600000
TABLE_SIZE = 0x00020000
CAMP_ADDR = 0x00700000
CAMP_SIZE = 0x00001000
CTX_ADDR = 0x00710000
CTX_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call target addresses; stubs are placed at the same addresses
# so both the original bytes and the relocated candidate resolve to them.
STUB_293C98 = 0x00293C98
STUB_27DCA0 = 0x0027DCA0
STUB_22A824 = 0x0022A824
STUB_3BE898 = 0x003BE898
STUB_282B94 = 0x00282B94
STUB_2475E4 = 0x002475E4
STUB_22AC9C = 0x0022AC9C
STUB_2AE3F0 = 0x002AE3F0
STUB_2AE394 = 0x002AE394
STUB_28412C = 0x0028412C
STUB_23EBF0 = 0x0023EBF0

STUB_NAMES = {
    STUB_293C98: "ui_func_00293c98",
    STUB_27DCA0: "ui_func_0027dca0",
    STUB_22A824: "ui_func_0022a824",
    STUB_3BE898: "ui_func_003be898",
    STUB_282B94: "ui_func_00282b94",
    STUB_2475E4: "camp_func_002475e4",
    STUB_22AC9C: "func_0022ac9c",
    STUB_2AE3F0: "battle_func_002ae3f0",
    STUB_2AE394: "script_vm_func_002ae394",
    STUB_28412C: "func_0028412c",
    STUB_23EBF0: "camp_func_0023ebf0",
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
    "d8": 0x1122334455667788,
    "d9": 0x99AABBCCDDEEFF00,
    "d10": 0x0F1E2D3C4B5A6978,
    "d11": 0x8877665544332211,
}
VFP_REGS = {
    "d8": arm.UC_ARM_REG_D8,
    "d9": arm.UC_ARM_REG_D9,
    "d10": arm.UC_ARM_REG_D10,
    "d11": arm.UC_ARM_REG_D11,
}

ROW_COUNT = 109
ROW_STRIDE = 0x288
ROW_ID_OFFSET = 8
ROW_ID_COUNT = 50


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def bits_f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "003beb40" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"ui_func_003beb40 not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} for {rel.symbol_name}"
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


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
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


def build_table(case: dict) -> bytes:
    table = bytearray(TABLE_SIZE)
    for row_key, id_key, prefix in (
        ("a_row", "id_a", "a"),
        ("b_row", "id_b", "b"),
    ):
        row = case.get(row_key)
        if row is None:
            continue
        row_base = row * ROW_STRIDE
        struct.pack_into(
            "<H", table, row_base + ROW_ID_OFFSET, case[id_key] & 0xFFFF
        )
        struct.pack_into(
            "<I", table, row_base + 0x00, case.get(f"{prefix}_row_flags", 0)
        )
        table[row_base + 0xCC] = case.get(f"{prefix}_cc", 0) & 0xFF
        struct.pack_into(
            "<H", table, row_base + 0x1C0, case.get(f"{prefix}_stat", 0) & 0xFFFF
        )
        table[row_base + 0x217] = case.get(f"{prefix}_affinity", 0) & 0xFF
    return bytes(table)


def build_low(case: dict) -> bytes:
    low = bytearray(LOW_SIZE)
    for offset, value in case.get("low_bytes", {}).items():
        low[offset] = value & 0xFF
    return bytes(low)


def build_ui(case: dict) -> bytes:
    ui = bytearray(UI_SIZE)
    struct.pack_into("<I", ui, 0x44A0, case.get("ui_flags", 0) & 0xFFFFFFFF)
    return bytes(ui)


def build_camp(case: dict) -> bytes:
    camp = bytearray(CAMP_SIZE)
    struct.pack_into("<f", camp, 0x00, float(case.get("camp0", 1.5)))
    struct.pack_into("<f", camp, 0x08, float(case.get("camp8", 1.25)))
    return bytes(camp)


def build_view(case: dict) -> bytes:
    view = bytearray(0x22)
    struct.pack_into("<H", view, 8, case.get("view_percent", 100) & 0xFFFF)
    struct.pack_into("<H", view, 2, case.get("sentinel", 0x1234) & 0xFFFF)
    for offset, value in case.get("view_bytes", {}).items():
        view[offset] = value & 0xFF
    for index, value in case.get("affinity", {}).items():
        view[0x0E + index] = value & 0xFF
    return bytes(view)


class UIRunner:
    """One Unicorn machine with deterministic stubs at the original call targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(LOW_ADDR, LOW_SIZE)
        self.uc.mem_map(UI_ADDR, UI_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(CAMP_ADDR, CAMP_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        # Enable the VFP coprocessor (CP10/CP11) and the floating-point unit.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0)

        self.call_log: list = []
        self.writes: list = []
        self.table = b""
        self.fixture: dict = {}
        self.view_ptr: int | None = None
        self.dead_ptr: int | None = None

    # ------------------------------------------------------------------ stubs
    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _scan(self, unit_id: int) -> int:
        if unit_id > 0x7FFFFFFF:
            unit_id -= 1 << 32
        for row in range(ROW_COUNT):
            row_base = row * ROW_STRIDE
            for slot in range(ROW_ID_COUNT):
                stored = struct.unpack_from(
                    "<h", self.table, row_base + ROW_ID_OFFSET + slot * 2
                )[0]
                if stored < 0:
                    continue
                if stored == unit_id:
                    return row_base
        return 0

    def _category_factor(self, category: int) -> float:
        if category == 8:
            return float(self.fixture["m8"])
        if category == 10:
            return float(self.fixture["m10"])
        return 1.0

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_293C98:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, UI_ADDR)
        elif address == STUB_27DCA0:
            self._log(address, r0, r1)
            row = self._scan(r1)
            uc.reg_write(arm.UC_ARM_REG_R0, TABLE_ADDR + row + 0xCC if row else 0)
        elif address == STUB_282B94:
            self._log(address, r0, r1)
            row = self._scan(r1)
            uc.reg_write(arm.UC_ARM_REG_R0, TABLE_ADDR + row if row else 0)
        elif address == STUB_22A824:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self._log(address, r0, s0)
            uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(self._category_factor(r0)))
        elif address == STUB_3BE898:
            self._log(address, r0, r1)
            uc.reg_write(
                arm.UC_ARM_REG_S0, f32_bits(float(self.fixture["status"]))
            )
        elif address == STUB_2475E4:
            self._log(address, r0, r1, r2)
            uc.mem_write(r0, self.fixture["view"])
            self.view_ptr = r0
        elif address == STUB_22AC9C:
            self._log(address, r0, r1)
            mapped = self.fixture["mapped"]
            if r0 not in (8, 10):
                written = 0x0B if r0 == 11 else r0
                uc.mem_write(r1, struct.pack("<I", written))
            uc.reg_write(arm.UC_ARM_REG_R0, mapped)
            self.dead_ptr = r1
        elif address == STUB_2AE3F0:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.fixture["object"])
        elif address == STUB_2AE394:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.fixture["count"])
        elif address == STUB_28412C:
            self._log(address, r0, r1, r2)
            uc.reg_write(arm.UC_ARM_REG_R0, self.fixture["bonus"])
        elif address == STUB_23EBF0:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, CAMP_ADDR)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            out = []
            for arg in args:
                if STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.view_ptr = None
        self.dead_ptr = None
        self.table = build_table(case)
        self.fixture = {
            "m8": case.get("m8", 1.0),
            "m10": case.get("m10", 1.0),
            "status": case.get("status", 1.0),
            "view": build_view(case),
            "mapped": case.get("mapped", 0x1111),
            "object": CTX_ADDR + 0x100 if case.get("object", False) else 0,
            "count": case.get("count", 0),
            "bonus": case.get("bonus", 0),
        }

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(LOW_ADDR, build_low(case))
        self.uc.mem_write(UI_ADDR, build_ui(case))
        self.uc.mem_write(TABLE_ADDR, self.table)
        self.uc.mem_write(CAMP_ADDR, build_camp(case))
        self.uc.mem_write(CTX_ADDR, bytes((i * 7 + 3) & 0xFF for i in range(CTX_SIZE)))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        # v4 is the only stack argument, at [entry_sp].
        self.uc.mem_write(ENTRY_SP, struct.pack("<i", case.get("v4", 4)))
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["id_a"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["id_b"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("v3", 2) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            reg = CALLEE_SAVED.get(name) or VFP_REGS[name]
            self.uc.reg_write(reg, value)
        self.uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(float(case.get("f0", 10.0))))
        self.uc.reg_write(arm.UC_ARM_REG_S1, f32_bits(float(case.get("f1", 1.0))))
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        view = None
        if self.view_ptr is not None:
            view = bytes(self.uc.mem_read(self.view_ptr, 0x22))
        dead = None
        if self.dead_ptr is not None:
            dead = bytes(self.uc.mem_read(self.dead_ptr, 4))

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not in_stack:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "vfp_saved": {
                name: self.uc.reg_read(reg) for name, reg in VFP_REGS.items()
            },
            "call_log": self._normalise(self.call_log),
            "view": view,
            "dead": dead,
            "fixtures": {
                "low": bytes(self.uc.mem_read(LOW_ADDR, LOW_SIZE)),
                "ui": bytes(self.uc.mem_read(UI_ADDR, UI_SIZE)),
                "table": bytes(self.uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
                "camp": bytes(self.uc.mem_read(CAMP_ADDR, CAMP_SIZE)),
                "ctx": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "vfp_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if orig["view"] != cand["view"]:
        problems.append(f"view buffer:\n    orig={orig['view']!r}\n    cand={cand['view']!r}")
    if orig["dead"] != cand["dead"]:
        problems.append(f"dead output:\n    orig={orig['dead']!r}\n    cand={cand['dead']!r}")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "id_a": 101,
        "id_b": 202,
        "a_row": 2,
        "b_row": 5,
        "a_row_flags": 0,
        "a_cc": 0,
        "a_stat": 100,
        "b_cc": 0,
        "b_affinity": 0,
        "v3": 2,
        "v4": 4,
        "f0": 10.0,
        "f1": 1.0,
        "m8": 1.0,
        "m10": 1.0,
        "status": 1.0,
        "view_percent": 100,
        "camp0": 1.5,
        "camp8": 1.25,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- baseline and record-factor branches (0x3BEBA0 + 0x3BECF0..0x3BED04)
    cases.append(base_case("baseline, both records plain"))
    cases.append(base_case("primary record bit 2 -> 0.8 factor", a_cc=4))
    cases.append(
        base_case("secondary record bit 2 -> camp table +0", b_cc=4)
    )
    cases.append(
        base_case(
            "both records bit 2 -> 0.8 and camp table +0", a_cc=4, b_cc=4
        )
    )
    cases.append(
        base_case("primary record bit 2 with other bits", a_cc=0x05)
    )

    # --- primary stat scaling (0x3BEBB0..0x3BEBA8, 0x3BEC7C)
    cases.append(base_case("negative primary stat", a_stat=-12345 & 0xFFFF))
    cases.append(base_case("zero primary stat", a_stat=0))
    cases.append(base_case("maximum positive primary stat", a_stat=0x7FFF))
    cases.append(base_case("minimum negative primary stat", a_stat=0x8000))

    # --- bonus gate (0x3BEC40/0x3BEC50) and bonus lookup (0x2AE3F0/394/28412C)
    cases.append(
        base_case(
            "bonus row flag, object, count 0",
            a_row_flags=2,
            object=True,
            count=0,
            bonus=0,
        )
    )
    cases.append(
        base_case(
            "bonus row flag, object, count 1",
            a_row_flags=2,
            object=True,
            count=1,
            bonus=7,
        )
    )
    cases.append(
        base_case(
            "bonus row flag, object, count 8",
            a_row_flags=2,
            object=True,
            count=8,
            bonus=42,
        )
    )
    cases.append(
        base_case(
            "bonus row flag, object, count 9",
            a_row_flags=2,
            object=True,
            count=9,
            bonus=-3,
        )
    )
    cases.append(
        base_case(
            "bonus row flag but 0x2AE3F0 returns null",
            a_row_flags=2,
            object=False,
            count=4,
            bonus=99,
        )
    )
    cases.append(
        base_case(
            "bonus row flag clear with object present",
            a_row_flags=0,
            object=True,
            count=4,
            bonus=99,
        )
    )

    # --- global gate bit 18 (0x3BECDC) for both secondary flag values
    cases.append(
        base_case("ui bit 18 set skips camp table", ui_flags=0x40000, b_cc=0)
    )
    cases.append(
        base_case("ui bit 18 set, secondary bit 2 set", ui_flags=0x40000, b_cc=4)
    )
    cases.append(
        base_case("ui flags present without bit 18", ui_flags=0x3FFFF)
    )
    cases.append(
        base_case("camp table +0 path", b_cc=4, camp0=-0.5, camp8=3.25)
    )

    # --- affinity gate (0x3BED28): zero and every in-contract index
    cases.append(base_case("affinity index 0, byte 0"))
    for index in (0, 3, 0x10, 0x11, 0x12, 0x13):
        cases.append(
            base_case(
                f"affinity index 0x{index:02x} non-zero",
                b_affinity=index,
                affinity={index: 50},
            )
        )
    for value in (1, 50, 99, 100, 255):
        cases.append(
            base_case(
                f"affinity byte {value}",
                b_affinity=0,
                affinity={0: value},
            )
        )

    # --- view percentage and caller floats (0x3BEC70..0x3BECD8)
    for percent in (0, 1, 100, 2000, 65535):
        cases.append(
            base_case(f"view percent {percent}", view_percent=percent)
        )
    for f0, f1 in (
        (0.0, 0.0),
        (0.0, 1.0),
        (10.0, 0.0),
        (-10.0, 1.0),
        (-10.5, -1.5),
        (1.0e20, 1.0),
        (-1.0e20, 1.0),
        (1.0e-10, 1.0),
        (123.456, 0.5),
    ):
        cases.append(
            base_case(f"floats f0={f0!r} f1={f1!r}", f0=f0, f1=f1)
        )

    # --- category/status helper values
    for m8, m10, status in (
        (1.5, 0.75, 1.0),
        (0.8333333, 1.6, 0.5),
        (0.0, 1.0, 1.0),
        (1.0, 0.0, 1.0),
        (-1.5, 2.0, 1.0),
        (1.0, 1.0, float("inf")),
        (float("nan"), 1.0, 1.0),
        (1.0e38, 1.0e30, 1.0),
    ):
        cases.append(
            base_case(
                f"category factors m8={m8!r} m10={m10!r} status={status!r}",
                m8=m8,
                m10=m10,
                status=status,
            )
        )

    # --- denominators: zero, opposite signs, negative
    cases.append(base_case("zero denominator, positive numerator", v3=2, v4=-2))
    cases.append(
        base_case("zero denominator, negative numerator", v3=-5, v4=5, f0=-10.0)
    )
    cases.append(
        base_case(
            "zero denominator, zero numerator -> NaN",
            v3=3,
            v4=-3,
            f1=0.0,
        )
    )
    cases.append(base_case("negative denominator", v3=-4, v4=-6))
    cases.append(base_case("opposite signs but non-zero sum", v3=7, v4=-3))
    cases.append(base_case("large signed range values", v3=0x7FFFFFFF, v4=1))

    # --- missing rows exercise the address-zero record fixture
    cases.append(
        base_case("primary row missing, address-zero fixture", a_row=None)
    )
    cases.append(
        base_case(
            "both rows missing, address-zero fixture",
            a_row=None,
            b_row=None,
        )
    )
    cases.append(
        base_case(
            "missing rows read nonzero address-zero fixture",
            a_row=None,
            b_row=None,
            low_bytes={
                0x00: 0x02,
                0xCC: 0x04,
                0xF4: 0x05,
                0x217: 0x03,
            },
        )
    )

    # --- rounding/conversion sweep; the differential itself is the oracle, but
    # these values deliberately sit near x.5 boundaries and outside s32.
    for f0 in (
        1.5,
        4.5,
        4.4999995,
        4.5000005,
        7.5,
        10.5,
        13.5,
        -1.5,
        -4.5,
        -4.4999995,
        -4.5000005,
        -7.5,
        -13.5,
        2.5,
        3.5,
        0.001,
        0.49999997,
        1.0e9,
        -1.0e9,
        8.0e9,
        -8.0e9,
    ):
        cases.append(base_case(f"conversion sweep f0={f0!r}", f0=f0))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = UIRunner().run(orig_code, case)
        cand = UIRunner().run(cand_code, case)
        if orig["view"] is None or orig["dead"] is None:
            raise RuntimeError(f"case {case['name']!r} did not reach the view mappers")
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
    print("Testing ui_func_003beb40 (0x003beb40)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B (relocations resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("stat_scale", "kStatScale = 4.5f;", "kStatScale = 4.0f;"),
        ("bonus_flag", "kRowBonusFlag = 0x02;", "kRowBonusFlag = 0x01;"),
    ):
        mutant = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = UIRunner().run(orig_code, case)
            bad = UIRunner().run(mutant, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
