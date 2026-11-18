#!/usr/bin/env python3
"""Differential test for aocTexCtrl_func_00393838 (0x00393838) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "engine" / "aoc.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_00393838"

FUNC_ADDR = 0x00393838
FUNC_SIZE = 456

STUB_ALLOC = 0x002C4B84
STUB_COPY = 0x002BCF58

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_COPY: "AsdMem_CopyLarge",
}

PTR_CTRL = 0x20000000
PTR_SRC_PTR = 0x20000100
PTR_FILE = 0x20001000
PTR_HEAP_BASE = 0x20010000
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
    for addr, name in STUB_NAMES.items():
        if name in symbol_name:
            return addr
    return None


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "aocTexCtrl_func_00393838" in name), None)
    if candidate is None:
        raise RuntimeError(f"aocTexCtrl_func_00393838 not found in {obj_file}")

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
            struct.pack_into("<I", code, off, (insn & 0xFF000000) | disp)
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "aoc.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"aoc_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"aoc_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


def build_file(records: list[tuple[int, int, int]]) -> bytes:
    buf = bytearray(0x40)
    for i in range(16):
        struct.pack_into("<I", buf, i * 4, 0x1000 + i)
    struct.pack_into("<i", buf, 0x20, len(records))
    for f0, icnt, f8 in records:
        rec = bytearray(0x0C + icnt * 20)
        rec[0] = f0 & 0xFF
        rec[4] = icnt & 0xFF
        rec[8] = f8 & 0xFF
        for j in range(icnt * 20):
            rec[0x0C + j] = (j + 1) & 0xFF
        buf.extend(rec)
    return bytes(buf)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_CTRL, 0x30000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(self, code: bytes, existing_state: int, records: list[tuple[int, int, int]]) -> dict[str, object]:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x400)
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(PTR_CTRL, struct.pack("<II", PTR_FILE, existing_state))
        uc.mem_write(PTR_SRC_PTR, struct.pack("<I", PTR_FILE))
        uc.mem_write(PTR_FILE, b"\x00" * 0x400)
        uc.mem_write(PTR_FILE, build_file(records))
        uc.mem_write(PTR_HEAP_BASE, b"\x00" * 0x1000)

        for stub_addr in STUB_NAMES:
            uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

        heap_idx = 0
        calls: list[tuple[object, ...]] = []
        bad_writes: list[int] = []

        def on_mem_invalid(uc_cb: unicorn.Uc, access: int, addr: int, size: int, val: int, _ud: object) -> bool:
            bad_writes.append(addr)
            return False

        def on_code(uc_cb: unicorn.Uc, addr: int, size: int, _ud: object) -> None:
            nonlocal heap_idx
            if addr == STUB_ALLOC:
                r0 = uc_cb.reg_read(arm.UC_ARM_REG_R0)
                r1 = uc_cb.reg_read(arm.UC_ARM_REG_R1)
                r2 = uc_cb.reg_read(arm.UC_ARM_REG_R2)
                r3 = uc_cb.reg_read(arm.UC_ARM_REG_R3)
                sp = uc_cb.reg_read(arm.UC_ARM_REG_SP)
                s0 = struct.unpack("<I", uc_cb.mem_read(sp, 4))[0]
                calls.append(("alloc", r0, r1, r2, r3, s0))
                ptr = PTR_HEAP_BASE + heap_idx * 0x100
                heap_idx += 1
                uc_cb.mem_write(ptr, b"\x00" * 0x100)
                uc_cb.reg_write(arm.UC_ARM_REG_R0, ptr)
            elif addr == STUB_COPY:
                r0 = uc_cb.reg_read(arm.UC_ARM_REG_R0)
                r1 = uc_cb.reg_read(arm.UC_ARM_REG_R1)
                r2 = uc_cb.reg_read(arm.UC_ARM_REG_R2)
                calls.append(("copy", r0, r1, r2))
                uc_cb.mem_write(r0, bytes(uc_cb.mem_read(r1, r2)))

        h_code = uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        h_mem = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_READ_UNMAPPED, on_mem_invalid)

        uc.reg_write(arm.UC_ARM_REG_R0, PTR_CTRL)
        uc.reg_write(arm.UC_ARM_REG_R1, PTR_SRC_PTR)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=2000)
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
            "calls": calls,
            "ctrl": bytes(uc.mem_read(PTR_CTRL, 8)),
            "heap": bytes(uc.mem_read(PTR_HEAP_BASE, 0x800)),
            "bad_writes": bad_writes,
        }


def compare(orig: dict[str, object], cand: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("pc", "sp", "callee", "calls", "ctrl", "heap"):
        if orig[k] != cand[k]:
            diffs.append(f"{k} mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()
    cases = [
        ("existing", PTR_HEAP_BASE, [(1, 2, 3)]),
        ("rec0", 0, []),
        ("rec2_mixed", 0, [(11, 2, 13), (7, 0, 9)]),
    ]
    for label, ex, recs in cases:
        orig_res = Runner().run(orig_bytes, ex, recs)
        cand_res = Runner().run(cand_bytes, ex, recs)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_guard", "void aocTexCtrl_func_00393838(AocTexCtrl* ctrl, void** source)\n{\n    if (ctrl->state != nullptr) {\n        return;\n    }", "void aocTexCtrl_func_00393838(AocTexCtrl* ctrl, void** source)\n{"),
        ("wrong_hdr_copy", "for (s32 i = 0; i < 16; ++i)", "for (s32 i = 0; i < 15; ++i)"),
        ("wrong_item_stride", "static_cast<u32>(item_count) * 20u;", "static_cast<u32>(item_count) * 16u;"),
        ("drop_prev_link", "*reinterpret_cast<void**>(prev + 0x10) = rec;", "// dropped"),
        ("wrong_rec_advance", "rec_data += 0x0C + (static_cast<u32>(item_count) * 20u);", "rec_data += 0x0C;"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, ex, recs in cases:
            if compare(Runner().run(orig_bytes, ex, recs), Runner().run(mut_bytes, ex, recs)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: aocTexCtrl_func_00393838 (0x00393838) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
