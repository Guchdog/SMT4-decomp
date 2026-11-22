#!/usr/bin/env python3
"""Differential Unicorn test for func_003f5428 (0x003f5428, 1368 B)."""

from __future__ import annotations

import struct
import sys
import tempfile
from pathlib import Path

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM, Uc
from unicorn.arm_const import (
    UC_ARM_REG_LR,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x003F5428
FUNC_SIZE = 1368
FUNC_NAME = "func_003f5428"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

GPU_ADDR = 0x00600000
TBL_ADDR = 0x00601000
AUX_ADDR = 0x00602000
IND_ADDR = 0x00602200
HANDLES_ADDR = 0x00603000
NODES_BASE = 0x00604000
OBJS_BASE = 0x00610000

G_GPU = 0x004655C0
G_TBL = 0x004655E8
G_FREE_FN = 0x0044E334
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x002BA948: "battle_func_002ba948",
    0x002BA860: "battle_func_002ba860",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_FREE = STUB_BASE + 0x100
STUB_BY_NAME["gpu_free"] = STUB_FREE
NAME_BY_STUB = {v: k for k, v in STUB_BY_NAME.items()}


def patch_cand_elf(obj_path: Path) -> tuple[bytes, list[tuple[int, bytes]], int]:
    elf = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", elf, 0x20)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", elf, 0x2E)
    sections = [struct.unpack_from("<10I", elf, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = sections[e_shstrndx][4]

    def sec_name(idx: int) -> str:
        n_off = shstr_off + sections[idx][0]
        return elf[n_off : elf.find(b"\x00", n_off)].decode("ascii", errors="replace")

    symtab = next(sh for sh in sections if sh[1] == 2)
    strtab = sections[symtab[6]]
    str_off = strtab[4]

    def sym_info(sym_idx: int) -> tuple[str, int, int]:
        s_off = symtab[4] + sym_idx * 16
        st_name, st_value, _, _, _, st_shndx = struct.unpack_from("<IIIBBH", elf, s_off)
        end = elf.find(b"\x00", str_off + st_name)
        return elf[str_off + st_name : end].decode("ascii", errors="replace"), st_value, st_shndx

    func_val = func_size = func_shndx = None
    for idx in range(symtab[5] // 16):
        name, val, shndx = sym_info(idx)
        if name == FUNC_NAME:
            s_off = symtab[4] + idx * 16
            func_size = struct.unpack_from("<I", elf, s_off + 8)[0]
            func_val, func_shndx = val, shndx
            break
    if func_val is None or func_shndx is None:
        raise RuntimeError(f"Symbol {FUNC_NAME} not found")

    text_sh = sections[func_shndx]
    text_bytes = bytearray(elf[text_sh[4] : text_sh[4] + text_sh[5]])
    text_name = sec_name(func_shndx)

    rodata_blobs: list[tuple[int, bytes]] = []
    rodata_map: dict[int, int] = {}
    cur_ro = RODATA_BASE
    for idx, sh in enumerate(sections):
        sname = sec_name(idx)
        if sh[1] == 1 and sh[5] > 0 and sname.startswith(".rodata"):
            blob = elf[sh[4] : sh[4] + sh[5]]
            rodata_map[idx] = cur_ro
            rodata_blobs.append((cur_ro, blob))
            cur_ro = (cur_ro + len(blob) + 15) & ~15

    rel_sh = None
    for idx, sh in enumerate(sections):
        if sh[1] == 9 and sh[7] == func_shndx:
            rel_sh = sh
            break
    if rel_sh is None:
        for idx, sh in enumerate(sections):
            if sh[1] == 9 and sec_name(idx) == f".rel{text_name}":
                rel_sh = sh
                break

    if rel_sh is not None:
        for off in range(0, rel_sh[5], 8):
            r_offset, r_info = struct.unpack_from("<II", elf, rel_sh[4] + off)
            r_type = r_info & 0xFF
            r_sym = r_info >> 8
            sname, sval, sshndx = sym_info(r_sym)
            if not (func_val <= r_offset < func_val + func_size) and not (
                r_type in (28, 29) and sname in STUB_BY_NAME
            ):
                continue
            if r_type in (28, 29):
                if sname in STUB_BY_NAME:
                    target = STUB_BY_NAME[sname]
                elif sshndx == func_shndx:
                    target = CODE_BASE + sval
                else:
                    raise RuntimeError(f"Unknown call target {sname}")
                insn = struct.unpack_from("<I", text_bytes, r_offset)[0]
                imm24 = ((target - (CODE_BASE + r_offset + 8)) >> 2) & 0x00FFFFFF
                struct.pack_into("<I", text_bytes, r_offset, (insn & 0xFF000000) | imm24)
            elif r_type == 2:
                addend = struct.unpack_from("<i", text_bytes, r_offset)[0]
                if sshndx in rodata_map:
                    target = rodata_map[sshndx] + sval + addend
                    struct.pack_into("<I", text_bytes, r_offset, target)
                elif sshndx == func_shndx:
                    target = CODE_BASE + sval + addend
                    struct.pack_into("<I", text_bytes, r_offset, target)
            elif r_type in (43, 44):
                if sshndx in rodata_map:
                    target = rodata_map[sshndx] + sval
                    insn = struct.unpack_from("<I", text_bytes, r_offset)[0]
                    imm16 = (target & 0xFFFF) if r_type == 43 else ((target >> 16) & 0xFFFF)
                    enc = ((imm16 & 0xF000) << 4) | (imm16 & 0x0FFF)
                    struct.pack_into("<I", text_bytes, r_offset, (insn & 0xFFF0F000) | enc)
            elif r_type == 42:
                pass
            else:
                raise RuntimeError(f"Unhandled reloc type {r_type} for {sname}")

    return bytes(text_bytes), rodata_blobs, func_val


def patch_orig_bl(code_bytes: bytearray) -> None:
    base = FUNC_ADDR - CODE_BASE
    for off in range(0, FUNC_SIZE, 4):
        insn = struct.unpack_from("<I", code_bytes, base + off)[0]
        top = (insn >> 24) & 0xFF
        if ((top & 0x0E) == 0x0A and top < 0xF0) or top in (0xFA, 0xFB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x800000:
                imm24 -= 0x1000000
            pc = FUNC_ADDR + off + 8
            target = pc + (imm24 << 2)
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target]]
                new_imm = ((stub - pc) >> 2) & 0x00FFFFFF
                op = 0xEB000000 if top in (0xFA, 0xFB) else (insn & 0xFF000000)
                struct.pack_into("<I", code_bytes, base + off, op | new_imm)


def run_case(
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry_addr: int,
    case: dict,
) -> tuple[list[tuple], bytes, bytes, bytes, int]:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STUB_BASE - 0x1000, 0x4000)
    uc.mem_map(RODATA_BASE, 0x20000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(GPU_ADDR, 0x20000)
    uc.mem_map(HALT_ADDR & ~0xFFF, 0x2000)

    uc.mem_write(CODE_BASE, code_bytes)
    for addr, blob in rodata_blobs:
        uc.mem_write(addr, blob)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    uc.mem_write(G_GPU, struct.pack("<I", GPU_ADDR))
    uc.mem_write(G_TBL, struct.pack("<II", TBL_ADDR, 0x9000))
    uc.mem_write(G_FREE_FN, struct.pack("<I", STUB_FREE))
    uc.mem_write(IND_ADDR, struct.pack("<I", AUX_ADDR))

    gpu = bytearray(0x300)
    for off in (0x5C, 0x60, 0x64, 0x68, 0x6C, 0x70, 0x74, 0x74 + 31 * 4, 0x10C, 0x10C + 32 * 4):
        struct.pack_into("<I", gpu, off, case.get("match_h", 0))
    for off in range(0x104, 0x10A):
        gpu[off] = 1
    struct.pack_into("<I", gpu, 0xF4, case.get("f4_h", 0))
    uc.mem_write(GPU_ADDR, bytes(gpu))

    tbl = bytearray(0x900)
    struct.pack_into("<I", tbl, 8, AUX_ADDR)
    struct.pack_into("<I", tbl, 0x8A8, IND_ADDR if case.get("indirect", True) else 0)
    uc.mem_write(TBL_ADDR, bytes(tbl))
    uc.mem_write(AUX_ADDR, b"\xAA" * 0x100)

    # Set up nodes: [(handle, kind, has_obj)]
    nodes = case.get("nodes", [])
    buckets: dict[int, list[tuple[int, int, bool]]] = {}
    for item in nodes:
        buckets.setdefault(item[0] & 0x1FF, []).append(item)

    node_idx = 0
    for b, items in buckets.items():
        items.sort(key=lambda x: x[0])
        prev_addr = 0
        first_addr = 0
        for h, kind, has_obj in items:
            naddr = NODES_BASE + node_idx * 0x20
            oaddr = (OBJS_BASE + node_idx * 0x900) if has_obj else 0
            if first_addr == 0:
                first_addr = naddr
            if prev_addr != 0:
                uc.mem_write(prev_addr + 0x0C, struct.pack("<I", naddr))
            uc.mem_write(naddr, struct.pack("<IIII", oaddr, kind, h, 0))
            if oaddr:
                obuf = bytearray(0x900)
                struct.pack_into("<I", obuf, 0x2C, 0x55550000 + node_idx)
                for k in range(6):
                    struct.pack_into("<I", obuf, 0x804 + k * 4, 0x880000 + k * 0x10)
                uc.mem_write(oaddr, bytes(obuf))
            prev_addr = naddr
            node_idx += 1
        uc.mem_write(TBL_ADDR + 0x10 + b * 4, struct.pack("<I", first_addr))

    handles = case.get("handles", [])
    if handles:
        uc.mem_write(HANDLES_ADDR, struct.pack(f"<{len(handles)}I", *handles))

    trace: list[tuple] = []

    def on_code(u: Uc, addr: int, _size: int, _user: object) -> None:
        if addr == HALT_ADDR:
            u.emu_stop()
            return
        name = NAME_BY_STUB.get(addr)
        if name is None:
            return
        r0 = u.reg_read(UC_ARM_REG_R0)
        r1 = u.reg_read(UC_ARM_REG_R1)
        r2 = u.reg_read(UC_ARM_REG_R2)
        r3 = u.reg_read(UC_ARM_REG_R3)
        if name == "battle_func_002ba948":
            trace.append((name, r0))
        elif name == "battle_func_002ba860":
            trace.append((name, r0, r1))
        elif name == "gpu_free":
            trace.append((name, r0, r1, r2, r3))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_ARM_REG_R0, case.get("count", len(handles)))
    uc.reg_write(UC_ARM_REG_R1, HANDLES_ADDR)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)

    min_h = struct.unpack_from("<I", uc.mem_read(G_TBL + 4, 4))[0]
    return trace, bytes(uc.mem_read(GPU_ADDR, 0x300)), bytes(uc.mem_read(TBL_ADDR, 0x900)), bytes(uc.mem_read(AUX_ADDR, 0x100)), min_h


