#!/usr/bin/env python3
"""Differential test for engine_func_00341578 (0x00341578) using Unicorn ARM."""

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
SRC_CPP = ROOT / "src/engine/leaf_batch45_a.cpp"
FUNC_ADDR = 0x00341578
FUNC_SIZE = 892
FUNC_NAME = "engine_func_00341578"

STUB_BASE = 0x00110000
RODATA_BASE = 0x00120000
MEM_BASE = 0x20000000
MEM_SIZE = 0x00020000
SELF_ADDR = 0x20000000
FP_ADDR = 0x20001000
NODE_ADDR = 0x20002000
MGR_ADDR = 0x20003000
CTX_ADDR = 0x20003100
ALLOC_MEM_ADDR = 0x20003200
ALLOC_OBJ_ADDR = 0x20003400
R8_ADDR = 0x20003600
R8_SUB_ADDR = 0x20003700
EVAL_CTX_ADDR = 0x20003800
RTTI_NODE_A = 0x20004000
RTTI_NODE_B = 0x0044E858
RTTI_NODE_C = 0x0044E820
STACK_TOP = 0x2001E000
TRAP_ADDR = 0x001F0000

STUB_V_GET_RTTI = STUB_BASE + 0x00
STUB_V_MGR_ALLOC = STUB_BASE + 0x04
STUB_V_OBJ_INIT = STUB_BASE + 0x08
STUB_EVAL_FN = STUB_BASE + 0x0C

CALLEES = {
    0x002C5E2C: ("script_vm_func_002c5e2c", 1),
    0x002C31BC: ("engine_func_002c31bc", 0),
    0x002C31D8: ("engine_func_002c31d8", 0),
    0x002C3188: ("engine_func_002c3188", 3),
    0x002A6108: ("engine_func_002a6108", 2),
    0x002A5CA4: ("engine_func_002a5ca4", 5),
    0x002C2210: ("engine_func_002c2210", 2),
    0x002C1774: ("ui_func_002c1774", 1),
    0x002C20A8: ("engine_func_002c20a8", 4),
    0x002C1FFC: ("ui_func_002c1ffc", 2),
    0x00298FEC: ("ui_func_00298fec", 1),
    0x003418F4: ("engine_func_003418f4", 3),
}

STUB_ADDRS = {addr: STUB_BASE + 0x40 + idx * 4 for idx, addr in enumerate(sorted(CALLEES))}
ADDR_BY_STUB = {v: k for k, v in STUB_ADDRS.items()}
NAME_TO_STUB = {CALLEES[k][0]: v for k, v in STUB_ADDRS.items()}


