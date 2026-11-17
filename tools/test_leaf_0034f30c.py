#!/usr/bin/env python3
"""Differential test for engine_func_0034f30c (0x0034F30C) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts engine_func_0034f30c,
resolves engine_func_002c3b48, engine_func_0023a7c4, and the virtual allocator
slot, and compares the pinned original against the compiled candidate across
modes 0..6, dimension thresholds, allocation failure, and rotation cases.
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
FUNC_ADDR = 0x0034F30C
FUNC_SIZE = 772
FUNC_NAME = "engine_func_0034f30c"

STUB_BASE = 0x00110000
STUB_ALLOC = STUB_BASE + 0x00
STUB_2C3B48 = STUB_BASE + 0x04
STUB_23A7C4 = STUB_BASE + 0x08
RODATA_BASE = 0x00120000

MEM_BASE = 0x20000000
MEM_SIZE = 0x00020000
SELF_ADDR = 0x20000000
ALLOC_ADDR = 0x20001000
VTBL_ADDR = 0x20002000
DESC_ADDR = 0x20003000
OUT_BUFS_ADDR = 0x20004000
OUT_TEX_ADDR = 0x20005000
OUT_DIMS_ADDR = 0x20006000
STACK_TOP = 0x2001F000
TRAP_ADDR = 0x001F0000


def encode_arm_branch(pc: int, target: int, link: bool) -> int:
    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if link else 0xEA000000
    return opcode | imm24


def patch_orig_code(raw: bytes) -> bytearray:
    code = bytearray(raw)
    mapping = {0x002C3B48: STUB_2C3B48, 0x0023A7C4: STUB_23A7C4}
    for off in range(0, len(code), 4):
        insn = struct.unpack_from("<I", code, off)[0]
        cond = (insn >> 28) & 0xF
        op = (insn >> 24) & 0xF
        if cond != 0xF and op in (0xA, 0xB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = pc + 8 + (imm24 << 2)
            if target in mapping:
                struct.pack_into("<I", code, off, encode_arm_branch(pc, mapping[target], link=(op == 0xB)))
    return code


def patch_cand_elf(obj_path: Path) -> tuple[bytearray, bytes]:
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
        st_name, st_value, _, _, st_shndx = struct.unpack_from("<IIIBH", elf, s_off)[:5]
        # Note: st_info, st_other are 1B each -> <IIIBBH
        st_name, st_value, _, _, _, st_shndx = struct.unpack_from("<IIIBBH", elf, s_off)
        end = elf.find(b"\x00", str_off + st_name)
        return elf[str_off + st_name : end].decode("ascii", errors="replace"), st_value, st_shndx

    func_val = None
    func_size = None
    func_shndx = None
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

    mapping = {"engine_func_002c3b48": STUB_2C3B48, "engine_func_0023a7c4": STUB_23A7C4}
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
                    target = mapping[s_name]
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
                        raise RuntimeError(f"Unsupported R_ARM_ABS32 section {sec_name(s_shndx)}")
                else:
                    raise RuntimeError(f"Unsupported relocation type {r_type} for {s_name}")
    return code, bytes(rodata_blob)


def build_candidate(src_text: str | None = None) -> tuple[bytearray, bytes]:
    out_dir = ROOT / "build" / "test_leaf_0034f30c"
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
    return patch_cand_elf(obj_path)


class Runner:
    def __init__(self, rodata: bytes = b"") -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        self.uc.mem_map(STUB_BASE, 0x1000)
        self.uc.mem_map(RODATA_BASE, 0x10000)
        self.uc.mem_map(FUNC_ADDR & ~0xFFF, 0x2000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))
        if rodata:
            self.uc.mem_write(RODATA_BASE, rodata)

        for addr in (STUB_ALLOC, STUB_2C3B48, STUB_23A7C4):
            self.uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)

        self.uc.mem_write(SELF_ADDR + 4, struct.pack("<I", ALLOC_ADDR))
        self.uc.mem_write(ALLOC_ADDR, struct.pack("<I", VTBL_ADDR))
        self.uc.mem_write(VTBL_ADDR, struct.pack("<I", STUB_ALLOC))

        desc = bytearray(0x40)
        struct.pack_into("<I", desc, 0x08, case["mode"])
        struct.pack_into("<ii", desc, 0x14, case["w"], case["h"])
        struct.pack_into("<I", desc, 0x24, case.get("rot", 0))
        self.uc.mem_write(DESC_ADDR, bytes(desc))

        call_log: list[tuple] = []
        alloc_seq = list(case.get("allocs", [0x30000000, 0x30100000]))

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc.reg_read(arm.UC_ARM_REG_R3)
            if addr == STUB_ALLOC:
                call_log.append(("alloc", r0, r1, r2))
                ret = alloc_seq.pop(0) if alloc_seq else 0
                uc.reg_write(arm.UC_ARM_REG_R0, ret)
            elif addr == STUB_2C3B48:
                call_log.append(("2c3b48", r0, r1))
            elif addr == STUB_23A7C4:
                sp = uc.reg_read(arm.UC_ARM_REG_SP)
                st = struct.unpack("<7I", uc.mem_read(sp, 28))
                call_log.append(("23a7c4", r0, r1, r2, r3, st))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_BASE + 0x10)
        sp_init = STACK_TOP - 4
        self.uc.mem_write(sp_init, struct.pack("<I", OUT_DIMS_ADDR))
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, DESC_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, OUT_BUFS_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R3, OUT_TEX_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_SP, sp_init)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "call_log": call_log,
            "self_tail": struct.unpack("<5I", self.uc.mem_read(SELF_ADDR + 0x28, 20)),
            "out_bufs": struct.unpack("<2I", self.uc.mem_read(OUT_BUFS_ADDR, 8)),
            "out_dims": struct.unpack("<2I", self.uc.mem_read(OUT_DIMS_ADDR, 8)),
            "out_tex_rot": (
                struct.unpack("<I", self.uc.mem_read(OUT_TEX_ADDR + 0x14, 4))[0],
                struct.unpack("<I", self.uc.mem_read(OUT_TEX_ADDR + 0x34, 4))[0],
            ),
        }


def make_cases() -> list[dict]:
    return [
        {"name": "mode6_small_rot1", "mode": 6, "w": 200, "h": 150, "rot": 1},
        {"name": "mode4_mid_rot2", "mode": 4, "w": 400, "h": 300, "rot": 2},
        {"name": "mode3_large_rot3", "mode": 3, "w": 513, "h": 513, "rot": 3},
        {"name": "mode0_rot0_two_allocs", "mode": 0, "w": 256, "h": 256, "rot": 0},
        {"name": "mode5_alloc_fail", "mode": 5, "w": 128, "h": 128, "rot": 0, "allocs": [0]},
    ]


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = patch_orig_code(raw_bin[off : off + FUNC_SIZE])
    src_text = SRC_CPP.read_text(encoding="utf-8")
    cand_code, rodata = build_candidate()
    print(f"{FUNC_NAME}: orig {len(orig_code)} B, cand {len(cand_code)} B")

    cases = make_cases()
    for case in cases:
        orig_res = Runner().run(orig_code, case)
        cand_res = Runner(rodata).run(cand_code, case)
        if orig_res != cand_res:
            print(f"FAIL [{case['name']}]:")
            print("  orig:", orig_res)
            print("  cand:", cand_res)
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("count_mode6", "(mode == 6) ? 1 : 2;", "(mode == 7) ? 1 : 2;"),
        ("tex_w_clamp", "(w > 0x200) ? 0x400u", "(w > 0x201) ? 0x400u"),
        ("rot_90", "0x42B40000u", "0x42B50000u"),
        ("gl_fmt", "0x6754u", "0x6755u"),
        ("self_28_mode1", "0x410u", "0x414u"),
    ]
    for name, old, new in mutants:
        assert old in src_text, f"Mutant target not found: {old}"
        m_code, m_rodata = build_candidate(src_text.replace(old, new, 1))
        detected = False
        for case in cases:
            orig_res = Runner().run(orig_code, case)
            try:
                bad_res = Runner(m_rodata).run(m_code, case)
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
