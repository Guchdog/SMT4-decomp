#!/usr/bin/env python3
"""Differential test for engine_func_0038d59c (0x0038d59c) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0038d59c"

FUNC_ADDR = 0x0038D59C
FUNC_SIZE = 500

STUBS = {
    0x002BB09C: "engine_func_002bb09c",
    0x002BAD80: "engine_func_002bad80",
    0x0038B600: "func_0038b600",
    0x0039444C: "engine_func_0039444c",
    0x0023A24C: "func_0023a24c",
    0x0038B470: "engine_func_0038b470",
    0x002A1578: "engine_func_002a1578",
    0x002B49F4: "func_002b49f4",
    0x0038B664: "nn_sdk_func_0038b664",
}

ADDR_MGR_PTR = 0x00432FC8
MGR_ADDR = 0x20000000
OUT_ADDR = 0x20001000
CTX_ADDR = 0x20002000
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
            if name == "engine_func_0038d59c":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol engine_func_0038d59c not found")

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
    state: int,
    r39444c: int,
    err_out: int,
    flag_out: int,
    r23a24c: int,
    r2a1578: int,
    r38b664: int,
    r38b600: int,
) -> tuple[bytes, bytes, list[tuple], dict[str, int]]:
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

    uc.mem_write(ADDR_MGR_PTR, struct.pack("<I", MGR_ADDR))
    uc.mem_write(OUT_ADDR, b"\x5A" * 0x20)
    ctx = bytearray(0x40)
    for off in range(0, 0x40, 4):
        struct.pack_into("<I", ctx, off, 0xA0000000 + off)
    struct.pack_into("<I", ctx, 4, state)
    uc.mem_write(CTX_ADDR, bytes(ctx))

    uc.reg_write(arm.UC_ARM_REG_R0, OUT_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, CTX_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    calls: list[tuple] = []
    ts_seq = 0

    def hook_code(uc_inst, address, size, user_data):
        nonlocal ts_seq
        tag = STUBS.get(address)
        if tag is None:
            return
        r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
        if tag == "engine_func_002bb09c":
            calls.append((tag, r0))
            # Returns r0
        elif tag == "engine_func_002bad80":
            ts_seq += 1
            calls.append((tag, r1))
            uc_inst.mem_write(r0, struct.pack("<II", 0x11110000 + ts_seq, 0x22220000 + ts_seq))
        elif tag == "engine_func_0039444c":
            init_err = struct.unpack_from("<I", uc_inst.mem_read(r1, 4))[0]
            calls.append((tag, r0, init_err))
            uc_inst.mem_write(r1, struct.pack("<I", err_out))
            uc_inst.mem_write(r2, struct.pack("<I", flag_out))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, r39444c)
        elif tag == "func_0023a24c":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, r23a24c)
        elif tag == "engine_func_0038b470":
            calls.append((tag, r1))
            uc_inst.mem_write(r0, struct.pack("<II", 0x33334444, 0x55556666))
        elif tag == "engine_func_002a1578":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, r2a1578)
        elif tag == "func_002b49f4":
            calls.append((tag, r0))
        elif tag == "nn_sdk_func_0038b664":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, r38b664)
        elif tag == "func_0038b600":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, r38b600)

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    out_mem = bytes(uc.mem_read(OUT_ADDR, 0x20))
    ctx_mem = bytes(uc.mem_read(CTX_ADDR, 0x40))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_mem, ctx_mem, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    cases = [
        ("s0_ok_neg_neg", 0, 1, 0, 0, 0x80000000, 0x80000000, 0, 0),
        ("s0_ok_pos_23a24c", 0, 1, 0, 0, 0x00000001, 0x80000000, 0, 0),
        ("s0_ok_pos_2a1578", 0, 1, 0, 0, 0x80000000, 0x00000001, 0, 0),
        ("s0_fail_pos_err", 0, 0, 0x00000001, 0, 0, 0, 0, 0),
        ("s0_fail_neg_flag0", 0, 0, 0x80000001, 0, 0, 0, 0, 0),
        ("s0_fail_neg_flag1", 0, 0, 0x80000001, 1, 0, 0, 0, 0),
        ("s1_nonzero", 1, 0, 0, 0, 0, 0, 1, 0),
        ("s1_zero", 1, 0, 0, 0, 0, 0, 0, 0),
        ("s2_nonzero", 2, 0, 0, 0, 0, 0, 0, 1),
        ("s2_zero", 2, 0, 0, 0, 0, 0, 0, 0),
        ("s3_default", 3, 0, 0, 0, 0, 0, 0, 0),
    ]

    for name, *args in cases:
        o_out, o_ctx, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, *args)
        c_out, c_ctx, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, *args)
        if o_out != c_out or o_ctx != c_ctx:
            print(f"FAIL {name}: mem mismatch")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref_out, ref_ctx, ref_calls, _ = run_one(orig_code, FUNC_ADDR, None, *cases[0][1:])
    mutants = [
        ("mut_s0_pos_23a24c", cases[1][1:]),
        ("mut_s0_pos_2a1578", cases[2][1:]),
        ("mut_s0_fail_flag1", cases[5][1:]),
        ("mut_s1_zero", cases[7][1:]),
        ("mut_s2_nonzero", cases[8][1:]),
    ]
    detected = 0
    for mname, margs in mutants:
        m_out, m_ctx, m_calls, _ = run_one(cand_code, 0x00180000, cand_relocs, *margs)
        if (m_out, m_ctx, m_calls) != (ref_out, ref_ctx, ref_calls):
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: engine_func_0038d59c (0x0038d59c) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
