#!/usr/bin/env python3
"""Differential test for engine_func_001e1d1c (0x001e1d1c) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_001e1d1c"

FUNC_ADDR = 0x001E1D1C
FUNC_SIZE = 500

STUBS = {
    0x002C5978: "engine_func_002c5978",
    0x002BF86C: "engine_func_002bf86c",
    0x002C583C: "engine_func_002c583c",
    0x0025C7D8: "engine_func_0025c7d8",
    0x0020118C: "script_vm_func_0020118c",
    0x002C4C00: "camp_func_002c4c00",
}

ADDR_GLOBAL = 0x0043E0D0
ADDR_PARAMS = 0x004937C4
OBJ_ADDR = 0x20000000
ARG_ADDR = 0x20001000
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
            if name == "engine_func_001e1d1c":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol engine_func_001e1d1c not found")

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
    hi = code[at_off + 3]
    insn = (hi << 24) | (delta & 0x00FFFFFF)
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
    arg_ptr: int,
    w0: int,
    w1: int,
    c583c_ret: int,
) -> tuple[bytes, bytes, list[tuple], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(RODATA_BASE, 0x00100000)
    uc.mem_map(0x20000000, 0x00010000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

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
    for addr in STUBS:
        uc.mem_write(addr, make_stub_bx_lr())

    uc.mem_write(ADDR_GLOBAL, struct.pack("<I", OBJ_ADDR))

    obj = bytearray(0x40)
    for off in range(0, 0x40, 4):
        struct.pack_into("<I", obj, off, 0xA0000000 + off)
    uc.mem_write(OBJ_ADDR, bytes(obj))

    params = bytearray(0x20)
    for off in range(0, 0x20, 4):
        struct.pack_into("<I", params, off, 0xB0000000 + off)
    uc.mem_write(ADDR_PARAMS, bytes(params))

    arg = bytearray(0x20)
    struct.pack_into("<II", arg, 0, w0, w1)
    arg[8:20] = b"EVT_TEST_01\x00"
    uc.mem_write(ARG_ADDR, bytes(arg))

    uc.reg_write(arm.UC_ARM_REG_R0, arg_ptr)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    calls: list[tuple] = []
    task_seq = 0x100

    def hook_code(uc_inst, address, size, user_data):
        nonlocal task_seq
        tag = STUBS.get(address)
        if tag is None:
            return
        if tag == "engine_func_002c5978":
            sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
            s0, s1, s2 = struct.unpack_from("<III", uc_inst.mem_read(sp, 12))
            calls.append((
                tag,
                read_cstr(uc_inst, uc_inst.reg_read(arm.UC_ARM_REG_R0)),
                uc_inst.reg_read(arm.UC_ARM_REG_R1),
                uc_inst.reg_read(arm.UC_ARM_REG_R2),
                uc_inst.reg_read(arm.UC_ARM_REG_R3),
                s0,
                s1,
                s2,
            ))
            task_seq += 1
            uc_inst.reg_write(arm.UC_ARM_REG_R0, task_seq)
        elif tag == "camp_func_002c4c00":
            sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
            s0, s1, s2, s3 = struct.unpack_from("<IIII", uc_inst.mem_read(sp, 16))
            calls.append((
                tag,
                read_cstr(uc_inst, uc_inst.reg_read(arm.UC_ARM_REG_R0)),
                uc_inst.reg_read(arm.UC_ARM_REG_R1),
                uc_inst.reg_read(arm.UC_ARM_REG_R2),
                uc_inst.reg_read(arm.UC_ARM_REG_R3),
                s0,
                s1,
                s2,
                s3,
            ))
        elif tag == "engine_func_002bf86c":
            calls.append((tag, uc_inst.reg_read(arm.UC_ARM_REG_R0), uc_inst.reg_read(arm.UC_ARM_REG_R1)))
        elif tag == "engine_func_002c583c":
            calls.append((tag, uc_inst.reg_read(arm.UC_ARM_REG_R0)))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, c583c_ret)
        elif tag == "engine_func_0025c7d8":
            calls.append((tag, uc_inst.reg_read(arm.UC_ARM_REG_R0)))
        elif tag == "script_vm_func_0020118c":
            calls.append((tag,))

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    out_obj = bytes(uc.mem_read(OBJ_ADDR, 0x40))
    out_params = bytes(uc.mem_read(ADDR_PARAMS, 0x20))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_obj, out_params, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_rodata, cand_relocs = compile_candidate()

    cases = [
        ("arg_nonnull_w1_not_neg1", ARG_ADDR, 11, 22, 0),
        ("arg_nonnull_w1_neg1", ARG_ADDR, 33, 0xFFFFFFFF, 0),
        ("arg_null_flag0", 0, 0, 0, 0),
        ("arg_null_flag1", 0, 0, 0, 1),
    ]

    for name, aptr, w0, w1, flg in cases:
        o_obj, o_par, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, None, aptr, w0, w1, flg)
        c_obj, c_par, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_rodata, cand_relocs, aptr, w0, w1, flg)
        if o_obj != c_obj or o_par != c_par:
            print(f"FAIL {name}: mem mismatch")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref_obj, ref_par, ref_calls, _ = run_one(orig_code, FUNC_ADDR, None, None, ARG_ADDR, 11, 22, 0)
    mutants = [
        ("mut_w0", ARG_ADDR, 99, 22, 0),
        ("mut_w1", ARG_ADDR, 11, 88, 0),
        ("mut_w1_neg1", ARG_ADDR, 11, 0xFFFFFFFF, 0),
        ("mut_null_0", 0, 11, 22, 0),
        ("mut_null_1", 0, 11, 22, 1),
    ]
    detected = 0
    for mname, aptr, w0, w1, flg in mutants:
        m_obj, m_par, m_calls, _ = run_one(cand_code, 0x00180000, cand_rodata, cand_relocs, aptr, w0, w1, flg)
        if (m_obj, m_par, m_calls) != (ref_obj, ref_par, ref_calls):
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: engine_func_001e1d1c (0x001e1d1c) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
