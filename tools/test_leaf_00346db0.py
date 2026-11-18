#!/usr/bin/env python3
"""Differential test for AsdPrimRenderData_func_00346db0 (0x00346db0) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_00346db0"

FUNC_ADDR = 0x00346DB0
FUNC_SIZE = 992

STUB_VERTEX_SIZE = 0x00347380
STUB_WORK_ALLOC = 0x002C34A4
STUB_GPU_ADDR = 0x002BC300
STUB_GPU_SUBMIT = 0x0023BB2C
STUB_WORK_ALLOC2 = 0x002BF798

STUB_NAMES = {
    STUB_VERTEX_SIZE: "AsdPrim_VertexSize",
    STUB_WORK_ALLOC: "AsdWork_Alloc",
    STUB_GPU_ADDR: "AsdGpu_Address",
    STUB_GPU_SUBMIT: "AsdGpu_Submit",
    STUB_WORK_ALLOC2: "engine_func_002bf798",
}

PTR_DATA = 0x20000000
PTR_VTX_BUF = 0x20010000
PTR_IDX_BUF = 0x20020000
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
    candidate = next((val for name, val in funcs.items() if "AsdPrimRenderData_func_00346db0" in name), None)
    if candidate is None:
        raise RuntimeError(f"AsdPrimRenderData_func_00346db0 not found in {obj_file}")

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
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"asd_texture_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"asd_texture_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_DATA, 0x00030000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        *,
        flags: int,
        vtx_count: int,
        idx_count: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(PTR_DATA, b"\x00" * 0x800)
        struct.pack_into("<I", dbuf := bytearray(0x20), 4, flags)
        struct.pack_into("<I", dbuf, 0x0C, vtx_count)
        struct.pack_into("<I", dbuf, 0x18, idx_count)
        uc.mem_write(PTR_DATA, bytes(dbuf))
        uc.mem_write(PTR_DATA + 0x7E4, b"\x55")
        uc.mem_write(PTR_VTX_BUF, b"\xAA" * 0x1000)
        uc.mem_write(PTR_IDX_BUF, b"\xBB" * 0x400)

        calls: list[tuple[str, tuple[object, ...]]] = []

        def ret_arm(val: int | None = None) -> None:
            if val is not None:
                uc.reg_write(arm.UC_ARM_REG_R0, val & 0xFFFFFFFF)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            uc.reg_write(arm.UC_ARM_REG_PC, lr & ~1)

        def on_code(uc_inst: unicorn.Uc, address: int, _size: int, _user: object) -> None:
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(arm.UC_ARM_REG_R3)
            if address == STUB_VERTEX_SIZE:
                calls.append(("vtx_size", (r0,)))
                ret_arm(vtx_count * 40)
            elif address == STUB_WORK_ALLOC:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                a4, a5 = struct.unpack("<II", uc_inst.mem_read(sp, 8))
                calls.append(("work_alloc", (r0, r1, r2, r3, a4, a5)))
                ret_arm(PTR_VTX_BUF)
            elif address == STUB_WORK_ALLOC2:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                a4, a5 = struct.unpack("<II", uc_inst.mem_read(sp, 8))
                calls.append(("work_alloc2", (r0, r1, r2, r3, a4, a5)))
                ret_arm(PTR_IDX_BUF)
            elif address == STUB_GPU_ADDR:
                calls.append(("gpu_addr", (r0,)))
                ret_arm(r0 + 0x40000000)
            elif address == STUB_GPU_SUBMIT:
                attr = bytes(uc_inst.mem_read(r1, 8))
                calls.append(("gpu_submit", (r0, attr, r2, r3)))
                ret_arm(None)

        hooks = [uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES]
        uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.reg_write(arm.UC_ARM_REG_R0, PTR_DATA)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            for h in hooks:
                uc.hook_del(h)

        ptrs = struct.unpack("<IIIII", uc.mem_read(PTR_DATA + 0x2C, 20))
        idx_buf_ptr = struct.unpack("<I", uc.mem_read(PTR_DATA + 0x48, 4))[0]
        idx_addr, idx_addr_cnt = struct.unpack("<II", uc.mem_read(PTR_DATA + 0x7DC, 8))
        idx_uploaded = uc.mem_read(PTR_DATA + 0x7E4, 1)[0]

        vtx_snap = b""
        if flags & 2:
            uv_ptr = ptrs[2]
            vtx_snap += bytes(uc.mem_read(uv_ptr, vtx_count * 16))
        if flags & 0x20:
            col_ptr = ptrs[3]
            vtx_snap += bytes(uc.mem_read(col_ptr, vtx_count * 4))
        idx_snap = bytes(uc.mem_read(idx_buf_ptr, idx_count * 2))

        return {
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "ptrs": ptrs,
            "idx_buf_ptr": idx_buf_ptr,
            "idx_meta": (idx_addr, idx_addr_cnt, idx_uploaded),
            "vtx_snap": vtx_snap,
            "idx_snap": idx_snap,
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("sp", "callee", "ptrs", "idx_buf_ptr", "idx_meta", "vtx_snap", "idx_snap", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()

    cases = [
        ("all_gpu_odd", {"flags": 0x127, "vtx_count": 3, "idx_count": 5}),
        ("no_gpu_even", {"flags": 0x027, "vtx_count": 2, "idx_count": 4}),
        ("empty_counts", {"flags": 0x127, "vtx_count": 0, "idx_count": 0}),
        ("pos_only_gpu", {"flags": 0x101, "vtx_count": 1, "idx_count": 1}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, **kw)
        cand_res = Runner().run(cand_bytes, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_gpu_arena", "data->buffer = AsdWork_Alloc(0x10000, 0x100, 0, vtx_size, 0x10, 1);", "data->buffer = AsdWork_Alloc(0x100, 0x100, 0, vtx_size, 0x10, 1);"),
        ("wrong_uv_val", "values[i] = 1.0f;", "values[i] = 0.0f;"),
        ("wrong_color_val", "values[i] = 0xFF;", "values[i] = 0xFE;"),
        ("wrong_idx_init", "indices[i] = 0;", "indices[i] = 1;"),
        ("drop_idx_addr", "data->index_address = AsdGpu_Address(data->index_buffer);", "data->index_address = 0;"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, kw in cases:
            if compare(Runner().run(orig_bytes, **kw), Runner().run(mut_bytes, **kw)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: AsdPrimRenderData_func_00346db0 (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
