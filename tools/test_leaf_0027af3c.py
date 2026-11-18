#!/usr/bin/env python3
"""Differential test for script_vm_func_0027af3c (0x0027af3c) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_0027af3c"

FUNC_ADDR = 0x0027AF3C
FUNC_SIZE = 452

STUB_267420 = 0x00267420
STUB_NAMES = {STUB_267420: "battle_func_00267420"}

RODATA_BASE = 0x18000000
ADDR_GLOBAL = 0x00447A48
PTR_ARR = 0x20000000
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


def _layout_rodata(obj_file: Path) -> tuple[bytes, dict[int, int]]:
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    raw_secs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = raw_secs[e_shstrndx][4]
    names = [data[shstr_off + s[0] : data.index(b"\x00", shstr_off + s[0])].decode("ascii", errors="replace") for s in raw_secs]

    image = bytearray()
    sec_addr: dict[int, int] = {}
    for i, s in enumerate(raw_secs):
        if s[1] == 1 and (s[2] & 2) and not names[i].startswith(".text"):
            align = max(s[8], 1)
            while len(image) % align:
                image.append(0)
            sec_addr[i] = RODATA_BASE + len(image)
            image.extend(data[s[4] : s[4] + s[5]])

    for i, s in enumerate(raw_secs):
        if s[1] == 9 and s[7] in sec_addr:
            target_off = sec_addr[s[7]] - RODATA_BASE
            symtab = raw_secs[s[6]]
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if r_type == 2:
                    st_shndx = struct.unpack_from("<H", data, symtab[4] + sym_idx * 16 + 14)[0]
                    if st_shndx in sec_addr:
                        val = struct.unpack_from("<I", image, target_off + r_off)[0]
                        struct.pack_into("<I", image, target_off + r_off, sec_addr[st_shndx] + val)

    return bytes(image), sec_addr


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    rodata, sec_addr = _layout_rodata(obj_file)
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    raw_secs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = raw_secs[e_shstrndx][4]
    names = [data[shstr_off + s[0] : data.index(b"\x00", shstr_off + s[0])].decode("ascii", errors="replace") for s in raw_secs]
    tidx = next(i for i, n in enumerate(names) if n.startswith(".text"))
    rel_sec = next(s for s in raw_secs if s[1] == 9 and s[7] == tidx)
    symtab = raw_secs[rel_sec[6]]
    strtab = raw_secs[symtab[6]]
    fn_off = 0
    for k in range(symtab[5] // 16):
        st_name, st_val, _sz, _inf, _oth, st_sh = struct.unpack_from("<IIIBBH", data, symtab[4] + k * 16)
        if st_sh == tidx:
            nm = data[strtab[4] + st_name : data.index(b"\x00", strtab[4] + st_name)].decode("ascii", errors="replace")
            if "script_vm_func_0027af3c" in nm:
                fn_off = st_val
                break
    rel_sym_shndx = {
        struct.unpack_from("<I", data, rel_sec[4] + k * 8)[0] - fn_off: struct.unpack_from("<H", data, symtab[4] + (struct.unpack_from("<I", data, rel_sec[4] + k * 8 + 4)[0] >> 8) * 16 + 14)[0]
        for k in range(rel_sec[5] // 8)
    }

    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "script_vm_func_0027af3c" in name), None)
    if candidate is None:
        raise RuntimeError(f"script_vm_func_0027af3c not found in {obj_file}")

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
            shndx = rel_sym_shndx[off]
            if shndx in sec_addr:
                addend = struct.unpack_from("<I", code, off)[0]
                struct.pack_into("<I", code, off, sec_addr[shndx] + addend)
            elif shndx == tidx:
                addend = struct.unpack_from("<I", code, off)[0]
                struct.pack_into("<I", code, off, FUNC_ADDR - fn_off + addend)
            else:
                raise RuntimeError(f"Unhandled ABS32 relocation: {sym_name}")
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code), rodata


    return bytes(code)


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    fs = text.index("extern \"C\" void script_vm_func_0027af3c(")
    fe = text.index("\n}\n", fs) + 3
    body = text[fs:fe]
    if body.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"leaf_batch45_b_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"leaf_batch45_b_mutant_{name}.o"
    mutant_src.write_text(text[:fs] + body.replace(old, new, 1) + text[fe:], encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(RODATA_BASE, 0x00010000)
        self.uc.mem_map(PTR_ARR, 0x00010000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(self, code: bytes, rodata: bytes, *, items: list[tuple[int, int, int]]) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)
        if rodata:
            uc.mem_write(RODATA_BASE, rodata)

        uc.mem_write(ADDR_GLOBAL, struct.pack("<I", PTR_ARR))
        uc.mem_write(PTR_ARR, b"\x00" * (24 * 40))
        for idx, (flag, kind, arg0) in enumerate(items):
            off = idx * 40 + 0x1C
            uc.mem_write(PTR_ARR + off, bytes([flag]))
            uc.mem_write(PTR_ARR + off + 4, struct.pack("<ffff", 1.0 + idx, 2.0, 3.0, 4.0))
            uc.mem_write(PTR_ARR + off + 0x16, struct.pack("<H", kind))
            uc.mem_write(PTR_ARR + off + 0x1C, struct.pack("<h", arg0))

        calls: list[tuple[object, ...]] = []

        def ret_arm() -> None:
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            uc.reg_write(arm.UC_ARM_REG_PC, lr & ~1)

        def on_code(uc_inst: unicorn.Uc, _address: int, _size: int, _user: object) -> None:
            r0 = struct.unpack("<i", struct.pack("<I", uc_inst.reg_read(arm.UC_ARM_REG_R0)))[0]
            floats = tuple(
                round(struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(getattr(arm, f"UC_ARM_REG_S{k}"))))[0], 2)
                for k in range(7)
            )
            calls.append((r0, floats))
            ret_arm()

        h = uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_267420, end=STUB_267420)
        uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            uc.hook_del(h)

        return {
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("sp", "callee", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()

    cases = [
        ("all_inactive", {"items": [(0, 0x10, 1), (0, 0x0A, 2)]}),
        ("all_kinds", {"items": [
            (1, 0x10, -5),
            (1, 0x0A, 10),
            (1, 0x0B, 20),
            (1, 0x0C, 30),
            (1, 0x17, 40),
            (1, 0x15, 50),
            (1, 0x14, 60),
            (1, 0x99, 70),
            (0, 0x10, 80),
        ]}),
        ("last_slot_23", {"items": [(0, 0, 0)] * 23 + [(1, 0x14, 99)]}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, b'', **kw)
        cand_res = Runner().run(cand_bytes, cand_rodata, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_flag_check", "if (elem[0] == 0) {\n            continue;\n        }", ""),
        ("wrong_loop_bound", "i < 24", "i < 23"),
        ("wrong_0a_p4", "1000.0f, 300.0f, 15.0f", "500.0f, 300.0f, 15.0f"),
        ("wrong_17_p4", "1100.0f, 600.0f, 60.0f", "1000.0f, 600.0f, 60.0f"),
        ("wrong_14_p6", "600.0f, 600.0f, 80.0f", "600.0f, 600.0f, 60.0f"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, kw in cases:
            if compare(Runner().run(orig_bytes, b'', **kw), Runner().run(mut_bytes, mut_rodata, **kw)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: script_vm_func_0027af3c (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
