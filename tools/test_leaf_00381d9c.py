#!/usr/bin/env python3
"""Differential test for script_vm_func_00381d9c (0x00381d9c) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_00381d9c"

FUNC_ADDR = 0x00381D9C
FUNC_SIZE = 492

STUBS = {
    0x003854D8: "script_vm_func_003854d8",
    0x002C4B30: "engine_func_002c4b30",
    0x00297704: "script_vm_func_00297704",
    0x002C3344: "camp_func_002c3344",
    0x002C32F8: "camp_func_002c32f8",
    0x00385CBC: "script_vm_func_00385cbc",
    0x00385CFC: "script_vm_func_00385cfc",
    0x00385D04: "script_vm_func_00385d04",
    0x002C4E28: "AsdTMTexTable_func_002c4e28",
    0x002A6214: "camp_func_002a6214",
    0x002BDA1C: "AsdText_func_002bda1c",
    0x002639F4: "PlaceWin_Init",
    0x002A7540: "ui_func_002a7540",
    0x001A15A0: "script_vm_func_001a15a0",
    0x002B6700: "script_vm_func_002b6700",
    0x0029923C: "script_vm_func_0029923c",
    0x0028F15C: "script_vm_func_0028f15c",
}

ARITIES = {
    "script_vm_func_003854d8": 1,
    "engine_func_002c4b30": 2,
    "script_vm_func_00297704": 3,
    "camp_func_002c3344": 1,
    "camp_func_002c32f8": 11,
    "script_vm_func_00385cbc": 1,
    "script_vm_func_00385cfc": 1,
    "script_vm_func_00385d04": 1,
    "AsdTMTexTable_func_002c4e28": 1,
    "camp_func_002a6214": 2,
    "AsdText_func_002bda1c": 1,
    "PlaceWin_Init": 0,
    "ui_func_002a7540": 1,
    "script_vm_func_001a15a0": 1,
    "script_vm_func_002b6700": 1,
    "script_vm_func_0029923c": 2,
    "script_vm_func_0028f15c": 1,
}

RODATA_BASE = 0x18000000
OBJ_ADDR = 0x20000000
NODE_BASE = 0x20002000
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
            if name == "script_vm_func_00381d9c":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol script_vm_func_00381d9c not found")

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


def read_cstr(uc: unicorn.Uc, ptr: int, max_len: int = 64) -> bytes:
    raw = bytes(uc.mem_read(ptr, max_len))
    nul = raw.find(b"\x00")
    return raw[:nul] if nul >= 0 else raw


def run_one(
    code_bytes: bytes,
    base_addr: int,
    cand_rodata: bytes | None,
    relocs: list[tuple[str, int]] | None,
    node_map: dict[int, tuple[int, int]],
) -> tuple[bytes, list[tuple], dict[str, int]]:
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

    obj = bytearray(0x1000)
    for off in range(0, 0x1000, 4):
        struct.pack_into("<I", obj, off, 0x5A5A5A5A)
    uc.mem_write(OBJ_ADDR, bytes(obj))

    uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    calls: list[tuple] = []
    text_handle_seq = 0x7000

    def hook_code(uc_inst, address, size, user_data):
        nonlocal text_handle_seq
        tag = STUBS.get(address)
        if tag is None:
            return
        argc = ARITIES[tag]
        args = []
        for i in range(min(argc, 4)):
            args.append(uc_inst.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")))
        sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
        for i in range(4, argc):
            val = struct.unpack_from("<I", uc_inst.mem_read(sp + (i - 4) * 4, 4))[0]
            args.append(val)

        if tag == "script_vm_func_00297704":
            # Compare string content in arg0 rather than pointer address
            args[0] = read_cstr(uc_inst, args[0])

        calls.append((tag, *args))

        if tag == "AsdText_func_002bda1c":
            text_handle_seq += 1
            uc_inst.reg_write(arm.UC_ARM_REG_R0, text_handle_seq)
        elif tag == "script_vm_func_002b6700":
            qid = args[0]
            if qid in node_map:
                flag_byte, _ = node_map[qid]
                naddr = NODE_BASE + qid * 0x10
                node = bytearray(0x10)
                node[6] = flag_byte
                uc_inst.mem_write(naddr, bytes(node))
                uc_inst.reg_write(arm.UC_ARM_REG_R0, naddr)
            else:
                uc_inst.reg_write(arm.UC_ARM_REG_R0, 0)
        elif tag == "script_vm_func_0029923c":
            qid = args[0]
            _, ret_val = node_map.get(qid, (0, 0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret_val)

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=100000)

    out_obj = bytes(uc.mem_read(OBJ_ADDR, 0x1000))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_obj, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_rodata, cand_relocs = compile_candidate()

    cases = [
        ("all_null", {}),
        ("mixed_nodes", {350: (0, 0), 351: (1, 0), 399: (0, 1)}),
        ("boundary_349_400_ignored", {349: (0, 0), 400: (0, 0), 375: (0, 0)}),
    ]

    for name, nmap in cases:
        o_obj, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, None, nmap)
        c_obj, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_rodata, cand_relocs, nmap)
        if o_obj != c_obj:
            print(f"FAIL {name}: obj mismatch")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls[:10]}\n  cand={c_calls[:10]}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref_obj, ref_calls, _ = run_one(orig_code, FUNC_ADDR, None, None, cases[1][1])
    mutants = [
        ("mut_empty", {}),
        ("mut_350_flag1", {350: (1, 0), 351: (1, 0), 399: (0, 1)}),
        ("mut_350_unlocked", {350: (0, 1), 351: (1, 0), 399: (0, 1)}),
        ("mut_399_flag1", {350: (0, 0), 351: (1, 0), 399: (1, 1)}),
        ("mut_extra_360", {350: (0, 0), 351: (1, 0), 360: (0, 0), 399: (0, 1)}),
    ]
    detected = 0
    for mname, mnmap in mutants:
        m_obj, m_calls, _ = run_one(cand_code, 0x00180000, cand_rodata, cand_relocs, mnmap)
        if (m_obj, m_calls) != (ref_obj, ref_calls):
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: script_vm_func_00381d9c (0x00381d9c) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
