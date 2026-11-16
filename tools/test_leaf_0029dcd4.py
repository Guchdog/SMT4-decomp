#!/usr/bin/env python3
"""Differential test for camp_func_0029dcd4 (0x0029dcd4) using Unicorn ARM emulation."""

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
FUNC_ADDR = 0x0029dcd4
FUNC_SIZE = 576

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
CODE_ADDR  = 0x001f0000
CODE_SIZE  = 0x00100000  # 1MB
DATA_ADDR  = 0x00430000
DATA_SIZE  = 0x00020000  # 128KB
WORK_ADDR  = 0x00500000
WORK_SIZE  = 0x00010000  # 64KB
SKILL_ADDR = 0x00600000
SKILL_SIZE = 0x00010000  # 64KB
TRAP_ADDR  = 0x90000000

STUB_2B9364 = 0x002b9364
STUB_29F088 = 0x0029f088
STUB_290A68 = 0x00290a68
STUB_2BE7FC = 0x002be7fc
STUB_295904 = 0x00295904
STUB_24BFBC = 0x0024bfbc
STUB_24BEAC = 0x0024beac
STUB_1F4480 = 0x001f4480
STUB_296D8C = 0x00296d8c

def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)

def get_symbol_offset(obj_file, sym_name):
    data = Path(obj_file).read_bytes()
    e_shoff, e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<IIHH", data, 32)[0], struct.unpack_from("<H", data, 46)[0], struct.unpack_from("<H", data, 48)[0], struct.unpack_from("<H", data, 50)[0]
    sections = [struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    symtab = [s for s in sections if s[1] == 2][0]
    strtab = sections[symtab[6]]
    for i in range(symtab[5] // 16):
        st_name, st_val, st_size, st_info, st_other, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + i * 16)
        name = data[strtab[4] + st_name:].split(b"\x00")[0].decode("ascii", errors="replace")
        if sym_name == name or name == f"_{sym_name}":
            return st_val
    return 0

def compile_candidate():
    out_dir = ROOT / "build/test_leaf_0029dcd4"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch45_a.o"
    src_file = ROOT / "src/engine/leaf_batch45_a.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    cand_entry = None
    for k in funcs:
        if "0029dcd4" in k:
            cand_entry = funcs[k]
            break
    if not cand_entry:
        raise RuntimeError(f"Function camp_func_0029dcd4 not found in {obj_file}: available {list(funcs.keys())}")
    
    code_raw, relocs = cand_entry
    code = bytearray(code_raw)
    func_sym_offset = get_symbol_offset(obj_file, "camp_func_0029dcd4")

    # Map rodata strings if present
    data = Path(obj_file).read_bytes()
    e_shoff, e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<IIHH", data, 32)[0], struct.unpack_from("<H", data, 46)[0], struct.unpack_from("<H", data, 48)[0], struct.unpack_from("<H", data, 50)[0]
    shstrtab = [struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize) for i in range(e_shnum)][e_shstrndx]
    shstr_data = data[shstrtab[4]:shstrtab[4] + shstrtab[5]]
    
    rodata_bytes = b""
    rodata_offset_in_file = 0
    for i in range(e_shnum):
        sh = struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        sec_name = shstr_data[sh[0]:].split(b"\x00")[0].decode("ascii", errors="replace")
        if sec_name in (".rodata", ".rodata.str1.1"):
            rodata_bytes = data[sh[4]:sh[4] + sh[5]]
            rodata_offset_in_file = sh[4]
            break

    RODATA_MAP_ADDR = 0x00700000

    for rel in relocs:
        offset = rel.offset
        sym = rel.symbol_name
        if rel.relocation_type in (28, 29, 10):  # R_ARM_CALL / R_ARM_JUMP24 / R_ARM_THM_CALL
            target = None
            if "002b9364" in sym: target = STUB_2B9364
            elif "0029f088" in sym: target = STUB_29F088
            elif "00290a68" in sym: target = STUB_290A68
            elif "002be7fc" in sym: target = STUB_2BE7FC
            elif "00295904" in sym: target = STUB_295904
            elif "0024bfbc" in sym: target = STUB_24BFBC
            elif "0024beac" in sym: target = STUB_24BEAC
            elif "001f4480" in sym: target = STUB_1F4480
            elif "00296d8c" in sym: target = STUB_296D8C
            if target is not None:
                pc = FUNC_ADDR + offset + 8
                disp = (target - pc) >> 2
                orig_inst = struct.unpack_from("<I", code, offset)[0]
                cond = orig_inst & 0xFF000000
                new_inst = cond | (disp & 0x00FFFFFF)
                struct.pack_into("<I", code, offset, new_inst)
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            orig_addend = struct.unpack_from("<I", code, offset)[0]
            if sym == ".text":
                target = FUNC_ADDR + (orig_addend - func_sym_offset)
                struct.pack_into("<I", code, offset, target)
            elif sym in (".rodata", ".rodata.str1.1"):
                target = RODATA_MAP_ADDR + orig_addend
                struct.pack_into("<I", code, offset, target)
    return bytes(code), rodata_bytes, RODATA_MAP_ADDR

