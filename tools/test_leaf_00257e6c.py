#!/usr/bin/env python3
"""Differential test for AsdTexTGA_func_00257e6c (0x00257e6c) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_00257e6c"

FUNC_ADDR = 0x00257E6C
FUNC_SIZE = 436

STUB_CMP = 0x002B45F8
STUB_ALLOC = 0x002BF798
STUB_COPY = 0x002C5FF4
STUB_MEMCLR4 = 0x003F0300

STUB_NAMES = {
    STUB_CMP: "AsdMem_Compare",
    STUB_ALLOC: "AsdWork_Alloc2",
    STUB_COPY: "AsdMem_Copy",
    STUB_MEMCLR4: "__aeabi_memclr4",
}

PTR_RODATA = 0x00500000
PTR_TEX = 0x20000000
PTR_TGA = 0x20001000
PTR_PIXELS = 0x20010000
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
    if "002b45f8" in symbol_name:
        return STUB_CMP
    if "002bf798" in symbol_name:
        return STUB_ALLOC
    if "002c5ff4" in symbol_name:
        return STUB_COPY
    for addr, name in STUB_NAMES.items():
        if name in symbol_name:
            return addr
    return None


def _extract_rodata_sections(obj_file: Path) -> dict[str, bytes]:
    data = obj_file.read_bytes()
    e_shoff, = struct.unpack_from("<I", data, 0x20)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 0x2E)
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr_off, shstr_size = sections[e_shstrndx][4], sections[e_shstrndx][5]
    shstr = data[shstr_off : shstr_off + shstr_size]
    out: dict[str, bytes] = {}
    for sh in sections:
        end = shstr.find(b"\x00", sh[0])
        name = shstr[sh[0] : end].decode("utf-8", errors="replace")
        if name.startswith(".rodata"):
            out[name] = data[sh[4] : sh[4] + sh[5]]
    return out


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "AsdTexTGA_func_00257e6c" in name), None)
    if candidate is None:
        raise RuntimeError(f"AsdTexTGA_func_00257e6c not found in {obj_file}")

    ro_secs = _extract_rodata_sections(obj_file)
    ro_blob = bytearray()
    ro_offsets: dict[str, int] = {}
    for sname, sbytes in ro_secs.items():
        ro_offsets[sname] = len(ro_blob)
        ro_blob.extend(sbytes)
        while len(ro_blob) % 16 != 0:
            ro_blob.append(0)

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
            addend = struct.unpack_from("<I", code, off)[0]
            if sym_name in ro_offsets:
                target = PTR_RODATA + ro_offsets[sym_name] + addend
            elif sym_name.startswith(".L.str") or sym_name == ".rodata.str1.1":
                target = PTR_RODATA + ro_offsets.get(".rodata.str1.1", 0) + addend
            elif sym_name == "" or sym_name.startswith(".L"):
                target = PTR_RODATA + ro_offsets.get(".rodata.str1.1", 0) + addend
            else:
                raise RuntimeError(f"Unhandled ABS32 relocation: {sym_name} +{addend:#x}")
            struct.pack_into("<I", code, off, target)
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code), bytes(ro_blob)


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


def build_tga(sig: bytes, width: int, height: int, tfm_name: bytes | None, payload: bytes) -> bytes:
    buf = bytearray(0x26)
    buf[0x0C:0x0E] = struct.pack("<H", width)
    buf[0x0E:0x10] = struct.pack("<H", height)
    buf[0x12 : 0x12 + len(sig)] = sig
    struct.pack_into("<I", buf, 0x22, 0x26)
    if payload:
        txd_sz = 0x0C + len(payload)
        buf.extend(b"nw4c_txd" + struct.pack("<I", txd_sz) + payload)
    if tfm_name is not None:
        tfm_sz = 0x0C + len(tfm_name)
        buf.extend(b"nw4c_tfm" + struct.pack("<I", tfm_sz) + tfm_name)
    buf.extend(b"nw4c_end" + struct.pack("<I", 0x0C))
    return bytes(buf)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        with open(ORIG_BIN, "rb") as handle:
            handle.seek(0x00309000)
            self.uc.mem_write(0x00409000, handle.read(0x1000))
        self.uc.mem_map(PTR_RODATA, 0x1000)
        self.uc.mem_map(PTR_TEX, 0x20000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(self, code: bytes, rodata: bytes, tga_bytes: bytes, kind: int) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x400)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(PTR_RODATA, b"\x00" * 0x1000)
        if rodata:
            uc.mem_write(PTR_RODATA, rodata)

        uc.mem_write(PTR_TEX, b"\x00" * 0x50)
        uc.mem_write(PTR_TGA, b"\x00" * 0x400)
        uc.mem_write(PTR_TGA, tga_bytes)
        uc.mem_write(PTR_PIXELS, b"\x00" * 0x100)

        for stub_addr in STUB_NAMES:
            uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

        calls: list[tuple[object, ...]] = []
        bad_writes: list[int] = []

        def on_mem_invalid(uc_cb: unicorn.Uc, access: int, addr: int, size: int, val: int, _ud: object) -> bool:
            bad_writes.append(addr)
            return False

        def on_code(uc_cb: unicorn.Uc, addr: int, size: int, _ud: object) -> None:
            if addr not in STUB_NAMES:
                return
            r0 = uc_cb.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_cb.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_cb.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc_cb.reg_read(arm.UC_ARM_REG_R3)
            sp = uc_cb.reg_read(arm.UC_ARM_REG_SP)
            if addr == STUB_CMP:
                b0 = bytes(uc_cb.mem_read(r0, r2))
                b1 = bytes(uc_cb.mem_read(r1, r2))
                res = 0 if b0 == b1 else (-1 if b0 < b1 else 1)
                uc_cb.reg_write(arm.UC_ARM_REG_R0, res & 0xFFFFFFFF)
            elif addr == STUB_ALLOC:
                s0, s1 = struct.unpack("<II", uc_cb.mem_read(sp, 8))
                calls.append(("alloc", r0, r1, r2, r3, s0, s1))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_PIXELS)
            elif addr == STUB_COPY:
                uc_cb.mem_write(r0, bytes(uc_cb.mem_read(r1, r2)))
                if r0 == PTR_PIXELS:
                    calls.append(("copy_pixels", r0, r2))
            elif addr == STUB_MEMCLR4:
                uc_cb.mem_write(r0, b"\x00" * r1)

        h_code = uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        h_mem = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_READ_UNMAPPED, on_mem_invalid)

        uc.reg_write(arm.UC_ARM_REG_R0, PTR_TEX)
        uc.reg_write(arm.UC_ARM_REG_R1, PTR_TGA)
        uc.reg_write(arm.UC_ARM_REG_R2, 0)
        uc.reg_write(arm.UC_ARM_REG_R3, kind)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=2000)
        finally:
            uc.hook_del(h_code)
            uc.hook_del(h_mem)

        callee = {
            reg_name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"))
            for reg_name in CALLEE_SAVED
        }
        return {
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": callee,
            "calls": calls,
            "tex": bytes(uc.mem_read(PTR_TEX, 0x30)),
            "pixels": bytes(uc.mem_read(PTR_PIXELS, 0x40)),
            "bad_writes": bad_writes,
        }


def compare(orig: dict[str, object], cand: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("pc", "sp", "callee", "calls", "tex", "pixels"):
        if orig[k] != cand[k]:
            diffs.append(f"{k} mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()
    cases = [
        ("bad_sig", build_tga(b"NOT_NW4C_SIG\x00\x00\x00\x00", 64, 64, b"Etc1\x00", b"\x11" * 16), 0x20000),
        ("etc1_a4", build_tga(b"NW4C_Tga Ver1.0\x00", 128, 64, b"Etc1_a4\x00", bytes(range(32))), 0x20000),
        ("etc1", build_tga(b"NW4C_Tga Ver1.0\x00", 32, 16, b"Etc1\x00", b"\xAB" * 24), 0x30000),
    ]
    for label, tga, kind in cases:
        orig_res = Runner().run(orig_bytes, b"", tga, kind)
        cand_res = Runner().run(cand_bytes, cand_rodata, tga, kind)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_sig_check", 'if (AsdMem_Compare(signature, "NW4C_Tga Ver1.0", 0x10) != 0)\n        return;', ""),
        ("wrong_format_de1", "texture->kind = texture_kind;\n    texture->format = 0xDE1;", "texture->kind = texture_kind;\n    texture->format = 0xDE2;"),
        ("wrong_txd_sz", "texture->data_size = size - 0x0Cu;", "texture->data_size = size;"),
        ("wrong_etc1_a4", 'if (AsdMem_Compare(name, "Etc1_a4", 8) == 0) {\n                texture->param = 0x1401;\n                texture->format2 = 0x675B;', 'if (AsdMem_Compare(name, "Etc1_a4", 8) == 0) {\n                texture->param = 0x1401;\n                texture->format2 = 0x675A;'),
        ("wrong_etc1", "if (AsdMem_Compare(name, etc1, 8) == 0) {\n                    texture->format2 = 0x675A;", "if (AsdMem_Compare(name, etc1, 8) == 0) {\n                    texture->format2 = 0x675B;"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, tga, kind in cases:
            if compare(
                Runner().run(orig_bytes, b"", tga, kind),
                Runner().run(mut_bytes, mut_rodata, tga, kind),
            ):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: AsdTexTGA_func_00257e6c (0x00257e6c) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
