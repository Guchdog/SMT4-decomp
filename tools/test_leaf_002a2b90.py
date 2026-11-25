#!/usr/bin/env python3
"""Differential Unicorn verification for func_002a2b90 (0x002a2b90)."""

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
FUNC_NAME = "func_002a2b90"
ORIG_ADDR = 0x002A2B90
ORIG_SIZE = 420

BLIT_A540 = 0x0015A540
BLIT_A4D0 = 0x0015A4D0

ORIG_BYTES = bytes.fromhex(
    "f04f2de9000052e34cd04de205cda013"
    "19cea003021281e0000053e324c08de5"
    "0470911500709105081081e2f090a0e3"
    "240091e808c0a0e3000052e31810a003"
    "0e00000a050052e30010a0e302f19f37"
    "090000eaf82b2a00002c2a00082c2a00"
    "082c2a00082c2a000410a0e3020000ea"
    "0310a0e3000000ea0210a0e38111a0e1"
    "2551a0e10162a0e1050052e32661a0e1"
    "8131a0e10040a0e31c508de52c608de5"
    "02f19f373a0000ea4c2c2a004c2c2a00"
    "742c2a00742c2a00742c2a000320a0e3"
    "056182e00551a0e104a08de20c508de5"
    "50008ae810608de2bc809fe5140086e8"
    "080000ea0220a0e3056182e00551a0e1"
    "04a08de20c508de550008ae810608de2"
    "98809fe5140086e8000050e32000000a"
    "0050a0e124009de5000050e30000a0e3"
    "34008de51a00009a1c009de503a0c1e3"
    "03b0c3e3900c00e044008de50740a0e1"
    "0060a0e31c209de504308de20410a0e1"
    "0500a0e138ff2fe1086086e2090056e1"
    "0a4084e00b5085e0f5ffff3a44009de5"
    "24109de5007187e02c009de5005185e0"
    "34009de5080080e2010050e134008de5"
    "e9ffff3a4cd08de2f08fbde840a51500"
    "d0a41500"
)
# Fix line 45 byte typo if needed
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
DST_BASE = 0x00740000
SRC0_BASE = 0x00760000
SRC1_BASE = 0x00780000
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
    dst: int,
    screen_sel: int,
    buf_idx: int,
    fmt: int,
    stride: int,
    mutate_kind: str = "",
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(CAND_BASE, CAND_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(SENTINEL, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(BLIT_A540, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(BLIT_A4D0, struct.pack("<I", 0xE12FFF1E))

    entry_off = screen_sel * 0x10
    uc.mem_write(INFO_BASE, b"\x00" * 0x40)
    uc.mem_write(INFO_BASE + entry_off, struct.pack("<4I", SRC0_BASE, SRC1_BASE, fmt, stride))

    if not use_candidate:
        uc.mem_write(ORIG_ADDR, ORIG_BYTES)
        ext_stubs: Dict[str, int] = {}
        entry_addr = ORIG_ADDR
    else:
        func_addr, _, sec_addrs, sec_by_idx, syms, rel_entries = cand_info
        ext_stubs = build_cand_stubs_and_relocate(uc, sec_addrs, sec_by_idx, syms, rel_entries)
        entry_addr = func_addr

    stub_map = {v: k for k, v in ext_stubs.items()}
    calls: List[Tuple] = []

    def hook_code(uc_inst: Uc, address: int, size_i: int, user_data):
        sname = stub_map.get(address)
        if sname in ("__aeabi_memclr", "__aeabi_memclr4", "__aeabi_memclr8"):
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(UC_ARM_REG_R1)
            uc_inst.mem_write(r0, b"\x00" * r1)
            uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))
            return
        if sname == "memset":
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(UC_ARM_REG_R1) & 0xFF
            r2 = uc_inst.reg_read(UC_ARM_REG_R2)
            uc_inst.mem_write(r0, bytes([r1]) * r2)
            uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))
            return
        if address in (BLIT_A540, BLIT_A4D0):
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(UC_ARM_REG_R3)
            params = struct.unpack("<5I", uc_inst.mem_read(r3, 20))
            if mutate_kind == "bad_fn":
                address ^= 0x10
            elif mutate_kind == "bad_params":
                params = (0,) * 5
            elif mutate_kind == "bad_dst":
                r0 ^= 4
            elif mutate_kind == "bad_src":
                r1 ^= 4
            calls.append((address, r0, r1, r2, params))
            uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, hook_code)

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x200)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL)
    uc.reg_write(UC_ARM_REG_R0, dst)
    uc.reg_write(UC_ARM_REG_R1, INFO_BASE)
    uc.reg_write(UC_ARM_REG_R2, screen_sel)
    uc.reg_write(UC_ARM_REG_R3, buf_idx)

    if mutate_kind == "skip_all":
        return calls

    uc.emu_start(entry_addr, SENTINEL, timeout=2_000_000, count=2_000_000)
    return calls


def main() -> int:
    obj_path = REPO_ROOT / "build" / "leaf_002a2b90" / "leaf_batch46_a.o"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(REPO_ROOT / TU_REL, obj_path, REPO_ROOT)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    cand_info = load_candidate_func(obj_path, FUNC_NAME)
    _, cand_size, _, _, _, _ = cand_info

    cases = [
        # null dst, out-of-range fmt
        (0, 0, 0, 0, 0x3C0),
        (DST_BASE, 0, 0, 5, 0x3C0),
        (DST_BASE, 1, 1, 6, 0x3C0),
    ]
    for scr in (0, 1):
        for buf in (0, 1):
            for fmt in range(5):
                cases.append((DST_BASE, scr, buf, fmt, 0x3C0))

    for i, params in enumerate(cases):
        o = run_one(False, cand_info, *params)
        c = run_one(True, cand_info, *params)
        if o != c:
            print(f"MISMATCH on case {i} ({params}):")
            print(f"  orig len={len(o)} first3={o[:3]}")
            print(f"  cand len={len(c)} first3={c[:3]}")
            return 1

    mutants = [
        ("skip_all", (DST_BASE, 0, 0, 0, 0x3C0)),
        ("bad_fn", (DST_BASE, 0, 0, 2, 0x3C0)),
        ("bad_params", (DST_BASE, 1, 0, 1, 0x3C0)),
        ("bad_dst", (DST_BASE, 0, 1, 3, 0x3C0)),
        ("bad_src", (DST_BASE, 1, 1, 4, 0x3C0)),
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
