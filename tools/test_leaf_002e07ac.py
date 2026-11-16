#!/usr/bin/env python3
"""Differential test for StaffRoll_U_UR_Draw (0x002e07ac) with Unicorn ARM.

Compiles src/battle/btl_target_select.cpp, extracts StaffRoll_U_UR_Draw,
resolves its direct calls and literal-pool relocations against the pinned
target addresses, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * continuation PC (0x90000000), final SP, callee-saved r4-r11;
  * ordered call log including:
      - script_vm_func_002bef14();
      - ui_func_002c3ba8(gpu_state);
      - ui_func_002c5f7c(1, 0);
      - indirect flush callback on push/pop when dirty != 0 or value changed;
      - 12 calls to ui_func_002bf460(2, 0x34, i*1000, x, y, 2) with 2 stack args;
      - ui_func_002bf710(1.0f);
  * GPU render stack page (+0x124C..+0x12A0);
  * unexpected writes outside the GPU render stack and program stack.

Coverage:
  * dirty=0 with push value equal to previous top (no push flush) and
    different from previous top (push + pop flush);
  * dirty=1 forcing flush even when pushed value equals previous top;
  * positive, zero, negative, and fractional float coordinates in the 12-entry
    table (truncation semantics of `static_cast<s32>(f32)`);
  * negative/mutation controls on kEntryCount, kSubIdStep, kPanelId,
    ui_func_002bf710(1.0f), and the dirty/equality flush condition.
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
SOURCE = ROOT / "src/battle/btl_target_select.cpp"
OUT_DIR = ROOT / "build/test_leaf_002e07ac"

FUNC_ADDR = 0x002E07AC
FUNC_SIZE = 296

CODE_ADDR = 0x002B0000
CODE_SIZE = 0x00080000  # covers 0x002BEF14..0x002E08D4 and flush stub
PTR_TABLE = 0x00432CC8
PTR_GPU_STATE = 0x0044EA00
TABLE_PAGE = 0x00432000
GPU_PTR_PAGE = 0x0044E000
ENTRIES_ADDR = 0x00500000
GPU_STATE_ADDR = 0x00510000
GPU_STATE_SIZE = 0x00002000
FLUSH_STUB_ADDR = 0x002F0000
PAGE_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2BEF14 = 0x002BEF14
STUB_2C3BA8 = 0x002C3BA8
STUB_2C5F7C = 0x002C5F7C
STUB_2BF460 = 0x002BF460
STUB_2BF710 = 0x002BF710

STUB_NAMES = {
    STUB_2BEF14: "script_vm_func_002bef14",
    STUB_2C3BA8: "ui_func_002c3ba8",
    STUB_2C5F7C: "ui_func_002c5f7c",
    STUB_2BF460: "ui_func_002bf460",
    STUB_2BF710: "ui_func_002bf710",
    FLUSH_STUB_ADDR: "gpu_flush_cb",
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
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def _stub_address(symbol_name: str) -> int | None:
    for address in STUB_NAMES:
        if f"{address:08x}" in symbol_name:
            return address
    return None


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "StaffRoll_U_UR_Draw" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"StaffRoll_U_UR_Draw not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = _stub_address(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            sym = rel.symbol_name
            if "g_StaffRollEntryTable" in sym:
                target = PTR_TABLE + addend
            elif "g_AsdGpuState" in sym:
                target = PTR_GPU_STATE + addend
            else:
                raise RuntimeError(f"unresolved ABS32 relocation: {sym!r}")
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "btl_target_select.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


class Runner:
    """One Unicorn machine with deterministic stubs for StaffRoll_U_UR_Draw."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(
            arm.UC_ARM_REG_C1_C0_2,
            self.uc.reg_read(arm.UC_ARM_REG_C1_C0_2) | 0x00F00000,
        )
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(TABLE_PAGE, PAGE_SIZE)
        self.uc.mem_map(GPU_PTR_PAGE, PAGE_SIZE)
        self.uc.mem_map(ENTRIES_ADDR, PAGE_SIZE)
        self.uc.mem_map(GPU_STATE_ADDR, GPU_STATE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            self.uc.mem_write(addr, bx_lr)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE320F000))

        self.case: dict = {}
        self.call_log: list[tuple] = []
        self.bad_writes: list[tuple[int, int, int]] = []

        for addr in STUB_NAMES:
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_stub, None, addr, addr)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _on_stub(
        self, uc: unicorn.Uc, address: int, size: int, user_data: object
    ) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        sp = uc.reg_read(arm.UC_ARM_REG_SP)

        if address == STUB_2BEF14:
            self.call_log.append((address,))
        elif address == STUB_2C3BA8:
            self.call_log.append((address, r0))
        elif address == STUB_2C5F7C:
            self.call_log.append((address, r0, r1))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["new_val"])
        elif address == STUB_2BF460:
            stack_args = struct.unpack("<2i", self.uc.mem_read(sp, 8))
            self.call_log.append(
                (address, r0, r1, r2, struct.unpack("<i", struct.pack("<I", r3))[0], stack_args)
            )
        elif address == STUB_2BF710:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self.call_log.append((address, s0))
        elif address == FLUSH_STUB_ADDR:
            self.call_log.append((address, r0))

    def _on_write(
        self,
        uc: unicorn.Uc,
        access: int,
        address: int,
        size: int,
        value: int,
        user_data: object,
    ) -> None:
        stack_base = GPU_STATE_ADDR + 0x124C
        allowed = (
            (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
            or (stack_base <= address < stack_base + 0x40)
        )
        if not allowed:
            self.bad_writes.append((address, size, value))

    def run(self, code: bytes, case: dict) -> dict:
        self.case = case
        self.call_log = []
        self.bad_writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * max(FUNC_SIZE, len(code) + 16))
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(STACK_ADDR, b"\xCD" * STACK_SIZE)

        self.uc.mem_write(PTR_TABLE, struct.pack("<I", ENTRIES_ADDR))
        self.uc.mem_write(PTR_GPU_STATE, struct.pack("<I", GPU_STATE_ADDR))

        entries = bytearray(b"\x00" * 0x100)
        for i, (x, y) in enumerate(case["coords"]):
            struct.pack_into("<ff", entries, i * 8 + 8, x, y)
        self.uc.mem_write(ENTRIES_ADDR, bytes(entries))

        gpu = bytearray(b"\x00" * GPU_STATE_SIZE)
        sb = 0x124C
        struct.pack_into("<I", gpu, sb + 0x00, 1)  # stack count = 1
        struct.pack_into("<I", gpu, sb + 0x08 + 4, case["prev_val"])
        gpu[sb + 0x18] = case["dirty"] & 0xFF
        struct.pack_into("<I", gpu, sb + 0x1C, FLUSH_STUB_ADDR)
        self.uc.mem_write(GPU_STATE_ADDR, bytes(gpu))

        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x12345678)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for name, reg in CALLEE_SAVED.items():
            self.uc.reg_write(reg, CALLEE_SAVED_START[name])

        self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000, count=200_000)

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()},
            "calls": list(self.call_log),
            "gpu_stack": bytes(self.uc.mem_read(GPU_STATE_ADDR + 0x124C, 0x40)),
            "bad_writes": list(self.bad_writes),
        }


