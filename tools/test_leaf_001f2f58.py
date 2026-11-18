#!/usr/bin/env python3
"""Differential test for Unite_Setup (0x001f2f58) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "camp" / "unite.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_001f2f58"

FUNC_ADDR = 0x001F2F58
FUNC_SIZE = 1704

MGR_PTR = 0x0043DD68

STUB_ALLOC = 0x002C4B84
STUB_ZERO = 0x002C4B30
STUB_30F5EC = 0x0030F5EC
STUB_CREATE_CALC = 0x002C5978
STUB_CREATE_DRAW = 0x002C4C00
STUB_ALLOC_2C23F8 = 0x002C23F8
STUB_3C9EBC = 0x003C9EBC
STUB_29B18C = 0x0029B18C
STUB_ALLOC_2C34A4 = 0x002C34A4
STUB_2BCF34 = 0x002BCF34
STUB_2BCE50 = 0x002BCE50
STUB_2C5468 = 0x002C5468
STUB_2C0BA8 = 0x002C0BA8
STUB_2A0FAC = 0x002A0FAC
STUB_2A043C = 0x002A043C
STUB_2A89E4 = 0x002A89E4
STUB_29EE4C = 0x0029EE4C
STUB_2C4450 = 0x002C4450
STUB_2C3344 = 0x002C3344
STUB_2C32F8 = 0x002C32F8
STUB_2BDB2C = 0x002BDB2C
STUB_2BF030 = 0x002BF030
STUB_2BDAC0 = 0x002BDAC0
STUB_2976AC = 0x002976AC
STUB_2C5E2C = 0x002C5E2C
STUB_2972F8 = 0x002972F8
STUB_2A0DD4 = 0x002A0DD4
STUB_2B8ADC = 0x002B8ADC
STUB_294AD8 = 0x00294AD8
STUB_263E48 = 0x00263E48
STUB_2950BC = 0x002950BC
STUB_29A2D0 = 0x0029A2D0
STUB_290A4C = 0x00290A4C

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_ZERO: "AsdMem_Zero",
    STUB_30F5EC: "func_0030f5ec",
    STUB_CREATE_CALC: "AsdTask_CreateCalc",
    STUB_CREATE_DRAW: "AsdTask_CreateDraw",
    STUB_ALLOC_2C23F8: "AsdMemory_func_002c23f8",
    STUB_3C9EBC: "func_003c9ebc",
    STUB_29B18C: "func_0029b18c",
    STUB_ALLOC_2C34A4: "engine_func_002c34a4",
    STUB_2BCF34: "func_002bcf34",
    STUB_2BCE50: "func_002bce50",
    STUB_2C5468: "func_002c5468",
    STUB_2C0BA8: "func_002c0ba8",
    STUB_2A0FAC: "func_002a0fac",
    STUB_2A043C: "func_002a043c",
    STUB_2A89E4: "func_002a89e4",
    STUB_29EE4C: "func_0029ee4c",
    STUB_2C4450: "func_002c4450",
    STUB_2C3344: "func_002c3344",
    STUB_2C32F8: "func_002c32f8",
    STUB_2BDB2C: "func_002bdb2c",
    STUB_2BF030: "func_002bf030",
    STUB_2BDAC0: "func_002bdac0",
    STUB_2976AC: "func_002976ac",
    STUB_2C5E2C: "func_002c5e2c",
    STUB_2972F8: "func_002972f8",
    STUB_2A0DD4: "func_002a0dd4",
    STUB_2B8ADC: "func_002b8adc",
    STUB_294AD8: "func_00294ad8",
    STUB_263E48: "func_00263e48",
    STUB_2950BC: "func_002950bc",
    STUB_29A2D0: "func_0029a2d0",
    STUB_290A4C: "func_00290a4c",
}

PTR_RODATA = 0x00500000
PTR_WORK = 0x20000000
PTR_STATE = 0x20010000
PTR_DEMON0 = 0x20011000
PTR_DEMON1 = 0x20012000
PTR_OBJ18 = 0x20013000
PTR_OBJ180 = 0x20014000
PTR_BUF4K = 0x20015000
PTR_CALC_TASK = 0x20016000
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
    candidate = next((val for name, val in funcs.items() if "Unite_Setup" in name), None)
    if candidate is None:
        raise RuntimeError(f"Unite_Setup not found in {obj_file}")

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
                target = PTR_RODATA + ro_offsets.get(".rodata.cst4", next(iter(ro_offsets.values()), 0)) + addend
            else:
                raise RuntimeError(f"Unhandled ABS32 relocation: {sym_name} +{addend:#x}")
            struct.pack_into("<I", code, off, target)
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code), bytes(ro_blob)


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "unite.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"unite_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"unite_mutant_{name}.o"
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
        self.uc.mem_map(PTR_RODATA, 0x2000)
        self.uc.mem_map(PTR_WORK, 0x20000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        rodata: bytes,
        existing_work: int,
        handle_ret: int,
        c0ba8: int,
        slot0_idx: int,
        slot0_id: int,
        slot1_idx: int,
        slot1_id: int,
        flag_0a: int,
        a0dd4: int,
        b8adc: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(PTR_RODATA, b"\x00" * 0x2000)
        if rodata:
            uc.mem_write(PTR_RODATA, rodata)

        uc.mem_write(MGR_PTR, struct.pack("<I", existing_work))
        uc.mem_write(PTR_WORK, b"\xAA" * 0x95F8)

        uc.mem_write(PTR_STATE, b"\x00" * 0x40)
        uc.mem_write(PTR_STATE + 0x1C, struct.pack("<hhHH", slot0_idx, slot1_idx, slot0_id, slot1_id))

        uc.mem_write(PTR_DEMON0, b"\x00" * 0x60)
        uc.mem_write(PTR_DEMON0 + 0x46, struct.pack("<H", 100))
        uc.mem_write(PTR_DEMON1, b"\x00" * 0x60)
        uc.mem_write(PTR_DEMON1 + 0x46, struct.pack("<H", 200))

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
            if addr == STUB_ALLOC:
                s0 = struct.unpack("<I", uc_cb.mem_read(sp, 4))[0]
                calls.append(("alloc", r0, r1, r2, r3, s0))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_WORK)
            elif addr == STUB_ZERO:
                calls.append(("zero", r0, r1))
                uc_cb.mem_write(r0, b"\x00" * r1)
            elif addr == STUB_CREATE_CALC:
                s0, s1, s2 = struct.unpack("<III", uc_cb.mem_read(sp, 12))
                calls.append(("create_calc", read_cstr(uc_cb, r0), r1, r2, r3, s0, s1, s2))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_CALC_TASK)
            elif addr == STUB_CREATE_DRAW:
                s0, s1, s2, s3 = struct.unpack("<IIII", uc_cb.mem_read(sp, 16))
                calls.append(("create_draw", read_cstr(uc_cb, r0), r1, r2, r3, s0, s1, s2, s3))
            elif addr == STUB_ALLOC_2C23F8:
                calls.append(("2c23f8", r0))
                if r0 == 0x180:
                    uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_OBJ180)
                else:
                    uc_cb.mem_write(PTR_OBJ18, b"\xAA" * 0x18)
                    uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_OBJ18)
            elif addr == STUB_3C9EBC:
                calls.append(("3c9ebc", r0))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_OBJ180 + 4)
            elif addr == STUB_29B18C:
                calls.append(("29b18c",))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 0x11223344)
            elif addr == STUB_ALLOC_2C34A4:
                s0, s1 = struct.unpack("<II", uc_cb.mem_read(sp, 8))
                calls.append(("2c34a4", r0, r1, r2, r3, s0, s1))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_BUF4K)
            elif addr == STUB_2BCF34:
                calls.append(("2bcf34", r0, r1, r2))
                uc_cb.mem_write(r0 + 0x08, struct.pack("<II", 0x100, 0x200))
            elif addr == STUB_2BCE50:
                desc = struct.unpack("<4I", uc_cb.mem_read(r1, 16))
                arg_val = struct.unpack("<I", uc_cb.mem_read(r3, 4))[0]
                s0, s1, s2, s3 = struct.unpack("<IIII", uc_cb.mem_read(sp, 16))
                calls.append(("2bce50", r0, desc, r2, arg_val, s0, s1, s2, s3))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, handle_ret)
            elif addr == STUB_2C0BA8:
                calls.append(("2c0ba8", r0))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, c0ba8)
            elif addr == STUB_2A0FAC:
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_STATE)
            elif addr == STUB_2A89E4:
                calls.append(("2a89e4", r0))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_DEMON0 if r0 == 0 else PTR_DEMON1)
            elif addr == STUB_29EE4C:
                calls.append(("29ee4c", r0, r1))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, flag_0a if r1 == 0x0A else 0)
            elif addr in (STUB_2C4450, STUB_2BDB2C, STUB_2BDAC0):
                if addr == STUB_2BDB2C:
                    s0 = struct.unpack("<I", uc_cb.mem_read(sp, 4))[0]
                    s0f = uc_cb.reg_read(arm.UC_ARM_REG_S0)
                    calls.append(("2bdb2c", r0, r1, r2, r3, s0, s0f))
                else:
                    calls.append((STUB_NAMES[addr], r0, r1, r2))
            elif addr == STUB_2C32F8:
                args = struct.unpack("<7I", uc_cb.mem_read(sp, 28))
                calls.append(("2c32f8", r0, r1, r2, r3) + args)
            elif addr in (STUB_2C5E2C, STUB_263E48):
                calls.append((STUB_NAMES[addr], read_cstr(uc_cb, r0)))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 0x5000 + (addr & 0xFFF))
            elif addr == STUB_29A2D0:
                calls.append(("29a2d0", read_cstr(uc_cb, r0), r1))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 0x6000 + len(read_cstr(uc_cb, r0)))
            elif addr == STUB_2A0DD4:
                uc_cb.reg_write(arm.UC_ARM_REG_R0, a0dd4)
            elif addr == STUB_2B8ADC:
                uc_cb.reg_write(arm.UC_ARM_REG_R0, b8adc)
            elif addr == STUB_294AD8:
                floats = [uc_cb.reg_read(getattr(arm, f"UC_ARM_REG_S{i}")) for i in range(9)]
                st = struct.unpack("<8I", uc_cb.mem_read(sp, 32))
                calls.append(("294ad8", r0, r1, r2, r3, tuple(floats), st))
            elif addr == STUB_290A4C:
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 0x77778888)
            elif addr == STUB_2972F8:
                calls.append(("2972f8", r0, r1))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 0x9999AAAA)
            elif addr in (STUB_2C5468, STUB_2950BC):
                calls.append((STUB_NAMES[addr], r0))
            elif addr == STUB_2A043C:
                calls.append((STUB_NAMES[addr],))
            else:
                calls.append((STUB_NAMES[addr], r0, r1))

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
            "state": bytes(uc.mem_read(PTR_STATE, 0x38)),
            "work_41c": bytes(uc.mem_read(PTR_WORK + 0x41C, 0x20)),
            "work_tail": bytes(uc.mem_read(PTR_WORK + 0x9460, 0x198)),
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
    if orig["state"] != cand["state"]:
        diffs.append("state mismatch")
    if orig["work_41c"] != cand["work_41c"]:
        diffs.append("work_41c mismatch")
    if orig["work_tail"] != cand["work_tail"]:
        diffs.append("work_tail mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()
    cases = [
        ("fresh_null", 0, 0x80000001, 0, -1, 0, -1, 0, 0, 1, 0),
        ("existing_valid", PTR_WORK, 0x80600001, 1, 0, 100, 1, 200, 0, 0, 1),
        ("existing_bad_ids", PTR_WORK, 0, 1, 0, 999, 1, 999, 1, 0, 0),
    ]
    for label, ex, hret, c0, s0i, s0d, s1i, s1d, f0a, a0d, b8a in cases:
        orig_res = Runner().run(orig_bytes, b"", ex, hret, c0, s0i, s0d, s1i, s1d, f0a, a0d, b8a)
        cand_res = Runner().run(cand_bytes, cand_rodata, ex, hret, c0, s0i, s0d, s1i, s1d, f0a, a0d, b8a)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_handle_mask", "(handle & 0x07E00000) != 0x00600000", "(handle & 0x07E00000) == 0x00600000"),
        ("wrong_c0ba8", "if (func_002c0ba8(0x418) == 0)", "if (false)"),
        ("wrong_294ad8_f", "0.0f, -1.0f, -565.0f,", "0.0f, -1.0f, -500.0f,"),
        ("wrong_mido_str", '"camp/jakyou_all_mido.bam"', '"camp/jakyou_all_x.bam"'),
        ("drop_41c", "*reinterpret_cast<u32*>(work + 0x41C) = func_00290a4c();", "// dropped"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, ex, hret, c0, s0i, s0d, s1i, s1d, f0a, a0d, b8a in cases:
            if compare(
                Runner().run(orig_bytes, b"", ex, hret, c0, s0i, s0d, s1i, s1d, f0a, a0d, b8a),
                Runner().run(mut_bytes, mut_rodata, ex, hret, c0, s0i, s0d, s1i, s1d, f0a, a0d, b8a),
            ):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: Unite_Setup (0x001f2f58) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
