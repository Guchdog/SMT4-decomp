#!/usr/bin/env python3
"""Differential test for func_0024ecc0 (0x0024ecc0) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0024ecc0"

FUNC_ADDR = 0x0024ECC0
FUNC_SIZE = 532

STUB_F370 = 0x0026F370
STUB_F294 = 0x0026F294

OBJ_ADDR = 0x20000000
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
            if name == "script_vm_func_0024ecc0":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol func_0024ecc0 not found")

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
    show: int,
    w108: int,
    w114: int,
    w28: int,
    b74: int,
    slot_34: tuple[int, int, int],
    f294_mask: int,
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
        for sym_name, off in relocs:
            if "func_0026f370" in sym_name:
                patch_bl(buf, off, base_addr + off, STUB_F370)
            elif "func_0026f294" in sym_name:
                patch_bl(buf, off, base_addr + off, STUB_F294)
            else:
                raise RuntimeError(f"unexpected relocation: {sym_name}")

    uc.mem_write(base_addr, bytes(buf))
    uc.mem_write(STUB_F370, make_stub_bx_lr())
    uc.mem_write(STUB_F294, make_stub_bx_lr())

    obj = bytearray(0x140)
    for i in range(3):
        struct.pack_into("<I", obj, i * 0x14 + 0x20, 10 + i)
        struct.pack_into("<i", obj, i * 0x14 + 0x34, slot_34[i])
        struct.pack_into("<I", obj, i * 0x14 + 0x48, 20 + i)
    struct.pack_into("<I", obj, 0x28, w28)
    obj[0x74] = b74
    struct.pack_into("<I", obj, 0x108, w108)
    struct.pack_into("<I", obj, 0x114, w114)
    uc.mem_write(OBJ_ADDR, bytes(obj))

    uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, show)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)
    uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)

    calls: list[tuple] = []
    f294_idx = 0

    def hook_code(uc_inst, address, size, user_data):
        nonlocal f294_idx
        if address == STUB_F370:
            calls.append((
                "f370",
                uc_inst.reg_read(arm.UC_ARM_REG_R0),
                uc_inst.reg_read(arm.UC_ARM_REG_R1),
                uc_inst.reg_read(arm.UC_ARM_REG_R2),
                uc_inst.reg_read(arm.UC_ARM_REG_S0),
                uc_inst.reg_read(arm.UC_ARM_REG_S1),
            ))
        elif address == STUB_F294:
            sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
            s0, s1 = struct.unpack_from("<II", uc_inst.mem_read(sp, 8))
            calls.append((
                "f294",
                uc_inst.reg_read(arm.UC_ARM_REG_R0),
                uc_inst.reg_read(arm.UC_ARM_REG_R1),
                uc_inst.reg_read(arm.UC_ARM_REG_R2),
                uc_inst.reg_read(arm.UC_ARM_REG_R3),
                s0,
                s1,
            ))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, (f294_mask >> f294_idx) & 1)
            f294_idx += 1

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=STUB_F370, end=STUB_F370)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=STUB_F294, end=STUB_F294)
    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    ret = uc.reg_read(arm.UC_ARM_REG_R0)
    out_obj = bytes(uc.mem_read(OBJ_ADDR, 0x140))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "d8": uc.reg_read(arm.UC_ARM_REG_D8),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return ret, out_obj, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    cases = [
        ("hide_w114_not2", 0, 2, 1, 0x3F800000, 0, (1, 2, 3), 0b010),
        ("hide_w114_is2_b74_1", 0, 2, 2, 0x3F000000, 1, (1, 2, 3), 0b111),
        ("show_w108_0_mixed", 1, 0, 0, 0x3F800000, 0, (0, 2, 3), 0b10),
        ("show_w108_4", 1, 4, 0, 0x3F800000, 0, (0, 3, 4), 0b001),
        ("show_w108_2_done", 1, 2, 0, 0x3F800000, 0, (0, 0, 0), 0),
        ("show_w108_2_not_done", 1, 2, 0, 0x3F7FFFFF, 0, (0, 0, 0), 0),
    ]

    for name, *args in cases:
        o_ret, o_obj, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, *args)
        c_ret, c_obj, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, *args)
        if o_ret != c_ret or o_obj != c_obj:
            print(f"FAIL {name}: ret/obj mismatch orig={o_ret} cand={c_ret}")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref_ret, ref_obj, ref_calls, _ = run_one(orig_code, FUNC_ADDR, None, *cases[2][1:])
    mutants = [
        ("mut_hide", (0, 0, 0, 0x3F800000, 0, (0, 2, 3), 0b10)),
        ("mut_w108_4", cases[3][1:]),
        ("mut_w108_2", cases[4][1:]),
        ("mut_slot_34", (1, 0, 0, 0x3F800000, 0, (0, 3, 2), 0b10)),
        ("mut_f294_mask", (1, 0, 0, 0x3F800000, 0, (0, 2, 3), 0b01)),
    ]
    detected = 0
    for mname, margs in mutants:
        m_ret, m_obj, m_calls, _ = run_one(cand_code, 0x00180000, cand_relocs, *margs)
        if (m_ret, m_obj, m_calls) != (ref_ret, ref_obj, ref_calls):
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: func_0024ecc0 (0x0024ecc0) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
