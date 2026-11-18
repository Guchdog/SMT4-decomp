#!/usr/bin/env python3
"""Differential test for AsdTMTexTable_func_002c5b04 (0x002c5b04) with Unicorn ARM."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "engine" / "asd_texture.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_002c5b04"

FUNC_ADDR = 0x002C5B04
FUNC_SIZE = 652

STUB_STRCPY = 0x002BF86C
STUB_STRCHR = 0x0010024C
STUB_FORMAT = 0x002BE7FC
STUB_RES_LOAD = 0x002C32F0
STUB_ALLOC_FLAGS = 0x002B76E8

STUB_NAMES = {
    STUB_STRCPY: "AsdString_Strcpy",
    STUB_STRCHR: "AsdString_Char",
    STUB_FORMAT: "UiText_Format",
    STUB_RES_LOAD: "AsdRes_Load",
    STUB_ALLOC_FLAGS: "AsdMem_AllocFlags",
}

ADDR_GLOBAL = 0x0044EA28
RODATA_BASE = 0x18000000
PTR_GROUPS = 0x20000000
PTR_PATHS = 0x20001000
PTR_FILE = 0x20004000
PTR_HEAP_BASE = 0x20010000
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


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def _stub_address(symbol_name: str) -> int | None:
    for addr, name in STUB_NAMES.items():
        if name in symbol_name:
            return addr
    return None


def _read_elf_section(obj_file: Path, sec_name: str) -> bytes:
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    str_sh_off = e_shoff + e_shstrndx * e_shentsize
    shstr_off, shstr_sz = struct.unpack_from("<II", data, str_sh_off + 16)
    shstr = data[shstr_off : shstr_off + shstr_sz]
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh_name, _sh_type, _flags, _addr, sh_offset, sh_size = struct.unpack_from("<6I", data, off)
        name = shstr[sh_name:].split(b"\x00", 1)[0].decode("ascii", errors="replace")
        if name == sec_name:
            return data[sh_offset : sh_offset + sh_size]
    return b""


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    rodata = _read_elf_section(obj_file, ".rodata.str1.1")
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "AsdTMTexTable_func_002c5b04" in name), None)
    if candidate is None:
        raise RuntimeError(f"AsdTMTexTable_func_002c5b04 not found in {obj_file}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        off = rel.offset
        sym_name = rel.symbol_name
        rtype = rel.relocation_type
        if rtype in (28, 29):
            dst = _stub_address(sym_name)
            if dst is None:
                raise RuntimeError(f"Unhandled call relocation: {sym_name}")
            pc = FUNC_ADDR + off + 8
            disp = ((dst - pc) >> 2) & 0x00FFFFFF
            insn = struct.unpack_from("<I", code, off)[0]
            struct.pack_into("<I", code, off, (insn & 0xFF000000) | disp)
        elif rtype == 2:
            if "g_AsdTMTexTable" in sym_name:
                struct.pack_into("<I", code, off, ADDR_GLOBAL)
            elif sym_name == "":
                addend = struct.unpack_from("<I", code, off)[0]
                struct.pack_into("<I", code, off, RODATA_BASE + addend)
            else:
                raise RuntimeError(f"Unhandled ABS32 relocation: {sym_name}")
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code), rodata


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "asd_texture.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"asd_texture_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"asd_texture_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


def build_ttd(entries: list[int], refs: list[tuple[int, int]]) -> bytes:
    node_off = 0x40
    node_count = 2
    entry_off = node_off + node_count * 0x50
    ref_off = entry_off + len(entries) * 0x14
    data_off = ref_off + len(refs) * 0x10
    total = data_off + 0x40

    buf = bytearray(total)
    buf[4:11] = b"texgrp\x00"
    struct.pack_into("<I", buf, 0x14, node_off)
    struct.pack_into("<I", buf, 0x1C, entry_off)
    struct.pack_into("<i", buf, 0x20, len(entries))
    struct.pack_into("<I", buf, 0x24, ref_off)
    struct.pack_into("<i", buf, 0x28, len(refs))
    struct.pack_into("<I", buf, 0x2C, data_off)

    for i, node_idx in enumerate(entries):
        struct.pack_into("<I", buf, entry_off + i * 0x14 + 0x0C, node_idx)
    for i, (e_idx, d_off) in enumerate(refs):
        struct.pack_into("<I", buf, ref_off + i * 0x10 + 0x00, e_idx)
        struct.pack_into("<I", buf, ref_off + i * 0x10 + 0x08, d_off)
    return bytes(buf)


def read_cstr(uc: unicorn.Uc, addr: int) -> str:
    out = bytearray()
    while len(out) < 512:
        b = uc.mem_read(addr + len(out), 1)[0]
        if b == 0:
            break
        out.append(b)
    return out.decode("ascii", errors="replace")


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(RODATA_BASE, 0x00010000)
        self.uc.mem_map(PTR_GROUPS, 0x00030000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        rodata: bytes,
        *,
        existing_table: int,
        flags: int,
        res_load_ok: bool,
        entries: list[int],
        refs: list[tuple[int, int]],
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)
        if rodata:
            uc.mem_write(RODATA_BASE, rodata)

        uc.mem_write(ADDR_GLOBAL, struct.pack("<II", PTR_GROUPS, PTR_PATHS))
        uc.mem_write(PTR_GROUPS, b"\x00" * 0x20000)
        group_id = 1
        entry_addr = PTR_GROUPS + group_id * 0x18
        ebuf = bytearray(0x18)
        struct.pack_into("<I", ebuf, 0, existing_table)
        ebuf[8:11] = b"ui\x00"
        uc.mem_write(entry_addr, bytes(ebuf))

        pbuf = bytearray(0x100)
        pbuf[0:10] = b"data\\tex\\\x00"
        pbuf[0x80:0x89] = b"sub\\dir\\\x00"
        uc.mem_write(PTR_PATHS, bytes(pbuf))

        ttd_bytes = build_ttd(entries, refs) if res_load_ok else b""
        if ttd_bytes:
            uc.mem_write(PTR_FILE, ttd_bytes)

        heap = [PTR_HEAP_BASE]
        allocs: list[tuple[int, int]] = []
        load_flags: list[int] = []
        formatted: list[str] = []

        def ret_arm(val: int | None = None) -> None:
            if val is not None:
                uc.reg_write(arm.UC_ARM_REG_R0, val & 0xFFFFFFFF)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            cpsr = uc.reg_read(arm.UC_ARM_REG_CPSR)
            uc.reg_write(arm.UC_ARM_REG_CPSR, cpsr & ~0x20)
            uc.reg_write(arm.UC_ARM_REG_PC, lr & ~1)

        def on_code(uc_inst: unicorn.Uc, address: int, _size: int, _user: object) -> None:
            if address == STUB_STRCPY:
                dst = uc_inst.reg_read(arm.UC_ARM_REG_R0)
                src = uc_inst.reg_read(arm.UC_ARM_REG_R1)
                s = read_cstr(uc_inst, src).encode("ascii") + b"\x00"
                uc_inst.mem_write(dst, s)
                ret_arm(dst)
            elif address == STUB_STRCHR:
                s_ptr = uc_inst.reg_read(arm.UC_ARM_REG_R0)
                ch = uc_inst.reg_read(arm.UC_ARM_REG_R1) & 0xFF
                s = uc_inst.mem_read(s_ptr, 256)
                nul = s.find(0)
                if nul != -1:
                    s = s[:nul]
                idx = s.find(ch)
                ret_arm(s_ptr + idx if idx != -1 else 0)
            elif address == STUB_FORMAT:
                dst = uc_inst.reg_read(arm.UC_ARM_REG_R0)
                fmt = read_cstr(uc_inst, uc_inst.reg_read(arm.UC_ARM_REG_R1))
                a0 = read_cstr(uc_inst, uc_inst.reg_read(arm.UC_ARM_REG_R2))
                a1 = read_cstr(uc_inst, uc_inst.reg_read(arm.UC_ARM_REG_R3))
                if fmt == "%s%s.%s":
                    sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                    p2 = struct.unpack("<I", uc_inst.mem_read(sp, 4))[0]
                    a2 = read_cstr(uc_inst, p2)
                    out = f"{a0}{a1}.{a2}"
                elif fmt == "%s%s/":
                    out = f"{a0}{a1}/"
                else:
                    raise AssertionError(f"Unexpected format {fmt!r}")
                formatted.append(out)
                uc_inst.mem_write(dst, out.encode("ascii") + b"\x00")
                ret_arm(len(out))
            elif address == STUB_RES_LOAD:
                out_size_ptr = uc_inst.reg_read(arm.UC_ARM_REG_R1)
                load_flags.append(uc_inst.reg_read(arm.UC_ARM_REG_R2))
                if res_load_ok:
                    uc_inst.mem_write(out_size_ptr, struct.pack("<I", len(ttd_bytes)))
                    ret_arm(PTR_FILE)
                else:
                    ret_arm(0)
            elif address == STUB_ALLOC_FLAGS:
                size = uc_inst.reg_read(arm.UC_ARM_REG_R0)
                aflags = uc_inst.reg_read(arm.UC_ARM_REG_R1)
                ptr = heap[0]
                heap[0] += (size + 15) & ~15
                uc_inst.mem_write(ptr, b"\x00" * size)
                allocs.append((size, aflags))
                ret_arm(ptr)

        hooks = [uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES]
        uc.reg_write(arm.UC_ARM_REG_R0, group_id)
        uc.reg_write(arm.UC_ARM_REG_R1, flags)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            for h in hooks:
                uc.hook_del(h)

        ret_val = uc.reg_read(arm.UC_ARM_REG_R0)
        stored_table = struct.unpack("<I", uc.mem_read(entry_addr, 4))[0]
        resolved_entries: list[int] = []
        resolved_refs: list[tuple[int, int]] = []
        descs: list[tuple[int, int]] = []
        table_path = ""
        table_files = (0, 0)
        if stored_table and existing_table == 0:
            entries_ptr, f0, f1 = struct.unpack("<III", uc.mem_read(stored_table, 12))
            table_files = (f0, f1)
            table_path = read_cstr(uc, stored_table + 0x0C)
            entry_off = struct.unpack("<I", uc.mem_read(PTR_FILE + 0x1C, 4))[0]
            ref_off = struct.unpack("<I", uc.mem_read(PTR_FILE + 0x24, 4))[0]
            for i in range(len(entries)):
                resolved_entries.append(struct.unpack("<I", uc.mem_read(PTR_FILE + entry_off + i * 0x14 + 0x0C, 4))[0])
            for i in range(len(refs)):
                ni, _, doff = struct.unpack("<III", uc.mem_read(PTR_FILE + ref_off + i * 0x10, 12))
                resolved_refs.append((ni, doff))
            if entries_ptr:
                for i in range(len(refs)):
                    own, rec = struct.unpack("<II", uc.mem_read(entries_ptr + i * 0x20, 8))
                    descs.append((own, rec))

        return {
            "ret": ret_val,
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "root": read_cstr(uc, PTR_PATHS),
            "base": read_cstr(uc, PTR_PATHS + 0x80),
            "formatted": formatted,
            "load_flags": load_flags,
            "allocs": allocs,
            "stored_table": stored_table,
            "table_files": table_files,
            "table_path": table_path,
            "resolved_entries": resolved_entries,
            "resolved_refs": resolved_refs,
            "descs": descs,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in (
        "ret", "sp", "callee", "root", "base", "formatted", "load_flags",
        "allocs", "stored_table", "table_files", "table_path",
        "resolved_entries", "resolved_refs", "descs",
    ):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()

    cases = [
        ("cached", {"existing_table": 0x20005000, "flags": 0, "res_load_ok": True, "entries": [], "refs": []}),
        ("load_null", {"existing_table": 0, "flags": 7, "res_load_ok": False, "entries": [], "refs": []}),
        ("empty_refs", {"existing_table": 0, "flags": 2, "res_load_ok": True, "entries": [], "refs": []}),
        ("populated", {"existing_table": 0, "flags": 5, "res_load_ok": True, "entries": [1, 0xFFFFFFFF], "refs": [(1, 0x10), (0, 0x20)]}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, b"", **kw)
        cand_res = Runner().run(cand_bytes, cand_rodata, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_cached", "if (entry->table != nullptr) {\n        return entry->table;\n    }", ""),
        ("wrong_flags_mask", "flags & 3u", "flags & 1u"),
        ("drop_invalid_node", "if (node == 0xFFFFFFFFu) {\n            entries[i].node_offset = 0;\n        }", "if (false) {}"),
        ("wrong_entry_stride", "ref->node_index * sizeof(AsdTMTexEntry)", "ref->node_index * 16u"),
        ("wrong_desc_stride", "static_cast<u32>(header->ref_count) * 0x20u", "static_cast<u32>(header->ref_count) * 0x10u"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, kw in cases:
            if compare(Runner().run(orig_bytes, b"", **kw), Runner().run(mut_bytes, mut_rodata, **kw)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: AsdTMTexTable_func_002c5b04 (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
