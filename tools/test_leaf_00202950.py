#!/usr/bin/env python3
"""Differential test for saveLoadUI_Calc (0x00202950) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "ui" / "save_load.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_00202950"

FUNC_ADDR = 0x00202950
FUNC_SIZE = 1256

MGR_ADDR = 0x0044DE28

STUB_ALLOC = 0x002C4B84
STUB_CREATE_CALC = 0x002C5978
STUB_CREATE_DRAW = 0x002C4C00
STUB_ALLOC2 = 0x002C54F0
STUB_26B844 = 0x0026B844
STUB_2BCF58 = 0x002BCF58
STUB_26B830 = 0x0026B830
STUB_2ADB40 = 0x002ADB40
STUB_2C0B94 = 0x002C0B94
STUB_297704 = 0x00297704
STUB_2C4E28 = 0x002C4E28
STUB_2A6214 = 0x002A6214
STUB_2976AC = 0x002976AC
STUB_29A2D0 = 0x0029A2D0
STUB_2C3344 = 0x002C3344
STUB_2C32F8 = 0x002C32F8
STUB_2BDB2C = 0x002BDB2C
STUB_2BF0A8 = 0x002BF0A8
STUB_2BDAC0 = 0x002BDAC0
STUB_2B8B78 = 0x002B8B78
STUB_ZERO = 0x002C4B30

FUNC_001C8D28 = 0x001C8D28
FUNC_00214960 = 0x00214960

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_CREATE_CALC: "AsdTask_CreateCalc",
    STUB_CREATE_DRAW: "AsdTask_CreateDraw",
    STUB_ALLOC2: "engine_func_002c54f0",
    STUB_26B844: "ui_func_0026b844",
    STUB_2BCF58: "ui_func_002bcf58",
    STUB_26B830: "ui_func_0026b830",
    STUB_2ADB40: "ui_func_002adb40",
    STUB_2C0B94: "ui_func_002c0b94",
    STUB_297704: "func_00297704",
    STUB_2C4E28: "func_002c4e28",
    STUB_2A6214: "func_002a6214",
    STUB_2976AC: "func_002976ac",
    STUB_29A2D0: "func_0029a2d0",
    STUB_2C3344: "func_002c3344",
    STUB_2C32F8: "func_002c32f8",
    STUB_2BDB2C: "func_002bdb2c",
    STUB_2BF0A8: "func_002bf0a8",
    STUB_2BDAC0: "func_002bdac0",
    STUB_2B8B78: "func_002b8b78",
    STUB_ZERO: "AsdMem_Zero",
}

PTR_RODATA = 0x00500000
PTR_WORK = 0x20000000
PTR_TASK = 0x20010000
PTR_BUF_BASE = 0x20020000
PTR_SYS_BASE = 0x20030000
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


def _extract_rodata_str(obj_file: Path) -> bytes:
    data = obj_file.read_bytes()
    e_shoff, = struct.unpack_from("<I", data, 0x20)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 0x2E)
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr_off, shstr_size = sections[e_shstrndx][4], sections[e_shstrndx][5]
    shstr = data[shstr_off : shstr_off + shstr_size]
    for sh in sections:
        end = shstr.find(b"\x00", sh[0])
        name = shstr[sh[0] : end].decode("utf-8", errors="replace")
        if name == ".rodata.str1.1":
            return data[sh[4] : sh[4] + sh[5]]
    return b""


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "saveLoadUI_Calc" in name), None)
    if candidate is None:
        raise RuntimeError(f"saveLoadUI_Calc not found in {obj_file}")

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
            if "g_SaveLoadUIManager" in sym_name:
                target = MGR_ADDR + addend
            elif "func_001c8d28" in sym_name:
                target = FUNC_001C8D28 + addend
            elif "func_00214960" in sym_name:
                target = FUNC_00214960 + addend
            elif sym_name == "" or sym_name.startswith(".L.str") or sym_name == ".rodata.str1.1":
                target = PTR_RODATA + addend
            else:
                raise RuntimeError(f"Unhandled ABS32 relocation: {sym_name} +{addend:#x}")
            struct.pack_into("<I", code, off, target)
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code), _extract_rodata_str(obj_file)


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "save_load.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"save_load_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"save_load_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


def read_cstr(uc: unicorn.Uc, addr: int) -> str:
    raw = bytes(uc.mem_read(addr, 48))
    end = raw.find(b"\x00")
    return raw[:end].decode("ascii", "replace") if end >= 0 else raw.decode("ascii", "replace")


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_RODATA, 0x1000)
        self.uc.mem_map(PTR_WORK, 0x40000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(self, code: bytes, rodata: bytes, mgr_unk08: int) -> dict[str, object]:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x800)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(PTR_RODATA, b"\x00" * 0x1000)
        if rodata:
            uc.mem_write(PTR_RODATA, rodata)

        uc.mem_write(MGR_ADDR, b"\xAA" * 0x10)
        uc.mem_write(MGR_ADDR + 0x08, struct.pack("<I", mgr_unk08))
        uc.mem_write(PTR_WORK, b"\xAA" * 0x388)

        for stub_addr in STUB_NAMES:
            uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

        alloc_idx = 0
        calls: list[tuple[object, ...]] = []
        bad_writes: list[int] = []

        def on_mem_invalid(uc_cb: unicorn.Uc, access: int, addr: int, size: int, val: int, _ud: object) -> bool:
            bad_writes.append(addr)
            return False

        def on_code(uc_cb: unicorn.Uc, addr: int, size: int, _ud: object) -> None:
            nonlocal alloc_idx
            if addr not in STUB_NAMES:
                return
            r0 = uc_cb.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_cb.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_cb.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc_cb.reg_read(arm.UC_ARM_REG_R3)
            sp = uc_cb.reg_read(arm.UC_ARM_REG_SP)
            if addr == STUB_ALLOC:
                s0 = struct.unpack("<I", uc_cb.mem_read(sp, 4))[0]
                calls.append(("alloc", r0, r1, r2, r3, s0))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_WORK)
            elif addr == STUB_CREATE_CALC:
                s0, s1, s2 = struct.unpack("<III", uc_cb.mem_read(sp, 12))
                calls.append(("create_calc", read_cstr(uc_cb, r0), r1, r2, r3, s0, s1, s2))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_TASK)
            elif addr == STUB_CREATE_DRAW:
                s0, s1, s2, s3 = struct.unpack("<IIII", uc_cb.mem_read(sp, 16))
                calls.append(("create_draw", read_cstr(uc_cb, r0), r1, r2, r3, s0, s1, s2, s3))
            elif addr == STUB_ALLOC2:
                s0 = struct.unpack("<I", uc_cb.mem_read(sp, 4))[0]
                calls.append(("alloc2", r0, r1, r2, r3, s0))
                buf_ptr = PTR_BUF_BASE + alloc_idx * 0x1000
                alloc_idx += 1
                uc_cb.reg_write(arm.UC_ARM_REG_R0, buf_ptr)
            elif addr in (STUB_26B844, STUB_26B830, STUB_2C0B94):
                calls.append((STUB_NAMES[addr],))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_SYS_BASE + (addr & 0xFFF))
            elif addr == STUB_2BCF58:
                calls.append(("2bcf58", r0, r1, r2))
            elif addr == STUB_2ADB40:
                calls.append(("2adb40", r0, r1))
            elif addr == STUB_297704:
                calls.append(("297704", read_cstr(uc_cb, r0), r1, r2))
            elif addr in (STUB_2C4E28, STUB_2976AC, STUB_2B8B78, STUB_2C3344):
                calls.append((STUB_NAMES[addr], r0))
            elif addr == STUB_2A6214:
                calls.append(("2a6214", r0, r1))
            elif addr == STUB_29A2D0:
                calls.append(("29a2d0", read_cstr(uc_cb, r0), r1))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 0xCAFEBABE)
            elif addr == STUB_2C32F8:
                args = struct.unpack("<7I", uc_cb.mem_read(sp, 28))
                calls.append(("2c32f8", r0, r1, r2, r3) + args)
            elif addr == STUB_2BDB2C:
                s0 = struct.unpack("<I", uc_cb.mem_read(sp, 4))[0]
                s0f = uc_cb.reg_read(arm.UC_ARM_REG_S0)
                calls.append(("2bdb2c", r0, r1, r2, r3, s0, s0f))
            elif addr == STUB_2BF0A8:
                s0, s1 = struct.unpack("<II", uc_cb.mem_read(sp, 8))
                s0f = uc_cb.reg_read(arm.UC_ARM_REG_S0)
                calls.append(("2bf0a8", r0, r1, r2, r3, s0, s1, s0f))
            elif addr == STUB_2BDAC0:
                calls.append(("2bdac0", r0, r1, r2))
            elif addr == STUB_ZERO:
                calls.append(("zero", r0, r1))
                uc_cb.mem_write(r0, b"\x00" * r1)

        h_code = uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        h_mem = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_READ_UNMAPPED, on_mem_invalid)

        uc.reg_write(arm.UC_ARM_REG_R0, 0)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=5000)
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
            "mgr": bytes(uc.mem_read(MGR_ADDR, 0x10)),
            "work": bytes(uc.mem_read(PTR_WORK, 0x388)),
            "bad_writes": bad_writes,
        }


def compare(orig: dict[str, object], cand: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    if orig["pc"] != cand["pc"]:
        diffs.append(f"pc: orig={orig['pc']:#x} cand={cand['pc']:#x}")
    if orig["sp"] != cand["sp"]:
        diffs.append(f"sp: orig={orig['sp']:#x} cand={cand['sp']:#x}")
    if orig["callee"] != cand["callee"]:
        diffs.append("callee-saved register mismatch")
    if orig["calls"] != cand["calls"]:
        diffs.append(f"calls mismatch (orig {len(orig['calls'])} vs cand {len(cand['calls'])})")
    if orig["mgr"] != cand["mgr"]:
        diffs.append("mgr mismatch")
    if orig["work"] != cand["work"]:
        # Compare byte-by-byte to report first diff offset
        for i, (a, b) in enumerate(zip(orig["work"], cand["work"])):
            if a != b:
                diffs.append(f"work mismatch at +{i:#x} (orig={a:#x} cand={b:#x})")
                break
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()
    cases = [
        ("unk08_0", 0),
        ("unk08_deadbeef", 0xDEADBEEF),
    ]
    for label, unk08 in cases:
        orig_res = Runner().run(orig_bytes, b"", unk08)
        cand_res = Runner().run(cand_bytes, cand_rodata, unk08)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_alloc_size", '"SAVELOAD_UI C",', '"SAVELOAD_UI X",'),
        ("wrong_draw_prio", '"SAVELOAD_UI UD",\n        0x7F,', '"SAVELOAD_UI UD",\n        0x7E,'),
        ("wrong_float_30", "*reinterpret_cast<f32*>(raw + 0x20) = 30.0f;", "*reinterpret_cast<f32*>(raw + 0x20) = 15.0f;"),
        ("wrong_width_640", "*reinterpret_cast<u32*>(raw + 0x68) = 0x280;", "*reinterpret_cast<u32*>(raw + 0x68) = 0x281;"),
        ("drop_zero_2cc", "AsdMem_Zero(raw + 0x2CC, 0x80);", "// dropped"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, unk08 in cases:
            if compare(
                Runner().run(orig_bytes, b"", unk08),
                Runner().run(mut_bytes, mut_rodata, unk08),
            ):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: saveLoadUI_Calc (0x00202950) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
