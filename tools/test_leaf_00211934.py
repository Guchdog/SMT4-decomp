#!/usr/bin/env python3
"""Differential Unicorn verification for engine_func_00211934 (0x00211934)."""

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
FUNC_NAME = "engine_func_00211934"
ORIG_ADDR = 0x00211934
ORIG_SIZE = 416

CALLEES_ORIG = {
    "engine_func_00296f60": 0x00296F60,
    "engine_func_002c4b30": 0x002C4B30,
    "script_vm_func_002be828": 0x002BE828,
    "engine_func_002bf86c": 0x002BF86C,
    "script_vm_func_00295904": 0x00295904,
    "script_vm_func_002bd25c": 0x002BD25C,
    "camp_func_0028ebd8": 0x0028EBD8,
    "engine_func_002bcff0": 0x002BCFF0,
    "camp_func_0029f088": 0x0029F088,
}

ORIG_BYTES = bytes.fromhex(
    "30402de984d04de20000a0e3861502eb"
    "0050a0e10100a0e3831502eb0040a0e1"
    "8010a0e30d00a0e173cc02eb240055e3"
    "05f19f37560000eafc192100fc192100"
    "fc192100fc192100fc192100fc192100"
    "fc192100fc1921002c1a21002c1a2100"
    "2c1a21002c1a21002c1a21002c1a2100"
    "2c1a21002c1a2100581a2100581a2100"
    "581a2100581a2100881a2100881a2100"
    "881a2100881a2100b41a2100b41a2100"
    "b41a2100b41a2100b41a2100b41a2100"
    "b41a2100b41a2100fc192100fc192100"
    "fc192100fc1921000110a0e30400a0e1"
    "87b302eb0010a0e10d00a0e195b702eb"
    "0d10a0e10500a0e1b80f02eb00f020e3"
    "00f020e3260000ea7400ffe609ae02eb"
    "0010a0e10d00a0e18ab702eb0d10a0e1"
    "0500a0e1ad0f02eb00f020e300f020e3"
    "1b0000ea7400bfe60110a0e35cf401eb"
    "0010a0e10d00a0e17eb702eb0d10a0e1"
    "0500a0e1a10f02eb00f020e300f020e3"
    "0f0000ea0400a0e157ad02eb0010a0e1"
    "0d00a0e173b702eb0d10a0e10500a0e1"
    "960f02eb00f020e300f020e3040000ea"
    "0030a0e30020e0e30410a0e10500a0e1"
    "6f3502eb84d08de20100a0e33080bde8"
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
            if sym_name == "script_vm_func_002be828":
                ext_stubs[sym_name] = target_addr
                uc.mem_write(target_addr, struct.pack("<I", 0xE12FFF1E))

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
    slot: int,
    val: int,
    mutate_kind: str = "",
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(CAND_BASE, CAND_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(SENTINEL, struct.pack("<I", 0xE12FFF1E))

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
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        if name == "engine_func_00296f60":
            events.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, slot if r0 == 0 else val)
        elif name == "engine_func_002c4b30":
            events.append((name, r1))
            uc_inst.mem_write(r0, b"\x00" * r1)
        elif name == "script_vm_func_002be828":
            events.append((name, r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x00750000)
        elif name == "script_vm_func_002bd25c":
            if mutate_kind == "bad_uxth":
                r0 ^= 0x10000
            events.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x00751000)
        elif name == "camp_func_0028ebd8":
            r0_s = struct.unpack("<i", struct.pack("<I", r0))[0]
            if mutate_kind == "bad_sxth":
                r0_s ^= 1
            events.append((name, r0_s, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x00752000)
        elif name == "engine_func_002bcff0":
            events.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x00753000)
        elif name == "engine_func_002bf86c":
            uc_inst.mem_write(r0, struct.pack("<I", r1))
            events.append((name, r1))
        elif name == "script_vm_func_00295904":
            buf_tag = struct.unpack("<I", uc_inst.mem_read(r1, 4))[0]
            buf_rest = bytes(uc_inst.mem_read(r1 + 4, 0x7C))
            assert buf_rest == b"\x00" * 0x7C
            events.append((name, r0, buf_tag))
        elif name == "camp_func_0029f088":
            r2 = uc_inst.reg_read(UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(UC_ARM_REG_R3)
            if mutate_kind == "bad_29f088":
                r2 ^= 1
            events.append((name, r0, r1, r2, r3))
        uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, hook_code)

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x200)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL)

    if mutate_kind == "skip_all":
        return events, 0

    uc.emu_start(entry_addr, SENTINEL, timeout=2_000_000, count=200_000)
    ret = uc.reg_read(UC_ARM_REG_R0)
    if mutate_kind == "bad_ret":
        ret ^= 1
    return events, ret


def main() -> int:
    obj_path = REPO_ROOT / "build" / "leaf_00211934" / "leaf_batch46_a.o"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(REPO_ROOT / TU_REL, obj_path, REPO_ROOT)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    cand_info = load_candidate_func(obj_path, FUNC_NAME)
    _, cand_size, _, _, _, _ = cand_info

    cases = []
    for s in range(38):
        cases.append((s, 0x12348765))
    cases.append((16, 0x0000FFFF))
    cases.append((8, 0xFFFF1234))

    for i, (s, v) in enumerate(cases):
        o = run_one(False, cand_info, s, v)
        c = run_one(True, cand_info, s, v)
        if o != c:
            print(f"MISMATCH on case {i} (slot={s}, val=0x{v:08x}):")
            print(f"  orig={o}")
            print(f"  cand={c}")
            return 1

    mutants = [
        ("skip_all", (0, 0x1234)),
        ("bad_uxth", (8, 0x12345678)),
        ("bad_sxth", (16, 0x00008001)),
        ("bad_29f088", (24, 0x1234)),
        ("bad_ret", (36, 0x1234)),
    ]
    detected = 0
    for name, (s, v) in mutants:
        o = run_one(False, cand_info, s, v)
        m = run_one(True, cand_info, s, v, mutate_kind=name)
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
