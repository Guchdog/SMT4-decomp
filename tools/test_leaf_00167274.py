#!/usr/bin/env python3
"""Differential Unicorn test for func_00167274 (0x00167274, 1056 B span / 48 B entry)."""

from __future__ import annotations

import struct
import sys
import tempfile
from pathlib import Path

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM, Uc
from unicorn.arm_const import (
    UC_ARM_REG_LR,
    UC_ARM_REG_R0,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x00167274
ENTRY_SIZE = 48
FUNC_NAME = "func_00167274"

CALLEE_ADDRS = {
    0x00163534: "func_00163534",
    0x0016691C: "func_0016691c",
    0x0016391C: "func_0016391c",
}

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
STUB_BY_NAME = {name: STUB_BASE + idx * 4 for idx, name in enumerate(CALLEE_ADDRS.values())}
NAME_BY_STUB = {addr: name for name, addr in STUB_BY_NAME.items()}

STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
CTX_ADDR = 0x004A0000
HALT_ADDR = 0x004FFFF0


def patch_cand_elf(obj_path: Path) -> tuple[bytes, int]:
    elf = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", elf, 0x20)[0]
    e_shentsize, e_shnum, _ = struct.unpack_from("<HHH", elf, 0x2E)
    sections = [struct.unpack_from("<10I", elf, e_shoff + i * e_shentsize) for i in range(e_shnum)]

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

    for sh in sections:
        if sh[1] == 9 and sh[7] == func_shndx:
            for pos in range(sh[4], sh[4] + sh[5], 8):
                r_off, r_info = struct.unpack_from("<II", elf, pos)
                if not (func_val <= r_off < func_val + func_size):
                    continue
                c_off = r_off - func_val
                r_type = r_info & 0xFF
                s_name, _, _ = sym_info(r_info >> 8)
                if r_type in (28, 29):
                    insn = struct.unpack_from("<I", code, c_off)[0]
                    cond = (insn >> 28) & 0xF
                    op = (insn >> 24) & 0xF
                    link = op == 0xB
                    target = STUB_BY_NAME[s_name]
                    pc = FUNC_ADDR + c_off
                    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
                    struct.pack_into("<I", code, c_off, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
                else:
                    raise RuntimeError(f"Unsupported reloc {r_type} for {s_name}")
    return bytes(code), func_size


def compile_candidate(cpp_text: str) -> tuple[bytes, int]:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        src = td_path / "cand.cpp"
        obj = td_path / "cand.o"
        src.write_text(cpp_text, encoding="utf-8")
        res = compile_tu_armv6k(src, obj)
        if res.returncode != 0:
            raise RuntimeError(f"compile failed:\n{res.stderr}")
        return patch_cand_elf(obj)


def run_one(code_bytes: bytes, hooks: dict[int, str], ctx_words: tuple[int, int]) -> dict:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)

    uc.mem_map(0x000F0000, 0x00010000)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(FUNC_ADDR, code_bytes)
    for addr in hooks:
        uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))  # bx lr

    uc.mem_write(HALT_ADDR, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(CTX_ADDR, struct.pack("<II", ctx_words[0], ctx_words[1]))

    trace: list[tuple[str, int]] = []

    def hook_code(uc_inst, address, size, user_data):
        name = hooks.get(address)
        if name is not None:
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            trace.append((name, r0))

    uc.hook_add(UC_HOOK_CODE, hook_code)
    uc.reg_write(UC_ARM_REG_R0, CTX_ADDR)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x1000)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(FUNC_ADDR, HALT_ADDR, timeout=5_000_000, count=10_000)

    ret = uc.reg_read(UC_ARM_REG_R0)
    return {"ret": ret, "trace": trace}


def load_orig_entry() -> bytes:
    with open(CODE_BIN, "rb") as f:
        f.seek(FUNC_ADDR - CODE_BASE)
        return f.read(ENTRY_SIZE)


def build_cases() -> list[tuple[str, tuple[int, int]]]:
    return [
        ("eq_zero", (0, 0)),
        ("eq_nonzero", (0x12345678, 0x12345678)),
        ("ne_diff_low", (0x00001000, 0x00001001)),
        ("ne_diff_highbit", (0x80000000, 0x00000000)),
        ("ne_max_u32", (0xFFFFFFFF, 0xFFFFFFFE)),
    ]


def verify(cpp_text: str) -> tuple[bool, int, str]:
    cand_code, cand_size = compile_candidate(cpp_text)
    orig_code = load_orig_entry()
    orig_hooks = dict(CALLEE_ADDRS)
    cand_hooks = dict(NAME_BY_STUB)

    for label, ctx_words in build_cases():
        orig_res = run_one(orig_code, orig_hooks, ctx_words)
        cand_res = run_one(cand_code, cand_hooks, ctx_words)
        if orig_res != cand_res:
            return False, cand_size, f"FAIL {label}: orig={orig_res} cand={cand_res}"
    return True, cand_size, "OK"


def run_negative_controls(cpp_text: str) -> None:
    mutations = [
        (
            "invert_cmp",
            "extern \"C\" void* func_00167274(const u32* ctx) {\n    if (ctx[0] == ctx[1]) {",
            "extern \"C\" void* func_00167274(const u32* ctx) {\n    if (ctx[0] != ctx[1]) {",
        ),
        (
            "wrong_eq_callee",
            "        reinterpret_cast<void* (*)(const u32*)>(func_00163534)(ctx);",
            "        func_0016691c(ctx);",
        ),
        (
            "wrong_ne_callee",
            "    } else {\n        func_0016691c(ctx);",
            "    } else {\n        reinterpret_cast<void* (*)(const u32*)>(func_00163534)(ctx);",
        ),
        (
            "skip_tail_call",
            "    return func_0016391c(ctx);\n}",
            "    return const_cast<u32*>(ctx);\n}",
        ),
        (
            "wrong_ret_null",
            "    return func_0016391c(ctx);\n}",
            "    func_0016391c(ctx);\n    return nullptr;\n}",
        ),
    ]
    for name, old, new in mutations:
        assert old in cpp_text, f"Mutation anchor missing: {name}"
        mutated = cpp_text.replace(old, new, 1)
        ok, _, _ = verify(mutated)
        if ok:
            raise AssertionError(f"Negative control {name} unexpectedly passed!")


def main() -> int:
    cpp_text = SRC_CPP.read_text(encoding="utf-8")
    ok, cand_size, msg = verify(cpp_text)
    if not ok:
        print(msg)
        return 1
    run_negative_controls(cpp_text)
    print(f"ALL PASS: {len(build_cases())} cases + 5 negative controls (cand_size={cand_size}B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
