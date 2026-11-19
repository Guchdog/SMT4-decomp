#!/usr/bin/env python3
"""Differential test for camp_func_0026adcc (0x0026adcc) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0026adcc"

FUNC_ADDR = 0x0026ADCC
FUNC_SIZE = 592

STUBS = {
    0x0029D8FC: "ui_func_0029d8fc",
    0x0029F0F4: "camp_func_0029f0f4",
    0x001C35A0: "func_001c35a0",
    0x0029EBF8: "engine_func_0029ebf8",
    0x001C3588: "script_vm_func_001c3588",
    0x002C615C: "ui_func_002c615c",
    0x0029EB58: "camp_func_0029eb58",
    0x0029F260: "camp_func_0029f260",
    0x0029F248: "camp_func_0029f248",
    0x0029EBDC: "camp_func_0029ebdc",
    0x0029EBA8: "engine_func_0029eba8",
    0x0029EDFC: "camp_func_0029edfc",
    0x002B91C4: "script_vm_func_002b91c4",
}

CURSOR_ADDR = 0x20000000
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
            if name == "camp_func_0026adcc":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol camp_func_0026adcc not found")

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


def pack_xy(x: int, y: int) -> int:
    return (x & 0xFFFF) | ((y & 0xFFFF) << 16)


def run_one(
    code_bytes: bytes,
    base_addr: int,
    relocs: list[tuple[str, int]] | None,
    pos: tuple[int, int],
    size: tuple[int, int],
    key_states: dict[int, int],
    is_grid: int,
    play_se: int,
    touch_xy: tuple[int, int],
    cur_pos: int,
    cur_off: int,
    total_cnt: int,
) -> tuple[int, list[tuple], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(0x20000000, 0x00010000)
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
    for addr in STUBS:
        uc.mem_write(addr, make_stub_bx_lr())

    uc.reg_write(arm.UC_ARM_REG_R0, CURSOR_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, pack_xy(*pos))
    uc.reg_write(arm.UC_ARM_REG_R2, pack_xy(*size))
    uc.reg_write(arm.UC_ARM_REG_R3, 102)
    uc.mem_write(STACK_INIT, struct.pack("<IIII", 100, 101, is_grid, play_se))
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    calls: list[tuple] = []

    def hook_code(uc_inst, address, sz, user_data):
        tag = STUBS.get(address)
        if tag is None:
            return
        r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
        if tag == "ui_func_0029d8fc":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, key_states.get(r0, 0))
        elif tag in ("camp_func_0029f0f4", "engine_func_0029ebf8"):
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, total_cnt)
        elif tag == "func_001c35a0":
            calls.append((tag,))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, touch_xy[1])
        elif tag == "script_vm_func_001c3588":
            calls.append((tag,))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, touch_xy[0])
        elif tag == "ui_func_002c615c":
            calls.append((tag, r0, r1))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, r0 // r1 if r1 else 0)
        elif tag in ("camp_func_0029eb58", "camp_func_0029edfc"):
            calls.append((tag, r0, r1))
        elif tag in ("camp_func_0029f260", "camp_func_0029ebdc"):
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, cur_pos)
        elif tag in ("camp_func_0029f248", "engine_func_0029eba8"):
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, cur_off)
        elif tag == "script_vm_func_002b91c4":
            calls.append((tag, r0))

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    ret = uc.reg_read(arm.UC_ARM_REG_R0)
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return ret, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    cases = [
        ("up_grid_se1", (10, 20), (100, 200), {100: 6}, 1, 1, (0, 0), 2, 1, 10),
        ("up_list_zero", (10, 20), (100, 200), {100: 2}, 0, 1, (0, 0), 0, 0, 10),
        ("dn_grid_ok_se1", (10, 20), (100, 200), {101: 6}, 1, 1, (0, 0), 2, 1, 10),
        ("dn_list_oob", (10, 20), (100, 200), {101: 2}, 0, 1, (0, 0), 8, 1, 10),
        ("idle_all_zero", (10, 20), (100, 200), {}, 0, 1, (0, 0), 0, 0, 10),
        ("drag_grid_in", (10, 20), (100, 200), {102: 1}, 1, 1, (55, 50), 2, 1, 10),
        ("drag_grid_oob", (10, 20), (100, 200), {102: 1}, 1, 1, (150, 50), 2, 1, 10),
        ("drag_list_diff_se1", (10, 20), (100, 200), {102: 1}, 0, 1, (50, 120), 1, 1, 10),
        ("drag_list_same_se1", (10, 20), (100, 200), {102: 1}, 0, 1, (50, 80), 2, 1, 10),
    ]

    for name, *args in cases:
        o_ret, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, *args)
        c_ret, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, *args)
        if o_ret != c_ret:
            print(f"FAIL {name}: ret orig={o_ret} cand={c_ret}")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref = run_one(orig_code, FUNC_ADDR, None, *cases[0][1:])[:2]
    mutants = [
        ("mut_idle", cases[4][1:]),
        ("mut_up_list", ((10, 20), (100, 200), {100: 6}, 0, 1, (0, 0), 2, 1, 10)),
        ("mut_no_se", ((10, 20), (100, 200), {100: 6}, 1, 0, (0, 0), 2, 1, 10)),
        ("mut_dn_grid", cases[2][1:]),
        ("mut_drag", cases[5][1:]),
    ]
    detected = 0
    for mname, margs in mutants:
        cur = run_one(cand_code, 0x00180000, cand_relocs, *margs)[:2]
        if cur != ref:
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: camp_func_0026adcc (0x0026adcc) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
