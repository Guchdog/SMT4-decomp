#!/usr/bin/env python3
"""Differential test for func_002f38bc (0x002f38bc) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_002f38bc"

FUNC_ADDR = 0x002F38BC
FUNC_SIZE = 496

STUB_DRAW_LINE = 0x0024742C
ADDR_COUNT = 0x00447A28
ADDR_BASE = 0x004A0FE4

OBJ_POOL = 0x20000000
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
            if name == "func_002f38bc":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol func_002f38bc not found")

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
    count_val: int,
    items: list[tuple[int, int]],
) -> tuple[list[tuple], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(0x20000000, 0x00010000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    # Enable VFP/NEON (CP10/CP11 in CPACR = c1_c0_2)
    cpacr = uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    buf = bytearray(code_bytes)
    if relocs is not None:
        for sym_name, off in relocs:
            if "func_0024742c" in sym_name:
                patch_bl(buf, off, base_addr + off, STUB_DRAW_LINE)
            else:
                raise RuntimeError(f"unexpected relocation: {sym_name}")

    uc.mem_write(base_addr, bytes(buf))
    uc.mem_write(STUB_DRAW_LINE, make_stub_bx_lr())

    uc.mem_write(ADDR_COUNT, struct.pack("<i", count_val))

    for i, (mode, kind) in enumerate(items):
        obj_addr = OBJ_POOL + i * 0x100
        inner_addr = obj_addr + 0x40
        mode_ptr = obj_addr + 0x80
        uc.mem_write(ADDR_BASE + i * 4, struct.pack("<I", obj_addr))
        uc.mem_write(obj_addr + 0x14, struct.pack("<I", inner_addr))
        uc.mem_write(inner_addr + 0x04, struct.pack("<I", kind))
        uc.mem_write(inner_addr + 0x1C, struct.pack("<I", mode_ptr))
        uc.mem_write(mode_ptr, struct.pack("<I", mode))

        box_addr = ADDR_BASE + 0x280 + i * 0x178
        box = bytearray(0x178)
        for off in range(0, 0x80, 4):
            val = float((i + 1) * 1.25 + (off // 4) * 0.5)
            struct.pack_into("<f", box, off, val)
        uc.mem_write(box_addr, bytes(box))

    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)
    uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)

    calls: list[tuple] = []
    sregs = [arm.UC_ARM_REG_S0, arm.UC_ARM_REG_S1, arm.UC_ARM_REG_S2, arm.UC_ARM_REG_S3, arm.UC_ARM_REG_S4, arm.UC_ARM_REG_S5]

    def hook_code(uc_inst, address, size, user_data):
        if address == STUB_DRAW_LINE:
            color = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            floats = tuple(uc_inst.reg_read(r) for r in sregs)
            calls.append((color, *floats))

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=STUB_DRAW_LINE, end=STUB_DRAW_LINE)
    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "d8": uc.reg_read(arm.UC_ARM_REG_D8),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    cases = [
        ("negative_count", -1, [(1, 0x27)]),
        ("zero_count", 0, []),
        ("all_modes", 5, [(0, 0), (1, 0x27), (1, 0x10), (2, 0), (3, 0)]),
    ]

    for name, cnt, items in cases:
        o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, cnt, items)
        c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, cnt, items)
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch orig={o_regs} cand={c_regs}")
            return 1

    # 5 negative / mutation controls
    ref_calls, _ = run_one(orig_code, FUNC_ADDR, None, 5, cases[2][2])
    mutants = [
        ("mut_count_3", 3, cases[2][2]),
        ("mut_kind_not_27", 5, [(0, 0), (1, 0x26), (1, 0x10), (2, 0), (3, 0)]),
        ("mut_mode_0_to_2", 5, [(2, 0), (1, 0x27), (1, 0x10), (2, 0), (3, 0)]),
        ("mut_mode_2_to_0", 5, [(0, 0), (1, 0x27), (1, 0x10), (0, 0), (3, 0)]),
        ("mut_mode_3_to_1", 5, [(0, 0), (1, 0x27), (1, 0x10), (2, 0), (1, 0)]),
    ]
    detected = 0
    for mname, mcnt, mitems in mutants:
        m_calls, _ = run_one(cand_code, 0x00180000, cand_relocs, mcnt, mitems)
        if m_calls != ref_calls:
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: func_002f38bc (0x002f38bc) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
