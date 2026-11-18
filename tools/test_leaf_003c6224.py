#!/usr/bin/env python3
"""Differential test for battle_func_003c6224 (0x003C6224) using Unicorn ARM."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SRC_CPP = ROOT / "src/engine/leaf_batch45_c.cpp"
FUNC_ADDR = 0x003C6224
FUNC_SIZE = 940
FUNC_NAME = "battle_func_003c6224"

STUB_BASE = 0x00110000
RODATA_BASE = 0x00120000
MEM_BASE = 0x20000000
MEM_SIZE = 0x00020000
SELF_ADDR = 0x20001000
R4_ADDR = 0x20002000
SUB_ADDR = 0x20007000
G4342C8_OBJ = 0x20008000
RET_PTR_ADDR = 0x20009000
STACK_TOP = 0x2001E000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x0022A4D8: ("battle_func_0022a4d8", 2),
    0x0022A5D8: ("battle_func_0022a5d8", 2),
    0x0022A5F8: ("battle_func_0022a5f8", 2),
}

STUB_ADDRS = {addr: STUB_BASE + idx * 4 for idx, addr in enumerate(sorted(CALLEES))}
ADDR_BY_STUB = {v: k for k, v in STUB_ADDRS.items()}
NAME_TO_STUB = {CALLEES[k][0]: v for k, v in STUB_ADDRS.items()}

TARGET_ADDRS = [
    0x00493554, 0x0049355C, 0x00434310, 0x00434314, 0x00434318, 0x0043431C,
    0x004342D4, 0x004342D8, 0x00434320, 0x00434324, 0x004342E0, 0x00434328,
    0x0043432C, 0x00434330, 0x004342E4, 0x00434334, 0x00434338, 0x004342E8,
    0x0043433C, 0x00434340, 0x004342EC, 0x00434344, 0x00434348, 0x0043434C,
    0x00434350, 0x00434354, 0x00439CEC, 0x004342F0,
]


def patch_orig_code(raw: bytes) -> bytearray:
    code = bytearray(raw)
    for off in range(0, len(code), 4):
        if 0x18 <= off < 0x94:
            continue
        insn = struct.unpack_from("<I", code, off)[0]
        cond = (insn >> 28) & 0xF
        op = (insn >> 24) & 0xF
        if cond != 0xF and op in (0xA, 0xB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = pc + 8 + (imm24 << 2)
            if target in STUB_ADDRS:
                new_imm = ((STUB_ADDRS[target] - (pc + 8)) >> 2) & 0x00FFFFFF
                struct.pack_into("<I", code, off, (insn & 0xFF000000) | new_imm)
    return code


def patch_cand_elf(obj_path: Path) -> tuple[bytearray, list[tuple[int, bytes]]]:
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
            func_val = val
            func_size = struct.unpack_from("<I", elf, symtab[4] + idx * 16 + 8)[0]
            func_shndx = shndx
            break
    assert func_val is not None and func_size is not None and func_shndx is not None

    text_sh = sections[func_shndx]
    code = bytearray(elf[text_sh[4] + func_val : text_sh[4] + func_val + func_size])

    rodata_blob = bytearray()
    rodata_map: dict[int, int] = {}
    for idx, sh in enumerate(sections):
        if sec_name(idx).startswith(".rodata"):
            rodata_map[idx] = RODATA_BASE + len(rodata_blob)
            rodata_blob.extend(elf[sh[4] : sh[4] + sh[5]])
            while len(rodata_blob) % 4 != 0:
                rodata_blob.append(0)

    for sh in sections:
        if sh[1] == 9 and sh[7] == func_shndx:
            for pos in range(sh[4], sh[4] + sh[5], 8):
                r_off, r_info = struct.unpack_from("<II", elf, pos)
                if not (func_val <= r_off < func_val + func_size):
                    continue
                c_off = r_off - func_val
                r_type = r_info & 0xFF
                s_name, _, s_shndx = sym_info(r_info >> 8)
                if r_type in (28, 29):
                    insn = struct.unpack_from("<I", code, c_off)[0]
                    cond = (insn >> 28) & 0xF
                    op = (insn >> 24) & 0xF
                    link = op == 0xB
                    target = NAME_TO_STUB[s_name]
                    pc = FUNC_ADDR + c_off
                    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
                    struct.pack_into("<I", code, c_off, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
                elif r_type == 2:
                    addend = struct.unpack_from("<I", code, c_off)[0]
                    if s_shndx == func_shndx:
                        struct.pack_into("<I", code, c_off, (FUNC_ADDR - func_val) + addend)
                    elif s_shndx in rodata_map:
                        struct.pack_into("<I", code, c_off, rodata_map[s_shndx] + addend)
                    else:
                        raise RuntimeError(f"Unexpected R_ARM_ABS32 section {s_shndx} ({s_name})")
                else:
                    raise RuntimeError(f"Unsupported reloc {r_type} for {s_name}")
    rodata_blobs = [(RODATA_BASE, bytes(rodata_blob))] if rodata_blob else []
    return code, rodata_blobs


class Runner:
    def __init__(self, code: bytes, rodata_blobs: list[tuple[int, bytes]] | None = None):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        cpacr = self.uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        if rodata_blobs:
            for addr, blob in rodata_blobs:
                self.uc.mem_write(addr, blob)
        # Map 0x003d64c0 helper (12 bytes) for case 1 tail-call in orig
        helper_3d64c0 = ORIG_BIN.read_bytes()[0x003D64C0 - 0x00100000 : 0x003D64C0 - 0x00100000 + 12]
        self.uc.mem_write(0x003D64C0, helper_3d64c0)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

    def run(self, cmd: int, flag_ret: int, val_ret: int, init_bits: int) -> dict:
        self.uc.mem_write(SELF_ADDR + 0x10, struct.pack("<I", SUB_ADDR))
        self.uc.mem_write(0x004342C8, struct.pack("<I", G4342C8_OBJ))
        self.uc.mem_write(G4342C8_OBJ + 0x560, struct.pack("<I", 0))
        self.uc.mem_write(G4342C8_OBJ + 0x634, struct.pack("<I", init_bits))
        self.uc.mem_write(R4_ADDR + 0x44A8, struct.pack("<I", init_bits))
        self.uc.mem_write(RET_PTR_ADDR, struct.pack("<I", val_ret))
        for addr in TARGET_ADDRS:
            self.uc.mem_write(addr, struct.pack("<I", 0))

        trace: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if addr not in ADDR_BY_STUB:
                return
            target = ADDR_BY_STUB[addr]
            name, nargs = CALLEES[target]
            regs = (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1)
            args = tuple(uc.reg_read(regs[i]) for i in range(nargs))
            trace.append((name, args))
            if name == "battle_func_0022a5d8":
                uc.reg_write(arm.UC_ARM_REG_R0, flag_ret)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, RET_PTR_ADDR)
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_R1, R4_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_R2, cmd & 0xFFFFFFFF)
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=10000)
        finally:
            self.uc.hook_del(hook)

        globals_out = tuple(
            struct.unpack("<I", bytes(self.uc.mem_read(a, 4)))[0] for a in TARGET_ADDRS
        )
        return {
            "g560": struct.unpack("<I", bytes(self.uc.mem_read(G4342C8_OBJ + 0x560, 4)))[0],
            "g634": struct.unpack("<I", bytes(self.uc.mem_read(G4342C8_OBJ + 0x634, 4)))[0],
            "r4_44a8": struct.unpack("<I", bytes(self.uc.mem_read(R4_ADDR + 0x44A8, 4)))[0],
            "globals": globals_out,
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    cases: list[tuple[str, dict]] = [
        ("cmd_0_set", {"cmd": 0, "flag_ret": 1, "val_ret": 0, "init_bits": 0x12340000}),
        ("cmd_0_clr", {"cmd": 0, "flag_ret": 0, "val_ret": 0, "init_bits": 0x12340100}),
        ("cmd_1", {"cmd": 1, "flag_ret": 0, "val_ret": 0x3F800000, "init_bits": 0}),
        ("cmd_2_set", {"cmd": 2, "flag_ret": 1, "val_ret": 0, "init_bits": 0x00001234}),
        ("cmd_2_clr", {"cmd": 2, "flag_ret": 0, "val_ret": 0, "init_bits": 0x40001234}),
        ("cmd_31_oob", {"cmd": 31, "flag_ret": 1, "val_ret": 0x99, "init_bits": 0}),
    ]
    for c in range(3, 31):
        cases.append((f"cmd_{c}", {"cmd": c, "flag_ret": 0, "val_ret": 0x1000 + c, "init_bits": 0}))
    return cases


def run_suite(orig_code: bytes, cand_code: bytes, rodata_blobs: list[tuple[int, bytes]]) -> list[str]:
    failures: list[str] = []
    for name, kwargs in build_cases():
        orig = Runner(orig_code).run(**kwargs)
        cand = Runner(cand_code, rodata_blobs).run(**kwargs)
        if orig != cand:
            failures.append(f"{name}: orig={orig} cand={cand}")
    return failures


def run_negative_controls(orig_code: bytes, cpp_text: str, work_dir: Path) -> None:
    mutations = [
        ("wrong_cmd0_bit", "0x100u", "0x200u"),
        ("wrong_cmd2_bit", "0x40000000u", "0x80000000u"),
        ("wrong_cmd11_helper", "cmd == 11u", "cmd == 12u"),
        ("wrong_target_30", "0x004342F0u", "0x004342F4u"),
        ("wrong_limit", "if (cmd >= 31u)", "if (cmd >= 30u)"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_cpp = work_dir / f"mut_{mut_name}.cpp"
        mut_obj = work_dir / f"mut_{mut_name}.o"
        mut_cpp.write_text(cpp_text.replace(old, new, 1), encoding="utf-8")
        compile_tu_armv6k(mut_cpp, mut_obj, ROOT)
        cand_code, rodata_blobs = patch_cand_elf(mut_obj)
        failures = run_suite(orig_code, cand_code, rodata_blobs)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_003c6224"
    work_dir.mkdir(parents=True, exist_ok=True)

    raw = ORIG_BIN.read_bytes()[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    orig_code = patch_orig_code(raw)

    obj_path = work_dir / "leaf_batch45_c.o"
    compile_tu_armv6k(SRC_CPP, obj_path, ROOT)
    cand_code, rodata_blobs = patch_cand_elf(obj_path)

    failures = run_suite(orig_code, cand_code, rodata_blobs)
    if failures:
        for f in failures[:5]:
            print("FAIL:", f)
        return 1

    run_negative_controls(orig_code, SRC_CPP.read_text(encoding="utf-8"), work_dir)
    cases = build_cases()
    print(f"ALL PASS: {len(cases)} cases + 5 negative controls (cand_size={len(cand_code)}B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
