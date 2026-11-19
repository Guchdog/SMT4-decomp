#!/usr/bin/env python3
"""Differential test for engine_func_002dfad4 (0x002dfad4) with Unicorn ARM."""

from __future__ import annotations

import math
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
OUT_DIR = ROOT / "build" / "test_leaf_002dfad4"

FUNC_ADDR = 0x002DFAD4
FUNC_SIZE = 544

STUBS = {
    0x002C0BCC: "engine_func_002c0bcc",
    0x0028277C: "script_vm_func_0028277c",
    0x00282600: "script_vm_func_00282600",
    0x0025B6E8: "engine_func_0025b6e8",
    0x00287E4C: "script_vm_func_00287e4c",
}

ADDR_STATE_PTR = 0x00447600
ADDR_CAM_PTR = 0x004474F4
ADDR_TGT_PTR = 0x00447E88
ADDR_FLAG_BASE = 0x0049FB1C

STATE_BASE = 0x20000000
CAM_BASE = 0x20004000
TGT_BASE = 0x20004100
OUT_ADDR = 0x20005000
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
            if name == "engine_func_002dfad4":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol engine_func_002dfad4 not found")

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


def u32_to_f32(u: int) -> float:
    return struct.unpack("<f", struct.pack("<I", u))[0]


def f32_to_u32(f: float) -> int:
    return struct.unpack("<I", struct.pack("<f", f))[0]


def run_one(
    code_bytes: bytes,
    base_addr: int,
    relocs: list[tuple[str, int]] | None,
    flag: int,
    init_cnt: int,
    hit_attempt: int,
) -> tuple[int, bytes, int, list[tuple], dict[str, int]]:
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

    uc.mem_write(ADDR_STATE_PTR, struct.pack("<I", STATE_BASE))
    uc.mem_write(ADDR_CAM_PTR, struct.pack("<I", CAM_BASE))
    uc.mem_write(ADDR_TGT_PTR, struct.pack("<I", TGT_BASE))
    uc.mem_write(ADDR_FLAG_BASE + 0x44, struct.pack("<H", flag))

    uc.mem_write(STATE_BASE + 0x3044, struct.pack("<i", init_cnt))
    uc.mem_write(CAM_BASE + 0x18, struct.pack("<f", 30.0))
    uc.mem_write(TGT_BASE + 0x1C, struct.pack("<fff", 100.0, 200.0, 300.0))
    uc.mem_write(OUT_ADDR, b"\x5A" * 0x40)

    uc.reg_write(arm.UC_ARM_REG_R0, OUT_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)
    for d in range(8, 14):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_D{d}"), 0x1111222233334444 + d)

    calls: list[tuple] = []
    los_idx = 0

    def hook_code(uc_inst, address, size, user_data):
        nonlocal los_idx
        tag = STUBS.get(address)
        if tag is None:
            return
        if tag == "engine_func_002c0bcc":
            m = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            calls.append((tag, m))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, 17)
        elif tag == "script_vm_func_0028277c":
            rad = u32_to_f32(uc_inst.reg_read(arm.UC_ARM_REG_S0))
            calls.append((tag, round(rad, 5)))
            uc_inst.reg_write(arm.UC_ARM_REG_S0, f32_to_u32(math.cos(rad)))
        elif tag == "script_vm_func_00282600":
            rad = u32_to_f32(uc_inst.reg_read(arm.UC_ARM_REG_S0))
            calls.append((tag, round(rad, 5)))
            uc_inst.reg_write(arm.UC_ARM_REG_S0, f32_to_u32(math.sin(rad)))
        elif tag == "engine_func_0025b6e8":
            p0 = struct.unpack_from("<fff", uc_inst.mem_read(uc_inst.reg_read(arm.UC_ARM_REG_R0), 12))
            p1 = struct.unpack_from("<fff", uc_inst.mem_read(uc_inst.reg_read(arm.UC_ARM_REG_R1), 12))
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            calls.append((tag, tuple(round(x, 3) for x in p0), tuple(round(x, 3) for x in p1), r2))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, 0xFFFFFFFF if los_idx == hit_attempt else 0)
            los_idx += 1
        elif tag == "script_vm_func_00287e4c":
            s = [round(u32_to_f32(uc_inst.reg_read(getattr(arm, f"UC_ARM_REG_S{i}"))), 3) for i in range(6)]
            calls.append((tag, *s))
            uc_inst.reg_write(arm.UC_ARM_REG_S0, f32_to_u32(42.5))

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=100000)

    ret = uc.reg_read(arm.UC_ARM_REG_R0)
    out_mem = bytes(uc.mem_read(OUT_ADDR, 0x40))
    final_cnt = struct.unpack_from("<i", uc.mem_read(STATE_BASE + 0x3044, 4))[0]
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{f"d{d}": uc.reg_read(getattr(arm, f"UC_ARM_REG_D{d}")) for d in range(8, 14)},
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return ret, out_mem, final_cnt, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    cases = [
        ("flag0_cnt0_hit0", 0, 0, 0),
        ("flag0_cnt11_hit3", 0, 11, 3),
        ("flag1_cnt0_hit1", 1, 0, 1),
        ("flag1_cnt11_miss_all", 1, 11, -1),
    ]

    for name, *args in cases:
        o_ret, o_out, o_cnt, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, *args)
        c_ret, c_out, c_cnt, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, *args)
        if o_ret != c_ret or o_out != c_out or o_cnt != c_cnt:
            print(f"FAIL {name}: ret/out/cnt mismatch orig=({o_ret},{o_cnt}) cand=({c_ret},{c_cnt})")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref = run_one(orig_code, FUNC_ADDR, None, 0, 0, 0)[:4]
    mutants = [
        ("mut_flag1", (1, 0, 0)),
        ("mut_cnt1", (0, 1, 0)),
        ("mut_cnt13", (0, 13, 0)),
        ("mut_hit1", (0, 0, 1)),
        ("mut_miss", (0, 0, -1)),
    ]
    detected = 0
    for mname, margs in mutants:
        cur = run_one(cand_code, 0x00180000, cand_relocs, *margs)[:4]
        if cur != ref:
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: engine_func_002dfad4 (0x002dfad4) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
