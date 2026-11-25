#!/usr/bin/env python3
"""Differential Unicorn verification for engine_func_002fb7a0 (0x002fb7a0)."""

from __future__ import annotations

import struct
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM, Uc
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_CPSR,
    UC_ARM_REG_FPEXC,
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
FUNC_NAME = "engine_func_002fb7a0"
ORIG_ADDR = 0x002FB7A0
ORIG_SIZE = 428

GLOBAL_S = 0x00447060
GLOBAL_CAM = 0x00447E88
GLOBAL_91C = 0x0049F91C

CALLEES_ORIG = {
    "script_vm_func_0027054c": 0x0027054C,
    "02d_func_0027b524": 0x0027B524,
    "engine_func_002d4fe0": 0x002D4FE0,
    "script_vm_func_00266c58": 0x00266C58,
    "script_vm_func_002819f4": 0x002819F4,
    "script_vm_func_002667b0": 0x002667B0,
    "script_vm_func_002668cc": 0x002668CC,
    "script_vm_func_00266704": 0x00266704,
}

ORIG_BYTES = bytes.fromhex(
    "f0472de90160a0e30070a0e378919fe5"
    "7c819fe57c519fe55c0a9fed004099e5"
    "180094e5060050e300f19f37540000ea"
    "e8b72f0050b82f00b8b82f0024b92f00"
    "24b92f00ccb82f00000098e5289084e2"
    "510adfed6310a0e3dc21c0e1240090e5"
    "f022c4e10d0089e8340084e50c0a84ed"
    "370ac4ede060c4e5481084e5041085e5"
    "49d3fdeb400094e5481094e5650050e3"
    "0030a0130a30a0036520a0030320a011"
    "37fffdebf861c4e100f020e3340000ea"
    "0400a0e1e165ffeb1c0094e5371a9fed"
    "010080e2100a00ee1c0084e50c1ad4ed"
    "090ad4ed000098e5c00ab8eee01a71ee"
    "800a21ee010a40ee080ac0ed1c0094e5"
    "1e0050e3220000ba1870c5e5280a9fed"
    "2a62c5e5370a84ed0200a0e3e060c4e5"
    "180084e51a0000ea0400a0e1c765ffeb"
    "00f020e300f020e3150000ea1d0a9fed"
    "240a84eddfacfdeb004099e50b70c4e5"
    "ec0094e50200c0e3ec0084e54018feeb"
    "400094e500f020e3acabfdeb400094e5"
    "482094e5641040e2ec0084e2eeabfdeb"
    "ec0084e200f020e379abfdeb1870c5e5"
    "2a62c5e50000a0e3f087bde860704400"
    "00004844887e44001cf9490000000000"
    "8988083d0000803f00004843"
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
S_BASE = 0x00720000
CAM_BASE = 0x00740000
SENTINEL = 0x006F0000


def enable_vfp(uc: Uc) -> None:
    uc.reg_write(UC_ARM_REG_C1_C0_2, uc.reg_read(UC_ARM_REG_C1_C0_2) | 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)


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
    state: int,
    timer: int,
    f40: int,
    mutate_kind: str = "",
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(CAND_BASE, CAND_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(SENTINEL, struct.pack("<I", 0xE12FFF1E))
    enable_vfp(uc)

    uc.mem_write(GLOBAL_S, struct.pack("<I", S_BASE))
    uc.mem_write(GLOBAL_CAM, struct.pack("<I", CAM_BASE))
    uc.mem_write(GLOBAL_91C, b"\xAA" * 0x240)
    uc.mem_write(CAM_BASE, b"\x00" * 0x40)
    uc.mem_write(CAM_BASE + 0x1C, struct.pack("<3f", 12.5, 100.0, -45.25))

    uc.mem_write(S_BASE, b"\x00" * 0x100)
    uc.mem_write(S_BASE + 0x0B, b"\x01")
    uc.mem_write(S_BASE + 0x18, struct.pack("<II", state, timer))
    uc.mem_write(S_BASE + 0x24, struct.pack("<f", 100.0))
    uc.mem_write(S_BASE + 0x30, struct.pack("<f", 800.0))
    uc.mem_write(S_BASE + 0x40, struct.pack("<I", f40))
    uc.mem_write(S_BASE + 0x48, struct.pack("<I", 0x63))
    uc.mem_write(S_BASE + 0xEC, struct.pack("<I", 0xFF))

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
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(UC_ARM_REG_R3)
        if name in ("script_vm_func_0027054c", "script_vm_func_00266c58", "script_vm_func_002819f4"):
            events.append((name,))
        elif name == "02d_func_0027b524":
            if mutate_kind == "bad_27b524":
                r2 ^= 1
            events.append((name, r0, r1, r2, r3))
        elif name in ("engine_func_002d4fe0", "script_vm_func_002667b0", "script_vm_func_00266704"):
            events.append((name, r0))
        elif name == "script_vm_func_002668cc":
            if mutate_kind == "bad_68cc":
                r1 ^= 1
            events.append((name, r0, r1, r2))
        uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, hook_code)

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x200)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL)

    if mutate_kind == "skip_all":
        return events, 0, b"", b"", b""

    uc.emu_start(entry_addr, SENTINEL, timeout=2_000_000, count=200_000)
    ret = uc.reg_read(UC_ARM_REG_R0)
    if mutate_kind == "corrupt_cam":
        uc.mem_write(CAM_BASE + 0x20, b"\x00\x00\x00\x00")
    elif mutate_kind == "corrupt_91c":
        uc.mem_write(GLOBAL_91C + 0x22A, b"\x55")

    s_dump = bytes(uc.mem_read(S_BASE, 0x100))
    cam_dump = bytes(uc.mem_read(CAM_BASE + 0x1C, 12))
    g_dump = bytes(uc.mem_read(GLOBAL_91C, 0x230))
    return events, ret, s_dump, cam_dump, g_dump


def main() -> int:
    obj_path = REPO_ROOT / "build" / "leaf_002fb7a0" / "leaf_batch46_a.o"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(REPO_ROOT / TU_REL, obj_path, REPO_ROOT)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    cand_info = load_candidate_func(obj_path, FUNC_NAME)
    _, cand_size, _, _, _, _ = cand_info

    cases = [
        (0, 0, 0x65),
        (0, 0, 0x66),
        (1, 0, 0x65),
        (1, 15, 0x65),
        (1, 28, 0x65),
        (1, 29, 0x65),
        (2, 0, 0x65),
        (3, 0, 0x65),
        (4, 0, 0x65),
        (5, 0, 0x65),
        (6, 0, 0x65),
    ]

    for i, params in enumerate(cases):
        o = run_one(False, cand_info, *params)
        c = run_one(True, cand_info, *params)
        if o != c:
            print(f"MISMATCH on case {i} ({params}):")
            print(f"  orig ev={o[0]} ret={o[1]}")
            print(f"  cand ev={c[0]} ret={c[1]}")
            return 1

    mutants = [
        ("skip_all", (0, 0, 0x65)),
        ("bad_27b524", (0, 0, 0x65)),
        ("corrupt_cam", (1, 15, 0x65)),
        ("corrupt_91c", (1, 29, 0x65)),
        ("bad_68cc", (5, 0, 0x65)),
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
