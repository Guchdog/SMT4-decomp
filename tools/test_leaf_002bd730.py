#!/usr/bin/env python3
"""Differential test for AsdTexture_func_002bd730 (0x002bd730) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "engine" / "asd_texture.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_002bd730"

FUNC_ADDR = 0x002BD730
FUNC_SIZE = 528

STUB_LOCK = 0x002BF2B0
STUB_HEAP_START = 0x002C3B98
STUB_HEAP_SIZE = 0x002C3B88
STUB_RESOLVE = 0x002A6A24
STUB_ALLOC = 0x002C54F0
STUB_COPY = 0x002A69B0
STUB_GPU_ADDR = 0x002BC300

STUB_NAMES = {
    STUB_LOCK: "AsdGpu_Lock",
    STUB_HEAP_START: "AsdGpu_HeapStart",
    STUB_HEAP_SIZE: "AsdGpu_HeapSize",
    STUB_RESOLVE: "AsdGpu_ResolveFormat",
    STUB_ALLOC: "AsdMem_AllocAlign",
    STUB_COPY: "AsdGpu_SubmitCopy",
    STUB_GPU_ADDR: "AsdGpu_Address",
}

HEAP_START = 0x20000000
HEAP_SIZE = 0x02000000
PTR_TEX = 0x30000000
PTR_CONV = 0x30010000
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
    candidate = next((val for name, val in funcs.items() if "AsdTexture_func_002bd730" in name), None)
    if candidate is None:
        raise RuntimeError(f"AsdTexture_func_002bd730 not found in {obj_file}")

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
    obj = OUT_DIR / "asd_texture.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Mutant {name}: {old!r} not found")
    mutant_src = OUT_DIR / f"asd_texture_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"asd_texture_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_TEX, 0x20000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        kind: int,
        w: int,
        h: int,
        fmt2: int,
        param: int,
        data_ptr: int,
        data_size: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x400)
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(PTR_TEX, b"\x00" * 0x50)
        uc.mem_write(PTR_TEX + 0x08, struct.pack("<I", kind))
        uc.mem_write(PTR_TEX + 0x14, struct.pack("<II", w, h))
        uc.mem_write(PTR_TEX + 0x1C, struct.pack("<IIII", fmt2, param, data_ptr, data_size))
        uc.mem_write(PTR_TEX + 0x44, struct.pack("<I", 0xCAFEBABE))

        for stub_addr in STUB_NAMES:
            uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

        calls: list[tuple[object, ...]] = []
        bad_writes: list[int] = []

        def on_mem_invalid(uc_cb: unicorn.Uc, access: int, addr: int, size: int, val: int, _ud: object) -> bool:
            bad_writes.append(addr)
            return False

        def on_code(uc_cb: unicorn.Uc, addr: int, size: int, _ud: object) -> None:
            if addr not in STUB_NAMES:
                return
            r0 = uc_cb.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_cb.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_cb.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc_cb.reg_read(arm.UC_ARM_REG_R3)
            sp = uc_cb.reg_read(arm.UC_ARM_REG_SP)
            if addr == STUB_LOCK:
                calls.append(("lock", r0))
            elif addr == STUB_HEAP_START:
                uc_cb.reg_write(arm.UC_ARM_REG_R0, HEAP_START)
            elif addr == STUB_HEAP_SIZE:
                uc_cb.reg_write(arm.UC_ARM_REG_R0, HEAP_SIZE)
            elif addr == STUB_RESOLVE:
                calls.append(("resolve", r0, r1, r2))
                uc_cb.mem_write(r2, struct.pack("<I", 0x55))
                uc_cb.reg_write(arm.UC_ARM_REG_S0, 0x40800000)  # 4.0f
            elif addr == STUB_ALLOC:
                s0 = struct.unpack("<I", uc_cb.mem_read(sp, 4))[0]
                calls.append(("alloc", r0, r1, r2, r3, s0))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_CONV)
            elif addr == STUB_COPY:
                calls.append(("copy", r0, r1, r2))
            elif addr == STUB_GPU_ADDR:
                calls.append(("gpu_addr", r0))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, r0 ^ 0x10000000)

        h_code = uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        h_mem = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_READ_UNMAPPED, on_mem_invalid)

        uc.reg_write(arm.UC_ARM_REG_R0, PTR_TEX)
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
            "tex": bytes(uc.mem_read(PTR_TEX, 0x48)),
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
    if orig["calls"] != cand["calls"]:
        diffs.append(f"calls mismatch (orig {orig['calls']} vs cand {cand['calls']})")
    if orig["tex"] != cand["tex"]:
        diffs.append("tex mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()
    cases = [
        ("below_heap", 0x20000, 64, 64, 0x675A, 1, 0x10000000, 0x1000),
        ("above_heap", 0x20000, 64, 64, 0x675A, 1, 0x22000000, 0x1000),
        ("unaligned_128", 0x20000, 64, 64, 0x675A, 1, 0x20000040, 0x1000),
        ("bank_cross", 0x20000, 64, 64, 0x675A, 1, 0x21FFF000, 0x2000),
        ("kind_10000", 0x10000, 64, 64, 0x675A, 1, 0x20001000, 0x4000),
        ("kind_20000", 0x20000, 32, 32, 0x675A, 2, 0x20002000, 0x1000),
        ("kind_30000", 0x30000, 16, 32, 0x6755, 3, 0x20003000, 0x800),
    ]
    for label, k, w, h, f2, p, dp, ds in cases:
        orig_res = Runner().run(orig_bytes, k, w, h, f2, p, dp, ds)
        cand_res = Runner().run(cand_bytes, k, w, h, f2, p, dp, ds)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_align_mask", "if ((address & 0x7Fu) != 0)", "if ((address & 0x3Fu) != 0)"),
        ("wrong_bank_mask", "0xFE000000u", "0xFC000000u"),
        ("wrong_kind_10000", "if (texture->kind == 0x10000)", "if (false)"),
        ("wrong_kind_30000", "else if (texture->kind == 0x30000)", "else if (false)"),
        ("drop_submit_copy", "AsdGpu_SubmitCopy(texture->data, texture->converted, byte_size);", "// dropped"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, k, w, h, f2, p, dp, ds in cases:
            if compare(
                Runner().run(orig_bytes, k, w, h, f2, p, dp, ds),
                Runner().run(mut_bytes, k, w, h, f2, p, dp, ds),
            ):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: AsdTexture_func_002bd730 (0x002bd730) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
