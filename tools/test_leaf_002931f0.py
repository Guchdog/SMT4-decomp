#!/usr/bin/env python3
"""Differential test for camp_func_002931f0 (0x002931F0) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts camp_func_002931f0,
resolves all 18 external callees to deterministic Unicorn stubs, and runs
the pinned original (extracted/exefs/code.bin) against the compiled candidate
across all mode/slot/tab/flag branches plus mutation negative controls.
"""

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

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SRC_CPP = ROOT / "src/engine/leaf_batch45_a.cpp"
FUNC_ADDR = 0x002931F0
FUNC_SIZE = 740
FUNC_NAME = "camp_func_002931f0"

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00020000
STUB_BASE = 0x00110000
RODATA_ADDR = 0x004012A0
SELF_ADDR = 0x20000000
MGR_ADDR = 0x20010000
ITEM_ADDR = 0x20020000
INFO_ADDR = 0x20021000
MEM_SIZE = 0x00030000
STACK_TOP = 0x2002F000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x002176A8: "engine_func_002176a8",
    0x0028D4F0: "camp_func_0028d4f0",
    0x0028D58C: "camp_func_0028d58c",
    0x002923D0: "camp_func_002923d0",
    0x002931CC: "camp_func_002931cc",
    0x00293C98: "ui_func_00293c98",
    0x00297F40: "camp_func_00297f40",
    0x0029CBEC: "camp_func_0029cbec",
    0x0029DCD4: "camp_func_0029dcd4",
    0x0029F10C: "camp_func_0029f10c",
    0x0029F248: "camp_func_0029f248",
    0x0029F260: "camp_func_0029f260",
    0x002A89E4: "camp_func_002a89e4",
    0x002B0824: "camp_func_002b0824",
    0x002B66EC: "script_vm_func_002b66ec",
    0x002C0BA8: "script_vm_func_002c0ba8",
    0x00309B8C: "camp_func_00309b8c",
    0x003171F8: "camp_func_003171f8",
}

ARITIES = {
    0x002176A8: 1,
    0x0028D4F0: 1,
    0x0028D58C: 2,
    0x002923D0: 1,
    0x002931CC: 1,
    0x00293C98: 0,
    0x00297F40: 2,
    0x0029CBEC: 1,
    0x0029DCD4: 4,
    0x0029F10C: 2,
    0x0029F248: 1,
    0x0029F260: 1,
    0x002A89E4: 1,
    0x002B0824: 1,
    0x002B66EC: 0,
    0x002C0BA8: 1,
    0x00309B8C: 2,
    0x003171F8: 2,
}

STUB_ADDRS = {addr: STUB_BASE + idx * 4 for idx, addr in enumerate(sorted(CALLEES))}
ADDR_BY_STUB = {v: k for k, v in STUB_ADDRS.items()}
NAME_TO_STUB = {CALLEES[k]: v for k, v in STUB_ADDRS.items()}


