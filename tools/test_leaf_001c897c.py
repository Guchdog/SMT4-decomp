#!/usr/bin/env python3
"""Differential test for saveLoadUI_DrawMain (0x001c897c) with Unicorn ARM."""

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

ORIG_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "ui" / "save_load.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_001c897c"

FUNC_ADDR = 0x001C897C
FUNC_SIZE = 940

STUB_QSORT = 0x002B7F0A  # Thumb
STUB_26B9EC = 0x0026B9EC
STUB_26B9A4 = 0x0026B9A4

STUB_NAMES = {
    STUB_QSORT: "func_002b7f0a",
    STUB_26B9EC: "ui_func_0026b9ec",
    STUB_26B9A4: "ui_func_0026b9a4",
}

PTR_WORK = 0x20000000
PTR_SRC = 0x20020000
STACK_BASE = 0x7F000000
STACK_SIZE = 0x10000
STACK_INIT = STACK_BASE + STACK_SIZE - 0x200
LR_SENTINEL = 0x90000000

CALLEE_SAVED = {
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
    if "saveLoadUI_DrawMain" in symbol_name:
        return FUNC_ADDR
    for addr, name in STUB_NAMES.items():
        if name in symbol_name:
            return addr
    return None


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "saveLoadUI_DrawMain" in name), None)
    if candidate is None:
        raise RuntimeError(f"saveLoadUI_DrawMain not found in {obj_file}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        off = rel.offset
        sym_name = rel.symbol_name
        rtype = rel.relocation_type
        if rtype in (28, 29):
            dst = _stub_address(sym_name)
            if dst is None:
                raise RuntimeError(f"Unhandled call relocation: {sym_name}")
            pc = FUNC_ADDR + off + 8
            disp = ((dst - pc) >> 2) & 0x00FFFFFF
            insn = struct.unpack_from("<I", code, off)[0]
            if dst == STUB_QSORT and rtype == 28:
                struct.pack_into("<I", code, off, 0xFA000000 | disp)
            else:
                struct.pack_into("<I", code, off, (insn & 0xFF000000) | disp)
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "save_load.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"save_load_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"save_load_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_WORK, 0x30000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        ids: list[int],
        flags: list[int],
        slots: list[int],
        src_ids: list[int],
        count_a: int,
        count_b: int,
        skip_idx: int,
        active_set: set[int],
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x800)
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(PTR_WORK + 0xD100, b"\x00" * 0x200)
        uc.mem_write(PTR_WORK + 0xD114, struct.pack("<8H", *ids))
        uc.mem_write(PTR_WORK + 0xD124, struct.pack("<8H", *flags))
        uc.mem_write(PTR_WORK + 0xD134, struct.pack("<8H", *slots))
        uc.mem_write(PTR_WORK + 0xD2C4, struct.pack("<ii", count_a, count_b))

        uc.mem_write(PTR_SRC, b"\x00" * 0x80)
        uc.mem_write(PTR_SRC + 0x32, struct.pack("<H", 10))
        uc.mem_write(PTR_SRC + 0x34, struct.pack("<8H", *src_ids))

        uc.mem_write(STUB_QSORT, struct.pack("<HH", 0x4770, 0x46C0))
        uc.mem_write(STUB_26B9EC, struct.pack("<I", 0xE12FFF1E))
        uc.mem_write(STUB_26B9A4, struct.pack("<I", 0xE12FFF1E))

        qsort_calls: list[tuple[int, int, int, int]] = []
        bad_writes: list[int] = []

        def on_mem_invalid(uc_cb: unicorn.Uc, access: int, addr: int, size: int, val: int, _ud: object) -> bool:
            bad_writes.append(addr)
            return False

        def on_code(uc_cb: unicorn.Uc, addr: int, size: int, _ud: object) -> None:
            if addr == STUB_QSORT:
                r0 = uc_cb.reg_read(arm.UC_ARM_REG_R0)
                r1 = uc_cb.reg_read(arm.UC_ARM_REG_R1)
                r2 = uc_cb.reg_read(arm.UC_ARM_REG_R2)
                r3 = uc_cb.reg_read(arm.UC_ARM_REG_R3)
                qsort_calls.append((r0, r1, r2, r3))
                arr = list(struct.unpack("<8H", uc_cb.mem_read(r0, 16)))
                arr.sort(key=lambda x: (x == 0, -x))
                uc_cb.mem_write(r0, struct.pack("<8H", *arr))
            elif addr == STUB_26B9EC:
                r1 = uc_cb.reg_read(arm.UC_ARM_REG_R1)
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 1 if r1 in active_set else 0)
            elif addr == STUB_26B9A4:
                r0 = uc_cb.reg_read(arm.UC_ARM_REG_R0)
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 1 if r0 in active_set else 0)

        h_code = uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        h_mem = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_READ_UNMAPPED, on_mem_invalid)

        uc.reg_write(arm.UC_ARM_REG_R0, PTR_WORK)
        uc.reg_write(arm.UC_ARM_REG_R1, 0x12345678)
        uc.reg_write(arm.UC_ARM_REG_R2, PTR_SRC)
        uc.reg_write(arm.UC_ARM_REG_R3, skip_idx & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=10000)
        finally:
            uc.hook_del(h_code)
            uc.hook_del(h_mem)

        callee = {
            reg_name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"))
            for reg_name in CALLEE_SAVED
        }
        return {
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": callee,
            "qsort_calls": qsort_calls,
            "work_mem": bytes(uc.mem_read(PTR_WORK + 0xD114, 0x1D0)),
            "bad_writes": bad_writes,
        }


