#!/usr/bin/env python3
"""Differential test for ui_func_002d81d0 (0x002d81d0) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_002d81d0"

FUNC_ADDR = 0x002D81D0
FUNC_SIZE = 596

STUBS = {
    0x002861F8: "Task_func_002861f8",
    0x002C4B30: "engine_func_002c4b30",
    0x002BCF58: "ui_func_002bcf58",
    0x00193B64: "battle_func_00193b64",
}

CFG_ADDR = 0x20000000
ARG1_ADDR = 0x20001000
ARG2_ADDR = 0x20002000
TASK_ADDR = 0x20003000
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
            if name == "ui_func_002d81d0":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol ui_func_002d81d0 not found")

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
    cfg_w0: int,
    cfg_b11: int,
    arg3_flag: int,
    alloc_ok: bool,
) -> tuple[int, bytes, list[tuple], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(0x20000000, 0x00010000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    cpacr = uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

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

    cfg = bytearray(0x20)
    struct.pack_into("<I", cfg, 0, cfg_w0)
    cfg[0x11] = cfg_b11
    uc.mem_write(CFG_ADDR, bytes(cfg))

    uc.mem_write(ARG1_ADDR, bytes((i & 0xFF) for i in range(0x134)))
    uc.mem_write(ARG2_ADDR, bytes(((i + 0x40) & 0xFF) for i in range(0xB0)))
    uc.mem_write(TASK_ADDR, b"\x5A" * 0x400)

    uc.reg_write(arm.UC_ARM_REG_R0, 0x12345678)
    uc.reg_write(arm.UC_ARM_REG_R1, ARG1_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R2, ARG2_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R3, arg3_flag)
    uc.mem_write(STACK_INIT, struct.pack("<IIIIIII", CFG_ADDR, 0x3F400000, 0x40000000, 0xAB, 0, 0x1234, 0x41200000))
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)
    uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)
    uc.reg_write(arm.UC_ARM_REG_D9, 0x99AABBCCDDEEFF00)

    calls: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        tag = STUBS.get(address)
        if tag is None:
            return
        r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(arm.UC_ARM_REG_R3)
        if tag == "Task_func_002861f8":
            sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
            s = struct.unpack_from("<5I", uc_inst.mem_read(sp, 20))
            calls.append((tag, r0, r1, r2, r3, *s))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, TASK_ADDR if alloc_ok else 0)
        elif tag == "engine_func_002c4b30":
            calls.append((tag, r0, r1))
            uc_inst.mem_write(r0, b"\x00" * r1)
        elif tag == "ui_func_002bcf58":
            calls.append((tag, r0, r1, r2))
            uc_inst.mem_write(r0, bytes(uc_inst.mem_read(r1, r2)))
        elif tag == "battle_func_00193b64":
            calls.append((tag, r0))

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    ret = uc.reg_read(arm.UC_ARM_REG_R0)
    out_task = bytes(uc.mem_read(TASK_ADDR, 0x400))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "d8": uc.reg_read(arm.UC_ARM_REG_D8),
        "d9": uc.reg_read(arm.UC_ARM_REG_D9),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return ret, out_task, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    cases = [
        ("b11_0_flag1_bit0", 0, 0, 1, True),
        ("b11_0_flag0_bit2", 2, 0, 0, True),
        ("b11_1_flag1_bit0", 0, 1, 1, True),
        ("b11_1_flag0_bit2", 2, 1, 0, True),
        ("b11_3_flag1_bit0", 0, 3, 1, True),
        ("b11_3_flag0_bit2", 2, 3, 0, True),
        ("b11_0_alloc_fail", 0, 0, 1, False),
    ]

    for name, *args in cases:
        o_ret, o_tsk, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, *args)
        c_ret, c_tsk, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, *args)
        if o_ret != c_ret or o_tsk != c_tsk:
            print(f"FAIL {name}: ret/task mismatch orig=0x{o_ret:08x} cand=0x{c_ret:08x}")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref = run_one(orig_code, FUNC_ADDR, None, *cases[0][1:])[:3]
    mutants = [
        ("mut_bit2", (2, 0, 1, True)),
        ("mut_b11_1", (0, 1, 1, True)),
        ("mut_b11_3", (0, 3, 1, True)),
        ("mut_flag0", (0, 0, 0, True)),
        ("mut_alloc_fail", (0, 0, 1, False)),
    ]
    detected = 0
    for mname, margs in mutants:
        cur = run_one(cand_code, 0x00180000, cand_relocs, *margs)[:3]
        if cur != ref:
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: ui_func_002d81d0 (0x002d81d0) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