def patch_orig_code(raw: bytes) -> bytearray:
    code = bytearray(raw)
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
        # Enable VFP/NEON (CP10/CP11) + FPEXC.EN
        cpacr = self.uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        if rodata_blobs:
            for addr, blob in rodata_blobs:
                self.uc.mem_write(addr, blob)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

    def run(self, outer_count: int, inner_count: int, has_r8: bool) -> dict:
        self.uc.mem_write(SELF_ADDR, b"\x00" * 0x700)
        fp_buf = bytearray(0x200)
        struct.pack_into("<I", fp_buf, 0x44, outer_count)
        struct.pack_into("<i", fp_buf, 0x48, 0x80 - 0x48)  # base at FP_ADDR + 0x80
        struct.pack_into("<i", fp_buf, 0x7C, inner_count)
        struct.pack_into("<i", fp_buf, 0x80, 0x40)  # arr80 at FP_ADDR + 0xC0
        for i in range(outer_count):
            off = 0x80 + 0x1C + i * 0x10
            struct.pack_into("<i", fp_buf, off + 0x0C, 0x140 - (off + 0x0C))
        fp_buf[0x140:0x146] = b"node0\x00"
        for j in range(inner_count):
            off = 0xC0 + j * 0x10 + 0x28
            struct.pack_into("<i", fp_buf, off, 0x160 - off)
        fp_buf[0x160:0x165] = b"sub0\x00"
        self.uc.mem_write(FP_ADDR, bytes(fp_buf))

        # RTTI chain: RTTI_NODE_A -> 0x0044E858 -> 0x0044E820 -> 0
        self.uc.mem_write(RTTI_NODE_A, struct.pack("<I", RTTI_NODE_B))
        self.uc.mem_write(RTTI_NODE_B, struct.pack("<I", RTTI_NODE_C))
        self.uc.mem_write(RTTI_NODE_C, struct.pack("<I", 0))

        # Node vtable at NODE_ADDR + 0x100
        node_buf = bytearray(0x300)
        struct.pack_into("<I", node_buf, 0x00, NODE_ADDR + 0x100)
        struct.pack_into("<I", node_buf, 0x108, STUB_V_GET_RTTI)
        struct.pack_into("<I", node_buf, 0x268, R8_ADDR if has_r8 else 0)
        self.uc.mem_write(NODE_ADDR, bytes(node_buf))

        # r8 & r8_sub
        r8_buf = bytearray(0x20)
        struct.pack_into("<I", r8_buf, 8, R8_SUB_ADDR)
        self.uc.mem_write(R8_ADDR, bytes(r8_buf))
        r8_sub_buf = bytearray(0x20)
        struct.pack_into("<f", r8_sub_buf, 0x10, 12.5)
        self.uc.mem_write(R8_SUB_ADDR, bytes(r8_sub_buf))

        # mgr vtable at MGR_ADDR + 0x40
        mgr_buf = bytearray(0x80)
        struct.pack_into("<I", mgr_buf, 0x00, MGR_ADDR + 0x40)
        struct.pack_into("<I", mgr_buf, 0x48, STUB_V_MGR_ALLOC)
        self.uc.mem_write(MGR_ADDR, bytes(mgr_buf))

        # alloc_obj vtable at ALLOC_OBJ_ADDR + 0x100
        obj_buf = bytearray(0x140)
        struct.pack_into("<I", obj_buf, 0x00, ALLOC_OBJ_ADDR + 0x100)
        struct.pack_into("<I", obj_buf, 0x10C, STUB_V_OBJ_INIT)
        struct.pack_into("<f", obj_buf, 0x38, 99.0)
        struct.pack_into("<f", obj_buf, 0x44, 1.5)
        struct.pack_into("<f", obj_buf, 0x48, 2.5)
        struct.pack_into("<I", obj_buf, 0x4C, STUB_EVAL_FN)
        struct.pack_into("<I", obj_buf, 0x50, EVAL_CTX_ADDR)
        self.uc.mem_write(ALLOC_OBJ_ADDR, bytes(obj_buf))

        trace: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if addr == STUB_V_GET_RTTI:
                trace.append(("v_get_rtti", uc.reg_read(arm.UC_ARM_REG_R0)))
                uc.reg_write(arm.UC_ARM_REG_R0, RTTI_NODE_A)
                uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
                return
            if addr == STUB_V_MGR_ALLOC:
                trace.append((
                    "v_mgr_alloc",
                    uc.reg_read(arm.UC_ARM_REG_R0),
                    uc.reg_read(arm.UC_ARM_REG_R1),
                    uc.reg_read(arm.UC_ARM_REG_R2),
                ))
                uc.reg_write(arm.UC_ARM_REG_R0, ALLOC_MEM_ADDR)
                uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
                return
            if addr == STUB_V_OBJ_INIT:
                trace.append((
                    "v_obj_init",
                    uc.reg_read(arm.UC_ARM_REG_R0),
                    uc.reg_read(arm.UC_ARM_REG_R1),
                ))
                uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
                return
            if addr == STUB_EVAL_FN:
                s0 = uc.reg_read(arm.UC_ARM_REG_S0)
                s1 = uc.reg_read(arm.UC_ARM_REG_S1)
                s2 = uc.reg_read(arm.UC_ARM_REG_S2)
                trace.append(("eval_fn", uc.reg_read(arm.UC_ARM_REG_R0), s0, s1, s2))
                uc.reg_write(arm.UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", 42.25))[0])
                uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
                return
            if addr not in ADDR_BY_STUB:
                return
            target = ADDR_BY_STUB[addr]
            name, nargs = CALLEES[target]
            regs = (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2, arm.UC_ARM_REG_R3)
            args = tuple(uc.reg_read(regs[i]) for i in range(min(nargs, 4)))
            if name == "script_vm_func_002c5e2c":
                trace.append((name, args))
                uc.reg_write(arm.UC_ARM_REG_R0, FP_ADDR)
            elif name == "engine_func_002c31bc":
                trace.append((name, args))
                uc.reg_write(arm.UC_ARM_REG_R0, MGR_ADDR)
            elif name == "engine_func_002c31d8":
                trace.append((name, args))
                uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
            elif name == "engine_func_002c3188":
                raw_desc = bytes(uc.mem_read(args[0], 0x28))
                desc = raw_desc[:5] + b"\x00\x00\x00" + raw_desc[8:37] + b"\x00\x00\x00"
                trace.append((name, desc, args[1], args[2]))
                uc.reg_write(arm.UC_ARM_REG_R0, NODE_ADDR)
            elif name == "engine_func_002a6108":
                trace.append((name, args))
                uc.reg_write(arm.UC_ARM_REG_R0, ALLOC_OBJ_ADDR)
            elif name == "engine_func_002a5ca4":
                sp_arg = struct.unpack("<i", bytes(uc.mem_read(uc.reg_read(arm.UC_ARM_REG_SP), 4)))[0]
                desc = bytes(uc.mem_read(args[1], 0x10))
                trace.append((name, args[0], desc, args[2], args[3], sp_arg))
            elif name == "engine_func_002c20a8":
                vecs = tuple(bytes(uc.mem_read(a, 12)) for a in args[1:4])
                trace.append((name, args[0], vecs))
            elif name == "ui_func_002c1ffc":
                s0 = uc.reg_read(arm.UC_ARM_REG_S0)
                s1 = uc.reg_read(arm.UC_ARM_REG_S1)
                s2 = uc.reg_read(arm.UC_ARM_REG_S2)
                s3 = uc.reg_read(arm.UC_ARM_REG_S3)
                trace.append((name, args[0], args[1], s0, s1, s2, s3))
            elif name == "engine_func_003418f4":
                trace.append((name, args))
                uc.emu_stop()
                return
            else:
                trace.append((name, args))
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_R1, 0x1234)
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {
            "self": bytes(self.uc.mem_read(SELF_ADDR, 0x700)),
            "alloc_obj": bytes(self.uc.mem_read(ALLOC_OBJ_ADDR, 0x60)),
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("empty_outer", {"outer_count": 0, "inner_count": 0, "has_r8": False}),
        ("outer1_no_r8", {"outer_count": 1, "inner_count": 1, "has_r8": False}),
        ("outer1_inner0", {"outer_count": 1, "inner_count": 0, "has_r8": True}),
        ("outer1_inner1", {"outer_count": 1, "inner_count": 1, "has_r8": True}),
        ("outer1_inner2", {"outer_count": 1, "inner_count": 2, "has_r8": True}),
        ("outer2_inner1", {"outer_count": 2, "inner_count": 1, "has_r8": True}),
    ]