CASES = [
    {"name": "count_0", "count": 0, "handles": []},
    {"name": "handle_0_and_missing", "handles": [0, 0x205], "nodes": [(0x005, 0, True)]},
    {"name": "kind0_head_indirect", "handles": [0x205], "match_h": 0x205, "nodes": [(0x205, 0, True)]},
    {"name": "kind1_chained_direct", "handles": [0x305], "match_h": 0x305, "indirect": False, "nodes": [(0x105, 0, True), (0x305, 1, True)]},
    {"name": "kind2_deferred_and_immediate", "handles": [0x401, 0x402], "f4_h": 0x401, "nodes": [(0x401, 2, True), (0x402, 2, True)]},
    {"name": "kind3_slots_and_subs", "handles": [0x501], "match_h": 0x501, "nodes": [(0x501, 3, True)]},
    {"name": "null_obj_unlinks", "handles": [0x601], "nodes": [(0x601, 0, False)]},
]


def compile_cand(cpp_text: str) -> tuple[bytes, list[tuple[int, bytes]], int]:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        src = td_path / "cand.cpp"
        obj = td_path / "cand.o"
        src.write_text(cpp_text, encoding="utf-8")
        compile_tu_armv6k(src, obj)
        text_bytes, rodata, func_val = patch_cand_elf(obj)
        cand_mem = bytearray(CODE_SIZE)
        cand_mem[0 : len(text_bytes)] = text_bytes
        return bytes(cand_mem), rodata, CODE_BASE + func_val


