#!/usr/bin/env python3
"""Differential Unicorn verification for script_vm_func_00273760 (0x00273760)."""

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
    UC_ARM_REG_SP,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.build_check import compile_tu_armv6k

TU_REL = "src/engine/leaf_batch46_a.cpp"
FUNC_NAME = "script_vm_func_00273760"
ORIG_ADDR = 0x00273760
ORIG_SIZE = 340

CALLEES_ORIG = {
    "script_vm_func_00297704": 0x00297704,
    "script_vm_func_002b8b78": 0x002B8B78,
    "scrScriptProcess_func_002972f8": 0x002972F8,
    "script_vm_func_002971e4": 0x002971E4,
    "script_vm_func_0019dfbc": 0x0019DFBC,
    "script_vm_func_00290694": 0x00290694,
    "script_vm_func_00299064": 0x00299064,
    "script_vm_func_00290410": 0x00290410,
    "script_vm_func_00290374": 0x00290374,
    "script_vm_func_0029066c": 0x0029066C,
}

ORIG_BYTES = bytes.fromhex(
    "70402de90040a0e1000090e50460a0e3"
    "050050e300f19f37470000ea90372700"
    "bc3727001038270084382700a4382700"
    "14019fe50020a0e30c1084e2d88f00eb"
    "08019fe50020a0e3101084e2d48f00eb"
    "0100a0e3000084e5370000ea0c0094e5"
    "000050e310009415000050133200000a"
    "0800d4e5000050e39000a013e514011b"
    "dc00c4e100f020e3c28e00eb0210a0e3"
    "140084e5081180e5140094e5041094e5"
    "778e00eb0200a0e300f020e31a0000ea"
    "140094e5e8a9fceb020050e300f020e3"
    "1d00001a9a7300eb0050a0e100f020e3"
    "0b9600eb000050e300f020e30200000a"
    "0010a0e30500a0e1f07200eb00f020e3"
    "c77200eb00f020e300f020e3827300eb"
    "000050e300f020e30a00000a140094e5"
    "0d10a0e35a8e00eb0300a0e3000084e5"
    "050000ea140094e5cba9fceb020050e3"
    "00f020e30000001a006084e50000a0e3"
    "7080bde80100a0e37080bde8b0f13f00"
    "94f13f00"
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
SELF_BASE = 0x00720000
PROC_BASE = 0x00740000
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
    state: int,
    arg4: int,
    flag8: int,
    c0: int,
    c1: int,
    status_ret: int,
    has_299064: int,
    has_29066c: int,
    mutate_kind: str = "",
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(CAND_BASE, CAND_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(SENTINEL, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(SELF_BASE, b"\x00" * 0x40)
    uc.mem_write(PROC_BASE, b"\x00" * 0x200)

    uc.mem_write(SELF_BASE + 0x00, struct.pack("<I", state))
    uc.mem_write(SELF_BASE + 0x04, struct.pack("<I", arg4))
    uc.mem_write(SELF_BASE + 0x08, bytes([flag8]))
    uc.mem_write(SELF_BASE + 0x0C, struct.pack("<I", c0))
    uc.mem_write(SELF_BASE + 0x10, struct.pack("<I", c1))
    uc.mem_write(SELF_BASE + 0x14, struct.pack("<I", PROC_BASE))

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

    def hook_code(uc_inst: Uc, address: int, size: int, user_data):
        name = stub_map.get(address)
        if name is None:
            return
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        if name == "script_vm_func_00297704":
            events.append((name, r0, r1, r2))
            if r1 == SELF_BASE + 0x0C:
                uc_inst.mem_write(r1, struct.pack("<I", 0x11111111))
            elif r1 == SELF_BASE + 0x10:
                uc_inst.mem_write(r1, struct.pack("<I", 0x22222222))
        elif name == "script_vm_func_002b8b78":
            events.append((name, r0))
        elif name == "scrScriptProcess_func_002972f8":
            events.append((name, r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, PROC_BASE)
        elif name == "script_vm_func_002971e4":
            if mutate_kind == "bad_2971e4":
                r1 ^= 1
            events.append((name, r0, r1))
        elif name == "script_vm_func_0019dfbc":
            events.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, status_ret)
        elif name == "script_vm_func_00290694":
            events.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x00760000)
        elif name == "script_vm_func_00299064":
            events.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, has_299064)
        elif name == "script_vm_func_00290410":
            events.append((name, r0, r1))
        elif name == "script_vm_func_00290374":
            events.append((name,))
        elif name == "script_vm_func_0029066c":
            events.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, has_29066c)
        uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, hook_code)

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x200)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL)
    uc.reg_write(UC_ARM_REG_R0, SELF_BASE)

    if mutate_kind == "skip_all":
        return events, 0, b"", b""

    uc.emu_start(entry_addr, SENTINEL, timeout=2_000_000, count=200_000)
    ret = uc.reg_read(UC_ARM_REG_R0)
    if mutate_kind == "bad_ret":
        ret ^= 1
    elif mutate_kind == "corrupt_state":
        uc.mem_write(SELF_BASE, struct.pack("<I", 0xDEAD))
    elif mutate_kind == "corrupt_proc":
        uc.mem_write(PROC_BASE + 0x108, struct.pack("<I", 0x99))

    self_dump = bytes(uc.mem_read(SELF_BASE, 0x18))
    proc_dump = bytes(uc.mem_read(PROC_BASE + 0x108, 4))
    return events, ret, self_dump, proc_dump


