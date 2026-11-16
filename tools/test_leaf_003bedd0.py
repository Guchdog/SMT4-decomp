#!/usr/bin/env python3
"""Differential test for ui_func_003bedd0 (0x003BEDD0) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the ui_func_003bedd0 body,
resolves its direct calls to deterministic stubs placed at the original
addresses, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.
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
OUT_DIR = ROOT / "build/test_leaf_003bedd0"

FUNC_ADDR = 0x003BEDD0
FUNC_SIZE = 700

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers 0x0022A824..0x003BEDD0
UI_ADDR = 0x00700000
UI_SIZE = 0x00005000
REC1_ADDR = 0x00710000
REC1_SIZE = 0x00001000
REC2_ADDR = 0x00720000
REC2_SIZE = 0x00001000
ROW_ADDR = 0x00730000
ROW_SIZE = 0x00001000
CAMP_ADDR = 0x00740000
CAMP_SIZE = 0x00001000
CTX_ADDR = 0x00780000
OBJ_ADDR = 0x00790000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_293C98 = 0x00293C98  # ui_func_00293c98
STUB_27DCA0 = 0x0027DCA0  # ui_func_0027dca0
STUB_22A824 = 0x0022A824  # ui_func_0022a824
STUB_3BE898 = 0x003BE898  # ui_func_003be898
STUB_282B94 = 0x00282B94  # ui_func_00282b94
STUB_2475E4 = 0x002475E4  # camp_func_002475e4
STUB_22AC9C = 0x0022AC9C  # func_0022ac9c
STUB_2AE3F0 = 0x002AE3F0  # battle_func_002ae3f0
STUB_2AE394 = 0x002AE394  # script_vm_func_002ae394
STUB_28412C = 0x0028412C  # func_0028412c
STUB_23EBF0 = 0x0023EBF0  # camp_func_0023ebf0

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
SYMBOL_TO_ADDRESS = {name: address for address, name in STUB_NAMES.items()}

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
VFP_CALLEE_SAVED = (
    ("d8", arm.UC_ARM_REG_D8, 0x3FF1111122222222),
    ("d9", arm.UC_ARM_REG_D9, 0x3FF3333344444444),
    ("d10", arm.UC_ARM_REG_D10, 0x3FF5555566666666),
    ("d11", arm.UC_ARM_REG_D11, 0x3FF7777788888888),
    ("d12", arm.UC_ARM_REG_D12, 0x3FF99999AAAAAAAA),
    ("d13", arm.UC_ARM_REG_D13, 0x3FFBBBBBCCCCCCCC),
    ("d14", arm.UC_ARM_REG_D14, 0x3FFDDDDDEEEEEEEE),
    ("d15", arm.UC_ARM_REG_D15, 0x3FFFFFFFFFFFFFFF),
)


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("ui_func_003bedd0")
    if candidate is None:
        raise RuntimeError(f"ui_func_003bedd0 not found in {obj_file}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = SYMBOL_TO_ADDRESS.get(rel.symbol_name)
        if target is None:
            raise RuntimeError(f"unresolved relocation {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        offset = target - pc
        if offset & 3:
            raise RuntimeError(f"unaligned ARM target 0x{target:08x}")
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | ((offset >> 2) & 0x00FFFFFF))
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compile failed:\n{result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    result = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"mutant {name} compile failed:\n{result.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for addr, size in (
            (CODE_ADDR, CODE_SIZE),
            (UI_ADDR, UI_SIZE),
            (REC1_ADDR, REC1_SIZE),
            (REC2_ADDR, REC2_SIZE),
            (ROW_ADDR, ROW_SIZE),
            (CAMP_ADDR, CAMP_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(addr, size)

        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))
        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))

        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_stub,
            begin=STUB_22A824,
            end=STUB_3BE898 + 4,
        )
        self.uc.hook_add(
            unicorn.UC_HOOK_MEM_WRITE,
            self._on_write,
            begin=0,
            end=0xFFFFFFFF,
        )

        self.case: dict = {}
        self.call_log: list[tuple] = []
        self.writes: list[tuple[int, int, int]] = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address, size, user_data) -> None:
        if address not in STUB_NAMES:
            return
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_293C98:
            self.call_log.append(("293c98",))
            uc.reg_write(arm.UC_ARM_REG_R0, UI_ADDR)
        elif address == STUB_27DCA0:
            self.call_log.append(("27dca0", r0, s32(r1)))
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                REC1_ADDR if s32(r1) == self.case["primary_id"] else REC2_ADDR,
            )
        elif address == STUB_22A824:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self.call_log.append(("22a824", s32(r0), s0))
            val = self.case["cat_primary"] if s32(r0) == 7 else self.case["cat_secondary"]
            uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(val))
        elif address == STUB_3BE898:
            self.call_log.append(("3be898", s32(r0), s32(r1)))
            uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(self.case["status_scale"]))
        elif address == STUB_282B94:
            self.call_log.append(("282b94", r0, s32(r1)))
            uc.reg_write(arm.UC_ARM_REG_R0, ROW_ADDR)
        elif address == STUB_2475E4:
            self.call_log.append(("2475e4", r1, r2))
            view = bytearray(0x20)
            struct.pack_into("<H", view, 0x02, 0x1234)
            struct.pack_into("<H", view, 0x08, self.case["view_percent"])
            view[0x0E + self.case["affinity_idx"]] = self.case["affinity"]
            uc.mem_write(r0, bytes(view))
        elif address == STUB_22AC9C:
            self.call_log.append(("22ac9c", r0 & 0xFFFF))
            uc.mem_write(r1, struct.pack("<I", 0))
        elif address == STUB_2AE3F0:
            self.call_log.append(("2ae3f0", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR if self.case["has_obj"] else 0)
        elif address == STUB_2AE394:
            self.call_log.append(("2ae394", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, 3)
        elif address == STUB_28412C:
            self.call_log.append(("28412c", r0, s32(r1), s32(r2)))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["bonus"])
        elif address == STUB_23EBF0:
            self.call_log.append(("23ebf0",))
            uc.reg_write(arm.UC_ARM_REG_R0, CAMP_ADDR)

    def run(self, code: bytes, case: dict) -> dict:
        self.case = case
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(UI_ADDR, b"\x00" * UI_SIZE)
        self.uc.mem_write(REC1_ADDR, b"\x00" * REC1_SIZE)
        self.uc.mem_write(REC2_ADDR, b"\x00" * REC2_SIZE)
        self.uc.mem_write(ROW_ADDR, b"\x00" * ROW_SIZE)
        self.uc.mem_write(CAMP_ADDR, b"\x00" * CAMP_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\xCC" * STACK_SIZE)

        self.uc.mem_write(UI_ADDR + 0x44A0, struct.pack("<I", case["global_flags"]))
        self.uc.mem_write(REC1_ADDR + 0x00, struct.pack("<B", case["rec1_flags"]))
        self.uc.mem_write(REC1_ADDR + 0xF0, struct.pack("<hh", case["stat_f0"], case["stat_f2"]))
        self.uc.mem_write(REC2_ADDR + 0x00, struct.pack("<B", case["rec2_flags"]))
        self.uc.mem_write(REC2_ADDR + 0x14B, struct.pack("<B", case["affinity_idx"]))
        self.uc.mem_write(ROW_ADDR + 0x00, struct.pack("<I", case["row_flags"]))
        self.uc.mem_write(CAMP_ADDR + 0x00, struct.pack("<fIf", case["camp_0"], 0, case["camp_8"]))

        # Stack args: [sp+0]=base_int, [sp+4]=range_a, [sp+8]=range_b
        self.uc.mem_write(
            ENTRY_SP,
            struct.pack("<iii", case["base_int"], case["range_a"], case["range_b"]),
        )

        self.uc.reg_write(arm.UC_ARM_REG_R0, case["ctx"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["mode"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["primary_id"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case["secondary_id"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(case["scale_a"]))
        self.uc.reg_write(arm.UC_ARM_REG_S1, f32_bits(case["scale_b"]))
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for name, reg in CALLEE_SAVED.items():
            self.uc.reg_write(reg, CALLEE_SAVED_START[name])
        for _name, reg, val in VFP_CALLEE_SAVED:
            self.uc.reg_write(reg, val)

        self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)

        return {
            "ret": s32(self.uc.reg_read(arm.UC_ARM_REG_R0)),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()},
            "vfp_saved": {name: self.uc.reg_read(reg) for name, reg, _v in VFP_CALLEE_SAVED},
            "call_log": list(self.call_log),
            "writes": sorted(self.writes),
        }


def base_case(**overrides) -> dict:
    case = {
        "name": "base",
        "ctx": CTX_ADDR,
        "mode": 0,
        "primary_id": 10,
        "secondary_id": 20,
        "scale_a": 1.5,
        "scale_b": 2.0,
        "base_int": 30,
        "range_a": 4,
        "range_b": 6,
        "rec1_flags": 0,
        "stat_f0": 40,
        "stat_f2": 60,
        "rec2_flags": 0,
        "affinity_idx": 2,
        "affinity": 120,
        "row_flags": 2,
        "has_obj": True,
        "bonus": 15,
        "global_flags": 0,
        "camp_0": 1.25,
        "camp_8": 0.75,
        "cat_primary": 1.1,
        "cat_secondary": 0.9,
        "status_scale": 1.2,
        "view_percent": 150,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    return [
        base_case(name="ctx_pos_bonus_camp8"),
        base_case(name="ctx_pos_rec1_rec2_flags_obj_null", rec1_flags=4, rec2_flags=4, has_obj=False, affinity=0),
        base_case(name="ctx_pos_suppress_camp", global_flags=0x40000, row_flags=0),
        base_case(name="ctx_null_mode_0", ctx=0, mode=0, row_flags=0),
        base_case(name="ctx_null_mode_1", ctx=0, mode=1, rec1_flags=4, row_flags=0),
        base_case(name="ctx_negative_s32", ctx=-1, mode=0, base_int=-10, row_flags=0),
    ]


def compare_results(orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("ret", "pc", "sp", "callee_saved", "vfp_saved", "call_log", "writes"):
        if orig[key] != cand[key]:
            diffs.append(f"{key} mismatch: orig={orig[key]!r} cand={cand[key]!r}")
    return diffs


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = raw_bin[off : off + FUNC_SIZE]

    cand_code = compile_candidate_baseline()
    print(f"ui_func_003bedd0: orig {len(orig_code)} B, cand {len(cand_code)} B")

    cases = make_cases()
    for case in cases:
        orig_res = Runner().run(orig_code, case)
        cand_res = Runner().run(cand_code, case)
        diffs = compare_results(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{case['name']}]:")
            for d in diffs:
                print(" ", d)
            return 1
        print(f"PASS [{case['name']}] (ret={orig_res['ret']})")

    mutants = [
        ("half", "constexpr float kDivisorHalf = 0.5f;", "constexpr float kDivisorHalf = 0.6f;"),
        ("one_third", "constexpr float kOneThird = 0.333333343f;", "constexpr float kOneThird = 0.25f;"),
        ("stat_mix", "constexpr float kStatMixScale = 4.5f;", "constexpr float kStatMixScale = 4.0f;"),
        ("stat_f2_off", "primary_record + 0xF2", "primary_record + 0xF4"),
        ("stat_f0_off", "primary_record + 0xF0", "primary_record + 0xF2"),
        ("ctx_gt_0", "reinterpret_cast<s32>(ctx) > 0", "reinterpret_cast<s32>(ctx) >= 0"),
    ]
    for name, old, new in mutants:
        m_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig_res = Runner().run(orig_code, case)
            bad_res = Runner().run(m_code, case)
            if compare_results(orig_res, bad_res):
                detected = True
                break
        if not detected:
            print(f"FAIL [mutant {name}]: not detected!")
            return 1
        print(f"PASS [mutant {name} detected]")

    print(f"ALL PASS: {len(cases)} cases + {len(mutants)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