def main() -> int:
    orig_mem = bytearray(CODE_SIZE)
    raw_code = CODE_BIN.read_bytes()
    orig_mem[0 : len(raw_code)] = raw_code
    patch_orig_bl(orig_mem)
    orig_bytes = bytes(orig_mem)

    cpp_text = SRC_CPP.read_text(encoding="utf-8")
    cand_bytes, cand_ro, cand_entry = compile_cand(cpp_text)

    for case in CASES:
        ores = run_case(orig_bytes, [], FUNC_ADDR, case)
        cres = run_case(cand_bytes, cand_ro, cand_entry, case)
        if ores != cres:
            print(f"FAIL {case['name']}")
            print(f"  orig trace: {ores[0]}")
            print(f"  cand trace: {cres[0]}")
            return 1
        print(f"PASS {case['name']} ({len(ores[0])} calls)")

    muts = [
        ("neg_bucket_mask", "        const u32 bucket = h & 0x1FFu;", "        const u32 bucket = h & 0xFFu;"),
        ("neg_kind0_flag_bit", "                *reinterpret_cast<u32*>(gpu) |= (0x400u << i);", "                *reinterpret_cast<u32*>(gpu) |= (0x200u << i);"),
        ("neg_kind1_loop6", "                for (s32 j = 0; j < 6; ++j) {", "                for (s32 j = 0; j < 5; ++j) {"),
        ("neg_kind2_deferred", "                    *reinterpret_cast<u32*>(tbl + 0x0Cu) = h;\n                    continue;", "                    *reinterpret_cast<u32*>(tbl + 0x0Cu) = h;"),
        ("neg_kind3_loop21", "                for (s32 i = 0; i < 0x21; ++i) {", "                for (s32 i = 0; i < 0x20; ++i) {"),
    ]

    for mname, old, new in muts:
        assert old in cpp_text, f"Anchor missing for {mname}"
        mut_cpp = cpp_text.replace(old, new, 1)
        m_bytes, m_ro, m_entry = compile_cand(mut_cpp)
        caught = False
        for case in CASES:
            if run_case(orig_bytes, [], FUNC_ADDR, case) != run_case(m_bytes, m_ro, m_entry, case):
                caught = True
                break
        if not caught:
            print(f"FAIL negative control {mname} was not caught!")
            return 1
        print(f"PASS {mname} (caught)")

    print(f"ALL PASS: {len(CASES)} cases + {len(muts)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
