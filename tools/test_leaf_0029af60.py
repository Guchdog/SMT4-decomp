#!/usr/bin/env python3
"""Differential Unicorn verification for script_vm_func_0029af60 (0x0029af60)."""

from __future__ import annotations

import struct
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM, Uc
from unicorn.arm_const import (
    UC_ARM_REG_CPSR,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_SP,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.build_check import compile_tu_armv6k

TU_REL = "src/engine/leaf_batch46_a.cpp"
FUNC_NAME = "script_vm_func_0029af60"
ORIG_ADDR = 0x0029AF60
ORIG_SIZE = 384

CALLEES_ORIG = {
    "script_vm_func_002990bc": 0x002990BC,
    "script_vm_func_00299224": 0x00299224,
    "script_vm_func_00299084": 0x00299084,
    "script_vm_func_002b6700": 0x002B6700,
    "func_002be4dc": 0x002BE4DC,
    "script_vm_func_002aec80": 0x002AEC80,
    "script_vm_func_002bef14": 0x002BEF14,
}

ORIG_BYTES = bytes.fromhex(
    "f04f2de90cd04de20180a0e10260a0e1"
    "0370a0e10090a0e10040a0e34ef8ffeb"
    "0050a0e10900a0e1a5f8ffeb000050e3"
    "0400000a000055e310419f1510419f05"
    "3700000a340000ea0900a0e134f8ffeb"
    "00a19fe5000050e301b04ae20300000a"
    "000055e32800000a0a40a0e12a0000ea"
    "0900a0e1c96d00eb0600d0e50b0050e3"
    "00f19f37220000ea14b0290028b02900"
    "50b0290050b029003cb029003cb02900"
    "28b0290074b0290064b0290064b02900"
    "a8b02900000055e39c409f159c409f05"
    "1700000a140000ea000055e390409f15"
    "90409f051200000a0f0000ea000055e3"
    "84409f1584409f050d00000a0a0000ea"
    "000055e378409f1578409f050800000a"
    "050000ea000055e3d6ffff1a0b40a0e1"
    "030000ea000055e30100000a58009fe5"
    "158d00eb0830a0e10420a0e11310a0e3"
    "0200a0e3f060cde1f84e00eb0cd08de2"
    "f04fbde89a8f00ea0cd08de2f08fbde8"
    "0f040000080400001b0400000a040000"
    "030400000b040000040400000c040000"
    "050400000d04000006040000ff0098f4"
)
assert len(ORIG_BYTES) == ORIG_SIZE

CODE_BASE = 0x00100000
CODE_SIZE = 0x00500000
CAND_BASE = 0x00600000
CAND_SIZE = 0x00100000
DATA_BASE = 0x00700000
DATA_SIZE = 0x00100000
STACK_BASE = 0x00900000
STACK_SIZE = 0x00020000
INFO_BASE = 0x00720000
SENTINEL = 0x006F0000


def parse_elf32(data: bytes):
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    shdrs = [
        struct.unpack_from("<10I", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]

    def read_str(strtab_idx: int, off: int) -> str:
        s_off = shdrs[strtab_idx][4]
        end = data.index(b"\x00", s_off + off)
        return data[s_off + off : end].decode("ascii", "replace")

    sections = {}
    for i, sh in enumerate(shdrs):
        name = read_str(e_shstrndx, sh[0])
        sections[name] = (i, sh, data[sh[4] : sh[4] + sh[5]])

    _, sym_sh, sym_bytes = sections[".symtab"]
    strtab_idx = sym_sh[6]
    syms = []
    for off in range(0, len(sym_bytes), 16):
        st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack_from(
            "<IIIBBH", sym_bytes, off
        )
        syms.append((read_str(strtab_idx, st_name), st_value, st_size, st_info, st_shndx))

    return shdrs, sections, syms


def load_candidate_func(obj_path: Path, func_name: str):
    data = obj_path.read_bytes()
    shdrs, sections, syms = parse_elf32(data)
    target = None
    for s in syms:
        if s[0] == func_name:
            target = s
            break
    assert target is not None, f"missing symbol {func_name}"
    _, st_value, st_size, _, st_shndx = target
    assert st_size > 0, f"{func_name} has zero size"

    sec_addrs: Dict[int, int] = {}
    cursor = CAND_BASE
    rel_entries: List[Tuple[int, int, int, int]] = []
    sec_by_idx: Dict[int, Tuple[str, Tuple[int, ...], bytes]] = {}
    for name, (idx, sh, sbytes) in sections.items():
        sec_by_idx[idx] = (name, sh, sbytes)

    for idx, (name, sh, sbytes) in sec_by_idx.items():
        if sh[2] & 0x2:
            align = max(4, sh[8])
            cursor = (cursor + align - 1) & ~(align - 1)
            sec_addrs[idx] = cursor
            cursor += max(4, len(sbytes))

    for name, (idx, sh, sbytes) in sections.items():
        if sh[1] == 9:
            target_sec = sh[7]
            if target_sec not in sec_addrs:
                continue
            for off in range(0, len(sbytes), 8):
                r_offset, r_info = struct.unpack_from("<II", sbytes, off)
                r_type = r_info & 0xFF
                r_sym = r_info >> 8
                rel_entries.append((target_sec, r_offset, r_type, r_sym))

    func_addr = sec_addrs[st_shndx] + st_value
    return func_addr, st_size, sec_addrs, sec_by_idx, syms, rel_entries


def build_cand_stubs_and_relocate(
    uc: Uc, sec_addrs, sec_by_idx, syms, rel_entries
) -> Dict[str, int]:
    for idx, addr in sec_addrs.items():
        _, _, sbytes = sec_by_idx[idx]
        if sbytes:
            uc.mem_write(addr, sbytes)

    stub_cursor = CAND_BASE + 0x40000
    ext_stubs: Dict[str, int] = {}

    def get_stub(name: str) -> int:
        nonlocal stub_cursor
        if name not in ext_stubs:
            ext_stubs[name] = stub_cursor
            uc.mem_write(stub_cursor, struct.pack("<I", 0xE12FFF1E))
            stub_cursor += 4
        return ext_stubs[name]

    for target_sec, r_offset, r_type, r_sym in rel_entries:
        if r_type == 42:
            continue
        patch_addr = sec_addrs[target_sec] + r_offset
        sym_name, sym_val, _, _, sym_shndx = syms[r_sym]
        if sym_shndx == 0:
            target_addr = get_stub(sym_name)
        else:
            target_addr = sec_addrs[sym_shndx] + sym_val

        cur_word = struct.unpack("<I", uc.mem_read(patch_addr, 4))[0]
        if r_type in (28, 29):
            imm24 = ((target_addr - (patch_addr + 8)) >> 2) & 0x00FFFFFF
            patched = (cur_word & 0xFF000000) | imm24
            uc.mem_write(patch_addr, struct.pack("<I", patched))
        elif r_type == 2:
            uc.mem_write(patch_addr, struct.pack("<I", (cur_word + target_addr) & 0xFFFFFFFF))
        elif r_type in (43, 44):
            imm16 = (target_addr & 0xFFFF) if r_type == 43 else ((target_addr >> 16) & 0xFFFF)
            imm4 = (imm16 >> 12) & 0xF
            imm12 = imm16 & 0xFFF
            patched = (cur_word & 0xFFF0F000) | (imm4 << 16) | imm12
            uc.mem_write(patch_addr, struct.pack("<I", patched))
        else:
            raise RuntimeError(f"unsupported reloc type {r_type} for {sym_name}")

    return ext_stubs


def run_one(
    use_candidate: bool,
    cand_info,
    a0: int,
    a1: int,
    a2: int,
    a3: int,
    r_bc: int,
    r_224: int,
    r_84: int,
    kind: int,
    mutate_kind: str = "",
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(CAND_BASE, CAND_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(SENTINEL, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(INFO_BASE, b"\x00" * 0x20)
    uc.mem_write(INFO_BASE + 6, bytes([kind]))

    if not use_candidate:
        uc.mem_write(ORIG_ADDR, ORIG_BYTES)
        for addr in CALLEES_ORIG.values():
            uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))
        stub_map = {v: k for k, v in CALLEES_ORIG.items()}
        entry_addr = ORIG_ADDR
    else:
        func_addr, _, sec_addrs, sec_by_idx, syms, rel_entries = cand_info
        ext_stubs = build_cand_stubs_and_relocate(
            uc, sec_addrs, sec_by_idx, syms, rel_entries
        )
        stub_map = {v: k for k, v in ext_stubs.items()}
        entry_addr = func_addr

    events: List[Tuple] = []

    def hook_code(uc_inst: Uc, address: int, size_i: int, user_data):
        name = stub_map.get(address)
        if name is None:
            return
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        if name == "script_vm_func_002990bc":
            events.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, r_bc)
        elif name == "script_vm_func_00299224":
            events.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, r_224)
        elif name == "script_vm_func_00299084":
            events.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, r_84)
        elif name == "script_vm_func_002b6700":
            events.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, INFO_BASE)
        elif name == "func_002be4dc":
            if mutate_kind == "bad_color":
                r0 ^= 1
            events.append((name, r0))
        elif name == "script_vm_func_002aec80":
            r1 = uc_inst.reg_read(UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(UC_ARM_REG_R3)
            sp = uc_inst.reg_read(UC_ARM_REG_SP)
            s0, s1 = struct.unpack("<2I", uc_inst.mem_read(sp, 8))
            if mutate_kind == "bad_msg_id":
                r2 ^= 1
            elif mutate_kind == "bad_stack":
                s1 ^= 1
            events.append((name, r0, r1, r2, r3, s0, s1))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x00750000)
        elif name == "script_vm_func_002bef14":
            if mutate_kind == "bad_bef14":
                r0 ^= 4
            events.append((name, r0))
        uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, hook_code)

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x200)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL)
    uc.reg_write(UC_ARM_REG_R0, a0)
    uc.reg_write(UC_ARM_REG_R1, a1)
    uc.reg_write(UC_ARM_REG_R2, a2)
    uc.reg_write(UC_ARM_REG_R3, a3)

    if mutate_kind == "skip_all":
        return events

    uc.emu_start(entry_addr, SENTINEL, timeout=2_000_000, count=200_000)
    return events