class CampRunner:
    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(SKILL_ADDR, SKILL_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_map(0x00700000, 0x10000) # rodata map
        self.call_log = []

        # Stubs
        bx_lr_arm = struct.pack("<I", 0xe12fff1e)
        bx_lr_thm = struct.pack("<H", 0x4770)
        stubs = [
            (STUB_2B9364, self._on_2b9364, bx_lr_arm),
            (STUB_29F088, self._on_29f088, bx_lr_arm),
            (STUB_290A68, self._on_290a68, bx_lr_arm),
            (STUB_2BE7FC, self._on_2be7fc, bx_lr_thm),
            (STUB_295904, self._on_295904, bx_lr_arm),
            (STUB_24BFBC, self._on_24bfbc, bx_lr_arm),
            (STUB_24BEAC, self._on_24beac, bx_lr_arm),
            (STUB_1F4480, self._on_1f4480, bx_lr_arm),
            (STUB_296D8C, self._on_296d8c, bx_lr_arm),
        ]
        for s_addr, s_hook, s_insn in stubs:
            self.uc.mem_write(s_addr, s_insn)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, s_hook, begin=s_addr, end=s_addr)

    def _read_str(self, addr):
        try:
            raw = self.uc.mem_read(addr, 128)
            end = raw.find(b"\x00")
            if end != -1:
                return bytes(raw[:end])
            return bytes(raw)
        except Exception:
            return b""

    def _on_2b9364(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("camp_func_002b9364", r0))
        if r0 == 0:
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        else:
            uc.reg_write(arm.UC_ARM_REG_R0, SKILL_ADDR)

    def _on_29f088(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        self.call_log.append(("camp_func_0029f088", r0, r1, r2))

    def _on_290a68(self, uc, address, size, user_data):
        dst = uc.reg_read(arm.UC_ARM_REG_R0)
        val = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("ui_func_00290a68", dst, val))
        text = f"{val}".encode("ascii") + b"\x00"
        uc.mem_write(dst, text)

    def _on_2be7fc(self, uc, address, size, user_data):
        dst = uc.reg_read(arm.UC_ARM_REG_R0)
        fmt_ptr = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        fmt = self._read_str(fmt_ptr)
        self.call_log.append(("ui_func_002be7fc", fmt, r2, r3))
        if b"%s" in fmt:
            s1 = self._read_str(r2)
            s2 = self._read_str(r3)
            out = s1 + b"\x81\x60" + s2 + b"\x00"
            uc.mem_write(dst, out)
        else:
            uc.mem_write(dst, fmt + b"\x00")

    def _on_295904(self, uc, address, size, user_data):
        widget = uc.reg_read(arm.UC_ARM_REG_R0)
        str_ptr = uc.reg_read(arm.UC_ARM_REG_R1)
        s = self._read_str(str_ptr)
        self.call_log.append(("script_vm_func_00295904", widget, s))

    def _on_24bfbc(self, uc, address, size, user_data):
        dst = uc.reg_read(arm.UC_ARM_REG_R0)
        elem = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("camp_func_0024bfbc", elem))
        out = f"Elem{elem}".encode("ascii") + b"\x00"
        uc.mem_write(dst, out)

    def _on_24beac(self, uc, address, size, user_data):
        dst = uc.reg_read(arm.UC_ARM_REG_R0)
        scope = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("shop_func_0024beac", scope))
        out = f"Scope{scope}".encode("ascii") + b"\x00"
        uc.mem_write(dst, out)

    def _on_1f4480(self, uc, address, size, user_data):
        a0 = uc.reg_read(arm.UC_ARM_REG_R0)
        a1 = uc.reg_read(arm.UC_ARM_REG_R1)
        a2 = uc.reg_read(arm.UC_ARM_REG_R2)
        dst = uc.reg_read(arm.UC_ARM_REG_R3)
        self.call_log.append(("engine_func_001f4480", a0, a1, a2))
        out = f"Desc_{a2}_{a1}".encode("ascii") + b"\x00"
        uc.mem_write(dst, out)

    def _on_296d8c(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        sp = uc.reg_read(arm.UC_ARM_REG_SP)
        sp0, sp1, sp2 = struct.unpack("<III", uc.mem_read(sp, 12))
        self.call_log.append(("script_vm_func_00296d8c", r0, r1, r2, r3, sp0, sp1, sp2))

    def run(self, code_bytes, rodata_bytes, rodata_addr, r0, r1, r2, r3, skill_data=None):
        self.call_log = []
        self.uc.mem_write(FUNC_ADDR, code_bytes)
        if rodata_bytes:
            self.uc.mem_write(rodata_addr, rodata_bytes)

        # Clear memory
        self.uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        self.uc.mem_write(WORK_ADDR, b"\x00" * WORK_SIZE)
        self.uc.mem_write(SKILL_ADDR, b"\x00" * SKILL_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        # Setup 0x0043da28 manager
        # [0x0043da28] = 0
        # [0x0043da2c] = WORK_ADDR
        # [0x0043da30] = 0x0043da30 (fallback target)
        struct.pack_into("<III", self.uc.mem_read(0x0043da28, 12), 0, 0, 0, 0)
        self.uc.mem_write(0x0043da28, struct.pack("<III", 0, WORK_ADDR, 0x0043da30))

        # Setup work buffer
        # [WORK_ADDR + 0x558] = 0x00558800 (render_handle)
        self.uc.mem_write(WORK_ADDR + 0x558, struct.pack("<I", 0x00558800))

        # Setup skill data if present
        if skill_data:
            self.uc.mem_write(SKILL_ADDR, skill_data)

        # Setup registers
        sp = STACK_ADDR + STACK_SIZE - 0x100
        self.uc.reg_write(arm.UC_ARM_REG_SP, sp)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, r0)
        self.uc.reg_write(arm.UC_ARM_REG_R1, r1)
        self.uc.reg_write(arm.UC_ARM_REG_R2, r2)
        self.uc.reg_write(arm.UC_ARM_REG_R3, r3)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
        except Exception as e:
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {e}")

        work_snapshot = bytes(self.uc.mem_read(WORK_ADDR + 0x4cb, 0x100))
        return {
            "call_log": list(self.call_log),
            "work_snapshot": work_snapshot,
        }

def make_skill(min_hits, max_hits, scope, element, ailment):
    buf = bytearray(0x20)
    # flags at +0x08:
    # scope: bits 1..4 -> (scope << 1)
    # min_hits: bits 5..7 -> (min_hits << 5)
    # max_hits: bits 8..10 -> (max_hits << 8)
    flags = ((scope & 0xf) << 1) | ((min_hits & 7) << 5) | ((max_hits & 7) << 8)
    struct.pack_into("<H", buf, 0x08, flags)
    buf[0x0a] = element
    buf[0x0c] = ailment
    return bytes(buf)

def main():
    print("Testing camp_func_0029dcd4 (0x0029dcd4)...")
    orig_code = get_orig_bytes()
    cand_code, cand_rodata, rodata_addr = compile_candidate()

    runner = CampRunner()

    test_cases = []

    # Case 1: skill_id = 0 (skill not found)
    test_cases.append({
        "name": "Skill not found (skill_id = 0)",
        "r0": 0x1111, "r1": 0x2222, "r2": 0, "r3": 0x3333,
        "skill": None
    })

    # Case 2: min_hits == max_hits (1 hit, fire, single, KO, target=0)
    test_cases.append({
        "name": "Single hit (min=1, max=1), element 2, KO, target=0",
        "r0": 0, "r1": 50, "r2": 101, "r3": 1,
        "skill": make_skill(min_hits=1, max_hits=1, scope=1, element=2, ailment=1)
    })

    # Case 3: min_hits != max_hits (1..3 hits, elec, all, poison, custom target)
    test_cases.append({
        "name": "Multi hit (min=1, max=3), element 4, Poison, custom target",
        "r0": 0x7777, "r1": 80, "r2": 102, "r3": 2,
        "skill": make_skill(min_hits=1, max_hits=3, scope=2, element=4, ailment=5)
    })

    # Case 4: Ailment None (ailment 0)
    test_cases.append({
        "name": "Ailment None (0)",
        "r0": 0, "r1": 10, "r2": 103, "r3": 0,
        "skill": make_skill(min_hits=2, max_hits=2, scope=1, element=0, ailment=0)
    })

    # Case 5: Ailments Panic (6), Sleep (7), Bind (8), Sick (9)
    for a_id, a_name in [(6, "Panic"), (7, "Sleep"), (8, "Bind"), (9, "Sick")]:
        test_cases.append({
            "name": f"Ailment {a_name} ({a_id})",
            "r0": 0x8888, "r1": 20, "r2": 200 + a_id, "r3": 1,
            "skill": make_skill(min_hits=1, max_hits=4, scope=3, element=15, ailment=a_id)
        })

    # Case 6: Unknown ailment (3) - should skip formatting ailment
    test_cases.append({
        "name": "Unknown ailment (3)",
        "r0": 0, "r1": 0, "r2": 300, "r3": 0,
        "skill": make_skill(min_hits=1, max_hits=1, scope=1, element=1, ailment=3)
    })

    total = 0
    passed = 0
    for tc in test_cases:
        total += 1
        res_orig = runner.run(orig_code, b"", 0, tc["r0"], tc["r1"], tc["r2"], tc["r3"], tc["skill"])
        res_cand = runner.run(cand_code, cand_rodata, rodata_addr, tc["r0"], tc["r1"], tc["r2"], tc["r3"], tc["skill"])

        # Compare call logs (function names and arguments)
        assert len(res_orig["call_log"]) == len(res_cand["call_log"]), f"Call log length mismatch on {tc['name']}:\n  Orig: {res_orig['call_log']}\n  Cand: {res_cand['call_log']}"
        for c_o, c_c in zip(res_orig["call_log"], res_cand["call_log"]):
            assert c_o == c_c, f"Call mismatch on {tc['name']}:\n  Orig: {c_o}\n  Cand: {c_c}"

        assert res_orig["work_snapshot"] == res_cand["work_snapshot"], f"Work buffer mismatch on {tc['name']}"
        passed += 1
        print(f"  [PASS] {tc['name']}")

    print(f"\nAll {passed}/{total} differential test cases PASSED!")

if __name__ == "__main__":
    main()