def main() -> int:
    obj_path = REPO_ROOT / "build" / "leaf_00273760" / "leaf_batch46_a.o"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(REPO_ROOT / TU_REL, obj_path, REPO_ROOT)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    cand_info = load_candidate_func(obj_path, FUNC_NAME)
    _, cand_size, _, _, _, _ = cand_info

    cases = [
        # state 0
        (0, 0x42, 0, 0, 0, 0, 0, 0),
        # state 1: missing c0 or c1
        (1, 0x42, 1, 0, 0x222, 0, 0, 0),
        (1, 0x42, 1, 0x111, 0, 0, 0, 0),
        # state 1: valid c0 & c1, flag8 == 0 and flag8 == 1
        (1, 0x42, 0, 0x111, 0x222, 0, 0, 0),
        (1, 0x77, 1, 0x111, 0x222, 0, 0, 0),
        # state 2: status != 2 and status == 2 with combinations of 299064 / 29066c
        (2, 0, 0, 0, 0, 0, 0, 0),
        (2, 0, 0, 0, 0, 1, 1, 1),
        (2, 0, 0, 0, 0, 2, 0, 0),
        (2, 0, 0, 0, 0, 2, 1, 0),
        (2, 0, 0, 0, 0, 2, 0, 1),
        (2, 0, 0, 0, 0, 2, 1, 1),
        # state 3: status != 2 and status == 2
        (3, 0, 0, 0, 0, 0, 0, 0),
        (3, 0, 0, 0, 0, 2, 0, 0),
        # state 4 -> returns 1
        (4, 0, 0, 0, 0, 0, 0, 0),
        # out of range -> returns 0
        (5, 0, 0, 0, 0, 0, 0, 0),
        (0xFFFFFFFF, 0, 0, 0, 0, 0, 0, 0),
    ]

    for i, params in enumerate(cases):
        o = run_one(False, cand_info, *params)
        c = run_one(True, cand_info, *params)
        if o != c:
            print(f"MISMATCH on case {i} ({params}):")
            print(f"  orig={o}")
            print(f"  cand={c}")
            return 1

    mutants = [
        ("skip_all", (0, 0x42, 0, 0, 0, 0, 0, 0)),
        ("bad_ret", (4, 0, 0, 0, 0, 0, 0, 0)),
        ("corrupt_state", (3, 0, 0, 0, 0, 2, 0, 0)),
        ("corrupt_proc", (1, 0x42, 0, 0x111, 0x222, 0, 0, 0)),
        ("bad_2971e4", (2, 0, 0, 0, 0, 2, 1, 1)),
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