def main() -> int:
    obj_path = REPO_ROOT / "build" / "leaf_0029af60" / "leaf_batch46_a.o"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(REPO_ROOT / TU_REL, obj_path, REPO_ROOT)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    cand_info = load_candidate_func(obj_path, FUNC_NAME)
    _, cand_size, _, _, _, _ = cand_info

    cases = []
    for r_bc in (0, 1):
        # r_224 != 0
        cases.append((0x11, 0x22, 0x33, 0x44, r_bc, 1, 0, 0))
        # r_224 == 0, r_84 != 0
        cases.append((0x11, 0x22, 0x33, 0x44, r_bc, 0, 1, 0))
        # r_224 == 0, r_84 == 0, all kind 0..12
        for k in range(13):
            cases.append((0x11, 0x22, 0x33, 0x44, r_bc, 0, 0, k))

    for i, params in enumerate(cases):
        o = run_one(False, cand_info, *params)
        c = run_one(True, cand_info, *params)
        if o != c:
            print(f"MISMATCH on case {i} ({params}):")
            print(f"  orig={o}")
            print(f"  cand={c}")
            return 1

    mutants = [
        ("skip_all", (0x11, 0x22, 0x33, 0x44, 0, 1, 0, 0)),
        ("bad_color", (0x11, 0x22, 0x33, 0x44, 1, 1, 0, 0)),
        ("bad_msg_id", (0x11, 0x22, 0x33, 0x44, 0, 0, 0, 8)),
        ("bad_stack", (0x11, 0x22, 0x33, 0x44, 0, 0, 0, 4)),
        ("bad_bef14", (0x11, 0x22, 0x33, 0x44, 1, 0, 0, 11)),
    ]
    detected = 0
    for name, params in mutants:
        o = run_one(False, cand_info, *params)
        m = run_one(True, cand_info, *params, mutate_kind=name)
        if o != m:
            detected += 1
        else:
            print(f"MUTANT NOT DETECTED: {name}")
            return 1

    print(
        f"PASS: {FUNC_NAME} (0x{ORIG_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants "
        f"(candidate {cand_size} B vs original {ORIG_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