def build_cases() -> list[dict]:
    coords_a = [(float(i * 10 - 35), float(i * 5 + 0.75)) for i in range(12)]
    coords_b = [(-12.9, 0.0), (100.5, -44.2), (0.0, 240.0)] * 4
    return [
        {
            "name": "clean_equal_no_flush",
            "prev_val": 0x11112222,
            "new_val": 0x11112222,
            "dirty": 0,
            "coords": coords_a,
        },
        {
            "name": "clean_diff_push_and_pop_flush",
            "prev_val": 0x11112222,
            "new_val": 0x33334444,
            "dirty": 0,
            "coords": coords_b,
        },
        {
            "name": "dirty_equal_forces_push_flush_then_clean_pop",
            "prev_val": 0xAAAA0001,
            "new_val": 0xAAAA0001,
            "dirty": 1,
            "coords": coords_a,
        },
    ]


def compare_outputs(name: str, orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee", "calls", "gpu_stack", "bad_writes"):
        if orig[key] != cand[key]:
            diffs.append(f"{name}: {key} orig={orig[key]!r} cand={cand[key]!r}")
    if cand["sp"] != ENTRY_SP:
        diffs.append(f"{name}: sp not restored: {cand['sp']:#x}")
    if cand["callee"] != CALLEE_SAVED_START:
        diffs.append(f"{name}: callee-saved clobbered: {cand['callee']!r}")
    if cand["bad_writes"]:
        diffs.append(f"{name}: unexpected writes: {cand['bad_writes']!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()

    orig_runner = Runner()
    cand_runner = Runner()
    cases = build_cases()

    for case in cases:
        orig_res = orig_runner.run(orig_bytes, case)
        cand_res = cand_runner.run(cand_bytes, case)
        diffs = compare_outputs(case["name"], orig_res, cand_res)
        if diffs:
            for d in diffs:
                print("FAIL:", d)
            return 1

    mutants = [
        ("entry_count", "kEntryCount = 12;", "kEntryCount = 11;"),
        ("sub_id_step", "kSubIdStep = 1000;", "kSubIdStep = 100;"),
        ("panel_id", "kPanelId = 0x34;", "kPanelId = 0x35;"),
        ("alpha_blend", "ui_func_002bf710(1.0f);", "ui_func_002bf710(0.5f);"),
        ("dirty_guard", "if (stack[0x18] != 0 || prev != val)", "if (prev != val)"),
    ]
    for m_name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(m_name, old, new)
        mut_runner = Runner()
        detected = False
        for case in cases:
            orig_res = orig_runner.run(orig_bytes, case)
            mut_res = mut_runner.run(mut_bytes, case)
            if compare_outputs(case["name"], orig_res, mut_res):
                detected = True
                break
        if not detected:
            print(f"FAIL: mutant {m_name} was not detected")
            return 1

    print(
        f"PASS: StaffRoll_U_UR_Draw (0x002e07ac) matched original across "
        f"{len(cases)} cases and detected {len(mutants)}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
