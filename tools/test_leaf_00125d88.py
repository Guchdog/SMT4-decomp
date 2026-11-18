#!/usr/bin/env python3
"""Differential test for ui_func_00125d88 (0x00125d88) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_00125d88"

FUNC_ADDR = 0x00125D88
FUNC_SIZE = 500

STUBS = {
    0x002C5F7C: "ui_func_002c5f7c",
    0x002BF710: "ui_func_002bf710",
    0x002BEF14: "script_vm_func_002bef14",
    0x002BF460: "ui_func_002bf460",
    0x002C583C: "engine_func_002c583c",
    0x002BE77C: "ui_func_002be77c",
    0x002AEFC8: "engine_func_002aefc8",
}
CB_STUB = 0x003F0200

ADDR_GLOBAL_A = 0x0044E2E8
ADDR_GLOBAL_B = 0x0044EA00
OBJ_A = 0x20000000
OBJ_B = 0x20001000
RODATA_BASE = 0x18000000
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


def _layout_rodata(obj_file: Path) -> tuple[bytes, dict[int, int]]:
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    raw_secs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = raw_secs[e_shstrndx][4]
    names = [data[shstr_off + s[0] : data.index(b"\x00", shstr_off + s[0])].decode("ascii", errors="replace") for s in raw_secs]

    image = bytearray()
    sec_addr: dict[int, int] = {}
    for i, s in enumerate(raw_secs):
        if s[1] == 1 and (s[2] & 2) and not names[i].startswith(".text"):
            align = max(s[8], 1)
            while len(image) % align:
                image.append(0)
            sec_addr[i] = RODATA_BASE + len(image)
            image.extend(data[s[4] : s[4] + s[5]])

    for i, s in enumerate(raw_secs):
        if s[1] == 9 and s[7] in sec_addr:
            target_off = sec_addr[s[7]] - RODATA_BASE
            symtab = raw_secs[s[6]]
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if r_type == 2:
                    st_shndx = struct.unpack_from("<H", data, symtab[4] + sym_idx * 16 + 14)[0]
                    if st_shndx in sec_addr:
                        val = struct.unpack_from("<I", image, target_off + r_off)[0]
                        struct.pack_into("<I", image, target_off + r_off, sec_addr[st_shndx] + val)

    return bytes(image), sec_addr


def compile_candidate() -> tuple[bytes, bytes, list[tuple[str, int]]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_path = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_path)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed:\n{res.stderr}\n{res.stdout}")

    rodata, sec_addr = _layout_rodata(obj_path)
    data = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    secs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = secs[e_shstrndx][4]
    sec_names = [data[shstr_off + s[0] : data.index(b"\x00", shstr_off + s[0])].decode("ascii", errors="replace") for s in secs]
    tidx = sec_names.index(".text")
    text_data = bytearray(data[secs[tidx][4] : secs[tidx][4] + secs[tidx][5]])

    symtab = next(s for s in secs if s[1] == 2)
    strtab_off = secs[symtab[6]][4]
    fn_off = fn_size = None
    for idx in range(symtab[5] // 16):
        st_name, st_value, st_size, _st_info, _st_other, st_shndx = struct.unpack_from("<IIIbbH", data, symtab[4] + idx * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == "ui_func_00125d88":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol ui_func_00125d88 not found")

    relocs: list[tuple[str, int]] = []
    for s in secs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if not (fn_off <= r_off < fn_off + fn_size):
                    continue
                if r_type in (28, 29):
                    st_name = struct.unpack_from("<I", data, symtab[4] + sym_idx * 16)[0]
                    sname = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
                    relocs.append((sname, r_off - fn_off))
                elif r_type == 2:
                    st_value, _, _, _, st_shndx = struct.unpack_from("<IIbbH", data, symtab[4] + sym_idx * 16 + 4)
                    if st_shndx in sec_addr:
                        addend = struct.unpack_from("<I", text_data, r_off)[0]
                        struct.pack_into("<I", text_data, r_off, sec_addr[st_shndx] + st_value + addend)

    return bytes(text_data[fn_off : fn_off + fn_size]), rodata, relocs


def patch_bl(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    insn = 0xEB000000 | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def read_cstr(uc: unicorn.Uc, ptr: int, max_len: int = 32) -> bytes:
    raw = bytes(uc.mem_read(ptr, max_len))
    nul = raw.find(b"\x00")
    return raw[:nul] if nul >= 0 else raw


def run_one(
    code_bytes: bytes,
    base_addr: int,
    cand_rodata: bytes | None,
    relocs: list[tuple[str, int]] | None,
    state_flag: int,
    stack_top_val: int,
    new_val: int,
    dirty_byte: int,
    c583c_ret: int,
) -> tuple[int, bytes, list[tuple], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(RODATA_BASE, 0x00100000)
    uc.mem_map(0x20000000, 0x00010000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    cpacr = uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    if cand_rodata is not None:
        uc.mem_write(RODATA_BASE, cand_rodata)

    buf = bytearray(code_bytes)
    if relocs is not None:
        name_to_addr = {v: k for k, v in STUBS.items()}
        for sym_name, off in relocs:
            target = name_to_addr.get(sym_name)
            if target is None:
                raise RuntimeError(f"unexpected relocation: {sym_name}")
            patch_bl(buf, off, base_addr + off, target)

    uc.mem_write(base_addr, bytes(buf))
    for addr in [*STUBS.keys(), CB_STUB]:
        uc.mem_write(addr, make_stub_bx_lr())

    uc.mem_write(ADDR_GLOBAL_A, struct.pack("<I", OBJ_A))
    uc.mem_write(ADDR_GLOBAL_B, struct.pack("<I", OBJ_B))

    obj_a = bytearray(0x20)
    struct.pack_into("<I", obj_a, 8, state_flag)
    uc.mem_write(OBJ_A, bytes(obj_a))

    blk_b = bytearray(0x20)
    struct.pack_into("<I", blk_b, 0x00, 1)  # stack index = 1
    struct.pack_into("<I", blk_b, 0x0C, stack_top_val)  # [blk_b + 8 + 1*4]
    blk_b[0x18] = dirty_byte
    struct.pack_into("<I", blk_b, 0x1C, CB_STUB)
    uc.mem_write(OBJ_B + 0x124C, bytes(blk_b))

    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)
    uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)
    uc.reg_write(arm.UC_ARM_REG_D9, 0x99AABBCCDDEEFF00)

    calls: list[tuple] = []
    all_hooks = {**STUBS, CB_STUB: "cb"}

    def hook_code(uc_inst, address, size, user_data):
        tag = all_hooks.get(address)
        if tag is None:
            return
        if tag == "ui_func_002c5f7c":
            calls.append((tag, uc_inst.reg_read(arm.UC_ARM_REG_R0), uc_inst.reg_read(arm.UC_ARM_REG_R1)))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, new_val)
        elif tag == "cb":
            calls.append((tag, uc_inst.reg_read(arm.UC_ARM_REG_R0)))
        elif tag == "ui_func_002bf710":
            calls.append((tag, uc_inst.reg_read(arm.UC_ARM_REG_S0)))
        elif tag == "script_vm_func_002bef14":
            calls.append((tag,))
        elif tag == "ui_func_002bf460":
            sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
            s0, s1 = struct.unpack_from("<II", uc_inst.mem_read(sp, 8))
            calls.append((
                tag,
                uc_inst.reg_read(arm.UC_ARM_REG_R0),
                uc_inst.reg_read(arm.UC_ARM_REG_R1),
                uc_inst.reg_read(arm.UC_ARM_REG_R2),
                uc_inst.reg_read(arm.UC_ARM_REG_R3),
                s0,
                s1,
            ))
        elif tag == "engine_func_002c583c":
            calls.append((tag, uc_inst.reg_read(arm.UC_ARM_REG_R0)))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, c583c_ret)
        elif tag == "ui_func_002be77c":
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            calls.append((
                tag,
                uc_inst.reg_read(arm.UC_ARM_REG_R0),
                uc_inst.reg_read(arm.UC_ARM_REG_R1),
                read_cstr(uc_inst, r2),
                uc_inst.reg_read(arm.UC_ARM_REG_S0),
                uc_inst.reg_read(arm.UC_ARM_REG_S1),
                uc_inst.reg_read(arm.UC_ARM_REG_S2),
                uc_inst.reg_read(arm.UC_ARM_REG_S3),
                uc_inst.reg_read(arm.UC_ARM_REG_S4),
            ))
        elif tag == "engine_func_002aefc8":
            calls.append((
                tag,
                uc_inst.reg_read(arm.UC_ARM_REG_R0),
                uc_inst.reg_read(arm.UC_ARM_REG_R1),
                uc_inst.reg_read(arm.UC_ARM_REG_S0),
                uc_inst.reg_read(arm.UC_ARM_REG_S1),
            ))

    for addr in all_hooks:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    ret = uc.reg_read(arm.UC_ARM_REG_R0)
    out_blk = bytes(uc.mem_read(OBJ_B + 0x124C, 0x20))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "d8": uc.reg_read(arm.UC_ARM_REG_D8),
        "d9": uc.reg_read(arm.UC_ARM_REG_D9),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return ret, out_blk, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_rodata, cand_relocs = compile_candidate()

    cases = [
        ("state_not_1", 0, 10, 20, 0, 0),
        ("state_1_diff_vals_flag0", 1, 10, 20, 0, 0),
        ("state_1_same_vals_dirty0_flag1", 1, 10, 10, 0, 1),
        ("state_1_same_vals_dirty1_flag1", 1, 10, 10, 1, 1),
    ]

    for name, st, top_v, new_v, dirty, flag in cases:
        o_ret, o_blk, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, None, st, top_v, new_v, dirty, flag)
        c_ret, c_blk, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_rodata, cand_relocs, st, top_v, new_v, dirty, flag)
        if o_ret != c_ret or o_blk != c_blk:
            print(f"FAIL {name}: ret/blk mismatch")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref_ret, ref_blk, ref_calls, _ = run_one(orig_code, FUNC_ADDR, None, None, 1, 10, 20, 0, 0)
    mutants = [
        ("mut_state_0", 0, 10, 20, 0, 0),
        ("mut_same_val", 1, 10, 10, 0, 0),
        ("mut_new_val_30", 1, 10, 30, 0, 0),
        ("mut_dirty_1_same", 1, 10, 10, 1, 0),
        ("mut_flag_1", 1, 10, 20, 0, 1),
    ]
    detected = 0
    for mname, st, top_v, new_v, dirty, flag in mutants:
        m_ret, m_blk, m_calls, _ = run_one(cand_code, 0x00180000, cand_rodata, cand_relocs, st, top_v, new_v, dirty, flag)
        if (m_ret, m_blk, m_calls) != (ref_ret, ref_blk, ref_calls):
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: ui_func_00125d88 (0x00125d88) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
