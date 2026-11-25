#!/usr/bin/env python3
"""Differential Unicorn verification for CommonBg_func_002d7b48 (0x002d7b48)."""

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
FUNC_NAME = "CommonBg_func_002d7b48"
ORIG_ADDR = 0x002D7B48
ORIG_SIZE = 468
ORIG_GLOBAL = 0x0043DC20

CALLEES_ORIG = {
    "engine_func_002c54f0": 0x002C54F0,
    "AsdText_func_002bda1c": 0x002BDA1C,
    "AsdText_func_00296de0": 0x00296DE0,
    "AsdTMTexTable_func_002c4e28": 0x002C4E28,
    "engine_func_002c5ab8": 0x002C5AB8,
    "camp_func_002c4c00": 0x002C4C00,
    "script_vm_func_002ed584": 0x002ED584,
    "script_vm_func_00221214": 0x00221214,
    "ui_func_002ed5d0": 0x002ED5D0,
}

ORIG_BYTES = bytes.fromhex(
    "70402de910d04de21c119fe5470f8fe2"
    "0000a0e10100a0e3011ca0e300008de5"
    "2430a0e30020a0e30100a0e15db6ffeb"
    "0050a0e3005080e5045080e5085080e5"
    "0c5080e5105080e518619fe5145080e5"
    "185080e51c5080e5205080e50040a0e1"
    "080086e50500a0e19997ffeb0c0084e5"
    "f4108fe204108de50030a0e30020e0e3"
    "0310a0e300508de582fcfeeb0000a0e3"
    "8f97ffeb100084e5dc108fe204108de5"
    "0030a0e30020e0e30310a0e300508de5"
    "78fcfeeb2d00a0e388b4ffeb0010a0e3"
    "2d00a0e3a9b7ffeb040096e5dc209fe5"
    "d4109fe504608de2000090e500208de5"
    "0030a0e30c008de5120086e80820a0e3"
    "0210a0e3b8008fe2eeb3ffeb000084e5"
    "bc109fe50c008de508408de522008de8"
    "0030a0e30820a0e3e710a0e3a4008fe2"
    "e4b3ffeb10d08de27080bde80c050000"
    "633a5c534d54345c5852443638365c73"
    "646473345c70726f6772616d5c63616d"
    "705c436f6d6d6f6e42675c436f6d6d6f"
    "6e42672e6370700020dc43008264828e"
    "828782818287828500000000826f828c"
    "828582818293828581408294828f8295"
    "82838288814082948288828581408289"
    "8283828f828e81440000000084d52e00"
    "14122200434f4d424720455645204341"
    "4c430000d0d52e00434f4d4247204444"
    "52415700"
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
G4_PTR = 0x00730000
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
            if sym_name == "script_vm_func_00221214":
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


def read_cstr(uc: Uc, addr: int) -> bytes:
    if addr == 0:
        return b"<null>"
    out = bytearray()
    for i in range(64):
        b = uc.mem_read(addr + i, 1)[0]
        if b == 0:
            break
        out.append(b)
    return bytes(out)


def run_one(
    use_candidate: bool,
    cand_info,
    g4_val: int,
    mutate_kind: str = "",
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(CAND_BASE, CAND_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(SENTINEL, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(ORIG_GLOBAL, b"\x00" * 0x20)
    uc.mem_write(ORIG_GLOBAL + 4, struct.pack("<I", G4_PTR))
    uc.mem_write(G4_PTR, struct.pack("<I", g4_val))
    uc.mem_write(SELF_BASE, b"\xAA" * 0x24)

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
    text_cnt = [0]
    proc_cnt = [0x00750000]

    def hook_code(uc_inst: Uc, address: int, size_i: int, user_data):
        name = stub_map.get(address)
        if name is None:
            return
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(UC_ARM_REG_R3)
        if name == "engine_func_002c54f0":
            sp = uc_inst.reg_read(UC_ARM_REG_SP)
            s0 = struct.unpack("<I", uc_inst.mem_read(sp, 4))[0]
            events.append((name, r0, r1, r2, r3, s0))
            uc_inst.reg_write(UC_ARM_REG_R0, SELF_BASE)
        elif name == "AsdText_func_002bda1c":
            events.append((name, r0))
            text_cnt[0] += 1
            uc_inst.reg_write(UC_ARM_REG_R0, 0x00740000 + text_cnt[0] * 0x10)
        elif name == "AsdText_func_00296de0":
            sp = uc_inst.reg_read(UC_ARM_REG_SP)
            s0, s1 = struct.unpack("<2I", uc_inst.mem_read(sp, 8))
            lbl = read_cstr(uc_inst, s1)
            if mutate_kind == "bad_label":
                lbl = b"mutated"
            events.append((name, r0, r1, r2, r3, s0, lbl))
        elif name == "AsdTMTexTable_func_002c4e28":
            events.append((name, r0))
        elif name == "engine_func_002c5ab8":
            events.append((name, r0, r1))
        elif name == "camp_func_002c4c00":
            pname = read_cstr(uc_inst, r0)
            sp = uc_inst.reg_read(UC_ARM_REG_SP)
            fn0, fn1, s_ptr, g4 = struct.unpack("<4I", uc_inst.mem_read(sp, 16))
            fn0_name = stub_map.get(fn0, f"0x{fn0:08x}")
            fn1_name = stub_map.get(fn1, "0" if fn1 == 0 else f"0x{fn1:08x}")
            if mutate_kind == "bad_proc" and pname == b"COMBG EVE CALC":
                fn0_name = "mutated"
            elif mutate_kind == "bad_ddraw" and pname == b"COMBG DDRAW":
                r1 ^= 1
            events.append((name, pname, r1, r2, r3, fn0_name, fn1_name, s_ptr, g4))
            proc_cnt[0] += 0x100
            uc_inst.reg_write(UC_ARM_REG_R0, proc_cnt[0])
        uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, hook_code)

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x200)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL)

    if mutate_kind == "skip_all":
        return events, b"", b""

    uc.emu_start(entry_addr, SENTINEL, timeout=2_000_000, count=200_000)
    if mutate_kind == "corrupt_self":
        uc.mem_write(SELF_BASE, b"\x55\x55\x55\x55")

    return events, bytes(uc.mem_read(SELF_BASE, 0x24)), bytes(uc.mem_read(ORIG_GLOBAL, 0x10))


def main() -> int:
    obj_path = REPO_ROOT / "build" / "leaf_002d7b48" / "leaf_batch46_a.o"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(REPO_ROOT / TU_REL, obj_path, REPO_ROOT)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    cand_info = load_candidate_func(obj_path, FUNC_NAME)
    _, cand_size, _, _, _, _ = cand_info

    cases = [0x12345678, 0xCAFEBABE, 0]
    for i, g4 in enumerate(cases):
        o = run_one(False, cand_info, g4)
        c = run_one(True, cand_info, g4)
        if o != c:
            print(f"MISMATCH on case {i} (g4=0x{g4:08x}):")
            print(f"  orig ev={o[0]}")
            print(f"  cand ev={c[0]}")
            return 1

    mutants = ["skip_all", "bad_label", "bad_proc", "bad_ddraw", "corrupt_self"]
    detected = 0
    for name in mutants:
        o = run_one(False, cand_info, 0x12345678)
        m = run_one(True, cand_info, 0x12345678, mutate_kind=name)
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
