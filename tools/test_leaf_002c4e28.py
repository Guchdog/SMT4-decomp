#!/usr/bin/env python3
"""Differential test for AsdTMTexTable_func_002c4e28 (0x002c4e28) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_002c4e28"

FUNC_ADDR = 0x002C4E28
FUNC_SIZE = 620

STUB_LOAD_TABLE = 0x002C5B04
STUB_STRCPY = 0x002BF86C
STUB_STRCHR = 0x0010024C
STUB_FORMAT = 0x002BE7FC
STUB_RES_LOAD = 0x002C32F0
STUB_ALLOC = 0x002C4B84
STUB_COPY_LARGE = 0x002BCF58
STUB_FREE = 0x002C4360

STUB_NAMES = {
    STUB_LOAD_TABLE: "AsdTMTexTable_func_002c5b04",
    STUB_STRCPY: "AsdString_Strcpy",
    STUB_STRCHR: "AsdString_Char",
    STUB_FORMAT: "UiText_Format",
    STUB_RES_LOAD: "AsdRes_Load",
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_COPY_LARGE: "AsdMem_CopyLarge",
    STUB_FREE: "AsdMem_Free",
}

ADDR_GLOBAL = 0x0044EA28
RODATA_BASE = 0x18000000
PTR_GROUPS = 0x20000000
PTR_PATHS = 0x20001000
PTR_GROUP_NAME = 0x20002000
PTR_TABLE = 0x20003000
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
    candidate = next((val for name, val in funcs.items() if "AsdTMTexTable_func_002c4e28" in name), None)
    if candidate is None:
        raise RuntimeError(f"AsdTMTexTable_func_002c4e28 not found in {obj_file}")

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


def build_tgd(records: list[tuple[int, int, int]]) -> bytes:
    buf = bytearray(0x40)
    for i in range(16):
        struct.pack_into("<I", buf, i * 4, 0x1000 + i)
    struct.pack_into("<i", buf, 0x20, len(records))
    for f0, icnt, f8 in records:
        rec = bytearray(0x0C + icnt * 20)
        rec[0] = f0 & 0xFF
        rec[4] = icnt & 0xFF
        rec[8] = f8 & 0xFF
        for j in range(icnt * 20):
            rec[0x0C + j] = (j + 1) & 0xFF
        buf.extend(rec)
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
        table_ret: int,
        existing_group: int,
        res_load_ok: bool,
        records: list[tuple[int, int, int]],
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
        struct.pack_into("<II", uc_buf := bytearray(0x18), 0, 0, existing_group)
        uc_buf[8:11] = b"ui\x00"
        uc.mem_write(entry_addr, bytes(uc_buf))
        uc.mem_write(PTR_PATHS, b"data\\tex\\\x00" + b"\x00" * 0x70)

        tgd_bytes = build_tgd(records) if res_load_ok else b""
        if tgd_bytes:
            uc.mem_write(PTR_FILE, tgd_bytes)

        heap = [PTR_HEAP_BASE]
        allocs: list[tuple[int, int]] = []
        freed: list[int] = []
        formatted: list[str] = []

        def ret_arm(val: int | None = None) -> None:
            if val is not None:
                uc.reg_write(arm.UC_ARM_REG_R0, val & 0xFFFFFFFF)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            cpsr = uc.reg_read(arm.UC_ARM_REG_CPSR)
            uc.reg_write(arm.UC_ARM_REG_CPSR, cpsr & ~0x20)
            uc.reg_write(arm.UC_ARM_REG_PC, lr & ~1)

        def on_code(uc_inst: unicorn.Uc, address: int, _size: int, _user: object) -> None:
            if address == STUB_LOAD_TABLE:
                ret_arm(table_ret)
            elif address == STUB_STRCPY:
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
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                p2, p3 = struct.unpack("<II", uc_inst.mem_read(sp, 8))
                a2 = read_cstr(uc_inst, p2)
                a3 = read_cstr(uc_inst, p3)
                assert fmt == "%s%s%s.%s", f"Unexpected format {fmt!r}"
                out = f"{a0}{a1}{a2}.{a3}"
                formatted.append(out)
                uc_inst.mem_write(dst, out.encode("ascii") + b"\x00")
                ret_arm(len(out))
            elif address == STUB_RES_LOAD:
                out_size_ptr = uc_inst.reg_read(arm.UC_ARM_REG_R1)
                if res_load_ok:
                    uc_inst.mem_write(out_size_ptr, struct.pack("<I", len(tgd_bytes)))
                    ret_arm(PTR_FILE)
                else:
                    ret_arm(0)
            elif address == STUB_ALLOC:
                size = uc_inst.reg_read(arm.UC_ARM_REG_R3)
                ptr = heap[0]
                heap[0] += (size + 15) & ~15
                uc_inst.mem_write(ptr, b"\x00" * size)
                allocs.append((ptr, size))
                ret_arm(ptr)
            elif address == STUB_COPY_LARGE:
                dst = uc_inst.reg_read(arm.UC_ARM_REG_R0)
                src = uc_inst.reg_read(arm.UC_ARM_REG_R1)
                size = uc_inst.reg_read(arm.UC_ARM_REG_R2)
                uc_inst.mem_write(dst, bytes(uc_inst.mem_read(src, size)))
                ret_arm(None)
            elif address == STUB_FREE:
                freed.append(uc_inst.reg_read(arm.UC_ARM_REG_R0))
                ret_arm(None)

        hooks = [uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES]
        uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.reg_write(arm.UC_ARM_REG_R0, group_id)
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
        group_ptr = struct.unpack("<I", uc.mem_read(entry_addr + 4, 4))[0]
        parsed_recs = []
        if group_ptr and existing_group == 0:
            hdr_ptr, cur = struct.unpack("<II", uc.mem_read(group_ptr, 8))
            hdr = bytes(uc.mem_read(hdr_ptr, 0x40))
            while cur:
                f0, icnt, f8, items_ptr, nxt = struct.unpack("<IIb3xII", uc.mem_read(cur, 0x14))
                items = bytes(uc.mem_read(items_ptr, icnt * 20)) if items_ptr and icnt > 0 else b""
                parsed_recs.append((f0, icnt, f8, items))
                cur = nxt
        else:
            hdr = b""

        return {
            "ret": ret_val,
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "root": read_cstr(uc, PTR_PATHS),
            "formatted": formatted,
            "group_ptr": group_ptr,
            "hdr": hdr,
            "recs": parsed_recs,
            "alloc_sizes": [s for _, s in allocs],
            "freed": freed,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("ret", "sp", "callee", "root", "formatted", "group_ptr", "hdr", "recs", "alloc_sizes", "freed"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()

    cases = [
        ("table_null", {"table_ret": 0, "existing_group": 0, "res_load_ok": True, "records": []}),
        ("group_cached", {"table_ret": PTR_TABLE, "existing_group": 0x20005000, "res_load_ok": True, "records": []}),
        ("load_null", {"table_ret": PTR_TABLE, "existing_group": 0, "res_load_ok": False, "records": []}),
        ("rec0", {"table_ret": PTR_TABLE, "existing_group": 0, "res_load_ok": True, "records": []}),
        ("rec2_mixed", {"table_ret": PTR_TABLE, "existing_group": 0, "res_load_ok": True, "records": [(11, 2, 13), (7, 0, 9)]}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, b"", **kw)
        cand_res = Runner().run(cand_bytes, cand_rodata, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_table_null", "if (table == nullptr) {\n        return nullptr;\n    }", ""),
        ("drop_cached_guard", "if (entry->group != nullptr) {\n        return table;\n    }", ""),
        ("drop_normalize", "AsdTMTex_NormalizeSlashes(path);\n    AsdString_Strcpy(g_AsdTMTexTable.paths->root, path);\n\n    UiText_Format", "AsdString_Strcpy(g_AsdTMTexTable.paths->root, path);\n\n    UiText_Format"),
        ("wrong_item_stride", "const u32 item_bytes = record->item_count * 20u;", "const u32 item_bytes = record->item_count * 16u;"),
        ("wrong_rec_advance", "record_data += 0x0C + record->item_count * 20u;", "record_data += 0x0C;"),
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
        f"PASS: AsdTMTexTable_func_002c4e28 (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
