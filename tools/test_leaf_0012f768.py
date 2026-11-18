#!/usr/bin/env python3
"""Differential test for engine_func_0012f768 (0x0012f768) with Unicorn ARM."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_0012f768"

FUNC_ADDR = 0x0012F768
FUNC_SIZE = 492

STUBS = {
    0x0013FDB0: "engine_func_0013fdb0",
    0x002BB218: "engine_func_002bb218",
    0x002BB0B4: "engine_func_002bb0b4",
    0x002B4D78: "engine_func_002b4d78",
    0x001409B8: "func_001409b8",
    0x002ACB8C: "func_002acb8c",
    0x002B4FA8: "func_002b4fa8",
}
VTBL_SLOT1_STUB = 0x003F0100

OBJ_ADDR = 0x20000000
ARR0_ADDR = 0x20001000
ARR1_ADDR = 0x20010000
ARR2_ADDR = 0x20020000
ARR3_ADDR = 0x20030000
VTBL_ADDR = 0x20000400
MGR_ADDR = 0x20000500
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


def make_stub_bx_lr() -> bytes:
    return struct.pack("<I", 0xE12FFF1E)


def compile_candidate() -> tuple[bytes, list[tuple[str, int]]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_path = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_path)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed:\n{res.stderr}\n{res.stdout}")

    data = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    secs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = secs[e_shstrndx][4]
    sec_names = [data[shstr_off + s[0] : data.index(b"\x00", shstr_off + s[0])].decode("ascii", errors="replace") for s in secs]
    tidx = sec_names.index(".text")
    text_data = data[secs[tidx][4] : secs[tidx][4] + secs[tidx][5]]

    symtab = next(s for s in secs if s[1] == 2)
    strtab_off = secs[symtab[6]][4]
    fn_off = fn_size = None
    for idx in range(symtab[5] // 16):
        st_name, st_value, st_size, _st_info, _st_other, st_shndx = struct.unpack_from("<IIIbbH", data, symtab[4] + idx * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == "engine_func_0012f768":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol engine_func_0012f768 not found")

    relocs: list[tuple[str, int]] = []
    for s in secs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if fn_off <= r_off < fn_off + fn_size and r_type in (28, 29):
                    st_name = struct.unpack_from("<I", data, symtab[4] + sym_idx * 16)[0]
                    sname = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
                    relocs.append((sname, r_off - fn_off))

    return bytes(text_data[fn_off : fn_off + fn_size]), relocs


def patch_bl(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    insn = 0xEB000000 | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def run_one(
    code_bytes: bytes,
    base_addr: int,
    relocs: list[tuple[str, int]] | None,
    count0: int,
    b4: int,
    b8: int,
    sz1: int,
    sz2: int,
    sz3: int,
    mutate_fn=None,
) -> tuple[bytes, list[tuple[str, int, int, int]], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(0x20000000, 0x00050000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    buf = bytearray(code_bytes)
    if relocs is not None:
        name_to_addr = {v: k for k, v in STUBS.items()}
        for sym_name, off in relocs:
            target = name_to_addr.get(sym_name)
            if target is None:
                raise RuntimeError(f"unexpected relocation: {sym_name}")
            patch_bl(buf, off, base_addr + off, target)

    uc.mem_write(base_addr, bytes(buf))
    for addr in [*STUBS.keys(), VTBL_SLOT1_STUB]:
        uc.mem_write(addr, make_stub_bx_lr())

    # Vtable with slot 1 pointing to VTBL_SLOT1_STUB
    uc.mem_write(VTBL_ADDR, struct.pack("<II", 0, VTBL_SLOT1_STUB))

    for arr, stride, sz in ((ARR1_ADDR, 0x558, sz1), (ARR2_ADDR, 0x460, sz2), (ARR3_ADDR, 0x2BD4, sz3)):
        cnt = sz // stride
        for i in range(cnt):
            uc.mem_write(arr + i * stride, struct.pack("<I", VTBL_ADDR))

    obj = bytearray(0xC0)
    for off in range(0, 0xC0, 4):
        struct.pack_into("<I", obj, off, 0xA0000000 + off)
    struct.pack_into("<I", obj, 0x20, count0)
    struct.pack_into("<I", obj, 0x24, ARR0_ADDR)
    struct.pack_into("<I", obj, 0x28, ARR1_ADDR)
    struct.pack_into("<I", obj, 0x2C, sz1)
    struct.pack_into("<I", obj, 0x34, 0x11111111)
    struct.pack_into("<I", obj, 0x40, 0x22222222)
    struct.pack_into("<I", obj, 0x48, ARR2_ADDR)
    struct.pack_into("<I", obj, 0x4C, sz2)
    struct.pack_into("<I", obj, 0x54, 0x33333333)
    struct.pack_into("<I", obj, 0x60, 0x44444444)
    struct.pack_into("<I", obj, 0x68, ARR3_ADDR)
    struct.pack_into("<I", obj, 0x6C, sz3)
    struct.pack_into("<I", obj, 0x74, 0x55555555)
    struct.pack_into("<I", obj, 0x80, 0x66666666)
    struct.pack_into("<I", obj, 0xB4, b4)
    struct.pack_into("<I", obj, 0xB8, b8)
    uc.mem_write(OBJ_ADDR, bytes(obj))

    if mutate_fn is not None:
        mutate_fn(uc)

    uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    calls: list[tuple[str, int, int, int]] = []
    all_hooks = {**STUBS, VTBL_SLOT1_STUB: "vtbl_dtor"}

    arities = {
        "engine_func_0013fdb0": 2,
        "engine_func_002bb218": 0,
        "engine_func_002bb0b4": 2,
        "engine_func_002b4d78": 2,
        "func_001409b8": 1,
        "func_002acb8c": 3,
        "func_002b4fa8": 3,
        "vtbl_dtor": 1,
    }

    def hook_code(uc_inst, address, size, user_data):
        tag = all_hooks.get(address)
        if tag is not None:
            argc = arities[tag]
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0) if argc >= 1 else 0
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1) if argc >= 2 else 0
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2) if argc >= 3 else 0
            calls.append((tag, r0, r1, r2))
            if address == 0x002BB218:
                uc_inst.reg_write(arm.UC_ARM_REG_R0, MGR_ADDR)
            elif address == 0x002BB0B4:
                uc_inst.reg_write(arm.UC_ARM_REG_R0, 0x13572468)

    for addr in all_hooks:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    out_obj = bytes(uc.mem_read(OBJ_ADDR, 0xC0))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_obj, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    cases = [
        ("zero_b4_early_exit", 0, 0, 0x99, 0x558 * 2, 0x460, 0x2BD4),
        ("count0_3_b4_0", 3, 0, 0x77, 0, 0, 0),
        ("all_arrays_active", 2, 0x20050000, 0x1234, 0x558 * 2, 0x460 * 3, 0x2BD4 * 2),
        ("non_multiple_sizes", 1, 0x20060000, 0x5555, 0x558 * 2 + 0x100, 0x460 - 1, 0x2BD4 + 0x123),
        ("empty_arrays_b4_nonzero", 0, 0x20070000, 0x8888, 0, 0, 0),
    ]

    for name, count0, b4, b8, sz1, sz2, sz3 in cases:
        o_obj, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, count0, b4, b8, sz1, sz2, sz3)
        c_obj, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, count0, b4, b8, sz1, sz2, sz3)
        if o_obj != c_obj:
            print(f"FAIL {name}: obj memory mismatch")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    mutants = [
        ("mut_count0", lambda uc: uc.mem_write(OBJ_ADDR + 0x20, struct.pack("<I", 1))),
        ("mut_b4_zero", lambda uc: uc.mem_write(OBJ_ADDR + 0xB4, struct.pack("<I", 0))),
        ("mut_sz1", lambda uc: uc.mem_write(OBJ_ADDR + 0x2C, struct.pack("<I", 0x558))),
        ("mut_sz2", lambda uc: uc.mem_write(OBJ_ADDR + 0x4C, struct.pack("<I", 0x460))),
        ("mut_sz3", lambda uc: uc.mem_write(OBJ_ADDR + 0x6C, struct.pack("<I", 0x2BD4))),
    ]
    _, c0, b4, b8, s1, s2, s3 = cases[2]
    ref_obj, ref_calls, _ = run_one(orig_code, FUNC_ADDR, None, c0, b4, b8, s1, s2, s3)
    detected = 0
    for mname, mfn in mutants:
        m_obj, m_calls, _ = run_one(cand_code, 0x00180000, cand_relocs, c0, b4, b8, s1, s2, s3, mutate_fn=mfn)
        if m_obj != ref_obj or m_calls != ref_calls:
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: engine_func_0012f768 (0x0012f768) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