def compare(orig: dict[str, object], cand: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    if orig["pc"] != cand["pc"]:
        diffs.append(f"pc: orig={orig['pc']:#x} cand={cand['pc']:#x}")
    if orig["sp"] != cand["sp"]:
        diffs.append(f"sp: orig={orig['sp']:#x} cand={cand['sp']:#x}")
    if orig["callee"] != cand["callee"]:
        diffs.append("callee-saved register mismatch")
    if orig["qsort_calls"] != cand["qsort_calls"]:
        diffs.append(f"qsort mismatch (orig {len(orig['qsort_calls'])} vs cand {len(cand['qsort_calls'])})")
    if orig["work_mem"] != cand["work_mem"]:
        diffs.append("work memory mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()
    cases = [
        ("skip_neg1", [10, 20, 0, 0, 0, 0, 0, 0], [1]*8, [10, 20, 0, 0, 0, 0, 0, 0], [10]*8, 2, 2, -1, {10, 20}),
        ("no_match", [10, 20, 0, 0, 0, 0, 0, 0], [1]*8, [10, 20, 0, 0, 0, 0, 0, 0], [99]*8, 2, 2, 0, {10, 20}),
        ("old1_new0_nz", [10, 20, 40, 0, 0, 0, 0, 0], [1]*8, [20, 30, 0, 0, 0, 0, 0, 0], [20, 40, 0, 0, 0, 0, 0, 0], 3, 2, 0, {10, 20, 30}),
        ("old0_new1", [10, 50, 0, 0, 0, 0, 0, 0], [0]*8, [50, 0, 0, 0, 0, 0, 0, 0], [50, 60, 0, 0, 0, 0, 0, 0], 1, 0, 0, {60}),
        ("old0_new0_dup", [10, 50, 60, 0, 0, 0, 0, 0], [0]*8, [50, 50, 70, 0, 0, 0, 0, 0], [50, 80, 90, 0, 0, 0, 0, 0], 3, 0, 0, set()),
    ]
    for label, ids, flags, slots, src_ids, ca, cb, sk, act in cases:
        orig_res = Runner().run(orig_bytes, ids, flags, slots, src_ids, ca, cb, sk, act)
        cand_res = Runner().run(cand_bytes, ids, flags, slots, src_ids, ca, cb, sk, act)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_skip_neg1", "skip_idx == -1 ||", ""),
        ("wrong_flag_set", "work[0xD2D0 + i] = 1;", "work[0xD2D0 + i] = 0;"),
        ("wrong_shift_loop", "slots[k] = slots[k - 1];", "slots[k] = 0;"),
        ("wrong_count_b_inc", "++(*count_b);", "--(*count_b);"),
        ("drop_tail_call", "saveLoadUI_DrawMain(work, record_arg, src, i);", "// dropped"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, ids, flags, slots, src_ids, ca, cb, sk, act in cases:
            if compare(
                Runner().run(orig_bytes, ids, flags, slots, src_ids, ca, cb, sk, act),
                Runner().run(mut_bytes, ids, flags, slots, src_ids, ca, cb, sk, act),
            ):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: saveLoadUI_DrawMain (0x001c897c) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