def run_suite(orig_code: bytes, cand_code: bytes, rodata_blobs: list[tuple[int, bytes]], verbose: bool = False) -> list[str]:
    failures: list[str] = []
    for name, kwargs in build_cases():
        orig = Runner(orig_code).run(**kwargs)
        cand = Runner(cand_code, rodata_blobs).run(**kwargs)
        if orig != cand:
            if verbose:
                for k in ("self", "alloc_obj", "trace"):
                    if orig[k] != cand[k]:
                        print(f"  [{name}] {k} differs:")
                        if k == "trace":
                            print("    orig:", orig[k])
                            print("    cand:", cand[k])
                        else:
                            for i in range(0, len(orig[k]), 4):
                                if orig[k][i:i+4] != cand[k][i:i+4]:
                                    print(f"    +0x{i:x}: orig={orig[k][i:i+4].hex()} cand={cand[k][i:i+4].hex()}")
            failures.append(f"{name}: mismatch")
    return failures


def run_negative_controls(orig_code: bytes, cpp_text: str, work_dir: Path) -> None:
    mutations = [
        ("wrong_rtti", "cast_rtti_341578(node, 0x0044E820u)", "cast_rtti_341578(node, 0x0044E824u)"),
        ("wrong_shift_prev", "*reinterpret_cast<float*>(obj + 0x3C) = prev;", "*reinterpret_cast<float*>(obj + 0x3C) = res;"),
        ("wrong_w_const", "0x3FD55555u", "0x3F800000u"),
        ("wrong_v54c_2", "v54c[2] = 1.0f;", "v54c[2] = 2.0f;"),
        ("wrong_tail_arg2", "engine_func_003418f4(self, 0u, -1);", "engine_func_003418f4(self, 0u, 0);"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_cpp = work_dir / f"mut_{mut_name}.cpp"
        mut_obj = work_dir / f"mut_{mut_name}.o"
        mut_cpp.write_text(cpp_text.replace(old, new, 1), encoding="utf-8")
        compile_tu_armv6k(mut_cpp, mut_obj, ROOT)
        cand_code, rodata_blobs = patch_cand_elf(mut_obj)
        failures = run_suite(orig_code, cand_code, rodata_blobs, verbose=False)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_00341578"
    work_dir.mkdir(parents=True, exist_ok=True)

    raw = ORIG_BIN.read_bytes()[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    orig_code = patch_orig_code(raw)

    obj_path = work_dir / "leaf_batch45_a.o"
    compile_tu_armv6k(SRC_CPP, obj_path, ROOT)
    cand_code, rodata_blobs = patch_cand_elf(obj_path)

    failures = run_suite(orig_code, cand_code, rodata_blobs, verbose=True)
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
