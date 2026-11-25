#!/usr/bin/env python3
"""Differential Unicorn verification for effPolygonTex_func_002f3290 (0x002f3290)."""

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
FUNC_NAME = "effPolygonTex_func_002f3290"
ORIG_ADDR = 0x002F3290
ORIG_SIZE = 396

CALLEES_ORIG = {
    "engine_func_002c34a4": 0x002C34A4,
    "engine_func_002c4b30": 0x002C4B30,
    "effGeometry_func_002474a0": 0x002474A0,
    "engine_func_0024c60c": 0x0024C60C,
    "engine_func_002c5ff4": 0x002C5FF4,
    "engine_func_0024c5ec": 0x0024C5EC,
    "engine_func_0024745c": 0x0024745C,
    "effP2A_func_00249324": 0x00249324,
    "engine_func_0024c5dc": 0x0024C5DC,
    "engine_func_00269758": 0x00269758,
    "effTLP_func_00249588": 0x00249588,
}

ORIG_BYTES = bytes.fromhex(
    "30402de90050a0e170019fe50cd04de2"
    "2410a0e30000a0e10110a0e31000a0e3"
    "f000cde1d430a0e30020a0e3011ca0e3"
    "0108a0e37640ffeb0040a0e1d410a0e3"
    "1646ffeb0010a0e3001084e5041084e5"
    "4b0a9fed081084e50c1084e5030a84ed"
    "101084e5141084e5181084e51c1084e5"
    "070a84ed0000e0e3240084e5000055e3"
    "080a84ed3a00000a4c00a0e300008de5"
    "f0309fe50420a0e30210a0e30100a0e3"
    "5a50fdebc80084e5bc00d5e1280084e5"
    "0500a0e1b064fdeb0010a0e19820a0e3"
    "300084e2264bffeb0500a0e1a264fdeb"
    "000050e32600000abc11d5e10a0051e3"
    "01f19f37220000ea04342f00a0332f00"
    "bc332f0004342f00d0332f0004342f00"
    "04342f00f8332f0004342f00a0332f00"
    "c82094e50010a0e10200a0e12a50fdeb"
    "00f020e300f020e3110000ea00f020e3"
    "d757fdebd00084e500f020e30c0000ea"
    "000090e5c85094e57000ffe67e64fdeb"
    "040085e500f020e3dad8fdeb00f020e3"
    "00f020e3020000ea00f020e36158fdeb"
    "cc0084e50cd08de20400a0e13080bde8"
    "080241000000803fc2374700"
)
# Fix line 45/46 typo check below if needed; let's assert len
assert len(ORIG_BYTES) == ORIG_SIZE, f"len={len(ORIG_BYTES)}"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00500000
CAND_BASE = 0x00600000
CAND_SIZE = 0x00100000
DATA_BASE = 0x00700000
DATA_SIZE = 0x00100000
STACK_BASE = 0x00900000
STACK_SIZE = 0x00020000
OBJ_BASE = 0x00720000
GEOM_BASE = 0x00730000
DESC_BASE = 0x00740000
PAYLOAD_BASE = 0x00750000
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
    desc_ptr: int,
    h0c: int,
    kind: int,
    has_payload: bool,
    mutate_kind: str = "",
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(CAND_BASE, CAND_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(SENTINEL, struct.pack("<I", 0xE12FFF1E))
    enable_vfp(uc)
    uc.mem_write(OBJ_BASE, b"\xAA" * 0x100)
    uc.mem_write(GEOM_BASE, b"\x00" * 0x40)
    if desc_ptr != 0:
        uc.mem_write(desc_ptr, b"\x00" * 0x40)
        uc.mem_write(desc_ptr + 0x0C, struct.pack("<H", h0c))
        uc.mem_write(desc_ptr + 0x1C, struct.pack("<H", kind))
        uc.mem_write(PAYLOAD_BASE, struct.pack("<H", 0xBEEF))

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
        if name == "engine_func_002c34a4":
            sp = uc_inst.reg_read(UC_ARM_REG_SP)
            s0, s1 = struct.unpack("<2I", uc_inst.mem_read(sp, 8))
            events.append((name, r0, r1, r2, r3, s0, s1))
            uc_inst.reg_write(UC_ARM_REG_R0, OBJ_BASE)
        elif name == "engine_func_002c4b30":
            events.append((name, r0, r1))
            uc_inst.mem_write(r0, b"\x00" * r1)
        elif name == "effGeometry_func_002474a0":
            sp = uc_inst.reg_read(UC_ARM_REG_SP)
            s0 = struct.unpack("<I", uc_inst.mem_read(sp, 4))[0]
            if mutate_kind == "bad_geom":
                s0 ^= 4
            events.append((name, r0, r1, r2, r3, s0))
            uc_inst.reg_write(UC_ARM_REG_R0, GEOM_BASE)
        elif name == "engine_func_0024c60c":
            events.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x00760000)
        elif name == "engine_func_002c5ff4":
            if mutate_kind == "bad_copy":
                r2 ^= 4
            events.append((name, r0, r1, r2))
        elif name == "engine_func_0024c5ec":
            events.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, PAYLOAD_BASE if has_payload else 0)
        elif name == "engine_func_0024745c":
            if mutate_kind == "bad_24745c":
                r1 ^= 4
            events.append((name, r0, r1))
        elif name == "effP2A_func_00249324":
            events.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x11112222)
        elif name == "engine_func_0024c5dc":
            events.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x33334444)
        elif name == "engine_func_00269758":
            if mutate_kind == "bad_269758":
                r0 ^= 1
            events.append((name, r0))
        elif name == "effTLP_func_00249588":
            events.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x55556666)
        uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, hook_code)

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x200)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL)
    uc.reg_write(UC_ARM_REG_R0, desc_ptr)

    if mutate_kind == "skip_all":
        return events, 0, b"", b""

    uc.emu_start(entry_addr, SENTINEL, timeout=2_000_000, count=200_000)
    ret = uc.reg_read(UC_ARM_REG_R0)
    obj_dump = bytes(uc.mem_read(OBJ_BASE, 0xD4))
    geom_dump = bytes(uc.mem_read(GEOM_BASE, 0x10))
    return events, ret, obj_dump, geom_dump


def main() -> int:
    obj_path = REPO_ROOT / "build" / "leaf_002f3290" / "leaf_batch46_a.o"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(REPO_ROOT / TU_REL, obj_path, REPO_ROOT)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    cand_info = load_candidate_func(obj_path, FUNC_NAME)
    _, cand_size, _, _, _, _ = cand_info

    cases = [
        (0, 0, 0, False),
        (DESC_BASE, 0x1234, 1, False),
    ]
    for k in range(12):
        cases.append((DESC_BASE, 0x4321 + k, k, True))

    for i, params in enumerate(cases):
        o = run_one(False, cand_info, *params)
        c = run_one(True, cand_info, *params)
        if o != c:
            print(f"MISMATCH on case {i} ({params}):")
            print(f"  orig ev={o[0]} ret=0x{o[1]:08x}")
            print(f"  cand ev={c[0]} ret=0x{c[1]:08x}")
            return 1

    mutants = [
        ("skip_all", (0, 0, 0, False)),
        ("bad_geom", (DESC_BASE, 0x1234, 1, True)),
        ("bad_copy", (DESC_BASE, 0x1234, 1, True)),
        ("bad_24745c", (DESC_BASE, 0x1234, 9, True)),
        ("bad_269758", (DESC_BASE, 0x1234, 4, True)),
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
