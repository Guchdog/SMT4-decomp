#!/usr/bin/env python3
"""Differential test for script_vm_func_002900b0 (0x002900b0) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_002900b0"

FUNC_ADDR = 0x002900B0
FUNC_SIZE = 428

STUB_28EFE0 = 0x0028EFE0
STUB_385EDC = 0x00385EDC
STUB_2BE7FC = 0x002BE7FC
STUB_2C5E2C = 0x002C5E2C
STUB_296D8C = 0x00296D8C
STUB_241D70 = 0x00241D70
STUB_333910 = 0x00333910
STUB_2B6700 = 0x002B6700
STUB_2BD1B0 = 0x002BD1B0
STUB_296DE0 = 0x00296DE0
STUB_29025C = 0x0029025C

STUB_NAMES = {
    STUB_28EFE0: "script_vm_func_0028efe0",
    STUB_385EDC: "script_vm_func_00385edc",
    STUB_2BE7FC: "ui_func_002be7fc",
    STUB_2C5E2C: "script_vm_func_002c5e2c",
    STUB_296D8C: "script_vm_func_00296d8c",
    STUB_241D70: "script_vm_func_00241d70",
    STUB_333910: "script_vm_func_00333910",
    STUB_2B6700: "script_vm_func_002b6700",
    STUB_2BD1B0: "script_vm_func_002bd1b0",
    STUB_296DE0: "AsdText_func_00296de0",
    STUB_29025C: "script_vm_func_0029025c",
}

ADDR_QUEST_GLOBAL = 0x0043DD50
ADDR_BUNDLE_GLOBAL = 0x00433158
RODATA_BASE = 0x18000000
PTR_QUEST_WORK = 0x20000000
PTR_BUNDLE = 0x20002000
PTR_ROW = 0x20003000
PTR_TEXT_STR = 0x20004000
PTR_LOADED_MBM = 0x20020000
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
    candidate = next((val for name, val in funcs.items() if "script_vm_func_002900b0" in name), None)
    if candidate is None:
        raise RuntimeError(f"script_vm_func_002900b0 not found in {obj_file}")

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
            if sym_name == "":
                addend = struct.unpack_from("<I", code, off)[0]
                struct.pack_into("<I", code, off, RODATA_BASE + addend)
            else:
                raise RuntimeError(f"Unhandled ABS32 relocation: {sym_name}")
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code), rodata


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    fs = text.index("extern \"C\" void script_vm_func_002900b0(")
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


def read_cstr(uc: unicorn.Uc, addr: int) -> str:
    out = bytearray()
    while len(out) < 128:
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
        self.uc.mem_map(PTR_QUEST_WORK, 0x00030000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        rodata: bytes,
        *,
        quest_id: int,
        mode: int,
        mbm_ret: int,
        sub_ret: int,
        msg_ret: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)
        if rodata:
            uc.mem_write(RODATA_BASE, rodata)

        uc.mem_write(ADDR_QUEST_GLOBAL, struct.pack("<I", PTR_QUEST_WORK))
        uc.mem_write(ADDR_BUNDLE_GLOBAL, struct.pack("<I", PTR_BUNDLE))
        uc.mem_write(PTR_QUEST_WORK, b"\x00" * 0x600)
        struct.pack_into(
            "<IIIII",
            qbuf := bytearray(20),
            0,
            0x20005001,  # +0x5D4
            0x20005002,  # +0x5D8
            0x20005003,  # +0x5DC
            0x20005004,  # +0x5E0
            0x20005005,  # +0x5E4
        )
        uc.mem_write(PTR_QUEST_WORK + 0x5D4, bytes(qbuf))
        uc.mem_write(PTR_QUEST_WORK + 0x5F7, b"\xAA")
        uc.mem_write(PTR_TEXT_STR, b"QuestDesc\x00")

        calls: list[tuple[str, tuple[object, ...]]] = []

        def ret_arm(val: int | None = None) -> None:
            if val is not None:
                uc.reg_write(arm.UC_ARM_REG_R0, val & 0xFFFFFFFF)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            cpsr = uc.reg_read(arm.UC_ARM_REG_CPSR)
            uc.reg_write(arm.UC_ARM_REG_CPSR, cpsr & ~0x20)
            uc.reg_write(arm.UC_ARM_REG_PC, lr & ~1)

        def on_code(uc_inst: unicorn.Uc, address: int, _size: int, _user: object) -> None:
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(arm.UC_ARM_REG_R3)
            if address == STUB_28EFE0:
                calls.append(("28efe0", (r0, r1, r2)))
                ret_arm(None)
            elif address == STUB_385EDC:
                calls.append(("385edc", (r0, r1)))
                ret_arm(mbm_ret)
            elif address == STUB_2BE7FC:
                fmt = read_cstr(uc_inst, r1)
                assert fmt == "event/quest/quest%03d.mbm", f"Unexpected fmt {fmt!r}"
                out = f"event/quest/quest{r2:03d}.mbm"
                uc_inst.mem_write(r0, out.encode("ascii") + b"\x00")
                calls.append(("format", (out,)))
                ret_arm(len(out))
            elif address == STUB_2C5E2C:
                calls.append(("2c5e2c", (read_cstr(uc_inst, r0),)))
                ret_arm(PTR_LOADED_MBM)
            elif address == STUB_296D8C:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                a4, a5, a6 = struct.unpack("<III", uc_inst.mem_read(sp, 12))
                calls.append(("296d8c", (r0, r1, r2, r3, a4, a5, a6)))
                ret_arm(None)
            elif address == STUB_241D70:
                calls.append(("241d70", (r0,)))
                ret_arm(sub_ret)
            elif address == STUB_333910:
                calls.append(("333910", (r0, r1)))
                ret_arm(msg_ret)
            elif address == STUB_2B6700:
                calls.append(("2b6700", (r0,)))
                ret_arm(PTR_ROW)
            elif address == STUB_2BD1B0:
                calls.append(("2bd1b0", (r0, r1)))
                ret_arm(PTR_TEXT_STR)
            elif address == STUB_296DE0:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                a4, fmt_ptr, str_ptr = struct.unpack("<III", uc_inst.mem_read(sp, 12))
                calls.append(("296de0", (r0, r1, r2, r3, a4, read_cstr(uc_inst, fmt_ptr), read_cstr(uc_inst, str_ptr))))
                ret_arm(None)
            elif address == STUB_29025C:
                calls.append(("29025c", (r0,)))
                ret_arm(None)

        hooks = [uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES]
        uc.reg_write(arm.UC_ARM_REG_R0, quest_id)
        uc.reg_write(arm.UC_ARM_REG_R1, mode)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            for h in hooks:
                uc.hook_del(h)

        f5e0 = struct.unpack("<I", uc.mem_read(PTR_QUEST_WORK + 0x5E0, 4))[0]
        f5f7 = uc.mem_read(PTR_QUEST_WORK + 0x5F7, 1)[0]
        return {
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "f5e0": f5e0,
            "f5f7": f5f7,
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("sp", "callee", "f5e0", "f5f7", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()

    cases = [
        ("quest_zero", {"quest_id": 0, "mode": 1, "mbm_ret": 0, "sub_ret": 0, "msg_ret": 0}),
        ("mbm_cached_sub_pos_msg_neg", {"quest_id": 7, "mode": 1, "mbm_ret": 0x20010000, "sub_ret": 5, "msg_ret": -1}),
        ("mbm_load_sub_zero_msg_pos", {"quest_id": 12, "mode": 2, "mbm_ret": 0, "sub_ret": 0, "msg_ret": 3}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, b"", **kw)
        cand_res = Runner().run(cand_bytes, cand_rodata, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_zero_guard", "if (quest_id == 0) {\n        return;\n    }", ""),
        ("wrong_cached_flag", "quest_work[0x5F7] = 1;", "quest_work[0x5F7] = 0;"),
        ("drop_sub_branch", "if (sub_idx > 0)", "if (false)"),
        ("flip_msg_branch", "if (msg_idx < 0)", "if (msg_idx > 0)"),
        ("drop_tail_call", "script_vm_func_0029025c(quest_id);", ""),
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
        f"PASS: script_vm_func_002900b0 (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