def parse_elf_relocs(elf_bytes: bytes, target_func: str) -> list[tuple[int, int, str]]:
    e_shoff = struct.unpack_from("<I", elf_bytes, 0x20)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", elf_bytes, 0x2E)

    sections = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh = struct.unpack_from("<10I", elf_bytes, off)
        sections.append(sh)

    shstr_off = sections[e_shstrndx][4]

    def sec_name(idx: int) -> str:
        n_off = shstr_off + sections[idx][0]
        end = elf_bytes.find(b"\x00", n_off)
        return elf_bytes[n_off:end].decode("ascii", errors="replace")

    symtab = None
    strtab = None
    text_idx = None
    for idx, sh in enumerate(sections):
        name = sec_name(idx)
        if sh[1] == 2:
            symtab = sh
            strtab = sections[sh[6]]
        elif name == ".text":
            text_idx = idx

    assert symtab is not None and strtab is not None and text_idx is not None
    str_off = strtab[4]

    def sym_name(sym_idx: int) -> str:
        s_off = symtab[4] + sym_idx * 16
        st_name = struct.unpack_from("<I", elf_bytes, s_off)[0]
        end = elf_bytes.find(b"\x00", str_off + st_name)
        return elf_bytes[str_off + st_name : end].decode("ascii", errors="replace")

    func_off = None
    func_size = None
    for idx in range(symtab[5] // 16):
        if sym_name(idx) == target_func:
            st_value, st_size = struct.unpack_from("<II", elf_bytes, symtab[4] + idx * 16 + 4)
            func_off = st_value
            func_size = st_size
            break
    assert func_off is not None and func_size is not None

    relocs: list[tuple[int, int, str]] = []
    for sh in sections:
        if sh[1] == 9 and sh[7] == text_idx:
            rel_off, rel_size = sh[4], sh[5]
            for pos in range(rel_off, rel_off + rel_size, 8):
                r_offset, r_info = struct.unpack_from("<II", elf_bytes, pos)
                r_type = r_info & 0xFF
                r_sym = r_info >> 8
                if func_off <= r_offset < func_off + func_size:
                    relocs.append((r_offset - func_off, r_type, sym_name(r_sym)))
    return relocs


def encode_arm_branch(pc: int, target: int, link: bool) -> int:
    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if link else 0xEA000000
    return opcode | imm24


def patch_orig_code(raw: bytes) -> bytearray:
    code = bytearray(raw)
    for off in range(0, len(code), 4):
        insn = struct.unpack_from("<I", code, off)[0]
        cond = (insn >> 28) & 0xF
        op = (insn >> 24) & 0xF
        if cond == 0xE and op in (0xA, 0xB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = pc + 8 + (imm24 << 2)
            if target in STUB_ADDRS:
                patched = encode_arm_branch(pc, STUB_ADDRS[target], link=(op == 0xB))
                struct.pack_into("<I", code, off, patched)
    return code


def patch_cand_code(raw: bytes, relocs: list) -> bytearray:
    code = bytearray(raw)
    for rel in relocs:
        r_off = rel.offset
        r_type = rel.relocation_type
        s_name = rel.symbol_name
        if r_type in (28, 29):  # R_ARM_CALL, R_ARM_JUMP24
            insn = struct.unpack_from("<I", code, r_off)[0]
            cond = (insn >> 28) & 0xF
            op = (insn >> 24) & 0xF
            link = op == 0xB
            target = NAME_TO_STUB[s_name]
            pc = FUNC_ADDR + r_off
            imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
            struct.pack_into("<I", code, r_off, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
        else:
            raise RuntimeError(f"Unsupported relocation type {r_type} for {s_name} at +{r_off:#x}")
    return code


def build_candidate(src_text: str | None = None) -> bytearray:
    out_dir = ROOT / "build" / "test_leaf_002931f0"
    out_dir.mkdir(parents=True, exist_ok=True)
    if src_text is None:
        src_path = SRC_CPP
        obj_path = out_dir / "baseline.o"
    else:
        src_path = out_dir / "mutant.cpp"
        obj_path = out_dir / "mutant.o"
        src_path.write_text(src_text, encoding="utf-8")

    res = compile_tu_armv6k(src_path, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compile failed:\n{res.stderr}")
    funcs = extract_elf_functions_detailed(obj_path)
    if FUNC_NAME not in funcs:
        raise RuntimeError(f"{FUNC_NAME} not found in compiled ELF")
    raw, relocs = funcs[FUNC_NAME]
    return patch_cand_code(raw, relocs)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(STUB_BASE, 0x1000)
        self.uc.mem_map(FUNC_ADDR & ~0xFFF, 0x2000)
        self.uc.mem_map(0x00401000, 0x1000)
        self.uc.mem_map(SELF_ADDR, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

        for stub_addr in STUB_ADDRS.values():
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))  # bx lr
        self.uc.mem_write(RODATA_ADDR, struct.pack("<6I", 0, 1, 2, 3, 4, 5))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(SELF_ADDR, b"\x00" * MEM_SIZE)

        # Populate self
        struct.pack_into("<I", buf := bytearray(0x6000), 0x305C, case["tab"])
        struct.pack_into("<I", buf, 0x340C, case["list_ptr"])
        struct.pack_into("<I", buf, 0x59BC, case["ui_obj"])
        for idx, val in case.get("u16_341a", {}).items():
            struct.pack_into("<H", buf, case["tab"] * 16 + idx * 2 + 0x341A, val)
        for idx, val in case.get("u16_341c", {}).items():
            struct.pack_into("<H", buf, case["tab"] * 16 + idx * 2 + 0x341C, val)
        for idx, val in case.get("u16_3480", {}).items():
            struct.pack_into("<H", buf, idx * 2 + 0x3480, val)
        if "s16_38f4" in case:
            struct.pack_into("<h", buf, case["tab"] * 2 + 0x38F4, case["s16_38f4"])
        self.uc.mem_write(SELF_ADDR, bytes(buf))

        # Populate mgr, item, info
        mgr = bytearray(0x4500)
        struct.pack_into("<I", mgr, 0x44A8, case.get("mgr_flags", 0))
        self.uc.mem_write(MGR_ADDR, bytes(mgr))

        item = bytearray(0x80)
        struct.pack_into("<H", item, 0x46, case.get("item_46", 0x1234))
        self.uc.mem_write(ITEM_ADDR, bytes(item))

        info = bytearray(0x20)
        struct.pack_into("<HH", info, 2, case.get("info_2", 0), case.get("info_4", 0))
        self.uc.mem_write(INFO_ADDR, bytes(info))

        call_log: list[tuple[str, int, int, int, int]] = []
        mode_seq = list(case["modes"])

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr not in ADDR_BY_STUB:
                return
            orig_target = ADDR_BY_STUB[addr]
            cname = CALLEES[orig_target]
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc.reg_read(arm.UC_ARM_REG_R3)
            arity = ARITIES[orig_target]
            call_log.append((cname, *(r0, r1, r2, r3)[:arity]))

            ret = 0
            if orig_target == 0x0029F260:
                ret = case["f260"]
            elif orig_target == 0x0029F248:
                ret = case["f248"]
            elif orig_target == 0x00297F40:
                ret = mode_seq.pop(0) if mode_seq else 0
            elif orig_target == 0x002931CC:
                ret = 1 if (r0 - 0x2E) in case.get("active_31cc", ()) else 0
            elif orig_target == 0x002176A8:
                ret = 0x5500 + r0
            elif orig_target == 0x00293C98:
                ret = MGR_ADDR
            elif orig_target == 0x002C0BA8:
                ret = case.get("f0ba8", 0)
            elif orig_target == 0x002B66EC:
                ret = INFO_ADDR
            elif orig_target == 0x002A89E4:
                ret = ITEM_ADDR
            elif orig_target == 0x002B0824:
                ret = 0x99000 + r0
            elif orig_target == 0x0028D58C:
                ret = case.get("f_d58c", 0)
            elif orig_target == 0x0028D4F0:
                ret = case.get("f_d4f0", 0)
            uc.reg_write(arm.UC_ARM_REG_R0, ret & 0xFFFFFFFF)

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_BASE + 0x100)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)
        return {"call_log": call_log}


def make_cases() -> list[dict]:
    return [
        {
            "name": "mode_none_matched",
            "modes": [0, 0, 0, 0],
            "tab": 0,
            "list_ptr": 0x1111,
            "ui_obj": 0x2222,
            "f260": 0,
            "f248": 0,
        },
        {
            "name": "mode1_tab1_slot0",
            "modes": [1],
            "tab": 1,
            "list_ptr": 0x1111,
            "ui_obj": 0x3333,
            "f260": 0,
            "f248": 0,
            "s16_38f4": -3,
            "item_46": 0x0042,
        },
        {
            "name": "mode1_tab1_slot2_flag40_on",
            "modes": [1],
            "tab": 1,
            "list_ptr": 0x1111,
            "ui_obj": 0x3333,
            "f260": 1,
            "f248": 1,
            "mgr_flags": 0x40,
        },
        {
            "name": "mode1_tab1_slot2_flag40_off",
            "modes": [1],
            "tab": 1,
            "list_ptr": 0x1111,
            "ui_obj": 0x3333,
            "f260": 1,
            "f248": 1,
            "mgr_flags": 0x00,
            "u16_341a": {2: 0x77},
        },
        {
            "name": "mode1_tab0_slot0",
            "modes": [1],
            "tab": 0,
            "list_ptr": 0x1111,
            "ui_obj": 0x4444,
            "f260": 0,
            "f248": 0,
        },
        {
            "name": "mode1_tab0_slot1_info_ok",
            "modes": [1],
            "tab": 0,
            "list_ptr": 0x1111,
            "ui_obj": 0x4444,
            "f260": 1,
            "f248": 0,
            "f0ba8": 1,
            "info_2": 1,
            "info_4": 2,
        },
        {
            "name": "mode1_tab0_slot3_info_ok_flag40_on",
            "modes": [1],
            "tab": 0,
            "list_ptr": 0x1111,
            "ui_obj": 0x4444,
            "f260": 2,
            "f248": 1,
            "f0ba8": 1,
            "info_2": 1,
            "info_4": 2,
            "mgr_flags": 0x40,
        },
        {
            "name": "mode1_tab0_slot3_info_off_flag40_off",
            "modes": [1],
            "tab": 0,
            "list_ptr": 0x1111,
            "ui_obj": 0x4444,
            "f260": 2,
            "f248": 1,
            "f0ba8": 0,
            "mgr_flags": 0x00,
            "u16_341c": {2: 0x88},
        },
        {
            "name": "mode2_flag40_on",
            "modes": [0, 2],
            "tab": 0,
            "list_ptr": 0x1111,
            "ui_obj": 0x5555,
            "f260": 1,
            "f248": 2,
            "mgr_flags": 0x40,
            "f_d58c": 0x19,
        },
        {
            "name": "mode2_flag40_off_zero",
            "modes": [0, 2],
            "tab": 0,
            "list_ptr": 0x1111,
            "ui_obj": 0x5555,
            "f260": 1,
            "f248": 2,
            "mgr_flags": 0x00,
            "f_d4f0": 0,
        },
        {
            "name": "mode7_calls_2923d0",
            "modes": [0, 0, 7],
            "tab": 0,
            "list_ptr": 0x1111,
            "ui_obj": 0x6666,
            "f260": 1,
            "f248": 1,
            "u16_3480": {2: 0x012A},
        },
        {
            "name": "mode3_selects_second_active",
            "modes": [0, 0, 0, 3],
            "tab": 0,
            "list_ptr": 0x1111,
            "ui_obj": 0x7777,
            "f260": 1,
            "f248": 0,
            "active_31cc": (1, 4, 5),
        },
    ]


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = patch_orig_code(raw_bin[off : off + FUNC_SIZE])
    src_text = SRC_CPP.read_text(encoding="utf-8")
    cand_code = build_candidate()
    print(f"{FUNC_NAME}: orig {len(orig_code)} B, cand {len(cand_code)} B")

    cases = make_cases()
    for case in cases:
        orig_res = Runner().run(orig_code, case)
        cand_res = Runner().run(cand_code, case)
        if orig_res != cand_res:
            print(f"FAIL [{case['name']}]:")
            print("  orig:", orig_res)
            print("  cand:", cand_res)
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("mode3_color", "0x323232ffu", "0x323232feu"),
        ("flag40_mask", "& 0x40u", "& 0x20u"),
        ("mode1_tab1_off", "+ 0x341Au", "+ 0x341Cu"),
        ("mode7_off", "+ 0x3480u", "+ 0x3482u"),
        ("mode3_base", "idx + 0x2Eu", "idx + 0x2Fu"),
    ]
    for name, old, new in mutants:
        assert old in src_text, f"Mutant target not found: {old}"
        m_code = build_candidate(src_text.replace(old, new, 1))
        detected = False
        for case in cases:
            orig_res = Runner().run(orig_code, case)
            try:
                bad_res = Runner().run(m_code, case)
            except unicorn.UcError:
                detected = True
                break
            if orig_res != bad_res:
                detected = True
                break
        if not detected:
            print(f"FAIL [mutant {name}]: not detected!")
            return 1
        print(f"PASS [mutant {name} detected]")

    print(f"ALL PASS: {len(cases)} cases + {len(mutants)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
