#!/usr/bin/env python3
"""Differential test for script_vm_func_0032acb8 (0x0032acb8) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0032acb8"

FUNC_ADDR = 0x0032ACB8
FUNC_SIZE = 544

STUB_GET_CFG = 0x002A0FAC
STUB_GET_CNT = 0x0029F0F4
STUB_SORT_THUMB = 0x002B7F0A
STUB_SORT_ARM = 0x0027F3D4

ADDR_CAMP_PTR = 0x0043DD50
CAMP_ADDR = 0x20000000
CFG_ADDR = 0x20002000
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


def make_stub_thumb_bx_lr() -> bytes:
    return struct.pack("<HH", 0x4770, 0x46C0)


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
            if name == "script_vm_func_0032acb8":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol script_vm_func_0032acb8 not found")

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
    hi = code[at_off + 3]
    insn = (hi << 24) | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def run_one(
    code_bytes: bytes,
    base_addr: int,
    relocs: list[tuple[str, int]] | None,
    skip: int,
    cfg_byte: int,
    row_count: int,
) -> tuple[list[tuple], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(0x20000000, 0x00010000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    buf = bytearray(code_bytes)
    if relocs is not None:
        for sym_name, off in relocs:
            if "camp_func_002a0fac" in sym_name:
                patch_bl(buf, off, base_addr + off, STUB_GET_CFG)
            elif "camp_func_0029f0f4" in sym_name:
                patch_bl(buf, off, base_addr + off, STUB_GET_CNT)
            elif "func_002b7f0a" in sym_name or "func_0027f3d4" in sym_name:
                patch_bl(buf, off, base_addr + off, STUB_SORT_ARM)
            else:
                raise RuntimeError(f"unexpected relocation: {sym_name}")

    uc.mem_write(base_addr, bytes(buf))
    uc.mem_write(STUB_GET_CFG, make_stub_bx_lr())
    uc.mem_write(STUB_GET_CNT, make_stub_bx_lr())
    uc.mem_write(STUB_SORT_ARM, make_stub_bx_lr())
    uc.mem_write(STUB_SORT_THUMB & ~1, make_stub_thumb_bx_lr())

    uc.mem_write(ADDR_CAMP_PTR, struct.pack("<I", CAMP_ADDR))
    cfg = bytearray(0x20)
    cfg[0x0E] = cfg_byte
    uc.mem_write(CFG_ADDR, bytes(cfg))

    uc.reg_write(arm.UC_ARM_REG_R0, skip)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    calls: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        if address == STUB_GET_CFG:
            calls.append(("get_cfg",))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, CFG_ADDR)
        elif address == STUB_GET_CNT:
            calls.append(("get_cnt", uc_inst.reg_read(arm.UC_ARM_REG_R0)))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, row_count)
        elif address in (STUB_SORT_ARM, STUB_SORT_THUMB & ~1):
            calls.append((
                "sort",
                uc_inst.reg_read(arm.UC_ARM_REG_R0),
                uc_inst.reg_read(arm.UC_ARM_REG_R1),
                uc_inst.reg_read(arm.UC_ARM_REG_R2),
                uc_inst.reg_read(arm.UC_ARM_REG_R3),
            ))

    for addr in (STUB_GET_CFG, STUB_GET_CNT, STUB_SORT_ARM, STUB_SORT_THUMB & ~1):
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    cases = [
        ("skip_nonzero", 1, 0x22, 15),
        ("key_22_asc", 0, 0x22, 15),
        ("key_22_desc", 0, 0x80 | 0x22, 15),
        ("key_21_asc", 0, 0x21, 12),
        ("key_21_desc", 0, 0x80 | 0x21, 12),
        ("key_18_asc", 0, 0x18, 9),
        ("key_18_desc", 0, 0x80 | 0x18, 9),
        ("key_19_asc", 0, 0x19, 7),
        ("key_19_desc", 0, 0x80 | 0x19, 7),
        ("key_1a_asc", 0, 0x1A, 5),
        ("key_1a_desc", 0, 0x80 | 0x1A, 5),
        ("key_other", 0, 0x01, 5),
    ]

    for name, *args in cases:
        o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, *args)
        c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, *args)
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref_calls, _ = run_one(orig_code, FUNC_ADDR, None, 0, 0x22, 15)
    mutants = [
        ("mut_skip", (1, 0x22, 15)),
        ("mut_desc", (0, 0x80 | 0x22, 15)),
        ("mut_key21", (0, 0x21, 15)),
        ("mut_key18", (0, 0x18, 15)),
        ("mut_key1a", (0, 0x1A, 15)),
    ]
    detected = 0
    for mname, margs in mutants:
        m_calls, _ = run_one(cand_code, 0x00180000, cand_relocs, *margs)
        if m_calls != ref_calls:
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: script_vm_func_0032acb8 (0x0032acb8) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
